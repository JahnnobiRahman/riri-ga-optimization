#!/usr/bin/env python3
"""
Evaluate B1-fixed: same weights as original B1 (w_e=0.10, w_s=0.80, w_c=0.10)
but with memory_window=512 to disable truncation.

Single-variable change to isolate the truncation defect effect.
"""

import os
import sys
import json
import pandas as pd
from dataclasses import asdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ga.genome import Genome
from evaluation.scoring import evaluate_breakdown
from generation.response_generator import generate_response
from evaluation.risk_labeling import label_risk

# ──────────────────────────────────────────────
# Load validation data
# ──────────────────────────────────────────────

DATA_PATH = "data/phq4_cleaned.csv"
OUT_DIR = "experiments/baseline_comparison"

df = pd.read_csv(DATA_PATH)

# Build user_prompt column (same as baseline_comparison.py)
df["user_prompt"] = (
    df["common_themes"].astype(str).str.strip()
    + " | "
    + df["thought_progression"].astype(str).str.strip()
).str.strip(" |")

df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)

# Build risk_label column using CORRECT label_risk() function
# This includes PHQ-4 thresholds AND keyword detection (Eq. 5 in paper)
df["risk_label"] = df.apply(label_risk, axis=1)

val_df = df.copy()
print(f"Loaded {len(val_df)} validation samples")

# ──────────────────────────────────────────────
# Define B1-fixed genome
# ──────────────────────────────────────────────

print("\n" + "="*60)
print("B1-FIXED: w_e=0.10, w_s=0.80, w_c=0.10, memory_window=512")
print("="*60)

b1_fixed_genome = Genome(
    p_id=0,
    w_e=0.10,
    w_s=0.80,
    w_c=0.10,
    memory_window=512,  # ← changed from 256
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
)
b1_fixed_genome.normalize()

print(f"After normalize(): w_e={b1_fixed_genome.w_e:.4f}, w_s={b1_fixed_genome.w_s:.4f}, w_c={b1_fixed_genome.w_c:.4f}, sum={sum([b1_fixed_genome.w_e, b1_fixed_genome.w_s, b1_fixed_genome.w_c]):.4f}")

# ──────────────────────────────────────────────
# Evaluate B1-fixed
# ──────────────────────────────────────────────

print("\nEvaluating B1-fixed on full validation set...")

# Use evaluate_breakdown (same as baseline_comparison.py)
metrics = evaluate_breakdown(b1_fixed_genome, val_df, n=len(val_df))

mean_empathy = metrics["empathy"]
mean_safety = metrics["safety"]
mean_structure = metrics["structure"]
mean_fitness = metrics["fitness"]

print("\n" + "="*60)
print("B1-FIXED RESULTS")
print("="*60)
print(f"Empathy:   {mean_empathy:.4f}")
print(f"Safety:    {mean_safety:.4f}")
print(f"Structure: {mean_structure:.4f}")
print(f"Fitness:   {mean_fitness:.4f}")
print("="*60)

# Save genome
b1_fixed_path = os.path.join(OUT_DIR, "best_genome_B1_fixed.json")
with open(b1_fixed_path, "w") as f:
    json.dump(asdict(b1_fixed_genome), f, indent=4)
print(f"\n✓ Saved B1-fixed genome to {b1_fixed_path}")

# Save detailed scores
scores_path = os.path.join(OUT_DIR, "b1_fixed_scores.json")
with open(scores_path, "w") as f:
    json.dump({
        "genome": asdict(b1_fixed_genome),
        "scores": {
            "empathy": mean_empathy,
            "safety": mean_safety,
            "structure": mean_structure,
            "fitness": mean_fitness
        },
        "n_samples": len(val_df)
    }, f, indent=4)
print(f"✓ Saved detailed scores to {scores_path}")

# ──────────────────────────────────────────────
# Generate qualitative examples for Table 8
# ──────────────────────────────────────────────

print("\n" + "="*60)
print("QUALITATIVE EXAMPLES (for Table 8)")
print("="*60)

# Find one example of each risk level
low_risk_row = val_df[val_df["risk_label"] == "low"].iloc[0]
mid_risk_row = val_df[val_df["risk_label"] == "mid"].iloc[0]
high_risk_row = val_df[val_df["risk_label"] == "high"].iloc[0]

examples = []

for risk_label, row in [("low", low_risk_row), ("mid", mid_risk_row), ("high", high_risk_row)]:
    user_prompt = row["user_prompt"]
    risk = row["risk_label"]
    
    response = generate_response(user_prompt, risk, b1_fixed_genome)
    
    # Evaluate this single response (create a single-row dataframe)
    temp_df = pd.DataFrame([{
        "user_prompt": user_prompt,
        "risk_label": risk
    }])
    temp_metrics = evaluate_breakdown(b1_fixed_genome, temp_df, n=1)
    
    examples.append({
        "risk_level": risk_label,
        "user_prompt": user_prompt,
        "response": response,
        "scores": {
            "empathy": temp_metrics["empathy"],
            "safety": temp_metrics["safety"],
            "structure": temp_metrics["structure"],
            "fitness": temp_metrics["fitness"]
        }
    })
    
    print(f"\n── {risk_label.upper()} RISK ──")
    print(f"Prompt: {user_prompt[:100]}...")
    print(f"Response: {response[:200]}...")
    print(f"Scores: empathy={temp_metrics['empathy']:.3f}, safety={temp_metrics['safety']:.3f}, structure={temp_metrics['structure']:.3f}, fitness={temp_metrics['fitness']:.3f}")

# Save examples
examples_path = os.path.join(OUT_DIR, "b1_fixed_qualitative_examples.json")
with open(examples_path, "w") as f:
    json.dump(examples, f, indent=2)
print(f"\n✓ Saved qualitative examples to {examples_path}")

print("\n" + "="*60)
print("COMPLETE")
print("="*60)
print(f"\nSummary for paper:")
print(f"B1-fixed (w_e=0.10, w_s=0.80, w_c=0.10, memory_window=512):")
print(f"  Empathy:   {mean_empathy:.4f}")
print(f"  Safety:    {mean_safety:.4f}")
print(f"  Structure: {mean_structure:.4f}")
print(f"  Fitness:   {mean_fitness:.4f}")
