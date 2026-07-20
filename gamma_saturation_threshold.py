"""
gamma_saturation_threshold.py

Two things: (1) a fine-grained gamma sweep to pinpoint the exact
saturation threshold between 0.05 and 0.10, and (2) a direct check of
the h_t distribution to confirm the hypothesis that a large cluster
sits at exactly 0.60 (the "isolated"/"একা" single-keyword weight),
explaining the sharp jump mechanistically rather than just inferring it.

Run from repo root with: PYTHONPATH=src python3 gamma_saturation_threshold.py
"""

import json
from collections import Counter

from evaluation.conversation_distress import compute_conversation_distress

DATA_PATH = "data/multiturn_cleaned.jsonl"
TAU_H = 0.65


def load_mid_risk_sessions(path: str):
    sessions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
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


def would_escalate(h_t: float, gamma: float) -> bool:
    return h_t > (TAU_H - gamma * h_t)


def main():
    print("Loading mid-risk sessions...")
    sessions = load_mid_risk_sessions(DATA_PATH)
    trajectories = [compute_conversation_distress(turns) for turns in sessions]

    all_h_values = [h for traj in trajectories for h in traj]
    total_turns = len(all_h_values)

    # --- Part 1: confirm the clustering hypothesis directly ---
    print(f"\n=== h_t distribution check (total {total_turns} turns) ===")
    rounded = [round(h, 2) for h in all_h_values]
    counts = Counter(rounded)
    print("Most common h_t values (rounded to 2dp):")
    for value, count in counts.most_common(10):
        print(f"  h_t={value:.2f}: {count} turns ({100*count/total_turns:.2f}%)")

    # --- Part 2: fine-grained gamma sweep to find the exact threshold ---
    print(f"\n=== Fine-grained gamma sweep (0.05 to 0.10) ===")
    baseline = [would_escalate(h, 0.0) for h in all_h_values]

    fine_gammas = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    print(f"{'gamma':>8} | {'n_escalating':>14} | {'flipped':>10} | {'effective_threshold':>20}")
    print("-" * 65)
    for gamma in fine_gammas:
        n_escalating = sum(1 for h in all_h_values if would_escalate(h, gamma))
        n_flipped = sum(1 for h, b in zip(all_h_values, baseline) if would_escalate(h, gamma) != b)
        # effective threshold for a turn AT h_t=0.60 specifically
        eff_thresh_at_060 = TAU_H - gamma * 0.60
        print(f"{gamma:>8.2f} | {n_escalating:>14} | {n_flipped:>10} | {eff_thresh_at_060:>20.4f}")

    print(f"\nThe saturation point should appear where 'flipped' jumps sharply "
          f"between two adjacent gamma values -- that's where the effective "
          f"threshold crosses below the dominant h_t cluster identified above.")


if __name__ == "__main__":
    main()