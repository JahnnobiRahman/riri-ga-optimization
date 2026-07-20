"""
gamma_effect_size_analysis.py

Tests whether gamma meaningfully changes escalation decisions across
the real multi-turn dataset, or is close to functionally inert -- i.e.
whether the P100 run's gamma-near-ceiling finding reflects genuine
optimization pressure, or genetic drift on a near-fitness-neutral gene.

Method: sweep gamma across its full range [0.0, 0.05, 0.10, 0.15, 0.20]
on ALL mid-risk sessions in the dataset, holding tau_h=0.65 fixed, and
count how many turns' escalation decision (crossed vs not crossed)
actually flips as gamma increases from 0.0. Cheap to run at full scale
since this only needs the distress trajectory (compute_distress_score
+ decay recurrence), not full response generation.

Run from repo root with: PYTHONPATH=src python3 gamma_effect_size_analysis.py
"""

import json

from evaluation.conversation_distress import compute_conversation_distress

DATA_PATH = "data/multiturn_cleaned.jsonl"
TAU_H = 0.65
GAMMA_VALUES = [0.0, 0.05, 0.10, 0.15, 0.20]


def load_mid_risk_sessions(path: str):
    sessions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            session = json.loads(line)
            if session["risk_label"] != "mid":
                continue
            user_turns = [t["message"] for t in session["turns"] if t.get("is_bot") == 0]
            if user_turns:
                sessions.append(user_turns)
    return sessions


def would_escalate(h_t: float, gamma: float) -> bool:
    effective_threshold = TAU_H - (gamma * h_t)
    return h_t > effective_threshold


def main():
    print("Loading mid-risk sessions...")
    sessions = load_mid_risk_sessions(DATA_PATH)
    print(f"Loaded {len(sessions)} mid-risk sessions.\n")

    # Compute each session's distress trajectory ONCE (gamma doesn't
    # affect the trajectory itself, only the escalation decision), then
    # reuse it for every gamma value tested -- avoids redundant
    # recomputation of compute_distress_score across the sweep.
    print("Computing distress trajectories (once per session)...")
    trajectories = [compute_conversation_distress(turns) for turns in sessions]
    total_turns = sum(len(t) for t in trajectories)
    print(f"Total scored turns across all sessions: {total_turns}\n")

    baseline_gamma = 0.0
    baseline_decisions = []
    for traj in trajectories:
        baseline_decisions.append([would_escalate(h, baseline_gamma) for h in traj])

    print(f"{'gamma':>8} | {'turns escalating':>18} | {'flipped vs gamma=0':>20} | {'% of all turns':>15}")
    print("-" * 70)

    for gamma in GAMMA_VALUES:
        n_escalating = 0
        n_flipped = 0

        for traj, baseline in zip(trajectories, baseline_decisions):
            for h_t, base_decision in zip(traj, baseline):
                decision = would_escalate(h_t, gamma)
                if decision:
                    n_escalating += 1
                if decision != base_decision:
                    n_flipped += 1

        pct_flipped = 100 * n_flipped / total_turns
        print(f"{gamma:>8.2f} | {n_escalating:>18} | {n_flipped:>20} | {pct_flipped:>14.3f}%")

    print(f"\nIf 'flipped vs gamma=0' stays small even at gamma=0.20 (the "
          f"observed ceiling), that supports the genetic-drift hypothesis: "
          f"gamma has limited practical effect on real escalation outcomes, "
          f"so the GA has little to no selection pressure pushing it away "
          f"from its ceiling once it drifts there.")


if __name__ == "__main__":
    main()