import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def plot_dataset_size(csv_path, out_dir):
    df = pd.read_csv(csv_path)

    plt.figure(figsize=(7, 4.5))
    plt.errorbar(
        df["dataset_size"],
        df["mean_fitness"],
        yerr=df["std_fitness"],
        marker='o',
        color='tab:blue',
        capsize=3,
    )
    plt.xlabel('Dataset Size')
    plt.ylabel('Validation Fitness')
    plt.title('Effect of Dataset Size on GA Optimization')
    plt.tight_layout()

    out_path = os.path.join(out_dir, "dataset_size_experiment_plot.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

    print(f"\nDataset size fitness range: {df['mean_fitness'].min():.4f} to {df['mean_fitness'].max():.4f}")
    print(f"Peak at N={df.loc[df['mean_fitness'].idxmax(), 'dataset_size']}")


def plot_population_size(csv_path, out_dir):
    df = pd.read_csv(csv_path)

    plt.figure(figsize=(7, 4.5))
    plt.errorbar(
        df["population"],
        df["mean_fitness"],
        yerr=df["std_fitness"],
        marker='o',
        color='tab:blue',
        capsize=3,
    )
    plt.xlabel('Population Size')
    plt.ylabel('Validation Fitness')
    plt.title('Population Size Sensitivity')
    plt.tight_layout()

    out_path = os.path.join(out_dir, "population_experiment_plot.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

    print(f"\nPopulation size fitness range: {df['mean_fitness'].min():.4f} to {df['mean_fitness'].max():.4f}")
    print(f"Peak at P={df.loc[df['mean_fitness'].idxmax(), 'population']}")
    print(f"Std range: {df['std_fitness'].min():.4f} to {df['std_fitness'].max():.4f}")


def plot_runtime(csv_path, out_dir):
    df = pd.read_csv(csv_path)

    plt.figure(figsize=(7, 4.5))
    plt.plot(
        df["dataset_size"],
        df["mean_runtime_sec"],
        marker='o',
        color='tab:blue',
    )
    plt.xlabel('Dataset Size')
    plt.ylabel('Mean Runtime (seconds)')
    plt.title('Runtime Scaling of GA Optimization')
    plt.tight_layout()

    out_path = os.path.join(out_dir, "runtime_scaling_plot.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

    peak_idx = df["mean_runtime_sec"].idxmax()
    print(f"\nRuntime range: {df['mean_runtime_sec'].min():.1f}s to {df['mean_runtime_sec'].max():.1f}s")
    print(f"Peak at N={df.loc[peak_idx, 'dataset_size']}: {df.loc[peak_idx, 'mean_runtime_sec']:.1f}s")
    print(f"Runtime at N={df['dataset_size'].iloc[-1]} (largest tested): {df['mean_runtime_sec'].iloc[-1]:.1f}s")


if __name__ == "__main__":
    dataset_csv = sys.argv[1] if len(sys.argv) > 1 else "../experiments/v2_population_experiment/dataset_size_experiment_FIXED.csv"
    population_csv = sys.argv[2] if len(sys.argv) > 2 else "../experiments/v2_population_experiment/population_experiment_FIXED.csv"
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "../paper/figures"

    os.makedirs(out_dir, exist_ok=True)

    plot_dataset_size(dataset_csv, out_dir)
    plot_population_size(population_csv, out_dir)
    plot_runtime(dataset_csv, out_dir)