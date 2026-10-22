#!/usr/bin/env python3
"""
Equal-budget random search over the full genome space, matching the GA's
implicit evaluation budget of P=100 x T=20 = 2000 genome evaluations per run.

Scoring path (must match five-seed GA significance / Table 6):
  evaluate_breakdown(g, val_df, n=400) on the seed-7 80/20 validation split.

Usage:
  python random_search_equal_budget.py --seeds 42          # timed gate
  python random_search_equal_budget.py                     # all five seeds
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from dataclasses import asdict
from typing import List, Optional

import pandas as pd

sys.path.insert(0, "src")

from ga.genome import Genome
from evaluation.scoring import evaluate_breakdown
from evaluation.risk_labeling import label_risk

# --- Genome bounds, matching Table 2 / the GA's search space ---
GENOME_BOUNDS = {
    "w_e": (0.10, 1.0),
    "w_s": (0.10, 1.0),
    "w_c": (0.10, 1.0),
    "theta_mid": (0.40, 0.70),
    "theta_high": (0.70, 0.95),
    "gamma": (0.0, 0.2),
}
D_CHOICES = [0, 1, 2]
M_CHOICES = [256, 512, 768, 1024]

N_EVALUATIONS = 2000
N_EVAL_PROMPTS = 400
VAL_SPLIT_SEED = 7
DEFAULT_RUN_SEEDS = [42, 142, 242, 342, 442]

# GA five-seed band (direct re-score under same path) for summary only
GA_MEAN = 0.6992537903225806
GA_BAND = [0.6948969758064517, 0.7026679435483872]

OUT_DIR = "experiments/baseline_comparison"
OUT_PATH = os.path.join(OUT_DIR, "random_search_five_seed.json")


def load_validation_set() -> pd.DataFrame:
    """Same 80/20 shuffled holdout as baseline_comparison.py (seed 7)."""
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

    df = df.sample(frac=1.0, random_state=VAL_SPLIT_SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    return df.iloc[split:].reset_index(drop=True)


def sample_random_genome(rng: random.Random) -> Genome:
    genome = Genome(
        p_id=rng.choice(D_CHOICES),
        w_e=rng.uniform(*GENOME_BOUNDS["w_e"]),
        w_s=rng.uniform(*GENOME_BOUNDS["w_s"]),
        w_c=rng.uniform(*GENOME_BOUNDS["w_c"]),
        memory_window=rng.choice(M_CHOICES),
        theta_mid=rng.uniform(*GENOME_BOUNDS["theta_mid"]),
        theta_high=rng.uniform(*GENOME_BOUNDS["theta_high"]),
        gamma=rng.uniform(*GENOME_BOUNDS["gamma"]),
    )
    genome.normalize()
    return genome


def score_genome(g: Genome, val_df: pd.DataFrame) -> float:
    """Same path as score_genome / five-seed significance: n=400 breakdown."""
    return float(evaluate_breakdown(g, val_df, n=N_EVAL_PROMPTS)["fitness"])


def genome_dict(g: Genome) -> dict:
    return asdict(g)


def run_one_seed(seed: int, val_df: pd.DataFrame) -> dict:
    rng = random.Random(seed)
    best_fitness = -float("inf")
    best_genome = None
    all_fitnesses: List[float] = []
    # (fitness, genome_dict) candidates for top-10
    ranked: List[tuple] = []

    t0 = time.perf_counter()
    for i in range(N_EVALUATIONS):
        genome = sample_random_genome(rng)
        fit = score_genome(genome, val_df)
        all_fitnesses.append(fit)
        ranked.append((fit, genome_dict(genome)))

        if fit > best_fitness:
            best_fitness = fit
            best_genome = genome
            print(
                f"  [seed {seed} eval {i+1}/{N_EVALUATIONS}] NEW BEST: "
                f"fitness={fit:.4f} (w_c={genome.w_c:.3f}, m={genome.memory_window})"
            )

        if (i + 1) % 200 == 0:
            mu = statistics.fmean(all_fitnesses)
            sd = statistics.pstdev(all_fitnesses)
            elapsed = time.perf_counter() - t0
            print(
                f"  ...seed {seed} checkpoint {i+1}/{N_EVALUATIONS}: "
                f"best={best_fitness:.4f}, mean={mu:.4f} ± {sd:.4f}, "
                f"elapsed={elapsed:.1f}s"
            )

    elapsed = time.perf_counter() - t0
    mu = statistics.fmean(all_fitnesses)
    sd = statistics.pstdev(all_fitnesses)
    ranked.sort(key=lambda x: x[0], reverse=True)
    top10 = [{"fitness": f, "genome": g} for f, g in ranked[:10]]

    return {
        "seed": seed,
        "n_evaluations": N_EVALUATIONS,
        "n_eval_prompts": N_EVAL_PROMPTS,
        "elapsed_seconds": elapsed,
        "best_fitness": best_fitness,
        "best_genome": genome_dict(best_genome),
        "mean_fitness_all_draws": mu,
        "std_fitness_all_draws": sd,
        "top10": top10,
        "all_fitnesses": all_fitnesses,
    }


def provenance() -> dict:
    return {
        "scoring": "evaluate_breakdown",
        "n_eval_prompts": N_EVAL_PROMPTS,
        "n_draws_per_run": N_EVALUATIONS,
        "val_split_seed": VAL_SPLIT_SEED,
        "split": "80/20 shuffled then holdout (no stratification)",
        "stratification": None,
        "data_path": "data/phq4_cleaned.csv",
        "genome_bounds": GENOME_BOUNDS,
        "d_choices": D_CHOICES,
        "m_choices": M_CHOICES,
        "normalize": "Genome.normalize() after uniform raw draw (same as GA)",
        "ga_comparison_band": {"mean": GA_MEAN, "min": GA_BAND[0], "max": GA_BAND[1]},
    }


def main(seeds: Optional[List[int]] = None):
    seeds = seeds if seeds is not None else DEFAULT_RUN_SEEDS

    print("=" * 70)
    print("RANDOM SEARCH — equal budget, evaluate_breakdown(n=400)")
    print(f"Seeds: {seeds} | draws/run: {N_EVALUATIONS}")
    print("=" * 70)

    val_df = load_validation_set()
    assert len(val_df) == 575, f"expected 575-row val split, got {len(val_df)}"
    print(f"Val rows: {len(val_df)} (assert OK) | n_eval_prompts={N_EVAL_PROMPTS}")

    runs = []
    for seed in seeds:
        print(f"\n── Run seed={seed} ──")
        run = run_one_seed(seed, val_df)
        runs.append(run)
        print(
            f"  DONE seed {seed}: best={run['best_fitness']:.4f} "
            f"mean={run['mean_fitness_all_draws']:.4f} ± "
            f"{run['std_fitness_all_draws']:.4f} "
            f"elapsed={run['elapsed_seconds']:.1f}s"
        )
        if seed == seeds[0] and run["elapsed_seconds"] > 600:
            print(
                "\n*** TIMING GATE FAILED: first seed exceeded 10 minutes. "
                "Stopping before remaining seeds. ***"
            )
            break

    maxima = [r["best_fitness"] for r in runs]
    summary = {
        "maxima": maxima,
        "n_runs_completed": len(runs),
        "n_exceed_ga_mean": sum(1 for m in maxima if m > GA_MEAN),
        "n_exceed_ga_band_max": sum(1 for m in maxima if m > GA_BAND[1]),
        "n_within_ga_band": sum(1 for m in maxima if GA_BAND[0] <= m <= GA_BAND[1]),
    }

    # Slim per-run view for console (full fitness vectors stay in JSON)
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for r in runs:
        top = [t["fitness"] for t in r["top10"]]
        print(
            f"  seed {r['seed']}: best={r['best_fitness']:.4f}  "
            f"draw μ±σ={r['mean_fitness_all_draws']:.4f}±"
            f"{r['std_fitness_all_draws']:.4f}  "
            f"top10=[{', '.join(f'{x:.4f}' for x in top)}]"
        )
    print(f"  vs GA mean {GA_MEAN:.4f}: {summary['n_exceed_ga_mean']}/{len(runs)} exceed")
    print(f"  vs GA band max {GA_BAND[1]:.4f}: {summary['n_exceed_ga_band_max']}/{len(runs)} exceed")

    out = {
        "method": (
            "five-seed equal-budget random search; "
            "evaluate_breakdown(n=400) on seed-7 80/20 val split; "
            "2000 draws per seed; Genome.normalize() after uniform draw"
        ),
        "provenance": provenance(),
        "runs": runs,
        "summary": summary,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        help="Run seeds (default: 42 142 242 342 442)",
    )
    args = parser.parse_args()
    main(seeds=args.seeds)
