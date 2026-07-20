"""
runner_multiturn.py

Multi-turn equivalent of ga/runner.py's run_ga(). Mirrors its structure
(elitism, tournament selection, logging format) as closely as possible
-- same operators.py functions (crossover/mutate/tournament_select) are
reused UNCHANGED, since they operate on Genome objects and fitness
lists regardless of what "fitness" means underneath.

KEY DIFFERENCE FROM run_ga(): train_data here is a List[Dict] of
sessions (each {"turns": [user message strings...], "risk_label": str}),
not a pandas DataFrame of single prompts -- conversations don't fit a
flat tabular row model well. Use load_sessions() below to build this
list from data/multiturn_cleaned.jsonl.

COMPUTE COST WARNING: scoring one conversation costs roughly
(genome.history_turns capped at the conversation length) x the cost of
a single-turn fitness() call, since each scored turn requires its own
generate_response() call. With history_turns ranging [4,24], a typical
multi-turn eval_n=500 could cost 15-20x more generate_response() calls
per generation than the equivalent single-turn eval_n=500. STRONGLY
recommend running a small test (small pop_size, generations, eval_n)
first and measuring actual wall-clock time before scaling up to
anything resembling the single-turn paper's main experiment
configuration (P=100, T=20, |I|=600).

best_genome_overall is returned as an actual Genome object (not just
logged to stdout) and the log dict is fully serializable -- this
avoids the exact problem your single-turn v0.9 work hit, where an
early gamma value was only visible in a terminal printout and never
serialized, making it unverifiable later.
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
    """
    Multi-turn seed genomes. Same w_s/w_e/w_c/theta_mid/theta_high/gamma
    balances as get_seed_genomes() in runner.py, but with history_turns
    added explicitly per seed (not left to the dataclass default),
    mirroring how gamma already varies deliberately per seed rather
    than being uniform.

    Rationale for history_turns choices (a starting hypothesis, not
    derived from data -- worth revisiting once real multi-turn GA
    results exist, same as how the single-turn seeds' weights were
    hand-chosen and only later validated/superseded by evolved values):
      - balanced:        12 (moderate context window)
      - safety-heavy:      8 (shorter window -- focuses fitness signal
                              on recent risk, consistent with a
                              safety-first strategy prioritizing acting
                              on the most current signal)
      - empathy-heavy:    16 (longer window -- more conversation history
                              to draw reflective/validating content from)
      - structure-heavy:  20 (broadest window -- more turns over which
                              to demonstrate consistent structural
                              support)

    All four use memory_window=512, matching the existing single-turn
    seeds -- already safe under the memory_window=256 exclusion fix.
    """
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
    """
    Loads multiturn_cleaned.jsonl into the {"turns": [...str...],
    "risk_label": str} format conversation_fitness_over_dataset()
    expects -- extracts just user message strings from each session's
    nested turn objects (same extraction pattern as
    smoke_test_multiturn.py's load_sessions()).
    """
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


def run_ga_multiturn(
    sessions: List[Dict],
    pop_size: int = 30,
    generations: int = 40,
    eval_n: int = 500,
    seed: int = SEED,
    use_seed_genomes: bool = True,
) -> Tuple[Genome, Dict[str, List[float]]]:
    """
    Multi-turn GA loop. Structurally identical to run_ga() in
    runner.py -- same elitism (top 2), same tournament selection,
    same crossover/mutate calls, same log format -- with
    conversation_fitness_over_dataset() substituted for fitness(),
    and session-list sampling substituted for DataFrame.sample().

    See module docstring for the compute-cost warning before running
    this with eval_n/pop_size/generations anywhere near single-turn
    main-experiment scale.
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


if __name__ == "__main__":
    import time

    print("Loading sessions...")
    all_sessions = load_sessions("data/multiturn_cleaned.jsonl")
    print(f"Loaded {len(all_sessions)} sessions.\n")

    print("Running SMALL test config to measure real wall-clock time "
          "before scaling up (pop_size=6, generations=2, eval_n=10)...\n")

    t0 = time.time()
    best_genome, log = run_ga_multiturn(
        sessions=all_sessions,
        pop_size=6,
        generations=2,
        eval_n=10,
        use_seed_genomes=True,
    )
    elapsed = time.time() - t0

    print(f"\nSmall test run completed in {elapsed:.1f} seconds.")
    print(f"Best genome: {best_genome}")
    print(f"Best fitness: {log['best'][-1]:.4f}")

    # Rough extrapolation to help decide what's actually feasible --
    # NOT a precise estimate (fitness cost varies with genome
    # history_turns and conversation length), just an order-of-magnitude
    # sanity check before committing to a longer run.
    per_gen_cost = elapsed / 2  # 2 generations in this test
    print(f"\nApprox cost per generation at this scale: {per_gen_cost:.1f}s")
    print("Scale this roughly linearly with pop_size and eval_n to "
          "estimate a larger run's total time before starting it.")