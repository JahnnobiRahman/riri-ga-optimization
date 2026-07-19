"""
smoke_test_structure.py

Targeted follow-up to smoke_test_multiturn.py: forces a genome with
w_c >= 0.55 (deterministic full-structure regime, per Section 3.4.1)
to confirm structure scoring actually produces nonzero values when
run through the new conversation pipeline, rather than relying on
random_genome() to happen to draw a high w_c by chance.

Run from repo root with: PYTHONPATH=src python3 smoke_test_structure.py
"""

import json

from ga.genome import Genome
from evaluation.conversation_scoring import score_conversation

DATA_PATH = "data/multiturn_cleaned.jsonl"


def load_one_session(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            session = json.loads(line)
            user_turns = [t["message"] for t in session["turns"] if t.get("is_bot") == 0]
            if user_turns:
                return {
                    "turns": user_turns,
                    "risk_label": session["risk_label"],
                }
    raise RuntimeError("No usable session found.")


def main():
    session = load_one_session(DATA_PATH)

    # Deliberately construct a high-structure genome, not randomly drawn.
    genome = Genome(
        p_id=0,
        w_s=0.15,
        w_e=0.15,
        w_c=0.70,  # well above the 0.55 deterministic full-structure threshold
        memory_window=512,
        theta_mid=0.55,
        theta_high=0.80,
        gamma=0.05,
        history_turns=6,
    )
    genome.normalize()
    print(f"Forced genome: {genome}\n")

    result = score_conversation(
        user_turns=session["turns"],
        session_risk_label=session["risk_label"],
        genome=genome,
    )

    print(f"Mean structure: {result['mean_structure']:.4f}")
    print(f"N turns scored: {result['n_turns']}\n")

    print("Per-turn bot responses (checking for grounding/action/question content):")
    for i, turn in enumerate(result["conversation_log"][:5]):
        print(f"  Turn {i}: {turn['bot_response']!r}")


if __name__ == "__main__":
    main()