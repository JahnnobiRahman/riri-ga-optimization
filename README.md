# EvoRiri: Risk-Aware Genetic Optimization of a Bangla/Banglish/English Mental-Health Assistant

## Overview

EvoRiri is a genetic-algorithm (GA) framework that evolves a small, interpretable **genome** controlling a template-based response generator ("Riri") for Bangla/Banglish/English mental-health support conversations. The generator makes no LLM calls at inference time; it assembles responses from fixed phrase banks, with the genome controlling which phrases and structural elements get included. Optimization is driven by a rule-based fitness function scored automatically per response.

## Project structure

```
src/
  ga/
    genome.py         # Genome dataclass, random_genome(), normalize()
    operators.py       # crossover(), mutate(), tournament_select()
    runner.py          # run_ga() — main GA loop, hand-designed seed genomes
    msga_runner.py      # run_ga_msga() — domain-division seeded init (Kabir 2017)
  generation/
    response_generator.py   # assemble_prompt_trace(), generate_response()
    user_prompt_builder.py  # build_realistic_user_prompt() — synthetic NL prompts
  evaluation/
    scoring.py          # score_empathy/safety/structure, length_penalty, fitness()
    risk_labeling.py    # label_risk() — PHQ-4 + regex risk labeling
    trace_export.py     # export_traces() — full per-response trace CSV

main_ga_riri.py         # main entry point: loads data, runs GA, runs experiments
baseline_comparison.py  # B1-B4 baseline comparison table + Wilcoxon tests
baseline_prompt.py      # hand-written B1 example text for Table 7 (see caveat below)
merge_baseline_optimised.py  # merges baseline_prompt.py output with trace_analysis.csv
run_model_comparisons.py     # B6-B8: mT5/BanglaT5/BanglaGPT zero-shot baselines
population_experiment.py     # population-size sensitivity sweep
dataset_size_experiment.py   # dataset-size sensitivity sweep
trace_analysis_plots.py      # generates Figures 6-8 (structure usage, safety by risk, empathy vs structure)
plot_dataset_scaling.py / plot_dataset_scatter.py / plot_runtime_scaling.py  # Figures 2, 9

data/
  phq4_cleaned.csv     # private, not included — see Data Availability
```

## Genome

```python
Genome(p_id, w_s, w_e, w_c, memory_window, theta_mid, theta_high)
```

| Gene | Range | What it actually does |
|---|---|---|
| `w_e` (empathy weight) | [0.10, 1.0], renormalized | Selects the empathy-line pool bucket (low/mid/high) and adds an extra empathy line when `w_e >= 0.45`. Functional. |
| `w_c` (structure weight) | [0.10, 1.0], renormalized | Governs which structure regime applies (see below). Functional. |
| `w_s` (safety weight) | [0.10, 1.0], renormalized | Selects one of several internal `[SAFETY]`-tagged annotation lines. These are stripped out before the response is finalized (`visible_response` filters `[SAFETY]`/`[TEMPLATE]` lines). **`w_s` currently has no effect on the visible response text or any automatic score.** |
| `theta_mid`, `theta_high` | [0.40, 0.70], [0.70, 0.95] | Crossed over and mutated like every other gene. **Not read anywhere in `response_generator.py` or `scoring.py`.** They carry no fitness gradient; expect them to drift under mutation without converging (visible in per-generation genome logs — `w_c` trends monotonically toward the optimum, `theta_mid`/`theta_high` don't). Reserved for a future graded-escalation mechanism (see Limitations below). |
| `p_id` | {0, 1, 2} | Discrete template selector. |
| `memory_window` | {256, 512, 768, 1024} | Response context length; also gates a truncation rule (see caveat below). |

**Normalization quirk worth knowing:** `Genome.normalize()` enforces a 0.10 floor on `w_s`/`w_e`/`w_c` and then rescales all three to sum to 1. If you construct a genome with all three at the floor (e.g. the B1 zero-shot baseline: `w_s=w_e=w_c=0.10`), normalization rescales each to `0.10/0.30 = 0.333`, **not** 0.10. This pushes `w_c` just past the 0.33 `weight_to_level()` boundary and into the stochastic structure regime described below — B1 is not as fully "zeroed out" post-normalization as the pre-normalization values suggest.

## Response generation mechanism

### Structure (grounding / action / question)

Not a smooth per-component threshold function. Three regimes on `w_c`:

- `w_c < 0.25`: no structural components added.
- `0.25 <= w_c < 0.55`: components are shuffled and up to 2 of the 3 are included, each independently gated by a risk-level-dependent probability. **Stochastic** — which two components appear varies run to run for the same genome.
- `w_c >= 0.55`: all three components included deterministically.

### Escalation

Purely categorical, gated on the dataset's risk label:

```python
escalate = (risk_label == "high")
```

High-risk prompts get crisis-style escalation language (contact a trusted person / professional / emergency support). Mid-risk prompts get non-crisis soft-support language, unconditionally — never escalation language, regardless of prompt content. Low-risk prompts get neither. `theta_mid`/`theta_high` and any prompt-derived distress signal play no role in this decision.

**Truncation caveat:** when `memory_window <= 256`, the assembled response is truncated to its first 4 parts. For high-risk prompts under the B1 zero-shot genome (`memory_window=256`), this frequently truncates away the escalation line that was otherwise unconditionally added, which is the primary driver of B1's low safety score on high-risk prompts — not an intentional safety mechanism, an emergent consequence of the truncation rule interacting with a short memory window.

## Scoring (`evaluation/scoring.py`)

### Empathy
Category-presence scoring, not marker-count/tanh:
```
score = 0.30*[validation present] + 0.25*[reflection present]
      + 0.20*[normalization present] + 0.15*[warmth present]
      + 0.05*[len>=25 words] + 0.05*[len>=50 words]
      - 0.05*[validation+reflection+normalization hits > 3]
```

### Safety
Categorical lookup by risk label and a single `has_escalation` boolean — no continuous S⁺/S⁻ decomposition:

| Risk | Escalation present | Score |
|---|---|---|
| high | yes / no | 1.00 / 0.00 |
| mid  | yes / no | 0.85 / 0.60 |
| low  | no / yes | 1.00 / 0.75 |

### Structure
Discrete lookup on component count, not a continuous `(1/3)Σcᵢ` formula:

| Components present | Score |
|---|---|
| 0 | 0.00 |
| 1 | 0.20 |
| 2 | 0.60 |
| 3 | 1.00 |

### Length penalty
```python
length_penalty = max(0, (word_count - 140) / 140)
```
Zero below 140 words, linear above. No penalty for short responses.

### Fitness
```python
score = 0.40*E + 0.40*S + 0.15*C - 0.05*L
if risk == "high" and S < 1.0:  score -= 0.50
if S < 0.94:                     score -= 0.15
if C < 0.70:  score -= 0.10 * (0.70 - C) / 0.70
if E < 0.62:  score -= 0.18 * (0.62 - E) / 0.62
# additional reinforcement, not part of the base A/B/C/D formula:
score += 0.05 * E
score += 0.05 * C
score += 0.05 * min(C, 0.8)
```
Structure is reinforced twice (`+0.05*C` and `+0.05*min(C,0.8)`), empathy once (`+0.05*E`), safety not at all beyond the base term and its penalties. This asymmetry is the most direct explanation for why the GA consistently converges to a structure-dominant genome.

There is no genome-level "hard kill" (i.e. no global fitness override for the whole genome based on any single unsafe example) — the `-0.50`/`-0.15` terms are per-example, additive penalties, not a constraint that eliminates a genome from selection outright.

**Note on B6–B8:** `run_model_comparisons.py` scores the LLM baselines with a simplified `0.40*E + 0.40*S + 0.15*C` only — no length penalty, no bonus/penalty adjustments. Not directly comparable to the B1–B5 fitness values on a like-for-like basis, though this doesn't change which baselines look worse or better; all three (mT5-small, BanglaT5, BanglaGPT) score far below any EvoRiri condition regardless.

## GA configuration

Main experiment (`main_ga_riri.py`, non-quick mode): population 100, generations 20, tournament size 3, elitism top 2, per-gene mutation probability 0.30, evaluation subset 600 prompts/generation, seed 7, five independent runs.

Initialization is **seeded**, not random: `runner.get_seed_genomes()` provides four hand-designed genomes (balanced / safety-heavy / empathy-heavy / structure-heavy), used directly when population size allows, padded with random genomes otherwise.

An alternative MSGA-based (Kabir et al. 2017) seeding strategy is implemented in `msga_runner.py`: divides the genome space into `m=4` domains via empirical (not theoretical) Euclidean-distance boundaries from a minimum-genome origin, builds an archive per domain, and seeds the initial population from the best genome in each archive. This is used for the B5 condition in the paper.

## Known caveats for anyone extending this code

1. **`baseline_prompt.py` is a hand-written text bank, not a generator call.** `generate_baseline_response()` returns one of three fixed sentences keyed only on risk level — it does not invoke `response_generator.py` at all. If you're using its output as a genuine B1 example (e.g. for qualitative tables), regenerate directly from `zeroshot_genome` through `assemble_prompt_trace()` instead.
2. **`theta_mid`/`theta_high` are non-functional** — see the genome table above. Any analysis of their evolved values (e.g. "the GA converged to θ_mid=0.70") is describing noise, not a fitness-driven result.
3. **`w_s` doesn't affect the visible response.** Don't attribute safety-related qualitative differences between genomes to `w_s`; attribute them to the risk-label escalation gate.

## Data

`phq4_cleaned.csv` is private and not included. Expected columns: `common_themes`, `thought_progression`, `risk_assessment`, `total_score`. Risk labels are derived via `evaluation/risk_labeling.py::label_risk()` (PHQ-4 total score thresholds + regex self-harm/suicide detection). User prompts are constructed as `common_themes + " | " + thought_progression`; empty prompts are dropped. 80/20 train/validation split, seed 7.

## Running

```bash
python main_ga_riri.py          # full GA run + population/dataset-size experiments
python baseline_comparison.py   # B1-B4 comparison table + significance tests
python run_model_comparisons.py # B6-B8 LLM baselines (requires transformers, model downloads)
```

## Author

Jahnnobi Rahman
CEO & Product Lead , Relaxy PTE. LTD. , Singapore , Bangladesh

Supervisor / co-author: Prof. Mir Md. Jahangir Kabir, Data Science and Innovation, Transdisciplinary School, University of Technology Sydney , Australia