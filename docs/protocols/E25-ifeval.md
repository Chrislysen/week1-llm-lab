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

---

## Outcome — INCOMPLETE. Harness built and validated; the cross-model run did not fit.

**Run attempted 2026-09-07. One model completed. The declared read rule needs
≥ 4 models and is NOT evaluated. No verdict is claimed.**

### What was established

The harness works and the classification is faithful. **215 of IFEval's 541
prompts** carry an analysable instruction, giving **104 inclusion** and **144
exclusion** observations — roughly 6× the exclusion n of the hand-written
E24-C set, on the benchmark's real items.

`llama3.2:3b`, first 45 prompts (30 inclusion / 25 exclusion observations):

| kind | n | satisfied | mean response |
|---|---|---|---|
| inclusion | 30 | 0.967 | 311.7 words |
| exclusion | 25 | 0.960 | |

A single model cannot test a cross-model correlation, so **nothing is concluded
from this.**

### Why it stopped

IFEval prompts frequently request 300–500 word responses, and many analysed
prompts also carry `combination:repeat_prompt`, which multiplies output length
further. Generation exceeded the runner's 10-minute ceiling at 45, 45, 24 and 24
prompts on successive attempts across two models. Completing all five models at
215 prompts would need roughly a hundred sequential chunked runs.

**This is a wall-clock limit, not a design fault.** `e25_ifeval.py` is
committed, the dataset is cached, the verifiers are written, and the run is
resumable with `--offset` / `--limit`.

### What this does and does not do to E24

It does **not** weaken E24. That result — inclusion and exclusion moving in
opposite directions under *manipulated* length, DiD 0.500 and 0.604 at n = 48
per cell — stands on its own manipulated-length evidence.

It leaves the standing objection **open**: the mechanism has not yet been shown
on a real benchmark's items. That remains the single most valuable next step,
and it is now a matter of compute time rather than design.
