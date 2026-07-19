import re
import random
import pandas as pd
import numpy as np
from dataclasses import asdict
from typing import List

from ga.genome import Genome, BASE_TEMPLATES

# ======================
# GA operators
# ======================
def tournament_select(pop: List[Genome], fits: List[float], k: int = 3) -> Genome:
    """Tournament selection: select k random individuals, return best."""
    ids = random.sample(range(len(pop)), k)
    best = max(ids, key=lambda i: fits[i])
    return pop[best]

def crossover(a: Genome, b: Genome) -> Genome:
    """
    Uniform crossover: each gene inherited from either parent a or b.
    Updated to include gamma gene.
    """
    child = Genome(
        p_id=random.choice([a.p_id, b.p_id]),
        w_s=random.choice([a.w_s, b.w_s]),
        w_e=random.choice([a.w_e, b.w_e]),
        w_c=random.choice([a.w_c, b.w_c]),
        memory_window=random.choice([a.memory_window, b.memory_window]),
        theta_mid=random.choice([a.theta_mid, b.theta_mid]),
        theta_high=random.choice([a.theta_high, b.theta_high]),
        gamma=random.choice([a.gamma, b.gamma]),  # NEW
        history_turns=random.choice([a.history_turns, b.history_turns]),  # <-- NEW

    )
    child.normalize()
    return child

def mutate(g: Genome, pm: float = 0.30) -> Genome:
    """
    Gaussian mutation: perturb each gene with probability pm.
    Updated to include gamma mutation.
    
    Parameters
    ----------
    g : Genome
        Genome to mutate
    pm : float
        Probability of mutating each gene
    
    Returns
    -------
    Genome
        Mutated copy of g
    """
    m = Genome(**asdict(g))

    if random.random() < pm:
        m.p_id = random.choice(list(BASE_TEMPLATES.keys()))

    if random.random() < pm:
        m.w_s = float(np.clip(m.w_s + random.uniform(-0.25, 0.25), 0, 1))
    if random.random() < pm:
        m.w_e = float(np.clip(m.w_e + random.uniform(-0.25, 0.25), 0, 1))
    if random.random() < pm:
        m.w_c = float(np.clip(m.w_c + random.uniform(-0.25, 0.25), 0, 1))

    if random.random() < pm:
        m.memory_window = random.choice([512, 768, 1024])  # 256 excluded,

    if random.random() < pm:
        m.theta_mid = float(np.clip(m.theta_mid + random.uniform(-0.06, 0.06), 0.40, 0.70))
    if random.random() < pm:
        m.theta_high = float(np.clip(m.theta_high + random.uniform(-0.06, 0.06), 0.70, 0.95))

    # NEW: gamma mutation
    if random.random() < pm:
        m.gamma = float(np.clip(m.gamma + random.uniform(-0.05, 0.05), 0.0, 0.2))


    # NEW: history_turns mutation
    if random.random() < pm:                                              # <-- NEW
        m.history_turns = random.choice([4, 8, 12, 16, 20,24])   

    m.normalize()
    return m