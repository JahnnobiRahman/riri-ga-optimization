#!/usr/bin/env python3
"""
Plot corrected dataset-size and population-size experiments with equivalence regions.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def plot_dataset_size(df, df_equiv, output_path):
    """Plot dataset size results with equivalence testing."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    
    ax.errorbar(
        df['dataset_size'], 
        df['mean_fitness'],
        yerr=df['std_fitness'],
        marker='o',
        markersize=8,
        capsize=5,
        capthick=2,
        linewidth=2,
        label='Mean ± SD (n=5 seeds)'
    )
    
    # Add equivalence region (±ε from full dataset)
    full_fitness = df[df['dataset_size'] == df['dataset_size'].max()]['mean_fitness'].values[0]
    epsilon = 0.01
    ax.axhspan(full_fitness - epsilon, full_fitness + epsilon, 
               alpha=0.15, color='green', label=f'Equivalence region (±{epsilon})')
    
    ax.set_xlabel('Dataset Size (N)', fontsize=12)
    ax.set_ylabel('Validation Fitness', fontsize=12)
    ax.set_title('Dataset Size Sensitivity (Nested Subsets)', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.25, linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Saved: {output_path}")

def plot_population_size(df, df_equiv, output_path):
    """Plot population size results with equivalence testing."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    
    ax.errorbar(
        df['population_size'], 
        df['mean_fitness'],
        yerr=df['std_fitness'],
        marker='o',
        markersize=8,
        capsize=5,
        capthick=2,
        linewidth=2,
        label='Mean ± SD (n=5 seeds)'
    )
    
    # Add equivalence region (±ε from P=100 baseline)
    baseline_fitness = df[df['population_size'] == 100]['mean_fitness'].values[0]
    epsilon = 0.01
    ax.axhspan(baseline_fitness - epsilon, baseline_fitness + epsilon, 
               alpha=0.15, color='green', label=f'Equivalence region (±{epsilon})')
    
    ax.set_xlabel('Population Size (P)', fontsize=12)
    ax.set_ylabel('Validation Fitness', fontsize=12)
    ax.set_title('Population Size Sensitivity', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.25, linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Saved: {output_path}")

def main():
    base_dir = "experiments/baseline_comparison"
    
    # Load results
    df_ds = pd.read_csv(f"{base_dir}/dataset_size_corrected.csv")
    df_ds_equiv = pd.read_csv(f"{base_dir}/dataset_size_equivalence.csv")
    
    df_pop = pd.read_csv(f"{base_dir}/population_size_corrected.csv")
    df_pop_equiv = pd.read_csv(f"{base_dir}/population_size_equivalence.csv")
    
    # Plot
    plot_dataset_size(df_ds, df_ds_equiv, "paper/figures/dataset_size_experiment_plot.png")
    plot_population_size(df_pop, df_pop_equiv, "paper/figures/population_experiment_plot.png")
    
    # Print equivalence summary
    print("\n" + "="*60)
    print("EQUIVALENCE TEST RESULTS")
    print("="*60)
    
    print("\nDataset Size (vs full N=2297):")
    for _, row in df_ds_equiv.iterrows():
        equiv = "✓ EQUIVALENT" if row['is_equivalent'] else "✗ NOT equivalent"
        print(f"  N={row['dataset_size']:4d}: {equiv} (p={row['tost_p_value']:.4f}, d={row['cohens_d']:+.3f})")
    
    print("\nPopulation Size (vs P=100 baseline):")
    for _, row in df_pop_equiv.iterrows():
        equiv = "✓ EQUIVALENT" if row['is_equivalent'] else "✗ NOT equivalent"
        print(f"  P={row['population_size']:3d}: {equiv} (p={row['tost_p_value']:.4f}, d={row['cohens_d']:+.3f})")
    
    print("\n✓ Plots saved to paper/figures/")

if __name__ == "__main__":
    main()
