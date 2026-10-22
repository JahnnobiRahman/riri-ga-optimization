"""Recompute Krippendorff's alpha for the human evaluation study.

Primary analysis (as reported in the paper): for each dimension, treat
each of the 60 blinded response units (30 items × 2 systems) as a
reliability unit rated by 5 annotators. Uses interval metric on 1–5 scores.

Data (gitignored via *.csv):
  experiments/human_eval/human_eval_long_format.csv
  experiments/human_eval/annotation_blinded.csv

Run from repo root: python compute_krippendorff.py
"""
from pathlib import Path
import csv
import numpy as np

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "experiments" / "human_eval" / "human_eval_long_format.csv"


def krippendorff_alpha(reliability_data, level="interval"):
    data = np.asarray(reliability_data, dtype=float)
    values = data[~np.isnan(data)]
    if values.size == 0:
        return np.nan
    uniq = np.unique(values)
    v_index = {v: i for i, v in enumerate(uniq)}
    m = len(uniq)
    O = np.zeros((m, m), dtype=float)
    n_pairable = 0
    for u in range(data.shape[1]):
        observed = data[:, u]
        observed = observed[~np.isnan(observed)]
        n_u = len(observed)
        if n_u < 2:
            continue
        n_pairable += n_u
        for i in range(n_u):
            for j in range(n_u):
                if i == j:
                    continue
                O[v_index[observed[i]], v_index[observed[j]]] += 1.0 / (n_u - 1)
    if n_pairable == 0:
        return np.nan
    n_c = O.sum(axis=1)
    n = n_c.sum()
    E = np.zeros_like(O)
    for c in range(m):
        for k in range(m):
            E[c, k] = (
                n_c[c] * (n_c[c] - 1) / (n - 1)
                if c == k and n > 1
                else (n_c[c] * n_c[k] / (n - 1) if n > 1 else 0)
            )

    def delta(c, k):
        if level == "nominal":
            return 0.0 if c == k else 1.0
        if level == "ordinal":
            if c == k:
                return 0.0
            lo, hi = min(c, k), max(c, k)
            g = n_c[lo : hi + 1].sum()
            return (g - (n_c[c] + n_c[k]) / 2.0) ** 2
        return (uniq[c] - uniq[k]) ** 2

    Do = De = 0.0
    for c in range(m):
        for k in range(m):
            d = delta(c, k)
            Do += O[c, k] * d
            De += E[c, k] * d
    Do /= n
    De /= n
    if De == 0:
        return 1.0 if Do == 0 else np.nan
    return 1.0 - Do / De


def pairwise_within_one(reliability_data):
    data = np.asarray(reliability_data, dtype=float)
    agree = total = 0
    for u in range(data.shape[1]):
        vals = data[:, u]
        vals = vals[~np.isnan(vals)]
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                total += 1
                if abs(vals[i] - vals[j]) <= 1:
                    agree += 1
    return agree / total if total else np.nan


def main():
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    raters = sorted({r["rater"] for r in rows})
    for dim in ["empathy", "safety", "helpfulness"]:
        sub = [r for r in rows if r["dimension"] == dim and r["system"] in ("B1", "B4")]
        units = sorted({(r["item_id"], r["system"]) for r in sub}, key=lambda x: (int(x[0]), x[1]))
        mat = np.full((len(raters), len(units)), np.nan)
        for r in sub:
            mat[raters.index(r["rater"]), units.index((r["item_id"], r["system"]))] = float(r["score"])
        print(
            f"{dim:12s}  α={krippendorff_alpha(mat):.4f}  "
            f"pairwise≤1={pairwise_within_one(mat):.3f}  units={len(units)}"
        )


if __name__ == "__main__":
    main()
