import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

with open('experiments/baseline_comparison/b4_fitness_log.json') as f:
    log = json.load(f)

gens = list(range(1, 21))

# Figure 4
fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.plot(gens, log['best'], lw=2.5, label='Best fitness')
ax.plot(gens, log['avg'], lw=2.5, ls='--', label='Average fitness')
ax.set_title('Genetic Algorithm Convergence')
ax.set_xlabel('Generation'); ax.set_ylabel('Fitness score')
ax.set_ylim(0, 1.02); ax.legend(); ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig('paper/figures/fitness_curve_paper.png', dpi=300)
plt.close()

# Figure 5
fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.plot(gens, log['var'], lw=2.5, label='Population variance')
ax.set_title('Population Diversity Across Generations')
ax.set_xlabel('Generation'); ax.set_ylabel('Variance')
ax.legend(); ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig('paper/figures/diversity_curve.png', dpi=300)
print('Done!')
