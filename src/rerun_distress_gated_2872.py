import sys
import os
import json
from dataclasses import asdict

sys.path.append(os.path.dirname(__file__))

import pandas as pd
from evaluation.risk_labeling import label_risk
from evaluation.scoring import evaluate_breakdown
from ga.runner import run_ga

SEED = 7

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "phq4_cleaned.csv")
OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", "v2_population_experiment")

print("Loading dataset...")
raw = pd.read_csv(DATA_PATH)

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in raw.columns:
        raw[col] = ""
raw["common_themes"] = raw["common_themes"].fillna("")
raw["thought_progression"] = raw["thought_progression"].fillna("")

raw["risk_label"] = raw.apply(label_risk, axis=1)
raw["user_prompt"] = (
    raw["common_themes"].astype(str).str.strip()
    + " | "
    + raw["thought_progression"].astype(str).str.strip()
).str.strip(" |")

raw = raw[raw["user_prompt"].str.len() > 0].reset_index(drop=True)
print(f"After filtering: {len(raw)} prompts")
print("Risk distribution:")
print(raw["risk_label"].value_counts())

data = raw[["user_prompt", "risk_label"]].copy()
print(f"\nFinal dataset: {len(data)} prompts")

# ── 80/20 split, matching baseline_comparison.py and paper Section 3.2 ──
data = data.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
split = int(0.8 * len(data))
train_data = data.iloc[:split].reset_index(drop=True)
val_data = data.iloc[split:].reset_index(drop=True)

print(f"Train size: {len(train_data)}")
print(f"Validation size: {len(val_data)}\n")

print("Starting GA on train split (80/20, matches paper methodology)...")
best_genome, log = run_ga(
    train_data=train_data,
    pop_size=100,
    generations=20,
    eval_n=600,
    seed=SEED,
    use_seed_genomes=True,
)

log_path = os.path.join(OUT_DIR, "ga_log_distress_gated_2872_SPLIT.json")
with open(log_path, "w") as f:
    json.dump(log, f, indent=2)
print(f"Saved fitness log to: {log_path}")

genome_path = os.path.join(OUT_DIR, "best_genome_distress_gated_2872_SPLIT.json")
with open(genome_path, "w") as f:
    json.dump(asdict(best_genome), f, indent=2)
print(f"Saved best genome to: {genome_path}")

print(f"\n✅ GA Complete!")
print(f"Train size: {len(train_data)} | Val size: {len(val_data)}")
print(f"Best fitness (from log, train-time): {max(log['best']):.4f}")
print(f"Best genome: {best_genome}")

print("\nBreakdown on VALIDATION set (held-out, matches paper's val_df evaluation):")
breakdown = evaluate_breakdown(best_genome, val_data, n=min(600, len(val_data)))
for k, v in breakdown.items():
    print(f"  {k}: {v:.4f}")

breakdown_path = os.path.join(OUT_DIR, "breakdown_distress_gated_2872_SPLIT.json")
with open(breakdown_path, "w") as f:
    json.dump(breakdown, f, indent=2)
print(f"Saved breakdown to: {breakdown_path}")