## Reviewer 1

> **Note for the authors (delete before submission).** Each reply describes the manuscript *after* the edits in `reviewer1_edit_guide.md` are made. The edit numbers in brackets (e.g. [E5]) point to that guide. Text in `[square brackets]` is a placeholder for you to fill in. Do not submit a reply whose edit you have not made.

We sincerely thank Reviewer 1 for a careful and generous report. We found the comments fair and helpful. We also agree with the reviewer's overall reading of the paper: its contribution is a diagnostic case study, not an optimisation method. We have used that reading as the guiding principle for this revision. Our responses to each point follow.

---

**Comment 1.1.** *The claimed novelty lies in the interpretable genome, generator and evaluation scheme rather than in optimisation; the genetic algorithm is standard; there is no theoretical analysis of convergence, complexity or landscape properties; the work may be better suited to a medical-informatics journal.*

**Response.** We thank the reviewer for this careful assessment, and we agree with it. The genetic algorithm is standard, and the paper does not propose a new optimisation method. The Introduction and Conclusions now say this directly (Section 1; Section 6) [E2, E3, E14].

We also accept that the original manuscript described the properties of the search problem only in prose. We have therefore added a short subsection, Section 3.9, "Properties of the Search Space and Fitness Function" [E5], which states these properties formally:

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

Third, we are grateful to the reviewer for noticing that some sentences still read as a justification of the GA. We have reworded these passages in Sections 1, 3.8, 4.2, 4.3, 4.5, 4.9, 5.1 and 5.4 so that they describe what was measured, without implying an advantage for the GA [E3, E6–E11].

---

**Comment 1.3.** *The prompts are reconstructions from structured fields rather than real user messages, so conclusions about a "mental-health-oriented assistant" remain claims about behaviour on a synthetic corpus.*

**Response.** We thank the reviewer and fully agree. Our conclusions describe behaviour on a synthetic corpus, not on real dialogues. We have revised the wording so that this is clear wherever the system's behaviour is summarised: the Introduction and Conclusions now describe the system as a template-based response generator evaluated on synthetic prompts, rather than as a mental-health assistant in general (Section 1; Section 6) [E4, E14]. Section 3.2 describes how the prompts are constructed and explains that their phrasing and code-switching come from our phrase banks rather than from users. Section 5.7 states explicitly that, for this reason, the findings do not extend to authentic or multi-turn conversations.

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

**Response.** We thank the reviewer and agree. While revising, we found that many caveats were repeated across several sections. Each caveat is now stated once, in the section that reports the supporting evidence, and later repetitions have been replaced with short cross-references. We have also moved secondary statistical detail to the appendices. The main text (Introduction to Conclusions) now occupies 38 pages, compared with 44 in the original submission, and contains about 2,300 fewer words (14%), even though the revision adds the formal analysis requested in Comment 1.1 (Section 3.9) and the new experiments requested by the other reviewers. No findings or limitations have been removed; the only element dropped is a figure (empathy versus structure) whose content is already covered in the text [E15].

---

**Comment 1.6.** *In the abstract and keywords, the term "multi-objective optimisation" should be avoided unless qualified by the caveat that in fact one dominant component is being optimised.*

**Response.** We thank the reviewer and agree. We have removed the term from the keywords [E1], and the abstract describes the objective only as a scalar (weighted-sum) fitness function. Where the term appears in the main text it is now qualified. Section 1 describes the objective as a scalarised fitness [E2]. Section 5.5, now titled "Scalarised Fitness and the Structure-Dominant Optimum" [E12], explains that in practice a single component, structure, dominates the optimum. The term "multi-objective" is otherwise used only for Pareto-based methods proposed as future work.

---

**Reviewer 1's recommendations for continuing the work.** We are grateful for the clear list of requirements and summarise here how each has been addressed.

1. *Ethics approval or official exemption.* Please see our response to Comment 1.4.
2. *Clean comparison of B2–B4 with isolation of effects.* We added the one-factor ablation (Section 5.4, Table 10), which attributes the full B2–B4 difference to the structure weight.
3. *Revising the scorer to remove circularity and make safety genuinely controllable.* We agree with both concerns.
   - *Circularity.* We examined two possible sources. The first is the distress score used for mid-risk escalation. On checking the implementation, we found that this score is computed from the analyst-written theme fields rather than from the synthetic prompt. It therefore does not depend on wording chosen with the risk label known, and we have corrected the description in Sections 3.2 and 3.4.3 [E17]. We also quantified its influence. Only 1 of the 114 mid-risk prompts in the 400-prompt validation subsample falls in the band where the distress-gating gene changes escalation, and 110 of the 114 have a distress score of zero (Section 4.7) [E16]. Any remaining dependence can therefore affect at most one validation prompt. The second source is the use of the validation split during scorer development. We state this openly and describe the split as a combined development and validation set (Sections 3.2 and 5.7).
   - *Safety controllability.* In the present generator, safety behaviour is governed by the risk label rather than by an evolvable gene. We now describe this accurately (Sections 3.3 and 5.5). Redesigning the generator so that safety becomes genuinely evolvable would change the frozen scorer and, in effect, produce a different study. We have therefore listed it as the first priority for future work (Section 5.7). We hope the reviewer finds this an acceptable approach for the present paper.
4. *Shortening and restructuring.* Please see our response to Comment 1.5.
5. *Positioning as a diagnostic case study.* The title already described the work as diagnostic; the abstract, Introduction and Conclusions now present it consistently in this way (Section 1; Section 6).

We thank Reviewer 1 once again. The comments have substantially improved the clarity and honesty of the paper.
