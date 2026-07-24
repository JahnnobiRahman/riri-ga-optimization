"""
build_spotcheck_materials.py (v2 -- fixed seed bug)

BUG FOUND AND FIXED: the previous version passed the same fixed
`seed=SEED` constant to every single call of
generate_conversation_responses(), regardless of which conversation
was being generated. Since NoRepeatRandom's internal random.Random is
fully determined by its seed, this meant every conversation produced
an IDENTICAL sequence of phrase choices at each turn index, regardless
of actual user content -- e.g. turn 2 of every conversation showed the
exact same three-line bot response, verbatim, across completely
different conversations. This is a worse artifact than the repetition
problem it was meant to help with: it makes the system look literally
scripted rather than responsive.

FIX: each conversation now gets its own seed, derived deterministically
from its own content (a stable hash of the conversation's user turns).
This preserves reproducibility -- re-running this script produces the
same output for the same input data -- while ensuring different
conversations produce genuinely different phrase sequences.

Run from repo root with: PYTHONPATH=src python3 build_spotcheck_materials.py
"""

import json
import random
import hashlib

from ga.genome import Genome
from ga.runner_multiturn import load_sessions, split_sessions
from generation.conversation_generator import generate_conversation_responses

SEED = 7  # still used for the SELECTION of which sessions to include (reproducible sampling)
DATA_PATH = "data/multiturn_cleaned.jsonl"
B4_GENOME_PATH = "experiments/multiturn_p100_seed7_v2split_best_genome.json"
OUTPUT_PATH = "experiments/human_eval_multiturn/spotcheck_materials.md"

N_WITH_ESCALATION = 3
N_WITHOUT_ESCALATION = 3


def derive_seed(user_turns) -> int:
    """
    Stable, content-derived seed for a specific conversation -- NOT a
    shared constant. Same conversation always gets the same seed
    (reproducible), but different conversations get genuinely
    different seeds (not identical phrase sequences).
    """
    content = "".join(user_turns)
    return int(hashlib.sha256(content.encode("utf-8")).hexdigest(), 16) % (2**31)


def session_has_full_escalation(user_turns, risk_label, genome):
    seed = derive_seed(user_turns)
    log = generate_conversation_responses(user_turns, risk_label, genome, seed=seed)
    return any(t["escalation_level"].value == "full" for t in log)


def select_sessions(val_sessions, genome):
    rnd = random.Random(SEED)
    mid_sessions = [s for s in val_sessions if s["risk_label"] == "mid"]
    rnd.shuffle(mid_sessions)

    with_esc, without_esc = [], []
    for s in mid_sessions:
        if len(with_esc) >= N_WITH_ESCALATION and len(without_esc) >= N_WITHOUT_ESCALATION:
            break
        has_esc = session_has_full_escalation(s["turns"], "mid", genome)
        if has_esc and len(with_esc) < N_WITH_ESCALATION:
            with_esc.append(s)
        elif not has_esc and len(without_esc) < N_WITHOUT_ESCALATION:
            without_esc.append(s)

    return with_esc + without_esc


def format_conversation(idx, session, genome):
    user_turns = session["turns"]
    seed = derive_seed(user_turns)  # per-conversation seed, not the shared constant
    log = generate_conversation_responses(user_turns, "mid", genome, seed=seed)

    lines = [f"## Conversation {idx} (mid-risk, {len(user_turns)} user turns)\n"]
    for i, turn in enumerate(log):
        esc = turn["escalation_level"].value
        h_t = turn["effective_distress"]
        lines.append(f"**Turn {i} (User):** {turn['user_message']}\n")
        lines.append(f"**Turn {i} (Bot)** _[escalation: {esc}, h_t={h_t:.2f}]_: {turn['bot_response']}\n")

    lines.append("\n### Escalation-Timing Assessment\n")
    lines.append("Did crisis language appear at appropriate moments across this conversation? (Yes/No/Partially): ___\n")
    lines.append("If No or Partially, which turn(s) felt wrong, and why: ___\n")
    lines.append("\n---\n")
    return "\n".join(lines)


def main():
    print("Loading and splitting sessions...")
    all_sessions = load_sessions(DATA_PATH)
    _, val_sessions = split_sessions(all_sessions, seed=SEED)

    with open(B4_GENOME_PATH) as f:
        genome = Genome(**json.load(f))

    print("Selecting mid-risk sessions (mix of escalation/no-escalation)...")
    selected = select_sessions(val_sessions, genome)
    print(f"Selected {len(selected)} sessions.\n")

    header = [
        "# Escalation-Timing Spot-Check\n",
        "**Scope note:** this is a focused check of one specific mechanism -- "
        "whether crisis-style language appears at appropriate moments across a "
        "multi-turn conversation, based on a distress score computed from the "
        "user's messages so far. It is NOT a general conversation-quality review: "
        "the system's response CONTENT does not reference earlier turns (a "
        "known, disclosed limitation of the current version), so responses may "
        "still read as somewhat repetitive within a single long conversation, "
        "though phrase variety has been improved. Please focus your judgment "
        "specifically on escalation timing, not overall conversational flow or "
        "content awareness.\n",
        "\n---\n",
    ]

    output_lines = header
    for idx, session in enumerate(selected, 1):
        output_lines.append(format_conversation(idx, session, genome))

    import os
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Saved {len(selected)} conversations to {OUTPUT_PATH}")
    print("IMPORTANT: contains real de-identified conversation content. "
          "Do not commit to git -- share directly with evaluators.")


if __name__ == "__main__":
    main()