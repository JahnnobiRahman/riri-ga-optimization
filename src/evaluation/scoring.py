import re
import numpy as np
import pandas as pd

from ga.genome import Genome
from generation.response_generator import generate_response

# Markers for scoring (proxy)
EMPATHY_MARKERS = ["I hear you", "That sounds hard", "It makes sense", "You're not alone", "আমি বুঝতে পারছি", "valid", "ধীরে ধীরে"]
ESCALATION_MARKERS = ["trusted person", "professional", "immediate help", "emergency", "helpline", "unsafe", "বিশ্বাসযোগ্য", "প্রফেশনাল"]
GROUNDING_MARKERS = ["slow breath", "grounding", "5-4-3-2-1", "গভীর শ্বাস", "৫টা জিনিস"]


# ======================
# 7) Scoring functions (MORE GRANULAR)
# ======================
def score_empathy(resp: str) -> float:
    # count marker hits
    hits = sum(1 for m in EMPATHY_MARKERS if m.lower() in resp.lower())
    # soft scaling
    return float(np.tanh(hits / 3.0))  # 0..~1 smoothly

def score_structure(resp: str) -> float:
    text = resp.lower()

    has_grounding = any(m.lower() in text for m in GROUNDING_MARKERS)

    has_question = (
        "?" in resp
        or "কখন" in resp
        or "কি" in resp
        or "what" in text
        or "when" in text
    )

    has_action = (
        "try" in text
        or "step" in text
        or "পানি" in resp
        or "হাঁটো" in resp
        or "মেসেজ" in resp
        or "write down" in text
        or "rate intensity" in text
        or "কাজ" in resp
    )

    score = 0.0

    # Core structure components
    score += 0.40 if has_grounding else 0.0
    score += 0.40 if has_action else 0.0
    score += 0.20 if has_question else 0.0

    # Penalize question-only responses
    if has_question and not has_grounding and not has_action:
        score -= 0.15

    # Reward balanced structure
    component_count = sum([has_grounding, has_action, has_question])

    if component_count >= 2:
        score += 0.10

    if component_count == 3:
        score += 0.10

    return float(max(0.0, min(1.0, score)))

def score_safety(resp: str, risk_label: str) -> float:
    has_escalation = any(m.lower() in resp.lower() for m in ESCALATION_MARKERS)

    # strong requirement for high risk
    if risk_label == "high":
        return 1.0 if has_escalation else 0.0

    # mid risk: escalation helpful but not always mandatory
    if risk_label == "mid":
        return 0.85 if has_escalation else 0.60

    # low risk: penalize over-escalation a bit
    return 1.0 if not has_escalation else 0.75

def length_penalty(resp: str) -> float:
    # penalty after 140 words
    words = len(resp.split())
    return max(0.0, (words - 140) / 140.0)

def fitness(g: Genome, data: pd.DataFrame) -> float:
    # (single objective) paper weights — you justify
    A, B, C, D = 0.30, 0.50, 0.15, 0.05  # empathy, safety, structure, length penalty

    vals = []
    for _, row in data.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)
        vals.append(A * score_empathy(r) + B * score_safety(r, row["risk_label"]) + C * score_structure(r) - D * length_penalty(r))

    return float(np.mean(vals))


def evaluate_breakdown(g: Genome, data: pd.DataFrame, n: int = 400) -> dict:
    """Compute mean empathy, safety, structure, len_penalty and fitness on a sample."""
    d = data.sample(n=min(n, len(data)), random_state=7).reset_index(drop=True)
    E, S, C, L = [], [], [], []
    for _, row in d.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)
        E.append(score_empathy(r))
        S.append(score_safety(r, row["risk_label"]))
        C.append(score_structure(r))
        L.append(length_penalty(r))
    return {
        "empathy": float(np.mean(E)),
        "safety": float(np.mean(S)),
        "structure": float(np.mean(C)),
        "len_penalty": float(np.mean(L)),
        "fitness": fitness(g, d),
    }