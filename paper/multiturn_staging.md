# Multi-Turn Extension — Staging Content for main.tex

Status: DRAFT. Not yet inserted into main.tex. Missing piece before this
is submission-ready: human evaluation with clinical psychologists (not
yet started). Everything below reflects verified, committed work on the
v0.10-multiturn branch as of today.

---

## Section: Multi-Turn Architecture (Methods)

The single-turn framework (Section 3) was extended to support multi-turn
conversations by adding a distress trajectory mechanism and a per-genome
scored-turn cap, while deliberately leaving the underlying per-turn
response generator (Section 3.4) unchanged.

### Distress Trajectory

The single-message distress score h(x_i) (Eq. 7, Section 3.4.2) is
extended to a per-conversation trajectory:

  h_t = max(raw_t, alpha * h_{t-1})

where raw_t is the single-message distress score for turn t, and
alpha = 0.6 is a decay coefficient. This recurrence lets a distress
signal persist across a few turns rather than resetting the instant a
subsequent message is calmer, while naturally forgetting old spikes
(alpha^10 ~= 0.006) without requiring the input to be explicitly
windowed.

### Escalation State Machine

A three-state escalation decision (FULL / LIGHT / NONE) governs
generation-time behavior per turn:

- FULL: first threshold crossing in the conversation, or a new distinct
  spike (h_t exceeding the last escalation's h value by more than 0.15).
  Maps to escalate_override=True in the per-turn generator.
- LIGHT: sustained elevated distress following a prior FULL escalation,
  not yet re-crossing the spike threshold. Maps to
  escalate_override=False -- the existing single-turn generator already
  provides a soft-support phrase tier (distinct from full crisis
  language) for this case, requiring no changes to the generator itself.
- NONE: below threshold. Also maps to escalate_override=False.

This avoids the full crisis-language block repeating verbatim on every
turn while distress remains elevated, without silently dropping
escalation entirely after the first mention.

### Genome Extension

One new gene, history_turns (range [4, 24]), governs how many of a
conversation's most recent turns are actually generated and scored per
genome -- distinct from the distress trajectory, which is always
computed over the full conversation regardless of this cap. This
separation matters: capping the trajectory itself would have
(re-)introduced a bug found during development, where early
conversation turns were silently excluded not just from scoring but
from the escalation state machine's memory of prior crossings.

An absolute safety ceiling (30 turns) bounds worst-case compute cost
independent of any individual genome's evolved history_turns value.

### Fitness Extension

Two additive terms were added to the per-turn fitness (Eq. 11),
applied only to mid-risk conversations:

1. An escalation-appropriateness bonus (+0.10) when a genuine
   distress crossing is followed by de-escalation to soft support
   rather than repeated verbatim crisis language on consecutive turns.
2. A flat over-escalation penalty (-0.12) when a turn escalates but
   its raw h_t did not exceed the FIXED baseline threshold tau_h=0.65
   on its own -- i.e., the genome's evolved gamma, not genuine
   distress, was responsible for triggering escalation. This mirrors
   the existing low-risk safety asymmetry (Eq. 8: 0.75 vs 1.00) that
   was previously absent for mid-risk.

---

## Finding: Gamma's Step-Function Saturation

Unlike single-turn's small, smoothly-interpretable evolved gamma
(gamma* ~= 0.028, Section 3.4.2), the multi-turn GA's best genomes'
gamma values ranged widely (0.09-0.20) across generations and seeds,
frequently reaching the parameter's upper bound.

Analysis of the full mid-risk session set (N=2,669 sessions, 36,113
scored turns) revealed this is not unconstrained drift or reward
exploitation, but a genuine, mechanistically-explained saturation
effect. Because the escalation-timing threshold relaxation
(tau_h - gamma * h_t) is self-referential in h_t, gamma's practical
effect is bounded: at its maximum value (0.2), the threshold can be
relaxed no lower than tau_h / 1.2 ~= 0.54. Real distress scores are
not continuous but cluster around discrete keyword-weight values (most
notably h_t = 0.60, from the single "isolated" keyword match, present
in 869 turns / 2.41% of the dataset). A fine-grained sweep pinpointed
the exact saturation threshold at gamma ~= 0.086 -- the point at which
the effective threshold crosses below the h_t=0.60 cluster. Below this
threshold, gamma has essentially zero practical effect (0 turns
flipped between gamma=0.00 and 0.08); above it, gamma has a large,
one-time effect (869 turns flip simultaneously) and then completely
saturates -- gamma=0.10, 0.15, and 0.20 produce IDENTICAL escalation
behavior across the entire dataset.

This explains the GA's behavior: once a genome's gamma crosses ~0.086,
further increases are fitness-neutral, so the population drifts freely
within [0.086, 0.20] under mutation with no selective pressure in
either direction -- the same phenomenon already documented for
theta_mid/theta_high (Appendix B), but affecting only the upper portion
of gamma's range rather than the whole gene.

---

## Results: Baseline Comparison (multi-turn)

Held-out validation set: n=1,791 sessions (80/20 split, seed=7,
matching single-turn's split methodology).

| Condition | Fitness |
|---|---|
| B1: Zero-shot (no GA) | -0.092 |
| B2: Fixed seed g_bal (no GA) | 0.547 |
| B3: Random genome (mean +/- std, n=5) | 0.366 +/- 0.105 |
| B4: GA Optimised (seed=7) | 0.704 |
| B4: GA Optimised (5-seed mean) | 0.7047 +/- 0.0007 |

For comparison, single-turn's Table 5 (same conditions, single-turn
setting): B1=-0.203, B2=0.527, B3=0.198+/-0.361, B4=0.677.

Note on B1: memory_window=256 was intentionally retained in the
multi-turn B1 genome, matching single-turn's B1 definition exactly,
even though this value is excluded from the GA's own search space
(see Limitations). This lets B1 exhibit the same truncation-driven
safety failure documented for single-turn's B1, but compounded across
a full conversation rather than a single prompt -- a genuine,
reportable characterization of naive deployment risk rather than an
inconsistency.

### Significance

Unlike the single-turn baseline comparison, which introduces sampling
noise into B1 and B2 by evaluating on a randomly-drawn subset per run
(enabling a paired Wilcoxon signed-rank test), the multi-turn baselines
are evaluated once against the full held-out validation set, with no
subsampling. B1 and B2 are therefore deterministic single values rather
than distributions, and a paired significance test is not meaningful
in this setting. Instead, we report that all five independently-seeded
GA runs achieve validation fitness in the range 0.7039-0.7055,
exceeding both B1 (-0.092) and B2 (0.547) without exception -- a
stronger and more direct claim of dominance than a probabilistic test
would provide here.

### Structure-Dominance Replication

The single-turn finding that the GA converges to a structure-dominant
genome (w_c* = 0.670, Section 3.8) replicates in the multi-turn
setting, more strongly and more consistently: w_c fell in the range
0.67-0.83 across every generation's best genome, in all five
independent seeds, across two full corrected-pipeline runs conducted
on different days during development. This cross-validates the
single-turn finding as a genuine property of the fitness landscape
rather than a single-run artefact.

---

## Open items before this section is submission-ready

1. Human evaluation with clinical psychologists -- not yet started.
   Needs its own annotation protocol design (multi-turn conversations
   are a different rating task than single response pairs).
2. Decide whether to report B4 as the single seed=7 genome (matching
   single-turn Table 5's convention) or the 5-seed mean (matching
   Table 6's convention) as the headline number, or both as done here.
3. Trace analysis / qualitative examples (paper's Appendix A/B
   equivalent) not yet drafted for multi-turn -- e.g. a worked example
   showing the escalation state machine's FULL/LIGHT/NONE behavior
   across a real conversation, mirroring Section 3.1's single-turn
   worked example.
4. Decide where this content lives structurally in main.tex: a new
   Section 4 subsection, a new numbered section entirely, or an
   appendix -- affects table/figure numbering throughout the rest of
   the document.