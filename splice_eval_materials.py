"""
splice_eval_materials.py

Replaces the low-risk section (original Conversations 1-3) in your
existing eval_materials.md with the corrected, vetted version, while
keeping Conversations 4-16 (mid/high-risk) completely untouched.

Run from repo root with: python3 splice_eval_materials.py
"""

ORIGINAL_PATH = "experiments/human_eval_multiturn/eval_materials.md"
NEW_LOW_RISK_PATH = "eval_materials_final_low_risk_section.md"  # the file I gave you
OUTPUT_PATH = "experiments/human_eval_multiturn/eval_materials_FINAL.md"

with open(ORIGINAL_PATH, "r", encoding="utf-8") as f:
    original = f.read()

with open(NEW_LOW_RISK_PATH, "r", encoding="utf-8") as f:
    new_low_risk = f.read()

# Find where Conversation 4 starts in the original -- everything from
# there onward (mid/high-risk) is kept unchanged.
marker = "## Conversation 4 (risk=mid, 14 user turns)"
idx = original.find(marker)

if idx == -1:
    raise RuntimeError(
        f"Could not find '{marker}' in {ORIGINAL_PATH}. "
        "Check the file wasn't already modified, or that the marker text matches exactly."
    )

rest_of_file = original[idx:]

# Build final output: header + new low-risk section + everything from Conversation 4 onward
header = "# Multi-Turn Human Evaluation Materials (FINAL)\n\n"
final_content = header + new_low_risk + "\n" + rest_of_file

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(final_content)

print(f"Spliced file written to {OUTPUT_PATH}")
print("Verify: open it and check Conversation 1 is the 'subscribe to relaxy premium' "
      "one (not the flagged content), and Conversation 4 still starts with "
      "'দুঃখিত আগে থেরাপি নেই আমি'.")