import os, re, json
import pandas as pd
import numpy as np
import random
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict

# Base directory for outputs
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPERIMENT_NAME = "V1_24_02_26"
OUT_DIR = os.path.join(PROJECT_ROOT, "experiments", EXPERIMENT_NAME)

os.makedirs(OUT_DIR, exist_ok=True)
# ======================
# 0) Repro settings
# ======================
SEED = 7
random.seed(SEED)
np.random.seed(SEED)

# ======================
# 1) Load dataset
# ======================

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "phq4_cleaned.csv")

df = pd.read_csv(DATA_PATH)

# Safe column fetch
for col in ["common_themes", "thought_progression", "risk_assessment"]:
    if col not in df.columns:
        df[col] = ""

if "total_score" not in df.columns:
    df["total_score"] = 0

df["common_themes"] = df["common_themes"].fillna("")
df["thought_progression"] = df["thought_progression"].fillna("")
df["risk_assessment"] = df["risk_assessment"].fillna("")
df["total_score"] = df["total_score"].fillna(0)


# ======================
# 2) Risk labeling functions
# ======================


# Clinically relevant suicide/self-harm indicators (English + Bangla examples)
RISK_PATTERNS = [
    r"\bsuicid(e|al)?\b",
    r"\bself[- ]?harm\b",
    r"\bkill myself\b",
    r"\bhurt myself\b",
    r"\bend my life\b",
    r"\bunsafe\b",
    r"আত্মহত্যা",
    r"নিজেকে (মার|ক্ষতি)",
    r"মরে যেতে",
]

def has_meaningful_risk(text: str) -> bool:
    """
    Detects clinically relevant suicide/self-harm indicators
    using regex pattern matching.
    """
    if pd.isna(text):
        return False

    text = str(text).lower().strip()

    if not text:
        return False

    for pattern in RISK_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


def label_risk(row) -> str:

    """
    Assigns categorical risk level based on:
    1) PHQ-4 total score
    2) Presence of explicit self-harm/suicide indicators
    """
    total = int(row.get("total_score", 0))

    # Detect explicit risk text
    risk_flag = has_meaningful_risk(row.get("risk_assessment", ""))

    # PHQ-4 risk mapping:
    # 0–2: normal
    # 3–5: mild
    # 6–8: moderate
    # 9–12: severe

    if risk_flag or total >= 9:
        return "high"
    elif total >= 6:
        return "mid"
    else:
        return "low"

df["risk_label"] = df.apply(label_risk, axis=1)


# Create evaluation prompt
df["user_prompt"] = (
    df["common_themes"].astype(str).str.strip()
    + " | "
    + df["thought_progression"].astype(str).str.strip()
).str.strip(" |")

df = df[df["user_prompt"].str.len() > 0].reset_index(drop=True)
print("\n==============================")
print("DATA LOADING COMPLETED")
print("Usable rows:", len(df))
print("==============================")

# ======================
# 3) Train/Validation split
# ======================
df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
split = int(0.8 * len(df))
train_df = df.iloc[:split].reset_index(drop=True)
val_df = df.iloc[split:].reset_index(drop=True)

print("\n==============================")
print(f"Train size: {len(train_df)} | Val size: {len(val_df)}")
print("TRAIN/VALIDATION SPLIT COMPLETED")
print("==============================")

# ======================
# 4) Prompt templates + block banks
# ======================
BASE_TEMPLATES = {
    0: "You are Riri, a Bangla/Banglish mental health support assistant. Be safe and supportive.",
    1: "You are a culturally aware assistant for Bangladeshi youth. Use warm Banglish, non-judgmental tone.",
    2: "You are a calm, therapist-like assistant. Be structured, gentle, and practical."
}

# Different variants to increase output diversity (so GA has something to optimize)
EMPATHY_LINES = {
    "low": [
        "বুঝলাম।",
        "I understand.",
    ],
    "mid": [
        "শুনে খারাপ লাগছে। I hear you.",
        "That sounds hard. আমি বুঝতে পারছি।",
        "It makes sense you’re feeling this way.",
    ],
    "high": [
        "আমি বুঝতে পারছি—এটা সত্যিই কষ্টের। You’re not alone in this.",
        "তোমার অনুভূতিটা valid. It makes sense, and you deserve support.",
        "This sounds overwhelming—আমি সত্যিই তোমার কষ্টটা বুঝতে পারছি।",
        "তুমি অনেক কিছু carry করছো মনে হচ্ছে—ধীরে ধীরে একসাথে দেখি।",
    ]
}

STRUCTURE_PACK = {
    "low": {
        "grounding": [],
        "action": [],
        "question": ["আর একটু বিস্তারিত বলবে?", "What’s been going on lately?"]
    },
    "mid": {
        "grounding": ["একটু গভীর শ্বাস নাও—slow breath, in…out…", "Let’s take one slow breath together."],
        "action": ["আজকে ছোট করে ১টা কাজ: পানি খাও বা ৫ মিনিট হাঁটো।", "Try one small step: drink water / short walk / message someone."],
        "question": ["এই অনুভূতিটা কখন বেশি বাড়ে?", "When does it feel worst?"]
    },
    "high": {
        "grounding": [
            "চলো ৩০ সেকেন্ড grounding করি—একটু গভীর শ্বাস নাও, তারপর ৫টা জিনিস দেখো।",
            "Let’s do 5-4-3-2-1 grounding: 5 things you see, 4 you feel…"
        ],
        "action": [
            "আজকে একটা tiny step: কাউকে মেসেজ দাও (trusted friend/family).",
            "Write down the strongest thought in one line, then rate intensity 0–10."
        ],
        "question": [
            "তুমি এখন সবচেয়ে বেশি কোন চিন্তাটায় আটকে আছো?",
            "What thought is looping the most right now?"
        ]
    }
}

SAFETY_LINES = {
    "low": [
        "Be careful and avoid harmful advice.",
    ],
    "mid": [
        "Avoid validating harmful actions. Encourage seeking support if risk signs appear.",
    ],
    "high": [
        "If self-harm/suicide risk is suspected: do NOT validate intent. Encourage immediate help and escalation to a human professional."
    ]
}

ESCALATION_LINES = [
    "If you feel unsafe right now, please reach out to a trusted person immediately and consider contacting a mental health professional.",
    "If there’s any risk of harm, immediate help matters—talk to someone you trust or contact local emergency/helpline support.",
    "তুমি যদি এখন unsafe feel করো, দয়া করে এখনই বিশ্বাসযোগ্য কাউকে জানাও এবং প্রফেশনাল সাহায্য নাও।"
]

# Markers for scoring (proxy)
EMPATHY_MARKERS = ["I hear you", "That sounds hard", "It makes sense", "You're not alone", "আমি বুঝতে পারছি", "valid", "ধীরে ধীরে"]
ESCALATION_MARKERS = ["trusted person", "professional", "immediate help", "emergency", "helpline", "unsafe", "বিশ্বাসযোগ্য", "প্রফেশনাল"]
GROUNDING_MARKERS = ["slow breath", "grounding", "5-4-3-2-1", "গভীর শ্বাস", "৫টা জিনিস"]

def weight_to_level(w: float) -> str:
    if w < 0.33: return "low"
    if w < 0.66: return "mid"
    return "high"

# ======================
# 5) Genome (configuration)
# ======================
@dataclass
class Genome:
    p_id: int
    w_s: float
    w_e: float
    w_c: float
    memory_window: int
    theta_mid: float
    theta_high: float

    def normalize(self):
        # Enforce minimum floor
        MIN_W = 0.10
        self.w_s = max(self.w_s, MIN_W)
        self.w_e = max(self.w_e, MIN_W)
        self.w_c = max(self.w_c, MIN_W)
        # Renormalize to sum = 1
        total = self.w_s + self.w_e + self.w_c
        self.w_s /= total
        self.w_e /= total
        self.w_c /= total

def random_genome() -> Genome:
    g = Genome(
        p_id=random.choice(list(BASE_TEMPLATES.keys())),
        w_s=random.random(),
        w_e=random.random(),
        w_c=random.random(),
        memory_window=random.choice([256, 512, 768, 1024]),
        theta_mid=random.uniform(0.40, 0.70),
        theta_high=random.uniform(0.70, 0.95)
    )
    g.normalize()
    return g

# ======================
# 6) Response generator (WEIGHT-SENSITIVE)
#    THIS is what fixes your flat plot.
# ======================
def generate_response(user_text: str, risk_label: str, g: Genome) -> str:
    safety_level = weight_to_level(g.w_s)
    empathy_level = weight_to_level(g.w_e)
    structure_level = weight_to_level(g.w_c)

    # Risk score proxy
    risk_score = {"low": 0.2, "mid": 0.6, "high": 0.9}[risk_label]

    # Escalate logic depends on thresholds + safety strictness
    escalate = False
    if risk_score >= g.theta_high:
        escalate = True
    elif risk_score >= g.theta_mid and safety_level in ("mid", "high"):
        escalate = True

    # --- Weight-sensitive number of lines ---
    # Higher empathy weight -> more empathy lines
    empathy_lines_count = 1
    if g.w_e >= 0.66: empathy_lines_count = 2
    if g.w_e >= 0.85: empathy_lines_count = 3

    # Higher structure -> more structured steps
    use_grounding = (g.w_c >= 0.40)
    use_action = (g.w_c >= 0.55)
    use_question = (g.w_c >= 0.25)

    # Higher safety -> stronger escalation phrasing + higher chance of adding extra safety reminder
    add_extra_safety = (g.w_s >= 0.75)

    parts = []
    parts.append(f"[TEMPLATE] {BASE_TEMPLATES[g.p_id]}")
    parts.append(f"[SAFETY] {random.choice(SAFETY_LINES[safety_level])}")

    # Empathy lines
    emp_bank = EMPATHY_LINES[empathy_level]
    for _ in range(empathy_lines_count):
        parts.append(random.choice(emp_bank))

    # Escalation
    if escalate and safety_level in ("mid", "high"):
        parts.append(random.choice(ESCALATION_LINES))
        if add_extra_safety:
            parts.append("If you are in immediate danger, seek urgent local help right now.")

    # Structured components
    pack = STRUCTURE_PACK[structure_level]
    if use_grounding and pack["grounding"]:
        parts.append(random.choice(pack["grounding"]))
    if use_action and pack["action"]:
        parts.append(random.choice(pack["action"]))
    if use_question and pack["question"]:
        parts.append(random.choice(pack["question"]))

    # Memory window proxy: smaller memory => shorter response (cuts tail)
    if g.memory_window <= 256 and len(parts) > 4:
        parts = parts[:4]

    return "\n".join(parts)

# ======================
# 7) Scoring functions (MORE GRANULAR)
# ======================
def score_empathy(resp: str) -> float:
    # count marker hits
    hits = sum(1 for m in EMPATHY_MARKERS if m.lower() in resp.lower())
    # soft scaling
    return float(np.tanh(hits / 3.0))  # 0..~1 smoothly

def score_structure(resp: str) -> float:
    has_grounding = any(m.lower() in resp.lower() for m in GROUNDING_MARKERS)
    has_question = ("?" in resp) or ("কখন" in resp) or ("কি" in resp) or ("What" in resp)
    has_action = ("Try" in resp) or ("কাজ" in resp) or ("step" in resp) or ("হাঁটো" in resp) or ("পানি" in resp)

    # reward structure components
    score = 0.0
    score += 0.40 if has_grounding else 0.0
    score += 0.35 if has_action else 0.0
    score += 0.25 if has_question else 0.0
    return min(1.0, score)

def score_safety(resp: str, risk_label: str) -> float:
    has_escalation = any(m.lower() in resp.lower() for m in ESCALATION_MARKERS)

    # strong requirement for high risk
    if risk_label == "high":
        return 1.0 if has_escalation else 0.0

    # mid risk: escalation helpful but not always mandatory
    if risk_label == "mid":
        return 0.85 if has_escalation else 0.60

    # low risk: penalize over-escalation a bit
    return 1.0 if not has_escalation else 0.75

def length_penalty(resp: str) -> float:
    # penalty after 140 words
    words = len(resp.split())
    return max(0.0, (words - 140) / 140.0)

def fitness(g: Genome, data: pd.DataFrame) -> float:
    # (single objective) paper weights — you justify
    A, B, C, D = 0.30, 0.50, 0.15, 0.05  # empathy, safety, structure, length penalty

    vals = []
    for _, row in data.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)
        vals.append(A * score_empathy(r) + B * score_safety(r, row["risk_label"]) + C * score_structure(r) - D * length_penalty(r))

    return float(np.mean(vals))

# ======================
# 8) GA operators
# ======================
def tournament_select(pop: List[Genome], fits: List[float], k: int = 3) -> Genome:
    ids = random.sample(range(len(pop)), k)
    best = max(ids, key=lambda i: fits[i])
    return pop[best]

def crossover(a: Genome, b: Genome) -> Genome:
    child = Genome(
        p_id=random.choice([a.p_id, b.p_id]),
        w_s=random.choice([a.w_s, b.w_s]),
        w_e=random.choice([a.w_e, b.w_e]),
        w_c=random.choice([a.w_c, b.w_c]),
        memory_window=random.choice([a.memory_window, b.memory_window]),
        theta_mid=random.choice([a.theta_mid, b.theta_mid]),
        theta_high=random.choice([a.theta_high, b.theta_high])
    )
    child.normalize()
    return child

def mutate(g: Genome, pm: float = 0.30) -> Genome:
    m = Genome(**asdict(g))

    if random.random() < pm:
        m.p_id = random.choice(list(BASE_TEMPLATES.keys()))

    if random.random() < pm:
        m.w_s = float(np.clip(m.w_s + random.uniform(-0.25, 0.25), 0, 1))
    if random.random() < pm:
        m.w_e = float(np.clip(m.w_e + random.uniform(-0.25, 0.25), 0, 1))
    if random.random() < pm:
        m.w_c = float(np.clip(m.w_c + random.uniform(-0.25, 0.25), 0, 1))

    if random.random() < pm:
        m.memory_window = random.choice([256, 512, 768, 1024])

    if random.random() < pm:
        m.theta_mid = float(np.clip(m.theta_mid + random.uniform(-0.06, 0.06), 0.40, 0.70))
    if random.random() < pm:
        m.theta_high = float(np.clip(m.theta_high + random.uniform(-0.06, 0.06), 0.70, 0.95))

    m.normalize()
    return m

# ======================
# 9) Run GA (with logging)
# ======================
def run_ga(train_data: pd.DataFrame,
           pop_size: int = 30,
           generations: int = 20,
           eval_n: int = 500,
           seed: int = SEED) -> Tuple[Genome, Dict[str, List[float]]]:

    random.seed(seed)
    np.random.seed(seed)

    # Evaluate on a subset each run for speed (keep stable with seed)
    eval_data = train_data.sample(n=min(eval_n, len(train_data)), random_state=seed).reset_index(drop=True)

    pop = [random_genome() for _ in range(pop_size)]
    fits = [fitness(g, eval_data) for g in pop]

    log = {"best": [], "avg": [], "var": []}

    for gen in range(1, generations + 1):
        best_i = int(np.argmax(fits))
        best_fit = float(fits[best_i])
        avg_fit = float(np.mean(fits))
        var_fit = float(np.var(fits))

        log["best"].append(best_fit)
        log["avg"].append(avg_fit)
        log["var"].append(var_fit)

        print(f"Gen {gen:02d} | best={best_fit:.4f} avg={avg_fit:.4f} var={var_fit:.6f} | best_genome={pop[best_i]}")

        # elitism: keep top 2
        elite_ids = np.argsort(fits)[-2:]
        new_pop = [pop[i] for i in elite_ids]

        while len(new_pop) < pop_size:
            p1 = tournament_select(pop, fits, k=3)
            p2 = tournament_select(pop, fits, k=3)
            child = mutate(crossover(p1, p2), pm=0.30)
            new_pop.append(child)

        pop = new_pop
        fits = [fitness(g, eval_data) for g in pop]

    best_i = int(np.argmax(fits))
    return pop[best_i], log

# ======================
# 10) Baseline vs best on Validation
# ======================
def evaluate_breakdown(g: Genome, data: pd.DataFrame, n: int = 400) -> Dict[str, float]:
    d = data.sample(n=min(n, len(data)), random_state=SEED).reset_index(drop=True)
    E, S, C, L = [], [], [], []
    for _, row in d.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)
        E.append(score_empathy(r))
        S.append(score_safety(r, row["risk_label"]))
        C.append(score_structure(r))
        L.append(length_penalty(r))
    return {
        "empathy": float(np.mean(E)),
        "safety": float(np.mean(S)),
        "structure": float(np.mean(C)),
        "len_penalty": float(np.mean(L)),
        "fitness": fitness(g, d)
    }

# ======================
# 11) Execute
# ======================
best_g, log = run_ga(train_df, pop_size=30, generations=20, eval_n=600, seed=SEED)

# baseline (manual) - adjust to match your current intended config
baseline = Genome(p_id=1, w_s=0.50, w_e=0.30, w_c=0.20, memory_window=512, theta_mid=0.55, theta_high=0.80)
baseline.normalize()


# ======================
# SAVE EXPERIMENT CONFIG
# ======================


config = {
    "population_size": 30,
    "generations": 20,
    "eval_subset": 600,
    "seed": SEED,
    "fitness_weights": {
        "empathy": 0.30,
        "safety": 0.50,
        "structure": 0.15,
        "length_penalty": 0.05
    },
    "length_threshold_words": 140
}

with open(os.path.join(OUT_DIR, "config.json"), "w") as f:
    json.dump(config, f, indent=4)


# ======================
# LENGTH DISTRIBUTION ANALYSIS
# ======================

def collect_response_lengths(g, data):
    lengths = []
    for _, row in data.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)
        lengths.append(len(r.split()))
    return np.array(lengths)

# Collect lengths for best optimized model
lengths = collect_response_lengths(best_g, val_df)


print("\n==============================")
print("LENGTH DISTRIBUTION ANALYSIS")
print("==============================")

print("Mean length:", np.mean(lengths))
print("Median length:", np.median(lengths))
print("75th percentile:", np.percentile(lengths, 75))
print("90th percentile:", np.percentile(lengths, 90))
print("95th percentile:", np.percentile(lengths, 95))
print("Max length:", np.max(lengths))


plt.figure()
plt.hist(lengths, bins=30)
plt.axvline(140, linestyle='--')
plt.xlabel("Response Length (words)")
plt.ylabel("Frequency")
plt.title("Distribution of Generated Response Lengths")
plt.tight_layout()

LENGTH_PLOT = os.path.join(OUT_DIR, "length_distribution.png")
plt.savefig(LENGTH_PLOT, dpi=300)
print("Saved length plot:", LENGTH_PLOT)



print("\n=== VALIDATION RESULTS ===")
base_metrics = evaluate_breakdown(baseline, val_df, n=400)
best_metrics = evaluate_breakdown(best_g, val_df, n=400)

print("Baseline:", baseline)
print("Baseline metrics:", base_metrics)
print("\nBest:", best_g)
print("Best metrics:", best_metrics)

# ======================
# 12) Save logs + plots
# ======================
out_history = pd.DataFrame({
    "generation": list(range(1, len(log["best"]) + 1)),
    "best_fitness": log["best"],
    "avg_fitness": log["avg"],
    "fitness_variance": log["var"]
})

# Output paths (same dir as script)

HISTORY_CSV = os.path.join(OUT_DIR, "ga_history_complete.csv")
PLOT_PNG = os.path.join(OUT_DIR, "ga_fitness_complete.png")

out_history.to_csv(HISTORY_CSV, index=False)

plt.figure()
plt.plot(out_history["generation"], out_history["best_fitness"], label="Best")
plt.plot(out_history["generation"], out_history["avg_fitness"], label="Average")
plt.xlabel("Generation")
plt.ylabel("Fitness")
plt.title("GA Fitness (Best & Average) Over Generations")
plt.legend()
plt.tight_layout()
plt.savefig(PLOT_PNG, dpi=300)

print("\nSaved:")
print("-", HISTORY_CSV)
print("-", PLOT_PNG)

# ======================
# 13) Show sample outputs on validation
# ======================
print("\n=== SAMPLE OUTPUTS (VALIDATION, BEST CONFIG) ===")
samples = val_df.sample(n=min(5, len(val_df)), random_state=SEED)
for _, row in samples.iterrows():
    print("\n---")
    print("Risk:", row["risk_label"], "| PHQ4:", row["total_score"])
    print("User:", row["user_prompt"][:180], "...")
    print("Bot:\n", generate_response(row["user_prompt"], row["risk_label"], best_g))


# ======================
# 14) MULTI-RUN EXPERIMENT
# ======================
from scipy.stats import ttest_rel, wilcoxon

def collect_prompt_scores(g: Genome, data: pd.DataFrame):
    scores = []
    for _, row in data.iterrows():
        r = generate_response(row["user_prompt"], row["risk_label"], g)
        score = (
            0.30 * score_empathy(r)
            + 0.50 * score_safety(r, row["risk_label"])
            + 0.15 * score_structure(r)
            - 0.05 * length_penalty(r)
        )
        scores.append(score)
    return np.array(scores)

def multi_run_experiment(train_df, val_df, runs=5):
    val_fitness_list = []
    param_list = []
    best_genomes = []

    for seed in range(1, runs+1):
        print(f"\n========== RUN {seed} ==========")
        best_g, log = run_ga(train_df,
                             pop_size=30,
                             generations=20,
                             eval_n=600,
                             seed=seed)

        metrics = evaluate_breakdown(best_g, val_df, n=400)

        print("Validation fitness:", metrics["fitness"])
        print("Weights -> w_s:", round(best_g.w_s,3),
              " w_e:", round(best_g.w_e,3),
              " w_c:", round(best_g.w_c,3))

        val_fitness_list.append(metrics["fitness"])
        param_list.append((best_g.w_s, best_g.w_e, best_g.w_c))
        best_genomes.append(best_g)

    return val_fitness_list, param_list, best_genomes



import time

def population_size_experiment(train_df, val_df):

    population_sizes = [30, 50, 100, 200, 300, 400]

    results = []

    for pop in population_sizes:

        print("\n==============================")
        print(f"Testing population size: {pop}")
        print("==============================")

        fitness_runs = []
        runtimes = []

        for run in range(1, 6):

            print(f"\nRun {run}/5")

            start = time.time()

            best_g, log = run_ga(
                train_df,
                pop_size=pop,
                generations=20,
                eval_n=600,
                seed=run
            )

            metrics = evaluate_breakdown(best_g, val_df, n=400)

            runtime = time.time() - start

            fitness_runs.append(metrics["fitness"])
            runtimes.append(runtime)

        mean_fit = np.mean(fitness_runs)
        std_fit = np.std(fitness_runs)
        mean_runtime = np.mean(runtimes)

        print("\nSummary:")
        print("Mean fitness:", mean_fit)
        print("Std fitness:", std_fit)
        print("Mean runtime:", mean_runtime)

        results.append({
            "population": pop,
            "mean_fitness": mean_fit,
            "std_fitness": std_fit,
            "mean_runtime_sec": mean_runtime
        })

    return pd.DataFrame(results)


# Run 5 independent GA runs
multi_fitness, param_list, best_genomes = multi_run_experiment(train_df, val_df, runs=5)


pop_results = population_size_experiment(train_df, val_df)

POP_RESULT_PATH = os.path.join(OUT_DIR, "population_experiment.csv")
pop_results.to_csv(POP_RESULT_PATH, index=False)

print("\nSaved population experiment results to:")
print(POP_RESULT_PATH)



plt.figure()

plt.errorbar(
    pop_results["population"],
    pop_results["mean_fitness"],
    yerr=pop_results["std_fitness"],
    marker="o"
)

plt.xlabel("Population Size")
plt.ylabel("Validation Fitness")
plt.title("Effect of Population Size on GA Optimization")

plt.tight_layout()

POP_PLOT = os.path.join(OUT_DIR, "population_experiment_plot.png")
plt.savefig(POP_PLOT, dpi=300)

print("Saved population plot:", POP_PLOT)




print("\n==============================")
print("MULTI-RUN SUMMARY")
print("==============================")
print("Validation fitness per run:", multi_fitness)
print("Mean fitness:", round(np.mean(multi_fitness), 4))
print("Std fitness:", round(np.std(multi_fitness), 4))





# ======================
# 15) STATISTICAL SIGNIFICANCE TEST
# ======================
print("\n==============================")
print("STATISTICAL TEST")
print("==============================")

# Use best genome from first run for statistical comparison
optimized_scores = collect_prompt_scores(best_genomes[0], val_df)
baseline_scores = collect_prompt_scores(baseline, val_df)

# Paired t-test
t_stat, p_ttest = ttest_rel(optimized_scores, baseline_scores)

# Wilcoxon (non-parametric)
w_stat, p_wilcoxon = wilcoxon(optimized_scores, baseline_scores)

print("Paired t-test p-value:", p_ttest)
print("Wilcoxon p-value:", p_wilcoxon)


# ======================
# 16) PARAMETER TREND ANALYSIS
# ======================
print("\n==============================")
print("PARAMETER TREND ANALYSIS")
print("==============================")

w_s_list = [p[0] for p in param_list]
w_e_list = [p[1] for p in param_list]
w_c_list = [p[2] for p in param_list]

print("Safety weights:", w_s_list)
print("Empathy weights:", w_e_list)
print("Structure weights:", w_c_list)

print("\nMean w_s:", round(np.mean(w_s_list), 3))
print("Mean w_e:", round(np.mean(w_e_list), 3))
print("Mean w_c:", round(np.mean(w_c_list), 3))




with open(os.path.join(OUT_DIR, "summary.txt"), "w") as f:
    f.write("=== VALIDATION RESULTS ===\n")
    f.write(f"Baseline fitness: {base_metrics['fitness']}\n")
    f.write(f"Optimized fitness: {best_metrics['fitness']}\n\n")
    f.write("=== PARAMETER TREND ===\n")
    f.write(f"Mean w_s: {np.mean(w_s_list)}\n")
    f.write(f"Mean w_e: {np.mean(w_e_list)}\n")
    f.write(f"Mean w_c: {np.mean(w_c_list)}\n\n")
    f.write("=== STATISTICAL TEST ===\n")
    f.write(f"Paired t-test p-value: {p_ttest}\n")
    f.write(f"Wilcoxon p-value: {p_wilcoxon}\n")