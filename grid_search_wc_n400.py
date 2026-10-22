#!/usr/bin/env python3
"""
Re-score the 12-point w_c grid under evaluate_breakdown(n=400) — same path
as the five-seed GA significance table and equal-budget random search.
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, "src")

from ga.genome import Genome
from evaluation.scoring import evaluate_breakdown
from evaluation.risk_labeling import label_risk

N_EVAL_PROMPTS = 400
VAL_SPLIT_SEED = 7
OUT_PATH = "experiments/baseline_comparison/grid_search_wc_n400.json"


def load_validation_set() -> pd.DataFrame:
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


def main():
    val_df = load_validation_set()
    assert len(val_df) == 575, f"expected 575-row val split, got {len(val_df)}"

    with open("experiments/baseline_comparison/best_genome_B4.json") as f:
        best = json.load(f)

    w_e_reported = best["w_e"]
    w_s_reported = best["w_s"]
    total_es = w_e_reported + w_s_reported
    w_e_share = w_e_reported / total_es
    w_s_share = w_s_reported / total_es

    w_c_grid = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90, 1.00]
    results = []

    print(f"Val rows={len(val_df)} | n={N_EVAL_PROMPTS}")
    for w_c in w_c_grid:
        rem = 1.0 - w_c
        g = Genome(
            p_id=best["p_id"],
            w_c=w_c,
            w_e=rem * w_e_share,
            w_s=rem * w_s_share,
            memory_window=best["memory_window"],
            theta_mid=best["theta_mid"],
            theta_high=best["theta_high"],
            gamma=best["gamma"],
        )
        g.normalize()
        m = evaluate_breakdown(g, val_df, n=N_EVAL_PROMPTS)
        row = {
            "w_c_target": w_c,
            "w_c_actual": g.w_c,
            "w_e_actual": g.w_e,
            "w_s_actual": g.w_s,
            "empathy": m["empathy"],
            "safety": m["safety"],
            "structure": m["structure"],
            "fitness": m["fitness"],
        }
        results.append(row)
        print(
            f"  w_c={w_c:.2f} → fit={m['fitness']:.4f} "
            f"C={m['structure']:.3f} E={m['empathy']:.3f} S={m['safety']:.3f}"
        )

    peak = max(results, key=lambda r: r["fitness"])
    out = {
        "method": (
            "12-point w_c grid; evaluate_breakdown(n=400) on seed-7 80/20 val; "
            "w_e:w_s ratio fixed from best_genome_B4; normalize no-op at grid points"
        ),
        "provenance": {
            "scoring": "evaluate_breakdown",
            "n_eval_prompts": N_EVAL_PROMPTS,
            "val_split_seed": VAL_SPLIT_SEED,
            "split": "80/20 shuffled then holdout (no stratification)",
            "stratification": None,
        },
        "results": results,
        "peak": peak,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nPeak: w_c={peak['w_c_target']:.2f} fitness={peak['fitness']:.4f}")
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
