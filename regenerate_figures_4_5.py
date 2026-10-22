#!/usr/bin/env python3
"""
Regenerate Figure 4 (fitness curve) and Figure 5 (diversity curve) using
the corrected B4 fitness log from the latest baseline_comparison run.
"""

import os
import json
import pandas as pd

# Set matplotlib backend to non-interactive before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def apply_paper_style():
    plt.rcParams.update({
        "figure.figsize": (7.5, 4.8),
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.8,
    })

def save_fitness_curve(df, output_dir):
    fig, ax = plt.subplots()

    ax.plot(
        df["generation"],
        df["best"],
        linewidth=2.5,
        label="Best fitness",
    )

    ax.plot(
        df["generation"],
        df["avg"],
        linewidth=2.5,
        linestyle="--",
        label="Average fitness",
    )

    ax.set_title("Genetic Algorithm Convergence")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness score")
    ax.legend(frameon=True)
    ax.set_ylim(0, 1.02)

    fig.tight_layout()
    output_path = os.path.join(output_dir, "fitness_curve_paper.png")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Saved: {output_path}")

def save_diversity_curve(df, output_dir):
    fig, ax = plt.subplots()

    ax.plot(
        df["generation"],
        df["var"],
        linewidth=2.5,
        label="Population variance",
    )

    ax.set_title("Population Diversity Across Generations")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Variance")
    ax.legend(frameon=True)

    fig.tight_layout()
    output_path = os.path.join(output_dir, "diversity_curve.png")
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ Saved: {output_path}")

def main():
    # Load B4 fitness log from the corrected baseline_comparison run
    log_path = "experiments/baseline_comparison/b4_fitness_log.json"
    output_dir = "paper/figures"
    
    print(f"Loading fitness log from: {log_path}")
    
    if not os.path.exists(log_path):
        raise FileNotFoundError(
            f"b4_fitness_log.json not found at {log_path}\n"
            "Run baseline_comparison.py first to generate this log."
        )
    
    with open(log_path) as f:
        log = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame({
        "generation": range(1, len(log["best"]) + 1),
        "best": log["best"],
        "avg":  log["avg"],
        "var":  log["var"],
    })
    
    print(f"\nLoaded {len(df)} generations from corrected B4 run:")
    print(f"  Best fitness: Gen 1 = {df['best'].iloc[0]:.4f}, "
          f"Gen {len(df)} = {df['best'].iloc[-1]:.4f}")
    print(f"  Final avg:    {df['avg'].iloc[-1]:.4f}")
    print(f"  Final var:    {df['var'].iloc[-1]:.6f}")
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Apply paper style and generate figures
    apply_paper_style()
    
    print(f"\nGenerating figures...")
    save_fitness_curve(df, output_dir)
    save_diversity_curve(df, output_dir)
    
    print(f"\n✓ Figures regenerated successfully!")
    print(f"  Figure 4 (fitness curve): {output_dir}/fitness_curve_paper.png")
    print(f"  Figure 5 (diversity curve): {output_dir}/diversity_curve.png")

if __name__ == "__main__":
    main()
