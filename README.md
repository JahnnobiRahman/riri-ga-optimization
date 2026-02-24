# Genetic Algorithm–Based Prompt Optimization for a Bangla/Banglish Mental Health Conversational System (Version 1)

## Abstract

This repository contains Version 1 of a Genetic Algorithm (GA)–based framework for optimizing prompt configuration parameters in a culturally adaptive mental health conversational assistant ("Riri").

The system optimizes multi-dimensional conversational behavior:  empathy, safety compliance, structural guidance, and response efficiency using evolutionary search over configurable prompt parameters.

The work is currently being prepared for submission to an MDPI journal.

---

## 1. Problem Statement

Conversational AI systems deployed in mental health contexts must balance multiple competing objectives:

- Empathetic validation  
- Clinical safety compliance  
- Structured psychological guidance  
- Response conciseness  

Manual prompt tuning is insufficient to systematically explore these trade-offs.  
This study proposes a stochastic evolutionary optimization approach.


##Experimental Pipeline

![Experimental Pipeline](figures/fig1_experimental_pipeline.png)

*Experimental pipeline for genetic algorithm–based prompt configuration optimization. The pipeline includes data preprocessing (risk labeling and prompt construction), optimization via genetic algorithm (population = 30, generations = 20, five independent runs), validation evaluation, statistical testing, and experiment logging.*

---

## 2. Data Preprocessing

The dataset (`phq4_cleaned.csv`) contains:

- `common_themes`
- `thought_progression`
- `risk_assessment`
- `total_score` (PHQ-4 score)

### 2.1 Prompt Construction

User prompts are constructed as:

common_themes + " | " + thought_progression

Empty prompts are removed.

### 2.2 Risk Labeling

Risk categories are derived using:

1. PHQ-4 total score  
2. Regex-based detection of suicide/self-harm indicators  

High risk if:
- PHQ-4 ≥ 9  
- OR explicit suicide/self-harm text detected  

Mid risk if:
- PHQ-4 ≥ 6  

Else:
- Low risk  

---

## 3. Prompt Configuration Genome

Each genome encodes:

- Template ID
- Safety weight (w_s)
- Empathy weight (w_e)
- Structure weight (w_c)
- Memory window size
- Escalation threshold θ_mid
- Escalation threshold θ_high

Weights are normalized with a minimum floor constraint (≥ 0.10).

---

## 4. Fitness Function

A single-objective composite fitness function is used:

F(x) = 0.30E(x) + 0.50S(x) + 0.15C(x) − 0.05L(x)

Where:

- E(x): Empathy score (marker-based, tanh scaled)
- S(x): Safety compliance score
- C(x): Structural coherence score
- L(x): Length penalty

### 4.1 Empathy Score

Marker-based phrase detection scaled via:

E(x) = tanh(marker_hits / 3)

### 4.2 Safety Score

- High-risk prompts require escalation
- Mid-risk prompts partially reward escalation
- Low-risk prompts penalize unnecessary escalation

### 4.3 Structure Score

Rewards presence of:
- Grounding technique
- Actionable step
- Reflective question

Each contributes proportionally to a bounded [0,1] score.

### 4.4 Length Penalty

A penalty is applied for responses exceeding 140 words:

L(x) = max(0, (words − 140) / 140)

The 140-word threshold is empirically validated via response length distribution analysis.

---

## 5. Genetic Algorithm Design

The GA implements:

- Random population initialization
- Tournament selection (k=3)
- Uniform crossover
- Mutation (continuous + discrete parameters)
- Elitism (top 2 preserved)
- 20 generations
- Population size = 30

---

## 6. GA Workflow

## Genetic Algorithm Framework

![GA Framework](figures/fig2_ga_framework.png)

*Genetic Algorithm framework for prompt configuration optimization.* 


---

## 7. Experimental Design

- Train/Validation split: 80/20
- Evaluation subset per generation: 600 samples
- Multi-run experiment: 5 independent seeds
- Statistical testing:
  - Paired t-test
  - Wilcoxon signed-rank test

Parameter trend analysis reports:

- Mean safety weight
- Mean empathy weight
- Mean structure weight

---

## 8. Experiment Logging

Each run is saved under:

experiments/<experiment_name>/

Including:

- config.json
- ga_history_complete.csv
- ga_fitness_complete.png
- length_distribution.png
- summary.txt

All experiments are reproducible via fixed seeds.

---

## 9. Project Structure

src/  
  ga_riri.py  

data/  
  phq4_cleaned.csv (private, excluded)  

experiments/  
  V1_24_02_26/  

---

## 10. Running the Experiment

From project root:

python src/ga_riri.py

Outputs will be saved inside the appropriate experiment folder.

---

## 11. Statistical Validation

Validation performance is evaluated using:

- Mean ± standard deviation across 5 runs  
- Per-prompt comparison against baseline  
- Paired t-test  
- Wilcoxon signed-rank test  

---

## 12. Data Availability

The dataset is private and not included.

To reproduce:

Place dataset at:

data/phq4_cleaned.csv

---

## 13. Version

Version: V1_24_02_26  
Seed: 7  
Population: 30  
Generations: 20  
Runs: 5  

---

## Author

Jahnnobi Rahman  
AI & Mental Health Systems Research
