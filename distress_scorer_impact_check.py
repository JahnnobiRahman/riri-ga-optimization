"""
distress_scorer_impact_check.py (v3 -- lookbehind-based fix)

Re-verifies the corrected fix against:
  1. The original bug (রক্ত inside বিরক্তিবোধ) -- must now correctly fail to match.
  2. Stem preservation (suicid/hopeless) -- must still match their variants.
  3. The newly-noticed "cutting" anomaly from the v2 check (matched
     something in a financial-hardship prompt with no obvious cutting-
     related content) -- printed in full this time so it can be read
     directly rather than guessed at.

Run from repo root with: python3 distress_scorer_impact_check.py
"""

import re
import pandas as pd

DATA_PATH = "data/phq4_cleaned.csv"
TAU_H = 0.65

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


def compute_distress_score_OLD(prompt_text: str):
    if pd.isna(prompt_text):
        return 0.0, []
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
    return float(score), matched


_BENGALI_BLOCK = "\u0980-\u09FF"
_COMPILED_PATTERNS = {
    k: re.compile(r"(?<![\w" + _BENGALI_BLOCK + r"])" + re.escape(k.lower()))
    for k in DISTRESS_KEYWORDS
}


def compute_distress_score_NEW(prompt_text: str):
    if pd.isna(prompt_text):
        return 0.0, []
    text = str(prompt_text).lower()
    score = 0.0
    matched = []
    for keyword, weight in DISTRESS_KEYWORDS.items():
        if _COMPILED_PATTERNS[keyword].search(text):
            score += weight
            matched.append(keyword)
    score = min(1.0, score)
    if len(matched) > 3:
        score = max(score - 0.05, 0.0)
    return float(score), matched


def main():
    print("=== Sanity checks ===")
    test_cases = [
        ("suicidal ideation expressed", "suicid", True, "should still match (stem)"),
        ("feelings of hopelessness", "hopeless", True, "should still match (stem)"),
        ("সবাই বিরক্তিবোধ করবে", "রক্ত", False, "should NOT match (embedded false positive)"),
        ("রক্ত দিতে হবে", "রক্ত", True, "should still match (standalone word)"),
    ]
    all_passed = True
    for text, expected_keyword, should_match, note in test_cases:
        score, matched = compute_distress_score_NEW(text)
        actually_matched = expected_keyword in matched
        status = "PASS" if actually_matched == should_match else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  [{status}] {note}: {text!r} -> matched={matched}")

    if not all_passed:
        print("\nSTOP: not all sanity checks passed. Do not proceed to the full "
              "dataset comparison or apply this fix until they do.")
        return

    print("\nAll sanity checks passed. Proceeding to full dataset comparison.\n")
    print("=== Full dataset comparison ===")
    df = pd.read_csv(DATA_PATH)

    if "common_themes" in df.columns and "thought_progression" in df.columns:
        prompts = (df["common_themes"].fillna("") + " | " + df["thought_progression"].fillna(""))
    elif "user_prompt" in df.columns:
        prompts = df["user_prompt"].fillna("")
    else:
        raise RuntimeError(f"Couldn't find expected prompt columns. Available: {list(df.columns)}")

    n_total = len(prompts)
    n_changed = 0
    n_crossed_differently = 0
    n_lost_signal = 0
    n_gained_signal = 0
    examples_lost = []
    examples_gained = []

    for prompt in prompts:
        old_score, old_matched = compute_distress_score_OLD(prompt)
        new_score, new_matched = compute_distress_score_NEW(prompt)

        if abs(old_score - new_score) > 1e-9:
            n_changed += 1
            old_crossed = old_score > TAU_H
            new_crossed = new_score > TAU_H
            if old_crossed != new_crossed:
                n_crossed_differently += 1
                if old_crossed and not new_crossed:
                    n_lost_signal += 1
                    if len(examples_lost) < 10:
                        examples_lost.append((prompt, old_score, old_matched, new_score, new_matched))
                elif new_crossed and not old_crossed:
                    n_gained_signal += 1
                    if len(examples_gained) < 10:
                        examples_gained.append((prompt, old_score, old_matched, new_score, new_matched))

    print(f"Total prompts: {n_total}")
    print(f"Changed score: {n_changed} ({100*n_changed/n_total:.2f}%)")
    print(f"Crossed tau_h differently: {n_crossed_differently} ({100*n_crossed_differently/n_total:.2f}%)")
    print(f"  -- LOST signal (should be ~0): {n_lost_signal}")
    print(f"  -- Fixed false positives (expected to be >0): {n_gained_signal}")

    if examples_lost:
        print(f"\n*** LOST SIGNAL EXAMPLES (investigate each one) ***")
        for prompt, os, om, ns, nm in examples_lost:
            print(f"\n  Full prompt: {prompt!r}")
            print(f"    OLD: {os:.3f} matched={om} -> NEW: {ns:.3f} matched={nm}")

    if examples_gained:
        print(f"\n*** FIXED FALSE POSITIVES ***")
        for prompt, os, om, ns, nm in examples_gained:
            print(f"\n  Full prompt: {prompt!r}")
            print(f"    OLD: {os:.3f} matched={om} -> NEW: {ns:.3f} matched={nm}")


if __name__ == "__main__":
    main()