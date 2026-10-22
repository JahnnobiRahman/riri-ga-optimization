#!/usr/bin/env python3
"""
Debug script to check B1 genome weights as passed to generator.
"""

import json
import pandas as pd
from src.ga.genome import Genome
from src.evaluation.scoring import fitness, score_structure
from src.evaluation.risk_labeling import label_risk
from src.generation.response_generator import generate_response

print("="*60)
print("B1 GENOME WEIGHTS DEBUG")
print("="*60)

# 1. Load saved B1 genome
print("\n1. Saved B1 genome from best_genome_B1.json:")
with open("experiments/baseline_comparison/best_genome_B1.json") as f:
    g_b1_data = json.load(f)
g_b1 = Genome(**g_b1_data)

print(f"   w_e (empathy):   {g_b1.w_e:.6f}")
print(f"   w_s (safety):    {g_b1.w_s:.6f}")
print(f"   w_c (structure): {g_b1.w_c:.6f}")
print(f"   SUM:             {g_b1.w_e + g_b1.w_s + g_b1.w_c:.6f}")
print(f"   memory_window:   {g_b1.memory_window}")
print(f"   p_id:            {g_b1.p_id}")

# 2. Create a fresh B1 genome as per baseline_comparison.py
print("\n2. Fresh B1 genome construction (as in baseline_comparison.py):")
g_b1_fresh = Genome(
    p_id=0,
    w_s=0.10,
    w_e=0.10,
    w_c=0.10,
    memory_window=256,
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
)
print(f"   BEFORE normalize():")
print(f"   w_e={g_b1_fresh.w_e:.6f}, w_s={g_b1_fresh.w_s:.6f}, w_c={g_b1_fresh.w_c:.6f}, sum={g_b1_fresh.w_e + g_b1_fresh.w_s + g_b1_fresh.w_c:.6f}")

g_b1_fresh.normalize()
print(f"   AFTER normalize():")
print(f"   w_e={g_b1_fresh.w_e:.6f}, w_s={g_b1_fresh.w_s:.6f}, w_c={g_b1_fresh.w_c:.6f}, sum={g_b1_fresh.w_e + g_b1_fresh.w_s + g_b1_fresh.w_c:.6f}")

# 3. Test if they're identical
print("\n3. Comparison:")
if (abs(g_b1.w_e - g_b1_fresh.w_e) < 1e-6 and 
    abs(g_b1.w_s - g_b1_fresh.w_s) < 1e-6 and 
    abs(g_b1.w_c - g_b1_fresh.w_c) < 1e-6):
    print("   ✓ Saved genome MATCHES fresh construction")
else:
    print("   ✗ Saved genome DIFFERS from fresh construction")

# 4. Generate a response and trace what genome is used
print("\n4. Testing response generation with saved B1 genome:")

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
df = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
split = int(0.8 * len(df))
val_df = df.iloc[split:].reset_index(drop=True)

test_row = val_df.iloc[0]
print(f"   Test prompt: {test_row['user_prompt'][:60]}...")
print(f"   Risk: {test_row['risk_label']}")

# Patch generate_response to print genome weights
import src.generation.response_generator as rg
original_generate = rg.generate_response

def debug_generate_response(user_text, risk_label, g, escalate_override=None):
    print(f"\n   → generate_response called with genome:")
    print(f"      w_e={g.w_e:.6f}, w_s={g.w_s:.6f}, w_c={g.w_c:.6f}, sum={g.w_e + g.w_s + g.w_c:.6f}")
    print(f"      p_id={g.p_id}, memory_window={g.memory_window}")
    return original_generate(user_text, risk_label, g, escalate_override)

rg.generate_response = debug_generate_response

# Generate response
resp = generate_response(
    test_row["user_prompt"],
    test_row["risk_label"],
    g_b1,
    escalate_override=None
)

print(f"\n   Generated response length: {len(resp)} chars")
print(f"   Structure score: {score_structure(resp):.3f}")

print("\n" + "="*60)
