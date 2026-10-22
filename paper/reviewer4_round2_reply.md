# Response to Reviewer 4 (Second Round)

We sincerely thank the reviewer for reading the revised manuscript again and for these further comments. We agree that the previous revision did not yet present the system architecture, its governing equations, or its relation to large language models in enough detail. We are grateful for the clear guidance, and we have revised the manuscript as described below. Section, figure, table and equation numbers refer to the revised manuscript.

---

**Comment 4.1.** *"The manuscript has only partially addressed the reviewer's comments. The proposed system architecture should be presented in place of Figure 1, currently entitled 'Overview of the EvoRiri Response-Generation and Optimisation Pipeline.' The revised figure should illustrate the system architecture, including the governing equation for each stage of the pipeline."*

**Response.** Thank you for this suggestion. As requested, we have replaced Figure 1 with a system-architecture diagram (Section 3.1, p. 7). The figure arranges the system into five layers, and every processing component now shows its governing equation:

1. **Data and risk layer:**
   - de-identified record, Eq. (5);
   - risk labelling, Eq. (6);
   - prompt construction, Eq. (4);
   - distress score, Eq. (11).
2. **Generation layer (no LLM):**
   - template generator, Eq. (2), with its empathy layer;
   - risk-aware escalation, Eq. (10);
   - structure regimes, Eq. (9);
   - response-part budget, Eq. (8).
3. **Evaluation layer (frozen scorer):**
   - empathy, safety and structure scores, Eqs. (12)–(14);
   - per-example fitness, Eq. (16), and global fitness, Eq. (17).
4. **Optimisation layer:**
   - genome, Eq. (7);
   - genetic algorithm, Eqs. (18)–(22);
   - objective, Eq. (3), which returns the evolved genome g⋆.
5. **Language-model interface:**
   - the implemented comparison path, Eq. (27);
   - a clearly marked proposed integration point, Eq. (28), described under Comment 4.2.

To make every stage governed by an explicit equation, we have added equations for the stages that the previous version described only in words:
- prompt construction, Eq. (4), Section 3.2;
- the structure regimes, Eq. (9), Section 3.4.2;
- the distress score, Eq. (11), Section 3.4.3;
- the genetic-algorithm operators (tournament selection, uniform crossover, mutation, weight renormalisation and the elitist update), Eqs. (18)–(22), Section 3.6.

These equations formalise the procedures already used in all reported experiments. No method or result has changed.

The caption describes each stage and its equation in turn, and the arrows show how data, responses, fitness values and genomes move between the components, including the loop in which the genome configures the generator.

---

**Comment 4.2.** *"Furthermore, the proposed model/system architecture should provide sufficient technical detail on how it integrates with large language models (LLMs), including the integration mechanisms and interactions between the system components."*

**Response.** We appreciate this comment very much and have addressed it in two ways.

**Interactions between the system components.** A new Table 2 (Section 3.1, p. 6) lists every component of Figure 1 with:
- its input;
- its output;
- its governing equation;
- the components it interacts with.

For example, the genetic algorithm receives F(g) from the fitness stage and sends new genomes to the generator, and the language-model interface sends its responses only to the scorer.

**Integration with LLMs.** We have added a new subsection, **Section 3.10, "Interface with Large Language Models"** (p. 21), which is also shown as layer (5) of Figure 1. It describes two integration points:

- **Implemented comparison interface (Eq. 27).** This is how the pre-trained Bangla models B6–B8 (mT5-small, BanglaT5, BanglaGPT) are connected to the system. Section 3.10 specifies:
  - how each model receives the synthetic prompt xᵢ built from the same record that the template generator receives, wrapped in a fixed instruction template (the template text is given in full);
  - the input truncation and the generation limit;
  - the decoding settings (beam search for the sequence-to-sequence models and greedy decoding for the causal model);
  - how the output is extracted;
  - that each response is scored by the same frozen scorer and fitness function, Eqs. (12)–(17).

  The interaction is one-directional: the language model receives no genome parameters and no feedback from the genetic algorithm, and its weights are not updated. Section 4.4.1 now points back to this description.

- **Proposed genome-conditioned LLM generator (Eq. 28), not evaluated in this study.** Here the language model would take the place of the template generator:
  - an instruction composer T_g maps the genes to explicit instructions;
  - a mapping κ(g) turns the response-part budget into decoding controls;
  - the escalation rule of Eq. (10) is applied deterministically after generation, so that crisis guidance does not depend on the language model.

  The scorer, the fitness function and the genetic algorithm remain unchanged. Section 3.10 explains the two reasons this design was not evaluated: the number of generations one run would need, and the poor zero-shot outputs observed for the available models. It is also listed as future work in Section 5.7.

Section 3.10 also states why the language model is kept outside the generation and search loop in the present system. This keeps crisis escalation deterministic, makes every response traceable to named genes, and allows the system to run without GPU infrastructure. We hope this makes the role of language models, and how they interact with each component, clear.

---

**Comment 4.3.** *"The technical contributions of this study should also be clearly articulated and discussed in the Introduction section."*

**Response.** Thank you for this helpful suggestion. We have rewritten the contributions paragraph in the Introduction (Section 1, pp. 2–3) as six labelled technical contributions. Each one states what was developed and where it appears in the manuscript:

- **C1:** an interpretable response policy, meaning the genome and the template generator (Sections 3.3–3.4, Figure 1).
- **C2:** a risk-aware scalar fitness (Section 3.5, Eqs. 12–17).
- **C3:** formal properties of the search problem (Section 3.9).
- **C4:** the language-model interface (Section 3.10).
- **C5:** a trace-based diagnostic method (Sections 5.3–5.4).
- **C6:** a reproducible evaluation protocol (Sections 4.5, 5.4 and 5.6).

The paragraph after the list, which clarifies what the study does and does not claim as novel, is kept so that the contributions are read in the right scope.

---

**Additional improvements.** We have also taken this opportunity to improve the presentation of the tables. All tables now use a uniform font size and row spacing. Table 1 has been rebalanced to fit the text width. Table 6 now uses self-explanatory condition names (for example, "B4: GA optimised"), with the standard deviations of the random-genome baseline on their own row. While formalising the genetic algorithm, we also corrected one sentence in Section 3.7 so that it matches the implementation: the initial population consists of the four seed genomes together with genomes drawn uniformly at random. No reported values have changed.

We thank the reviewer once again for the time and care given to our manuscript. These comments have made the presentation of the system considerably clearer, and we hope the revised version addresses them satisfactorily.
