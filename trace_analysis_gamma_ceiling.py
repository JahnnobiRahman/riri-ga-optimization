"""
trace_analysis_gamma_ceiling.py

Checks whether the P100 run's gamma-at-ceiling best genome is
escalating appropriately or over-triggering on real mid-risk
conversations. No new GA run needed -- reuses the already-saved best
genome and scores a handful of real sessions, printing every turn's
distress score, escalation decision, and the actual bot response text
so a human can judge appropriateness directly (same spirit as the
paper's Appendix A qualitative failure-mode examples).

Run from repo root with: PYTHONPATH=src python3 trace_analysis_gamma_ceiling.py
"""

import json

from ga.genome import Genome
from evaluation.conversation_scoring import score_conversation

DATA_PATH = "data/multiturn_cleaned.jsonl"
BEST_GENOME_PATH = "experiments/multiturn_p100_best_genome.json"
N_MID_RISK_SESSIONS_TO_CHECK = 3


def load_mid_risk_sessions(path: str, n: int):
    sessions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(sessions) >= n:
                break
            line = line.strip()
            if not line:
                continue
            session = json.loads(line)
            if session["risk_label"] != "mid":
                continue
            user_turns = [t["message"] for t in session["turns"] if t.get("is_bot") == 0]
            if user_turns:
                sessions.append(user_turns)
    return sessions


def main():
    with open(BEST_GENOME_PATH) as f:
        genome_dict = json.load(f)
    genome = Genome(**genome_dict)
    print(f"Loaded genome: {genome}\n")
    print(f"gamma = {genome.gamma} (ceiling is 0.2)\n")
    print("=" * 80)

    sessions = load_mid_risk_sessions(DATA_PATH, N_MID_RISK_SESSIONS_TO_CHECK)

    for session_idx, user_turns in enumerate(sessions):
        print(f"\n--- MID-RISK SESSION {session_idx + 1} ({len(user_turns)} user turns) ---\n")

        result = score_conversation(user_turns, "mid", genome)

        n_full = sum(1 for t in result["conversation_log"] if t["escalation_level"].value == "full")
        n_light = sum(1 for t in result["conversation_log"] if t["escalation_level"].value == "light")
        n_none = sum(1 for t in result["conversation_log"] if t["escalation_level"].value == "none")
        print(f"Escalation summary: {n_full} full, {n_light} light, {n_none} none "
              f"(out of {len(result['conversation_log'])} scored turns)\n")

        for i, turn in enumerate(result["conversation_log"]):
            print(f"  Turn {i} | h_t={turn['effective_distress']:.3f} | "
                  f"level={turn['escalation_level'].value}")
            print(f"    User:  {turn['user_message'][:100]!r}")
            print(f"    Bot:   {turn['bot_response'][:150]!r}")
            print()

        print("=" * 80)


if __name__ == "__main__":
    main()