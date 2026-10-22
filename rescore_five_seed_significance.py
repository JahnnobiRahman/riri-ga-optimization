#!/usr/bin/env python3
"""
Re-score Table 6 five-seed significance test under the current (corrected) scorer.

For each archived GA seed genome (13/26/39/52/65), score GA, B1, and B2 on the
same val split with N_EVAL=400. No broadcast delta_fit.
"""

import json
import os
import random
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "src")

from evaluation.risk_labeling import label_risk
from evaluation.scoring import evaluate_breakdown
from ga.genome import Genome

SEED = 7
N_EVAL = 400
OUT_DIR = "experiments/baseline_comparison"
SEED_DIR = os.path.join(OUT_DIR, "seed_genomes")
SEEDS = [13, 26, 39, 52, 65]


def load_val_df():
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
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    return df.iloc[split:].reset_index(drop=True)


def load_genome(path: str) -> Genome:
    with open(path) as f:
        d = json.load(f)
    # drop non-Genome keys if present
    keys = {
        "p_id", "w_s", "w_e", "w_c", "memory_window",
        "theta_mid", "theta_high", "gamma",
    }
    return Genome(**{k: d[k] for k in keys})


def cohens_d_paired(a, b):
    diff = np.asarray(a) - np.asarray(b)
    return float(diff.mean() / diff.std(ddof=1)) if diff.std(ddof=1) > 0 else 0.0


def boot_ci(diff, n=10000, seed=7):
    rng = np.random.default_rng(seed)
    diff = np.asarray(diff)
    means = [rng.choice(diff, size=len(diff), replace=True).mean() for _ in range(n)]
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def hodges_lehmann(diff):
    diff = np.asarray(diff)
    pairwise = [(diff[i] + diff[j]) / 2 for i in range(len(diff)) for j in range(i, len(diff))]
    return float(np.median(pairwise))


def main():
    val_df = load_val_df()
    print(f"Val rows: {len(val_df)} | N_EVAL={N_EVAL}")

    b1 = load_genome(os.path.join(OUT_DIR, "best_genome_B1.json"))
    b2 = load_genome(os.path.join(OUT_DIR, "best_genome_B2.json"))
    print(f"B1: {b1}")
    print(f"B2: {b2}")

    ga_runs, b1_runs, b2_runs = [], [], []
    per_seed = []

    for seed_r in SEEDS:
        g_path = os.path.join(SEED_DIR, f"best_genome_seed_{seed_r}.json")
        ga = load_genome(g_path)

        random.seed(seed_r)
        np.random.seed(seed_r)
        ga_m = evaluate_breakdown(ga, val_df, n=N_EVAL)

        random.seed(seed_r)
        np.random.seed(seed_r)
        b1_m = evaluate_breakdown(b1, val_df, n=N_EVAL)

        random.seed(seed_r)
        np.random.seed(seed_r)
        b2_m = evaluate_breakdown(b2, val_df, n=N_EVAL)

        ga_runs.append(ga_m["fitness"])
        b1_runs.append(b1_m["fitness"])
        b2_runs.append(b2_m["fitness"])
        per_seed.append({
            "seed": seed_r,
            "ga": ga_m,
            "b1": b1_m,
            "b2": b2_m,
        })
        print(
            f"Seed {seed_r:2d}: GA={ga_m['fitness']:.6f} "
            f"(C={ga_m['structure']:.4f})  "
            f"B1={b1_m['fitness']:.6f}  B2={b2_m['fitness']:.6f}"
        )

    ga = np.array(ga_runs)
    b1a = np.array(b1_runs)
    b2a = np.array(b2_runs)

    stat_b1, p_b1 = stats.wilcoxon(ga, b1a, alternative="greater")
    stat_b2, p_b2 = stats.wilcoxon(ga, b2a, alternative="greater")

    diff1 = ga - b1a
    diff2 = ga - b2a
    d1 = cohens_d_paired(ga, b1a)
    d2 = cohens_d_paired(ga, b2a)
    ci1 = boot_ci(diff1)
    ci2 = boot_ci(diff2)

    rs_best = 0.7068298737727912
    ga_mean = float(ga.mean())
    ga_std = float(ga.std(ddof=1))
    z_rs = (rs_best - ga_mean) / ga_std if ga_std > 0 else float("nan")
    n_exceed = int(np.sum(rs_best > ga))

    out = {
        "method": (
            "direct re-score of archived five-seed GA genomes + B1/B2 "
            "under current corrected structure scorer; N_EVAL=400; "
            "no delta_fit broadcast"
        ),
        "n_eval": N_EVAL,
        "seeds": SEEDS,
        "b1_genome": "experiments/baseline_comparison/best_genome_B1.json",
        "b2_genome": "experiments/baseline_comparison/best_genome_B2.json",
        "ga_fitness_runs": ga_runs,
        "b1_fitness_runs": b1_runs,
        "b2_fitness_runs": b2_runs,
        "per_seed_breakdown": per_seed,
        "mean_std": {
            "GA": [ga_mean, ga_std],
            "B1": [float(b1a.mean()), float(b1a.std(ddof=1))],
            "B2": [float(b2a.mean()), float(b2a.std(ddof=1))],
        },
        "range_GA": [float(ga.min()), float(ga.max())],
        "wilcoxon_GA_vs_B1": {"statistic": float(stat_b1), "p_value": float(p_b1)},
        "wilcoxon_GA_vs_B2": {"statistic": float(stat_b2), "p_value": float(p_b2)},
        "effect": {
            "mean_diff_B1": float(diff1.mean()),
            "d_B1": d1,
            "ci_B1": ci1,
            "HL_B1": hodges_lehmann(diff1),
            "diff_B1": diff1.tolist(),
            "mean_diff_B2": float(diff2.mean()),
            "d_B2": d2,
            "ci_B2": ci2,
            "HL_B2": hodges_lehmann(diff2),
            "diff_B2": diff2.tolist(),
        },
        "random_search_comparison": {
            "rs_best": rs_best,
            "ga_mean": ga_mean,
            "ga_std": ga_std,
            "z_above_ga_mean": z_rs,
            "n_ga_seeds_exceeded": n_exceed,
        },
    }

    out_path = os.path.join(OUT_DIR, "stats_summary_corrected_markers.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")
    print(f"GA mean±std: {ga_mean:.4f} ± {ga_std:.4f}  range [{ga.min():.4f}, {ga.max():.4f}]")
    print(f"B1 mean±std: {b1a.mean():.4f} ± {b1a.std(ddof=1):.4f}")
    print(f"B2 mean±std: {b2a.mean():.4f} ± {b2a.std(ddof=1):.4f}")
    print(f"Wilcoxon GA>B1: W={stat_b1}, p={p_b1}")
    print(f"Wilcoxon GA>B2: W={stat_b2}, p={p_b2}")
    print(f"RS best z vs GA mean: {z_rs:.4f} (exceeds {n_exceed}/5 seeds)")


if __name__ == "__main__":
    main()
