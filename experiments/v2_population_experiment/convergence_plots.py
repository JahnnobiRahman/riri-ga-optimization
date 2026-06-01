import os
import pandas as pd
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
    fig.savefig(os.path.join(output_dir, "fitness_curve_paper.png"), bbox_inches="tight")
    plt.close(fig)


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
    fig.savefig(os.path.join(output_dir, "diversity_curve_paper.png"), bbox_inches="tight")
    plt.close(fig)


def main():
    base_path = os.path.dirname(__file__)
    output_dir = os.path.join(base_path, "analysis_plots")
    os.makedirs(output_dir, exist_ok=True)

    # Load real GA log — no fallback
    log_path = os.path.join(base_path, "ga_log.json")
    if not os.path.exists(log_path):
        raise FileNotFoundError(
            f"ga_log.json not found at {log_path}\n"
            "Run main_ga_riri.py with QUICK_MODE=False first."
        )

    import json
    with open(log_path) as f:
        log = json.load(f)

    df = pd.DataFrame({
        "generation": range(1, len(log["best"]) + 1),
        "best": log["best"],
        "avg":  log["avg"],
        "var":  log["var"],
    })

    print(f"Loaded real GA log: {len(df)} generations")
    print(f"Best fitness: Gen 1 = {df['best'].iloc[0]:.4f}, "
          f"Gen {len(df)} = {df['best'].iloc[-1]:.4f}")

    apply_paper_style()
    save_fitness_curve(df, output_dir)
    save_diversity_curve(df, output_dir)

    print("Saved paper-style plots:")
    print(os.path.join(output_dir, "fitness_curve_paper.png"))
    print(os.path.join(output_dir, "diversity_curve_paper.png"))

if __name__ == "__main__":
    main()
    