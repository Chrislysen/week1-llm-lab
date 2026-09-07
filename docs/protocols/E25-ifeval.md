# E25 — does the type-by-length confound appear on IFEval's real items?

**Declared 2026-09-07 with zero E25 generations. Closes the standing objection
to E24/E24-C: those used 16 hand-written constraints. This uses IFEval's actual
541 prompts and its actual instruction types. NOT a novelty claim; T-2 remains
NARROW.**

## Classification, from IFEval's own instruction ids and kwargs

| kind | IFEval instruction ids | n obs |
|---|---|---|
| **inclusion** — easier when longer | `keywords:existence`, `keywords:frequency` (relation *at least*), `length_constraints:number_words` (relation *at least*) | **104** |
| **exclusion** — harder when longer | `keywords:forbidden_words`, `punctuation:no_comma`, `keywords:frequency` (*less than*), `length_constraints:number_words` (*less than*) | **144** |

215 of the 541 prompts carry at least one analysed instruction. Every other
instruction type — formatting, casing, language, structure, combination — is
length-neutral or ambiguous and is **excluded from the analysis rather than
guessed at**.

Scoring is IFEval's **instruction-level** convention: each target instruction is
verified independently, so a prompt with several contributes one observation
each. Verifiers reimplement IFEval's semantics from its `kwargs`.

## Prediction, fixed before the first generation

Across models, mean response length should correlate **positively** with
inclusion satisfaction and **negatively** with exclusion satisfaction.

## Read rule, fixed before the first generation

Over the models run (≥ 4):

- **CONFOUND CONFIRMED ON REAL ITEMS** if the sign of the correlation between
  mean response words and satisfaction is **positive for inclusion and negative
  for exclusion**, and the two type-specific rates are separated by more than
  their 95 % intervals in at least one model.
- **NOT CONFIRMED** if the two correlations share a sign, or neither separates.
- **INCONCLUSIVE** otherwise.

Secondary, descriptive: the aggregate an IFEval-style report would give at
inclusion:exclusion mixes of 25:75, 50:50, 75:25, with intervals, and whether
any model ordering changes beyond those intervals.

## Limits, stated in advance

Response length here is **not manipulated** — it is each model's natural output
on IFEval's own prompts, so length is confounded with everything else that
differs between models. E24 supplies the manipulated-length evidence; E25 tests
whether the pattern shows up on real items. Some IFEval prompts carry an
explicit length instruction, which is itself one of the analysed types; that is
inherent to the benchmark and is not corrected for. Verifiers are a
reimplementation, not IFEval's official harness, so absolute rates are not
comparable to published IFEval numbers — only the between-type contrast is used.

## Files

`e25_ifeval.py`; outputs `results/e25_<model>_o<offset>.csv`.

---

## Outcome

*Pending. Zero E25 generations at the time of this commit.*
