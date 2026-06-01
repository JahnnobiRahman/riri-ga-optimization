import pandas as pd
import matplotlib.pyplot as plt
import os


def plot_empathy_vs_fitness(df, out_dir):
    plt.figure()
    plt.scatter(df["empathy_score"], df["structure_score"])
    plt.xlabel("Empathy Score")
    plt.ylabel("Structure Score")
    plt.title("Empathy vs Structure")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "empathy_vs_structure.png"), dpi=300)
    plt.close()


def plot_safety_by_risk(df, out_dir):
    # Force clinical order: low → mid → high
    risk_order = ["low", "mid", "high"]

    fig, ax = plt.subplots()

    groups = [
        df.loc[df["risk_label"] == r, "safety_score"].dropna().values
        for r in risk_order
    ]

    ax.boxplot(groups, labels=risk_order)

    ax.set_title("Safety Score by Risk Level")
    ax.set_xlabel("Risk Label")
    ax.set_ylabel("Safety Score")
    fig.tight_layout()

    fig.savefig(os.path.join(out_dir, "safety_by_risk.png"), dpi=300)
    plt.close(fig)


def plot_structure_usage(df, out_dir):
    structure_counts = [
        df["has_grounding"].mean(),
        df["has_action"].mean(),
        df["has_question"].mean()
    ]

    labels = ["Grounding", "Action", "Question"]

    plt.figure()
    plt.bar(labels, structure_counts)
    plt.xlabel("Component")
    plt.ylabel("Usage Frequency")
    plt.title("Structure Component Usage")
    plt.tight_layout()

    plt.savefig(os.path.join(out_dir, "structure_usage.png"), dpi=300)
    plt.close()


def run_all_plots(csv_path, out_dir):
    df = pd.read_csv(csv_path)

    os.makedirs(out_dir, exist_ok=True)

    plot_empathy_vs_fitness(df, out_dir)
    plot_safety_by_risk(df, out_dir)
    plot_structure_usage(df, out_dir)

    print("Saved all analysis plots to:", out_dir)


if __name__ == "__main__":
    # Defaults: same experiment bundle as main_ga_riri.py
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    _csv = os.path.join(_root, "experiments", "v2_population_experiment", "trace_analysis.csv")
    _out = os.path.join(_root, "experiments", "v2_population_experiment", "analysis_plots")
    run_all_plots(_csv, _out)