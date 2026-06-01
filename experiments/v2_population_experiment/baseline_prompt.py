import pandas as pd
from pathlib import Path


# =========================
# Baseline Response Generator
# =========================
# B1 baseline:
# - no GA optimization
# - weak structure
# - minimal empathy
# - conservative/simple response
# - intentionally less complete than optimized system


def detect_risk_from_text(text, risk_label=None):
    """
    Uses existing risk_label if available.
    Otherwise detects risk heuristically from text.
    """
    if risk_label in ["low", "mid", "high"]:
        return risk_label

    text = str(text).lower()

    high_markers = [
        "don't want to live",
        "dont want to live",
        "আর বাঁচতে চাই না",
        "bachte chai na",
        "suicide",
        "kill myself",
        "harm myself",
        "i need help immediately",
        "unsafe",
    ]

    mid_markers = [
        "scared",
        "overwhelmed",
        "nothing feels good",
        "pressure",
        "anxious",
        "panic",
        "ভালো লাগছে না",
        "matha kaj korche na",
        "মাথা কাজ করছে না",
    ]

    if any(m in text for m in high_markers):
        return "high"

    if any(m in text for m in mid_markers):
        return "mid"

    return "low"


def generate_baseline_response(user_prompt, risk_label=None):
    """
    B1 Zero-shot baseline response.
    This represents unoptimized/simple generation.
    It is intentionally generic and structurally weak,
    so it can be compared against GA-optimized responses.
    """

    risk = detect_risk_from_text(user_prompt, risk_label)

    if risk == "high":
        return (
            "I am sorry you are feeling this way. "
            "Please try to stay calm and talk to someone you trust."
        )

    if risk == "mid":
        return (
            "That sounds difficult. "
            "Try to take a deep breath and talk to someone if you can."
        )

    return (
        "I understand. "
        "Try to take things slowly and take care of yourself."
    )


def build_baseline_file(
    input_csv="trace_analysis.csv",
    output_csv="baseline_responses.csv",
    user_prompt_col="user_prompt_full",
    risk_col="risk_label",
    base_dir: Path | None = None,
):
    """
    Reads trace_analysis.csv and creates baseline responses
    for the same prompts used in optimized evaluation.
    """

    base = base_dir if base_dir is not None else Path(__file__).resolve().parent
    input_path = Path(input_csv)
    if not input_path.is_absolute():
        input_path = base / input_path
    output_path = Path(output_csv)
    if not output_path.is_absolute():
        output_path = base / output_path

    if not input_path.exists():
        raise FileNotFoundError(f"Could not find input file: {input_path}")

    df = pd.read_csv(input_path)

    if user_prompt_col not in df.columns:
        raise ValueError(
            f"Column '{user_prompt_col}' not found. Available columns: {list(df.columns)}"
        )

    rows = []

    for _, row in df.iterrows():
        user_prompt = row.get(user_prompt_col, "")
        risk_label = row.get(risk_col, None)

        baseline_response = generate_baseline_response(user_prompt, risk_label)

        rows.append({
            "risk_label": risk_label,
            "user_prompt": user_prompt,
            "baseline_response": baseline_response,
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved baseline responses to: {output_path}")
    print(f"Total rows: {len(out_df)}")


if __name__ == "__main__":
    build_baseline_file(
        input_csv="trace_analysis.csv",
        output_csv="baseline_responses.csv",
        user_prompt_col="user_prompt_full",
        risk_col="risk_label",
    )