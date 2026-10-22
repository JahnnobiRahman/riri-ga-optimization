#!/usr/bin/env python3
"""
Diagnostic: generator structure flags vs scorer-detected components.

For w_c in {0.10, 0.40, 0.50} over the 575-prompt validation set:
  - count non-empty chosen_grounding / chosen_action / chosen_question
  - count scorer-detected grounding / action / question on final_response
  - when they disagree, record which side and which markers matched
"""

import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, "src")

from ga.genome import Genome
from evaluation.risk_labeling import label_risk
from evaluation.scoring import (
    GROUNDING_MARKERS,
    ACTION_MARKERS,
    score_structure,
)
from generation.response_generator import assemble_prompt_trace

SEED = 7
DATA_PATH = "data/phq4_cleaned.csv"

# Reported genome e:s ratio, remainder split when sweeping w_c
W_E_REP, W_S_REP = 0.131, 0.101
E_SHARE = W_E_REP / (W_E_REP + W_S_REP)
S_SHARE = W_S_REP / (W_E_REP + W_S_REP)


def load_val_df():
    df = pd.read_csv(DATA_PATH)
    for col in ["common_themes", "thought_progression", "risk_assessment"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    if "total_score" not in df.columns:
        df["total_score"] = 0
    df["total_score"] = df["total_score"].fillna(0)
    df["risk_label"] = df.apply(label_risk, axis=1)
    df["user_prompt"] = (
        df["common_themes"].astype(str).str.strip()
        + " | "
        + df["thought_progression"].astype(str).str.strip()
    ).str.strip(" |")
    df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    split = int(0.8 * len(df))
    return df.iloc[split:].reset_index(drop=True)


def make_genome(w_c: float, memory_window: int = 512) -> Genome:
    remaining = 1.0 - w_c
    g = Genome(
        p_id=0,
        w_e=remaining * E_SHARE,
        w_s=remaining * S_SHARE,
        w_c=w_c,
        memory_window=memory_window,
        theta_mid=0.588,
        theta_high=0.700,
        gamma=0.059,
    )
    g.normalize()
    return g


def make_b1_genome() -> Genome:
    g = Genome(
        p_id=0,
        w_e=0.10,
        w_s=0.80,
        w_c=0.10,
        memory_window=256,
        theta_mid=0.70,
        theta_high=0.95,
        gamma=0.0,
    )
    g.normalize()
    return g


def scorer_components(resp: str):
    text = resp.lower()
    g_hits = [m for m in GROUNDING_MARKERS if m.lower() in text]
    a_hits = [m for m in ACTION_MARKERS if m.lower() in text]
    q_reasons = []
    if "?" in resp:
        q_reasons.append("?")
    if "কখন" in resp:
        q_reasons.append("কখন")
    if "কি" in resp:
        q_reasons.append("কি")
    if "what" in text:
        q_reasons.append("what")
    if "when" in text:
        q_reasons.append("when")
    return {
        "grounding": len(g_hits) > 0,
        "action": len(a_hits) > 0,
        "question": len(q_reasons) > 0,
        "grounding_markers": g_hits,
        "action_markers": a_hits,
        "question_reasons": q_reasons,
    }


def gen_flags(trace):
    return {
        "grounding": bool(trace.get("grounding")),
        "action": bool(trace.get("action")),
        "question": bool(trace.get("question")),
    }


def run_condition(name, genome, val_df):
    n = len(val_df)
    gen_counts = []
    scorer_counts = []
    structure_scores = []

    # disagreement buckets
    scorer_extra = Counter()  # component scorer has, generator doesn't
    gen_extra = Counter()     # generator has, scorer doesn't
    marker_when_scorer_extra = Counter()
    examples = defaultdict(list)

    both_agree_exact = 0
    scorer_gt_gen = 0
    gen_gt_scorer = 0

    for _, row in val_df.iterrows():
        trace = assemble_prompt_trace(
            row["user_prompt"],
            row["risk_label"],
            genome,
            escalate_override=None,
        )
        resp = trace["final_response"]
        gf = gen_flags(trace)
        sf = scorer_components(resp)

        g_count = sum(gf.values())
        s_count = sum([sf["grounding"], sf["action"], sf["question"]])
        gen_counts.append(g_count)
        scorer_counts.append(s_count)
        structure_scores.append(score_structure(resp))

        if g_count == s_count and gf["grounding"] == sf["grounding"] and gf["action"] == sf["action"] and gf["question"] == sf["question"]:
            both_agree_exact += 1
        if s_count > g_count:
            scorer_gt_gen += 1
        if g_count > s_count:
            gen_gt_scorer += 1

        for comp in ("grounding", "action", "question"):
            if sf[comp] and not gf[comp]:
                scorer_extra[comp] += 1
                if comp == "grounding":
                    for m in sf["grounding_markers"]:
                        marker_when_scorer_extra[f"grounding:{m}"] += 1
                elif comp == "action":
                    for m in sf["action_markers"]:
                        marker_when_scorer_extra[f"action:{m}"] += 1
                else:
                    for m in sf["question_reasons"]:
                        marker_when_scorer_extra[f"question:{m}"] += 1
                if len(examples[comp]) < 3:
                    examples[comp].append({
                        "risk": row["risk_label"],
                        "gen_flags": gf,
                        "scorer": {k: sf[k] for k in ("grounding", "action", "question")},
                        "markers": {
                            "grounding": sf["grounding_markers"],
                            "action": sf["action_markers"],
                            "question": sf["question_reasons"],
                        },
                        "resp_preview": resp[:300].replace("\n", " | "),
                    })
            if gf[comp] and not sf[comp]:
                gen_extra[comp] += 1

    from statistics import mean, pstdev

    print("=" * 70)
    print(f"CONDITION: {name}")
    print(f"  genome: w_e={genome.w_e:.4f} w_s={genome.w_s:.4f} w_c={genome.w_c:.4f} m={genome.memory_window}")
    print(f"  n={n}")
    print("-" * 70)
    print(f"  Generator component count: mean={mean(gen_counts):.4f}  "
          f"min={min(gen_counts)} max={max(gen_counts)}  "
          f"hist={dict(Counter(gen_counts))}")
    print(f"  Scorer component count:    mean={mean(scorer_counts):.4f}  "
          f"min={min(scorer_counts)} max={max(scorer_counts)}  "
          f"hist={dict(Counter(scorer_counts))}")
    print(f"  Structure score:           mean={mean(structure_scores):.4f}  "
          f"sd={pstdev(structure_scores):.4f}")
    print()
    print(f"  Exact flag agreement:      {both_agree_exact}/{n} ({100*both_agree_exact/n:.1f}%)")
    print(f"  Scorer count > gen count:  {scorer_gt_gen}/{n} ({100*scorer_gt_gen/n:.1f}%)")
    print(f"  Gen count > scorer count:  {gen_gt_scorer}/{n} ({100*gen_gt_scorer/n:.1f}%)")
    print()
    print(f"  Scorer EXTRA components (false positives vs generator flags):")
    for comp in ("grounding", "action", "question"):
        print(f"    {comp:10s}: {scorer_extra[comp]:4d} / {n} ({100*scorer_extra[comp]/n:.1f}%)")
    print(f"  Generator EXTRA (scorer miss / truncation):")
    for comp in ("grounding", "action", "question"):
        print(f"    {comp:10s}: {gen_extra[comp]:4d} / {n} ({100*gen_extra[comp]/n:.1f}%)")
    print()
    print("  Markers responsible when scorer adds a component generator didn't set:")
    if not marker_when_scorer_extra:
        print("    (none)")
    else:
        for k, v in marker_when_scorer_extra.most_common(20):
            print(f"    {k:30s} {v:4d}")
    print()
    if examples:
        print("  Example false-positive responses (up to 3 per component):")
        for comp, exs in examples.items():
            for i, ex in enumerate(exs, 1):
                print(f"    [{comp} #{i}] risk={ex['risk']} gen={ex['gen_flags']} "
                      f"scorer={ex['scorer']} markers={ex['markers']}")
                print(f"      {ex['resp_preview'][:200]}")
    print()
    return {
        "name": name,
        "gen_mean": mean(gen_counts),
        "scorer_mean": mean(scorer_counts),
        "structure_mean": mean(structure_scores),
        "scorer_extra": dict(scorer_extra),
        "marker_fp": marker_when_scorer_extra.most_common(10),
        "exact_agree": both_agree_exact / n,
        "scorer_gt_gen_rate": scorer_gt_gen / n,
    }


def main():
    val_df = load_val_df()
    print(f"Validation set: {len(val_df)} prompts")
    print(f"Risk mix: {val_df['risk_label'].value_counts().to_dict()}")
    print()

    results = []
    # Mid-regime points (code: 0.35 <= w_c < 0.55 → shuffle, up to 2)
    for w_c in (0.40, 0.50):
        results.append(run_condition(f"w_c={w_c:.2f}", make_genome(w_c), val_df))

    # B1 bottom regime
    results.append(run_condition("B1 (w_c=0.10, m=256)", make_b1_genome(), val_df))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for r in results:
        print(f"{r['name']}: gen_mean={r['gen_mean']:.3f} scorer_mean={r['scorer_mean']:.3f} "
              f"structure={r['structure_mean']:.3f} exact_agree={100*r['exact_agree']:.1f}% "
              f"scorer>gen={100*r['scorer_gt_gen_rate']:.1f}% "
              f"FP_by_comp={r['scorer_extra']}")
        if r["marker_fp"]:
            print(f"  top FP markers: {r['marker_fp'][:5]}")


if __name__ == "__main__":
    main()
