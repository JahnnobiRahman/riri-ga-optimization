"""
Regenerate Figure 9 (runtime scaling with dataset size) from the
nested-subset dataset-size experiment's corrected results
(dataset_size_corrected.csv), under the frozen, corrected scorer.

Prefer loading directly from the actual CSV output rather than the
hardcoded fallback below, to avoid transcription error.
"""

import csv
import matplotlib.pyplot as plt

CSV_PATH = "experiments/baseline_comparison/dataset_size_corrected.csv"

try:
    dataset_sizes = []
    runtimes = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("dataset_size"):
                continue
            dataset_sizes.append(int(row["dataset_size"]))
            runtimes.append(float(row["mean_runtime_sec"]))
    print(f"Loaded {len(dataset_sizes)} rows from {CSV_PATH}")
except (FileNotFoundError, KeyError, ValueError) as e:
    print(f"Could not load {CSV_PATH} ({e}); falling back to transcribed values.")
    print("Recommend verifying these against the actual CSV before using.")
    dataset_sizes = [100, 300, 600, 1200, 2297]
    runtimes = [15.854033279418946, 46.9573935508728, 98.39848494529724,
                478.2022132396698, 205.6154537677765]

print("Dataset sizes:", dataset_sizes)
print("Mean runtimes (s):", runtimes)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(dataset_sizes, runtimes, marker='o', color='tab:blue', linewidth=2)
ax.set_xlabel('Dataset Size')
ax.set_ylabel('Mean Runtime (seconds)')
ax.set_title('Runtime Scaling of GA Optimization with Dataset Size')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('figures/runtime_scaling_plot.png', dpi=150)
plt.close()
print("Saved figures/runtime_scaling_plot.png")