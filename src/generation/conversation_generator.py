"""
conversation_generator.py

Wires the escalation state machine (conversation_distress.py) into
per-turn response generation. Reuses generate_response() UNCHANGED --
this module only decides WHEN to pass escalate_override=True/False.

CONFIRMED against actual response_generator.py source:
  generate_response(user_text: str, risk_label: str, g: Genome,
                     escalate_override: bool = False) -> str

escalate_override is STRICTLY boolean. response_generator.py already has
a built-in soft-support tier (SOFT_SUPPORT_LINES) that fires automatically
for mid-risk prompts whenever escalate_override=False -- so both
EscalationLevel.LIGHT and EscalationLevel.NONE map to False here; no
changes to response_generator.py are required.

history_turns NOW HAS A REAL PURPOSE (as of this version): it governs
how many of a conversation's MOST RECENT turns actually get a bot
response generated and scored, per genome -- letting the GA evolve
whether shorter or longer scored context performs better. This was a
deliberate choice over letting it remain evolved-but-unused (which
would have repeated the theta_mid/theta_high non-functional-gene
pattern). Range widened to [4, 24] to actually span real conversation
lengths -- see history_turns_range_patch.txt.

ABSOLUTE_MAX_TURNS_SCORED below is a separate, fixed safety ceiling
(not evolved) that applies regardless of what any individual genome's
history_turns value is -- bounds worst-case compute cost on the rare
very long conversations (max observed: 45 turns) even if a genome
evolves history_turns all the way to its 24-turn upper bound.

The distress trajectory itself is still computed over the FULL
conversation (see conversation_distress.py) -- history_turns/
ABSOLUTE_MAX_TURNS_SCORED only affect which turns get GENERATED and
SCORED, not the escalation state machine's view of conversation
history, which remains correct regardless of the scoring window.
"""

from typing import List, Dict

from ga.genome import Genome
from generation.response_generator import generate_response
from evaluation.conversation_distress import (
    run_conversation_escalation,
    EscalationLevel,
    TurnDistressResult,
)

TAU_H = 0.65                    # same fixed threshold as the single-turn mechanism (Eq. 6)
ABSOLUTE_MAX_TURNS_SCORED = 30  # fixed safety ceiling, independent of genome.history_turns


def select_scoring_window(user_turns: List[str], max_turns: int) -> List[str]:
    """
    Returns the turns that will actually get a bot response generated
    and scored: the most recent `max_turns` messages, or the whole
    conversation if it's already shorter than that.
    """
    if len(user_turns) <= max_turns:
        return user_turns
    return user_turns[-max_turns:]


def generate_conversation_responses(
    user_turns: List[str],
    session_risk_label: str,
    genome: Genome,
) -> List[Dict]:
    """
    Generates a bot response for each SCORED turn (see
    select_scoring_window) in a conversation, with escalation timing
    driven by the distress trajectory computed over the FULL
    conversation -- so even if a genome's history_turns caps
    generation/scoring to a shorter window, the escalation state
    machine still correctly reflects whether an earlier crossing
    happened, not just what's visible in the capped window.

    The effective scoring cap for this genome is
    min(genome.history_turns, ABSOLUTE_MAX_TURNS_SCORED) -- the genome
    value governs evolved behavior; the absolute ceiling exists purely
    as a compute-cost safety net and should rarely bind in practice
    given genome.history_turns' own upper bound of 24.

    session_risk_label is fixed for the whole conversation (from the
    PHQ-4 total_score) -- this function never changes risk_label
    mid-conversation.

    Returns a list of dicts, one per scored turn:
        {
            "user_message": str,
            "bot_response": str,
            "escalation_level": EscalationLevel,
            "effective_distress": float,
        }
    """
    full_results: List[TurnDistressResult] = run_conversation_escalation(
        user_turns=user_turns,
        tau_h=TAU_H,
        gamma=genome.gamma,
    )

    effective_cap = min(genome.history_turns, ABSOLUTE_MAX_TURNS_SCORED)
    scored_turns = select_scoring_window(user_turns, effective_cap)
    n_skipped = len(user_turns) - len(scored_turns)
    scored_results = full_results[n_skipped:]  # aligned suffix of full_results

    conversation_log = []

    for turn_result, user_msg in zip(scored_results, scored_turns):

        if session_risk_label == "high":
            escalate_override = True
        elif session_risk_label == "mid":
            escalate_override = (turn_result.escalation_level == EscalationLevel.FULL)
        else:  # low risk
            escalate_override = False

        bot_response = generate_response(
            user_text=user_msg,
            risk_label=session_risk_label,
            g=genome,
            escalate_override=escalate_override,
        )

        conversation_log.append({
            "user_message": user_msg,
            "bot_response": bot_response,
            "escalation_level": turn_result.escalation_level,
            "effective_distress": turn_result.effective_distress,
        })

    return conversation_log