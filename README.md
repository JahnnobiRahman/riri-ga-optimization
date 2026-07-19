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

### Fitness (updated in v0.9)
```python
score = 0.40*E + 0.40*S + 0.15*C - 0.05*L
if risk == "high" and S < 1.0:  score -= 0.50
if S < 0.94:                     score -= 0.15
if C < 0.70:  score -= 0.10 * (0.70 - C) / 0.70
if E < 0.62:  score -= 0.18 * (0.62 - E) / 0.62
score += 0.05 * E
score += 0.05 * C
score += 0.05 * min(C, 0.8)

# New in v0.9: direct fitness pressure toward evolving gamma
if h_i > TAU_H and risk_label == "mid":
    if not has_escalation_language:
        score -= 0.10
```

Structure is reinforced twice (`+0.05*C` and `+0.05*min(C,0.8)`), empathy once (`+0.05*E`), safety not at all beyond the base term and its penalties. This asymmetry is the most direct explanation for why the GA consistently converges to a structure-dominant genome.

The distress-gating penalty (`-0.10`) is a **fitness-level** incentive that complements the **generation-time** gating described above — it does not change what the generator produces, but gives the GA a direct selection pressure to evolve `gamma` toward values that make escalation actually occur on high-distress mid-risk prompts.

There is no genome-level "hard kill" — the `-0.50`/`-0.15`/`-0.10` terms are all per-example, additive penalties, not a constraint that eliminates a genome from selection outright.

**Note on B6–B8:** `run_model_comparisons.py` scores the LLM baselines with a simplified `0.40*E + 0.40*S + 0.15*C` only — no length penalty, no bonus/penalty adjustments. Not directly comparable to the B1–B5 fitness values on a like-for-like basis, though this doesn't change which baselines look worse or better; all three (mT5-small, BanglaT5, BanglaGPT) score far below any EvoRiri condition regardless.

## GA configuration

Main experiment (`main_ga_riri.py`, non-quick mode): population 100, generations 20, tournament size 3, elitism top 2, per-gene mutation probability 0.30, evaluation subset 600 prompts/generation, seed 7, five independent runs.

Initialization is **seeded**, not random: `runner.get_seed_genomes()` provides four hand-designed genomes (balanced / safety-heavy / empathy-heavy / structure-heavy), used directly when population size allows, padded with random genomes otherwise.

An alternative MSGA-based (Kabir et al. 2017) seeding strategy is implemented in `msga_runner.py`: divides the genome space into `m=4` domains via empirical (not theoretical) Euclidean-distance boundaries from a minimum-genome origin, builds an archive per domain, and seeds the initial population from the best genome in each archive. Used for the B5 condition in the paper.

## Distress-gated escalation results (v0.9)

Full-dataset (N=2872) GA run with distress gating enabled converges to **γ⋆ ≈ 0.028** (`experiments/v2_population_experiment/best_genome_distress_gated_2872_SPLIT.json`). This is a small evolved relaxation, indicating the fixed threshold τ_h=0.65 already captures most of the useful escalation signal — the learned gate provides a secondary, fine-grained adjustment rather than a large behavioral shift (safety −0.003, empathy +0.004, structure −0.004, fitness −0.006 vs. base GA-optimized system B4).

> **Note on file naming:** `best_genome_distress_gated_2872_SPLIT.json` is the genome reported in the paper (Table 4). `best_genome_distress_gated_2872_FIXED.json` is a **different, unrelated genome** from a separate run (γ=0.0137) — do not confuse the two.

## Known caveats for anyone extending this code

1. **`baseline_prompt.py` is a hand-written text bank, not a generator call.** `generate_baseline_response()` returns one of three fixed sentences keyed only on risk level — it does not invoke `response_generator.py` at all. If you're using its output as a genuine B1 example, regenerate directly from `zeroshot_genome` through `assemble_prompt_trace()` instead.
2. **`theta_mid`/`theta_high` are non-functional** — see the genome table above. Any analysis of their evolved values is describing noise, not a fitness-driven result.
3. **`w_s` doesn't affect the visible response.** Attribute safety-related qualitative differences between genomes to the risk-label/distress-gate escalation logic, not `w_s`.
4. **Always serialize the full genome dict when running GA experiments** — `ga_log_*.json` files store only fitness curves (`best`/`avg`/`var` arrays), not genome fields. An early distress-gating run reported γ from an unserialized terminal readout (γ≈0.093) that could not later be verified; the properly serialized re-run (γ≈0.028) is what's reported in the paper. Use `rerun_distress_gated_2872.py`'s `best_genome_*.json` output as the source of truth for any genome value you plan to cite.

## Data

`phq4_cleaned.csv` is private and not included. Expected columns: `common_themes`, `thought_progression`, `risk_assessment`, `total_score`. Risk labels are derived via `evaluation/risk_labeling.py::label_risk()` (PHQ-4 total score thresholds + regex self-harm/suicide detection). User prompts are constructed as `common_themes + " | " + thought_progression`; empty prompts are dropped. 80/20 train/validation split, seed 7.

## Running

```bash
python main_ga_riri.py              # full GA run + population/dataset-size experiments
python baseline_comparison.py       # B1-B4 comparison table + significance tests
python src/rerun_distress_gated_2872.py  # v0.9 distress-gated GA run, full N=2872
python run_model_comparisons.py     # B6-B8 LLM baselines (requires transformers, model downloads)
```

## Compiling the paper

```bash
cd paper/
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

Requires an older TeX Live distribution (pre-2025) to avoid `lineno`/`cleveref` incompatibilities with the MDPI class file.

## Author

Jahnnobi Rahman
CEO & Product Lead, Relaxy PTE. LTD., Singapore and Bangladesh
ORCID: [0009-0002-7744-9853](https://orcid.org/0009-0002-7744-9853)

Supervisor / co-author: Prof. Mir Md. Jahangir Kabir, Data Science and Innovation, Transdisciplinary School, University of Technology Sydney, Australia
ORCID: [0000-0003-4963-8905](https://orcid.org/0000-0003-4963-8905)
