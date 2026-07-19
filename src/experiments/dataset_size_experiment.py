import time
import numpy as np
import pandas as pd

from ga.runner import run_ga
from evaluation.scoring import evaluate_breakdown


def dataset_size_experiment(train_df, val_df):

    dataset_sizes = [100, 300, 600, 1200, len(train_df)]

    results = []
    raw_results = []

    for size in dataset_sizes:

        print("\n==============================")
        print(f"Testing dataset size: {size}")
        print("==============================")

        subset = train_df.sample(
        n=min(size, len(train_df)),
        random_state=42,  # ADD THIS — any fixed value works, just needs to be consistent
    ).reset_index(drop=True)

        fitness_runs = []
        runtimes = []

        for run in range(1, 6):

            print(f"Run {run}/5")

            start = time.time()

            best_g, log = run_ga(
                subset,
                pop_size=100,
                generations=20,
                eval_n=min(600, len(subset)),
                seed=run
            )

            metrics = evaluate_breakdown(best_g, val_df, n=400)

            runtime = time.time() - start

            fitness_runs.append(metrics["fitness"])
            runtimes.append(runtime)

            raw_results.append({
    "dataset_size": size,
    "run_id": run,
    "fitness": metrics["fitness"],
    "runtime_sec": runtime
})

        mean_fit = np.mean(fitness_runs)
        std_fit = np.std(fitness_runs)
        mean_runtime = np.mean(runtimes)

        print("\nSummary:")
        print("Mean fitness:", mean_fit)
        print("Std fitness:", std_fit)
        print("Mean runtime:", mean_runtime)

        results.append({
            "dataset_size": size,
            "mean_fitness": mean_fit,
            "std_fitness": std_fit,
            "mean_runtime_sec": mean_runtime
        })

    return pd.DataFrame(results), pd.DataFrame(raw_results)