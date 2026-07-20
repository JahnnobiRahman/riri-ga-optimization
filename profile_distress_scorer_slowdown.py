"""
profile_distress_scorer_slowdown.py

Isolates two possible causes of the P100 v2 run's 2x+ slowdown:
  1. compute_distress_score() being called TWICE per turn in
     run_conversation_escalation() -- once inside
     compute_conversation_distress() to build the trajectory, and
     again redundantly in the loop just to populate
     TurnDistressResult.raw_distress (which is only used for trace
     printouts, not by any generation/scoring logic).
  2. The new regex-based lookbehind matching being inherently slower
     per call than the old plain substring check.

Run from repo root with: PYTHONPATH=src python3 profile_distress_scorer_slowdown.py
"""

import time
import re
import json

from evaluation.distress_scorer import compute_distress_score as compute_distress_score_NEW

DATA_PATH = "data/multiturn_cleaned.jsonl"
N_CALLS = 50000  # enough to get a stable timing signal


# Old substring-based version, for direct comparison
DISTRESS_KEYWORDS = {
    "suicid": 1.0, "kill myself": 0.95, "end my life": 0.95,
    "not live": 0.90, "can't live": 0.90, "don't want to live": 0.90,
    "dont want to live": 0.90, "আত্মহত্যা": 1.0, "মরে যেতে": 0.90,
    "আর বাঁচতে": 0.85, "মৃত্যু": 0.80, "self-harm": 0.90,
    "self harm": 0.90, "hurt myself": 0.85, "cutting": 0.80,
    "নিজেকে ক্ষতি": 0.90, "রক্ত": 0.75, "no future": 0.75,
    "hopeless": 0.75, "no reason to live": 0.80, "nothing matters": 0.75,
    "কোন ভবিষ্যত": 0.75, "ভবিষ্যত নেই": 0.75, "completely alone": 0.65,
    "nobody cares": 0.70, "isolated": 0.60, "একা": 0.60,
    "কেউ বোঝে না": 0.65, "cannot handle": 0.60, "falling apart": 0.65,
    "unbearable": 0.70, "সহ্য করতে পারছি না": 0.70,
}


def compute_distress_score_OLD(prompt_text):
    if not prompt_text:
        return 0.0
    text = str(prompt_text).lower()
    score = 0.0
    matched = []
    for keyword, weight in DISTRESS_KEYWORDS.items():
        if keyword.lower() in text:
            score += weight
            matched.append(keyword)
    score = min(1.0, score)
    if len(matched) > 3:
        score = max(score - 0.05, 0.0)
    return float(score)


def load_sample_messages(path, n=2000):
    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if len(messages) >= n:
                break
            line = line.strip()
            if not line:
                continue
            session = json.loads(line)
            for t in session["turns"]:
                if t.get("is_bot") == 0 and t.get("message", "").strip():
                    messages.append(t["message"])
                    if len(messages) >= n:
                        break
    return messages


def main():
    print("Loading sample messages...")
    messages = load_sample_messages(DATA_PATH, n=2000)
    print(f"Loaded {len(messages)} real messages for timing.\n")

    # Repeat the sample to reach N_CALLS calls
    repeats = (N_CALLS // len(messages)) + 1
    test_messages = (messages * repeats)[:N_CALLS]

    print(f"=== Timing {N_CALLS} calls ===\n")

    t0 = time.perf_counter()
    for msg in test_messages:
        compute_distress_score_OLD(msg)
    old_time = time.perf_counter() - t0
    print(f"OLD (substring matching): {old_time:.3f}s "
          f"({N_CALLS/old_time:.0f} calls/sec)")

    t0 = time.perf_counter()
    for msg in test_messages:
        compute_distress_score_NEW(msg)
    new_time = time.perf_counter() - t0
    print(f"NEW (regex lookbehind):   {new_time:.3f}s "
          f"({N_CALLS/new_time:.0f} calls/sec)")

    slowdown = new_time / old_time
    print(f"\nPer-call slowdown from regex change: {slowdown:.2f}x")

    print(f"\n=== Combined effect estimate ===")
    print(f"If the redundant double-call in run_conversation_escalation() "
          f"is also present, total slowdown vs the ORIGINAL (old scorer, "
          f"single call) baseline would be approximately:")
    print(f"  2x (redundancy) * {slowdown:.2f}x (regex overhead) = "
          f"{2*slowdown:.2f}x")
    print(f"\nCompare this to the observed real-world slowdown: "
          f"6419.3s / 2761.7s = {6419.3/2761.7:.2f}x")


if __name__ == "__main__":
    main()