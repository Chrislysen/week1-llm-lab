# E24 — do inclusion and exclusion constraints move oppositely with length?

**Declared 2026-09-06 with zero E24 generations. Gated NARROW (T-2). NOT a
novelty claim: the general principle that aggregation composition affects
rankings is published (arXiv:2608.30044; ATLAS compares four aggregation
functions). The mechanism below, and its demonstration, were not found.**

## The mechanism, which is arithmetic before it is empirical

- **Inclusion** constraints — "use X at least 3 times", "at least 5 sentences",
  "include these three words" — get **monotonically easier** as a response
  lengthens. More text, more chances to satisfy.
- **Exclusion** constraints — "never use the word Y", "no digits", "no question
  marks" — get **monotonically harder**. More text, more chances to slip.

**IFEval scores both in one aggregate.** Its Keywords family contains
`include keywords` and `keyword frequency` beside `forbidden words`. If the two
types respond oppositely to length, a model's aggregate depends on the
benchmark's **inclusion:exclusion ratio**, which is an authoring choice — and
two benchmarks built from the same constraint pool in different proportions can
rank the same models differently, without either being wrong about any
individual constraint.

## Design

16 verifiable constraints, 8 inclusion and 8 exclusion, each checked by a short
function as in IFEval. 6 neutral base tasks with no overlap with the E16 corpus.
Response length pinned by instruction at **40 / 120 / 300 words** — the
technique E17 validated at ~100 % compliance. 3 × 6 × 16 = **288 generations per
model**, temperature 0.

Models: `llama3.2:3b` and `qwen2.5:7b-instruct`.

## Read rule, fixed before the first generation

Let `inc(L)` and `exc(L)` be satisfaction rates at length L, and

    DiD = (inc_long − inc_short) − (exc_long − exc_short)

- **INTERACTION CONFIRMED** if, in **at least 2 models**: `inc` rises from short
  to long, `exc` falls from short to long, and **DiD ≥ 0.15**.
- **NO INTERACTION** if DiD < 0.05, or if both types move in the same direction.
- **PARTIAL** otherwise, recorded as partial.

**Validity.** Mean response words must rise monotonically across the three
targets, or the length manipulation failed and the cell is void. Constraints
whose satisfaction is 0 or 1 at every length carry no information and are
reported separately.

**Secondary, descriptive.** Given the observed per-type rates, compute the
aggregate score a benchmark would report at inclusion:exclusion mixes of
25:75, 50:50 and 75:25, and whether the model ordering changes between them.

## Limits, stated in advance

Two models, 16 hand-written constraints, one length-control method, six tasks.
These are not IFEval's actual items and no claim is made about IFEval's
published numbers. Pinning length by instruction changes the prompt, so the
comparison is across prompts that differ in one sentence. A confirmed
interaction shows the confound is real *for these constraints*; establishing it
for a deployed benchmark would require running that benchmark.

## Files

`e24_constraint_length.py`; outputs `results/e24_<model>_o<offset>.csv`.

---

## Outcome

*Pending. Zero E24 generations at the time of this commit.*
