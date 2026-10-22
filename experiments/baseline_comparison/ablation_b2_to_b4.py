"""
One-factor-at-a-time ablation between B2 (fixed g_bal) and B4 (reported GA genome).

Question answered: of the genome differences between B2 and B4 (weights, response-part
budget m, gamma), which ones account for the fitness gap?

Design
------
Forward  (B2 + one B4 change):  start from B2, move ONE factor to B4's value.
Reverse  (B4 - one B4 change):  start from B4, move ONE factor back to B2's value.
Factors:
  wc      structure weight only. w_e:w_s keep the BASE genome's ratio and split the
          remainder, so raw weights sum to 1 and normalize() is a no-op (same
          construction as grid_search_wc_corrected.py). This avoids the shared-
          denominator confound.
  weights all three (w_e, w_s, w_c) taken together from the other genome
  m       response-part budget (memory_window)
  gamma   distress-gating gene
  d       template index (p_id)
theta_mid / theta_high are inactive genes and are left at the base genome's values.

A factor whose value is identical in B2 and B4 is reported as "identical" and skipped.

Each condition is evaluated R times on the same fixed 400-prompt subsample, with the
RNG seeded per repeat (same seeds across conditions), so results are reproducible and
the noise (SD ~0.003) is measured, not assumed.

Usage (from the repo root, same environment as rescore_five_seed_significance.py):
    python ablation_b2_to_b4.py            # real run
    python ablation_b2_to_b4.py --dry-run  # mock genome/evaluator, tests the logic only
"""

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, replace
from statistics import mean, stdev

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "src"))

# Same val split / scorer path as rescore_five_seed_significance.py
N_EVAL = 400          # fixed 400-prompt subsample (seed 7), as in Table 6
REPEATS = 10          # repeated evaluations per condition
OUT_PATH = os.path.join(ROOT, "experiments/baseline_comparison/ablation_b2_to_b4.json")
VAL_SPLIT_SEED = 7


def load_val_df():
    df = pd.read_csv(os.path.join(ROOT, "data/phq4_cleaned.csv"))
    for col in ["common_themes", "thought_progression", "risk_assessment"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    if "total_score" not in df.columns:
        df["total_score"] = 0
    df["total_score"] = df["total_score"].fillna(0)
    from evaluation.risk_labeling import label_risk
    df["risk_label"] = df.apply(label_risk, axis=1)
    df["user_prompt"] = (
        df["common_themes"].astype(str).str.strip()
        + " | "
        + df["thought_progression"].astype(str).str.strip()
    ).str.strip(" |")
    df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)
    df = df.sample(frac=1.0, random_state=VAL_SPLIT_SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    return df.iloc[split:].reset_index(drop=True)


def load_genome_json(path, Genome):
    with open(path) as f:
        d = json.load(f)
    keys = {
        "p_id", "w_s", "w_e", "w_c", "memory_window",
        "theta_mid", "theta_high", "gamma",
    }
    return Genome(**{k: d[k] for k in keys})


def load_real():
    """Return (Genome class, evaluate_breakdown, val_df, g_bal genome)."""
    from ga.genome import Genome
    from evaluation.scoring import evaluate_breakdown
    g_bal = load_genome_json(
        os.path.join(ROOT, "experiments/baseline_comparison/best_genome_B2.json"),
        Genome,
    )
    return Genome, evaluate_breakdown, load_val_df(), g_bal


# B4 = archived reported genome (best_genome_B4.json), not the rounded Table 4 cells
B4 = dict(
    w_e=0.13095859853619485,
    w_s=0.10121741632155216,
    w_c=0.767823985142253,
    theta_mid=0.5877710669673699,
    theta_high=0.7,
    gamma=0.0584849049466897,
    p_id=0,
    memory_window=512,
)


# ----------------------------------------------------------------------------------
# 2) Genome construction helpers
# ----------------------------------------------------------------------------------
def genome_fields(g):
    return dict(w_e=g.w_e, w_s=g.w_s, w_c=g.w_c, theta_mid=g.theta_mid,
                theta_high=g.theta_high, gamma=g.gamma, p_id=g.p_id,
                memory_window=g.memory_window)


def with_wc(base, w_c):
    """Set w_c exactly; split the rest in the BASE genome's w_e:w_s ratio (sum = 1)."""
    es = base["w_e"] + base["w_s"]
    rem = 1.0 - w_c
    out = dict(base)
    out["w_c"] = w_c
    out["w_e"] = rem * base["w_e"] / es
    out["w_s"] = rem * base["w_s"] / es
    return out


def swap(base, other, factor):
    """Return `base` with ONE factor moved to `other`'s value."""
    out = dict(base)
    if factor == "wc":
        return with_wc(base, other["w_c"])
    if factor == "weights":
        for k in ("w_e", "w_s", "w_c"):
            out[k] = other[k]
    elif factor == "m":
        out["memory_window"] = other["memory_window"]
    elif factor == "gamma":
        out["gamma"] = other["gamma"]
    elif factor == "d":
        out["p_id"] = other["p_id"]
    else:
        raise ValueError(factor)
    return out


def factor_differs(b2, b4, factor):
    if factor == "wc":
        return abs(b2["w_c"] - b4["w_c"]) > 1e-9
    if factor == "weights":
        return any(abs(b2[k] - b4[k]) > 1e-9 for k in ("w_e", "w_s", "w_c"))
    key = {"m": "memory_window", "gamma": "gamma", "d": "p_id"}[factor]
    return abs(b2[key] - b4[key]) > 1e-9


FACTORS = ["wc", "weights", "m", "gamma", "d"]


def build_conditions(b2, b4):
    conds = [("B2 (base)", b2), ("B4 (base)", b4)]
    skipped = []
    for f in FACTORS:
        if not factor_differs(b2, b4, f):
            skipped.append(f)
            continue
        conds.append((f"B2 + B4's {f}", swap(b2, b4, f)))
    for f in FACTORS:
        if f in skipped:
            continue
        conds.append((f"B4 with B2's {f}", swap(b4, b2, f)))
    # combined: everything except gamma moved (tests "is gamma needed?")
    if "gamma" not in skipped:
        x = swap(b2, b4, "weights")
        if "m" not in skipped:
            x = swap(x, b4, "m")
        if "d" not in skipped:
            x = swap(x, b4, "d")
        conds.append(("B2 + B4's weights, m, d (no gamma)", x))
    return conds, skipped


# ----------------------------------------------------------------------------------
# 3) Evaluation
# ----------------------------------------------------------------------------------
def pick(d, *names):
    for n in names:
        if n in d:
            return float(d[n])
    raise KeyError(f"none of {names} in {list(d)}")


def run_condition(Genome, evaluate_breakdown, val_df, fields):
    rows = []
    for rep in range(REPEATS):
        seed = 1000 + rep                        # same seeds for every condition
        random.seed(seed)
        np.random.seed(seed)
        g = Genome(**fields)
        g.normalize()                            # no-op for with_wc genomes; needed for 'weights'
        r = evaluate_breakdown(g, val_df, n=N_EVAL)
        rows.append(dict(
            fitness=pick(r, "fitness", "mean_fitness", "F"),
            empathy=pick(r, "empathy", "E", "mean_empathy"),
            safety=pick(r, "safety", "S", "mean_safety"),
            structure=pick(r, "structure", "C", "mean_structure"),
        ))
    return rows


def summarize(rows):
    out = {}
    for k in ("fitness", "empathy", "safety", "structure"):
        v = [r[k] for r in rows]
        out[k] = dict(mean=mean(v), sd=stdev(v) if len(v) > 1 else 0.0,
                      min=min(v), max=max(v))
    return out


# ----------------------------------------------------------------------------------
# 4) Dry-run mocks (logic test only, NOT results)
# ----------------------------------------------------------------------------------
@dataclass
class MockGenome:
    w_e: float; w_s: float; w_c: float; theta_mid: float; theta_high: float
    gamma: float; p_id: int; memory_window: int
    def normalize(self):
        t = self.w_e + self.w_s + self.w_c
        self.w_e, self.w_s, self.w_c = self.w_e / t, self.w_s / t, self.w_c / t


def mock_eval(g, val_df, n):
    s = 1.0 if g.w_c >= 0.55 else 0.6 if g.w_c >= 0.25 else 0.0
    f = 0.2 + 0.4 * s - (0.6 if g.memory_window <= 256 else 0) + random.gauss(0, 0.003)
    return dict(fitness=f, empathy=0.4, safety=0.9, structure=s)


# ----------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        Genome, ev, val_df = MockGenome, mock_eval, None
        b2 = dict(w_e=0.33, w_s=0.33, w_c=0.34, theta_mid=0.7, theta_high=0.95,
                  gamma=0.0, p_id=0, memory_window=512)
        print("DRY RUN: mock genome/evaluator, numbers below are NOT results.\n")
    else:
        Genome, ev, val_df, g_bal = load_real()
        b2 = genome_fields(g_bal)

    conds, skipped = build_conditions(b2, B4)
    print("B2 genome:", b2)
    print("B4 genome:", B4)
    if skipped:
        print("Identical in B2 and B4 (skipped):", skipped)

    results = []
    for name, fields in conds:
        rows = run_condition(Genome, ev, val_df, fields)
        s = summarize(rows)
        results.append(dict(condition=name, genome=fields, summary=s, repeats=rows))
        print(f"{name:40s} fitness {s['fitness']['mean']:.4f} +/- {s['fitness']['sd']:.4f}"
              f"  E {s['empathy']['mean']:.3f}  S {s['safety']['mean']:.3f}"
              f"  C {s['structure']['mean']:.3f}")

    base = next(r for r in results if r["condition"] == "B2 (base)")["summary"]["fitness"]["mean"]
    top = next(r for r in results if r["condition"] == "B4 (base)")["summary"]["fitness"]["mean"]
    gap = top - base
    print(f"\nTotal B2 -> B4 gap: {gap:+.4f}")
    print(f"{'condition':40s} {'delta vs B2':>12s} {'share of gap':>13s}")
    for r in results:
        d = r["summary"]["fitness"]["mean"] - base
        print(f"{r['condition']:40s} {d:+12.4f} {d / gap:13.0%}")
    print("\nDifferences below ~0.008 are within the evaluation noise (SD ~0.003) "
          "and should not be interpreted.")

    if not args.dry_run:
        with open(OUT_PATH, "w") as fh:
            json.dump(dict(b2=b2, b4=B4, skipped=skipped, n_eval=N_EVAL,
                           repeats=REPEATS, results=results), fh, indent=2)
        print("Saved:", OUT_PATH)


if __name__ == "__main__":
    sys.exit(main())