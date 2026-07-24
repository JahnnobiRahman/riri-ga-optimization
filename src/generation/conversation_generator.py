"""
conversation_generator.py (v4 -- no-repeat phrase selection)

FIX: response_generator.py's assemble_prompt_trace() draws phrase-bank
lines via independent random.choice() calls with no memory across
turns -- fine for single-turn (each call is genuinely a fresh,
unrelated prompt), but produces visible repetition within a single
multi-turn conversation (same grounding/action line drawn 5+ times in
an 18-turn conversation, purely by chance).

FIXED (this file only, NOT response_generator.py): assemble_prompt_trace()
already accepts an optional custom `rng` parameter matching Python's
random.Random interface. This module builds a NoRepeatRandom wrapper
that remembers which specific phrase-bank lines have already been used
THIS CONVERSATION and avoids repeating them until every option in that
context has been used once (falls back to full reuse only once a
bank's variety is genuinely exhausted, which unavoidably happens with
long conversations and small banks -- can't manufacture variety that
doesn't exist in the phrase banks).

This does NOT fix the separate, larger issue that assemble_prompt_trace()
has no conversation-history parameter and generates each turn's
CONTENT independently of prior turns -- that is a distinct, deliberate
scope limitation being decided separately, not addressed here.
"""

import random
from typing import List, Dict, Any

from ga.genome import Genome
from generation.response_generator import assemble_prompt_trace
from evaluation.conversation_distress import (
    run_conversation_escalation,
    EscalationLevel,
    TurnDistressResult,
)

TAU_H = 0.65
ABSOLUTE_MAX_TURNS_SCORED = 30


class NoRepeatRandom:
    """
    Wraps a random.Random instance. Passes .random() and .shuffle()
    through unchanged (no dedup needed for probability checks or
    reordering). .choice() prefers options not yet used earlier in
    this same instance's lifetime, falling back to the full option
    set only once every option in the current call's list has
    already been used at least once.

    Intended to be instantiated FRESH per conversation (not shared
    across conversations, not shared across genomes) so repetition
    tracking is scoped correctly.
    """

    def __init__(self, seed=None):
        self._rnd = random.Random(seed)
        self._used = set()

    def random(self):
        return self._rnd.random()

    def shuffle(self, seq):
        return self._rnd.shuffle(seq)

    def choice(self, options):
        if not options:
            return self._rnd.choice(options)  # let it raise naturally

        unused = [o for o in options if self._key(o) not in self._used]
        pool = unused if unused else options  # fallback: bank exhausted, allow reuse
        chosen = self._rnd.choice(pool)
        self._used.add(self._key(chosen))
        return chosen

    @staticmethod
    def _key(option):
        # structure_blocks entries are (name, line) tuples; everything
        # else is a plain phrase string. Dedup on the actual text either way.
        if isinstance(option, tuple):
            return option[1]
        return option


def select_scoring_window(user_turns: List[str], max_turns: int) -> List[str]:
    if len(user_turns) <= max_turns:
        return user_turns
    return user_turns[-max_turns:]


def generate_conversation_responses(
    user_turns: List[str],
    session_risk_label: str,
    genome: Genome,
    seed: int = None,
) -> List[Dict[str, Any]]:
    """
    Generates a bot response for each scored turn, using ONE
    NoRepeatRandom instance for the entire conversation so phrase
    repetition is tracked and minimized across turns. Escalation
    timing logic (distress trajectory, FULL/LIGHT/NONE state machine)
    is unchanged from the previous version.
    """
    full_results: List[TurnDistressResult] = run_conversation_escalation(
        user_turns=user_turns,
        tau_h=TAU_H,
        gamma=genome.gamma,
    )

    effective_cap = min(genome.history_turns, ABSOLUTE_MAX_TURNS_SCORED)
    scored_turns = select_scoring_window(user_turns, effective_cap)
    n_skipped = len(user_turns) - len(scored_turns)
    scored_results = full_results[n_skipped:]

    # ONE no-repeat RNG for the whole conversation -- this is the key change.
    conv_rng = NoRepeatRandom(seed=seed)

    conversation_log = []

    for turn_result, user_msg in zip(scored_results, scored_turns):

        if session_risk_label == "high":
            escalate_override = True
        elif session_risk_label == "mid":
            escalate_override = (turn_result.escalation_level == EscalationLevel.FULL)
        else:
            escalate_override = False

        trace = assemble_prompt_trace(
            user_text=user_msg,
            risk_label=session_risk_label,
            g=genome,
            rng=conv_rng,
            escalate_override=escalate_override,
        )
        bot_response = trace["final_response"]

        conversation_log.append({
            "user_message": user_msg,
            "bot_response": bot_response,
            "escalation_level": turn_result.escalation_level,
            "effective_distress": turn_result.effective_distress,
        })

    return conversation_log