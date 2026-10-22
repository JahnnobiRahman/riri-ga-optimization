#!/usr/bin/env python3
"""
Compare exact response text from two different code paths.
"""

import json
import pandas as pd
from src.ga.genome import Genome
from src.evaluation.scoring import score_structure, fitness
from src.evaluation.risk_labeling import label_risk
from src.generation.response_generator import generate_response

# Load B1 genome
with open("experiments/baseline_comparison/best_genome_B1.json") as f:
    g_b1_data = json.load(f)
g_b1 = Genome(**g_b1_data)

# Load data
df = pd.read_csv("data/phq4_cleaned.csv")

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].fillna("")

if "total_score" not in df.columns:
    df["total_score"] = 0
df["total_score"] = df["total_score"].fillna(0)

df["risk_label"] = df.apply(label_risk, axis=1)

df["user_prompt"] = (
    df["common_themes"].astype(str).str.strip()
    + " | "
    + df["thought_progression"].astype(str).str.strip()
).str.strip(" |")

df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)

# Use same split
df = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
split = int(0.8 * len(df))
val_df = df.iloc[split:].reset_index(drop=True)

print("="*60)
print("RESPONSE CONSISTENCY CHECK")
print("="*60)
print("\nTesting 5 prompts, generating 3 times each...\n")

test_prompts = val_df.head(5)

for idx, row in test_prompts.iterrows():
    print(f"\nPrompt {idx + 1}: {row['user_prompt'][:60]}...")
    print(f"Risk: {row['risk_label']}")
    
    responses = []
    scores = []
    
    for run in range(3):
        resp = generate_response(
            row["user_prompt"],
            row["risk_label"],
            g_b1,
            escalate_override=None
        )
        struct_score = score_structure(resp)
        responses.append(resp)
        scores.append(struct_score)
        print(f"  Run {run+1}: len={len(resp):3d} chars, structure={struct_score:.3f}")
    
    # Check if any are identical
    if responses[0] == responses[1] == responses[2]:
        print("  ✓ ALL IDENTICAL")
    else:
        print("  ✗ DIFFERENT responses")
        # Show first 100 chars of each
        for i, r in enumerate(responses):
            print(f"    Run {i+1}: {r[:80]}...")

print("\n" + "="*60)
