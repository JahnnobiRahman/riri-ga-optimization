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
    csv_path = os.path.join(base_path, "trace_analysis.csv")
    output_dir = os.path.join(base_path, "analysis_plots")

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(csv_path)

    required_cols = ["generation", "best", "avg", "var"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        # Fallback: adapt trace-level CSV into a convergence proxy.
        score_cols = ["empathy_score", "safety_score", "structure_score", "length_penalty"]
        if all(col in df.columns for col in score_cols):
            # Match the scoring.py weights to build per-row fitness proxy.
            df = df.copy()
            df["fitness"] = (
                0.35 * df["empathy_score"]
                + 0.35 * df["safety_score"]
                + 0.25 * df["structure_score"]
                - 0.05 * df["length_penalty"]
            )
            df["generation"] = range(1, len(df) + 1)
            df["best"] = df["fitness"].cummax()
            df["avg"] = df["fitness"].expanding().mean()
            df["var"] = df["fitness"].expanding().var().fillna(0.0)
            print("Missing GA columns; using trace-derived convergence proxy.")
        else:
            raise ValueError(
                "Missing columns in trace_analysis.csv: "
                f"{missing}. Also need {score_cols} for fallback."
            )

    apply_paper_style()
    save_fitness_curve(df, output_dir)
    save_diversity_curve(df, output_dir)

    print("Saved paper-style plots:")
    print(os.path.join(output_dir, "fitness_curve_paper.png"))
    print(os.path.join(output_dir, "diversity_curve_paper.png"))


if __name__ == "__main__":
    main()
    