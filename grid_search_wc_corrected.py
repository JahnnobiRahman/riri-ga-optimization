"""
Corrected minimal grid-search ablation over the structure weight w_c.

Fix for the previous run's confound: rather than holding w_e and w_s
constant in RAW form (which let normalized w_e/w_s drift substantially
as w_c was swept, due to the shared renormalizing denominator), this
version constructs each genome so that:
  - w_c is set EXACTLY to the target grid value,
  - w_e and w_s split the remainder (1 - w_c) in the same ratio as the
    reported genome (w_e:w_s = 0.131:0.101),
  - the three raw values already sum to 1, so genome.normalize() is a
    provable no-op at every grid point.

This isolates w_c as the single swept variable, with w_e:w_s ratio held
constant, rather than allowing normalized w_e/w_s to drift.
"""

import sys
import os
import json
from statistics import mean
import pandas as pd

sys.path.insert(0, "src")

from ga.genome import Genome
from generation.response_generator import generate_response
from evaluation.scoring import score_empathy, score_safety, score_structure, fitness, evaluate_breakdown
from evaluation.risk_labeling import label_risk


def load_validation_set():
    """Load the same 575-prompt validation set used in baseline_comparison.py"""
    DATA_PATH = "data/phq4_cleaned.csv"
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
    
    SEED = 7
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    val_df = df.iloc[split:].reset_index(drop=True)
    
    return val_df


def evaluate_genome(genome, validation_df):
    """Evaluate genome on full validation set using evaluate_breakdown (all 575 prompts)."""
    # Use evaluate_breakdown with n=len(validation_df) to score all prompts
    return evaluate_breakdown(genome, validation_df, n=len(validation_df))


def main():
    print("Loading validation set...")
    validation_df = load_validation_set()
    print(f"Loaded {len(validation_df)} validation prompts")

    # Load best genome to get fixed parameters
    with open("experiments/baseline_comparison/best_genome_B4.json", "r") as f:
        best_genome = json.load(f)

    # Reported genome's w_e:w_s ratio, held fixed across the sweep
    w_e_reported = best_genome["w_e"]  # 0.131
    w_s_reported = best_genome["w_s"]  # 0.101
    total_es = w_e_reported + w_s_reported
    w_e_share = w_e_reported / total_es   # 0.5647
    w_s_share = w_s_reported / total_es   # 0.4353

    print(f"\nFixed w_e:w_s ratio = {w_e_share:.4f}:{w_s_share:.4f}")
    print(f"Other fixed params: theta_mid={best_genome['theta_mid']:.4f}, "
          f"theta_high={best_genome['theta_high']:.4f}, gamma={best_genome['gamma']:.4f}")

    w_c_grid = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90, 1.00]

    results = []
    for i, w_c in enumerate(w_c_grid, 1):
        print(f"\n[{i}/{len(w_c_grid)}] Target w_c={w_c:.2f}")
        
        remaining = 1.0 - w_c
        w_e = remaining * w_e_share
        w_s = remaining * w_s_share

        genome = Genome(
            p_id=best_genome["p_id"],
            w_e=w_e,
            w_s=w_s,
            w_c=w_c,
            memory_window=best_genome["memory_window"],
            theta_mid=best_genome["theta_mid"],
            theta_high=best_genome["theta_high"],
            gamma=best_genome["gamma"],
        )
        genome.normalize()

        # Sanity check: normalize() should be a no-op (raw already sums to 1)
        total = genome.w_e + genome.w_s + genome.w_c
        matches_target = abs(genome.w_c - w_c) < 1e-6
        ratio_preserved = abs((genome.w_e / genome.w_s) - (w_e / w_s)) < 1e-6 if w_s > 0 else True
        
        print(f"  After normalize: w_e={genome.w_e:.4f}, w_s={genome.w_s:.4f}, w_c={genome.w_c:.4f}")
        print(f"  Sum={total:.4f}, matches_target={matches_target}, ratio_preserved={ratio_preserved}")

        scores = evaluate_genome(genome, validation_df)
        print(f"  empathy={scores['empathy']:.3f}  safety={scores['safety']:.3f}  "
              f"structure={scores['structure']:.3f}  fitness={scores['fitness']:.3f}")

        results.append({
            "w_c_target": w_c,
            "w_c_actual": genome.w_c,
            "w_e_actual": genome.w_e,
            "w_s_actual": genome.w_s,
            **scores,
        })

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'w_c':>8} {'w_e':>8} {'w_s':>8} {'empathy':>10} {'safety':>10} {'structure':>10} {'fitness':>10}")
    print("-"*70)
    for r in results:
        print(f"{r['w_c_actual']:>8.3f} {r['w_e_actual']:>8.3f} {r['w_s_actual']:>8.3f} "
              f"{r['empathy']:>10.3f} {r['safety']:>10.3f} "
              f"{r['structure']:>10.3f} {r['fitness']:>10.3f}")

    print("\n" + "="*70)
    print("THRESHOLD ANALYSIS")
    print("="*70)
    
    below_threshold = [r for r in results if r['w_c_actual'] < 0.55]
    at_or_above_threshold = [r for r in results if r['w_c_actual'] >= 0.55]
    
    if below_threshold and at_or_above_threshold:
        mean_structure_below = mean([r['structure'] for r in below_threshold])
        mean_structure_above = mean([r['structure'] for r in at_or_above_threshold])
        
        print(f"Mean structure below w_c=0.55: {mean_structure_below:.3f}")
        print(f"Mean structure at/above w_c=0.55: {mean_structure_above:.3f}")
        print(f"Jump at threshold: {mean_structure_above - mean_structure_below:+.3f}")

    out_path = "experiments/baseline_comparison/grid_search_wc_corrected.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
