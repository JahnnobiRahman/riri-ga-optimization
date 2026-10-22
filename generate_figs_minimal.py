import json
import matplotlib
matplotlib.use('Agg')  # Must be before pyplot import
import matplotlib.pyplot as plt

# Load data
with open('experiments/baseline_comparison/b4_fitness_log.json') as f:
    log = json.load(f)

generations = list(range(1, len(log['best']) + 1))

# Figure 4: Fitness curve
fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=120)
ax.plot(generations, log['best'], linewidth=2.5, label='Best fitness')
ax.plot(generations, log['avg'], linewidth=2.5, linestyle='--', label='Average fitness')
ax.set_title('Genetic Algorithm Convergence')
ax.set_xlabel('Generation')
ax.set_ylabel('Fitness score')
ax.set_ylim(0, 1.02)
ax.legend(frameon=True)
ax.grid(True, alpha=0.25, linewidth=0.8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
fig.savefig('paper/figures/fitness_curve_paper.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('✓ Saved: paper/figures/fitness_curve_paper.png')

# Figure 5: Diversity curve
fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=120)
ax.plot(generations, log['var'], linewidth=2.5, label='Population variance')
ax.set_title('Population Diversity Across Generations')
ax.set_xlabel('Generation')
ax.set_ylabel('Variance')
ax.legend(frameon=True)
ax.grid(True, alpha=0.25, linewidth=0.8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
fig.tight_layout()
fig.savefig('paper/figures/diversity_curve.png', dpi=300, bbox_inches='tight')
plt.close(fig)
print('✓ Saved: paper/figures/diversity_curve.png')

print(f'\n✓ Both figures regenerated from corrected B4 run!')
print(f'  Gen 1: best={log["best"][0]:.4f}, avg={log["avg"][0]:.4f}')
print(f'  Gen 20: best={log["best"][-1]:.4f}, avg={log["avg"][-1]:.4f}')
