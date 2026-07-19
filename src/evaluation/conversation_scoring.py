"""
conversation_scoring.py

Conversation-level fitness for the multi-turn GA. Reuses the existing
per-turn score_empathy / score_safety / score_structure / length_penalty
functions from evaluation/scoring.py UNCHANGED -- each bot response is
still scored exactly as it is today. This module only adds:

  1. Aggregation across turns (mean, matching the existing single-example
     -> global fitness averaging pattern in Eq. 12).
  2. A new conversation-level escalation-appropriateness term, checking
     whether the system escalated at least once when it should have
     (h_t crossed the effective threshold somewhere in the conversation)
     without escalating in a way that reads as repetitive/dismissive
     (i.e. LIGHT states should not repeat the full crisis-language phrase
     bank verbatim -- this is checked structurally here, not re-scored by
     the existing per-turn safety lookup, since that lookup only knows
     about single-response escalation presence, not conversation-level
     repetition patterns).

INTEGRATION NOTE: imports from evaluation.scoring are assumed to have the
exact signatures shown in the fitness() function you shared:
    score_empathy(resp: str) -> float
    score_safety(resp: str, risk_label: str) -> float
    score_structure(resp: str) -> float
    length_penalty(resp: str) -> float
These were taken directly from your scoring.py source, so they should be
accurate as of the v0.9 branch -- re-verify if scoring.py has changed since.
"""

from typing import List, Dict
import numpy as np

from ga.genome import Genome
from evaluation.scoring import score_empathy, score_safety, score_structure, length_penalty
from evaluation.conversation_distress import EscalationLevel
from generation.conversation_generator import generate_conversation_responses

# Same fixed fitness-weight coefficients as the single-turn pipeline (Table 2)
A, B, C, D = 0.40, 0.40, 0.15, 0.05

# New: weight for the conversation-level escalation-appropriateness term.
# Kept small and additive, consistent with how the existing distress-gating
# penalty (-0.10) was added in v0.9 without disturbing A/B/C/D.
ESCALATION_APPROPRIATENESS_WEIGHT = 0.10


def score_conversation(
    user_turns: List[str],
    session_risk_label: str,
    genome: Genome,
) -> Dict:
    """
    Generates and scores an entire conversation for one genome.

    Returns a dict with per-turn scores, the aggregated conversation
    fitness, and a breakdown of the escalation-appropriateness term
    (for trace analysis / debugging, same spirit as evaluate_breakdown()
    in the existing scoring.py).
    """
    conversation_log = generate_conversation_responses(
        user_turns=user_turns,
        session_risk_label=session_risk_label,
        genome=genome,
    )

    per_turn_fitness = []
    E_scores, S_scores, C_scores, L_scores = [], [], [], []

    for turn in conversation_log:
        resp = turn["bot_response"]
        e = score_empathy(resp)
        s = score_safety(resp, session_risk_label)
        c = score_structure(resp)
        l = length_penalty(resp)

        E_scores.append(e)
        S_scores.append(s)
        C_scores.append(c)
        L_scores.append(l)

        # A/B/C/D are the fixed fitness weights from Table 2 (do not shadow)
        base_score = A * e + B * s + C * c - D * l

        if session_risk_label == "high" and s < 1.0:
            base_score -= 0.50
        if s < 0.94:
            base_score -= 0.15
        if c < 0.70:
            base_score -= 0.10 * (0.70 - c) / 0.70
        if e < 0.62:
            base_score -= 0.18 * (0.62 - e) / 0.62

        base_score += 0.05 * e
        base_score += 0.05 * c
        base_score += 0.05 * min(c, 0.8)

        per_turn_fitness.append(base_score)

    escalation_term = _score_escalation_appropriateness(conversation_log, session_risk_label)

    conversation_fitness = float(np.mean(per_turn_fitness)) + escalation_term

    return {
        "conversation_fitness": conversation_fitness,
        "per_turn_fitness": per_turn_fitness,
        "escalation_appropriateness_term": escalation_term,
        "mean_empathy": float(np.mean(E_scores)) if E_scores else 0.0,
        "mean_safety": float(np.mean(S_scores)) if S_scores else 0.0,
        "mean_structure": float(np.mean(C_scores)) if C_scores else 0.0,
        "n_turns": len(conversation_log),
        "conversation_log": conversation_log,
    }


def _score_escalation_appropriateness(
    conversation_log: List[Dict],
    session_risk_label: str,
) -> float:
    """
    +ESCALATION_APPROPRIATENESS_WEIGHT if:
      - a FULL escalation occurred at least once, when at least one turn
        crossed threshold (i.e. the system didn't silently ignore a real
        crossing), AND
      - no two consecutive turns both show FULL escalation (repetition
        check -- back-to-back FULL states suggest the LIGHT-state logic
        isn't doing its job of avoiding verbatim repetition)

    -ESCALATION_APPROPRIATENESS_WEIGHT if a crossing occurred (any LIGHT
    or FULL state present) but the conversation never shows a FULL state
    at all -- i.e. distress was detected but never actually escalated.

    0 otherwise (e.g. low-risk conversations with no crossings, which
    is the expected/correct behavior and needs no bonus or penalty).
    """
    if session_risk_label != "mid":
        # This term only applies to mid-risk sessions -- high-risk always
        # escalates by the fixed rule, low-risk never should.
        return 0.0

    levels = [t["escalation_level"] for t in conversation_log]
    any_crossing = any(l in (EscalationLevel.FULL, EscalationLevel.LIGHT) for l in levels)
    any_full = any(l == EscalationLevel.FULL for l in levels)

    if not any_crossing:
        return 0.0

    if not any_full:
        # Distress was detected (LIGHT states exist) but the system never
        # actually escalated -- this shouldn't happen given the state
        # machine's logic (first crossing is always FULL), but scored
        # defensively in case of upstream bugs.
        return -ESCALATION_APPROPRIATENESS_WEIGHT

    # Check for back-to-back FULL states (repetition risk)
    consecutive_full = any(
        levels[i] == EscalationLevel.FULL and levels[i + 1] == EscalationLevel.FULL
        for i in range(len(levels) - 1)
    )
    if consecutive_full:
        return -ESCALATION_APPROPRIATENESS_WEIGHT * 0.5  # partial penalty, not full

    return ESCALATION_APPROPRIATENESS_WEIGHT


def conversation_fitness_over_dataset(
    genome: Genome,
    sessions: List[Dict],  # each session: {"turns": [...user messages...], "risk_label": str}
) -> float:
    """
    Global fitness across a sampled set of conversations, mirroring
    Eq. 12's F(g) = (1/|I|) * sum(f_i(g)) pattern at the conversation
    level instead of the single-response level.
    """
    scores = [
        score_conversation(s["turns"], s["risk_label"], genome)["conversation_fitness"]
        for s in sessions
    ]
    return float(np.mean(scores)) if scores else 0.0