import os
import json
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.append("src")

# modular imports
from evaluation.risk_labeling import label_risk
from ga.runner import run_ga
from experiments.population_experiment import population_size_experiment
from evaluation.scoring import evaluate_breakdown
from ga.genome import Genome
from experiments.dataset_size_experiment import dataset_size_experiment


# ======================
# 0) Reproducibility
# ======================

SEED = 7
random.seed(SEED)
np.random.seed(SEED)


# ======================
# 1) Project paths
# ======================

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "phq4_cleaned.csv")

EXPERIMENT_NAME = "v2_population_experiment"

OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", EXPERIMENT_NAME)

os.makedirs(OUT_DIR, exist_ok=True)


# ======================
# 2) Load dataset
# ======================

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in df.columns:
        df[col] = ""

if "total_score" not in df.columns:
    df["total_score"] = 0

df["common_themes"] = df["common_themes"].fillna("")
df["thought_progression"] = df["thought_progression"].fillna("")
df["risk_assessment"] = df["risk_assessment"].fillna("")
df["total_score"] = df["total_score"].fillna(0)


# ======================
# 3) Risk labeling
# ======================

print("Applying risk labeling...")

df["risk_label"] = df.apply(label_risk, axis=1)


# ======================
# 4) Prompt construction
# ======================

df["user_prompt"] = (
    df["common_themes"].astype(str).str.strip()
    + " | "
    + df["thought_progression"].astype(str).str.strip()
).str.strip(" |")

df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)

print("Usable rows:", len(df))


# ======================
# 5) Train / validation split
# ======================

df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

split = int(0.8 * len(df))

train_df = df.iloc[:split].reset_index(drop=True)
val_df = df.iloc[split:].reset_index(drop=True)

print("Train size:", len(train_df))
print("Validation size:", len(val_df))


# ======================
# 6) Run GA
# ======================

print("\nRunning GA optimization...")

# ======================
# QUICK MODE SWITCH
# ======================
QUICK_MODE = False

if QUICK_MODE:
    pop_size = 30
    generations = 5
    eval_n = 100
else:
    pop_size = 100
    generations = 20
    eval_n = 600

# ======================
# RUN GA
# ======================
best_g, log = run_ga(
    train_df,
    pop_size=pop_size,
    generations=generations,
    eval_n=eval_n,
    seed=7
)

import json
log_path = os.path.join(OUT_DIR, "ga_log.json")
with open(log_path, "w") as f:
    json.dump(log, f, indent=2)
print("Saved GA log to:", log_path)




from evaluation.trace_export import export_traces

TRACE_PATH = os.path.join(OUT_DIR, "trace_analysis.csv")

if QUICK_MODE:
    export_traces(best_g, val_df, TRACE_PATH, n=50)
else:
    export_traces(best_g, val_df, TRACE_PATH, n=200)



from analysis.trace_analysis_plots import run_all_plots

PLOT_DIR = os.path.join(OUT_DIR, "analysis_plots")

run_all_plots(TRACE_PATH, PLOT_DIR)


# ======================
# 7) Baseline configuration
# ======================

baseline = Genome(
    p_id=1,
    w_s=0.50,
    w_e=0.30,
    w_c=0.20,
    memory_window=512,
    theta_mid=0.55,
    theta_high=0.80
)

baseline.normalize()


# ======================
# 8) Validation evaluation
# ======================

print("\nEvaluating baseline vs optimized")

baseline_metrics = evaluate_breakdown(baseline, val_df)
best_metrics = evaluate_breakdown(best_g, val_df)

print("Baseline metrics:", baseline_metrics)
print("Optimized metrics:", best_metrics)


# ======================
# 9) Save config
# ======================

config = {
    "population_size": pop_size,
    "generations": generations,
    "seed": SEED,
    "mode": "quick" if QUICK_MODE else "full"
}

with open(os.path.join(OUT_DIR, "config.json"), "w") as f:
    json.dump(config, f, indent=4)


# ======================
# 10) Population experiment
# ======================

if not QUICK_MODE:
    print("\nRunning population size experiment...")
    pop_results = population_size_experiment(train_df, val_df)
    pop_csv = os.path.join(OUT_DIR, "population_experiment.csv")
    pop_results.to_csv(pop_csv, index=False)
    print("Saved:", pop_csv)

    # ======================
    # 11) Plot population experiment
    # ======================
    plt.figure()
    plt.errorbar(
        pop_results["population"],
        pop_results["mean_fitness"],
        yerr=pop_results["std_fitness"],
        marker="o"
    )
    plt.xlabel("Population Size")
    plt.ylabel("Validation Fitness")
    plt.title("Population Size Sensitivity")
    plt.tight_layout()

    plot_path = os.path.join(OUT_DIR, "population_experiment_plot.png")
    plt.savefig(plot_path, dpi=300)
    print("Saved:", plot_path)
else:
    print("\nSkipping population experiment in QUICK_MODE.")


print("\nExperiment completed.")


print("\n==============================")
print("DATASET SIZE EXPERIMENT")
print("==============================")

if not QUICK_MODE:


    dataset_results, dataset_raw = dataset_size_experiment(train_df, val_df)
    DATASET_RESULT_PATH = os.path.join(
        OUT_DIR,
        "dataset_size_experiment.csv"
    )
    dataset_results.to_csv(DATASET_RESULT_PATH, index=False)
    print("Saved dataset size experiment to:")
    print(DATASET_RESULT_PATH)

    DATASET_RAW_PATH = os.path.join(
        OUT_DIR,
        "dataset_size_raw_runs.csv"
    )
    dataset_raw.to_csv(DATASET_RAW_PATH, index=False)
    print("Saved dataset size raw runs to:")
    print(DATASET_RAW_PATH)

    plt.figure()
    plt.errorbar(
        dataset_results["dataset_size"],
        dataset_results["mean_fitness"],
        yerr=dataset_results["std_fitness"],
        marker="o"
    )
    plt.xlabel("Dataset Size")
    plt.ylabel("Validation Fitness")
    plt.title("Effect of Dataset Size on GA Optimization")
    plt.tight_layout()

    DATASET_PLOT = os.path.join(
        OUT_DIR,
        "dataset_size_experiment_plot.png"
    )
    plt.savefig(DATASET_PLOT, dpi=300)
    print("Saved dataset size plot:", DATASET_PLOT)
else:
    print("Skipping dataset size experiment in QUICK_MODE.")