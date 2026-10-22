"""
Check how many of the 422 self-reported age-13-17 records fall specifically
in the 575-prompt validation set (as opposed to the training/optimization
set), using the same split logic as the rest of the pipeline.
"""

import pandas as pd

# --- Data loading ---
DATA_PATH = "data/phq4_cleaned.csv"
AGE_COLUMN = "age_group"  # based on CSV header inspection
SEED = 7

df = pd.read_csv(DATA_PATH)
print(f"Total records loaded: {len(df)}")

# First, let's see what age_group values exist
print(f"\nAge group distribution:")
print(df[AGE_COLUMN].value_counts().sort_index())

# Check if it's a string like "13-17" or numeric
# If it's "13-17" string, we'll filter by that
# If numeric, we'll use the range check
sample_value = df[AGE_COLUMN].iloc[0]
print(f"\nSample age_group value: {sample_value} (type: {type(sample_value)})")

# Determine the 422 minors based on the data format
if isinstance(sample_value, str) or df[AGE_COLUMN].dtype == 'object':
    # Likely categorical like "13-17"
    minors_mask = df[AGE_COLUMN].isin(["13-17", "13-18"])  # try both common ranges
    print(f"\nUsing categorical filter for minors")
else:
    # Numeric age values
    minors_mask = (df[AGE_COLUMN] >= 13) & (df[AGE_COLUMN] <= 17)
    print(f"\nUsing numeric range filter for minors")

minors_count = minors_mask.sum()
print(f"\nSelf-reported minors: {minors_count} records")
print(f"Paper reports: 422 records")
print(f"Match: {'YES' if minors_count == 422 else 'NO - check filter logic'}")

# --- Reproduce the same shuffle + 80/20 split used in baseline_comparison.py ---
df_shuffled = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
split_idx = int(0.8 * len(df_shuffled))
train_df = df_shuffled.iloc[:split_idx]
val_df = df_shuffled.iloc[split_idx:]

print(f"\n{'='*70}")
print(f"SPLIT SIZES")
print(f"{'='*70}")
print(f"Train set size: {len(train_df)}")
print(f"Validation set size: {len(val_df)}")

# Count minors in each split
if isinstance(sample_value, str) or df[AGE_COLUMN].dtype == 'object':
    train_minors = train_df[AGE_COLUMN].isin(["13-17", "13-18"]).sum()
    val_minors = val_df[AGE_COLUMN].isin(["13-17", "13-18"]).sum()
else:
    train_minors = ((train_df[AGE_COLUMN] >= 13) & (train_df[AGE_COLUMN] <= 17)).sum()
    val_minors = ((val_df[AGE_COLUMN] >= 13) & (val_df[AGE_COLUMN] <= 17)).sum()

print(f"\n{'='*70}")
print(f"MINORS (AGE 13-17) DISTRIBUTION")
print(f"{'='*70}")
print(f"Minors in TRAINING set: {train_minors}")
print(f"Minors in VALIDATION set: {val_minors}")
print(f"Total minors: {train_minors + val_minors}")
print(f"\nValidation set minors as % of validation set: {val_minors/len(val_df)*100:.1f}%")
print(f"Validation set minors as % of all {minors_count}: {val_minors/minors_count*100:.1f}%")

# Expected if evenly distributed
expected_val = minors_count * 0.2
print(f"\nExpected in validation if evenly distributed (20%): {expected_val:.1f}")
print(f"Actual: {val_minors}")
print(f"Difference: {val_minors - expected_val:+.1f}")
