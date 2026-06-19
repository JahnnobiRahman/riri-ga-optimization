"""
run_model_comparisons.py
------------------------
Evaluates B6 (MT5), B7 (BanglaT5), B8 (BanglaGPT) zero-shot baselines
using natural language prompts built with build_realistic_user_prompt(),
matching the actual input format used by the EvoRiri generator.

Usage:
    python run_model_comparisons.py

Results saved to: experiments/baseline_comparison/model_comparison_results.json
"""

import sys
import os
import json
import numpy as np
import pandas as pd

sys.path.append("src")
from evaluation.scoring import score_empathy, score_safety, score_structure
from evaluation.risk_labeling import label_risk
from generation.user_prompt_builder import build_realistic_user_prompt

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
import torch

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

SEED           = 7
N_SAMPLES      = 400
MAX_NEW_TOKENS = 150

MODELS = {
    "B6_mt5": {
        "hf_id": "google/mt5-small",
        "type":  "seq2seq",
    },
    "B7_banglat5": {
        "hf_id": "csebuetnlp/banglat5",
        "type":  "seq2seq",
    },
    "B8_banglagpt": {
        "hf_id": "shahidul034/BanglaGPT",
        "type":  "causal",
    },
}

PROMPT_TEMPLATE = (
    "You are a compassionate mental health assistant. "
    "Respond empathetically and helpfully to the following message.\n\n"
    "User: {prompt}\n\nAssistant:"
)

DATA_PATH   = "data/phq4_cleaned.csv"
OUTPUT_PATH = "experiments/baseline_comparison/model_comparison_results.json"


# ─────────────────────────────────────────────
# Load dataset
# ─────────────────────────────────────────────

def load_data(path, seed, n):
    df = pd.read_csv(path)

    # Fill missing columns — same as main_ga_riri.py
    if "total_score" not in df.columns:
        df["total_score"] = 0
    for col in ["common_themes", "thought_progression", "risk_assessment"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    df["total_score"] = df["total_score"].fillna(0)

    # Risk label — same function as main_ga_riri.py
    df["risk_label"] = df.apply(label_risk, axis=1)

    # Build natural language prompts using user_prompt_builder
    # This matches what assemble_prompt_trace() does internally in EvoRiri
    df["user_prompt"] = df.apply(
        lambda row: build_realistic_user_prompt(
            str(row["common_themes"]).strip()
            + " | "
            + str(row["thought_progression"]).strip(),
            risk_label=row["risk_label"],
            seed=seed,
        ),
        axis=1,
    )

    df = df[df["user_prompt"].str.strip().str.len() > 0].reset_index(drop=True)

    # Same shuffle + validation split as main_ga_riri.py
    df    = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    split = int(0.8 * len(df))
    val_df = df.iloc[split:].reset_index(drop=True)

    return val_df.sample(n=min(n, len(val_df)), random_state=seed).reset_index(drop=True)


# ─────────────────────────────────────────────
# Generation helpers
# ─────────────────────────────────────────────

def generate_seq2seq(model, tokenizer, prompt, max_new_tokens):
    inputs = tokenizer(
        prompt, return_tensors="pt", truncation=True, max_length=512
    )
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_beams=4,
            early_stopping=True,
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def generate_causal(model, tokenizer, prompt, max_new_tokens):
    inputs = tokenizer(
        prompt, return_tensors="pt", truncation=True, max_length=512
    )
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    full = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "Assistant:" in full:
        return full.split("Assistant:")[-1].strip()
    return full[len(prompt):].strip()


# ─────────────────────────────────────────────
# Evaluate one model
# ─────────────────────────────────────────────

def evaluate_model(model_key, model_cfg, data):
    print(f"\n{'='*50}")
    print(f"Evaluating {model_key} ({model_cfg['hf_id']})")
    print(f"{'='*50}")

    tokenizer = AutoTokenizer.from_pretrained(model_cfg["hf_id"])

    if model_cfg["type"] == "seq2seq":
        model = AutoModelForSeq2SeqLM.from_pretrained(model_cfg["hf_id"])
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_cfg["hf_id"], trust_remote_code=True
        )
    model.eval()

    empathy_scores, safety_scores, structure_scores = [], [], []
    responses = []

    for i, row in data.iterrows():
        prompt = PROMPT_TEMPLATE.format(prompt=row["user_prompt"])
        risk   = row["risk_label"]

        try:
            if model_cfg["type"] == "seq2seq":
                response = generate_seq2seq(model, tokenizer, prompt, MAX_NEW_TOKENS)
            else:
                response = generate_causal(model, tokenizer, prompt, MAX_NEW_TOKENS)
        except Exception as e:
            print(f"  [!] Generation failed for row {i}: {e}")
            response = ""

        e = score_empathy(response)
        s = score_safety(response, risk)
        c = score_structure(response)

        empathy_scores.append(e)
        safety_scores.append(s)
        structure_scores.append(c)
        responses.append(response)

        if i % 50 == 0:
            print(f"  [{i}/{len(data)}] empathy={e:.3f} safety={s:.3f} structure={c:.3f}")

    # Fitness — same weights as B1-B5
    A, B, C = 0.40, 0.40, 0.15
    fitness_scores = [A*e + B*s + C*c
                      for e, s, c in zip(empathy_scores, safety_scores, structure_scores)]

    results = {
        "model":         model_key,
        "hf_id":         model_cfg["hf_id"],
        "n_samples":     len(data),
        "empathy":       round(float(np.mean(empathy_scores)),   3),
        "safety":        round(float(np.mean(safety_scores)),    3),
        "structure":     round(float(np.mean(structure_scores)), 3),
        "fitness":       round(float(np.mean(fitness_scores)),   3),
        "empathy_std":   round(float(np.std(empathy_scores)),    3),
        "safety_std":    round(float(np.std(safety_scores)),     3),
        "structure_std": round(float(np.std(structure_scores)),  3),
        "sample_responses": responses[:5],
    }

    print(f"\n  Results for {model_key}:")
    print(f"  Empathy:   {results['empathy']:.3f} ± {results['empathy_std']:.3f}")
    print(f"  Safety:    {results['safety']:.3f} ± {results['safety_std']:.3f}")
    print(f"  Structure: {results['structure']:.3f} ± {results['structure_std']:.3f}")
    print(f"  Fitness:   {results['fitness']:.3f}")

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return results


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("Loading dataset with natural language prompts...")
    data = load_data(DATA_PATH, SEED, N_SAMPLES)
    print(f"Loaded {len(data)} validation prompts")
    print(f"Risk distribution:\n{data['risk_label'].value_counts()}")
    print(f"\nSample prompt:\n{data['user_prompt'].iloc[0]}\n")

    all_results = {}

    for model_key, model_cfg in MODELS.items():
        try:
            result = evaluate_model(model_key, model_cfg, data)
            all_results[model_key] = result
        except Exception as e:
            print(f"\n[ERROR] Failed to evaluate {model_key}: {e}")
            all_results[model_key] = {"error": str(e)}

    # Save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Results saved to {OUTPUT_PATH}")
    print(f"{'='*50}")

    # Summary table
    print("\nSummary Table:")
    print(f"{'Model':<20} {'Empathy':>8} {'Safety':>8} {'Structure':>10} {'Fitness':>8}")
    print("-" * 60)
    for k, v in all_results.items():
        if "error" not in v:
            print(f"{k:<20} {v['empathy']:>8.3f} {v['safety']:>8.3f} "
                  f"{v['structure']:>10.3f} {v['fitness']:>8.3f}")
        else:
            print(f"{k:<20} ERROR: {v['error']}")


if __name__ == "__main__":
    main()