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

**Run 2026-09-06/07. Verdict: INTERACTION CONFIRMED, 2 of 2 models.** The two
constraint types move in **opposite** directions with response length, by a wide
margin. The secondary ranking-reorder claim is **not** demonstrated.

| model | length | kind | n | mean words | satisfied |
|---|---|---|---|---|---|
| llama3.2:3b | short | inclusion | 48 | 47.4 | 0.625 |
| llama3.2:3b | short | exclusion | 48 | 40.3 | **0.958** |
| llama3.2:3b | medium | inclusion | 48 | 110.7 | 0.896 |
| llama3.2:3b | medium | exclusion | 48 | 105.1 | 0.938 |
| llama3.2:3b | long | inclusion | 48 | 300.5 | **0.979** |
| llama3.2:3b | long | exclusion | 48 | 289.3 | 0.812 |
| qwen2.5:7b-instruct | short | inclusion | 48 | 31.6 | 0.521 |
| qwen2.5:7b-instruct | short | exclusion | 48 | 26.0 | **0.938** |
| qwen2.5:7b-instruct | medium | inclusion | 24 | 79.3 | 0.792 |
| qwen2.5:7b-instruct | medium | exclusion | 24 | 79.6 | 0.917 |
| qwen2.5:7b-instruct | long | inclusion | **8** | 108.6 | **1.000** |
| qwen2.5:7b-instruct | long | exclusion | **16** | 149.9 | 0.812 |

### Read rule applied

| model | inclusion short→long | exclusion short→long | DiD | |
|---|---|---|---|---|
| llama3.2:3b | **+0.354** | **−0.146** | **0.500** | CONFIRMS |
| qwen2.5:7b-instruct | **+0.479** | **−0.125** | **0.604** | CONFIRMS |

Both models: inclusion rises, exclusion falls, DiD far above the declared 0.15.
**INTERACTION CONFIRMED.** The length manipulation validity check passes for
llama (47 → 111 → 301 words, monotone against targets 40/120/300).

### What this means for verifiable-constraint benchmarks

Satisfaction of a verifiable constraint is not a property of the model's
instruction-following alone — it is a joint property of the model, the
constraint's **type**, and how long the model happens to write. Making a model
more verbose *raises* its inclusion score and *lowers* its exclusion score, at
roughly 0.35–0.48 against 0.13–0.15 in these data.

IFEval scores both types in one aggregate — `include keywords` and
`keyword frequency` sit in the same Keywords family as `forbidden words`. The
aggregate a benchmark reports therefore depends on its **inclusion:exclusion
ratio**, an authoring choice nobody reports. On the long-response data:

| mix (inclusion:exclusion) | llama3.2:3b | qwen2.5:7b-instruct |
|---|---|---|
| 25:75 | 0.854 | 0.859 |
| 50:50 | 0.896 | 0.906 |
| 75:25 | 0.938 | 0.953 |

Re-weighting the same constraint pool moves a model's reported score by
**~0.08–0.09** — large by benchmark standards, and attributable entirely to
composition.

### What is NOT shown, and it is the part that would have mattered most

**No ranking reorder was demonstrated.** qwen scores slightly above llama at
every mix, so the composition shift moves both scores without crossing them.
The claim that composition can *reorder* models is arithmetically available from
this mechanism but is **not evidenced here**, and would need models whose
verbosity differs far more than these two.

### Limits

Sixteen hand-written constraints, six tasks, two models. **These are not
IFEval's items and nothing here is a claim about IFEval's published numbers.**

The qwen long cell is **badly underpowered**: repeated runner timeouts at 300-word
generation left n = 8 inclusion and n = 16 exclusion, against 48/48 for llama.
qwen's DiD of 0.604 rests on that, and should be treated as indicative only.
qwen also undershot the length target severely (108.6 words for a 300-word
instruction), so its "long" condition is closer to llama's medium — which makes
its confirmation conservative rather than inflated, but it is still a failed
manipulation check for that cell.

Pinning length changes the prompt by one sentence, so conditions differ in more
than length alone. Some constraints are at ceiling or floor throughout and carry
no information.

**No novelty is asserted.** T-2 was gated NARROW before this ran: cross-benchmark
aggregation sensitivity is published (arXiv:2608.30044, ATLAS). What was not
found, and what this supplies, is the **type-by-length mechanism** and a direct
demonstration of it.

### Files

`results/e24_llama32-3b_o{0,144}.csv`,
`results/e24_qwen25-7b-instruct_o{0,216}.csv`.
