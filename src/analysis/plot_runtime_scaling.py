import os
import pandas as pd
import matplotlib.pyplot as plt

# Paths relative to project root (parent of src/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENT_DIR = os.path.join(PROJECT_ROOT, "experiments", "v2_population_experiment")

# load raw results
df = pd.read_csv(os.path.join(EXPERIMENT_DIR, "dataset_size_raw_runs.csv"))

# compute mean runtime per dataset size
runtime_df = df.groupby("dataset_size")["runtime_sec"].mean().reset_index()

plt.figure()

plt.plot(
    runtime_df["dataset_size"],
    runtime_df["runtime_sec"],
    marker="o",
    linewidth=2
)

plt.xlabel("Dataset Size")
plt.ylabel("Mean Runtime (seconds)")
plt.title("Runtime Scaling of GA Optimization")

plt.grid(True)

plt.savefig(os.path.join(EXPERIMENT_DIR, "runtime_scaling_plot.png"), dpi=300)

plt.show()