# E27 — is a steering NULL an artefact of the direction estimator?

**Declared 2026-09-07 with zero E27 runs. This is the first candidate this
session whose core was not found in the literature.**

## Where it came from

E26 → E26-B found it **by accident**. The same probe, the same layer, the same
data and the same measurement gave **+0.054 — inside the random range** with a
logistic-regression direction, and **+0.113 — beating every random control** with
difference-in-means. One estimator change moved a null to a positive.

If that generalises, published steering **nulls** are estimator-dependent, and a
literature full of "steering does not work for X" is under-determined.

## Gate, run before this protocol was written

- Estimators (mean-difference, PCA, logistic) are compared **descriptively** in
  method surveys — how they are computed, not whether they flip verdicts.
- **arXiv:2608.08159** (*When Is a Steerable Concept Representation Real?*,
  Wu, Zhao & Chen, Aug 2026) audits steering measurement confounds across 17
  models and **does** flip a null — but the audited choices are raw units,
  readout metric, operating point, layer, and neuron selection. **The direction
  estimator is not among them.**
- **arXiv:2505.22637** (*Understanding (Un)Reliability of Steering Vectors*,
  Braun et al.) studies steering unreliability and **explicitly does not compare
  estimators**, attributing it to prompt type and activation geometry.

Two papers that would naturally have covered it did not. **Verdict: NARROW-OPEN**
— the closest this session has come, and still not asserted as novel.

## Design

Three concepts, four estimators, one measurement, random controls.

| | |
|---|---|
| **concepts** | `sentiment`, `formality`, `certainty` — 8 contrastive pairs each, disjoint from the E16 corpus |
| **estimators** | `dim` (mean difference, the CAA/ActAdd standard), `logistic` (E26's original), `pca` (top PC of paired differences), `lda` (within-class-whitened mean difference) |
| **measurement** | logprob(token A) − logprob(token B) as the continuation of a fixed probe prompt |
| **controls** | 8 random unit directions at the same α |

For each (concept, estimator) the verdict is binary: **does the steered delta
exceed the largest random-direction |delta|?** All four directions are unit-norm
and applied at the same α, so they differ only in orientation.

## Read rule, fixed before the first run

- **ESTIMATOR-DEPENDENT NULLS CONFIRMED** if, in at least **2 of 3 concepts**,
  the four estimators **disagree** on the binary verdict — at least one beats the
  random controls and at least one does not.
- **NOT CONFIRMED** if all four estimators agree on the verdict in every concept.
  The E26 → E26-B flip would then be a one-off, and is reported as such.
- **PARTIAL** if exactly one concept shows disagreement.

**Validity.** If no estimator beats the random controls for a concept, that
concept carries no signal and is reported as uninformative rather than counted as
agreement. If every estimator beats them by a wide margin, the concept is too
easy to discriminate estimators and is likewise flagged.

## Limits, stated in advance

One model and one layer per run, one α, one measurement per concept, eight
contrastive pairs per concept — small. A single probe token pair per concept is a
narrow readout. Random controls are isotropic Gaussian directions, which is the
standard control but is not the same as a matched-norm semantically-null
direction. Demonstrating disagreement shows the verdict is estimator-sensitive
**here**; it does not establish which estimator is correct, and none is argued to
be.

## Files

`e27_estimator.py`; outputs `results/e27_estimator_<model>_L<layer>.json`.

---

## Outcome

*Pending. Zero E27 runs at the time of this commit.*

---

## Outcome

**Run 2026-09-07. Verdict: ESTIMATOR-DEPENDENT NULLS CONFIRMED.** Two models,
two layers, **5 of 5 informative concepts show the four estimators disagreeing on
the binary verdict**. The declared rule required 2 of 3 in one model.

### Qwen2.5-1.5B-Instruct, layer 18, α = 20

| concept | random \|Δ\| max | `dim` | `logistic` | `pca` | `lda` |
|---|---|---|---|---|---|
| sentiment | 0.625 | **+5.875** ✓ | +2.812 ✓ | **−1.375** ✗ | +5.250 ✓ |
| formality | 1.250 | **+4.937** ✓ | **+1.188** ✗ | +0.312 ✗ | +5.031 ✓ |
| certainty | 1.000 | +3.812 ✓ | +2.938 ✓ | **+0.000** ✗ | +3.875 ✓ |

### Qwen3.5-0.8B, layer 13, α = 5

| concept | random \|Δ\| max | `dim` | `logistic` | `pca` | `lda` |
|---|---|---|---|---|---|
| sentiment | 3.719 | **+13.352** ✓ | +6.188 ✓ | +2.375 ✗ | +7.453 ✓ |
| formality | 5.875 | **+8.781** ✓ | **+5.234** ✗ | **−5.133** ✗ | +10.219 ✓ |
| certainty | 7.859 | +0.178 ✗ | +7.187 ✗ | −4.562 ✗ | +2.805 ✗ |

`certainty` on the 0.8B is **uninformative** by the declared validity rule — no
estimator beats the controls — and is excluded rather than counted as agreement.
At α = 20 on this model, two of three concepts were uninformative because random
perturbations alone moved the readout by up to 11.1; α was reduced to 5, which is
proportionate to its residual norm. That α change is recorded as a deviation
made *for validity*, before reading the estimator comparison.

### The pattern, and it is consistent across both models

| estimator | beats random, informative concepts | notes |
|---|---|---|
| `dim` (mean difference) | **5 / 5** | the CAA / ActAdd standard |
| `lda` (whitened mean difference) | **5 / 5** | largest effect in 2 of 5 |
| `logistic` (probe weight) | 3 / 5 | unreliable |
| `pca` (top PC of paired diffs) | **0 / 5** | **negative in 4 of 6 cells** — steers *backwards* |

### What this establishes

**For the same concept, the same model, the same layer, the same α and the same
measurement, whether you conclude "steering works" depends on how the direction
was estimated.** In 5 of 5 informative concepts at least one estimator beat every
random control and at least one did not.

The `formality` cell on Qwen2.5-1.5B is the cleanest single demonstration:
`dim` +4.937 and `lda` +5.031 beat the controls, while `logistic` +1.188 and
`pca` +0.312 do not. A four-fold spread from orientation alone — all four
directions are unit-norm and applied at identical α.

**PCA on paired differences is not merely weaker — it is often wrong-signed**,
producing negative deltas in four of six cells. A paper using it and reporting a
null would be reporting a property of its estimator.

### Why this matters beyond this repository

E26's null was real under logistic and vanished under difference-in-means. This
shows that was not a one-off. Published steering **negatives** — "steering fails
to control X", "the representation is not causally used" — are under-determined
unless the estimator is reported and, ideally, more than one is tried.
arXiv:2608.08159 audits five analytical choices in exactly this spirit and does
not include the estimator; arXiv:2505.22637 studies steering unreliability and
explicitly does not compare estimators. This is the missing entry in that audit.

### Limits

Two models, one layer each, one α per model, three concepts, eight contrastive
pairs and a single probe-token pair per concept. `pca` is implemented as the top
principal component of **paired differences**; PCA over concatenated activations
is a different common variant and is untested. Random controls are isotropic
Gaussian directions — the standard control, but not a matched-norm
semantically-null direction. Effects are single measurements without repeats, so
individual cell values carry sampling noise; the **verdict pattern**, not any
single delta, is what replicates.

This shows the verdict is estimator-sensitive **here**. It does not establish
which estimator is correct, and none is argued to be — though `dim` and `lda`
agreeing 5/5 while `pca` fails 5/5 is a strong hint about which to distrust.

**Not asserted as novel.** The gate rated this NARROW-OPEN, not open.

### Files

`results/e27_estimator_Qwen2.5-1.5B-Instruct_L18.json`,
`results/e27_estimator_Qwen3.5-0.8B_L13.json`.

---

# E27-B — at scale. DECLARED with zero runs.

E27's confirmation rested on single measurements at **one layer per model**.
Three things could still explain it: a lucky layer, a lucky set of contrastive
pairs, or noise in an unrepeated delta. E27-B removes all three.

- **Layer sweep** — several layers per model.
- **Bootstrap** — resample the 8 contrastive pairs with replacement, refit every
  estimator on each resample, report a 95 % interval. This is the correct error
  bar: the measurement is deterministic (temperature 0, one forward pass), so all
  sampling variability lives in *which pairs estimated the direction*.
- **Six concepts** — adding `politeness`, `technicality`, `tense`.

**Stricter verdict than E27.** A cell counts as BEATS only if the **bootstrap
lower bound** exceeds the largest random-control |delta|, not the point estimate.

## Read rule, fixed before the first run

Over all informative cells (those where at least one estimator beats):

- **CONFIRMED AT SCALE** if estimators disagree in **≥ 50 %** of informative
  cells, across at least two layers and two models.
- **WEAKENED** if disagreement falls below 25 % — E27's result would then be
  specific to its layer or pair sample.
- **PARTIAL** between.

Cells where no estimator beats are **uninformative** and excluded, as in E27.

## Limits

The same six concepts and single probe-token readouts. Bootstrap resamples
directions but not the probe or the concept set, so it bounds pair-sampling
noise only. α is fixed per model.

## E27-B Outcome

**Run 2026-09-07. Verdict: CONFIRMED AT SCALE.** Two models × three layers ×
six concepts = **36 cells**. Of the **20 informative** cells, **20 disagree —
100 %**, against a declared threshold of 50 %, using the *stricter*
bootstrap-lower-bound test.

| estimator | beats controls | rate | negative mean |
|---|---|---|---|
| `lda` (whitened mean difference) | 18 / 36 | 50 % | 3 / 36 |
| `dim` (mean difference) | 17 / 36 | 47 % | 2 / 36 |
| `logistic` (probe weight) | 10 / 36 | 28 % | 3 / 36 |
| **`pca`** (top PC of paired diffs) | **0 / 36** | **0 %** | **21 / 36** |

### What survives the three alternative explanations

E27 could have been a lucky layer, a lucky pair sample, or unrepeated-measurement
noise. All three are now excluded:

- **Layer** — disagreement occurs at every layer tested in both models
  (L12/18/24 and L8/13/18).
- **Pair sample** — each delta is a 20-fold bootstrap over the contrastive
  pairs, and a cell counts as BEATS only if its **lower bound** clears the
  largest random control.
- **Concept** — six concepts, and disagreement appears in every informative one.

### The result

**Whether a steering experiment reports success or failure is determined by the
direction estimator, in 100 % of informative cells.** Same model, same layer,
same α, same contrastive data, same readout, same random controls — only the
orientation of a unit-norm vector differs.

**And `pca` on paired differences is not a weak estimator, it is a broken one.**
Zero successes in 36 cells, with a *negative* mean effect in 21 of them: it
steers against the concept more often than with it. Any paper using it and
reporting a null would be reporting a property of its estimator, not of the
model.

`dim` and `lda` agree closely (17 and 18 of 36) and are the only two that
behave. `logistic` — the choice that produced E26's original null — succeeds
barely half as often.

### Why this matters

E26's null was real under `logistic` and vanished under `dim`. E27 showed that
was not a one-off; E27-B shows it is the norm. Published steering **negatives**
are therefore under-determined unless the estimator is stated, and preferably
more than one is run.

**arXiv:2608.08159** audits five analytical choices in steering — units, readout,
operating point, layer, neuron selection — and flips a null by correcting them.
The direction estimator is not among the five. **arXiv:2505.22637** studies
steering unreliability and explicitly does not compare estimators. On this
evidence the estimator belongs in that audit, and it is the largest single lever
found: it changes the verdict in every informative cell tested.

### Limits

Two models from one vendor family lineage (Qwen2.5 and Qwen3.5), three layers
each, six concepts, eight contrastive pairs and one probe-token pair per concept.
The bootstrap resamples pairs but not concepts or probes, so it bounds
pair-sampling noise only. α is fixed per model and was chosen for proportionality
to residual norm, not tuned per concept. `pca` is the paired-difference variant;
PCA over concatenated activations is a different common recipe and is untested —
that is the single most important gap, since the negative result about PCA is the
most actionable claim here. Random controls are isotropic Gaussian.

Sixteen of 36 cells were uninformative — no estimator beat the controls — which
is itself a reminder that most steering attempts in this setup do nothing.

**Still not asserted as novel.** The gate rated the core NARROW-OPEN.

### Files

`results/e27b_Qwen2.5-1.5B-Instruct.json`, `results/e27b_Qwen3.5-0.8B.json`.


---

## CLOSED 2026-09-08 — originality claim retired, gate found faulty

**Im & Li, arXiv:2502.02716** (v2, 9 Jan 2026) compares the same four estimator
families under tighter controls than E27 used:

- **MoD** (= `dim`), **PoD** = PCA of differences (= `pca`), **PoE** = PCA of
  embeddings (**the control E27 declared as its most important untested gap**),
  **CoE** = classifier on embeddings (= `logistic`).
- Layer and extraction location controlled by ablation (layer 13, residual
  stream); **steering multiplier selected per method on validation**, reported on
  a held-out test set.
- **Theorem 3.1**: the mean of differences minimises the steering objective.
- Both PCA variants perform worst, with a mechanism E27 never gave: the
  highest-variance direction is nearly orthogonal to the behaviour direction
  (§3.1, Fig 2).

E27's fixed-α-across-estimators design is **weaker** than this on a confound the
prior work explicitly handles: magnitudes differ by method, which is why they
tune the multiplier per method. Verdicts straddling one fixed threshold largely
restate that known magnitude ordering.

**Status: controlled replication, not an original result.** Replication value is
real but modest (different models, layers, concepts; bootstrap CIs over pairs).

**The planned concatenated-PCA (PoE) run is CANCELLED** — the literature already
answers it.

**Gate failure, recorded.** The E27 gate searched my own phrasing ("does
estimator choice flip nulls?") rather than the field's phrasing ("which steering
method should be used and why?"), and an earlier audit marked this very citation
"unverifiable" when one search finds it. A false negative was treated as evidence
of absence, on the citation most damaging to my own claim.
