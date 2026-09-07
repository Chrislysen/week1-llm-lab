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
