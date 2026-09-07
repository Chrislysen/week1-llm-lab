# Session resume — 2026-09-06 / 07

**Scope:** work done in the final stretch of the session, covering E25 (full
run) through E27-B. Written for external review. Every number below is
re-derivable from committed artifacts; every claim is labelled with its status.

**Headline, stated plainly:** one confirmed methodological result that is
original to this work (E27/E27-B), three successful replications of other
people's published claims, and four predictions of my own that I refuted myself.
**No breakthrough. No novel discovery about how language models work.**

**Update 2026-09-08:** adds E28, a declared feasibility probe for a proposed
agent-communication cost study (section 3b). It passed its declared rule for the
cost contrast it tested and established nothing about novelty, recovery
effectiveness, or preservation of task quality. Three of its first-pass
conclusions were withdrawn after external review.

---

## 1. The one original result — E27 / E27-B

### Claim

> Whether an activation-steering experiment reports success or failure is
> determined by the **direction estimator**, holding everything else fixed.

### Evidence

36 cells = 2 models × 3 layers × 6 concepts. A "cell" is one
(model, layer, concept); within it, four estimators produce four unit-norm
directions applied at identical α, measured by the same readout against the same
random controls.

| estimator | beats controls | negative mean effect |
|---|---|---|
| `lda` (whitened mean difference) | 18 / 36 | 3 / 36 |
| `dim` (mean difference; CAA/ActAdd standard) | 17 / 36 | 2 / 36 |
| `logistic` (probe weight) | 10 / 36 | 3 / 36 |
| **`pca` (top PC of paired differences)** | **0 / 36** | **21 / 36** |

Of the **20 informative cells** (≥1 estimator beats controls), **20 show the
estimators disagreeing on the binary verdict — 100 %**, against a threshold of
50 % fixed before the run.

### Why alternative explanations are excluded

- **Lucky layer** — disagreement at every layer tested in both models
  (L12/18/24; L8/13/18).
- **Lucky pair sample** — each delta is a 20-fold bootstrap resampling the eight
  contrastive pairs; a cell counts as BEATS only if the bootstrap **lower bound**
  clears the largest random control.
- **Unrepeated-measurement noise** — the readout is deterministic (temperature 0,
  single forward pass); all sampling variability is in direction estimation,
  which the bootstrap targets directly.

### Provenance

Found by accident. E26 tested my own prediction that a knowledge–action gap could
be closed by steering; it returned a null using logistic-regression directions.
Suspecting my estimator choice rather than the result, I re-ran with
difference-in-means (the field standard). The null became a positive
(+0.054 → +0.113, moving from inside the random range to beating every control).
E27 tested whether that generalised; E27-B tested it at scale.

### Practical recommendation

Report the estimator. Run more than one. **Do not use paired-difference PCA** —
0/36 successes with a wrong-signed mean effect in 21/36.

### Prior-art status: NARROW-OPEN, not open

- Estimators (MD / PCA / LR) are compared **descriptively** in method surveys —
  how they are computed, not whether they flip verdicts.
- **arXiv:2608.08159** (Wu, Zhao & Chen, Aug 2026) audits steering measurement
  confounds across 17 models and flips a null — auditing units, readout metric,
  operating point, layer, neuron selection. **The estimator is not among them.**
- **arXiv:2505.22637** (Braun et al.) studies steering unreliability and
  **explicitly does not compare estimators**.

Two papers that would naturally have covered it did not. This is best described
as **the missing entry in an existing audit**, not a new research direction.

### Limits (the honest list)

Two models of one vendor lineage (Qwen2.5-1.5B, Qwen3.5-0.8B); three layers each;
six concepts; eight contrastive pairs and a single probe-token readout per
concept. The bootstrap bounds pair-sampling noise only, not concept or probe
choice. α fixed per model, chosen for proportionality to residual norm, not tuned
per concept. **`pca` here is the paired-difference variant; PCA over concatenated
activations is untested — the most important gap, since the PCA negative is the
most actionable claim.** 16 of 36 cells were uninformative.

---

## 2. Replications of others' published claims — all successful

| study | claim tested | outcome |
|---|---|---|
| **E20** | arXiv:2606.24077 — 2–4 % of attention heads carry contextual entrainment, ablating them mitigates it without hurting performance | **REPLICATES.** Held-out Δ +3.224 → +1.883 (41.6 % reduction), above the random-set p95 (+0.292), `score_absent` shift 0.166. Post-hoc: at <1.5 % of heads the model is damaged; only at 2.98 % do both halves hold — the paper's own specified range. |
| **E25** | the type-by-length constraint mechanism, on IFEval's real items | **Within-model: CONFIRMED.** 14/14 pure-type cells in the predicted direction, sign test p = 1.2 × 10⁻⁴, capability held fixed. 1 075 generations across 5 models, all 215 analysable prompts. |
| **E19 / E19-B** | arXiv:2606.24077 — contextual entrainment exists and decreases with scale | **Existence: replicates decisively** (Δ > 0, 144/144 dialogues positive, all 5 models). **Scale: replicates** under 2 of 3 measures. |

**E21** additionally produced a clean mechanistic dissociation: the heads that
causally carry entrainment carry **none** of the rejected-vs-unmentioned
discrimination — ablating them shifted every status ~1.35 nats while leaving all
contrasts fixed.

---

## 3. My own predictions, refuted by my own follow-ups

This is the part I would most want a reviewer to check.

| prediction | refuted by | what happened |
|---|---|---|
| Contextual entrainment's scale claim fails (E19) | **E19-B** | 4 of 5 measure×ladder combinations replicate it; the single failure was the paper's raw log difference in one ladder, driven by one model's low baseline. **Withdrawn.** |
| The verdict is *barely represented* rather than present-but-unread (E23) | **E23-B** | Filling in the scale curve showed two models with the verdict **86–94 % decodable and behaviourally unused** — a genuine knowledge–action gap where I had assumed nothing was. **Corrected.** |
| Constraint-mix composition distorts real benchmark rankings (E24-C) | **E25** | On IFEval's real items, verbosity and capability are positively correlated, so the effect does not distort rankings. **Scope narrowed.** |
| The gap is repairable at decoding time (E23-B) | **E26** | Steering fails to recover it. **Withdrawn** — then *partially* reinstated by E26-B in a much weaker, sub-threshold form. |

A fifth reversal is internal to the winning line: **E26's own null was partly a
method artefact**, caught by E26-B.

I also ran two internal validations of the E25 result that **failed** — a
relation-split check (12/20 against a chance of 10/20, which withdrew my "the
classification is doing real work" claim) and a hazard-gradient check (4/4 but
p = 0.125, and formulated *after* the first check failed, which I flagged as a
forking-path hazard before reporting it).

---

## 3b. E28 — a declared feasibility probe (added 2026-09-08)

E28 was a declared feasibility probe for measuring paired token-cost differences
on `llama3.2:3b`, run against the existing `DialogueEngine` before building
anything. Each pair is 2 runs x 8 turns = 16 model calls, so the declared run
used **192 calls** (8 instances + 4 repeats), with 80 more for E28-D, 128 for
E28-C and 16 for the smoke run: **416 total**. It returned
**POWERED** under its declared rule: mean saving 560.5 tokens (16.3 %) and an
estimated **MDE of 203.9 tokens (5.9 %) at 12 instances**. Counterbalanced over
arm order, that becomes **+623.4 tokens (17.9 %)** with **MDE 162.2 tokens
(4.6 %)**.

The intervention was **mechanical context truncation**. It did not test learned
communication or recovery quality. **Two of three quantitative predictions
failed** (SD ratio 0.67 against a predicted <0.3; mean saving 16.3 % against a
predicted 20–40 %). **E28-D** refuted a first-process-call prediction and
exposed a **non-exhaustive read rule** — neither declared branch covered the
outcome. **E28-C**, prompted by external review, found that arm order had been
**confounded with request position** (`full` ran first in every pair);
counterbalancing refuted my predicted *direction* and moved the point estimate by
~126 tokens, though at n=8 that shift is not distinguishable from zero
(t = 1.53, p ≈ 0.17) — a bare threshold with no uncertainty treatment, the same
error E24-B already recorded in this repo. Repeated runs showed an unexplained
process-associated cost pattern, motivating process blocking and randomised arm
order.

**Three claims from the first write-up were withdrawn** after external review:
the "five-fold margin" against REVISE (which compares *model-call* reductions,
not tokens under truncation — an invalid cross-quantity comparison); the
assertion that this contrast's SD_H is a *lower bound* on a recovery study's
(asserted, not argued — it is an optimistic planning proxy); and the claim that
the unlearning bound of 2609.04875 closes the direction a priori (it bounds
worst-case *exact reconstruction* over transitions, not decoded tokens, and does
not preclude changing prospective exposure).

E28 also does not address **power for task quality**: zero additional-failure
events across 12 independent task pairs still permits a one-sided exact 95 %
upper bound of ≈ 22.1 %.

> **E28 establishes provisional feasibility for its tested cost contrast. It does
> not establish novelty, the power of a different recovery contrast, preservation
> of task quality, or freedom from all statistical risks.**

**Outcome of the direction (2026-09-08): CLOSED on novelty.** External review
specified the method concretely and withdrew its own recommendation: the
specification decomposes into adapted CPE-style prompt search, REVISE-style
selective recovery, and tuned static isolation, with no additional search
mechanism, guarantee, or demonstrated advantage. The recovery backend is not
built and is not warranted on this rationale. **Tally: 22 candidates gated, 21
closed**; E27 remains the single NARROW-OPEN result.

Two further corrections after review: the order shift's 95 % interval is
[-68.5, +320.1] tokens, so the observed *direction* is reportable but systematic
second-position inflation is **not** established (and order coincides with
collection period here); and SD_H = 182.6 belongs to the **order-averaged**
design at 32 calls/instance, so a one-randomised-pair design cannot inherit the
4.65 % figure.

The binding risk is novelty and it is not statistical: CPE (arXiv:2606.14314)
already performs rollout-driven communication-prompt optimisation with training
and validation gates, so the next decision — taken **before** any further large
inference run — is to state concretely what the proposed algorithm does beyond
CPE-style search with a substituted objective, REVISE-style recovery, and tuned
static isolation. If that cannot be specified and tested, the breakthrough
framing is retired and the engineering and feasibility record kept.

## 4. Negative and null results worth recording

- **E22** — a rejection-circuit search was **designed, power-checked, and not
  run**. Baseline effect +0.121 against a random-ablation noise SD of 0.041
  (S/N 3.0), with random ablation already removing 30–90 % of the effect. Running
  it would have repeated a documented past failure in this repo (a conclusion
  asserted at power 0.14, later retracted in full).
- **E24-B** — the declared read rule returned REORDER DEMONSTRATED and **the rule
  was wrong**: its 0.02 threshold was set with no power analysis, against 95 %
  half-widths of 0.080–0.132. Recorded, not relied on.
- **21 candidate hypotheses were gated against the literature; 20 closed.**
  Framings tried: behavioural (8), measurement (3), meta-science (1), bounding
  (1), latent/mechanistic (1), circuit-identity (1), thesis-level (1), and others.
  Every closed one had all its components already published.

---

## 5. Methodological practices used throughout

- **Every protocol declared with zero outcomes before its first model call**, with
  predictions and a read rule fixed in advance, committed to git ahead of any run.
- **Declared escape hatches fired and were honoured** — E16's menu diagnostic
  returned UNINFORMATIVE because its precondition failed; E26's validity condition
  voided an apparent "+0.341 recovery" that came with 3.9 nats of model damage.
- **Post-hoc analyses labelled as post-hoc**, including when they were the more
  interesting result (E25's within-model finding).
- **Frozen state verified continuously**: `verify_claims.py` 167 verified / 0
  mismatched / 4 unverifiable; 135 tests; E16 corpus hash unchanged throughout.
- **Engineering changes made opt-in** to preserve reproducibility: a
  `num_predict` runaway guard (added after one IFEval prompt looped for 515 s) was
  added as a parameter defaulting to `None`, leaving every earlier experiment
  byte-unchanged.

---

## 6. What a reviewer should conclude

**Can be claimed:** one original, well-controlled methodological result with a
concrete recommendation for a live literature (E27-B); three successful
replications, two of them supplying controls the original papers did not run
(E20's specificity control, E25's within-model design); one clean mechanistic
dissociation (E21).

**Cannot be claimed:** any novel finding about language model behaviour or
capability. Any breakthrough. Twenty of twenty-one hypotheses were closed by
existing literature, and the twenty-first is a missing entry in an existing audit
rather than a new direction.

**The strongest evidence of rigour** is not any single result — it is that four
of my own predictions and one of my own read rules were refuted by tests I
designed and ran specifically to kill them.

---

## Artifacts

Protocols in `docs/protocols/`: E16-zombie-screen, E16-menu-diagnostic,
E17-menu-law, E18-revocation-scale, E19-entrainment, E20-entrainment-heads,
E21-circuit-identity, E23-verdict-probe, E24-constraint-length, E25-ifeval,
E26-steering, E27-estimator. Candidate gates and citation audit in
`docs/E16-CANDIDATES.md`. Negative-results record in `docs/NEGATIVE-RESULTS.md`.
Raw outputs in `results/`. ~165 commits, working tree clean.
