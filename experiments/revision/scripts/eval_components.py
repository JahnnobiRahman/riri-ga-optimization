"""Per-response escalation and structure components for B1, B2, B4 on the
paper's 400-prompt validation subsample (seed 7), seeded generation."""
import json, random, sys
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from evaluation.risk_labeling import label_risk
from evaluation.scoring import (ESCALATION_MARKERS, GROUNDING_MARKERS, ACTION_MARKERS,
                                score_safety, score_structure, TAU_H)
from evaluation.distress_scorer import compute_distress_score
from generation.response_generator import generate_response
from ga.genome import Genome

df = pd.read_csv("data/phq4_cleaned.csv")
for c in ["common_themes", "thought_progression", "risk_assessment"]:
    df[c] = df[c].fillna("") if c in df.columns else ""
df["total_score"] = df["total_score"].fillna(0)
df["risk_label"] = df.apply(label_risk, axis=1)
df["user_prompt"] = (df["common_themes"].astype(str).str.strip() + " | " + df["thought_progression"].astype(str).str.strip()).str.strip(" |")
df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True).sample(frac=1.0, random_state=7).reset_index(drop=True)
val = df.iloc[int(0.8 * len(df)):].reset_index(drop=True)
v400 = val.sample(n=400, random_state=7).reset_index(drop=True)

def load(p):
    d = json.load(open(p)); g = Genome(**{k: d[k] for k in ["p_id","w_s","w_e","w_c","memory_window","theta_mid","theta_high","gamma"]}); g.normalize(); return g
B = "experiments/baseline_comparison"
G = {"B1": load(f"{B}/best_genome_B1.json"), "B2": load(f"{B}/best_genome_B2.json"), "B4": load(f"{B}/best_genome_B4.json")}
out = {}
for name, g in G.items():
    random.seed(7); np.random.seed(7)
    rows = []
    for _, r in v400.iterrows():
        up, rl = r["user_prompt"], r["risk_label"]
        h = compute_distress_score(up)
        esc_override = (h > TAU_H - g.gamma * h and rl == "mid")
        resp = generate_response(up, rl, g, escalate_override=esc_override)
        t = resp.lower()
        rows.append({"risk": rl,
                     "esc": any(m.lower() in t for m in ESCALATION_MARKERS),
                     "g": any(m.lower() in t for m in GROUNDING_MARKERS),
                     "a": any(m.lower() in t for m in ACTION_MARKERS),
                     "q": ("?" in resp or "কখন" in resp or "কি" in resp or "what" in t or "when" in t),
                     "S": score_safety(resp, rl), "C": score_structure(resp)})
    d = pd.DataFrame(rows)
    out[name] = {
        "n_by_risk": d.risk.value_counts().to_dict(),
        "esc_rate_by_risk": d.groupby("risk").esc.mean().to_dict(),
        "safety_by_risk": d.groupby("risk").S.mean().to_dict(),
        "component_rate": {"grounding": d.g.mean(), "action": d.a.mean(), "question": d.q.mean(), "all_three": (d.g & d.a & d.q).mean()},
        "structure_mean": d.C.mean(), "safety_mean": d.S.mean(),
    }
json.dump(out, open(sys.argv[1], "w"), indent=2, default=float)
print(json.dumps(out, indent=1, default=float))
