"""
conversation_distress.py

Extends the v0.9 single-message distress scorer (evaluation/distress_scorer.py)
to multi-turn conversations.

FIX (post-smoke-test): compute_conversation_distress() previously sliced
the input to the last `history_turns` messages BEFORE computing the
trajectory. This was a real bug, not a legitimate performance cap: the
decay recurrence h_t = max(raw_t, DECAY_ALPHA * h_{t-1}) only depends on
the immediately preceding h value, not an explicit lookback window --
DECAY_ALPHA^10 ~= 0.006, so old spikes naturally become negligible after
~10 turns without needing the input truncated at all. Slicing the input
first meant conversations longer than history_turns silently had their
early turns excluded not just from the trajectory calc but, downstream,
from generation and scoring entirely.

This version always runs the recurrence over the FULL conversation.
Capping which turns actually get a bot response generated/scored is now
handled separately in conversation_generator.py (see select_scoring_window),
using "most recent N turns" rather than an arbitrary truncated input to
this module.

Escalation state machine (EscalationStateMachine) is unchanged from the
original design: FULL on first crossing or a new distinct spike, LIGHT on
sustained-but-not-worsening distress, NONE below threshold. Session-level
risk label (from PHQ-4 total_score) is never changed by this module --
only escalation *timing* within a mid-risk session is affected, mirroring
the existing single-turn gamma mechanism in Eq. 6.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from evaluation.distress_scorer import compute_distress_score

# ======================
# Configuration
# ======================

DECAY_ALPHA = 0.6    # how much of h_{t-1} carries into h_t
SPIKE_DELTA = 0.15   # how much higher than the last-escalation h_t counts
                      # as a "new distinct spike" (re-triggers FULL)


class EscalationLevel(Enum):
    NONE = "none"
    LIGHT = "light"
    FULL = "full"


@dataclass
class TurnDistressResult:
    turn_index: int
    raw_distress: float          # this turn's own compute_distress_score()
    effective_distress: float    # h_t after decay carry-over
    escalation_level: EscalationLevel


def compute_conversation_distress(user_turns: List[str]) -> List[float]:
    """
    Returns h_t for EVERY user message in the conversation, in order.
    No truncation -- the decay recurrence naturally lets old spikes
    fade on their own (see module docstring for why explicit windowing
    was removed here).
    """
    trajectory: List[float] = []
    carried = 0.0
    for msg in user_turns:
        raw = compute_distress_score(msg)
        h_t = max(raw, DECAY_ALPHA * carried)
        trajectory.append(h_t)
        carried = h_t

    return trajectory


class EscalationStateMachine:
    """
    Tracks escalation state across a single conversation. Call
    `.step(h_t, tau_h_effective)` once per turn, in order, over the
    FULL conversation trajectory (not a windowed subset) so that state
    (has this conversation escalated before? what was the last
    escalation's h value?) is correct regardless of which turns are
    later selected for actual generation/scoring.
    """

    def __init__(self):
        self._has_escalated = False
        self._last_escalation_h = 0.0

    def step(self, h_t: float, tau_h_effective: float) -> EscalationLevel:
        crossed = h_t > tau_h_effective

        if not crossed:
            # Below threshold this turn. Do not reset _has_escalated --
            # a brief dip below threshold shouldn't erase escalation
            # history within the same conversation.
            return EscalationLevel.NONE

        if not self._has_escalated:
            self._has_escalated = True
            self._last_escalation_h = h_t
            return EscalationLevel.FULL

        if h_t > self._last_escalation_h + SPIKE_DELTA:
            self._last_escalation_h = h_t
            return EscalationLevel.FULL

        return EscalationLevel.LIGHT

    def reset(self):
        """Call between conversations if reusing the same instance."""
        self._has_escalated = False
        self._last_escalation_h = 0.0


def run_conversation_escalation(
    user_turns: List[str],
    tau_h: float,
    gamma: float,
) -> List[TurnDistressResult]:
    """
    Computes the full distress trajectory and escalation-level decision
    for EVERY turn in the conversation (no truncation). Mirrors Eq. 6's
    tau_h - gamma * h_i relaxation, applied per turn, over the whole
    conversation history.
    """
    trajectory = compute_conversation_distress(user_turns)

    machine = EscalationStateMachine()
    results = []
    for i, (msg, h_t) in enumerate(zip(user_turns, trajectory)):
        tau_h_effective = tau_h - (gamma * h_t)
        level = machine.step(h_t, tau_h_effective)
        raw = compute_distress_score(msg)
        results.append(TurnDistressResult(
            turn_index=i,
            raw_distress=raw,
            effective_distress=h_t,
            escalation_level=level,
        ))

    return results