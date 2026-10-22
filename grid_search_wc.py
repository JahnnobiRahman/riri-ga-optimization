"""
Minimal grid-search ablation over the structure weight w_c, holding all
other genome parameters fixed at the reported genome's values.

Purpose: test whether crossing the deterministic structure threshold
(w_c >= 0.55, Section 3.4.2) is sufficient to explain the GA's structural
gain, without needing evolutionary search.
"""

import sys
import os
import json
from statistics import mean
import pandas as pd

sys.path.insert(0, "src")

from ga.genome import Genome
from generation.response_generator import generate_response
from evaluation.scoring import score_empathy, score_safety, score_structure, fitness
from evaluation.risk_labeling import label_risk


def load_validation_set():
    """Load the same 575-prompt validation set used in baseline_comparison.py"""
    DATA_PATH = "data/phq4_cleaned.csv"
    df = pd.read_csv(DATA_PATH)
    
    # Same preprocessing as baseline_comparison.py
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
    
    # Same 80/20 split with seed=7
    SEED = 7
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    val_df = df.iloc[split:].reset_index(drop=True)
    
    return val_df


def evaluate_genome(genome, validation_df):
    """Evaluate a genome on the validation set, returning mean E/S/C/F."""
    empathy_scores, safety_scores, structure_scores, fitness_scores = [], [], [], []
    
    for _, row in validation_df.iterrows():
        prompt = row["user_prompt"]
        risk = row["risk_label"]
        
        resp = generate_response(prompt, risk, genome)
        
        e = score_empathy(resp)
        s = score_safety(resp, risk)
        c = score_structure(resp)
        
        empathy_scores.append(e)
        safety_scores.append(s)
        structure_scores.append(c)
        
        # Compute fitness using the full fitness function
        temp_df = pd.DataFrame([{"user_prompt": prompt, "risk_label": risk}])
        f = fitness(genome, temp_df)
        fitness_scores.append(f)
    
    return {
        "empathy": mean(empathy_scores),
        "safety": mean(safety_scores),
        "structure": mean(structure_scores),
        "fitness": mean(fitness_scores),
    }


def main():
    print("Loading validation set...")
    validation_df = load_validation_set()
    print(f"Loaded {len(validation_df)} validation prompts")
    
    # Grid over w_c; w_e and w_s held at the reported genome's values
    w_c_grid = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90, 1.00]
    
    # Load actual best genome values
    with open("experiments/baseline_comparison/best_genome_B4.json", "r") as f:
        best_genome_data = json.load(f)
    
    fixed_w_e = best_genome_data["w_e"]
    fixed_w_s = best_genome_data["w_s"]
    
    print(f"\nFixed parameters from best B4 genome:")
    print(f"  w_e = {fixed_w_e:.4f}")
    print(f"  w_s = {fixed_w_s:.4f}")
    print(f"  theta_mid = {best_genome_data['theta_mid']:.4f}")
    print(f"  theta_high = {best_genome_data['theta_high']:.4f}")
    print(f"  gamma = {best_genome_data['gamma']:.4f}")
    print(f"  memory_window = {best_genome_data['memory_window']}")
    
    results = []
    for i, w_c in enumerate(w_c_grid, 1):
        print(f"\n[{i}/{len(w_c_grid)}] Testing w_c = {w_c:.2f}")
        
        genome = Genome(
            p_id=best_genome_data["p_id"],
            w_e=fixed_w_e,
            w_s=fixed_w_s,
            w_c=w_c,
            memory_window=best_genome_data["memory_window"],
            theta_mid=best_genome_data["theta_mid"],
            theta_high=best_genome_data["theta_high"],
            gamma=best_genome_data["gamma"],
        )
        genome.normalize()
        
        # Sanity check
        total = genome.w_e + genome.w_s + genome.w_c
        print(f"  w_c (raw)={w_c:.2f} -> normalized: "
              f"w_e={genome.w_e:.3f}, w_s={genome.w_s:.3f}, w_c={genome.w_c:.3f} "
              f"(sum={total:.3f})")
        
        scores = evaluate_genome(genome, validation_df)
        print(f"  empathy={scores['empathy']:.3f}  safety={scores['safety']:.3f}  "
              f"structure={scores['structure']:.3f}  fitness={scores['fitness']:.3f}")
        
        results.append({
            "w_c_raw": w_c,
            "w_c_normalized": genome.w_c,
            "w_e_normalized": genome.w_e,
            "w_s_normalized": genome.w_s,
            **scores,
        })
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'w_c (raw)':>10} {'w_c (norm)':>11} {'empathy':>10} {'safety':>10} {'structure':>10} {'fitness':>10}")
    print("-"*70)
    for r in results:
        print(f"{r['w_c_raw']:>10.2f} {r['w_c_normalized']:>11.3f} "
              f"{r['empathy']:>10.3f} {r['safety']:>10.3f} "
              f"{r['structure']:>10.3f} {r['fitness']:>10.3f}")
    
    print("\n" + "="*70)
    print("THRESHOLD ANALYSIS")
    print("="*70)
    
    below_threshold = [r for r in results if r['w_c_normalized'] < 0.55]
    at_or_above_threshold = [r for r in results if r['w_c_normalized'] >= 0.55]
    
    if below_threshold and at_or_above_threshold:
        mean_structure_below = mean([r['structure'] for r in below_threshold])
        mean_structure_above = mean([r['structure'] for r in at_or_above_threshold])
        
        print(f"Mean structure below w_c=0.55: {mean_structure_below:.3f}")
        print(f"Mean structure at/above w_c=0.55: {mean_structure_above:.3f}")
        print(f"Jump at threshold: {mean_structure_above - mean_structure_below:+.3f}")
    
    out_path = "experiments/baseline_comparison/grid_search_wc_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
