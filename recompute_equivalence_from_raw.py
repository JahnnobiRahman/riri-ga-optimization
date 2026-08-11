#!/usr/bin/env python3
"""
recompute_equivalence_from_raw.py
---------------------------------
Recompute the dataset-size and population-size equivalence tests from the
archived per-seed fitness values, using the corrected Schuirmann TOST in
run_corrected_experiments.tost_equivalence (Welch, SciPy only).

The previously published equivalence artifacts were produced by a version of
tost_equivalence whose two one-sided tails were swapped. That version returned
max(p_lower, p_upper) >= 0.5 for every possible input, so "not equivalent" was
a foregone conclusion rather than a result. This script regenerates the derived
artifacts without re-running the GA.

Reads (never modified):
    experiments/baseline_comparison/dataset_size_corrected_raw.csv
    experiments/baseline_comparison/population_size_corrected_raw.csv

Writes:
    experiments/baseline_comparison/dataset_size_equivalence.csv
    experiments/baseline_comparison/population_size_equivalence.csv
    experiments/baseline_comparison/corrected_experiments_summary.json
    experiments/baseline_comparison/equivalence_tost_table.csv   (manuscript table)

The superseded artifacts are copied to *_prebugfix.* before being overwritten.

Usage:
    python recompute_equivalence_from_raw.py
"""

import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_corrected_experiments import tost_equivalence

OUT_DIR = "experiments/baseline_comparison"
EPSILON = 0.01
ALPHA = 0.05

EXPERIMENTS = [
    {
        "name": "dataset_size",
        "raw": "dataset_size_corrected_raw.csv",
        "summary_csv": "dataset_size_corrected.csv",
        "equiv_csv": "dataset_size_equivalence.csv",
        "level_col": "dataset_size",
        "ref_col": "vs_full",
        "reference": 2297,
        "label": "N",
    },
    {
        "name": "population_size",
        "raw": "population_size_corrected_raw.csv",
        "summary_csv": "population_size_corrected.csv",
        "equiv_csv": "population_size_equivalence.csv",
        "level_col": "population_size",
        "ref_col": "vs_baseline",
        "reference": 100,
        "label": "P",
    },
]


def archive(path):
    if os.path.exists(path):
        stem, ext = os.path.splitext(path)
        shutil.copy2(path, f"{stem}_prebugfix{ext}")


def run_experiment(cfg):
    raw = pd.read_csv(os.path.join(OUT_DIR, cfg["raw"]))
    col, ref = cfg["level_col"], cfg["reference"]

    if ref not in set(raw[col]):
        raise SystemExit(f"reference {col}={ref} absent from {cfg['raw']}")

    ref_fitness = raw.loc[raw[col] == ref, "fitness"].to_numpy()

    summary_rows = []
    for level in sorted(raw[col].unique()):
        fit = raw.loc[raw[col] == level, "fitness"].to_numpy()
        runtime = raw.loc[raw[col] == level, "runtime_sec"].to_numpy()
        summary_rows.append({
            col: int(level),
            "mean_fitness": float(np.mean(fit)),
            "std_fitness": float(np.std(fit, ddof=1)),
            "mean_runtime_sec": float(np.mean(runtime)),
            "n_seeds": int(len(fit)),
        })

    equiv_rows = []
    for level in sorted(raw[col].unique()):
        if level == ref:
            continue
        fit = raw.loc[raw[col] == level, "fitness"].to_numpy()
        res = tost_equivalence(fit, ref_fitness, epsilon=EPSILON, alpha=ALPHA)
        equiv_rows.append({col: int(level), cfg["ref_col"]: ref, **res})

    return raw, pd.DataFrame(summary_rows), pd.DataFrame(equiv_rows)


def main():
    print("=" * 96)
    print("Recomputing TOST equivalence from archived per-seed fitness values")
    print(f"Schuirmann TOST, Welch df, epsilon={EPSILON}, alpha={ALPHA} "
          f"({int((1 - 2 * ALPHA) * 100)}% interval)")
    print("=" * 96)

    summary = {}
    table_rows = []

    existing = os.path.join(OUT_DIR, "corrected_experiments_summary.json")
    if os.path.exists(existing):
        with open(existing) as f:
            summary["total_runtime_sec"] = json.load(f).get("total_runtime_sec")

    for cfg in EXPERIMENTS:
        raw, df_summary, df_equiv = run_experiment(cfg)
        col, ref, label = cfg["level_col"], cfg["reference"], cfg["label"]

        print(f"\n{cfg['name']}  (reference {label}={ref}, "
              f"{df_summary['n_seeds'].iloc[0]} seeds per condition)")
        print(f"{'level':>7} {'mean diff':>11} {'90% CI':>22} "
              f"{'p_lower':>10} {'p_upper':>10} {'TOST p':>10}  decision")
        for _, r in df_equiv.iterrows():
            ci = f"[{r['ci_lower']:+.5f}, {r['ci_upper']:+.5f}]"
            decision = "equivalent" if r["is_equivalent"] else "NOT equivalent"
            print(f"{int(r[col]):>7} {r['mean_diff']:>+11.5f} {ci:>22} "
                  f"{r['p_lower']:>10.5f} {r['p_upper']:>10.5f} "
                  f"{r['tost_p_value']:>10.5f}  {decision}")
            table_rows.append({
                "experiment": cfg["name"],
                "comparison": f"{label}={int(r[col])} vs {label}={ref}",
                "mean_diff": r["mean_diff"],
                "ci90_lower": r["ci_lower"],
                "ci90_upper": r["ci_upper"],
                "p_lower": r["p_lower"],
                "p_upper": r["p_upper"],
                "tost_p_value": r["tost_p_value"],
                "is_equivalent": bool(r["is_equivalent"]),
                "cohens_d": r["cohens_d"],
                "welch_df": r["df"],
                "epsilon": EPSILON,
            })

        n_eq = int(df_equiv["is_equivalent"].sum())
        print(f"  -> equivalence established in {n_eq}/{len(df_equiv)} comparisons")

        equiv_path = os.path.join(OUT_DIR, cfg["equiv_csv"])
        archive(equiv_path)
        df_equiv.to_csv(equiv_path, index=False)

        summary[f"{cfg['name']}_summary"] = df_summary.to_dict(orient="records")
        summary[f"{cfg['name']}_equivalence"] = df_equiv.to_dict(orient="records")

    summary["tost_method"] = (
        "Schuirmann TOST, independent samples, Welch (unequal-variance) t with "
        "Welch-Satterthwaite df; SciPy only. Interval reported is the "
        f"{int((1 - 2 * ALPHA) * 100)}% interval matching the TOST decision at "
        f"alpha={ALPHA}."
    )
    summary["tost_epsilon"] = EPSILON
    summary["tost_alpha"] = ALPHA
    summary["provenance"] = (
        "Equivalence statistics recomputed by recompute_equivalence_from_raw.py "
        "from dataset_size_corrected_raw.csv and population_size_corrected_raw.csv. "
        "Per-seed fitness values are unchanged from the original GA runs; only the "
        "equivalence statistics were recomputed after fixing swapped one-sided "
        "tails in tost_equivalence. Superseded artifacts kept as *_prebugfix.*"
    )

    summary_path = os.path.join(OUT_DIR, "corrected_experiments_summary.json")
    archive(summary_path)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    table_path = os.path.join(OUT_DIR, "equivalence_tost_table.csv")
    pd.DataFrame(table_rows).to_csv(table_path, index=False)

    print(f"\nWrote {summary_path}")
    print(f"Wrote {table_path}")
    for cfg in EXPERIMENTS:
        print(f"Wrote {os.path.join(OUT_DIR, cfg['equiv_csv'])}")
    print("Raw per-seed CSVs were read only and left unchanged.")


if __name__ == "__main__":
    main()
