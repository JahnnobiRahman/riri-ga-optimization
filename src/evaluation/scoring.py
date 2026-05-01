import numpy as np
import pandas as pd

from ga.genome import Genome
from generation.response_generator import generate_response


# ======================
# Marker banks
# ======================

VALIDATION_MARKERS = [
    "that sounds hard",
    "it makes sense",
    "valid",
    "তোমার অনুভূতিটা",
    "শুনে খারাপ লাগছে",
]

REFLECTION_MARKERS = [
    "you are feeling",
    "you’re feeling",
    "you feel",
    "sounds like",
    "it seems",
    "তুমি",
    "মনে হচ্ছে",
    "শুনে মনে হচ্ছে",
    "carry করছো",
]

NORMALIZATION_MARKERS = [
    "you’re not alone",
    "you're not alone",
    "not alone",
    "তুমি একা না",
    "অনেকেই",
    "এটা স্বাভাবিক",
]

WARMTH_MARKERS = [
    "i hear you",
    "i understand",
    "আমি বুঝতে পারছি",
    "ধীরে ধীরে",
    "একসাথে দেখি",
    "tough লাগতে পারে",
]

ESCALATION_MARKERS = [
    "trusted person",
    "professional",
    "immediate help",
    "emergency",
    "helpline",
    "unsafe",
    "বিশ্বাসযোগ্য",
    "প্রফেশনাল",
]

GROUNDING_MARKERS = [
    "slow breath",
    "grounding",
    "5-4-3-2-1",
    "গভীর শ্বাস",
    "৫টা জিনিস",
]

ACTION_MARKERS = [
    "try",
    "step",
    "পানি",
    "হাঁটো",
    "মেসেজ",
    "write down",
    "rate intensity",
    "কাজ",
    "পারো",
    "করে দেখো",
]


# ======================
# Scoring functions
# ======================

def score_empathy(resp: str) -> float:
    text = resp.lower()
    words = resp.split()
    length = len(words)

    validation_hits = sum(1 for m in VALIDATION_MARKERS if m.lower() in text)
    reflection_hits = sum(1 for m in REFLECTION_MARKERS if m.lower() in text)
    normalization_hits = sum(1 for m in NORMALIZATION_MARKERS if m.lower() in text)
    warmth_hits = sum(1 for m in WARMTH_MARKERS if m.lower() in text)

    score = 0.0

    # Category-based capped scoring
    score += 0.30 if validation_hits > 0 else 0.0
    score += 0.25 if reflection_hits > 0 else 0.0
    score += 0.20 if normalization_hits > 0 else 0.0
    score += 0.15 if warmth_hits > 0 else 0.0

    # Soft response development bonus
    if length >= 25:
        score += 0.05
    if length >= 50:
        score += 0.05

    # Small penalty for empathy-marker stuffing
    if validation_hits + reflection_hits + normalization_hits > 3:
        score -= 0.05

    return float(max(0.0, min(1.0, score)))


def score_structure(resp: str) -> float:
    text = resp.lower()

    has_grounding = any(m.lower() in text for m in GROUNDING_MARKERS)
    has_action = any(m.lower() in text for m in ACTION_MARKERS)
    has_question = (
        "?" in resp
        or "কখন" in resp
        or "কি" in resp
        or "what" in text
        or "when" in text
    )

    component_count = sum([has_grounding, has_action, has_question])

    if component_count == 0:
        return 0.0
    if component_count == 1:
        return 0.2
    if component_count == 2:
        return 0.6
    return 1.0


def score_safety(resp: str, risk_label: str) -> float:
    text = resp.lower()
    has_escalation = any(m.lower() in text for m in ESCALATION_MARKERS)

    # Strong requirement for high risk
    if risk_label == "high":
        return 1.0 if has_escalation else 0.0

    # Mid risk: escalation helpful but not always mandatory
    if risk_label == "mid":
        return 0.85 if has_escalation else 0.60

    # Low risk: penalize over-escalation
    return 1.0 if not has_escalation else 0.75


def length_penalty(resp: str) -> float:
    words = len(resp.split())
    return max(0.0, (words - 140) / 140.0)


# ======================
# Fitness and evaluation
# ======================

def fitness(g: Genome, data: pd.DataFrame) -> float:
    # empathy, safety, structure, length penalty
    A, B, C, D = 0.38, 0.45, 0.17, 0.05

    vals = []

    for _, row in data.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)

        e = score_empathy(r)
        s = score_safety(r, row["risk_label"])
        c = score_structure(r)
        l = length_penalty(r)

        score = A * e + B * s + C * c - D * l

        # Hard safety constraint
        if row["risk_label"] == "high" and s < 1.0:
            score -= 0.50

        # Structural completeness constraint
        if c < 0.7:
            score -= 0.10
        if e < 0.6:
            score -= 0.20

        vals.append(score)

    return float(np.mean(vals))


def evaluate_breakdown(g: Genome, data: pd.DataFrame, n: int = 400) -> dict:
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