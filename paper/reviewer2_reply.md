## Reviewer 2

> **Note for the authors (delete before submission).** The `main.tex` edits listed at the end of this file (R2-E2 to R2-E9) have been applied; R2-E1 was not. Section numbers refer to the current compiled manuscript. The new results come from experiments run on 18 Oct 2026 with the same pipeline, data split and frozen scorer as the paper; the script and raw outputs are in the scratch folder `reviewer2_out/`.

We thank Reviewer 2 for the concise and technically precise comments. Several of them pointed to mechanisms that we had not examined carefully enough. In response, we ran four new sets of experiments: 30 GA seeds, 30 equal-budget random searches under a common selection design, a recalibrated safety threshold, and a GA with the inactive genes removed. We describe them below.

---

**Comment 2.1.** *It is not clear what the main reasons are for using a genetic algorithm over non-evolutionary approaches; for example, the 12-point 1D grid search performs better than the GA. Please add the justification.*

**Response.** We thank the reviewer for this question. We chose the GA before running the experiments, because of three properties of the problem (Section 1):
- the genome mixes continuous weights with discrete genes, namely a template index and a categorical budget (Eq. 6);
- the fitness function is non-differentiable and contains threshold regimes (Eqs. 7, 11 and 13), so gradient-based methods do not apply;
- we did not know in advance how the genes interact.

A population-based, derivative-free method suited all three.

We agree that our results do not show an advantage for the GA over simpler methods, and the revised manuscript no longer suggests one. The 12-point grid reaches the same fitness region because, as Proposition 4 (Section 3.9) shows, fitness depends on the structure weight through a deterministic plateau. The sweep could be restricted to that single gene only because the GA traces and the ablation (Table 10) had already identified it. A grid at the same resolution over all active genes would need about 10⁴ evaluations, five times the GA's budget. We present the comparison between methods as a finding about this search space rather than as a justification of the GA (Section 5.4).

---

**Comment 2.2.** *Also, justify how evolutionary search provides empirical benefits over uniform random sampling or single-parameter grid search.*

**Response.** We thank the reviewer for this question, and we agree that it needed a cleaner test. The original comparison had a weakness, which we noted in the manuscript: the random searches selected their best genome on the same validation prompts used to report them.

We have therefore repeated the comparison with **30 paired seeds** under a common design (Section 5.4) [R2-E2]:
- For each seed, the GA and an equal-budget random search (2,000 draws from the same genome space) both selected on the same 600-prompt sample of the optimisation set.
- The selected genomes were then scored on the 400-prompt validation subsample, with the same generation seed for both methods.
- Neither method saw the validation prompts during selection.

The results were as follows:
- The two methods selected different genomes, but all of them lie on the structure plateau.
- On **28 of the 30 seeds**, they received identical validation scores.
- Mean validation fitness was 0.7000 for both methods. The paired difference is 1.7 × 10⁻⁵, with a 90% CI of [−2.9 × 10⁻⁵, 6.4 × 10⁻⁵].
- A paired equivalence test (TOST) establishes **equivalence at the margin ε = 0.01** (p < 10⁻⁵⁰).
- The GA reached higher fitness on its own selection sample (0.710 versus 0.705), but this did not carry over to validation.

We therefore report, in answer to the reviewer's question, that we did not find an empirical benefit of evolutionary search over equal-budget random sampling in this search space, as Proposition 4 predicts. We have updated the Abstract, Section 5.4, Section 5.7 and the Conclusions accordingly [R2-E2, R2-E7, R2-E8, R2-E9].

---

**Comment 2.3.** *There seem to be some flaws in the genome parameters (dead, passive, and weakly identified). Inactive or dummy parameters may be pruned to reduce the artificial search-space dimension and avoid misleading parameter-drift interpretations.*

**Response.** We thank the reviewer for this careful observation, and we agree that these genes needed a clearer treatment.

The revised manuscript states their status formally. Proposition 1 (Section 3.9) shows that the fitness does not depend on θ_mid and θ_high, and that the effective search space is therefore smaller than the nominal genome. Proposition 2 shows that, because crossover and mutation act on each gene independently, the presence of these genes does not change the search dynamics of the active genes. Any "drift" in them is therefore neutral and is not interpreted anywhere in the paper. We also describe w_s as a renormalisation participant only (Section 3.3; Appendix B.1) and γ as weakly identified (Section 3.4.3; Section 4.7).

To confirm Proposition 2 empirically, we **ran the GA with θ_mid and θ_high removed** (frozen at constant values) for five seeds. The pruned runs gave **exactly the same validation fitness** as the full-genome runs with the same seeds (0.6949–0.7027), although the selected genomes differ in their other genes (Section 3.9) [R2-E3].

We have kept the two genes in the reported genome because they are the intended interface for graded escalation in future work, and we now show explicitly that keeping them has no effect on the results. If the reviewer prefers, we would be glad to remove them from the genome definition altogether.

---

**Comment 2.4.** *In Eq. 10, mid-risk safety scores are capped at 0.85, yet Eq. 13 applies a −0.15 penalty whenever safety falls below 0.94. The soft threshold should be recalibrated to properly evaluate mid-risk escalation quality.*

**Response.** We thank the reviewer for spotting this; we agree that the threshold is miscalibrated for mid-risk prompts. On closer analysis, we found that it does not affect which genomes are selected. Because every mid-risk response scores either 0.60 or 0.85, the penalty applies to all mid-risk examples whatever the genome. Over a fixed evaluation set it therefore subtracts the same constant from every genome, and it cannot change their ranking (Proposition 3, Section 3.9). Escalation quality for mid-risk prompts is still rewarded, through the base safety term (0.40 × (0.85 − 0.60) = 0.10 per example).

To check this empirically, we **re-scored the 30 GA genomes and both baselines with the threshold recalibrated to 0.80**, so that escalated mid-risk responses are no longer penalised. Fitness rises slightly: by 0.007–0.014 for the GA, 0.008–0.012 for B2 and 0.002–0.005 for B1. The ranking of the GA genomes is preserved (Spearman ρ = 0.94), and none of the comparisons reported in the paper changes [R2-E4].

Because recalibrating the scorer would alter every reported value without changing any conclusion, we have kept the frozen scorer for the main analysis and report the recalibrated result alongside it (Section 3.9). We hope this approach is acceptable to the reviewer.

---

**Comment 2.5.** *A small amount of noise obscures small performance differences between algorithms. Fix random-generation seeds during evaluation to make fitness scoring deterministic, allowing clear separation between search methods.*

**Response.** We are grateful for this suggestion, which led directly to the clearest result in the revision.

All new evaluations use a fixed generation seed per run, with the same seed for every condition compared (common random numbers). This covers the 30-seed significance analysis, the 30-seed GA–random-search comparison and the age-record robustness check (Section 3.5.6) [R2-E5]. Under seeded evaluation, fitness is deterministic: re-running a seed reproduces its genome and score exactly, and the first five of the 30 GA runs reproduce the archived genomes of Table 6 exactly.

As the reviewer anticipated, seeding allows a clear separation between search methods. In this case it shows that GA and random search reach identical scores on 28 of 30 seeds (see our response to Comment 2.2).

---

**Comment 2.6.** *Consider renaming `memory_window` to `response_part_budget` in the manuscript to avoid misunderstandings about the system's operational scope.*

**Response.** Thank you; we agree and have done this. The gene is now called the *response-part budget* $m$ throughout the manuscript. The implementation field name `memory_window` is retained only for code traceability (Section 3.3, Section 3.4.1 and Table 2), and both sections state explicitly that it is not a conversational context window, since the generator is single-turn and keeps no dialogue history.

---

**Comment 2.7.** *To strengthen statistical significance testing, experiments may be expanded to 20–30 independent seeds per condition.*

**Response.** We thank the reviewer for this suggestion and have **expanded the main comparison to 30 independent seeds** (Section 4.5) [R2-E6]. All 30 GA genomes scored above both fixed baselines:

| | Mean ± SD (30 seeds) |
|---|---|
| GA | 0.7000 ± 0.0035 |
| B1 | −0.2158 ± 0.0098 |
| B2 | 0.5535 ± 0.0070 |

- One-sided Wilcoxon signed-rank test: W = 465, p = 9.3 × 10⁻¹⁰ for both comparisons. With 30 seeds the test is no longer limited by its minimum attainable p-value of 1/32, as it was with five.
- The median GA–B2 difference is 0.147 (range 0.132–0.161; bootstrap 95% CI 0.144–0.149), matching the five-seed estimate.

The 30-seed GA–random-search comparison described under Comment 2.2 also uses 30 seeds. The dataset-size and population-size experiments still use five seeds per condition, and we say so in Section 5.7.

---

We thank Reviewer 2 again. The suggestions on seeding and on the number of seeds turned an inconclusive comparison into a clear one.

---
---

## `main.tex` edits for Reviewer 2 (applied 18 Oct 2026, except R2-E1)

| # | Where | What |
|---|---|---|
| R2-E1 | §5.4 | *Not applied, by your choice: the grid-cost point stays in the letter only* |
| R2-E2 | §5.4, random-search discussion | Soften the old conclusion sentence, then add a new paragraph on the 30-seed comparison |
| R2-E3 | §3.9, after the proof of Proposition 2 | Add one sentence on the pruned-genome runs |
| R2-E4 | §3.9, after the note on Proposition 3 | Add one sentence on the 0.80-threshold check |
| R2-E5 | §3.5.6, "Evaluation noise" | Say which evaluations are seeded |
| R2-E6 | §4.5, end of the significance paragraph | Replace the "20–30 seeds would be preferable" clause with the 30-seed result |
| R2-E7 | Abstract | Update the GA vs. random search sentence |
| R2-E8 | §6 Conclusions | Update the GA vs. random search sentence |
| R2-E9 | §5.7 Limitations | Update three phrases that the new runs make outdated |
