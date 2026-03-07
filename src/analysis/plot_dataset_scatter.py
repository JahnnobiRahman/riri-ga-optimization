import os
import pandas as pd
import matplotlib.pyplot as plt

# Paths relative to project root (parent of src/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENT_DIR = os.path.join(PROJECT_ROOT, "experiments", "v2_population_experiment")

# load raw results
df = pd.read_csv(os.path.join(EXPERIMENT_DIR, "dataset_size_raw_runs.csv"))

# compute mean fitness
mean_df = df.groupby("dataset_size")["fitness"].mean().reset_index()

plt.figure()

# scatter plot of all runs
plt.scatter(
    df["dataset_size"],
    df["fitness"],
    alpha=0.6,
    label="Individual Runs"
)

# mean fitness line
plt.plot(
    mean_df["dataset_size"],
    mean_df["fitness"],
    marker="o",
    linewidth=2,
    label="Mean Fitness"
)

plt.xlabel("Dataset Size")
plt.ylabel("Validation Fitness")
plt.title("GA Performance vs Dataset Size")

plt.legend()
plt.grid(True)

plt.savefig(os.path.join(EXPERIMENT_DIR, "dataset_size_scatter_plot.png"), dpi=300)

plt.show()