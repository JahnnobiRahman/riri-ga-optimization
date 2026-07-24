"""
baseline_comparison_multiturn.py
==================================
Multi-turn equivalent of baseline_comparison.py. Produces B1-B4 using
the exact same genome definitions as the single-turn script, extended
with history_turns where needed. Evaluates ALL conditions on the same
held-out validation split used for the 5-seed GA replication (session
7 as the split seed), for a fair, methodologically consistent
comparison.

B1 (zero-shot): memory_window=256 kept intentionally, matching
single-turn's B1 exactly, even though 256 is excluded from the GA's
own search space. This lets B1 exhibit the same truncation-driven
safety failure as single-turn's B1, but compounded across a full
multi-turn conversation instead of one prompt -- a real, reportable
characterization of naive deployment risk, not an oversight.

Run from repo root with: PYTHONPATH=src python3 baseline_comparison_multiturn.py
"""

import json
import random
from dataclasses import asdict

import numpy as np

from ga.genome import Genome, random_genome
from ga.runner_multiturn import load_sessions, split_sessions
from evaluation.conversation_scoring import conversation_fitness_over_dataset

SEED = 7
N_RANDOM_RUNS = 5
DATA_PATH = "data/multiturn_cleaned.jsonl"
OUT_DIR = "experiments/baseline_comparison_multiturn"

import os
os.makedirs(OUT_DIR, exist_ok=True)

print("Loading and splitting sessions...")
all_sessions = load_sessions(DATA_PATH)
train_sessions, val_sessions = split_sessions(all_sessions, seed=SEED)
print(f"Train: {len(train_sessions)} | Val: {len(val_sessions)}\n")


# ──────────────────────────────────────────────
# B1: Zero-shot baseline
# ──────────────────────────────────────────────

print("── B1: Zero-shot baseline ──")

zeroshot_genome = Genome(
    p_id=0,
    w_s=0.10,
    w_e=0.10,
    w_c=0.10,
    memory_window=256,   # intentionally kept -- see module docstring
    theta_mid=0.70,
    theta_high=0.95,
    gamma=0.0,
    history_turns=4,      # floor value, matching the "no optimization" convention
                           # already used for w_s/w_e/w_c
)
zeroshot_genome.normalize()

b1_fitness = conversation_fitness_over_dataset(zeroshot_genome, val_sessions)
print(f"B1 (zero-shot) fitness: {b1_fitness:.4f}")


# ──────────────────────────────────────────────
# B2: Fixed balanced seed genome (no GA search)
# ──────────────────────────────────────────────

print("\n── B2: Fixed seed genome (g_bal) ──")

gbal = Genome(
    p_id=1,
    w_s=0.33,
    w_e=0.33,
    w_c=0.34,
    memory_window=512,
    theta_mid=0.55,
    theta_high=0.80,
    gamma=0.10,
    history_turns=12,   # matches get_seed_genomes_multiturn()'s balanced seed
)
gbal.normalize()

b2_fitness = conversation_fitness_over_dataset(gbal, val_sessions)
print(f"B2 (g_bal fixed) fitness: {b2_fitness:.4f}")


# ──────────────────────────────────────────────
# B3: Random genome (mean of N_RANDOM_RUNS)
# ──────────────────────────────────────────────

print(f"\n── B3: Random genome (mean of {N_RANDOM_RUNS} draws) ──")

random_fitness_scores = []
for run in range(N_RANDOM_RUNS):
    rng_seed = SEED + run
    random.seed(rng_seed)
    np.random.seed(rng_seed)
    rg = random_genome()
    fit = conversation_fitness_over_dataset(rg, val_sessions)
    random_fitness_scores.append(fit)
    print(f"  Run {run+1}: fitness={fit:.4f} (genome: w_c={rg.w_c:.3f}, "
          f"gamma={rg.gamma:.3f}, history_turns={rg.history_turns})")

b3_mean = float(np.mean(random_fitness_scores))
b3_std = float(np.std(random_fitness_scores))
print(f"B3 (random) mean±std: {b3_mean:.4f} ± {b3_std:.4f}")


# ──────────────────────────────────────────────
# B4: GA Optimised -- reuse the seed=7 result from the 5-seed replication
# ──────────────────────────────────────────────

print("\n── B4: GA Optimised (from 5-seed replication, seed=7) ──")

with open("experiments/multiturn_p100_seed7_v2split_best_genome.json") as f:
    b4_genome_dict = json.load(f)
b4_genome = Genome(**b4_genome_dict)

b4_fitness = conversation_fitness_over_dataset(b4_genome, val_sessions)
print(f"B4 (GA optimised, seed=7) fitness: {b4_fitness:.4f}")
print(f"  (5-seed replication mean was 0.7047 +/- 0.0007 -- this single-seed "
      f"value may differ slightly, both are valid to report depending on "
      f"which table format you're matching)")


# ──────────────────────────────────────────────
# Summary table
# ──────────────────────────────────────────────

print("\n\n" + "=" * 60)
print("MULTI-TURN BASELINE COMPARISON TABLE")
print("=" * 60)
print(f"{'Condition':<35} {'Fitness':>15}")
print("-" * 60)
print(f"{'B1: Zero-shot (no GA)':<35} {b1_fitness:>15.4f}")
print(f"{'B2: Fixed seed g_bal (no GA)':<35} {b2_fitness:>15.4f}")
print(f"{'B3: Random genome (mean, n=5)':<35} {b3_mean:>15.4f} ± {b3_std:.4f}")
print(f"{'B4: GA Optimised (seed=7)':<35} {b4_fitness:>15.4f}")
print(f"{'B4: GA Optimised (5-seed mean)':<35} {'0.7047':>15} ± 0.0007")

results = {
    "b1_zeroshot": {"fitness": b1_fitness, "genome": asdict(zeroshot_genome)},
    "b2_fixed_gbal": {"fitness": b2_fitness, "genome": asdict(gbal)},
    "b3_random": {"mean": b3_mean, "std": b3_std, "individual_runs": random_fitness_scores},
    "b4_ga_optimised_seed7": {"fitness": b4_fitness, "genome": asdict(b4_genome)},
    "b4_ga_optimised_5seed_mean": 0.7047,
    "b4_ga_optimised_5seed_std": 0.0007,
}

with open(f"{OUT_DIR}/baseline_comparison_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {OUT_DIR}/baseline_comparison_results.json")