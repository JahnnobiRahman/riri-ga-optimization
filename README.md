# EvoRiri: Interpretable Evolutionary Search for Diagnosing Reward-Design Failures in a Bangla Mental-Health Assistant

This repository contains the code, experiment outputs, manuscript and peer-review record for **EvoRiri**, a study submitted to *Mathematics* (MDPI), Special Issue "Evolutionary Algorithms in Artificial Intelligence".

**Authors:** Jahnnobi Rahman ([ORCID 0009-0002-7744-9853](https://orcid.org/0009-0002-7744-9853)) and Mir Md. Jahangir Kabir, University of Technology Sydney ([ORCID 0000-0003-4963-8905](https://orcid.org/0000-0003-4963-8905)).

**Status (October 2026):** second-round revision submitted. Reviewers 1 and 3 recommended acceptance, Reviewer 2 had no further comments, and Reviewer 4's second-round comments were addressed in the current manuscript.

---

## Contents

1. [What this project is](#1-what-this-project-is)
2. [Where to start reading](#2-where-to-start-reading)
3. [Repository map](#3-repository-map)
4. [How the system works](#4-how-the-system-works)
5. [Project history, from start to finish](#5-project-history-from-start-to-finish)
6. [Peer review and how each comment was handled](#6-peer-review-and-how-each-comment-was-handled)
7. [Running the code](#7-running-the-code)
8. [Building the manuscript](#8-building-the-manuscript)
9. [Data and privacy](#9-data-and-privacy)
10. [Known caveats](#10-known-caveats)

---

## 1. What this project is

EvoRiri is a **template-based** Bangla, Banglish and English mental-health support assistant whose behaviour is controlled by a small, interpretable **genome**. A **genetic algorithm (GA)** searches over that genome to maximise a **rule-based fitness function** that scores each response for empathy, safety and structure.

The system **does not use a language model** to generate, score or search. Responses are assembled from fixed phrase banks; the genome decides which phrases and structural elements are included. Pre-trained Bangla language models appear only as **comparison baselines** (B6–B8).

The final contribution of the paper is a **diagnostic case study of reward design**, not a claim that evolutionary search is superior. The main findings are:

- The evolved genome raises structural completeness from 0.65 to 1.00 and fitness from 0.556 to 0.703 over a fixed reference genome, with comparable safety.
- A one-factor ablation attributes this gain to a single structure-weight threshold.
- Over 30 paired seeds, the GA and an equal-budget random search reach equivalent validation fitness.
- Trace analysis exposed failures that aggregate fitness hid: question-only structural collapse, empathy-marker stuffing, a structure-marker coverage gap and response-part-budget truncation.

## 2. Where to start reading

| If you want to… | Read |
|---|---|
| Understand the study | [`paper/main.pdf`](paper/main.pdf) (current manuscript) |
| See what the reviewers asked and how it was answered | [`paper/response_to_reviewers.md`](paper/response_to_reviewers.md) (round 1) and [`paper/reviewer4_round2_reply.md`](paper/reviewer4_round2_reply.md) (round 2) |
| Understand the code | Section 4 of this README, then [`src/`](src/) |
| Reproduce a number in the paper | Section 7 of this README, then [`experiments/`](experiments/) |
| See how the project evolved | Section 5 of this README and `git log` |

## 3. Repository map

```
paper/                          Manuscript and review record
  main.tex                      Manuscript source (the single source of truth)
  main.pdf                      Compiled manuscript (51 pages, round-2 version)
  references.bib                Bibliography
  build.sh                      Reproducible build script (see Section 8)
  Definitions/                  MDPI class and template files (27 July 2026 template)
  figures/                      Figures used by main.tex (vector PDFs; older PNGs kept for history)
  response_to_reviewers.md      Full round-1 response letter (all four reviewers)
  reviewer1_reply.md … reviewer4_reply.md   Round-1 replies, one file per reviewer
  reviewer1_edit_guide.md       Edit guide prepared while revising for Reviewer 1
  reviewer4_round2_reply.md     Round-2 reply to Reviewer 4
  round2_reviewer4_paste.html   The same round-2 reply formatted for pasting into a document
  Response_to_Reviewers.docx    Word version of the response letter (round 1 + round 2)
  TEMPLATE_UPDATE_CHECKLIST.md  Notes from moving to the updated MDPI template

src/                            The EvoRiri system
  ga/
    genome.py                   Genome dataclass, random_genome(), normalize() (weight floor 0.10)
    operators.py                tournament_select(), crossover() (uniform), mutate() (p_m = 0.30)
    runner.py                   run_ga(): GA loop with four hand-designed seed genomes, elitism E = 2
    msga_runner.py              run_ga_msga(): MSGA domain-division seeding (B5)
  generation/
    response_generator.py       assemble_prompt_trace(), generate_response(): the template generator G
    user_prompt_builder.py      build_realistic_user_prompt(): synthetic prompt x_i from theme text
  evaluation/
    scoring.py                  Empathy, safety and structure scores; fitness(); evaluate_breakdown()
    fitness.py                  Shared per-example fitness used by the GA (B1–B5) and LLM baselines (B6–B8)
    distress_scorer.py          compute_distress_score(): keyword-based distress score h_i
    risk_labeling.py            label_risk(): PHQ-4 thresholds + self-harm keyword override
    trace_export.py             Per-response trace export used for trace analysis
  experiments/                  Population-size and dataset-size sweeps (first versions)
  analysis/                     Early analysis and plotting scripts
  main_ga_riri.py               Main entry point: data loading, GA run, size experiments
  baseline_comparison.py        B1–B5 comparison table and five-seed Wilcoxon tests
  rerun_distress_gated_2872.py  GA with distress gating on the full N = 2,872 corpus
  rerun_size_experiments.py, plot_*.py   Size-experiment reruns and plots

experiments/                    Every result the paper reports, with the script that produced it
  baseline_comparison/          Main results: B1–B5 genomes and logs, five-seed significance,
                                grid search over w_c, equal-budget random search, B2→B4 ablation,
                                TOST equivalence tables (corrected and *_prebugfix audit copies),
                                B1-fixed truncation diagnostic, LLM baseline results (B6–B8)
    seed_genomes/               Best genome and fitness log for each of the five significance seeds
    b3_random_genomes/          The five random genomes used for B3
  revision/                     Experiments added during peer review (Section 6)
    scripts/                    reviewer2_runs.py, rerun_no_minors.py, eval_components.py,
                                score_table7.py, make_figures.py
    results/reviewer2/          30-seed GA vs random search, threshold check, pruned genome (+ run logs)
    results/no_minors/          Headline experiments repeated without self-reported 13–17 records
    results/components.json     Per-condition structure-component and escalation rates (Figures 3–4)
  v2_population_experiment/     Distress-gated runs on N = 2,872 and earlier population experiments
  V1_24_02_26/                  The very first GA experiment (February 2026)
  human_eval/                   Clinician ratings (private, not in git; see Section 9)

Root-level scripts              One-off checks and analyses written while answering specific questions
  run_corrected_experiments.py, recompute_equivalence_from_raw.py   Size experiments and TOST (Section 5)
  plot_corrected_experiments.py, regen_figs.py, regenerate_figures_4_5.py, generate_figs_minimal.py
  run_model_comparisons.py      B6–B8 zero-shot LLM baselines (mT5-small, BanglaT5, BanglaGPT)
  grid_search_wc*.py            Grid search over the structure weight w_c
  random_search_equal_budget.py Equal-budget (2,000-draw) random search
  rescore_five_seed_significance.py, add_b1_fixed_to_significance_test.py,
  compute_b1_fixed_significance_direct.py, evaluate_b1_fixed.py, test_b1_expected.py,
  check_b1_structure_variance.py, check_b2_structure_variance.py, debug_b1_genome_weights.py
                                B1 truncation diagnostic and significance re-scoring
  diagnose_structure_false_positives.py, check_response_consistency.py   Scorer audits
  minors_sensitivity_check.py, check_validation_minors*.py   Age-record checks
  compute_krippendorff.py       Inter-rater agreement for the human evaluation

figures/                        Early project diagrams (February 2026)
data/                           Private data (not in git; see Section 9)
```

## 4. How the system works

The manuscript is the authoritative description: Figure 1 shows the architecture, and Table 2 lists every component with its inputs, outputs, governing equation and interactions. Equation numbers below refer to the current manuscript.

### 4.1 Data and prompts

Each de-identified record has a PHQ-4 score, analyst-written theme fields (`common_themes`, `thought_progression`) and a risk-assessment note.

- The **risk label** r_i ∈ {low, mid, high} comes from the PHQ-4 score plus a self-harm keyword override applied to the risk note (Eq. 6, `risk_labeling.py`).
- The theme fields are joined into a **theme text** u_i. The template generator and the distress score read u_i.
- `build_realistic_user_prompt()` turns u_i into a **synthetic prompt** x_i (Eq. 4). Only the LLM baselines read x_i.
- The **distress score** h_i is a capped, weighted count over a 32-marker Bangla and English lexicon (Eq. 11, `distress_scorer.py`).
- The corpus has N = 2,872 records, split once 80/20 at seed 7 into 2,297 optimisation and 575 validation prompts. Most reported comparisons use a fixed 400-prompt validation subsample drawn at seed 7.

### 4.2 Genome (Eq. 7)

```python
Genome(p_id, w_s, w_e, w_c, memory_window, theta_mid, theta_high, gamma)
```

| Gene | Range | Role |
|---|---|---|
| `w_e` | [0.10, 1.0] | Empathy weight: selects the empathy-line pool. Functional. |
| `w_s` | [0.10, 1.0] | Safety weight: selects internal annotation lines that are stripped from the visible response. Its only effect is through the shared renormalisation of the three weights. |
| `w_c` | [0.10, 1.0] | Structure weight: selects the structure regime (Eq. 9). Functional and the gene that decides fitness. |
| `theta_mid`, `theta_high` | [0.40, 0.70], [0.70, 0.95] | Reserved escalation thresholds. **Not read** by the generator or the scorer; they drift under mutation. |
| `gamma` | [0.0, 0.2] | Distress gate: lowers the mid-risk escalation threshold (Eq. 10). |
| `p_id` (written d in the paper) | {0, 1, 2} | Template selector. |
| `memory_window` (written m, "response-part budget") | {256, 512, 768, 1024} | m ≤ 256 caps the response at 4 parts (truncation); larger values do not truncate (Eq. 8). |

After crossover and mutation, the three weights are floored at 0.10 and renormalised to sum to 1 (Eq. 21).

The genome reported in the paper is [`experiments/baseline_comparison/best_genome_B4.json`](experiments/baseline_comparison/best_genome_B4.json): w_e = 0.131, w_s = 0.101, w_c = 0.768, γ ≈ 0.058, d = 0, m = 512.

### 4.3 Template generator G (Eq. 2)

- **Empathy layer:** an opening line and reflection lines, chosen according to w_e.
- **Structure regimes (Eq. 9):**
  - w_c < 0.25: no structural components;
  - 0.25 ≤ w_c < 0.55: a random subset of grounding, action and question;
  - w_c ≥ 0.55: all three, deterministically.
- **Risk-aware escalation (Eq. 10):** escalate if r_i = high, or if r_i = mid and h_i > τ_h − γ·h_i, with τ_h = 0.65. Escalation adds crisis guidance to a complete reply rather than refusing.
- **Response-part budget (Eq. 8):** m ≤ 256 truncates the response to 4 parts. This is what removes B1's escalation lines.

### 4.4 Scoring and fitness (Eqs. 12–17)

- **Empathy E_i:** category presence (validation, reflection, normalisation, warmth) plus small length terms, minus a marker-stuffing penalty.
- **Safety S_i:** a lookup on risk level and whether escalation is present:

  | Risk | Escalation present | No escalation |
  |---|---|---|
  | high | 1.00 | 0.00 |
  | mid | 0.85 | 0.60 |
  | low | 0.75 | 1.00 |

- **Structure C_i:** 0, 1, 2 or 3 components give 0.00, 0.20, 0.60 or 1.00.
- **Per-example fitness:**

  ```
  0.40 E + 0.40 S + 0.15 C − 0.05 L
  ```

  plus per-example safety penalties (−0.50 for unsafe high-risk responses, −0.15 when S < 0.94), soft structure and empathy penalties, small reinforcement terms, and −0.10 for un-escalated high-distress mid-risk prompts.
- **Global fitness F(g):** the mean of the per-example fitness over the evaluation sample.

The scorer is **frozen**: the marker lists, formula and evaluation procedure were fixed for all reported analyses (manuscript Section 3.5.7).

### 4.5 Genetic algorithm (Eqs. 18–22)

| Setting | Value |
|---|---|
| Population, generations | P = 100, T = 20 (2,000 evaluations per run) |
| Selection | Tournament of size 3 |
| Crossover | Uniform, gene by gene |
| Mutation | Per gene, p_m = 0.30. Uniform noise ±0.25 for weights, ±0.06 for thresholds, ±0.05 for γ; categorical resampling for d and m |
| Elitism | Top E = 2 copied unchanged |
| Initialisation | Four seed genomes (balanced, safety-heavy, empathy-heavy, structure-heavy); the rest of the population drawn uniformly at random |
| Evaluation sample | 600 training prompts per run |

### 4.6 Conditions compared

| Condition | Description |
|---|---|
| B1 | Minimal-structure, short-budget baseline (w_e = 0.10, w_c = 0.10, w_s = 0.80, m = 256). It carries a truncation defect. |
| B2 | Fixed balanced seed genome g_bal, with no search |
| B3 | Five random genomes |
| B4 | GA-optimised genome (the reported condition) |
| B5 | GA with MSGA seeding |
| B6–B8 | Zero-shot mT5-small, BanglaT5 and BanglaGPT, scored with the same scorer |

## 5. Project history, from start to finish

Dates come from the git history and the review correspondence.

| When | What happened |
|---|---|
| **Feb 2026** | First GA experiment on the Riri template generator (`experiments/V1_24_02_26/`). The project README and the framework and pipeline diagrams were added. |
| **Mar 2026** | Population-size sensitivity experiment, dataset-size experiment, runtime scaling plots and GA logging. The code was made modular (`src/ga`, `src/generation`, `src/evaluation`). |
| **Apr–May 2026** | Seeded initialisation, trace export and balanced structure scoring. Several rounds of empathy-scorer improvements. Generator v2 (dynamic structure, more varied openings), risk-aware prompt generation and controlled escalation. Convergence and diversity plots. |
| **Jun 2026** | Convergence figures were replaced with real data from the T = 20 GA run (an earlier figure did not come from the logged run). v0.7 added MSGA seeding (B5), reorganised the paper and fixed the Bengali font. The zero-shot LLM baselines B6–B8 were added. |
| **Jul 2026** | Distress-gated escalation (gene γ, v0.9) was run on the full N = 2,872 corpus. The paper was revised around the empathy–structure trade-off. The structure scorer was **frozen** with expanded marker lists, and the full pipeline was re-run under it. |
| **Aug 2026** | The five-seed significance test was re-scored under the frozen scorer, and the provenance of the 400-prompt subsample was documented. A **bug in the TOST equivalence test** (swapped one-sided tails, which made equivalence impossible to establish) was found and fixed. All equivalence statistics were recomputed from the unchanged raw per-seed results; superseded files are kept as `*_prebugfix` (see Section 10). The paper moved to the 27 July 2026 MDPI template and was **submitted**. |
| **Oct 2026: round 1** | Four reviewer reports. The manuscript was substantially revised and new experiments were run (Section 6). The response letter is in `paper/response_to_reviewers.md`. |
| **Oct 2026: round 2** | Reviewers 1 and 3 recommended acceptance; Reviewer 2 had no further comments. Reviewer 4 asked for a system-architecture figure with the governing equation of each stage, technical detail on how the system integrates with LLMs, clearer technical contributions, and better figures and tables. These were addressed in the current `paper/main.tex` (Section 6). |

## 6. Peer review and how each comment was handled

### Round 1

**Reviewer 1** asked for mathematical substance, a clean separation of the GA effect from the B1 defect, honesty about synthetic prompts, ethics clarification, a shorter text and correct use of "multi-objective".

- A section on formal properties of the search space and fitness function was added (four propositions on neutral genes, a selection-invariant penalty and the structure plateau).
- A one-factor B2→B4 ablation (`experiments/baseline_comparison/ablation_b2_to_b4.*`) and a B1 truncation diagnostic ("B1-fixed") were added.
- The contribution was repositioned as a diagnostic case study.
- The ethics section was expanded, and all experiments were re-run without the self-reported 13–17 records (`experiments/revision/results/no_minors/`). The conclusions are unchanged (manuscript Table 12).
- "Multi-objective" was replaced with "scalarised fitness".

**Reviewer 2** asked for:
- **a justification of the GA over grid and random search:** 30 GA seeds were compared with 30 equal-budget random searches (`experiments/revision/scripts/reviewer2_runs.py`, R1/R2). GA fitness is 0.7000 ± 0.0035, and the GA is significantly better than B1 and B2 (Wilcoxon W = 465, p = 9.3 × 10⁻¹⁰). GA and random search are equivalent (TOST), with 28 of the 30 pairs identical.
- **pruning the inactive genes:** re-running with θ frozen gives identical results (R4).
- **recalibrating the 0.94 safety threshold:** re-scoring at 0.80 preserves the ranking (Spearman ρ = 0.94) (R3).
- **fixed seeds for deterministic evaluation:** the seeded re-scoring is described in manuscript Section 3.5.6.
- **renaming memory_window:** it is now called the "response-part budget" in the paper.
- **20–30 seeds:** 30 seeds were run.

**Reviewer 3** asked for a clearer GA contribution, a separation of fitness design from search, the status of the θ genes, care with the B1 comparison, the limits of proxy scores and presentation fixes. These were answered by the same analyses, by reframing, and by text and figure corrections. For example, Figure 5 was renamed to "fitness dispersion".

**Reviewer 4** asked for a rewritten abstract, a clearer novelty statement, a clearer pipeline figure, the role of LLMs, a rewritten Table 7 and a rewritten conclusion. All were rewritten. The LLM baselines were characterised as zero-shot references only.

All data figures were regenerated as vector graphics in one consistent style.

### Round 2 (Reviewer 4)

- **Figure 1** was replaced with a five-layer system-architecture diagram in which every box cites its governing equation.
- New equations were added for prompt construction (Eq. 4), the structure regimes (Eq. 9), the distress score (Eq. 11) and the GA operators (Eqs. 18–22).
- New **Table 2** lists each component with its input, output, equation and interactions.
- New **Section 3.10, "Interface with Large Language Models"**, describes the implemented comparison interface (Eq. 27) and a proposed, not evaluated, genome-conditioned LLM generator (Eq. 28).
- The contributions in the Introduction were rewritten as **C1–C6**.
- All tables were restyled, and the data figures were redrawn at the exact text width (`experiments/revision/scripts/make_figures.py`).
- One sentence in Section 3.7 was corrected so that it matches the code: the rest of the initial population is drawn uniformly at random.
- No reported value changed in round 2.

## 7. Running the code

Run everything from the repository root with the project virtual environment. Python 3.13, with numpy, pandas, scipy and matplotlib; the LLM baselines also need transformers.

```bash
python src/main_ga_riri.py                       # main GA run + size experiments
python src/baseline_comparison.py                # B1–B5 table + five-seed significance
python src/rerun_distress_gated_2872.py          # distress-gated GA on N = 2,872
python run_model_comparisons.py                  # B6–B8 LLM baselines (downloads models)
python run_corrected_experiments.py              # dataset-size and population-size experiments
python recompute_equivalence_from_raw.py         # TOST tables from the raw per-seed CSVs
python experiments/baseline_comparison/ablation_b2_to_b4.py   # one-factor ablation
python experiments/revision/scripts/reviewer2_runs.py OUT_DIR  # 30-seed GA vs RS, threshold, pruning
python experiments/revision/scripts/rerun_no_minors.py OUT_DIR # no-minors rerun
python experiments/revision/scripts/eval_components.py OUT.json            # component and escalation rates
python experiments/revision/scripts/make_figures.py paper/figures COMPONENTS.json   # all data figures
```

All scripts need the private data file `data/phq4_cleaned.csv` (Section 9). Results are seeded: seed 7 for the split and main run, and seeds 13, 26, …, 390 for the 30-seed study.

## 8. Building the manuscript

```bash
cd paper
./build.sh            # xelatex + bibtex + xelatex ×2, non-interactive, with a lock
./build.sh --clean    # remove generated files first
```

The build needs XeLaTeX with Palatino and Noto Serif Bengali fonts. A clean build reports no errors and no undefined references.

## 9. Data and privacy

- `data/phq4_cleaned.csv` and the other files in `data/` are **private** and never committed. Expected columns: `common_themes`, `thought_progression`, `risk_assessment`, `total_score`.
- The clinician ratings in `experiments/human_eval/` (manuscript Table 9 and Krippendorff's α) are **private** and have never been committed. They are available from the corresponding author on reasonable request.
- `experiments/baseline_comparison/b1_fixed_qualitative_examples.json` contains theme text from real records and is excluded from git for the same reason.
- Committed result files contain genomes, fitness values and aggregate statistics only.

## 10. Known caveats

1. **`theta_mid` and `theta_high` are non-functional.** Any analysis of their evolved values describes drift, not selection.
2. **`w_s` does not affect the visible response.** Safety differences come from the risk label, the distress gate and truncation.
3. **B1's low safety is a truncation artefact** of m = 256, not a property of its weights. See the B1-fixed diagnostic.
4. **TOST correction:** the original `tost_equivalence()` swapped its two one-sided tails, so it could never establish equivalence, and it labelled a 90% interval as 95%. It was corrected, and all statistics were recomputed from unchanged raw CSVs (`recompute_equivalence_from_raw.py`, cross-checked against `statsmodels` to 1e-12). The superseded `*_prebugfix` files are kept only as an audit record. **Do not cite them.**
5. **Distress-gated runs:** `best_genome_distress_gated_2872_SPLIT.json` and `_FIXED.json` in `experiments/v2_population_experiment/` come from different runs. The genome reported in the paper is `best_genome_B4.json`.
6. **Evaluation noise:** unseeded single evaluations vary by about 0.003–0.005, so differences below about 0.01 are not resolvable (manuscript Section 3.5.6).
