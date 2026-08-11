#!/usr/bin/env python3
"""
Corrected dataset-size and population-size experiments with:
1. Nested subsets (not independent samples) for dataset-size
2. Fixed B1 scorer (w_s=0.80)
3. Proper TOST equivalence testing
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append("src")

from ga.runner import run_ga
from evaluation.scoring import evaluate_breakdown
from evaluation.risk_labeling import label_risk

# ──────────────────────────────────────────────
# TOST Equivalence Test
# ──────────────────────────────────────────────

def tost_equivalence(x, y, epsilon=0.01, alpha=0.05):
    """
    Schuirmann's Two One-Sided Tests (TOST) for equivalence of two
    independent samples, using the Welch (unequal-variance) t statistic.

    Equivalence is established when BOTH one-sided nulls are rejected:
        lower test  H0: delta <= -epsilon   vs  H1: delta > -epsilon
        upper test  H0: delta >= +epsilon   vs  H1: delta < +epsilon
    where delta = mean(x) - mean(y). The lower test is an upper-tail test
    (survival function) and the upper test is a lower-tail test (CDF);
    getting these two tails the wrong way round inverts the whole procedure.

    The reported interval is the (1 - 2*alpha) interval, which is the one
    that corresponds to the TOST decision: equivalence holds if and only if
    that interval lies entirely inside (-epsilon, +epsilon). At alpha=0.05
    this is a 90% interval, not a 95% one.

    Implemented with SciPy only, so no additional dependency is required.

    Returns a dict with the mean difference, both one-sided p-values, the
    overall TOST p-value, the (1 - 2*alpha) interval, Cohen's d, and the
    equivalence decision.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mean_diff = float(np.mean(x) - np.mean(y))
    n1, n2 = len(x), len(y)
    s1, s2 = np.std(x, ddof=1), np.std(y, ddof=1)

    v1, v2 = s1**2 / n1, s2**2 / n2
    se = float(np.sqrt(v1 + v2))

    pooled_std = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    cohens_d = float(mean_diff / pooled_std) if pooled_std > 0 else 0.0

    if se == 0:
        is_equivalent = abs(mean_diff) < epsilon
        return {
            "mean_diff": mean_diff, "se": 0.0, "df": float(n1 + n2 - 2),
            "p_lower": 0.0 if is_equivalent else 1.0,
            "p_upper": 0.0 if is_equivalent else 1.0,
            "tost_p_value": 0.0 if is_equivalent else 1.0,
            "ci_lower": mean_diff, "ci_upper": mean_diff,
            "ci_level": 1 - 2 * alpha, "cohens_d": cohens_d,
            "epsilon": epsilon, "alpha": alpha,
            "is_equivalent": bool(is_equivalent),
        }

    # Welch-Satterthwaite degrees of freedom
    df = float((v1 + v2) ** 2 / (v1**2 / (n1 - 1) + v2**2 / (n2 - 1)))

    p_lower = float(stats.t.sf((mean_diff + epsilon) / se, df=df))
    p_upper = float(stats.t.cdf((mean_diff - epsilon) / se, df=df))
    p_value = max(p_lower, p_upper)

    t_crit = stats.t.ppf(1 - alpha, df=df)  # (1 - 2*alpha) interval
    ci_lower = mean_diff - t_crit * se
    ci_upper = mean_diff + t_crit * se

    return {
        "mean_diff": mean_diff, "se": se, "df": df,
        "p_lower": p_lower, "p_upper": p_upper, "tost_p_value": p_value,
        "ci_lower": float(ci_lower), "ci_upper": float(ci_upper),
        "ci_level": 1 - 2 * alpha, "cohens_d": cohens_d,
        "epsilon": epsilon, "alpha": alpha,
        "is_equivalent": bool(p_value < alpha),
    }

# ──────────────────────────────────────────────
# Dataset Size Experiment (CORRECTED)
# ──────────────────────────────────────────────

def dataset_size_experiment_corrected(train_df, val_df, output_dir):
    """
    Dataset size experiment with NESTED subsets and equivalence testing.
    """
    print("\n" + "="*60)
    print("DATASET SIZE EXPERIMENT (CORRECTED)")
    print("="*60)
    
    dataset_sizes = [100, 300, 600, 1200, len(train_df)]
    n_seeds = 5
    epsilon = 0.01  # Equivalence margin
    
    # Create one shuffled train set, then take nested subsets
    shuffled_train = train_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    results = []
    raw_results = []
    
    for size in dataset_sizes:
        print(f"\n{'='*60}")
        print(f"Testing dataset size: {size}")
        print(f"{'='*60}")
        
        # NESTED SUBSET (not independent sample)
        subset = shuffled_train.iloc[:size].reset_index(drop=True)
        
        fitness_runs = []
        runtimes = []
        
        for run in range(1, n_seeds + 1):
            print(f"  Run {run}/{n_seeds}...", end=" ", flush=True)
            
            start = time.time()
            
            best_g, log = run_ga(
                subset,
                pop_size=100,
                generations=20,
                eval_n=min(600, len(subset)),
                seed=run
            )
            
            metrics = evaluate_breakdown(best_g, val_df, n=400)
            runtime = time.time() - start
            
            fitness_runs.append(metrics["fitness"])
            runtimes.append(runtime)
            
            raw_results.append({
                "dataset_size": size,
                "run_id": run,
                "fitness": metrics["fitness"],
                "empathy": metrics["empathy"],
                "safety": metrics["safety"],
                "structure": metrics["structure"],
                "runtime_sec": runtime
            })
            
            print(f"fitness={metrics['fitness']:.4f}, time={runtime:.1f}s")
        
        mean_fit = np.mean(fitness_runs)
        std_fit = np.std(fitness_runs, ddof=1)
        mean_runtime = np.mean(runtimes)
        
        results.append({
            "dataset_size": size,
            "mean_fitness": mean_fit,
            "std_fitness": std_fit,
            "mean_runtime_sec": mean_runtime,
            "n_seeds": n_seeds
        })
        
        print(f"  Summary: fitness={mean_fit:.4f} ± {std_fit:.4f}, runtime={mean_runtime:.1f}s")
    
    # Equivalence testing: compare each size against full dataset
    full_fitness = [r["fitness"] for r in raw_results if r["dataset_size"] == dataset_sizes[-1]]
    
    equivalence_results = []
    for size in dataset_sizes[:-1]:  # Exclude full dataset
        size_fitness = [r["fitness"] for r in raw_results if r["dataset_size"] == size]
        
        res = tost_equivalence(size_fitness, full_fitness, epsilon=epsilon)

        equivalence_results.append({
            "dataset_size": size,
            "vs_full": dataset_sizes[-1],
            **res,
        })

        equiv_str = "✓ EQUIVALENT" if res["is_equivalent"] else "✗ NOT equivalent"
        print(f"  N={size} vs N={dataset_sizes[-1]}: {equiv_str} "
              f"(TOST p={res['tost_p_value']:.4f}, d={res['cohens_d']:.3f})")
    
    # Save results
    df_results = pd.DataFrame(results)
    df_raw = pd.DataFrame(raw_results)
    df_equiv = pd.DataFrame(equivalence_results)
    
    df_results.to_csv(os.path.join(output_dir, "dataset_size_corrected.csv"), index=False)
    df_raw.to_csv(os.path.join(output_dir, "dataset_size_corrected_raw.csv"), index=False)
    df_equiv.to_csv(os.path.join(output_dir, "dataset_size_equivalence.csv"), index=False)
    
    print(f"\n✓ Saved dataset size results to {output_dir}")
    
    return df_results, df_raw, df_equiv

# ──────────────────────────────────────────────
# Population Size Experiment (CORRECTED)
# ──────────────────────────────────────────────

def population_size_experiment_corrected(train_df, val_df, output_dir):
    """
    Population size experiment with equivalence testing.
    """
    print("\n" + "="*60)
    print("POPULATION SIZE EXPERIMENT (CORRECTED)")
    print("="*60)
    
    population_sizes = [30, 50, 100, 200, 300, 400]
    n_seeds = 5
    epsilon = 0.01
    
    results = []
    raw_results = []
    
    for pop_size in population_sizes:
        print(f"\n{'='*60}")
        print(f"Testing population size: {pop_size}")
        print(f"{'='*60}")
        
        fitness_runs = []
        runtimes = []
        
        for run in range(1, n_seeds + 1):
            print(f"  Run {run}/{n_seeds}...", end=" ", flush=True)
            
            start = time.time()
            
            best_g, log = run_ga(
                train_df,
                pop_size=pop_size,
                generations=20,
                eval_n=600,
                seed=run
            )
            
            metrics = evaluate_breakdown(best_g, val_df, n=400)
            runtime = time.time() - start
            
            fitness_runs.append(metrics["fitness"])
            runtimes.append(runtime)
            
            raw_results.append({
                "population_size": pop_size,
                "run_id": run,
                "fitness": metrics["fitness"],
                "empathy": metrics["empathy"],
                "safety": metrics["safety"],
                "structure": metrics["structure"],
                "runtime_sec": runtime
            })
            
            print(f"fitness={metrics['fitness']:.4f}, time={runtime:.1f}s")
        
        mean_fit = np.mean(fitness_runs)
        std_fit = np.std(fitness_runs, ddof=1)
        mean_runtime = np.mean(runtimes)
        
        results.append({
            "population_size": pop_size,
            "mean_fitness": mean_fit,
            "std_fitness": std_fit,
            "mean_runtime_sec": mean_runtime,
            "n_seeds": n_seeds
        })
        
        print(f"  Summary: fitness={mean_fit:.4f} ± {std_fit:.4f}, runtime={mean_runtime:.1f}s")
    
    # Equivalence testing: compare P=100 (baseline) against others
    baseline_pop = 100
    baseline_fitness = [r["fitness"] for r in raw_results if r["population_size"] == baseline_pop]
    
    equivalence_results = []
    for pop_size in population_sizes:
        if pop_size == baseline_pop:
            continue
            
        pop_fitness = [r["fitness"] for r in raw_results if r["population_size"] == pop_size]
        
        res = tost_equivalence(pop_fitness, baseline_fitness, epsilon=epsilon)

        equivalence_results.append({
            "population_size": pop_size,
            "vs_baseline": baseline_pop,
            **res,
        })

        equiv_str = "✓ EQUIVALENT" if res["is_equivalent"] else "✗ NOT equivalent"
        print(f"  P={pop_size} vs P={baseline_pop}: {equiv_str} "
              f"(TOST p={res['tost_p_value']:.4f}, d={res['cohens_d']:.3f})")
    
    # Save results
    df_results = pd.DataFrame(results)
    df_raw = pd.DataFrame(raw_results)
    df_equiv = pd.DataFrame(equivalence_results)
    
    df_results.to_csv(os.path.join(output_dir, "population_size_corrected.csv"), index=False)
    df_raw.to_csv(os.path.join(output_dir, "population_size_corrected_raw.csv"), index=False)
    df_equiv.to_csv(os.path.join(output_dir, "population_size_equivalence.csv"), index=False)
    
    print(f"\n✓ Saved population size results to {output_dir}")
    
    return df_results, df_raw, df_equiv

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    print("Loading dataset...")
    df = pd.read_csv("data/phq4_cleaned.csv")
    
    # Prepare data (same as baseline_comparison.py)
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
    
    # 80/20 split
    df = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
    split = int(0.8 * len(df))
    train_df = df.iloc[:split].reset_index(drop=True)
    val_df = df.iloc[split:].reset_index(drop=True)
    
    print(f"Train: {len(train_df)} | Val: {len(val_df)}")
    
    output_dir = "experiments/baseline_comparison"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run both experiments
    print("\n" + "="*60)
    print("STARTING CORRECTED EXPERIMENTS")
    print("="*60)
    print(f"Using corrected B1 scorer (w_s=0.80)")
    print(f"Equivalence margin: ε=0.01")
    print(f"Seeds per condition: 5")
    
    start_time = time.time()
    
    # Dataset size experiment
    ds_results, ds_raw, ds_equiv = dataset_size_experiment_corrected(train_df, val_df, output_dir)
    
    # Population size experiment
    pop_results, pop_raw, pop_equiv = population_size_experiment_corrected(train_df, val_df, output_dir)
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "="*60)
    print("EXPERIMENTS COMPLETE")
    print("="*60)
    print(f"Total runtime: {total_time/60:.1f} minutes")
    print(f"\nDataset size:")
    print(ds_results[['dataset_size', 'mean_fitness', 'std_fitness']].to_string(index=False))
    print(f"\nPopulation size:")
    print(pop_results[['population_size', 'mean_fitness', 'std_fitness']].to_string(index=False))
    
    # Save summary
    summary = {
        "total_runtime_sec": total_time,
        "dataset_size_summary": ds_results.to_dict(orient='records'),
        "population_size_summary": pop_results.to_dict(orient='records'),
        "dataset_size_equivalence": ds_equiv.to_dict(orient='records'),
        "population_size_equivalence": pop_equiv.to_dict(orient='records')
    }
    
    with open(os.path.join(output_dir, "corrected_experiments_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ All results saved to {output_dir}/")

if __name__ == "__main__":
    main()
