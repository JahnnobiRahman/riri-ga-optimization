
import re
import pandas as pd





# ======================
# 2) Risk labeling functions
# ======================


# Clinically relevant suicide/self-harm indicators (English + Bangla examples)
RISK_PATTERNS = [
    r"\bsuicid(e|al)?\b",
    r"\bself[- ]?harm\b",
    r"\bkill myself\b",
    r"\bhurt myself\b",
    r"\bend my life\b",
    r"\bunsafe\b",
    r"আত্মহত্যা",
    r"নিজেকে (মার|ক্ষতি)",
    r"মরে যেতে",
]

def has_meaningful_risk(text: str) -> bool:
    """
    Detects clinically relevant suicide/self-harm indicators
    using regex pattern matching.
    """
    if pd.isna(text):
        return False

    text = str(text).lower().strip()

    if not text:
        return False

    for pattern in RISK_PATTERNS:
        if re.search(pattern, text):
            return True

    return False



def label_risk(row) -> str:

    """
    Assigns categorical risk level based on:
    1) PHQ-4 total score
    2) Presence of explicit self-harm/suicide indicators
    """
    total = int(row.get("total_score", 0))

    # Detect explicit risk text
    risk_flag = has_meaningful_risk(row.get("risk_assessment", ""))

    # PHQ-4 risk mapping:
    # 0–2: normal
    # 3–5: mild
    # 6–8: moderate
    # 9–12: severe

    if risk_flag or total >= 9:
        return "high"
    elif total >= 6:
        return "mid"
    else:
        return "low"

