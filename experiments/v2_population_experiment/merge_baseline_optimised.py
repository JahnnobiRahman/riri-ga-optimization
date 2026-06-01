import pandas as pd
from pathlib import Path


def main():
    base = Path(__file__).resolve().parent

    baseline_df = pd.read_csv(base / "baseline_responses.csv")
    optimized_df = pd.read_csv(base / "trace_analysis.csv")

    if "final_response" in optimized_df.columns:
        resp_col = "final_response"
    elif "response" in optimized_df.columns:
        resp_col = "response"
    else:
        raise ValueError(
            "trace_analysis.csv needs 'final_response' or 'response'. "
            f"Got: {list(optimized_df.columns)}"
        )

    optimized_subset = optimized_df[
        [
            "risk_label",
            "user_prompt_full",
            resp_col,
        ]
    ].copy()

    optimized_subset.columns = [
        "risk_label",
        "user_prompt",
        "optimized_response",
    ]

    merged = pd.merge(
        baseline_df,
        optimized_subset,
        on=["risk_label", "user_prompt"],
        how="inner",
    )

    out_path = base / "baseline_vs_optimized.csv"
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Saved: {out_path}")
    print(merged.head())


if __name__ == "__main__":
    main()
