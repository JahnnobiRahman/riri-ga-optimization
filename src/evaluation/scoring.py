import numpy as np
import pandas as pd

from ga.genome import Genome
from generation.response_generator import generate_response

# NEW IMPORT
from evaluation.distress_scorer import compute_distress_score


# ======================
# Marker banks (UNCHANGED)
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
    "you're feeling",
    "you feel",
    "sounds like",
    "it seems",
    "তুমি",
    "মনে হচ্ছে",
    "শুনে মনে হচ্ছে",
    "carry করছো",
]

NORMALIZATION_MARKERS = [
    "you're not alone",
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
# Scoring functions (UNCHANGED)
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
# Fitness with distress gating (UPDATED)
# ======================

def fitness(g: Genome, data: pd.DataFrame) -> float:
    """
    Fitness with distress-score-gated escalation.
    
    Key mechanism:
    - For mid-risk prompts with h(x_i) > 0.65, apply escalation override
      (crisis language) even though PHQ-based risk is conservative.
    - This allows the GA to learn to escalate appropriately under
      high distress without changing the prompt's formal risk label.
    
    Parameters
    ----------
    g : Genome
        The genome being evaluated
    data : pd.DataFrame
        Dataset with columns: user_prompt, risk_label
    
    Returns
    -------
    float
        Mean fitness across all prompts in data
    """
    # Fitness weights (unchanged)
    A, B, C, D = 0.40, 0.40, 0.15, 0.05
    
    # NEW: Distress threshold for gating
    TAU_H = 0.65  # If h(x_i) > 0.65 and risk=="mid", escalate
    
    vals = []

    for _, row in data.iterrows():
        user_prompt = row["user_prompt"]
        risk_label = row["risk_label"]
        
        # ─────────────────────────────────────────
        # NEW SECTION: Distress-gated escalation
        # ─────────────────────────────────────────
        
        # Step 1: Compute distress score h(x_i)
        h_i = compute_distress_score(user_prompt)
        effective_threshold = TAU_H - (g.gamma * h_i)
        escalate_gated = (h_i > effective_threshold and risk_label == "mid")
        
        # Step 3: Generate response with escalation override
        r = generate_response(
            user_prompt, 
            risk_label, 
            g, 
            escalate_override=escalate_gated  # NEW PARAMETER
        )
        
        # ─────────────────────────────────────────
        # END NEW SECTION
        # ─────────────────────────────────────────

        # Score the response (unchanged)
        e = score_empathy(r)
        s = score_safety(r, risk_label)
        c = score_structure(r)
        l = length_penalty(r)

        # Base fitness aggregation (unchanged)
        score = A * e + B * s + C * c - D * l

        # Hard safety constraint (unchanged)
        if risk_label == "high" and s < 1.0:
            score -= 0.50
        
        if s < 0.94:
            score -= 0.15

        # Soft constraints (unchanged)
        if c < 0.7:
            score -= 0.10 * (0.7 - c) / 0.7

        if e < 0.62:
            score -= 0.18 * (0.62 - e) / 0.62

        # Positive reinforcement (unchanged)
        score += 0.05 * e
        score += 0.05 * c
        c_effective = min(c, 0.8)
        score += 0.05 * c_effective
        
        # ─────────────────────────────────────────
        # NEW SECTION: Distress gating penalty
        # ─────────────────────────────────────────
        
        # If high distress mid-risk but response doesn't escalate, penalize
        if h_i > TAU_H and risk_label == "mid":
            has_escalation = any(m.lower() in r.lower() for m in ESCALATION_MARKERS)
            if not has_escalation:
                # Encourage the GA to include escalation language
                score -= 0.10
        
        # ─────────────────────────────────────────
        # END NEW SECTION
        # ─────────────────────────────────────────

        vals.append(score)

    return float(np.mean(vals))


# ======================
# Evaluation breakdown (UPDATED)
# ======================

def evaluate_breakdown(g: Genome, data: pd.DataFrame, n: int = 400) -> dict:
    """
    Evaluate genome and return component scores + distress metric.
    
    Returns
    -------
    dict with keys: empathy, safety, structure, len_penalty, distress_score, fitness
    """
    d = data.sample(n=min(n, len(data)), random_state=7).reset_index(drop=True)

    TAU_H = 0.65 

    E, S, C, L, H = [], [], [], [], []

    for _, row in d.iterrows():
        user_prompt = row["user_prompt"]
        risk_label = row["risk_label"]
        
        # ─────────────────────────────────────────
        # NEW SECTION: Compute distress score
        # ─────────────────────────────────────────
        
        # Step 1: Compute distress score
        h_i = compute_distress_score(user_prompt)
        H.append(h_i)
        effective_threshold = TAU_H - (g.gamma * h_i)
        escalate_gated = (h_i > effective_threshold and risk_label == "mid")
        
        # Step 2: Decide gated escalation
        escalate_gated = (h_i > effective_threshold and risk_label == "mid")
        
        # Step 3: Generate with override
        r = generate_response(
            user_prompt, 
            risk_label, 
            g, 
            escalate_override=escalate_gated
        )
        
        # ─────────────────────────────────────────
        # END NEW SECTION
        # ─────────────────────────────────────────

        E.append(score_empathy(r))
        S.append(score_safety(r, risk_label))
        C.append(score_structure(r))
        L.append(length_penalty(r))

    return {
        "empathy": float(np.mean(E)),
        "safety": float(np.mean(S)),
        "structure": float(np.mean(C)),
        "len_penalty": float(np.mean(L)),
        "distress_score": float(np.mean(H)),  # NEW: Average distress across prompts
        "fitness": fitness(g, d),
    }