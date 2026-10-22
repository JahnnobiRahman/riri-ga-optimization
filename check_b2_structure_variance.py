#!/usr/bin/env python3
"""
Check B2 structure score variance - same as B1 check.
"""

import json
import pandas as pd
from src.ga.genome import Genome
from src.evaluation.scoring import fitness, score_structure, score_empathy, score_safety
from src.evaluation.risk_labeling import label_risk
from src.generation.response_generator import generate_response

def load_b2_genome():
    """Load the B2 genome."""
    with open("experiments/baseline_comparison/best_genome_B2.json") as f:
        data = json.load(f)
    return Genome(**data)

def load_eval_data():
    """Load evaluation dataset."""
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
    
    df = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
    split = int(0.8 * len(df))
    val_df = df.iloc[split:].reset_index(drop=True)
    
    return val_df

def run_b2_multiple_times(n_runs=10):
    """Run B2 evaluation multiple times and track structure scores."""
    g_b2 = load_b2_genome()
    eval_data = load_eval_data()
    
    results = []
    for run_idx in range(n_runs):
        fit = fitness(g_b2, eval_data)
        
        empathy_scores = []
        safety_scores = []
        structure_scores = []
        
        for _, row in eval_data.iterrows():
            r = generate_response(
                row["user_prompt"],
                row["risk_label"],
                g_b2,
                escalate_override=None
            )
            empathy_scores.append(score_empathy(r))
            safety_scores.append(score_safety(r, row["risk_label"]))
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

def trace_b2_responses(n_samples=50):
    """Trace individual B2 responses and count structural components."""
    g_b2 = load_b2_genome()
    eval_data = load_eval_data()
    
    sample_data = eval_data.sample(n=min(n_samples, len(eval_data)), random_state=42)
    
    has_structure_count = 0
    structure_scores = []
    
    for idx, row in sample_data.iterrows():
        r = generate_response(
            row["user_prompt"],
            row["risk_label"],
            g_b2,
            escalate_override=None
        )
        
        struct_score = score_structure(r)
        structure_scores.append(struct_score)
        
        if struct_score > 0:
            has_structure_count += 1
    
    print(f"\n{'='*60}")
    print(f"B2 Response Structure Analysis (n={len(sample_data)})")
    print(f"{'='*60}")
    print(f"Responses with structure (score > 0): {has_structure_count} / {len(sample_data)} ({100*has_structure_count/len(sample_data):.1f}%)")
    print(f"Average structure score: {sum(structure_scores)/len(structure_scores):.4f}")
    print(f"Min structure score: {min(structure_scores):.4f}")
    print(f"Max structure score: {max(structure_scores):.4f}")
    
    return has_structure_count, structure_scores

if __name__ == "__main__":
    print("="*60)
    print("B2 STRUCTURE VARIANCE ANALYSIS")
    print("="*60)
    print()
    
    print("1. Running B2 evaluation 10 times...")
    print("-" * 60)
    results = run_b2_multiple_times(n_runs=10)
    
    structure_scores = [r["structure"] for r in results]
    print(f"\n{'='*60}")
    print(f"Structure Score Statistics:")
    print(f"  Mean:   {sum(structure_scores)/len(structure_scores):.4f}")
    print(f"  Min:    {min(structure_scores):.4f}")
    print(f"  Max:    {max(structure_scores):.4f}")
    print(f"  Range:  {max(structure_scores) - min(structure_scores):.4f}")
    print(f"  Std:    {(sum((x - sum(structure_scores)/len(structure_scores))**2 for x in structure_scores)/len(structure_scores))**0.5:.4f}")
    
    print("\n2. Tracing 50 individual B2 responses...")
    print("-" * 60)
    has_struct, scores = trace_b2_responses(n_samples=50)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
