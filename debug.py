import pandas as pd

df = pd.read_csv("experiments/v2_population_experiment/trace_analysis.csv")

sample = df.sample(10)

with open("debug_sample_with_input.txt", "w", encoding="utf-8") as f:
    f.write("User Prompt vs Response\n")
    f.write("="*60 + "\n\n")

    for _, row in sample.iterrows():

        
        f.write("USER:\n")
        f.write(row["user_prompt_full"] + "\n\n")

        print("\n---")
        print("RISK:", row["risk_label"])

        f.write("RESPONSE:\n")
        f.write(row["final_response"] + "\n")

        f.write("\n" + "-"*60 + "\n\n")

print("Saved to debug_sample_with_input.txt")
sample.to_csv("debug_sample.csv", index=False)