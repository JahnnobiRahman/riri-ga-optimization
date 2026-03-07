import re
import random
import pandas as pd
from dataclasses import dataclass

# Template IDs used by random_genome (must match keys in generation.response_generator.BASE_TEMPLATES)
BASE_TEMPLATES = {0: "", 1: "", 2: ""}

# ======================
# 5) Genome (configuration)
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

    def normalize(self):
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

def random_genome() -> Genome:
    g = Genome(
        p_id=random.choice(list(BASE_TEMPLATES.keys())),
        w_s=random.random(),
        w_e=random.random(),
        w_c=random.random(),
        memory_window=random.choice([256, 512, 768, 1024]),
        theta_mid=random.uniform(0.40, 0.70),
        theta_high=random.uniform(0.70, 0.95)
    )
    g.normalize()
    return g