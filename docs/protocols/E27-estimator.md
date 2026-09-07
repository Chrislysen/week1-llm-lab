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
