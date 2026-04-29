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


def plot_safety_by_risk(df, out_dir):
    plt.figure()

    df.boxplot(column="safety_score", by="risk_label")

    plt.title("Safety Score by Risk Level")
    plt.suptitle("")  # remove default title
    plt.xlabel("Risk Label")
    plt.ylabel("Safety Score")
    plt.tight_layout()

    plt.savefig(os.path.join(out_dir, "safety_by_risk.png"), dpi=300)


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


def run_all_plots(csv_path, out_dir):
    df = pd.read_csv(csv_path)

    os.makedirs(out_dir, exist_ok=True)

    plot_empathy_vs_fitness(df, out_dir)
    plot_safety_by_risk(df, out_dir)
    plot_structure_usage(df, out_dir)

    print("Saved all analysis plots to:", out_dir)