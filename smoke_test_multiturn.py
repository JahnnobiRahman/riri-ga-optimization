"""
smoke_test_multiturn.py

Pulls a handful of real sessions from data/multiturn_cleaned.jsonl and
runs them end-to-end through score_conversation() -- not a real
experiment, just confirming the whole pipeline (distress trajectory ->
escalation state machine -> generator -> scoring -> aggregation) runs
without errors on real data and produces sane-looking output.

Run from repo root with: PYTHONPATH=src python3 smoke_test_multiturn.py
"""

import json

from ga.genome import random_genome
from evaluation.conversation_scoring import score_conversation

N_SESSIONS_TO_TEST = 5
DATA_PATH = "data/multiturn_cleaned.jsonl"


def load_sessions(path: str, n: int):
    sessions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(sessions) >= n:
                break
            line = line.strip()
            if not line:
                continue
            session = json.loads(line)
            user_turns = [
                t["message"] for t in session["turns"]
                if t.get("is_bot") == 0
            ]
            if user_turns:
                sessions.append({
                    "turns": user_turns,
                    "risk_label": session["risk_label"],
                    "n_user_exchanges": session["n_user_exchanges"],
                })
    return sessions


def main():
    sessions = load_sessions(DATA_PATH, N_SESSIONS_TO_TEST)
    print(f"Loaded {len(sessions)} sessions for smoke test.\n")

    genome = random_genome()
    print(f"Test genome: {genome}\n")

    for i, session in enumerate(sessions):
        print(f"--- Session {i+1} (risk={session['risk_label']}, "
              f"{session['n_user_exchanges']} user exchanges) ---")

        result = score_conversation(
            user_turns=session["turns"],
            session_risk_label=session["risk_label"],
            genome=genome,
        )

        print(f"  Conversation fitness: {result['conversation_fitness']:.4f}")
        print(f"  Mean empathy:         {result['mean_empathy']:.4f}")
        print(f"  Mean safety:          {result['mean_safety']:.4f}")
        print(f"  Mean structure:       {result['mean_structure']:.4f}")
        print(f"  Escalation term:      {result['escalation_appropriateness_term']:.4f}")
        print(f"  N turns scored:       {result['n_turns']}")

        print("  Escalation levels across turns:",
              [t["escalation_level"].value for t in result["conversation_log"]])

        print("  First bot response:  ",
              result["conversation_log"][0]["bot_response"][:150].replace("\n", " "))
        print()


if __name__ == "__main__":
    main()