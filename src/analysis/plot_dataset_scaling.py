import pandas as pd
import matplotlib.pyplot as plt

# load results
df = pd.read_csv("experiments/v2_population_experiment/dataset_size_experiment.csv")

plt.figure()

plt.errorbar(
    df["dataset_size"],
    df["mean_fitness"],
    yerr=df["std_fitness"],
    marker="o",
    capsize=4
)

plt.xlabel("Dataset Size")
plt.ylabel("Validation Fitness")
plt.title("Effect of Dataset Size on GA Optimization")

plt.grid(True)

plt.savefig("experiments/v2_population_experiment/dataset_size_scaling_plot.png")

plt.show()