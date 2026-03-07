import random
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List

from ga.genome import Genome, random_genome
from ga.operators import crossover, mutate, tournament_select
from evaluation.scoring import fitness

SEED = 7

# ======================
# 9) Run GA (with logging)
# ======================
def run_ga(train_data: pd.DataFrame,
           pop_size: int = 30,
           generations: int = 40,
           eval_n: int = 500,
           seed: int = SEED) -> Tuple[Genome, Dict[str, List[float]]]:

    random.seed(seed)
    np.random.seed(seed)

    # Evaluate on a subset each run for speed (keep stable with seed)
    eval_data = train_data.sample(n=min(eval_n, len(train_data)), random_state=seed).reset_index(drop=True)

    pop = [random_genome() for _ in range(pop_size)]
    fits = [fitness(g, eval_data) for g in pop]

    log = {"best": [], "avg": [], "var": []}

    for gen in range(1, generations + 1):
        best_i = int(np.argmax(fits))
        best_fit = float(fits[best_i])
        avg_fit = float(np.mean(fits))
        var_fit = float(np.var(fits))

        log["best"].append(best_fit)
        log["avg"].append(avg_fit)
        log["var"].append(var_fit)

        print(f"Gen {gen:02d} | best={best_fit:.4f} avg={avg_fit:.4f} var={var_fit:.6f} | best_genome={pop[best_i]}")

        # elitism: keep top 2
        elite_ids = np.argsort(fits)[-2:]
        new_pop = [pop[i] for i in elite_ids]

        while len(new_pop) < pop_size:
            p1 = tournament_select(pop, fits, k=3)
            p2 = tournament_select(pop, fits, k=3)
            child = mutate(crossover(p1, p2), pm=0.30)
            new_pop.append(child)

        pop = new_pop
        fits = [fitness(g, eval_data) for g in pop]

    best_i = int(np.argmax(fits))
    return pop[best_i], log