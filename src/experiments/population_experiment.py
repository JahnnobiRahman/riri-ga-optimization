import time
import numpy as np
import pandas as pd

from ga.runner import run_ga
from evaluation.scoring import evaluate_breakdown


def population_size_experiment(train_df, val_df):

    population_sizes = [30, 50, 100, 200, 300, 400]

    results = []

    for pop in population_sizes:

        print("\n==============================")
        print(f"Testing population size: {pop}")
        print("==============================")

        fitness_runs = []
        runtimes = []

        for run in range(1, 6):

            print(f"\nRun {run}/5")

            start = time.time()

            best_g, log = run_ga(
                train_df,
                pop_size=pop,
                generations=20,
                eval_n=600,
                seed=run
            )

            metrics = evaluate_breakdown(best_g, val_df, n=400)

            runtime = time.time() - start

            fitness_runs.append(metrics["fitness"])
            runtimes.append(runtime)

        mean_fit = np.mean(fitness_runs)
        std_fit = np.std(fitness_runs)
        mean_runtime = np.mean(runtimes)

        print("\nSummary:")
        print("Mean fitness:", mean_fit)
        print("Std fitness:", std_fit)
        print("Mean runtime:", mean_runtime)

        results.append({
            "population": pop,
            "mean_fitness": mean_fit,
            "std_fitness": std_fit,
            "mean_runtime_sec": mean_runtime
        })

    return pd.DataFrame(results)