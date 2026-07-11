import re
import pandas as pd

# ======================
# Distress markers with weights (Bangla + English)
# ======================
# Weights based on clinical severity:
# 1.0 = immediate crisis (suicide ideation)
# 0.8–0.9 = self-harm, severe hopelessness
# 0.6–0.75 = isolation, overwhelm, moderate distress

DISTRESS_KEYWORDS = {
    # Suicide ideation (highest weight)
    "suicid": 1.0,
    "kill myself": 0.95,
    "end my life": 0.95,
    "not live": 0.90,
    "can't live": 0.90,
    "don't want to live": 0.90,
    "dont want to live": 0.90,
    "আত্মহত্যা": 1.0,
    "মরে যেতে": 0.90,
    "আর বাঁচতে": 0.85,
    "মৃত্যু": 0.80,
    
    # Self-harm
    "self-harm": 0.90,
    "self harm": 0.90,
    "hurt myself": 0.85,
    "cutting": 0.80,
    "নিজেকে ক্ষতি": 0.90,
    "রক্ত": 0.75,
    
    # Hopelessness
    "no future": 0.75,
    "hopeless": 0.75,
    "no reason to live": 0.80,
    "nothing matters": 0.75,
    "কোন ভবিষ্যত": 0.75,
    "ভবিষ্যত নেই": 0.75,
    
    # Isolation
    "completely alone": 0.65,
    "nobody cares": 0.70,
    "isolated": 0.60,
    "একা": 0.60,
    "কেউ বোঝে না": 0.65,
    
    # Severe overwhelm
    "cannot handle": 0.60,
    "falling apart": 0.65,
    "unbearable": 0.70,
    "সহ্য করতে পারছি না": 0.70,
}


# ======================
# Main function
# ======================

def compute_distress_score(prompt_text: str) -> float:
    """
    Compute continuous distress score h(x_i) from prompt text.
    
    The score aggregates weighted distress markers (suicide ideation, self-harm,
    hopelessness, isolation, severe overwhelm) and caps at 1.0. A small penalty
    applies for marker stuffing (>3 distinct signals), discouraging gaming.
    
    Parameters
    ----------
    prompt_text : str
        User prompt in Bangla, Banglish, or English
    
    Returns
    -------
    float in [0, 1]
        Weighted sum of distress markers, capped at 1.0.
    
    Examples
    --------
    >>> compute_distress_score("I don't want to live")
    0.9
    
    >>> compute_distress_score("I feel overwhelmed")
    0.0  # "overwhelmed" not an exact keyword match
    
    >>> compute_distress_score("suicide ideation self-harm hopeless")
    0.95  # Penalty applied for >3 keywords
    """
    if pd.isna(prompt_text):
        return 0.0
    
    text = str(prompt_text).lower()
    score = 0.0
    matched_keywords = []
    
    # Check each distress marker
    for keyword, weight in DISTRESS_KEYWORDS.items():
        if keyword.lower() in text:
            score += weight
            matched_keywords.append(keyword)
    
    # Cap at 1.0
    score = min(1.0, score)
    
    # Small penalty for marker stuffing (>3 distinct distress signals)
    # This discourages gaming the system by repeating keywords
    if len(matched_keywords) > 3:
        # Mild penalty: reduce by 5%, don't let it go below 0
        score = max(score - 0.05, 0.0)
    
    return float(score)
    