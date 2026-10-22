"""
Simple check for minors in validation set - no heavy imports
"""

import pandas as pd

# Load data
df = pd.read_csv("data/phq4_cleaned.csv")
print(f"Total records: {len(df)}")

# Check age_group format
print(f"\nAge group distribution:")
print(df['age_group'].value_counts().sort_index())

# Count minors (13-17 or similar)
# Based on typical formats, try both string and numeric
minors_mask = df['age_group'].astype(str).str.contains('13')
minors_count = minors_mask.sum()
print(f"\nRecords with '13' in age_group: {minors_count}")

# Also try exact matches
exact_minors = df['age_group'].isin(['13-17', '13-18', '13_17', '13_18'])
print(f"Records with exact '13-17' or '13-18' match: {exact_minors.sum()}")

# Use the one that gives us 422
if exact_minors.sum() == 422:
    print("\nUsing exact match filter")
    minors_mask = exact_minors
elif minors_count == 422:
    print("\nUsing contains filter")
else:
    print(f"\nWARNING: Neither filter gives 422 (expected from paper)")

minors_count = minors_mask.sum()

# Shuffle and split - SEED=7
SEED = 7
df_shuffled = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
split_idx = int(0.8 * len(df_shuffled))
val_df = df_shuffled.iloc[split_idx:]

print(f"\n{'='*70}")
print("VALIDATION SET")
print(f"{'='*70}")
print(f"Size: {len(val_df)}")

# Count minors in validation
val_minors = minors_mask[val_df.index].sum()

print(f"\n{'='*70}")
print("RESULT")
print(f"{'='*70}")
print(f"Total minors (13-17) in dataset: {minors_count}")
print(f"Minors in VALIDATION set: {val_minors}")
print(f"Minors in TRAINING set: {minors_count - val_minors}")
print(f"\nValidation minors as % of all minors: {val_minors/minors_count*100:.1f}%")
print(f"Expected if evenly split (20%): ~{minors_count*0.2:.0f}")
