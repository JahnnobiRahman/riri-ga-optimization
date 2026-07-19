"""
build_multiturn_dataset.py

Filters and de-identifies raw multi-turn conversation data (all_data.jsonl)
into a clean, research-usable multi-turn dataset, analogous to how
phq4_cleaned.csv was derived from the raw single-turn PHQ-4 screening data.

Filtering criteria (per session):
  - phq.is_completed == True
  - at least MIN_USER_EXCHANGES real (non-empty) user messages

Risk labeling:
  - Same PHQ-4 total-score thresholds as src/evaluation/risk_labeling.py
    (>=9 or explicit risk pattern -> high; >=6 -> mid; else -> low)
  - IMPORTANT DEVIATION FROM SINGLE-TURN PIPELINE: the single-turn dataset's
    has_meaningful_risk() runs on a pre-summarized `risk_assessment` field
    that does not exist in this raw data. Here, the same regex patterns are
    applied instead to the concatenated raw user messages in the session.
    This is a deliberate adaptation, not a silent substitution -- flag this
    in the paper/methods section if the multi-turn risk distribution is
    reported alongside the single-turn one.

De-identification:
  - user_id and session_id are replaced with a stable SHA-256-derived hash
    (same raw ID always maps to the same hash, but the original ID cannot
    be recovered from the hash alone without the salt).
  - Set MTD_SALT as an environment variable before running, or edit SALT
    below. Keep the salt private -- do not commit it to git.

Output:
  - One JSON object per line (JSONL), each representing one filtered,
    de-identified, risk-labeled session.
"""

import json
import os
import re
import hashlib
from datetime import datetime

# ======================
# Configuration
# ======================

INPUT_PATH = "data/all_data.jsonl"
OUTPUT_PATH = "data/multiturn_cleaned.jsonl"
MIN_USER_EXCHANGES = 4  # matches the scoping decision: 4+ exchanges

# Set this via: export MTD_SALT="your-private-salt-string"
# Do NOT commit the salt to git. If not set, a default placeholder is used
# and a warning is printed -- replace it before running on real data.
SALT = os.environ.get("MTD_SALT", "CHANGE-ME-BEFORE-RUNNING")


# ======================
# Risk labeling (mirrors src/evaluation/risk_labeling.py)
# ======================

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
    if not text:
        return False
    text = str(text).lower().strip()
    if not text:
        return False
    for pattern in RISK_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def label_risk(total_score: int, concatenated_user_text: str) -> str:
    """
    Session-level risk label. Same total_score thresholds as the
    single-turn pipeline; risk-pattern detection runs on concatenated
    raw user turns instead of a risk_assessment summary field (see
    module docstring).
    """
    risk_flag = has_meaningful_risk(concatenated_user_text)

    if risk_flag or total_score >= 9:
        return "high"
    elif total_score >= 6:
        return "mid"
    else:
        return "low"


# ======================
# De-identification
# ======================

def anonymize_id(raw_id: str) -> str:
    if not raw_id:
        return ""
    return hashlib.sha256(f"{SALT}:{raw_id}".encode("utf-8")).hexdigest()[:16]


# ======================
# Main processing
# ======================

def process_session(user_id_raw: str, session: dict) -> dict | None:
    phq = session.get("phq")
    if not phq or not phq.get("is_completed"):
        return None

    turns = session.get("turns", [])
    user_msgs = [
        t for t in turns
        if t.get("is_bot") == 0 and t.get("message", "").strip() != ""
    ]

    if len(user_msgs) < MIN_USER_EXCHANGES:
        return None

    total_score = phq.get("total_score", 0)
    concatenated_user_text = " ".join(t.get("message", "") for t in user_msgs)
    risk_label = label_risk(total_score, concatenated_user_text)

    anon_user_id = anonymize_id(user_id_raw)
    anon_session_id = anonymize_id(session.get("id", ""))

    clean_turns = []
    for t in turns:
        msg = t.get("message", "")
        if not msg.strip():
            continue  # drop empty session-init phantom turns
        clean_turns.append({
            "is_bot": t.get("is_bot"),
            "message": msg,
            "timestamp": t.get("timestamp"),
        })

    return {
        "anon_user_id": anon_user_id,
        "anon_session_id": anon_session_id,
        "started_at": session.get("started_at"),
        "phq_total_score": total_score,
        "phq_scores": [
            {"question_index": s.get("question_index"), "score": s.get("score")}
            for s in phq.get("scores", [])
        ],
        "risk_label": risk_label,
        "n_user_exchanges": len(user_msgs),
        "n_total_turns": len(clean_turns),
        "turns": clean_turns,
    }


def main():
    if SALT == "CHANGE-ME-BEFORE-RUNNING":
        print("WARNING: using default placeholder salt. Set MTD_SALT env var "
              "before running on real data:\n"
              "  export MTD_SALT=\"your-private-salt-string\"\n")

    n_input_sessions = 0
    n_output_sessions = 0
    risk_counts = {"low": 0, "mid": 0, "high": 0}

    with open(INPUT_PATH, "r", encoding="utf-8") as f_in, \
         open(OUTPUT_PATH, "w", encoding="utf-8") as f_out:

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            user = json.loads(line)
            user_id_raw = user.get("user_id", "")

            for session in user.get("sessions", []):
                n_input_sessions += 1
                cleaned = process_session(user_id_raw, session)
                if cleaned is None:
                    continue

                f_out.write(json.dumps(cleaned, ensure_ascii=False) + "\n")
                n_output_sessions += 1
                risk_counts[cleaned["risk_label"]] += 1

    print(f"Input sessions scanned:  {n_input_sessions}")
    print(f"Output sessions kept:    {n_output_sessions} "
          f"(filter: is_completed=True, >={MIN_USER_EXCHANGES} user exchanges)")
    print(f"Risk label distribution:")
    for label, count in risk_counts.items():
        pct = 100 * count / n_output_sessions if n_output_sessions else 0
        print(f"  {label}: {count} ({pct:.1f}%)")
    print(f"\nOutput written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()