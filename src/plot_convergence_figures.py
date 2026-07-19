import json
import os
import sys
import matplotlib.pyplot as plt

def plot_convergence(log_path, out_dir):
    with open(log_path) as f:
        log = json.load(f)

    generations = list(range(1, len(log["best"]) + 1))
    best = log["best"]
    avg = log["avg"]
    var = log["var"]

    os.makedirs(out_dir, exist_ok=True)

    # Figure 4: GA Convergence
    plt.figure(figsize=(7, 4.5))
    plt.plot(generations, best, '-', color='tab:blue', linewidth=1.8, label='Best fitness')
    plt.plot(generations, avg, '--', color='tab:orange', linewidth=1.8, label='Average fitness')
    plt.xlabel('Generation')
    plt.ylabel('Fitness score')
    plt.title('Genetic Algorithm Convergence')
    plt.ylim(0, 1.0)
    plt.legend()
    plt.tight_layout()
    fitness_path = os.path.join(out_dir, "fitness_curve_paper.png")
    plt.savefig(fitness_path, dpi=300)
    plt.close()
    print(f"Saved: {fitness_path}")

    # Figure 5: Population Diversity
    plt.figure(figsize=(7, 4.5))
    plt.plot(generations, var, '-', color='tab:blue', linewidth=1.8, label='Population variance')
    plt.xlabel('Generation')
    plt.ylabel('Variance')
    plt.title('Population Diversity Across Generations')
    plt.legend()
    plt.tight_layout()
    diversity_path = os.path.join(out_dir, "diversity_curve.png")
    plt.savefig(diversity_path, dpi=300)
    plt.close()
    print(f"Saved: {diversity_path}")

    # Print stats useful for the paper's prose
    print(f"\nBest fitness: gen1={best[0]:.4f}, min={min(best):.4f}, max={max(best):.4f}")
    print(f"Avg fitness: gen1={avg[0]:.4f}, min={min(avg):.4f}, max={max(avg):.4f}")
    print(f"Variance: gen1={var[0]:.6f}, min={min(var):.6f}, max={max(var):.6f}")

if __name__ == "__main__":
    log_path = sys.argv[1] if len(sys.argv) > 1 else "../experiments/baseline_comparison/b4_fitness_log.json"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "../paper/figures"
    plot_convergence(log_path, out_dir)
    