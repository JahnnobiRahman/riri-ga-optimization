"""
Re-run the headline experiments with all self-reported 13-17 records removed.

Same pipeline as the paper (src/), same seed-7 80/20 partition; the minor
records are dropped from both sides AFTER the split, so the partition is the
paper's minus the minors. Writes only to OUT_DIR (outside the repo).

Run from the project root:  .venv/bin/python <this file> <OUT_DIR>
"""
import json
import multiprocessing as mp
import os
import random
import sys
import time
from dataclasses import asdict

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "src")
from evaluation.risk_labeling import label_risk          # noqa: E402
from evaluation.scoring import evaluate_breakdown        # noqa: E402
from ga.genome import Genome, random_genome              # noqa: E402
from ga.runner import run_ga                             # noqa: E402

OUT_DIR = sys.argv[1]
os.makedirs(OUT_DIR, exist_ok=True)
SEED, N_EVAL = 7, 400
GA_SEEDS = [7, 13, 26, 39, 52, 65]       # 7 = main run (B4); others = Table 6 seeds
SIG_SEEDS = [13, 26, 39, 52, 65]
MINOR = "13-17"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_split():
    df = pd.read_csv("data/phq4_cleaned.csv")
    for c in ["common_themes", "thought_progression", "risk_assessment"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("")
    df["total_score"] = df["total_score"].fillna(0)
    df["risk_label"] = df.apply(label_risk, axis=1)
    df["user_prompt"] = (df["common_themes"].astype(str).str.strip() + " | "
                         + df["thought_progression"].astype(str).str.strip()).str.strip(" |")
    df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    tr, va = df.iloc[:split], df.iloc[split:]
    return (tr.reset_index(drop=True), va.reset_index(drop=True),
            tr[tr.age_group != MINOR].reset_index(drop=True),
            va[va.age_group != MINOR].reset_index(drop=True))


def load_genome(path):
    d = json.load(open(path))
    keys = ["p_id", "w_s", "w_e", "w_c", "memory_window", "theta_mid", "theta_high", "gamma"]
    return Genome(**{k: d[k] for k in keys})


def seeded_eval(g, data, seed):
    random.seed(seed)
    np.random.seed(seed)
    return evaluate_breakdown(g, data, n=N_EVAL)


TRAIN_NM = None


def ga_job(seed):
    t0 = time.time()
    with open(os.path.join(OUT_DIR, f"ga_seed_{seed}.log"), "w") as fh:
        so = sys.stdout
        sys.stdout = fh
        try:
            g, lg = run_ga(TRAIN_NM, pop_size=100, generations=20, eval_n=600, seed=seed)
        finally:
            sys.stdout = so
    return seed, asdict(g), lg, time.time() - t0


def boot_ci(diff, n=10000, seed=7):
    rng = np.random.default_rng(seed)
    m = [rng.choice(diff, size=len(diff), replace=True).mean() for _ in range(n)]
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def main():
    global TRAIN_NM
    tr, va, tr_nm, va_nm = load_split()
    TRAIN_NM = tr_nm
    counts = {
        "train_full": len(tr), "val_full": len(va),
        "train_no_minors": len(tr_nm), "val_no_minors": len(va_nm),
        "removed_train": len(tr) - len(tr_nm), "removed_val": len(va) - len(va_nm),
        "risk_val_no_minors": va_nm.risk_label.value_counts().to_dict(),
        "risk_train_no_minors": tr_nm.risk_label.value_counts().to_dict(),
    }
    log(f"counts: {counts}")
    json.dump(counts, open(os.path.join(OUT_DIR, "counts.json"), "w"), indent=2)

    # ---- GA runs in parallel (fork after imports) ----
    log(f"starting {len(GA_SEEDS)} GA runs in parallel")
    ctx = mp.get_context("fork")
    ga = {}
    with ctx.Pool(len(GA_SEEDS)) as pool:
        for seed, gd, lg, dt in pool.imap_unordered(ga_job, GA_SEEDS):
            ga[seed] = {"genome": gd, "log": lg, "seconds": dt}
            json.dump(gd, open(os.path.join(OUT_DIR, f"best_genome_seed_{seed}.json"), "w"), indent=2)
            log(f"GA seed {seed} done in {dt:.0f}s: {gd}")

    # ---- fixed genomes ----
    B = "experiments/baseline_comparison"
    b1 = load_genome(f"{B}/best_genome_B1.json")
    b1f = load_genome(f"{B}/best_genome_B1.json"); b1f.memory_window = 512
    b2 = load_genome(f"{B}/best_genome_B2.json")
    b4_paper = load_genome(f"{B}/best_genome_B4.json")
    for g in (b1, b1f, b2, b4_paper):
        g.normalize()
    b4_new = Genome(**ga[7]["genome"])

    res = {"counts": counts}

    # Table 5 analogue (single evaluations, generator seeded at 7 for reproducibility)
    t5 = {
        "B1": seeded_eval(b1, va_nm, SEED),
        "B1-fixed": seeded_eval(b1f, va_nm, SEED),
        "B2": seeded_eval(b2, va_nm, SEED),
        "B4_new (GA re-run, seed 7)": seeded_eval(b4_new, va_nm, SEED),
        "B4_paper (archived genome)": seeded_eval(b4_paper, va_nm, SEED),
    }
    rnd = []
    for r in range(5):
        random.seed(SEED + r); np.random.seed(SEED + r)
        rg = random_genome()
        rnd.append(seeded_eval(rg, va_nm, SEED + r))
    t5["B3 mean"] = {k: float(np.mean([m[k] for m in rnd])) for k in ("empathy", "safety", "structure", "fitness")}
    t5["B3 std"] = {k: float(np.std([m[k] for m in rnd])) for k in ("empathy", "safety", "structure", "fitness")}
    res["table5_no_minors"] = t5
    log("table 5 analogue done")

    # Table 6 analogue (five paired seeded re-scores)
    rows, gar, b1r, b2r = [], [], [], []
    for s in SIG_SEEDS:
        g = Genome(**ga[s]["genome"])
        a, b, c = seeded_eval(g, va_nm, s), seeded_eval(b1, va_nm, s), seeded_eval(b2, va_nm, s)
        gar.append(a["fitness"]); b1r.append(b["fitness"]); b2r.append(c["fitness"])
        rows.append({"seed": s, "ga": a["fitness"], "b1": b["fitness"], "b2": c["fitness"],
                     "ga_structure": a["structure"], "genome": ga[s]["genome"]})
    gar, b1r, b2r = map(np.array, (gar, b1r, b2r))
    d1, d2 = gar - b1r, gar - b2r
    res["table6_no_minors"] = {
        "rows": rows,
        "mean_sd": {"GA": [gar.mean(), gar.std(ddof=1)], "B1": [b1r.mean(), b1r.std(ddof=1)],
                    "B2": [b2r.mean(), b2r.std(ddof=1)]},
        "wilcoxon_GA_gt_B1": list(map(float, stats.wilcoxon(gar, b1r, alternative="greater"))),
        "wilcoxon_GA_gt_B2": list(map(float, stats.wilcoxon(gar, b2r, alternative="greater"))),
        "diff_B1_range": [d1.min(), d1.max()], "diff_B1_median": float(np.median(d1)), "ci_B1": boot_ci(d1),
        "diff_B2_range": [d2.min(), d2.max()], "diff_B2_median": float(np.median(d2)), "ci_B2": boot_ci(d2),
    }
    # archived (paper) seed genomes on the no-minors validation set, for reference
    arch = []
    for s in SIG_SEEDS:
        g = load_genome(f"{B}/seed_genomes/best_genome_seed_{s}.json")
        arch.append(seeded_eval(g, va_nm, s)["fitness"])
    res["archived_seed_genomes_on_no_minors_val"] = arch
    res["ga_runtimes_s"] = {s: ga[s]["seconds"] for s in ga}
    res["ga_best_train_fitness"] = {s: max(ga[s]["log"]["best"]) for s in ga}

    def conv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    json.dump(res, open(os.path.join(OUT_DIR, "results.json"), "w"), indent=2, default=conv)
    log("ALL DONE")


if __name__ == "__main__":
    main()
