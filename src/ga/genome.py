import re
import random
import pandas as pd
import numpy as np
from dataclasses import dataclass

# Template IDs used by random_genome (must match keys in generation.response_generator.BASE_TEMPLATES)
BASE_TEMPLATES = {0: "", 1: "", 2: ""}

# ======================
# Genome (configuration) - UPDATED WITH GAMMA
# ======================
@dataclass
class Genome:
    p_id: int
    w_s: float
    w_e: float
    w_c: float
    memory_window: int
    theta_mid: float
    theta_high: float
    gamma: float  # NEW: distress-gating parameter [0, 0.2]
    history_turns: int = 6  # <-- NEW: how many prior user turns the


    def normalize(self):
        """
        Enforce minimum floor on weights and renormalize to sum = 1.
        Clamp gamma to valid range.
        """
        # Enforce minimum floor
        MIN_W = 0.10
        self.w_s = max(self.w_s, MIN_W)
        self.w_e = max(self.w_e, MIN_W)
        self.w_c = max(self.w_c, MIN_W)
        # Renormalize to sum = 1
        total = self.w_s + self.w_e + self.w_c
        self.w_s /= total
        self.w_e /= total
        self.w_c /= total
        
        # NEW: Clamp gamma to valid range [0, 0.2]
        self.gamma = float(np.clip(self.gamma, 0.0, 0.2))
        self.history_turns = int(np.clip(self.history_turns, 4, 24))  # <-- NEW


def random_genome() -> Genome:
    """
    Generate a random genome with all genes initialized uniformly.
    Gamma is initialized in [0, 0.2] for distress gating.
    """
    g = Genome(
        p_id=random.choice(list(BASE_TEMPLATES.keys())),
        w_s=random.random(),
        w_e=random.random(),
        w_c=random.random(),
        memory_window=random.choice([512, 768, 1024]),  # 256 excluded -- see
        theta_mid=random.uniform(0.40, 0.70),
        theta_high=random.uniform(0.70, 0.95),
        gamma=random.uniform(0.0, 0.2),  # NEW
        history_turns=random.choice([4, 8, 12, 16, 20,24]),  # <-- NEW

    )
    g.normalize()
    return g
    

