## Reviewer 3

> **Note for the authors (delete before submission).** The `main.tex` edits listed at the end of this file (R3-E1 to R3-E5) have been applied. Section, table, figure and proposition numbers refer to the current compiled manuscript.

We sincerely thank Reviewer 3 for the careful and constructive comments, which helped us clarify the contribution of the work and improve its presentation. We respond to each point below and indicate where the changes appear in the revised manuscript.

---

**Comment 3.1.** *The main concern is that the GA advantage is not clearly established. The authors show that grid search and equal-budget random search can also reach the same fitness region. Therefore, the actual contribution of the GA needs to be explained more clearly.*

**Response.** We agree, and we thank the reviewer for raising this central point. The revised manuscript no longer presents an advantage of the GA as a contribution, and it now tests the question directly.

- **A cleaner comparison.** We repeated the GA versus random-search comparison with 30 paired seeds. Both methods select on the same optimisation-set sample, and both are scored on the validation prompts with the same generation seed. The two methods are statistically equivalent: identical validation scores on 28 of the 30 seeds, equivalence at ε = 0.01 (Section 5.4).
- **The reason.** Proposition 4 (Section 3.9) shows that the fitness depends on the structure weight through a deterministic plateau, so any search that samples that region reaches the same fitness.
- **The role of the GA.** The study treats the GA as a standard, interpretable search procedure. The contribution lies in the genome–generator–scorer framework and in what it made visible: four reward-design and generator failures, and the mechanism behind the measured gain. We now state this in the Introduction (contribution list and novelty paragraph), the Abstract and the Conclusions.

---

**Comment 3.2.** *The fitness function contains several manually selected weights, thresholds and penalty terms. It is difficult to understand whether the improvement is coming from the GA or mainly from the design of the scoring function.*

**Response.** This is an important question, and we are grateful to the reviewer for raising it. The evidence in the revised manuscript indicates that the improvement comes from the design of the generator and fitness function rather than from the search method.

- **One-factor ablation (Section 5.4, Table 10).** Moving genes one at a time between the fixed reference genome (B2) and the GA genome (B4) shows that the structure weight alone reproduces the entire improvement. A hand-set value in the plateau gives the same result.
- **Formal properties (Section 3.9).** Proposition 4 shows how the structure-dependent fitness terms create that plateau. Proposition 3 shows that one of the hand-set penalties (the mid-risk safety threshold) adds the same constant to every genome and cannot affect which genome is selected.
- **Sensitivity of a hand-set threshold.** Recalibrating that threshold from 0.94 to 0.80 shifts all fitness values slightly but preserves the ranking of genomes (Spearman ρ = 0.94) and leaves every comparison unchanged (Section 3.9).
- **Why the optimum is structure-dominant.** Section 5.5 explains that the structure-dominant optimum follows from where the fitness function leaves the most headroom and rewards structure most, not from the nominal weights.

The rationale for the fixed weights is given in Section 3.5.5. We have added a sentence to Section 5.4 stating plainly that the measured improvement comes from the design of the generator and the fitness function, not from the search method [R3-E2].

---

**Comment 3.3.** *The genome contains θ_mid and θ_high, but these parameters are not used by the present generator or fitness calculation. Including inactive genes in the optimisation makes the genome formulation confusing.*

**Response.** We thank the reviewer for raising this point, and we agree that the role of these two genes needed to be explained more clearly. We have addressed it in three ways.

- **Labelling.** The two genes are marked as reserved and inactive wherever they appear: in the definition of the genome (Section 3.3), in Tables 2 and 4, and in Appendix B.1, which also explains why they are kept (as the interface for graded escalation in future work).
- **Formal treatment.** Proposition 1 (Section 3.9) shows that the fitness does not depend on these genes, so the effective search space is smaller than the nominal genome. Proposition 2 shows that, because the variation operators act on each gene independently, their presence does not change the search on the active genes.
- **Empirical check.** Running the GA with the two genes removed gave exactly the same validation fitness as the full genome for all five seeds tested (Section 3.9).

The genome formulation therefore now states exactly which genes affect the results and which do not.

---

**Comment 3.4.** *The B1–B4 comparison is affected by the truncation problem in B1. Therefore, the improvement shown in the human evaluation cannot be considered only as an effect of GA optimisation. The authors should be more careful while interpreting this comparison.*

**Response.** We thank the reviewer for this observation and fully agree that this comparison calls for careful interpretation.

- **Truncation isolated.** A controlled diagnostic in Section 5.4 (Table 9) changes only B1's response-part budget. This alone removes most of B1's safety deficit, so that deficit is attributed to the truncation defect rather than to optimisation.
- **Human evaluation reinterpreted.** The human-evaluation section now opens by stating this limitation (Section 4.9). It reads the clinicians' ratings only as a preference for complete over truncated responses, not as evidence that evolutionary search improves clinical quality (Section 4.9.2).
- **Better comparator.** Throughout the paper, B2 rather than B1 is treated as the informative non-GA comparator.
- **Future work.** A clinician comparison of B2 against B4 is listed in Section 5.7 (future-work item 6).

---

**Comment 3.5.** *The safety and empathy scores are both based on predefined rules and markers. The empathy marker-stuffing problem shows that a higher automatic score may not always mean a better response. The limitation of these proxy scores should be clearly considered when discussing the optimised results.*

**Response.** We are grateful to the reviewer for this important observation, and we fully agree. In the revised manuscript, we now acknowledge this limitation at the point where the optimised results are first presented: Section 4.3 notes that the automatic scores are rule-based proxies and, with reference to the marker-stuffing case, that a higher automatic score does not necessarily indicate a better response [R3-E1].

We have also taken care to reflect this limitation in five further places:
- Section 4.7 reports a further example: a supportive phrase used for mid-risk prompts contains a word on the escalation-marker list, so some mid-risk responses are scored as escalated.
- Section 4.9.2 shows the opposite risk: the empathy proxy under-credits an improvement that clinicians perceive.
- Section 5.3 and Appendix A.2 document marker stuffing itself.
- Section 5.6 discusses the deployment risk of responses that are "metrically but not clinically safe".
- Section 5.7 lists the limits of keyword-based scoring, which cannot capture context, negation, sarcasm or culturally specific expression.

Throughout, we interpret the automatic scores as directional optimisation signals, not as measures of clinical quality.

---

**Comment 3.6.** *Figure 5 is called population diversity although it represents fitness variance, and there are a few grammatical and formatting errors throughout the manuscript.*

**Response.** We thank the reviewer for drawing our attention to these presentation issues, and we have corrected them as follows.

- **The figure.** It is now titled "Population fitness dispersion", and its caption states that it is not a measure of genotype diversity. Because it is a secondary result, we have moved it, with its short discussion, to Appendix B.2 (now Figure A1); Section 4.2 summarises it in one sentence.
- **Proofreading.** We have proofread the whole manuscript. Corrections include spacing around citations and punctuation, a missing phrase in Section 5.2, a duplicated word, and an ungrammatical sentence in the Introduction [R3-E3, R3-E4].
- **Spelling.** We have made the spelling consistently British throughout; the original mixed "optimisation" and "optimization", for example [R3-E5].
- **Figure quality.** We have regenerated all data figures as vector graphics in one consistent style, using the journal's typeface, a colour-blind-safe palette and labels sized for print. We have also redesigned the two least informative figures: Figure 3 now compares how often B1, B2 and B4 include each structural component (Section 4.6), and Figure 4 shows how often each condition escalates at each risk level (Section 4.7).

---

We thank Reviewer 3 again for comments that helped us state the contribution of the paper more precisely.

---
---

## `main.tex` edits for Reviewer 3 (applied 18 Oct 2026)

| # | Where | What |
|---|---|---|
| R3-E1 | §4.3, after "…scores higher than B1 and B2." | Add one sentence on proxy scores and marker stuffing |
| R3-E2 | §5.4, end of the RQ2 paragraph | Add one sentence stating that the gain comes from the generator and fitness design |
| R3-E3 | §1, line 81 | Fix the ungrammatical sentence and the misplaced citation |
| R3-E4 | Five citations (lines 84, 100, 365, 551, 561) | Change " \cite" to "~\cite" |
| R3-E5 | Main text (41 words, headings included) | Make US spellings British, matching the rest of the paper; labels, citation keys and code names are untouched |
