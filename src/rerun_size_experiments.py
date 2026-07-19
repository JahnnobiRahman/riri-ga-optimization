# src/rerun_size_experiments.py
import sys
import os
import json

sys.path.append(os.path.dirname(__file__))

import pandas as pd
from evaluation.risk_labeling import label_risk
from experiments.dataset_size_experiment import dataset_size_experiment
from experiments.population_experiment import population_size_experiment

SEED = 7

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "phq4_cleaned.csv")
OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", "v2_population_experiment")
os.makedirs(OUT_DIR, exist_ok=True)

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in df.columns:
        df[col] = ""
if "total_score" not in df.columns:
    df["total_score"] = 0
df["common_themes"] = df["common_themes"].fillna("")
df["thought_progression"] = df["thought_progression"].fillna("")
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
train_df = df.iloc[:split].reset_index(drop=True)
val_df = df.iloc[split:].reset_index(drop=True)

print(f"Train: {len(train_df)} | Val: {len(val_df)}")

print("\n" + "=" * 60)
print("DATASET SIZE EXPERIMENT (corrected)")
print("=" * 60)
dataset_results, dataset_raw = dataset_size_experiment(train_df, val_df)
dataset_results.to_csv(os.path.join(OUT_DIR, "dataset_size_experiment_FIXED.csv"), index=False)
dataset_raw.to_csv(os.path.join(OUT_DIR, "dataset_size_raw_runs_FIXED.csv"), index=False)
print("Saved dataset size experiment results.")

print("\n" + "=" * 60)
print("POPULATION SIZE EXPERIMENT (corrected)")
print("=" * 60)
pop_results = population_size_experiment(train_df, val_df)
pop_results.to_csv(os.path.join(OUT_DIR, "population_experiment_FIXED.csv"), index=False)
print("Saved population size experiment results.")

print("\nAll done.")