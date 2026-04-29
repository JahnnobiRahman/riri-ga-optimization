import pandas as pd
from generation.response_generator import assemble_prompt_trace
from evaluation.scoring import score_empathy, score_safety, score_structure, length_penalty


def export_traces(genome, data, output_path, n=100):

    rows = []

    sample = data.sample(n=min(n, len(data)), random_state=42).reset_index(drop=True)

    for _, row in sample.iterrows():

        trace = assemble_prompt_trace(
            row["user_prompt"],
            row["risk_label"],
            genome
        )

        resp = trace["final_response"]

        rows.append({
            "user_prompt": row["user_prompt"],
            "risk_label": row["risk_label"],

            "template": trace["template"],
            "safety_level": trace["safety_level"],
            "empathy_level": trace["empathy_level"],
            "structure_level": trace["structure_level"],
            "escalate": trace["escalate"],

            "num_empathy_lines": len(trace["empathy"]),
            "has_grounding": trace["grounding"] is not None,
            "has_action": trace["action"] is not None,
            "has_question": trace["question"] is not None,

            "empathy_score": score_empathy(resp),
            "safety_score": score_safety(resp, row["risk_label"]),
            "structure_score": score_structure(resp),
            "length_penalty": length_penalty(resp),

            "final_response": resp
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

    print(f"Saved trace file to: {output_path}")