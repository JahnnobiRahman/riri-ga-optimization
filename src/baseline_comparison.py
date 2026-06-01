"""
baseline_comparison.py
======================
Gap 2 fix: Baseline comparison experiment for EvoRiri paper.

Produces Table 2 with FOUR conditions:
  B1 — Zero-shot (raw template, no genome weights)
  B2 — Seeded genome g_bal (no GA search)
  B3 — Random genome (mean of 5 random draws)
  B4 — GA Optimised (your existing best_g)

Drop this file into your project root (same level as main_ga_riri.py)
and run:  python baseline_comparison.py

Requirements: your existing src/ layout must be on sys.path.
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append("src")

from evaluation.risk_labeling import label_risk
from evaluation.scoring import evaluate_breakdown, fitness
from ga.genome import Genome, random_genome
from ga.runner import run_ga
from generation.response_generator import generate_response

# ──────────────────────────────────────────────
# 0) Reproducibility
# ──────────────────────────────────────────────

SEED = 7
random.seed(SEED)
np.random.seed(SEED)

N_RANDOM_RUNS = 5   # how many random genomes to average for B3
N_EVAL        = 400  # validation rows to score (matches your existing experiments)

# ──────────────────────────────────────────────
# 1) Load & prepare dataset  (mirrors main_ga_riri.py)
# ──────────────────────────────────────────────

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "phq4_cleaned.csv")

print("Loading dataset...")
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

# Same 80/20 split as main_ga_riri.py
df       = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
split    = int(0.8 * len(df))
train_df = df.iloc[:split].reset_index(drop=True)
val_df   = df.iloc[split:].reset_index(drop=True)

print(f"Train: {len(train_df)} | Val: {len(val_df)}")

# ──────────────────────────────────────────────
# 2) Helper: score a genome and return dict
# ──────────────────────────────────────────────

def score_genome(g: Genome, val: pd.DataFrame, n: int = N_EVAL) -> dict:
    """Returns evaluate_breakdown dict for a genome on val subset."""
    return evaluate_breakdown(g, val, n=n)

# ──────────────────────────────────────────────
# 3) B1 — Zero-shot baseline
#
# Definition: a fixed genome with equal weights and the
# LOWEST structure enforcement (w_c = 0.10 minimum floor)
# and no risk-aware escalation thresholds active.
# This mimics "just ask the LLM with a basic prompt" —
# in your template-based system it means no genome tuning at all.
# ──────────────────────────────────────────────

print("\n── B1: Zero-shot baseline ──")

zeroshot_genome = Genome(
    p_id=0,           # simplest template: "Be safe, warm, supportive"
    w_s=0.10,         # minimum safety weight (floor)
    w_e=0.10,         # minimum empathy weight (floor)
    w_c=0.10,         # minimum structure weight → very little structure
    memory_window=256, # short context, minimal output
    theta_mid=0.70,   # high threshold → escalation rarely triggers
    theta_high=0.95   # very high threshold → almost never escalates
)
zeroshot_genome.normalize()

b1_metrics = score_genome(zeroshot_genome, val_df)
print("B1 (zero-shot):", b1_metrics)

# ──────────────────────────────────────────────
# 4) B2 — Fixed seed genome g_bal (no GA search)
#
# This is the balanced seed used to initialise the GA.
# Comparing against it shows that GA *search* adds value
# beyond just starting from a good initial point.
# ──────────────────────────────────────────────

print("\n── B2: Fixed seed genome (g_bal) ──")

gbal = Genome(
    p_id=1,
    w_s=0.33,
    w_e=0.33,
    w_c=0.34,
    memory_window=512,
    theta_mid=0.55,
    theta_high=0.80
)
gbal.normalize()

b2_metrics = score_genome(gbal, val_df)
print("B2 (g_bal fixed):", b2_metrics)

# ──────────────────────────────────────────────
# 5) B3 — Random genome (average of N_RANDOM_RUNS)
#
# Shows GA beats chance — random parameter selection
# cannot reliably find good policies.
# ──────────────────────────────────────────────

print(f"\n── B3: Random genome (mean of {N_RANDOM_RUNS} draws) ──")

random_fitness_scores  = []
random_empathy_scores  = []
random_safety_scores   = []
random_structure_scores = []

for run in range(N_RANDOM_RUNS):
    rg = random_genome()
    rng_seed = SEED + run
    random.seed(rng_seed)
    np.random.seed(rng_seed)
    m = score_genome(rg, val_df)
    random_fitness_scores.append(m["fitness"])
    random_empathy_scores.append(m["empathy"])
    random_safety_scores.append(m["safety"])
    random_structure_scores.append(m["structure"])
    print(f"  Run {run+1}: fitness={m['fitness']:.4f}")

b3_metrics = {
    "empathy":   float(np.mean(random_empathy_scores)),
    "safety":    float(np.mean(random_safety_scores)),
    "structure": float(np.mean(random_structure_scores)),
    "fitness":   float(np.mean(random_fitness_scores)),
}
b3_std = {
    "empathy":   float(np.std(random_empathy_scores)),
    "safety":    float(np.std(random_safety_scores)),
    "structure": float(np.std(random_structure_scores)),
    "fitness":   float(np.std(random_fitness_scores)),
}
print("B3 (random) mean:", b3_metrics)
print("B3 (random) std: ", b3_std)

# ──────────────────────────────────────────────
# 6) B4 — GA Optimised (run full GA, same settings as paper)
# ──────────────────────────────────────────────

print("\n── B4: GA Optimised ──")

best_g, log = run_ga(
    train_df,
    pop_size=100,
    generations=20,
    eval_n=600,
    seed=SEED
)

b4_metrics = score_genome(best_g, val_df)
print("B4 (GA optimised):", b4_metrics)

# ──────────────────────────────────────────────
# 7) Statistical significance tests
#
# Wilcoxon signed-rank test: B4 vs each baseline
# Run 5 independent GA seeds and collect per-run scores
# to get proper distributions for testing.
# ──────────────────────────────────────────────

print("\n── Statistical significance tests (5 independent GA runs) ──")

ga_fitness_runs = []
b1_fitness_runs = []
b2_fitness_runs = []

for run in range(1, 6):
    seed_r = run * 13  # different seeds

    # GA run
    g_r, _ = run_ga(train_df, pop_size=100, generations=20, eval_n=600, seed=seed_r)
    ga_m   = score_genome(g_r, val_df)
    ga_fitness_runs.append(ga_m["fitness"])

    # B1 always same (deterministic fixed genome) — slight noise from eval sample
    random.seed(seed_r)
    np.random.seed(seed_r)
    b1_m = score_genome(zeroshot_genome, val_df)
    b1_fitness_runs.append(b1_m["fitness"])

    # B2 always same fixed genome
    random.seed(seed_r)
    np.random.seed(seed_r)
    b2_m = score_genome(gbal, val_df)
    b2_fitness_runs.append(b2_m["fitness"])

    print(f"  Seed {seed_r}: GA={ga_m['fitness']:.4f}  B1={b1_m['fitness']:.4f}  B2={b2_m['fitness']:.4f}")

# Wilcoxon tests
stat_b1, p_b1 = stats.wilcoxon(ga_fitness_runs, b1_fitness_runs, alternative='greater')
stat_b2, p_b2 = stats.wilcoxon(ga_fitness_runs, b2_fitness_runs, alternative='greater')

print(f"\nWilcoxon GA vs B1 (zero-shot):    statistic={stat_b1:.3f}, p={p_b1:.4f}")
print(f"Wilcoxon GA vs B2 (fixed g_bal):  statistic={stat_b2:.3f}, p={p_b2:.4f}")

# ──────────────────────────────────────────────
# 8) Build and print the final comparison table
# ──────────────────────────────────────────────

print("\n\n══════════════════════════════════════════════════")
print("TABLE 2: Baseline vs Optimised Performance")
print("══════════════════════════════════════════════════")

table = pd.DataFrame([
    {
        "Condition":       "B1: Zero-shot (no GA)",
        "Empathy Score":   round(b1_metrics["empathy"],   3),
        "Safety Score":    round(b1_metrics["safety"],    3),
        "Structure Score": round(b1_metrics["structure"], 3),
        "Fitness Score":   round(b1_metrics["fitness"],   3),
        "vs GA (p-value)": f"p={p_b1:.4f}",
    },
    {
        "Condition":       "B2: Fixed seed g_bal (no GA)",
        "Empathy Score":   round(b2_metrics["empathy"],   3),
        "Safety Score":    round(b2_metrics["safety"],    3),
        "Structure Score": round(b2_metrics["structure"], 3),
        "Fitness Score":   round(b2_metrics["fitness"],   3),
        "vs GA (p-value)": f"p={p_b2:.4f}",
    },
    {
        "Condition":       f"B3: Random genome (mean±std, n={N_RANDOM_RUNS})",
        "Empathy Score":   f"{b3_metrics['empathy']:.3f} ± {b3_std['empathy']:.3f}",
        "Safety Score":    f"{b3_metrics['safety']:.3f} ± {b3_std['safety']:.3f}",
        "Structure Score": f"{b3_metrics['structure']:.3f} ± {b3_std['structure']:.3f}",
        "Fitness Score":   f"{b3_metrics['fitness']:.3f} ± {b3_std['fitness']:.3f}",
        "vs GA (p-value)": "—",
    },
    {
        "Condition":       "B4: GA Optimised (proposed)",
        "Empathy Score":   round(b4_metrics["empathy"],   3),
        "Safety Score":    round(b4_metrics["safety"],    3),
        "Structure Score": round(b4_metrics["structure"], 3),
        "Fitness Score":   round(b4_metrics["fitness"],   3),
        "vs GA (p-value)": "—",
    },
])

print(table.to_string(index=False))

# ──────────────────────────────────────────────
# 9) Save results
# ──────────────────────────────────────────────

OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", "baseline_comparison")
os.makedirs(OUT_DIR, exist_ok=True)

table.to_csv(os.path.join(OUT_DIR, "baseline_comparison_table.csv"), index=False)

stats_summary = {
    "wilcoxon_GA_vs_B1": {"statistic": float(stat_b1), "p_value": float(p_b1)},
    "wilcoxon_GA_vs_B2": {"statistic": float(stat_b2), "p_value": float(p_b2)},
    "ga_fitness_runs":   ga_fitness_runs,
    "b1_fitness_runs":   b1_fitness_runs,
    "b2_fitness_runs":   b2_fitness_runs,
    "b3_mean_fitness":   b3_metrics["fitness"],
    "b3_std_fitness":    b3_std["fitness"],
}

with open(os.path.join(OUT_DIR, "stats_summary.json"), "w") as f:
    json.dump(stats_summary, f, indent=4)

print(f"\nSaved results to: {OUT_DIR}")
print("  baseline_comparison_table.csv")
print("  stats_summary.json")

# ──────────────────────────────────────────────
# 10) Best genome summary (for paper Section 3.6 hyperparameter table)
# ──────────────────────────────────────────────

print("\n── Best GA genome (for hyperparameter table in paper) ──")
print(f"  p_id:          {best_g.p_id}")
print(f"  w_e (empathy): {best_g.w_e:.4f}")
print(f"  w_s (safety):  {best_g.w_s:.4f}")
print(f"  w_c (structure): {best_g.w_c:.4f}")
print(f"  theta_mid:     {best_g.theta_mid:.4f}")
print(f"  theta_high:    {best_g.theta_high:.4f}")
print(f"  memory_window: {best_g.memory_window}")