# E13 — Recognition → Utilization — protocol v1

**PREREGISTERED. Committed with zero E13 outcomes in the tree.**

## 1. The question

E12 established, at adequate power and with clustering handled, that the model
prices *k* reports from **one** evidential root exactly as it prices *k*
**independent** roots (difference +0.0185, cluster CI [−0.037, +0.074], inside
the SESOI of 0.10). A frozen probe shows it can *report* the difference (27/36
vs 0/36, p = 1.5e-08).

> **When a model correctly recognises that corroborating reports share one
> evidential root, why does that recognition not reach the decision — and does
> routing it into the reasoning step make the model price independence
> correctly?**

**No novelty is claimed.** `docs/novelty_matrix.md` C8 records two papers that
could pre-empt this outright (CAMA arXiv:2608.19701; Information Discernment
arXiv:2607.19355) and the search to check them **cannot run this session**.

## 2. Design

108 (instance, proposition) units in **36 instance clusters** — E12's units,
unmutated. 5 interventions × 2 dependence levels = **10 cells**, 1080 calls per
model.

| arm | what it adds | purpose |
|---|---|---|
| `default` | nothing — **byte-identical to E12's prompt** (gate-asserted) | RQ2 replication |
| `identify` | required machine-parseable assessment before the plan | RQ3 |
| `normative` | `identify` + one frozen sentence of principle | RQ4 |
| `sham` | same structured burden, **task-irrelevant** property | control for RQ3/RQ4 |
| `gold` | correct structure stated outright | **diagnostic only, never pooled** |

**Frozen principle (NORMATIVE only):** *"Multiple reports derived from the same
underlying evidence should not be treated as multiple independent confirmations.
Distinct independent evidence may provide additional corroborative weight."*

`LEDGER` (RQ5) is **deferred by its own conditional** — it is only asked if the
simpler normative intervention works.

## 3. Definitions, fixed before scoring

- **recognition correct (primary)** — `same_underlying_source` matches the
  construction (true for SAME_ROOT, false for INDEPENDENT_ROOT).
- **recognition correct (secondary)** — the count, scored **strict** (= k+1) and
  **lenient** (k+1 or k+2). A smoke test showed the model answering 4 where the
  support rests on 3; the contradiction is also a report and counting it is
  defensible, so both readings are reported. The boolean is primary *because* it
  has no such ambiguity.
- **behavioural differentiation** — `flip(SAME) − flip(INDEP)`. **Positive is the
  normative direction**: one root is weaker evidence, so it should protect less.
- **action independence-sensitive (per unit)** — flipped on SAME_ROOT *and* held
  the source ordering on INDEPENDENT_ROOT.

## 4. Statistics — and the contingency that makes E10's failure impossible

Sampling unit is the **instance cluster**. Cluster permutation (instance-level
label swaps) and cluster bootstrap (resampling instances), exactly as E12.
Secondary intervention contrasts are Holm-corrected. `p > .05` is never read as
equivalence.

`prospective_design_check.py` was run **before any model call**. At 108 units in
36 clusters with SESOI 0.10, this design is powered (≥ 0.80) only for **observed
discordance in [0.08, 0.12]**:

| discordance | 0.05 | 0.08 | 0.10 | 0.12 | 0.15 | 0.20 |
|---|---|---|---|---|---|---|
| power | 0.42 | **0.84** | **0.95** | **0.83** | 0.70 | 0.58 |

Power *falls* as discordance rises — a larger discordant subset carries more
variance than signal.

> **PREREGISTERED CONTINGENCY: any contrast whose observed discordance falls
> outside [0.08, 0.12] is printed INCONCLUSIVE BY RULE and never as a null.**
> The analysis code enforces this; it is not a matter of interpretation.

The same tool, run on E10's configuration, returns **ABORT** (power 0.16). Run on
E12's, it returns 0.93 power / 0.77 equivalence-attainment — which records that
E12's equivalence conclusion, though correct, was nearer the edge than it looked.

## 5. Falsification — any one of these kills or narrows the direction

1. `default` does **not** replicate E12's non-differentiation → stop, report
   instability.
2. Recognition accuracy is weak → the problem is **perceptual**, not
   utilization.
3. `identify` differentiates but `sham` differentiates equally → the cause is
   the **structured-output burden**, not dependence reasoning.
4. `normative` improves and `sham` improves equally → same conclusion.
5. The effect appears in one model family only → **model-specific**.
6. Reported grouping is uncoupled from the action —
   `P(sensitive | recognized) ≈ P(sensitive | misrecognized)` → the model's own
   report does not govern its behaviour.
7. CAMA or Information Discernment already show this exact
   recognition→behaviour dissociation for source *dependence* → **PREEMPTED**.

## 6. Outcomes, named in advance

- **A** — `default` null, `identify` differentiates → available but not
  spontaneously routed.
- **B** — `default` and `identify` null, `normative` differentiates → represented
  but no spontaneous *normative* use.
- **C** — even `gold` leaves behaviour unchanged → **strong utilization
  failure**: the structure is explicitly present and behaviourally inert.
  Verify hard before escalating.
- **D** — nothing replicates cross-family → retire.

## 7. Cross-model

Only after the mechanism is identified on `llama3.2:3b`, and then across the
same three **genuinely distinct** families as E12 — Llama (Meta), Aya (Cohere),
Qwen (Alibaba). Multiple Qwen sizes are **one** family.

## 8. Gates (11, all passing)

Frozen corpora intact (E10/E11/E12 hashes asserted); `default` byte-identical to
E12; discussion text identical across all non-`gold` arms; no lineage label,
arm name or basis string in any instruction or in the gold note; `normative` =
`identify` + the principle and nothing else; `sham` burden-matched to within 6
words and free of evidence vocabulary; prompt lengths recorded; deterministic
regeneration.

---

## Amendment A1 — 2026-09-01, POST-HOC, written after all outcomes existed

Nothing above is rewritten. An adversarial panel run after scoring found three
defects, all verified and recorded in `docs/protocols/E13-CORRECTIONS.md`:

1. §1's premise "prices *k* reports from one root exactly as *k* independent
   roots" holds for the **ordering verdict only**. The plan's second decision
   field, `ready`, was never scored by E12 or E13 and is dependence-sensitive
   in every arm (post-hoc; unconfirmed).
2. The paired count analysis reported for RQ1 was **not** in this
   preregistration; it was added after the first 36 units were on disk. Rule 2
   has no threshold and is unadjudicated.
3. Outcome C ("behaviourally inert") was never declared and must not be:
   `gold` is INCONCLUSIVE BY RULE on the ordering verdict and moves `ready`.
