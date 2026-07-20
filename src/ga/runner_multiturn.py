"""
runner_multiturn.py (v2 -- proper train/val split)

FIX: previously, run_ga_multiturn() sampled its evaluation subset
directly from the full session list with no train/val separation --
every GA result was evaluated in-sample, unlike single-turn's
baseline_comparison.py, which explicitly splits 80/20, trains only on
train_df, and evaluates only on held-out val_df. This version adds
split_sessions(), matching that methodology exactly (same 80/20
fraction, same seed-based reproducibility). The fix is applied at the
call site -- pass only train_sessions into run_ga_multiturn(), then
evaluate the resulting best_genome separately against val_sessions.

Everything else is unchanged from the previous version.
"""

import json
import random
from typing import Tuple, Dict, List

import numpy as np

from ga.genome import Genome, random_genome
from ga.operators import crossover, mutate, tournament_select
from evaluation.conversation_scoring import conversation_fitness_over_dataset

SEED = 7


def get_seed_genomes_multiturn() -> List[Genome]:
    seeds = []

    seeds.append(Genome(
        p_id=1, w_s=0.33, w_e=0.33, w_c=0.34,
        memory_window=512, theta_mid=0.55, theta_high=0.80,
        gamma=0.10, history_turns=12,
    ))

    seeds.append(Genome(
        p_id=1, w_s=0.70, w_e=0.15, w_c=0.15,
        memory_window=512, theta_mid=0.50, theta_high=0.75,
        gamma=0.15, history_turns=8,
    ))

    seeds.append(Genome(
        p_id=1, w_s=0.20, w_e=0.60, w_c=0.20,
        memory_window=512, theta_mid=0.60, theta_high=0.85,
        gamma=0.05, history_turns=16,
    ))

    seeds.append(Genome(
        p_id=1, w_s=0.20, w_e=0.20, w_c=0.60,
        memory_window=512, theta_mid=0.55, theta_high=0.80,
        gamma=0.12, history_turns=20,
    ))

    for s in seeds:
        s.normalize()

    return seeds


def load_sessions(path: str) -> List[Dict]:
    sessions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            session = json.loads(line)
            user_turns = [
                t["message"] for t in session["turns"]
                if t.get("is_bot") == 0
            ]
            if user_turns:
                sessions.append({
                    "turns": user_turns,
                    "risk_label": session["risk_label"],
                })
    return sessions


def split_sessions(
    sessions: List[Dict],
    seed: int = SEED,
    train_frac: float = 0.8,
) -> Tuple[List[Dict], List[Dict]]:
    """
    80/20 train/val split, matching single-turn's baseline_comparison.py
    methodology exactly (same split fraction, same seed-based
    reproducibility -- shuffle once with the given seed, then split).
    """
    shuffled = sessions.copy()
    random.Random(seed).shuffle(shuffled)
    split_idx = int(train_frac * len(shuffled))
    train_sessions = shuffled[:split_idx]
    val_sessions = shuffled[split_idx:]
    return train_sessions, val_sessions


def run_ga_multiturn(
    sessions: List[Dict],
    pop_size: int = 30,
    generations: int = 40,
    eval_n: int = 500,
    seed: int = SEED,
    use_seed_genomes: bool = True,
) -> Tuple[Genome, Dict[str, List[float]]]:
    """
    Multi-turn GA loop. IMPORTANT: `sessions` here should be the
    TRAINING split (from split_sessions()), not the full dataset --
    the caller is responsible for splitting before calling this, and
    for evaluating the returned best_genome separately against a
    held-out validation split.
    """
    random.seed(seed)
    np.random.seed(seed)
    rnd = random.Random(seed)

    eval_sessions = rnd.sample(sessions, k=min(eval_n, len(sessions)))

    if use_seed_genomes:
        seed_genomes = get_seed_genomes_multiturn()
        if pop_size <= len(seed_genomes):
            pop = seed_genomes[:pop_size]
        else:
            pop = seed_genomes + [random_genome() for _ in range(pop_size - len(seed_genomes))]
    else:
        pop = [random_genome() for _ in range(pop_size)]

    fits = [conversation_fitness_over_dataset(g, eval_sessions) for g in pop]

    log = {"best": [], "avg": [], "var": []}

    best_genome_overall = None
    best_fit_overall = -float("inf")

    for gen in range(1, generations + 1):
        best_i = int(np.argmax(fits))
        best_fit = float(fits[best_i])
        avg_fit = float(np.mean(fits))
        var_fit = float(np.var(fits))
        log["best"].append(best_fit)
        log["avg"].append(avg_fit)
        log["var"].append(var_fit)
        print(f"Gen {gen:02d} | best={best_fit:.4f} avg={avg_fit:.4f} "
              f"var={var_fit:.6f} | best_genome={pop[best_i]}")

        if best_fit > best_fit_overall:
            best_fit_overall = best_fit
            best_genome_overall = pop[best_i]

        elite_ids = np.argsort(fits)[-2:]
        new_pop = [pop[i] for i in elite_ids]
        while len(new_pop) < pop_size:
            p1 = tournament_select(pop, fits, k=3)
            p2 = tournament_select(pop, fits, k=3)
            child = mutate(crossover(p1, p2), pm=0.30)
            new_pop.append(child)
        pop = new_pop
        fits = [conversation_fitness_over_dataset(g, eval_sessions) for g in pop]

    return best_genome_overall, log