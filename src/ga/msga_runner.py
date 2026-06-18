"""
msga_runner.py
==============
Multiple Seeds Based Genetic Algorithm (MSGA) initialization for EvoRiri.

Implements the domain-division seeding approach from:
    Kabir, M.M.J., Xu, S., Kang, B.H., & Zhao, Z. (2017).
    "A new multiple seeds based genetic algorithm for discovering a set of
    interesting Boolean association rules."
    Expert Systems With Applications, 74, 55-69.

Instead of hand-designed seeds (runner.py), this module:
    1. Divides the genome solution space into m equal domains
       using Euclidean distance from the initial chromosome.
    2. Randomly generates candidates and assigns each to its domain archive.
    3. Evaluates all candidates and selects the top-fitness genome
       from each archive as a seed.
    4. Generates the initial population by mutating each seed,
       giving m * (pop_size // m) individuals with guaranteed
       coverage across the solution space.

Usage:
    from ga.msga_runner import run_ga_msga

    best_genome, log = run_ga_msga(
        train_data, pop_size=100, generations=20, eval_n=600, seed=7
    )

Branch: v0.7-msga-seeded-init
"""

import math
import random
import numpy as np
import pandas as pd
from dataclasses import asdict
from typing import List, Tuple, Dict

from ga.genome import Genome, random_genome, BASE_TEMPLATES
from ga.operators import crossover, mutate, tournament_select
from evaluation.scoring import fitness


# ─────────────────────────────────────────────
# Genome space boundaries
# These must stay consistent with genome.py
# ─────────────────────────────────────────────

# Continuous genes and their [min, max] bounds
# Order: w_s, w_e, w_c, theta_mid, theta_high
# Note: weights are pre-normalisation values
GENE_BOUNDS = {
    "w_s":        (0.10, 1.0),
    "w_e":        (0.10, 1.0),
    "w_c":        (0.10, 1.0),
    "theta_mid":  (0.40, 0.70),
    "theta_high": (0.70, 0.95),
}

# Discrete genes — not included in Euclidean distance
# (following Kabir 2017: distance computed on continuous genes only)
DISCRETE_GENES = {
    "p_id":          list(BASE_TEMPLATES.keys()),   # [0, 1, 2]
    "memory_window": [256, 512, 768, 1024],
}

# Fixed endpoints of the continuous solution space
# (initial = all minimums, end = all maximums)
G_INIT = np.array([v[0] for v in GENE_BOUNDS.values()])  # shape (5,)
G_END  = np.array([v[1] for v in GENE_BOUNDS.values()])  # shape (5,)


# ─────────────────────────────────────────────
# Helper: genome → continuous vector
# ─────────────────────────────────────────────

def genome_to_vec(g: Genome) -> np.ndarray:
    """Extract the 5 continuous genes as a numpy vector."""
    return np.array([g.w_s, g.w_e, g.w_c, g.theta_mid, g.theta_high])


def vec_to_genome(vec: np.ndarray, p_id: int = 1,
                  memory_window: int = 512) -> Genome:
    """Reconstruct a Genome from a continuous vector."""
    g = Genome(
        p_id=p_id,
        w_s=float(np.clip(vec[0], *GENE_BOUNDS["w_s"])),
        w_e=float(np.clip(vec[1], *GENE_BOUNDS["w_e"])),
        w_c=float(np.clip(vec[2], *GENE_BOUNDS["w_c"])),
        memory_window=memory_window,
        theta_mid=float(np.clip(vec[3], *GENE_BOUNDS["theta_mid"])),
        theta_high=float(np.clip(vec[4], *GENE_BOUNDS["theta_high"])),
    )
    g.normalize()
    return g


# ─────────────────────────────────────────────
# Step 1: Euclidean distance from G_INIT
# ─────────────────────────────────────────────

def euclidean_from_init(g: Genome) -> float:
    """
    Distance of genome g from the initial (minimum) chromosome.
    Computed on continuous genes only, following Kabir (2017) Eq. 2.
    """
    vec = genome_to_vec(g)
    return float(np.sqrt(np.sum((vec - G_INIT) ** 2)))



# ─────────────────────────────────────────────
# Step 2: Build m archives via domain division
# ─────────────────────────────────────────────

def compute_empirical_boundaries(m: int, n_samples: int = 500) -> List[float]:
    """
    Compute domain boundaries from the actual distribution of random genomes.

    The problem with theoretical min/max boundaries is that after normalize(),
    the three weights are constrained to a simplex — they can never all be at
    their minimum simultaneously. This means most genomes cluster in a narrow
    distance band, leaving most theoretical domains empty.

    Solution (following the spirit of Kabir 2017): sample the actual genome
    distribution, compute distances from G_INIT, then divide that empirical
    range into m equal-width bands. This guarantees all archives get populated.
    """
    distances = []
    for _ in range(n_samples):
        g = random_genome()
        distances.append(euclidean_from_init(g))

    d_min = float(np.min(distances))
    d_max = float(np.max(distances))
    domain_range = (d_max - d_min) / m

    # Return m+1 boundary points: [d_min, d_min+r, d_min+2r, ..., d_max]
    boundaries = [d_min + i * domain_range for i in range(m + 1)]
    boundaries[-1] = d_max + 1e-6  # ensure last boundary is inclusive

    print(f"[MSGA] Empirical distance range: [{d_min:.4f}, {d_max:.4f}]")
    print(f"[MSGA] Domain range per archive (m={m}): {domain_range:.4f}")
    print(f"[MSGA] Domain boundaries: {[f'{b:.4f}' for b in boundaries]}")

    return boundaries


def assign_domain(dist: float, boundaries: List[float]) -> int:
    """Assign a genome to a domain index based on its distance."""
    for i in range(len(boundaries) - 1):
        if boundaries[i] <= dist < boundaries[i + 1]:
            return i
    return len(boundaries) - 2  # fallback to last domain


def build_archives(m: int,
                   archive_size: int,
                   eval_data: pd.DataFrame,
                   seed: int = 7) -> List[List[Tuple[Genome, float]]]:
    """
    Divide the genome solution space into m equal domains using empirical
    distance boundaries. Randomly generate candidates, assign each to its
    domain archive, and evaluate fitness.

    Uses empirical boundaries (not theoretical min/max) to ensure all
    archives are naturally populated — necessary because genome normalization
    constrains the reachable solution space.

    Returns:
        archives: list of m lists, each containing
                  (Genome, fitness) tuples sorted best-first.
    """
    random.seed(seed)
    np.random.seed(seed)

    # ── Compute empirical domain boundaries ──
    print(f"[MSGA] Computing empirical domain boundaries from 500 samples...")
    boundaries = compute_empirical_boundaries(m=m, n_samples=500)

    # Each archive stores (Genome, fitness) pairs
    archives: List[List[Tuple[Genome, float]]] = [[] for _ in range(m)]

    max_attempts = archive_size * m * 30
    attempts = 0

    while any(len(a) < archive_size for a in archives) and attempts < max_attempts:
        attempts += 1
        g = random_genome()
        dist = euclidean_from_init(g)
        domain_idx = assign_domain(dist, boundaries)

        if len(archives[domain_idx]) < archive_size:
            f = fitness(g, eval_data)
            archives[domain_idx].append((g, f))

    # Warn if any archive is still underfilled (shouldn't happen now)
    for i, arch in enumerate(archives):
        if len(arch) < archive_size:
            print(f"[MSGA] Warning: archive {i} underfilled "
                  f"({len(arch)}/{archive_size}). Filling with random genomes.")
            while len(arch) < archive_size:
                g = random_genome()
                f = fitness(g, eval_data)
                arch.append((g, f))

    # Sort each archive best-first by fitness
    for i in range(m):
        archives[i].sort(key=lambda x: x[1], reverse=True)

    # Print archive summary
    for i, arch in enumerate(archives):
        best_f = arch[0][1] if arch else float('nan')
        print(f"[MSGA] Archive {i}: {len(arch)} candidates | "
              f"best fitness={best_f:.4f}")

    return archives


# ─────────────────────────────────────────────
# Step 3: Select one seed per archive
# ─────────────────────────────────────────────

def select_seeds(archives: List[List[Tuple[Genome, float]]]) -> List[Genome]:
    """
    Select the top-ranked (highest fitness) genome from each archive
    as the seed for that domain. Returns m seed genomes.
    """
    seeds = []
    for i, archive in enumerate(archives):
        seed_genome, seed_fitness = archive[0]
        print(f"[MSGA] Seed {i}: fitness={seed_fitness:.4f} | {seed_genome}")
        seeds.append(seed_genome)
    return seeds


# ─────────────────────────────────────────────
# Step 4: Generate initial population from seeds
# ─────────────────────────────────────────────

def generate_population_from_seeds(seeds: List[Genome],
                                   pop_size: int,
                                   pm_init: float = 1.0) -> List[Genome]:
    """
    Generate pop_size individuals by mutating each seed.
    Each seed produces pop_size // m offspring (mutation probability = 1.0
    during initialization, following Kabir 2017).

    Any remainder slots are filled by mutating seeds round-robin.
    """
    m = len(seeds)
    per_seed = pop_size // m
    population = []

    for seed_genome in seeds:
        for _ in range(per_seed):
            # High mutation probability during init to diversify around seed
            child = mutate(seed_genome, pm=pm_init)
            population.append(child)

    # Fill remainder (if pop_size not divisible by m)
    remainder = pop_size - len(population)
    for i in range(remainder):
        child = mutate(seeds[i % m], pm=pm_init)
        population.append(child)

    print(f"[MSGA] Generated initial population: {len(population)} individuals "
          f"from {m} seeds ({per_seed} per seed + {remainder} remainder)")

    return population


# ─────────────────────────────────────────────
# Main: run_ga_msga
# Drop-in replacement for runner.run_ga
# ─────────────────────────────────────────────

def run_ga_msga(train_data: pd.DataFrame,
                pop_size: int = 100,
                generations: int = 20,
                eval_n: int = 600,
                seed: int = 7,
                m: int = 4,
                archive_size: int = 25) -> Tuple[Genome, Dict[str, List[float]]]:
    """
    Run the GA with MSGA-style domain-based seeded initialization.

    Parameters
    ----------
    train_data   : full training DataFrame
    pop_size     : number of genomes per generation
    generations  : number of GA generations
    eval_n       : number of prompts sampled per fitness evaluation
    seed         : random seed for reproducibility
    m            : number of domains / archives (default 4, matches Kabir 2017)
    archive_size : candidates generated per domain for seed selection
                   (default pop_size // m = 25 when pop_size=100)

    Returns
    -------
    best_genome  : the highest-fitness genome found
    log          : dict with 'best', 'avg', 'var' lists across generations
    """
    random.seed(seed)
    np.random.seed(seed)

    # Evaluation subset — stable across generations
    eval_data = train_data.sample(
        n=min(eval_n, len(train_data)),
        random_state=seed
    ).reset_index(drop=True)

    print(f"\n{'='*60}")
    print(f"[MSGA] Starting MSGA-seeded GA")
    print(f"[MSGA] pop_size={pop_size} | generations={generations} | "
          f"eval_n={eval_n} | m={m} | archive_size={archive_size}")
    print(f"{'='*60}\n")

    # ── Phase 1: Build archives ──
    print("[MSGA] Phase 1: Building domain archives...")
    if archive_size is None:
        archive_size = max(pop_size // m, 10)
    archives = build_archives(m=m,
                               archive_size=archive_size,
                               eval_data=eval_data,
                               seed=seed)

    # ── Phase 2: Select seeds ──
    print("\n[MSGA] Phase 2: Selecting seeds from archives...")
    seeds = select_seeds(archives)

    # ── Phase 3: Generate initial population ──
    print("\n[MSGA] Phase 3: Generating initial population from seeds...")
    pop = generate_population_from_seeds(seeds, pop_size, pm_init=0.80)

    # ── Phase 4: Evaluate initial population ──
    print("\n[MSGA] Phase 4: Evaluating initial population...")
    fits = [fitness(g, eval_data) for g in pop]

    log = {"best": [], "avg": [], "var": []}

    # ── Phase 5: Evolutionary loop ──
    print(f"\n[MSGA] Phase 5: Running {generations} generations...\n")

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

        # Elitism: keep top 2
        elite_ids = np.argsort(fits)[-2:]
        new_pop = [pop[i] for i in elite_ids]

        # Fill rest via tournament selection + crossover + mutation
        while len(new_pop) < pop_size:
            p1 = tournament_select(pop, fits, k=3)
            p2 = tournament_select(pop, fits, k=3)
            child = mutate(crossover(p1, p2), pm=0.30)
            new_pop.append(child)

        pop = new_pop
        fits = [fitness(g, eval_data) for g in pop]

    best_i = int(np.argmax(fits))
    best_genome = pop[best_i]

    print(f"\n[MSGA] Done. Best fitness: {fits[best_i]:.4f}")
    print(f"[MSGA] Best genome: {best_genome}")

    return best_genome, log