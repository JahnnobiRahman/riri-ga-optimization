"""
Sensitivity check: re-evaluate the ALREADY-TRAINED reported genomes
(B1, B1-fixed, B2, B4) on the validation set with the 88 self-reported
minor (age 13-17) records excluded, WITHOUT retraining anything.

This answers: "does excluding these 88 records change the headline
fitness numbers?" -- a fast, no-retraining check that's separate from
the governance question of whether they should be excluded from
training too.
"""

import sys
import pandas as pd

sys.path.insert(0, "src")

from ga.genome import Genome
from evaluation.scoring import fitness
from evaluation.risk_labeling import label_risk

DATA_PATH = "data/phq4_cleaned.csv"
SEED = 7

# --- The four already-reported genomes (exact values from archived JSON files) ---
REPORTED_GENOMES = {
    "B1": Genome(
        p_id=0,
        w_e=0.1,
        w_s=0.8,
        w_c=0.1,
        memory_window=256,
        theta_mid=0.7,
        theta_high=0.95,
        gamma=0.0
    ),
    "B1-fixed": Genome(
        p_id=0,
        w_e=0.1,
        w_s=0.8,
        w_c=0.1,
        memory_window=512,  # Only difference from B1
        theta_mid=0.7,
        theta_high=0.95,
        gamma=0.0
    ),
    "B2": Genome(
        p_id=1,
        w_e=0.33,
        w_s=0.33,
        w_c=0.34,
        memory_window=512,
        theta_mid=0.55,
        theta_high=0.8,
        gamma=0.1
    ),
    "B4": Genome(
        p_id=0,
        w_e=0.13095859853619485,
        w_s=0.10121741632155216,
        w_c=0.767823985142253,
        memory_window=512,
        theta_mid=0.5877710669673699,
        theta_high=0.7,
        gamma=0.0584849049466897
    ),
}

# Normalize all genomes
for g in REPORTED_GENOMES.values():
    g.normalize()


def main():
    print("="*70)
    print("MINORS SENSITIVITY CHECK")
    print("="*70)
    print("\nLoading and filtering dataset...")
    
    # Load raw data
    df = pd.read_csv(DATA_PATH)
    
    # Apply EXACT same filtering as baseline_comparison.py (lines 60-79)
    for col in ["common_themes", "thought_progression", "risk_assessment"]:
        if col not in df.columns:
            df[col] = ""
    
    if "total_score" not in df.columns:
        df["total_score"] = 0
    
    for col in ["common_themes", "thought_progression", "risk_assessment"]:
        df[col] = df[col].fillna("")
    df["total_score"] = df["total_score"].fillna(0)
    
    # Build user_prompt
    df["user_prompt"] = (
        df["common_themes"].astype(str).str.strip()
        + " | "
        + df["thought_progression"].astype(str).str.strip()
    ).str.strip(" |")
    
    # CRITICAL FILTER: remove rows with empty user_prompt
    df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)
    
    print(f"Filtered dataset: {len(df)} records")
    assert len(df) == 2872, (
        f"ERROR: Filtered dataset has {len(df)} rows, expected 2872. "
        "Filter logic doesn't match baseline_comparison.py"
    )
    print("✓ Dataset size verified (N=2872)")
    
    # Add risk_label column (required by fitness function)
    df["risk_label"] = df.apply(label_risk, axis=1)
    
    # Reproduce exact same shuffle + split
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    split_idx = int(0.8 * len(df))
    val_df_full = df.iloc[split_idx:].reset_index(drop=True)
    
    print(f"Validation set: {len(val_df_full)} records")
    assert len(val_df_full) == 575, (
        f"ERROR: Validation set has {len(val_df_full)} rows, expected 575."
    )
    print("✓ Validation set size verified (N=575)")
    
    # Identify minors
    minors_mask = (val_df_full["age_group"] == "13-17")
    n_minors = minors_mask.sum()
    print(f"\nMinors (13-17) in validation set: {n_minors}")
    assert n_minors == 88, (
        f"ERROR: Expected 88 minors in validation set, found {n_minors}"
    )
    print("✓ Minors count verified (N=88)")
    
    # Create filtered validation set (exclude minors)
    val_df_filtered = val_df_full[~minors_mask].reset_index(drop=True)
    print(f"Validation set with minors excluded: {len(val_df_filtered)} records")
    
    print("\n" + "="*70)
    print("EVALUATING GENOMES ON BOTH VALIDATION SETS")
    print("="*70)
    
    results = []
    for name, genome in REPORTED_GENOMES.items():
        print(f"\n{name}:")
        print(f"  Genome: w_e={genome.w_e:.3f}, w_s={genome.w_s:.3f}, w_c={genome.w_c:.3f}, m={genome.memory_window}")
        
        # Evaluate on full validation set
        fit_full = fitness(genome, val_df_full)
        print(f"  Full validation (n=575):     fitness = {fit_full:.4f}")
        
        # Evaluate on minors-excluded set
        fit_filtered = fitness(genome, val_df_filtered)
        print(f"  Minors excluded (n=494):      fitness = {fit_filtered:.4f}")
        
        diff = fit_filtered - fit_full
        rel_diff = (diff / fit_full * 100) if fit_full != 0 else float("nan")
        print(f"  Difference: {diff:+.4f} ({rel_diff:+.2f}% relative)")
        
        results.append({
            "condition": name,
            "fitness_full_validation": fit_full,
            "fitness_minors_excluded": fit_filtered,
            "absolute_difference": diff,
            "relative_diff_percent": rel_diff,
        })
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    max_abs_diff = max(abs(r["absolute_difference"]) for r in results)
    mean_abs_diff = sum(abs(r["absolute_difference"]) for r in results) / len(results)
    
    print(f"\nLargest absolute fitness change: {max_abs_diff:.4f}")
    print(f"Mean absolute fitness change: {mean_abs_diff:.4f}")
    
    if max_abs_diff < 0.01:
        print("\n⇒ VERDICT: Numbers are essentially UNCHANGED by excluding the 88 minors.")
        print("  This supports treating the ethics question as separable from")
        print("  the reported fitness numbers (Option B/C become more defensible).")
    else:
        print("\n⇒ VERDICT: Numbers SHIFT MEANINGFULLY (Δ ≥ 0.01).")
        print("  This is evidence the ethics question and the reported numbers")
        print("  ARE entangled -- full exclusion (Option A, including retraining)")
        print("  is the more defensible path.")
    
    # Save results
    out_df = pd.DataFrame(results)
    out_path = "experiments/baseline_comparison/minors_sensitivity_check.csv"
    out_df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")
    print("="*70)


if __name__ == "__main__":
    main()
