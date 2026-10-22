# Reviewer 1: Edit Guide for `main.tex`

This guide lists every manuscript change the Reviewer 1 reply ([reviewer1_reply.md](reviewer1_reply.md)) depends on. Line numbers refer to `main.tex` as of 17 Oct 2026, before any edits. Edit from the **bottom of the file up** (highest line numbers first) so that the earlier line numbers stay valid while you work.

| # | Section | Lines | Reviewer point | Type |
|---|---|---|---|---|
| E1 | Keywords | 70 | 1.6 | wording |
| E2 | §1 Introduction, methodological paragraph | 126–133 | 1.6, 1.1 | wording |
| E3 | §1 Novelty paragraph, last sentences | 175–181 | 1.2 | soften |
| E4 | §1 "In this article we introduce…" | 118–119 | 1.3 | wording |
| E5 | **New §3.9** (insert before `\section{Results}`) | after 1229 | 1.1 | **new content** |
| E6 | §3.8, end | 1223–1229 | 1.2 | soften |
| E7 | §4.3 Convergence | 1388–1392 | 1.2 | soften |
| E8 | §4.5 Overall Performance | 1564–1567 | 1.2 | soften |
| E9 | §4.7 Significance | 1666–1668, 1738–1743 | 1.2 | soften |
| E10 | §5.1 Seeded Initialization | 2160–2163 | 1.2 | soften |
| E11 | §5.4 Ablation paragraph | 2404 | 1.2 | **important** soften |
| E12 | §5.5 title and one sentence | 2436, 2470–2471 | 1.6 | wording |
| E13 | §5.6, IRB statement, Data Availability | 2570–2581, 2783–2804, 2815–2825 | 1.4 | depends on ethics outcome |
| E14 | §6 Conclusions, first paragraph | 2742–2747 | 1.1, 1.3 | wording |
| E15 | Shortening (several sections) | see list | 1.5 | cuts |
| E16 | §4.9 Risk-Aware Safety | 1792–1799 | 1.R3 (circularity) | numbers filled in |
| E17 | §3.2 and §3.4.3, distress-score description | 511–522, 791, 798 | 1.R3 (circularity) | **correction** |

---

## E1 · Keywords (line 70) · Comment 1.6

**Current**
```latex
\keyword{evolutionary algorithms; genetic algorithms; mental-health chatbots; empathy; safety; structure-dominant multi-objective optimisation; conversational agents; Bangla; risk-aware AI}
```
**Replace with**
```latex
\keyword{evolutionary algorithms; genetic algorithms; reward design; scalarised fitness; fitness landscape; mental-health chatbots; conversational agents; Bangla; risk-aware AI}
```
"Fitness landscape" also signals the new §3.9 to the *Mathematics* readership.

---

## E2 · §1, methodological paragraph (lines 126–133) · Comments 1.6, 1.1

**Current** (from "From a methodological perspective…" to "…multi-objective trade-off.")
```latex
From a methodological perspective, the work studies
mixed continuous--discrete, non-differentiable genetic optimisation over an
interpretable policy space, with a scalarized multi-objective fitness function
and sensitivity analyses across dataset and population size. As
Section~\ref{sec:balance-discussion} shows, the discovered optimum is
structure-dominant rather than balanced across objectives, so this
scalarization should not be read as achieving a smooth multi-objective
trade-off.
```
**Replace with**
```latex
From a methodological perspective, the work studies a mixed
continuous--discrete, non-differentiable search space over an interpretable
policy, optimised against a single scalar (weighted-sum) fitness function.
Section~\ref{sec:landscape} states several properties of this search space
formally, and Section~\ref{sec:balance-discussion} shows that the resulting
optimum is dominated by one component, structure, rather than balanced across
empathy, safety, and structure. The genetic algorithm itself is standard; the
study does not propose a new optimisation method.
```

---

## E3 · §1, end of the novelty paragraph (lines 175–181) · Comment 1.2

The current ending speculates that guided search "may show a clearer advantage". A reviewer may read that as advocacy.

**Current**
```latex
interpretable policy space. This equivalence between search strategies is
specific to a genome space with a deterministic structure threshold that
any sufficiently exploratory search can locate (Section~\ref{sec:progressive-structure});
genome spaces or fitness designs without such an easily-found shortcut,
where the interaction between genes is less separable, may show a
clearer advantage for guided evolutionary search over undirected
alternatives, and testing this is a natural direction for future work.
```
**Replace with**
```latex
interpretable policy space. The absence of a resolvable difference between
search strategies is explained by a deterministic structure threshold that
any sufficiently exploratory search can locate
(Sections~\ref{sec:progressive-structure} and~\ref{sec:landscape}). Whether
the same holds in genome spaces without such a threshold is an open question
that the present study does not address.
```

---

## E4 · §1, "In this article we introduce…" (lines 118–119) · Comment 1.3

**Current**
```latex
In this article we introduce a Genetic Algorithm (GA)-based risk-aware framework for mental-health-oriented assistants designed for Bangla-speaking
users.
```
**Replace with**
```latex
In this article we study a template-based, risk-aware response generator for
Bangla-speaking users, whose parameters are searched with a genetic algorithm
(GA) and which we evaluate on synthetic prompts reconstructed from
de-identified records (Section~\ref{sec:methods}).
```

**Optional title change**, which makes the framing clear from the first line:
> EvoRiri: Interpretable Evolutionary Search for Diagnosing Reward-Design Failures in a **Template-Based** Bangla Mental-Health **Response Generator**

---

## E5 · NEW §3.9 "Properties of the Search Space and Fitness Function" · Comment 1.1

**Where:** insert after line 1229 (the end of §3.8, "…do not claim this to be a global optimum.") and **before** line 1231 (`\section{Results}`).

This is the main answer to "no theoretical analysis". Every statement follows from equations already in the paper, and I checked the code: `src/ga/operators.py` applies crossover and mutation gene by gene, and nothing reads `theta_mid` or `theta_high`. The MDPI class provides the `Proposition` environment (capital P).

```latex
\subsection{Properties of the Search Space and Fitness Function}
\label{sec:landscape}

This subsection states four properties of the search problem that follow
directly from the generator and fitness definitions above. They are not
convergence results; their purpose is to make explicit the structure of the
landscape that the empirical comparisons in Section~\ref{sec:interp-baseline}
later reflect. Throughout, $\mathcal{I}$ is a fixed evaluation set and
$\tilde w_k = w_k/(w_e+w_s+w_c)$, $k\in\{e,s,c\}$, denotes a renormalised weight.

\begin{Proposition}[Neutral genes]\label{prop:neutral}
$F(g)$ is invariant to $\theta_{\mathrm{mid}}$ and $\theta_{\mathrm{high}}$.
Consequently, the effective search space is
$\Delta^{2}\times[0,0.2]\times\{0,1,2\}\times\{0,1\}$, where $\Delta^{2}$ is the
2-simplex of renormalised weights $(\tilde w_e,\tilde w_s,\tilde w_c)$, the
interval is the range of $\gamma$, $\{0,1,2\}$ indexes the template $d$, and
$\{0,1\}$ is the indicator $\mathbb{I}\{m\le256\}$, the only behaviourally
active distinction of the response-part budget (Eq.~\eqref{eq:part-budget}).
\end{Proposition}
\begin{proof}
Neither the generator $G$ (Section~\ref{sec:generator}) nor any term of
$f_i$ (Eq.~\eqref{eq:per-example-fitness}) reads $\theta_{\mathrm{mid}}$ or
$\theta_{\mathrm{high}}$; the weights enter $G$ only through their
renormalised values; and $m\in\{512,768,1024\}$ produce identical outputs.
\end{proof}

\begin{Proposition}[Neutral genes do not alter the search on active genes]\label{prop:dynamics}
Let $A_t$ denote the active genes of the population at generation $t$. Under
tournament selection on $F$, uniform crossover, and per-gene mutation
(Section~\ref{sec:ga-config}), the law of $(A_t)_{t\ge0}$ is the same whether
or not $\theta_{\mathrm{mid}}$ and $\theta_{\mathrm{high}}$ are present in the
genome. The same holds for uniform random search.
\end{Proposition}
\begin{proof}
Selection depends on the population only through $F$, which by
Proposition~\ref{prop:neutral} depends only on active genes. Uniform crossover
draws each child gene independently of the others, and mutation perturbs each
gene independently, so the active genes of an offspring are conditionally
independent of the neutral genes given the parents' active genes.
Renormalisation involves only $w_e,w_s,w_c$.
\end{proof}

\begin{Proposition}[A selection-invariant penalty]\label{prop:offset}
For every mid-risk example the soft-threshold indicator
$\mathbb{I}\{S_i<0.94\}$ in Eq.~\eqref{eq:per-example-fitness} equals~1 for
all genomes. Hence, over a fixed $\mathcal{I}$ containing $n_{\mathrm{mid}}$
mid-risk examples,
\[
  F(g) = F^{\circ}(g) - 0.15\,\frac{n_{\mathrm{mid}}}{|\mathcal{I}|},
\]
where $F^{\circ}$ omits that indicator for mid-risk examples, and the second
term does not depend on $g$. The maximiser of $F$, the ranking of genomes, and
all paired differences $F(g)-F(g')$ are therefore unaffected by this term.
\end{Proposition}
\begin{proof}
By Eq.~\eqref{eq:safety}, $S_i\in\{0.60,0.85\}$ whenever $r_i=\mathrm{mid}$,
and both values are below $0.94$.
\end{proof}
\noindent Escalation quality for mid-risk prompts is still distinguished, but
through the base term: $B\,(0.85-0.60)=0.10$ per example.

\begin{Proposition}[Piecewise structure contribution]\label{prop:plateau}
Let $\phi(C_i)=C\,C_i-0.10\,\max(0,0.70-C_i)/0.70+0.05\,C_i+0.05\min(C_i,0.8)$
denote the structure-dependent terms of $f_i$. If $\tilde w_c\ge0.55$ and all
three inserted components are detected, then $C_i=1$ and
$\phi(C_i)=0.24$ for every example. If $\tilde w_c<0.25$ and no component is
detected, then $C_i=0$ and $\phi(C_i)=-0.10$. The structure-dependent part of
$F$ is therefore constant on each of these two regions, with a gap of $0.34$
per example between them.
\end{Proposition}
\begin{proof}
Direct substitution into Eqs.~\eqref{eq:structure}
and~\eqref{eq:per-example-fitness} with $C=0.15$, using the regimes of
Section~\ref{sec:progressive-structure}.
\end{proof}
\noindent Proposition~\ref{prop:plateau} explains the main empirical
observation of Section~\ref{sec:interp-baseline}: any search that samples a
point with $\tilde w_c\ge0.55$ reaches the structure plateau, and on the
plateau the remaining variation in $F$ can come only from the other
components. The detection condition is an empirical one, verified for the
reported genome in Section~\ref{sec:structure-analysis}; the keyword detector
can occasionally over- or under-count components
(Section~\ref{sec:interp-baseline}).

\emph{Evaluation cost.} Each fitness evaluation generates and scores
$|\mathcal{I}|$ responses, each at a cost bounded by a constant (a bounded
number of response parts and fixed marker lists). One GA run therefore costs
$\mathcal{O}(P\,T\,|\mathcal{I}|)$ generator-and-scorer calls, i.e.\
$100\times20\times600=1.2\times10^{6}$ in the main configuration. The
equal-budget random search of Section~\ref{sec:interp-baseline} has the same
order of cost. Observed wall-clock times range from 64\,s to 882\,s per run
across the population sizes tested, on CPU only
(Appendix~\ref{app:population-tost}).
```

*Please check the arithmetic yourself.* For $C_i=1$: $0.15 + 0 + 0.05 + 0.04 = 0.24$. For $C_i=0$: $0 - 0.10 + 0 + 0 = -0.10$.

Optional cross-references afterwards:
- §3.4.3, near line 828: append "(see also Proposition~\ref{prop:neutral})".
- §3.5.2, end of the paragraph at line 902: append "As Proposition~\ref{prop:offset} shows, this penalty shifts all genomes equally and does not affect selection."
- §4.4, line 1413: you can replace the long parenthetical with "(Proposition~\ref{prop:neutral})".

---

## E6 · §3.8, end (lines 1223–1229) · Comment 1.2

**Current**
```latex
This reflects the fitness landscape: safety is largely ensured by the fixed
escalation rule and safety penalty terms, freeing the GA to focus its
search on structural completeness. The result aligns with the large structure gains observed in
Table~\ref{tab:baseline-optimized} and is consistent with balanced initialisation
($g_\mathrm{bal}$, $w_c = 0.34$) substantially underestimating $w_c$'s value
within this fitness design, though we have only examined one search space
and one scoring design and do not claim this to be a global optimum.
```
**Replace with**
```latex
This reflects the fitness landscape rather than a property of the search
method: safety is set largely by the fixed escalation rule, and the
structure-dependent terms reach their maximum once $\tilde w_c\ge0.55$
(Proposition~\ref{prop:plateau}). We have examined one search space and one
scoring design and do not claim this genome to be a global optimum.
```

---

## E7 · §4.3, Convergence (lines 1388–1392) · Comment 1.2

**Current**
```latex
This supports the
broader point that seeded initialisation (four hand-designed seeds
spanning different regions of the genome space, rather than a fully random
population) accelerates convergence toward a high-structure region, via
$g_\mathrm{str}$-like individuals reaching high fitness quickly.
```
**Replace with**
```latex
In this run, therefore, a high-structure individual was present from the
first generation, and the remaining generations did not produce a resolvable
improvement on it.
```

---

## E8 · §4.5, Overall Performance (lines 1564–1567) · Comment 1.2

**Current**
```latex
The GA-optimised system (B4) substantially outperforms the non-GA
baselines. The most pronounced difference is in structural completeness: B4 achieves a
```
**Replace with**
```latex
Under the frozen scorer, the reported GA configuration (B4) scores higher
than B1 and B2. The largest difference is in structural completeness: B4 achieves a
```

---

## E9 · §4.7, Significance (two places) · Comment 1.2

**(a) Lines 1666–1668. Current**
```latex
The GA consistently outperformed both baselines across all five runs
(Table~\ref{tab:significance}). The one-sided Wilcoxon test confirms that the
GA-optimised system achieves higher fitness than both B1 ($W = 15$,
```
**Replace with**
```latex
All five GA seeds scored above both fixed baselines
(Table~\ref{tab:significance}). The one-sided Wilcoxon test indicates that
this direction is consistent across seeds for both B1 ($W = 15$,
```

**(b) Lines 1738–1743. Current**
```latex
These results show that the reported GA-optimised configurations consistently
achieve higher fitness than the fixed seed reference B2 and the five
individually sampled random genomes B3 under the same fixed generation and scoring path. This does not
establish a causal advantage of evolutionary search alone, and the separate
equal-budget random-search comparison in section~\ref{sec:interp-baseline} shows no resolvable
difference between methods under the present evaluation design.
```
**Replace with**
```latex
These results describe the reported configurations, not the search method:
the equal-budget random search in Section~\ref{sec:interp-baseline} reaches
the same fitness region, with no resolvable difference from the GA.
```

---

## E10 · §5.1, Seeded Initialization (lines 2160–2163) · Comment 1.2

The current text makes a general claim about acceleration and reproducibility that no experiment in the paper tests.

**Current**
```latex
Seeded initialization plausibly plays a dual role in this framework.
Seeding with four hand-designed genomes alongside randomly initialised
individuals commonly accelerates convergence and improves run-to-run
reproducibility relative to fully random initialisation. Per-generation
```
**Replace with**
```latex
Seeded initialization played two roles in this study. We did not run a
randomly initialised control, so we make no general claim about its effect
on convergence. Per-generation
```

---

## E11 · §5.4, ablation paragraph (line 2404) · Comment 1.2 · **important**

This sentence is the one Reviewer 1 is most likely to object to. Random search *also* located the region without prior knowledge, so the claim does not set the GA apart.

**Current** (near the end of the long paragraph)
```latex
the contribution of the genetic search lies in locating this region without prior knowledge of the regime boundary, not in tuning the remaining genes.
```
**Replace with**
```latex
both the genetic search and equal-budget random search located this region without prior knowledge of the regime boundary, as Proposition~\ref{prop:plateau} predicts for any search that samples $\tilde w_c\ge0.55$.
```

---

## E12 · §5.5 title and one sentence (lines 2436, 2470–2471) · Comment 1.6

**Line 2436. Current**
```latex
\subsection{Did the GA Achieve Multi-Objective Balance?}
```
**Replace with**
```latex
\subsection{Scalarised Fitness and the Structure-Dominant Optimum}
```

**Lines 2470–2471. Current:** `This is a genuine limitation of collapsing multi-objective optimisation into one scalar fitness with fixed coefficients:`
**Replace with:** `This is a limitation of combining three objectives into one scalar fitness with fixed coefficients:`

---

## E13 · Ethics (three places) · Comment 1.4

**Wait for the outcome of the ethics application before editing these.**

### Version A: approval or exemption obtained

**§5.6, "Ethical oversight and data governance" (lines 2570–2581).** Replace the paragraph with:
```latex
\textbf{Ethical oversight and data governance.} [Retrospective approval / A
formal exemption] for the secondary analysis of these de-identified data was
granted by [committee], reference [number], dated [date] (see the
Institutional Review Board Statement). The data are de-identified records from
routine mental-health screening delivered through the application; the
screening questionnaires were administered by Relaxy PTE.\ LTD., and the
research team used only the resulting de-identified data.
```

**IRB statement (lines 2783–2804).** Replace the first sentence ("No independent institutional review board…") with:
```latex
This study was [approved / granted an exemption] by [committee], reference
[number], dated [date], for secondary analysis of de-identified data.
```
Keep the remaining sentences about consent, self-reported age and the 14.7% sensitivity analysis. **Delete** the final sentence ("We recognise that de-identification and electronic consent do not substitute…").

**Data Availability (lines 2819–2821).** Delete "no independent institutional ethics board approval was sought or obtained" and replace it with "the study was [approved / exempted] by [committee] (reference [number])".

### Version B: approval not obtained

Leave the three passages as they are; they already state this honestly. Fill in Version B of reply 1.4.

### Optional, strongest response

Re-run the main experiments with the 13–17 records removed from the dataset entirely, then update Tables 5, 6 and 11. This converts Table 11 from a post-hoc check into the main analysis.

---

## E14 · §6 Conclusions, first paragraph (lines 2742–2747) · Comments 1.1, 1.3

**Current**
```latex
We presented EvoRiri, an interpretable evolutionary-search framework for a
template-based Bangla--Banglish--English mental-health assistant that needs no
GPU or external language model. On a synthetic single-turn corpus under a
frozen rule-based scoring pipeline, the evolved genome raised structural
completeness from 0.65 to 1.00 and fitness from 0.556 to 0.703 over the fixed
reference genome, with a similar escalation-calibration safety proxy.
```
**Replace with**
```latex
We presented EvoRiri, a diagnostic case study of interpretable evolutionary
search over a template-based Bangla--Banglish--English response generator that
needs no GPU or language model. The genetic algorithm is standard; the
contribution lies in what the interpretable design made visible. On synthetic
single-turn prompts under a frozen rule-based scorer, the reported genome
raised structural completeness from 0.65 to 1.00 and fitness from 0.556 to
0.703 over a fixed reference genome, with a similar safety proxy.
```

---

## E15 · Shortening plan · Comment 1.5

**Principle:** state each caveat **once**, where its evidence is reported, and replace every later repetition with a one-line cross-reference. Measure the page count before you start so you can fill in [X]/[Y]/[Z] in reply 1.5.

| Topic | Keep in full at | Cut or condense at (lines) | Suggested replacement |
|---|---|---|---|
| B1 truncation defect | §5.4 (2262–2319) | 699–704; 1568–1578; 1834–1838; 1919–1930; 1946–1966; 1975–1983; 2024–2033; 2150–2152; 2636–2640; 2751–2754 | "B1 also carries a truncation defect (Section 5.4)." |
| Evaluation noise floor | §3.5.6 (1005–1022) | 1368–1371; 1615–1618; 1728–1732; 2373–2375 | "(within evaluation noise; Section 3.5.6)" |
| $w_s$ renormalisation | Appendix B.1 | 631–649 and 679–687 (§3.3) | two sentences plus "(Appendix B.1)" |
| Distress-gating penalty argument | Appendix D.1 | 820–847 (§3.4.3) | about three sentences plus a pointer |
| Mid-risk γ band caveat | §3.4.3 | 1789–1799 (§4.9) | one sentence (see also E16) |
| Proxy-validity caveat | §5.7 | 1557–1562; 2488–2495 | a pointer to §5.7 |
| Human-eval Krippendorff interpretation | Appendix F | 2125–2138 | one sentence: "α ≈ 0.56–0.61; ratings are read as directional (Appendix F)" |
| Related work: trace-diagnosis paragraph | §5.3 | 280–292 (§2.1) | delete; §5.3 covers it |
| LLM survey description | — | 226–234 (§2.1) | condense to two sentences |
| Empathy proxy vs clinician tension | §4.12.2 | 1954–1966 (§4.11) | delete; §4.12.2 covers it |
| Limitations restating results | §5.7 | 2634–2672 | keep implications only; drop re-stated numbers |

The B1-truncation and noise-floor repetitions alone account for roughly 3–4 pages. Together with the moves to the appendices, a cut of 25–35% of the main text is realistic without removing any result.

---

## E16 · §4.9 Risk-Aware Safety (lines 1792–1799) · Reviewer 1 recommendation 3 (circularity)

The manuscript currently says this has **not** been quantified:
```latex
We have
not directly quantified, however, how many mid-risk prompts in this dataset actually
fall in that band at $\gamma^{\star} \approx 0.058$.
```
**Computed (17 Oct 2026, read-only).** Same pipeline as the paper: 80/20 split at seed 7, 400-prompt subsample at seed 7, B4's $\gamma^\star = 0.05848$, so the band is $0.6141 < h_i \le 0.65$.

| Set | Mid-risk prompts | In γ\* band | In widest band (γ = 0.2) | $h_i > 0.65$ (escalate regardless of γ) | $h_i = 0$ |
|---|---|---|---|---|---|
| 400-prompt validation subsample | 114 | **1** (0.9%) | 1 | 3 | 110 |
| Full validation split (575) | 166 | 1 (0.6%) | 1 | 5 | 160 |
| Full corpus (2,872) | 834 | 1 (0.1%) | 4 | 21 | 809 |

**Replace the passage with:**
```latex
Of the 114 mid-risk prompts in the 400-prompt validation subsample, only one
falls in this band at $\gamma^{\star}\approx0.058$, and still only one at the
largest permitted value $\gamma=0.2$; 110 of the 114 have $h_i=0$. The
distress-gating gene therefore changes escalation for a single validation
prompt, consistent with $\gamma$ being only weakly identified by the present
fitness design (Section~\ref{sec:risk-escalation},
Appendix~\ref{app:distress-penalty}).
```
You can also cite these numbers in Proposition 1's discussion (E5): γ is formally active, but in practice it changes the output for almost no prompts.

---

## E17 · Distress-score description (lines 511–522 and 798) · Reviewer 1 recommendation 3 (circularity) · **correction**

**Found while computing E16.** The code computes $h_i$ on the **theme-text string** (`common_themes | thought_progression`), not on the synthetic prompt $x_i$. See `src/evaluation/scoring.py` (`fitness` and `evaluate_breakdown` call `compute_distress_score(user_prompt)`, where `user_prompt` is the theme text), and `run_corrected_experiments.py:331`. The synthetic prompt is built later, inside `generate_response`. The manuscript currently says the opposite, and its circularity caveat rests on that description. Please confirm this against the code yourself before you edit.

**(a) §3.2, lines 511–522. Current** (from "This has a specific consequence…" to "…(further discussed in Section~\ref{sec:limitations}).")
```latex
This has a specific consequence for the risk-aware escalation mechanism
(Section~\ref{sec:risk-escalation}): for prompts labeled high-risk,
\texttt{build\_realistic\_user\_prompt()} deliberately selects
higher-intensity language consistent with that label, so the distress
score $h(x_i)$ -- itself computed from keyword matches on $x_i$ -- is not
fully independent of the risk label $r_i$ ...
```
**Replace with**
```latex
The distress score $h_i$ used for mid-risk escalation
(Section~\ref{sec:risk-escalation}) is computed by keyword matching on the
intermediate theme-text string, not on the synthetic prompt $x_i$, so it
does not depend on the phrases selected by
\texttt{build\_realistic\_user\_prompt()}. The theme fields were written by
analysts and may nonetheless correlate with the information used to assign
$r_i$, so $h_i$ is not treated as a fully independent signal; in practice it
affects escalation for only one validation prompt
(Section~\ref{sec:structure-analysis}).
```
(Point the last reference at whichever section holds the E16 sentence, i.e. §4.9; it has no label yet, so add `\label{sec:risk-safety}` under `\subsection{Risk-Aware Safety Behavior}` and cite that.)

**(b) §3.4.3, line 798. Current:** `where $h(x_i) \in [0,1]$ is a distress score computed from prompt keywords`
**Replace with:** `where $h_i \in [0,1]$ is a distress score computed from keywords in the record's theme text (Section~\ref{sec:methods})`

**(c) Notation.** For consistency, change `h(x_i)` to `h_i` at lines 791 and 798, and in Eq. 8 if it appears there; Eq. 8 already uses $h_i$.

**Side check:** when $h$ is instead computed on freshly generated synthetic prompts (one stochastic draw), 0 of the 114 mid-risk prompts fall in the band and 3 exceed 0.65. Either way, the conclusion is the same.
