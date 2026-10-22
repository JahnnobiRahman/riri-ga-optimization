#!/usr/bin/env python3
"""
Add B1-fixed to the five-seed significance test.

Evaluates B1-fixed (memory_window=512) on the same five seeds as the
existing GA vs B1 vs B2 significance test.
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "src")

from evaluation.risk_labeling import label_risk
from evaluation.scoring import evaluate_breakdown
from ga.genome import Genome

# ──────────────────────────────────────────────
# Load dataset (same as baseline_comparison.py)
# ──────────────────────────────────────────────

DATA_PATH = "data/phq4_cleaned.csv"
OUT_DIR = "experiments/baseline_comparison"

df = pd.read_csv(DATA_PATH)

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in df.columns:
        df[col] = ""

if "total_score" not in df.columns:
    df["total_score"] = 0

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    df[col] = df[col].fillna("")
df["total_score"] = df["total_score"].fillna(0)

df["risk_label"] = df.apply(label_risk, axis=1)

df["user_prompt"] = (
    df["common_themes"].astype(str).str.strip()
    + " | "
    + df["thought_progression"].astype(str).str.strip()
).str.strip(" |")

df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)

# 80/20 split with shuffle (matches baseline_comparison.py line 82)
SEED = 7
df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
train_size = int(0.8 * len(df))
train_df = df.iloc[:train_size].reset_index(drop=True)
val_df = df.iloc[train_size:].reset_index(drop=True)

print(f"Loaded dataset: N={len(df)} (train={len(train_df)}, val={len(val_df)})")

# ──────────────────────────────────────────────
# Define genomes
# ──────────────────────────────────────────────

# B1 (original buggy version with memory_window=256)
b1_genome = Genome(
    p_id=0,
    w_e=0.10,
    w_s=0.80,
    w_c=0.10,
    memory_window=256,
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
)
b1_genome.normalize()

# B1-fixed (memory_window=512, truncation disabled)
b1_fixed_genome = Genome(
    p_id=0,
    w_e=0.10,
    w_s=0.80,
    w_c=0.10,
    memory_window=512,  # ← ONLY CHANGE
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
)
b1_fixed_genome.normalize()

# B2 (fixed seed g_bal)
gbal = Genome(
    p_id=1,
    w_e=0.33,
    w_s=0.33,
    w_c=0.33,
    memory_window=512,
    theta_mid=0.55,
    theta_high=0.85,
    gamma=0.15,
)
gbal.normalize()

def score_genome(g: Genome, val: pd.DataFrame, n: int = 400) -> dict:
    """Returns evaluate_breakdown dict for a genome on val subset."""
    return evaluate_breakdown(g, val, n=n)

# ──────────────────────────────────────────────
# Load existing GA results and run B1-fixed
# ──────────────────────────────────────────────

print("\n" + "="*60)
print("FIVE-SEED SIGNIFICANCE TEST: Adding B1-fixed")
print("="*60)

seed_genome_dir = os.path.join(OUT_DIR, "seed_genomes")
ga_fitness_runs = []
b1_fitness_runs = []
b1_fixed_fitness_runs = []
b2_fitness_runs = []

for run in range(1, 6):
    seed_r = run * 13  # seeds: 13, 26, 39, 52, 65
    
    # Load existing GA result
    genome_path = os.path.join(seed_genome_dir, f"best_genome_seed_{seed_r}.json")
    with open(genome_path, "r") as f:
        ga_genome_dict = json.load(f)
    
    ga_genome = Genome(**ga_genome_dict)
    
    # Evaluate all genomes with same seed
    random.seed(seed_r)
    np.random.seed(seed_r)
    
    ga_m = score_genome(ga_genome, val_df)
    ga_fitness_runs.append(ga_m["fitness"])
    
    random.seed(seed_r)
    np.random.seed(seed_r)
    b1_m = score_genome(b1_genome, val_df)
    b1_fitness_runs.append(b1_m["fitness"])
    
    random.seed(seed_r)
    np.random.seed(seed_r)
    b1_fixed_m = score_genome(b1_fixed_genome, val_df)
    b1_fixed_fitness_runs.append(b1_fixed_m["fitness"])
    
    random.seed(seed_r)
    np.random.seed(seed_r)
    b2_m = score_genome(gbal, val_df)
    b2_fitness_runs.append(b2_m["fitness"])
    
    print(f"Seed {seed_r:2d}: GA={ga_m['fitness']:.4f}  B1={b1_m['fitness']:.4f}  "
          f"B1-fixed={b1_fixed_m['fitness']:.4f}  B2={b2_m['fitness']:.4f}")

# Statistical tests
stat_b1, p_b1 = stats.wilcoxon(ga_fitness_runs, b1_fitness_runs, alternative='greater')
stat_b1_fixed, p_b1_fixed = stats.wilcoxon(ga_fitness_runs, b1_fixed_fitness_runs, alternative='greater')
stat_b2, p_b2 = stats.wilcoxon(ga_fitness_runs, b2_fitness_runs, alternative='greater')

print("\n" + "="*60)
print("STATISTICAL TESTS")
print("="*60)
print(f"Wilcoxon GA vs B1:         statistic={stat_b1:.3f}, p={p_b1:.4f}")
print(f"Wilcoxon GA vs B1-fixed:   statistic={stat_b1_fixed:.3f}, p={p_b1_fixed:.4f}")
print(f"Wilcoxon GA vs B2:         statistic={stat_b2:.3f}, p={p_b2:.4f}")

# Effect sizes (Cohen's d)
def cohens_d(a, b):
    na, nb = len(a), len(b)
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled_std = np.sqrt(((na - 1) * va + (nb - 1) * vb) / (na + nb - 2))
    return (np.mean(a) - np.mean(b)) / pooled_std if pooled_std > 0 else 0

d_b1 = cohens_d(ga_fitness_runs, b1_fitness_runs)
d_b1_fixed = cohens_d(ga_fitness_runs, b1_fixed_fitness_runs)
d_b2 = cohens_d(ga_fitness_runs, b2_fitness_runs)

print(f"\nCohen's d:")
print(f"  GA vs B1:         {d_b1:.3f}")
print(f"  GA vs B1-fixed:   {d_b1_fixed:.3f}")
print(f"  GA vs B2:         {d_b2:.3f}")

# Save results
results = {
    "ga_fitness_runs": ga_fitness_runs,
    "b1_fitness_runs": b1_fitness_runs,
    "b1_fixed_fitness_runs": b1_fixed_fitness_runs,
    "b2_fitness_runs": b2_fitness_runs,
    "wilcoxon_ga_vs_b1": {"statistic": float(stat_b1), "p_value": float(p_b1)},
    "wilcoxon_ga_vs_b1_fixed": {"statistic": float(stat_b1_fixed), "p_value": float(p_b1_fixed)},
    "wilcoxon_ga_vs_b2": {"statistic": float(stat_b2), "p_value": float(p_b2)},
    "cohens_d_b1": float(d_b1),
    "cohens_d_b1_fixed": float(d_b1_fixed),
    "cohens_d_b2": float(d_b2),
}

output_path = os.path.join(OUT_DIR, "b1_fixed_significance_test.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Saved results to {output_path}")
