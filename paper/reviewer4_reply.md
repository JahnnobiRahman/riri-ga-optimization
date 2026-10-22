## Reviewer 4

> **Note for the authors (delete before submission).** The `main.tex` edits listed at the end of this file (R4-E1 to R4-E5) have been applied. Section, table and figure numbers refer to the current compiled manuscript.

We thank Reviewer 4 for the helpful comments on presentation. They have made the paper clearer in several places. We also appreciate the questions about language models, which showed us that the original manuscript did not state clearly enough that the system uses none. Our responses follow.

---

**Comment 4.1.** *The abstract does not mainly indicate the main contents of the paper, such as the technical details and parameters. It should be rewritten.*

**Response.** We thank the reviewer for this suggestion and have rewritten the abstract [R4-E1]. It now states the main technical content explicitly, while staying within the journal's 200-word limit:
- the eight genes of the genome and what each controls;
- the GA configuration: population 100, 20 generations, tournament selection, uniform crossover, and 2,000 evaluations per run;
- the fitness weights for empathy, safety and structure (0.40/0.40/0.15) and the per-example safety penalties;
- the dataset (2,872 de-identified records rendered as synthetic prompts);
- the main quantitative results: the improvement over the fixed reference genome, the ablation, and the 30-seed comparison with random search.

---

**Comment 4.2.** *The novelty of this work lies less in evolutionary search being uniquely necessary to reach a given fitness level; however, the novelty of the study is not stated clearly. It should be rewritten.*

**Response.** Thank you for your comment; we agree that the earlier paragraph explained mainly what the novelty is *not*. We have rewritten it so that it states the novelty directly, as three elements (Section 1, the paragraph after the contribution list) [R4-E2]:
1. **An interpretable design for a low-resource setting.** In the genome, generator and scorer, every gene and score component maps to a named response behaviour, for a Bangla–Banglish–English setting that needs neither a GPU nor a language model.
2. **A trace-based diagnosis.** It uncovers four reward-design and generator failures that aggregate fitness concealed: question-only structural collapse, empathy-marker stuffing, a structure-marker coverage gap, and a response-truncation defect.
3. **A formal and empirical account of search behaviour.** It explains why different search methods behave identically in this space: a deterministic structure threshold that any sufficiently exploratory search can locate (Section 3.9).

---

**Comment 4.3.** *Figure 1 (overview of the EvoRiri pipeline): what is the input, and what are the outputs? The model is not clearly described.*

**Response.** We thank the reviewer for this question, and we have clarified the model as follows.
- **Input:** a user prompt with its risk label, $(x_i, r_i)$.
- **Output of the generation pipeline:** a response, $y_i = G(x_i, r_i; g)$, together with its automatic scores and fitness.
- **Output of the optimisation loop:** the evolved genome $g^\star$.

Figure 1 labels the input and the response output explicitly. We have revised the caption so that it names all of these, including the evolved genome, and states that no language model is used at any stage [R4-E3]. Appendix A.4 walks a single prompt through every stage of the pipeline, with the actual values at each step.

---

**Comment 4.4.** *The proposed model using LLMs should be drawn with its described details.*

**Response.** We are grateful for this comment, because it showed us that an important point was not stated clearly enough. **EvoRiri does not use a large language model at any stage.** Its responses are assembled from fixed, hand-written Bangla, Banglish and English phrase banks, and the genetic algorithm evolves only the parameters that decide which phrases are combined (Section 1; Section 3.4). Language models appear in the paper only as external, zero-shot comparison baselines (B6–B8; Section 4.4.1), and they play no part in the pipeline.

To prevent this misunderstanding, the generator box in Figure 1 is now labelled "Template composer (no LLM)", and the caption states that no language model is used at any stage [R4-E3]. Since there is no LLM component in the proposed model, Figure 1 shows the complete system.

---

**Comment 4.5.** *Table 7 (side-by-side comparison of B1) conveys little information about the prompts. It is better to rewrite the contents of the table.*

**Response.** We agree and thank the reviewer for this helpful suggestion. We have revised Table 7 [R4-E4]:
- Each response now lists the response components it contains (empathy, reflection, support, grounding, action, question, escalation).
- Each response now shows its automatic scores (empathy, safety, structure and per-example fitness), so that the reader can connect each qualitative difference to the quantitative results.
- The caption now explains that the prompts are excerpts of synthetic prompts and how the component labels and scores are computed; the risk level of each row is shown in the first column.

---

**Comment 4.6.** *The conclusion section should be rewritten, without the detailed content.*

**Response.** We thank the reviewer for this helpful suggestion. We have rewritten the Conclusions (Section 6) [R4-E5]. They now consist of three short paragraphs, covering what was built, what was learned, and the scope of the findings together with future work. The detailed numerical results, which are reported in the Results and Discussion, have been removed.

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
---

## `main.tex` edits for Reviewer 4 (applied 18 Oct 2026)

| # | Where | What |
|---|---|---|
| R4-E1 | Abstract | Rewrite with technical details and parameters (191 words) |
| R4-E2 | §1, novelty paragraph | State the novelty directly as three elements, and update "five random searches" to the 30-seed result |
| R4-E3 | Figure 1 | Label the generator box "Template composer (no LLM)"; extend the caption with the outputs and the no-LLM statement |
| R4-E4 | Table 7 | Add the components present and the automatic scores for each response; expand the caption |
| R4-E5 | §6 Conclusions | Rewrite as three short paragraphs without detailed numbers |
