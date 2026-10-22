"""
Check how many of the 422 self-reported age-13-17 records fall specifically
in the 575-prompt validation set, using the EXACT same filtering and split
logic as baseline_comparison.py.

This version replicates the exact data loading/filtering pipeline to ensure
we're checking the real N=2872 dataset, not the raw N=3279.
"""

import pandas as pd
from sys import exit as sys_exit

# --- Use EXACT same logic as baseline_comparison.py ---
DATA_PATH = "data/phq4_cleaned.csv"
SEED = 7

print("Loading raw dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Raw records loaded: {len(df)}")

# Replicate baseline_comparison.py data loading (lines 60-79)
for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in df.columns:
        df[col] = ""

if "total_score" not in df.columns:
    df["total_score"] = 0

for col in ["common_themes", "thought_progression", "risk_assessment"]:
    df[col] = df[col].fillna("")
df["total_score"] = df["total_score"].fillna(0)

# Build user_prompt (same as baseline_comparison.py)
df["user_prompt"] = (
    df["common_themes"].astype(str).str.strip()
    + " | "
    + df["thought_progression"].astype(str).str.strip()
).str.strip(" |")

# CRITICAL FILTER: remove rows with empty user_prompt (line 79 of baseline_comparison.py)
df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)

print(f"Filtered records (non-empty prompts): {len(df)}")

# Safety check: must be exactly 2872
if len(df) != 2872:
    print(f"\n*** ERROR: Expected exactly 2872 filtered records, got {len(df)} ***")
    print("The filtering logic doesn't match baseline_comparison.py")
    sys_exit(1)

print("✓ Dataset size matches expected N=2872")

# Count minors in filtered dataset
# Check if age_group exists, otherwise fall back to age
if "age_group" in df.columns:
    minors_mask = df["age_group"] == "13-17"
    age_col = "age_group"
elif "age" in df.columns:
    minors_mask = (df["age"] >= 13) & (df["age"] <= 17)
    age_col = "age"
else:
    print("\n*** ERROR: No 'age_group' or 'age' column found ***")
    sys_exit(1)

total_minors = minors_mask.sum()
print(f"\nTotal minors (13-17) in filtered dataset: {total_minors}")
print(f"Paper reports: 422")
print(f"Match: {'YES ✓' if total_minors == 422 else f'NO - difference of {total_minors - 422:+d}'}")

# --- Reproduce EXACT same shuffle + 80/20 split as baseline_comparison.py (line 82-85) ---
df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
split_idx = int(0.8 * len(df))
train_df = df.iloc[:split_idx].reset_index(drop=True)
val_df = df.iloc[split_idx:].reset_index(drop=True)

print(f"\n{'='*70}")
print("SPLIT VERIFICATION")
print(f"{'='*70}")
print(f"Train set: {len(train_df)} records (expected: 2297)")
print(f"Validation set: {len(val_df)} records (expected: 575)")

if len(val_df) != 575:
    print(f"\n*** WARNING: Validation set size is {len(val_df)}, expected 575 ***")

# Count minors in each split (recompute mask on split dataframes)
if "age_group" in train_df.columns:
    train_minors = (train_df["age_group"] == "13-17").sum()
    val_minors = (val_df["age_group"] == "13-17").sum()
else:
    train_minors = ((train_df["age"] >= 13) & (train_df["age"] <= 17)).sum()
    val_minors = ((val_df["age"] >= 13) & (val_df["age"] <= 17)).sum()

print(f"\n{'='*70}")
print("MINORS (AGE 13-17) DISTRIBUTION")
print(f"{'='*70}")
print(f"Minors in TRAINING set: {train_minors}")
print(f"Minors in VALIDATION set: {val_minors}")
print(f"Total: {train_minors + val_minors}")

print(f"\n{'='*70}")
print("KEY RESULTS")
print(f"{'='*70}")
print(f"Validation minors as % of validation set: {val_minors/len(val_df)*100:.1f}%")
print(f"Validation minors as % of all minors: {val_minors/total_minors*100:.1f}%")

# Expected if evenly distributed
expected_val = total_minors * 0.2
print(f"\nExpected in validation if evenly split (20%): {expected_val:.1f}")
print(f"Actual: {val_minors}")
print(f"Difference: {val_minors - expected_val:+.1f}")

print(f"\n{'='*70}")
print("INTERPRETATION")
print(f"{'='*70}")
if val_minors < 30:
    print("⇒ LOW exposure: Few minors in validation set")
    print("  Headline results minimally affected by minor-exclusion question")
elif val_minors > 70:
    print("⇒ HIGH exposure: Many minors in validation set")
    print("  Headline results substantially affected by minor-exclusion question")
else:
    print("⇒ MODERATE exposure: Some minors in validation set")
    print("  Headline results moderately affected by minor-exclusion question")
