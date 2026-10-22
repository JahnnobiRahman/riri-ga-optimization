#!/usr/bin/env python3
"""
Check B1 structure score variance and response component survival.
"""

import json
import pandas as pd
from pathlib import Path
from src.ga.genome import Genome
from src.evaluation.scoring import fitness, score_structure, score_empathy, score_safety
from src.evaluation.risk_labeling import label_risk
from src.generation.response_generator import generate_response
import random

def load_b1_genome():
    """Load the B1 genome."""
    with open("experiments/baseline_comparison/best_genome_B1.json") as f:
        data = json.load(f)
    return Genome(**data)

def load_eval_data():
    """Load evaluation dataset."""
    df = pd.read_csv("data/phq4_cleaned.csv")
    
    # Prepare columns as in baseline_comparison.py
    for col in ["common_themes", "thought_progression", "risk_assessment"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    
    if "total_score" not in df.columns:
        df["total_score"] = 0
    df["total_score"] = df["total_score"].fillna(0)
    
    # Create risk_label
    df["risk_label"] = df.apply(label_risk, axis=1)
    
    # Create user_prompt
    df["user_prompt"] = (
        df["common_themes"].astype(str).str.strip()
        + " | "
        + df["thought_progression"].astype(str).str.strip()
    ).str.strip(" |")
    
    df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)
    
    # Use same validation split as baseline_comparison (80/20 split after shuffle with seed 7)
    df = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
    split = int(0.8 * len(df))
    val_df = df.iloc[split:].reset_index(drop=True)
    
    return val_df

def run_b1_multiple_times(n_runs=10):
    """Run B1 evaluation multiple times and track structure scores."""
    g_b1 = load_b1_genome()
    eval_data = load_eval_data()
    
    results = []
    for run_idx in range(n_runs):
        fit = fitness(g_b1, eval_data)
        
        # Compute individual component scores
        empathy_scores = []
        safety_scores = []
        structure_scores = []
        
        for _, row in eval_data.iterrows():
            r = generate_response(
                row["user_prompt"],
                row["risk_assessment"],
                g_b1,
                escalate_override=None
            )
            empathy_scores.append(score_empathy(r))
            safety_scores.append(score_safety(r, row["risk_assessment"]))
            structure_scores.append(score_structure(r))
        
        avg_empathy = sum(empathy_scores) / len(empathy_scores)
        avg_safety = sum(safety_scores) / len(safety_scores)
        avg_structure = sum(structure_scores) / len(structure_scores)
        
        results.append({
            "run": run_idx + 1,
            "fitness": fit,
            "empathy": avg_empathy,
            "safety": avg_safety,
            "structure": avg_structure
        })
        print(f"Run {run_idx + 1:2d}: fitness={fit:.4f} empathy={avg_empathy:.3f} safety={avg_safety:.3f} structure={avg_structure:.3f}")
    
    return results

def trace_b1_responses(n_samples=50):
    """Trace individual B1 responses and count structural components."""
    g_b1 = load_b1_genome()
    eval_data = load_eval_data()
    
    # Sample n_samples rows
    sample_data = eval_data.sample(n=min(n_samples, len(eval_data)), random_state=42)
    
    has_structure_count = 0
    structure_scores = []
    
    for idx, row in sample_data.iterrows():
        r = generate_response(
            row["user_prompt"],
            row["risk_assessment"],
            g_b1,
            escalate_override=None
        )
        
        struct_score = score_structure(r)
        structure_scores.append(struct_score)
        
        if struct_score > 0:
            has_structure_count += 1
    
    print(f"\n{'='*60}")
    print(f"B1 Response Structure Analysis (n={len(sample_data)})")
    print(f"{'='*60}")
    print(f"Responses with structure (score > 0): {has_structure_count} / {len(sample_data)} ({100*has_structure_count/len(sample_data):.1f}%)")
    print(f"Average structure score: {sum(structure_scores)/len(structure_scores):.4f}")
    print(f"Min structure score: {min(structure_scores):.4f}")
    print(f"Max structure score: {max(structure_scores):.4f}")
    
    return has_structure_count, structure_scores

def check_random_seed_behavior():
    """Check if the generator uses fixed random seeds per evaluation."""
    g_b1 = load_b1_genome()
    eval_data = load_eval_data()
    
    # Take first 5 prompts and generate responses twice
    test_prompts = eval_data.head(5)
    
    print(f"\n{'='*60}")
    print(f"Random Seed Behavior Check")
    print(f"{'='*60}")
    print("Generating same prompts twice to check for determinism...\n")
    
    responses_run1 = []
    responses_run2 = []
    
    for idx, row in test_prompts.iterrows():
        r1 = generate_response(
            row["user_prompt"],
            row["risk_assessment"],
            g_b1,
            escalate_override=None
        )
        responses_run1.append(r1)
    
    for idx, row in test_prompts.iterrows():
        r2 = generate_response(
            row["user_prompt"],
            row["risk_assessment"],
            g_b1,
            escalate_override=None
        )
        responses_run2.append(r2)
    
    # Check if responses are identical
    all_identical = all(r1 == r2 for r1, r2 in zip(responses_run1, responses_run2))
    
    if all_identical:
        print("✓ DETERMINISTIC: All responses identical across runs")
        print("  → Generator uses fixed/seeded randomness per evaluation")
    else:
        print("✗ STOCHASTIC: Responses differ across runs")
        print("  → Generator uses unseeded randomness (explains variance)")
        
        # Show examples of differences
        for i, (r1, r2) in enumerate(zip(responses_run1, responses_run2)):
            if r1 != r2:
                print(f"\n  Prompt {i+1} differs:")
                print(f"    Run 1 length: {len(r1)} chars")
                print(f"    Run 2 length: {len(r2)} chars")
                print(f"    Run 1 score: {score_structure(r1):.3f}")
                print(f"    Run 2 score: {score_structure(r2):.3f}")
    
    return all_identical

if __name__ == "__main__":
    print("="*60)
    print("B1 STRUCTURE VARIANCE ANALYSIS")
    print("="*60)
    print()
    
    # 1. Run B1 multiple times
    print("1. Running B1 evaluation 10 times...")
    print("-" * 60)
    results = run_b1_multiple_times(n_runs=10)
    
    structure_scores = [r["structure"] for r in results]
    print(f"\n{'='*60}")
    print(f"Structure Score Statistics:")
    print(f"  Mean:   {sum(structure_scores)/len(structure_scores):.4f}")
    print(f"  Min:    {min(structure_scores):.4f}")
    print(f"  Max:    {max(structure_scores):.4f}")
    print(f"  Range:  {max(structure_scores) - min(structure_scores):.4f}")
    print(f"  Std:    {(sum((x - sum(structure_scores)/len(structure_scores))**2 for x in structure_scores)/len(structure_scores))**0.5:.4f}")
    
    # 2. Trace individual responses
    print("\n2. Tracing 50 individual B1 responses...")
    print("-" * 60)
    has_struct, scores = trace_b1_responses(n_samples=50)
    
    # 3. Check random seed behavior
    print("\n3. Checking random seed behavior...")
    print("-" * 60)
    is_deterministic = check_random_seed_behavior()
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
