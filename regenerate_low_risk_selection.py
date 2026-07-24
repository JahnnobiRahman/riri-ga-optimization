"""
regenerate_low_risk_selection.py

Regenerates the low-risk conversation selection with a different
random draw than the original packet (which surfaced a conversation
containing content outside the system's designed scope -- witnessed
sexual content causing user distress, which no existing keyword list
or risk-labeling mechanism is built to detect, since the system was
designed and evaluated specifically for depression/suicide-risk
signals per PHQ-4).

This does NOT attempt to automatically filter for this category of
content -- that's the whole problem, there's no reliable keyword-based
way to catch it. Instead, this prints the new candidates in full for
YOU to personally read and approve before they go into the final
packet. Do not skip this review step.

Run from repo root with: PYTHONPATH=src python3 regenerate_low_risk_selection.py
"""

import json
import random

from ga.genome import Genome
from ga.runner_multiturn import load_sessions, split_sessions
from generation.conversation_generator import generate_conversation_responses

SEED = 7
DATA_PATH = "data/multiturn_cleaned.jsonl"
B4_GENOME_PATH = "experiments/multiturn_p100_seed7_v2split_best_genome.json"

# Different seed specifically for the low-risk re-draw, to get a
# genuinely different set of 3 sessions than the original selection.
LOW_RISK_RESEED = 42

N_LOW = 3


def get_zeroshot_genome() -> Genome:
    g = Genome(
        p_id=0, w_s=0.10, w_e=0.10, w_c=0.10,
        memory_window=256, theta_mid=0.70, theta_high=0.95,
        gamma=0.0, history_turns=4,
    )
    g.normalize()
    return g


def format_conversation_pair(idx, session, b1_genome, b4_genome):
    user_turns = session["turns"]
    b1_log = generate_conversation_responses(user_turns, "low", b1_genome)
    b4_log = generate_conversation_responses(user_turns, "low", b4_genome)

    lines = [f"## Conversation 1 (CANDIDATE {idx}) (risk=low, {len(user_turns)} user turns)\n"]
    lines.append("### B1 (Zero-shot)\n")
    for i, turn in enumerate(b1_log):
        lines.append(f"**Turn {i} (User):** {turn['user_message']}\n")
        lines.append(f"**Turn {i} (B1 Bot):** {turn['bot_response']}\n")
    lines.append("\n### B4 (GA-Optimised)\n")
    for i, turn in enumerate(b4_log):
        lines.append(f"**Turn {i} (User):** {turn['user_message']}\n")
        lines.append(f"**Turn {i} (B4 Bot):** {turn['bot_response']}\n")
    lines.append("\n---\n")
    return "\n".join(lines)


def main():
    print("Loading and splitting sessions...")
    all_sessions = load_sessions(DATA_PATH)
    _, val_sessions = split_sessions(all_sessions, seed=SEED)

    with open(B4_GENOME_PATH) as f:
        b4_genome = Genome(**json.load(f))
    b1_genome = get_zeroshot_genome()

    low_risk_sessions = [s for s in val_sessions if s["risk_label"] == "low"]

    # Draw MORE than N_LOW candidates so you have options to choose from,
    # not just 3 forced picks -- pulling 6 candidates for review.
    rnd = random.Random(LOW_RISK_RESEED)
    shuffled = low_risk_sessions.copy()
    rnd.shuffle(shuffled)
    candidates = shuffled[:6]

    print(f"Generated {len(candidates)} low-risk candidates for manual review.\n")
    print("READ EACH ONE BEFORE APPROVING. This script does not filter for "
          "content outside the system's designed scope -- that's on you to check.\n")

    output_lines = ["# Low-Risk Conversation Candidates (for manual review)\n"]
    for idx, session in enumerate(candidates, 1):
        output_lines.append(format_conversation_pair(idx, session, b1_genome, b4_genome))

    output_path = "experiments/human_eval_multiturn/low_risk_candidates_for_review.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Saved {len(candidates)} candidates to {output_path}")
    print("Read this file, pick 3 you're comfortable with, and let me know "
          "which ones (by candidate number) to splice into the final packet.")


if __name__ == "__main__":
    main()