# Response to Reviewers

**Manuscript:** EvoRiri: Interpretable Evolutionary Search for Diagnosing Reward-Design Failures in a Bangla Mental-Health Assistant
**Journal:** *Mathematics* (MDPI)

---

Dear Editor and Reviewers,

We thank the four reviewers for their careful reading of our manuscript. Their comments, several of which agree with each other, have sharpened how the work is positioned, and especially how its claims about evolutionary search are qualified. Below we answer each comment in turn and say where in the revised manuscript the corresponding material appears.

One theme runs through several reports (Comments 1.1, 1.2, 2.1, 2.2, 3.1 and 4.2), so we address it once here. **We do not claim that the genetic algorithm outperforms other search methods.** The paper's contribution is an interpretable genome–generator–scorer framework, together with the trace-level and controlled analyses it makes possible. Those analyses show *why* the measured gains occur. In response to the reviewers, we have also tested the question directly: over 30 paired seeds, equal-budget random search is statistically equivalent to the GA, and Section 3.9 explains formally why. We have made this positioning explicit throughout the Abstract, Introduction, Discussion and Conclusions.

The revision also includes new analyses requested by the reviewers:
- a formal subsection on the properties of the search space (Section 3.9);
- 30-seed significance tests and a 30-seed GA–random-search comparison with seeded, deterministic evaluation (Sections 4.5 and 5.4);
- a recalibrated-threshold check and a pruned-genome check (Section 3.9);
- a full re-run with all records with a self-reported age of 13–17 years removed (Section 5.6, Table 11).

---

## Reviewer 1

We sincerely thank Reviewer 1 for a careful and generous report. We found the comments fair and helpful. We also agree with the reviewer's overall reading of the paper: its contribution is a diagnostic case study, not an optimisation method. We have used that reading as the guiding principle for this revision. Our responses to each point follow.

---

**Comment 1.1.** *The claimed novelty lies in the interpretable genome, generator and evaluation scheme rather than in optimisation; the genetic algorithm is standard; there is no theoretical analysis of convergence, complexity or landscape properties; the work may be better suited to a medical-informatics journal.*

**Response.** We thank the reviewer for this careful assessment, and we agree with it. The genetic algorithm is standard, and the paper does not propose a new optimisation method. The Introduction and Conclusions now say this directly (Section 1; Section 6).

We also accept that the original manuscript described the properties of the search problem only in prose. We have therefore added a short subsection, Section 3.9, "Properties of the Search Space and Fitness Function", which states these properties formally:

- **Proposition 1.** The fitness function does not depend on the two reserved genes ($\theta_{\mathrm{mid}}, \theta_{\mathrm{high}}$). The effective search space is therefore smaller than the nominal eight-gene genome.
- **Proposition 2.** The variation operators act on each gene independently. As a result, the reserved genes do not change the search dynamics of the active genes.
- **Proposition 3.** The mid-risk safety penalty adds the same constant to every genome over a fixed evaluation set. It therefore cannot change which genome is selected.
- **Proposition 4.** The structure-dependent part of the fitness is piecewise in the normalised structure weight, with a deterministic plateau. This explains why grid, random and evolutionary search all reach the same region.

The subsection also reports the evaluation cost of the search. We have been careful not to present these statements as convergence results. They are modest properties of the landscape, but we hope they make the mathematical content of the study clearer and give a formal basis for the paper's main empirical finding.

We fully understand the reviewer's concern about fit with the journal. We would, of course, defer to the Editor's judgement on this question.

---

**Comment 1.2.** *B1 contains a truncation defect, so the B1–B4 comparison conflates the defect with the effect of optimisation; B2–B4 also differ in several parameters, so the causal contribution of evolutionary search is not isolated; in places the conclusions still sound like a justification of the GA's advantage.*

**Response.** We thank the reviewer for this point, and we agree with it. We have made two analytical changes and one change in wording.

First, to separate the truncation defect from the effect of optimisation, we re-evaluated B1 with only the response-part budget changed ("B1-fixed"; Section 5.4, Table 9). Removing the truncation alone accounts for most of B1's safety deficit (0.475 to 0.905).

Second, to isolate the B2–B4 difference, we moved one gene at a time between the two genomes (Section 5.4, Table 10). The structure weight $w_c$ alone reproduces the entire difference. The distress-gating gene, the template index and the $w_e{:}w_s$ split have no measurable effect. A hand-set value of $w_c$ in the plateau gives the same result, so we no longer attribute the improvement to evolutionary search. We also note that this one-at-a-time ablation does not test interactions between genes (Section 5.7).

Third, we are grateful to the reviewer for noticing that some sentences still read as a justification of the GA. We have reworded these passages in Sections 1, 3.8, 4.2, 4.3, 4.5, 4.9, 5.1 and 5.4 so that they describe what was measured, without implying an advantage for the GA.

---

**Comment 1.3.** *The prompts are reconstructions from structured fields rather than real user messages, so conclusions about a "mental-health-oriented assistant" remain claims about behaviour on a synthetic corpus.*

**Response.** We thank the reviewer and fully agree. Our conclusions describe behaviour on a synthetic corpus, not on real dialogues. We have revised the wording so that this is clear wherever the system's behaviour is summarised: the Introduction and Conclusions now describe the system as a template-based response generator evaluated on synthetic prompts, rather than as a mental-health assistant in general (Section 1; Section 6). Section 3.2 describes how the prompts are constructed and explains that their phrasing and code-switching come from our phrase banks rather than from users. Section 5.7 states explicitly that, for this reason, the findings do not extend to authentic or multi-turn conversations.

---

**Comment 1.4.** *No approval from an independent ethics committee or IRB was obtained; the data relate to mental health, were collected via an app, and 14.7% of records have a self-reported age of 13–17 years.*

**Response.** We thank the reviewer for raising this concern, which we take seriously. We did not seek independent ethics approval for this secondary analysis of de-identified data. The research use of the data was authorised by the data controller, and in our setting secondary analyses of this kind are not routinely submitted for independent review; we nonetheless recognise that such review would have been preferable. In the revised manuscript we therefore:
- state the absence of independent approval clearly in the Institutional Review Board Statement and in Section 5.6;
- describe the safeguards in place: de-identification, electronic consent, one record per user, and prompts reconstructed synthetically, so that no user text is reproduced;
- report a robustness check in which all 422 records with a self-reported age of 13–17 years were removed, the six GA runs repeated from scratch, and the main conditions re-evaluated; every comparison is unchanged (Section 5.6, Table 11).

We would also be glad to report the analysis without these records as the main result if the reviewer or Editor prefers.

We recognise that these measures do not replace independent ethical review, and we respectfully leave the question of whether this is acceptable to the Editor.

---

**Comment 1.5.** *The manuscript is overloaded with repetitions and caveats; it could be shortened by 30–40% without loss of content.*

**Response.** We thank the reviewer and agree. While revising, we found that many caveats were repeated across several sections. Each caveat is now stated once, in the section that reports the supporting evidence, and later repetitions have been replaced with short cross-references. We have also moved secondary statistical detail to the appendices. The main text (Introduction to Conclusions) now occupies 38 pages, compared with 44 in the original submission, and contains about 2,300 fewer words (14%), even though the revision adds the formal analysis requested in Comment 1.1 (Section 3.9) and the new experiments requested by the other reviewers. No findings or limitations have been removed; the only element dropped is a figure (empathy versus structure) whose content is already covered in the text.

---

**Comment 1.6.** *In the abstract and keywords, the term "multi-objective optimisation" should be avoided unless qualified by the caveat that in fact one dominant component is being optimised.*

**Response.** We thank the reviewer and agree. We have removed the term from the keywords, and the abstract describes the objective only as a scalar (weighted-sum) fitness function. Where the term appears in the main text it is now qualified. Section 1 describes the objective as a scalarised fitness. Section 5.5, now titled "Scalarised Fitness and the Structure-Dominant Optimum", explains that in practice a single component, structure, dominates the optimum. The term "multi-objective" is otherwise used only for Pareto-based methods proposed as future work.

---

**Reviewer 1's recommendations for continuing the work.** We are grateful for the clear list of requirements and summarise here how each has been addressed.

1. *Ethics approval or official exemption.* Please see our response to Comment 1.4.
2. *Clean comparison of B2–B4 with isolation of effects.* We added the one-factor ablation (Section 5.4, Table 10), which attributes the full B2–B4 difference to the structure weight.
3. *Revising the scorer to remove circularity and make safety genuinely controllable.* We agree with both concerns.
   - *Circularity.* We examined two possible sources. The first is the distress score used for mid-risk escalation. On checking the implementation, we found that this score is computed from the analyst-written theme fields rather than from the synthetic prompt. It therefore does not depend on wording chosen with the risk label known, and we have corrected the description in Sections 3.2 and 3.4.3. We also quantified its influence. Only 1 of the 114 mid-risk prompts in the 400-prompt validation subsample falls in the band where the distress-gating gene changes escalation, and 110 of the 114 have a distress score of zero (Section 4.7). Any remaining dependence can therefore affect at most one validation prompt. The second source is the use of the validation split during scorer development. We state this openly and describe the split as a combined development and validation set (Sections 3.2 and 5.7).
   - *Safety controllability.* In the present generator, safety behaviour is governed by the risk label rather than by an evolvable gene. We now describe this accurately (Sections 3.3 and 5.5). Redesigning the generator so that safety becomes genuinely evolvable would change the frozen scorer and, in effect, produce a different study. We have therefore listed it as the first priority for future work (Section 5.7). We hope the reviewer finds this an acceptable approach for the present paper.
4. *Shortening and restructuring.* Please see our response to Comment 1.5.
5. *Positioning as a diagnostic case study.* The title already described the work as diagnostic; the abstract, Introduction and Conclusions now present it consistently in this way (Section 1; Section 6).

We thank Reviewer 1 once again. The comments have substantially improved the clarity and honesty of the paper.

---

## Reviewer 2

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

We have therefore repeated the comparison with **30 paired seeds** under a common design (Section 5.4):
- For each seed, the GA and an equal-budget random search (2,000 draws from the same genome space) both selected on the same 600-prompt sample of the optimisation set.
- The selected genomes were then scored on the 400-prompt validation subsample, with the same generation seed for both methods.
- Neither method saw the validation prompts during selection.

The results were as follows:
- The two methods selected different genomes, but all of them lie on the structure plateau.
- On **28 of the 30 seeds**, they received identical validation scores.
- Mean validation fitness was 0.7000 for both methods. The paired difference is 1.7 × 10⁻⁵, with a 90% CI of [−2.9 × 10⁻⁵, 6.4 × 10⁻⁵].
- A paired equivalence test (TOST) establishes **equivalence at the margin ε = 0.01** (p < 10⁻⁵⁰).
- The GA reached higher fitness on its own selection sample (0.710 versus 0.705), but this did not carry over to validation.

We therefore report, in answer to the reviewer's question, that we did not find an empirical benefit of evolutionary search over equal-budget random sampling in this search space, as Proposition 4 predicts. We have updated the Abstract, Section 5.4, Section 5.7 and the Conclusions accordingly.

---

**Comment 2.3.** *There seem to be some flaws in the genome parameters (dead, passive, and weakly identified). Inactive or dummy parameters may be pruned to reduce the artificial search-space dimension and avoid misleading parameter-drift interpretations.*

**Response.** We thank the reviewer for this careful observation, and we agree that these genes needed a clearer treatment.

The revised manuscript states their status formally. Proposition 1 (Section 3.9) shows that the fitness does not depend on θ_mid and θ_high, and that the effective search space is therefore smaller than the nominal genome. Proposition 2 shows that, because crossover and mutation act on each gene independently, the presence of these genes does not change the search dynamics of the active genes. Any "drift" in them is therefore neutral and is not interpreted anywhere in the paper. We also describe w_s as a renormalisation participant only (Section 3.3; Appendix B.1) and γ as weakly identified (Section 3.4.3; Section 4.7).

To confirm Proposition 2 empirically, we **ran the GA with θ_mid and θ_high removed** (frozen at constant values) for five seeds. The pruned runs gave **exactly the same validation fitness** as the full-genome runs with the same seeds (0.6949–0.7027), although the selected genomes differ in their other genes (Section 3.9).

We have kept the two genes in the reported genome because they are the intended interface for graded escalation in future work, and we now show explicitly that keeping them has no effect on the results. If the reviewer prefers, we would be glad to remove them from the genome definition altogether.

---

**Comment 2.4.** *In Eq. 10, mid-risk safety scores are capped at 0.85, yet Eq. 13 applies a −0.15 penalty whenever safety falls below 0.94. The soft threshold should be recalibrated to properly evaluate mid-risk escalation quality.*

**Response.** We thank the reviewer for spotting this; we agree that the threshold is miscalibrated for mid-risk prompts. On closer analysis, we found that it does not affect which genomes are selected. Because every mid-risk response scores either 0.60 or 0.85, the penalty applies to all mid-risk examples whatever the genome. Over a fixed evaluation set it therefore subtracts the same constant from every genome, and it cannot change their ranking (Proposition 3, Section 3.9). Escalation quality for mid-risk prompts is still rewarded, through the base safety term (0.40 × (0.85 − 0.60) = 0.10 per example).

To check this empirically, we **re-scored the 30 GA genomes and both baselines with the threshold recalibrated to 0.80**, so that escalated mid-risk responses are no longer penalised. Fitness rises slightly: by 0.007–0.014 for the GA, 0.008–0.012 for B2 and 0.002–0.005 for B1. The ranking of the GA genomes is preserved (Spearman ρ = 0.94), and none of the comparisons reported in the paper changes.

Because recalibrating the scorer would alter every reported value without changing any conclusion, we have kept the frozen scorer for the main analysis and report the recalibrated result alongside it (Section 3.9). We hope this approach is acceptable to the reviewer.

---

**Comment 2.5.** *A small amount of noise obscures small performance differences between algorithms. Fix random-generation seeds during evaluation to make fitness scoring deterministic, allowing clear separation between search methods.*

**Response.** We are grateful for this suggestion, which led directly to the clearest result in the revision.

All new evaluations use a fixed generation seed per run, with the same seed for every condition compared (common random numbers). This covers the 30-seed significance analysis, the 30-seed GA–random-search comparison and the age-record robustness check (Section 3.5.6). Under seeded evaluation, fitness is deterministic: re-running a seed reproduces its genome and score exactly, and the first five of the 30 GA runs reproduce the archived genomes of Table 6 exactly.

As the reviewer anticipated, seeding allows a clear separation between search methods. In this case it shows that GA and random search reach identical scores on 28 of 30 seeds (see our response to Comment 2.2).

---

**Comment 2.6.** *Consider renaming `memory_window` to `response_part_budget` in the manuscript to avoid misunderstandings about the system's operational scope.*

**Response.** Thank you; we agree and have done this. The gene is now called the *response-part budget* $m$ throughout the manuscript. The implementation field name `memory_window` is retained only for code traceability (Section 3.3, Section 3.4.1 and Table 2), and both sections state explicitly that it is not a conversational context window, since the generator is single-turn and keeps no dialogue history.

---

**Comment 2.7.** *To strengthen statistical significance testing, experiments may be expanded to 20–30 independent seeds per condition.*

**Response.** We thank the reviewer for this suggestion and have **expanded the main comparison to 30 independent seeds** (Section 4.5). All 30 GA genomes scored above both fixed baselines:

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

## Reviewer 3

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

The rationale for the fixed weights is given in Section 3.5.5. We have added a sentence to Section 5.4 stating plainly that the measured improvement comes from the design of the generator and the fitness function, not from the search method.

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

**Response.** We are grateful to the reviewer for this important observation, and we fully agree. In the revised manuscript, we now acknowledge this limitation at the point where the optimised results are first presented: Section 4.3 notes that the automatic scores are rule-based proxies and, with reference to the marker-stuffing case, that a higher automatic score does not necessarily indicate a better response.

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
- **Proofreading.** We have proofread the whole manuscript. Corrections include spacing around citations and punctuation, a missing phrase in Section 5.2, a duplicated word, and an ungrammatical sentence in the Introduction.
- **Spelling.** We have made the spelling consistently British throughout; the original mixed "optimisation" and "optimization", for example.
- **Figure quality.** We have regenerated all data figures as vector graphics in one consistent style, using the journal's typeface, a colour-blind-safe palette and labels sized for print. We have also redesigned the two least informative figures: Figure 3 now compares how often B1, B2 and B4 include each structural component (Section 4.6), and Figure 4 shows how often each condition escalates at each risk level (Section 4.7).

---

We thank Reviewer 3 again for comments that helped us state the contribution of the paper more precisely.

---

## Reviewer 4

We thank Reviewer 4 for the helpful comments on presentation. They have made the paper clearer in several places. We also appreciate the questions about language models, which showed us that the original manuscript did not state clearly enough that the system uses none. Our responses follow.

---

**Comment 4.1.** *The abstract does not mainly indicate the main contents of the paper, such as the technical details and parameters. It should be rewritten.*

**Response.** We thank the reviewer for this suggestion and have rewritten the abstract. It now states the main technical content explicitly, while staying within the journal's 200-word limit:
- the eight genes of the genome and what each controls;
- the GA configuration: population 100, 20 generations, tournament selection, uniform crossover, and 2,000 evaluations per run;
- the fitness weights for empathy, safety and structure (0.40/0.40/0.15) and the per-example safety penalties;
- the dataset (2,872 de-identified records rendered as synthetic prompts);
- the main quantitative results: the improvement over the fixed reference genome, the ablation, and the 30-seed comparison with random search.

---

**Comment 4.2.** *The novelty of this work lies less in evolutionary search being uniquely necessary to reach a given fitness level; however, the novelty of the study is not stated clearly. It should be rewritten.*

**Response.** Thank you for your comment; we agree that the earlier paragraph explained mainly what the novelty is *not*. We have rewritten it so that it states the novelty directly, as three elements (Section 1, the paragraph after the contribution list):
1. **An interpretable design for a low-resource setting.** In the genome, generator and scorer, every gene and score component maps to a named response behaviour, for a Bangla–Banglish–English setting that needs neither a GPU nor a language model.
2. **A trace-based diagnosis.** It uncovers four reward-design and generator failures that aggregate fitness concealed: question-only structural collapse, empathy-marker stuffing, a structure-marker coverage gap, and a response-truncation defect.
3. **A formal and empirical account of search behaviour.** It explains why different search methods behave identically in this space: a deterministic structure threshold that any sufficiently exploratory search can locate (Section 3.9).

---

**Comment 4.3.** *Figure 1 (overview of the EvoRiri pipeline): what is the input, and what are the outputs? The model is not clearly described.*

**Response.** We thank the reviewer for this question, and we have clarified the model as follows.
- **Input:** a user prompt with its risk label, $(x_i, r_i)$.
- **Output of the generation pipeline:** a response, $y_i = G(x_i, r_i; g)$, together with its automatic scores and fitness.
- **Output of the optimisation loop:** the evolved genome $g^\star$.

Figure 1 labels the input and the response output explicitly. We have revised the caption so that it names all of these, including the evolved genome, and states that no language model is used at any stage. Appendix A.4 walks a single prompt through every stage of the pipeline, with the actual values at each step.

---

**Comment 4.4.** *The proposed model using LLMs should be drawn with its described details.*

**Response.** We are grateful for this comment, because it showed us that an important point was not stated clearly enough. **EvoRiri does not use a large language model at any stage.** Its responses are assembled from fixed, hand-written Bangla, Banglish and English phrase banks, and the genetic algorithm evolves only the parameters that decide which phrases are combined (Section 1; Section 3.4). Language models appear in the paper only as external, zero-shot comparison baselines (B6–B8; Section 4.4.1), and they play no part in the pipeline.

To prevent this misunderstanding, the generator box in Figure 1 is now labelled "Template composer (no LLM)", and the caption states that no language model is used at any stage. Since there is no LLM component in the proposed model, Figure 1 shows the complete system.

---

**Comment 4.5.** *Table 7 (side-by-side comparison of B1) conveys little information about the prompts. It is better to rewrite the contents of the table.*

**Response.** We agree and thank the reviewer for this helpful suggestion. We have revised Table 7:
- Each response now lists the response components it contains (empathy, reflection, support, grounding, action, question, escalation).
- Each response now shows its automatic scores (empathy, safety, structure and per-example fitness), so that the reader can connect each qualitative difference to the quantitative results.
- The caption now explains that the prompts are excerpts of synthetic prompts and how the component labels and scores are computed; the risk level of each row is shown in the first column.

---

**Comment 4.6.** *The conclusion section should be rewritten, without the detailed content.*

**Response.** We thank the reviewer for this helpful suggestion. We have rewritten the Conclusions (Section 6). They now consist of three short paragraphs, covering what was built, what was learned, and the scope of the findings together with future work. The detailed numerical results, which are reported in the Results and Discussion, have been removed.

---

**Question 4.7.** *Why does the proposed model integrate LLMs and the GA? Please clarify.*

**Response.** Thank you for the question. The proposed model does not integrate an LLM with the GA. The GA searches the parameters of a template-based generator, and no language model is called during generation, scoring or search (Sections 1 and 3.4). We chose this design deliberately, for two reasons:
- **Low resources.** The system runs without GPU infrastructure or API access.
- **Interpretability.** Every behaviour can be traced to a named parameter, which is what made the diagnosis of reward-design failures possible (Section 5.3).

The work on combining GAs with LLMs reviewed in Section 2.1 (for example GenDLN, GAAPO and MLES) is discussed only to position our approach. Our approach evolves an interpretable response policy rather than prompts or model weights.

---

**Question 4.8.** *What kind of LLM is used in the implementation in practice? Please clarify.*

**Response.** Thank you for this question. No LLM is used in EvoRiri itself. For the external zero-shot comparison baselines, we evaluated three pre-trained Bangla-capable models without fine-tuning (Section 4.4.1; Table 5):
- **mT5-small** (`google/mt5-small`, B6);
- **BanglaT5** (`csebuetnlp/banglat5`, B7);
- **BanglaGPT** (`shahidul034/BanglaGPT`, B8).

They are included only to characterise how general-purpose models behave on this task without adaptation, not as competitive systems.

---

We thank Reviewer 4 again for these comments, which have made the paper easier to read.

---

We thank the editor and the reviewers once more for their time and expertise. We believe the revised manuscript gives a clearer, more carefully scoped and better-supported account of what the framework does and does not show.

Sincerely,
Jahnnobi Rahman and Mir Md. Jahangir Kabir
