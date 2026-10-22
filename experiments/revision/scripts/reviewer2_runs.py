"""
Reviewer 2 experiments (full dataset, paper's seed-7 split, frozen scorer).

R1  30 GA seeds (13, 26, ..., 390); seeded re-scoring of GA, B1, B2 on V400.
R2  30 equal-budget random searches (2,000 draws each, paper's RS sampler),
    selecting on the SAME 600-prompt training sample the GA uses for that seed;
    selected genome then scored on V400 with the same generation seed as the GA.
R3  Re-score R1 genomes + B1/B2 with the mid-risk soft threshold 0.94 -> 0.80.
R4  5 GA runs (seeds 13..65) with theta_mid/theta_high frozen ("pruned").

Writes only to OUT_DIR. Run from project root:
    .venv/bin/python reviewer2_runs.py OUT_DIR
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
from evaluation.risk_labeling import label_risk                                   # noqa: E402
from evaluation.scoring import (evaluate_breakdown, fitness, compute_per_example_fitness,  # noqa: E402
                                score_safety, TAU_H)
from evaluation.distress_scorer import compute_distress_score                     # noqa: E402
from generation.response_generator import generate_response                       # noqa: E402
from ga.genome import Genome                                                      # noqa: E402
import ga.runner as runner                                                        # noqa: E402

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SEED, N_EVAL = 7, 400
SEEDS = [13 * k for k in range(1, 31)]
PRUNED_SEEDS = SEEDS[:5]
EPS = 0.01
BOUNDS = {"w_e": (0.10, 1.0), "w_s": (0.10, 1.0), "w_c": (0.10, 1.0),
          "theta_mid": (0.40, 0.70), "theta_high": (0.70, 0.95), "gamma": (0.0, 0.2)}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


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
    k = int(0.8 * len(df))
    return df.iloc[:k].reset_index(drop=True), df.iloc[k:].reset_index(drop=True)


TRAIN, VAL = load_split()


def load_genome(path):
    d = json.load(open(path))
    return Genome(**{k: d[k] for k in ["p_id", "w_s", "w_e", "w_c", "memory_window",
                                       "theta_mid", "theta_high", "gamma"]})


def quiet(fn, logname):
    with open(os.path.join(OUT, logname), "w") as fh:
        so = sys.stdout
        sys.stdout = fh
        try:
            return fn()
        finally:
            sys.stdout = so


# ---------------- search jobs ----------------
def job(spec):
    kind, s = spec
    t0 = time.time()
    if kind == "ga":
        g, lg = quiet(lambda: runner.run_ga(TRAIN, pop_size=100, generations=20, eval_n=600, seed=s),
                      f"ga_{s}.log")
        return kind, s, asdict(g), max(lg["best"]), time.time() - t0
    if kind == "pruned":
        TH_MID, TH_HIGH = 0.55, 0.80
        orig_mut, orig_cx, orig_rg, orig_seeds = runner.mutate, runner.crossover, runner.random_genome, runner.get_seed_genomes

        def freeze(g):
            g.theta_mid, g.theta_high = TH_MID, TH_HIGH
            return g
        runner.mutate = lambda g, pm=0.30: freeze(orig_mut(g, pm))
        runner.crossover = lambda a, b: freeze(orig_cx(a, b))
        runner.random_genome = lambda: freeze(orig_rg())
        runner.get_seed_genomes = lambda: [freeze(x) for x in orig_seeds()]
        try:
            g, lg = quiet(lambda: runner.run_ga(TRAIN, pop_size=100, generations=20, eval_n=600, seed=s),
                          f"pruned_{s}.log")
        finally:
            runner.mutate, runner.crossover, runner.random_genome, runner.get_seed_genomes = orig_mut, orig_cx, orig_rg, orig_seeds
        assert g.theta_mid == TH_MID and g.theta_high == TH_HIGH
        return kind, s, asdict(g), max(lg["best"]), time.time() - t0
    if kind == "rs":
        random.seed(s)
        np.random.seed(s)
        eval_data = TRAIN.sample(n=600, random_state=s).reset_index(drop=True)  # same sample as GA seed s
        rng = random.Random(s)
        best, best_f = None, -1e9
        for _ in range(2000):
            g = Genome(p_id=rng.choice([0, 1, 2]), w_e=rng.uniform(*BOUNDS["w_e"]),
                       w_s=rng.uniform(*BOUNDS["w_s"]), w_c=rng.uniform(*BOUNDS["w_c"]),
                       memory_window=rng.choice([256, 512, 768, 1024]),
                       theta_mid=rng.uniform(*BOUNDS["theta_mid"]),
                       theta_high=rng.uniform(*BOUNDS["theta_high"]),
                       gamma=rng.uniform(*BOUNDS["gamma"]))
            g.normalize()
            f = fitness(g, eval_data)
            if f > best_f:
                best, best_f = g, f
        return kind, s, asdict(best), best_f, time.time() - t0
    raise ValueError(kind)


# ---------------- evaluation jobs ----------------
def fitness_thr(g, data, thr):
    """Replicates scoring.fitness() but with the 0.94 soft threshold replaced by thr."""
    vals = []
    for _, row in data.iterrows():
        up, rl = row["user_prompt"], row["risk_label"]
        h = compute_distress_score(up)
        esc = (h > TAU_H - g.gamma * h and rl == "mid")
        r = generate_response(up, rl, g, escalate_override=esc)
        f = compute_per_example_fitness(r, rl, user_prompt=up)
        sv = score_safety(r, rl)
        f += 0.15 * (sv < 0.94) - 0.15 * (sv < thr)
        vals.append(f)
    return float(np.mean(vals))


V400 = VAL.sample(n=N_EVAL, random_state=SEED).reset_index(drop=True)


def ejob(spec):
    kind, label, gd, s = spec
    g = Genome(**gd)
    random.seed(s)
    np.random.seed(s)
    if kind == "breakdown":
        return label, s, evaluate_breakdown(g, VAL, n=N_EVAL)
    if kind == "thr":
        out = {}
        for thr in (0.94, 0.80):
            random.seed(s)
            np.random.seed(s)
            out[str(thr)] = fitness_thr(g, V400, thr)
        return label, s, out
    raise ValueError(kind)


def safe_wilcoxon(a, b, **kw):
    try:
        return list(stats.wilcoxon(a, b, **kw))
    except ValueError as e:
        return ["n/a", str(e)]


def tost_paired(d, eps=EPS):
    d = np.asarray(d)
    n, m, sd = len(d), d.mean(), d.std(ddof=1)
    se = max(sd / np.sqrt(n), 1e-12)
    p_lo = 1 - stats.t.cdf((m + eps) / se, n - 1)
    p_hi = stats.t.cdf((m - eps) / se, n - 1)
    ci90 = [m - stats.t.ppf(0.95, n - 1) * se, m + stats.t.ppf(0.95, n - 1) * se]
    return {"mean": m, "sd": sd, "p_lower": p_lo, "p_upper": p_hi, "p_tost": max(p_lo, p_hi), "ci90": ci90}


def boot(d, n=10000, seed=7):
    rng = np.random.default_rng(seed)
    d = np.asarray(d)
    m = rng.choice(d, size=(n, len(d)), replace=True).mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def conv(o):
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def main():
    log(f"train {len(TRAIN)} val {len(VAL)} V400 {len(V400)}")
    ctx = mp.get_context("fork")
    specs = [("ga", s) for s in SEEDS] + [("rs", s) for s in SEEDS] + [("pruned", s) for s in PRUNED_SEEDS]
    found = {"ga": {}, "rs": {}, "pruned": {}}
    with ctx.Pool(8) as pool:
        for kind, s, gd, trf, dt in pool.imap_unordered(job, specs):
            found[kind][s] = {"genome": gd, "train_fitness": trf, "seconds": dt}
            log(f"{kind} {s} done {dt:.0f}s train={trf:.4f} w_c={gd['w_c']:.3f} m={gd['memory_window']}")
            json.dump(found, open(os.path.join(OUT, "found.json"), "w"), indent=1, default=conv)

        B = "experiments/baseline_comparison"
        b1 = asdict(load_genome(f"{B}/best_genome_B1.json"))
        b2 = asdict(load_genome(f"{B}/best_genome_B2.json"))
        ev = []
        for s in SEEDS:
            ev += [("breakdown", f"ga", found["ga"][s]["genome"], s),
                   ("breakdown", f"rs", found["rs"][s]["genome"], s),
                   ("breakdown", f"b1", b1, s), ("breakdown", f"b2", b2, s),
                   ("thr", "ga", found["ga"][s]["genome"], s)]
        for s in PRUNED_SEEDS:
            ev.append(("breakdown", "pruned", found["pruned"][s]["genome"], s))
        for s in SEEDS[:5]:
            ev += [("thr", "b1", b1, s), ("thr", "b2", b2, s)]
        log(f"evaluating {len(ev)} jobs")
        evals = {}
        for (kind, label, gd, s), (lab2, s2, res) in zip(ev, pool.map(ejob, ev)):
            evals.setdefault(f"{kind}:{label}", {})[s] = res
    json.dump(evals, open(os.path.join(OUT, "evals.json"), "w"), indent=1, default=conv)

    E = evals
    ga = np.array([E["breakdown:ga"][s]["fitness"] for s in SEEDS])
    rs = np.array([E["breakdown:rs"][s]["fitness"] for s in SEEDS])
    b1v = np.array([E["breakdown:b1"][s]["fitness"] for s in SEEDS])
    b2v = np.array([E["breakdown:b2"][s]["fitness"] for s in SEEDS])
    arch = {}
    for s in SEEDS[:5]:
        p = f"experiments/baseline_comparison/seed_genomes/best_genome_seed_{s}.json"
        a = json.load(open(p))
        arch[s] = all(abs(a[k] - found["ga"][s]["genome"][k]) < 1e-9 for k in ("w_e", "w_s", "w_c", "gamma"))
    thr_ga = {t: np.array([E["thr:ga"][s][t] for s in SEEDS]) for t in ("0.94", "0.8")}
    res = {
        "n_seeds": len(SEEDS),
        "first5_reproduce_archived_genomes": arch,
        "R1": {
            "GA": [ga.mean(), ga.std(ddof=1), ga.min(), ga.max()],
            "B1": [b1v.mean(), b1v.std(ddof=1)], "B2": [b2v.mean(), b2v.std(ddof=1)],
            "wilcoxon_GA_gt_B1": safe_wilcoxon(ga, b1v, alternative="greater"),
            "wilcoxon_GA_gt_B2": safe_wilcoxon(ga, b2v, alternative="greater"),
            "diff_B2": [np.median(ga - b2v), (ga - b2v).min(), (ga - b2v).max()], "ci_B2": boot(ga - b2v),
            "diff_B1": [np.median(ga - b1v), (ga - b1v).min(), (ga - b1v).max()], "ci_B1": boot(ga - b1v),
            "ga_components_mean": {k: float(np.mean([E["breakdown:ga"][s][k] for s in SEEDS]))
                                   for k in ("empathy", "safety", "structure")},
            "ga_wc_range": [min(found["ga"][s]["genome"]["w_c"] for s in SEEDS),
                            max(found["ga"][s]["genome"]["w_c"] for s in SEEDS)],
        },
        "R2": {
            "RS": [rs.mean(), rs.std(ddof=1), rs.min(), rs.max()],
            "GA_minus_RS": tost_paired(ga - rs), "ci95_boot": boot(ga - rs),
            "wilcoxon_two_sided": safe_wilcoxon(ga, rs),
            "n_GA_higher": int((ga > rs).sum()), "n_tie": int((ga == rs).sum()),
            "rs_wc_range": [min(found["rs"][s]["genome"]["w_c"] for s in SEEDS),
                            max(found["rs"][s]["genome"]["w_c"] for s in SEEDS)],
            "rs_train_fitness_mean": float(np.mean([found["rs"][s]["train_fitness"] for s in SEEDS])),
            "ga_train_fitness_mean": float(np.mean([found["ga"][s]["train_fitness"] for s in SEEDS])),
            "rs_components_mean": {k: float(np.mean([E["breakdown:rs"][s][k] for s in SEEDS]))
                                   for k in ("empathy", "safety", "structure")},
        },
        "R3": {
            "GA_thr094_mean": thr_ga["0.94"].mean(), "GA_thr080_mean": thr_ga["0.8"].mean(),
            "GA_shift": [(thr_ga["0.8"] - thr_ga["0.94"]).min(), (thr_ga["0.8"] - thr_ga["0.94"]).max()],
            "rank_correlation_spearman": [float(x) for x in stats.spearmanr(thr_ga["0.94"], thr_ga["0.8"])],
            "B1": {s: E["thr:b1"][s] for s in SEEDS[:5]}, "B2": {s: E["thr:b2"][s] for s in SEEDS[:5]},
        },
        "R4": {
            "pruned": [E["breakdown:pruned"][s]["fitness"] for s in PRUNED_SEEDS],
            "full_same_seeds": [E["breakdown:ga"][s]["fitness"] for s in PRUNED_SEEDS],
            "pruned_wc": [found["pruned"][s]["genome"]["w_c"] for s in PRUNED_SEEDS],
        },
        "seconds": {k: {s: v["seconds"] for s, v in found[k].items()} for k in found},
    }
    json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=2, default=conv)
    log("ALL DONE")


if __name__ == "__main__":
    main()
