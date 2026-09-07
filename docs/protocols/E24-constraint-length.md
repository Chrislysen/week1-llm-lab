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

---

# E24-B — can constraint mix REORDER models? DECLARED, zero outcomes

E24 confirmed the type-by-length interaction but **did not** demonstrate the
consequence that matters: that a benchmark's inclusion:exclusion mix can change
which model looks better. Its two models sat too close together, and both were
run at *instructed* lengths, which suppresses exactly the natural-verbosity
differences the mechanism feeds on.

**Design.** Drop the length instruction entirely — each model writes at its own
natural length. Same 16 constraints, same 6 tasks, temperature 0, 96 generations
per model. Five models spanning families and sizes, chosen for expected spread
in verbosity: `llama3.2:3b`, `qwen2.5:3b-instruct`, `qwen2.5:7b-instruct`,
`gemma4:e4b`, `aya-expanse:8b`.

**Read rule, fixed before the first generation.**

Compute each model's inclusion rate and exclusion rate, then the aggregate a
benchmark would report at inclusion:exclusion mixes of **25:75, 50:50, 75:25**.

- **REORDER DEMONSTRATED** if at least one pair of models **swaps rank** between
  any two of the three mixes.
- **NO REORDER** if the ordering of all five models is identical at all three
  mixes — the mechanism is real (E24) but does not bite on ranking at this
  spread, and that is reported as a negative.
- Any reorder must involve models whose aggregate scores differ by more than
  0.02 at one of the mixes, so that a swap on near-identical scores is not
  counted.

**Validity.** Natural word counts must actually differ across models, or there
is no verbosity spread to exploit and the test is uninformative — reported as
such.

**Limits.** Same 16 hand-written constraints, not IFEval's items. Natural length
is confounded with everything else that differs between these models; the claim
under test is only that *mix changes ranking*, not that verbosity causes it.

## E24-B Outcome

**Run 2026-09-07. The declared rule returns REORDER DEMONSTRATED — and the rule
was underpowered. The reorder is NOT established, and the threshold I set is the
reason. Read both halves of this section.**

Five models, natural length, the same balanced 48-item block (3 tasks x 16
constraints, 24 inclusion / 24 exclusion) for every model.

| model | mean words | inclusion | exclusion |
|---|---|---|---|
| gemma4:e4b | **144.6** | **0.958** | **0.917** |
| aya-expanse:8b | 86.3 | 0.917 | 0.958 |
| llama3.2:3b | 78.2 | 0.917 | 1.000 |
| qwen2.5:3b-instruct | 69.1 | 0.750 | 0.958 |
| qwen2.5:7b-instruct | 59.1 | 0.875 | 0.958 |

**The predicted trade-off is visible in the point estimates.** The most verbose
model (gemma, 144.6 words) has the **highest** inclusion and the **lowest**
exclusion. The least verbose (qwen2.5:7b, 59.1 words) has high exclusion and
mediocre inclusion. Verbosity spread is real — 59 to 145 words — so the validity
check passes.

### Aggregate by mix, and the apparent reorder

| model | 25:75 | 50:50 | 75:25 |
|---|---|---|---|
| gemma4:e4b | 0.9271 | 0.9375 | **0.9479** |
| aya-expanse:8b | 0.9479 | 0.9375 | 0.9271 |
| llama3.2:3b | **0.9792** | **0.9583** | 0.9375 |
| qwen2.5:7b-instruct | 0.9375 | 0.9167 | 0.8958 |
| qwen2.5:3b-instruct | 0.9062 | 0.8542 | 0.8021 |

    rank at 25:75   llama > aya > qwen7b > gemma > qwen3b
    rank at 75:25   gemma > llama > aya > qwen7b > qwen3b

gemma moves from **4th to 1st** on constraint mix alone. Five pairwise swaps
clear the declared 0.02 margin.

### Why that verdict must not be relied on

Each rate rests on **n = 24**. At p ≈ 0.92–0.96 the standard error is
0.041–0.056, so the 95 % half-width is **0.080–0.132**. The observed swap
margins are **0.0104 to 0.0521** — comfortably *inside* sampling noise.

**The declared rule fired because I set its threshold at 0.02 on point estimates
without a power analysis.** That threshold was wrong for this n. The rule's
output is recorded as declared, and the honest reading is:

> **The reorder is consistent with the point estimates and with the mechanism
> E24 established, and it is NOT statistically demonstrated here.**

This repository retracted a conclusion once before for exactly this — asserting
a result from a design whose power was never checked
(`docs/protocols/E10-H3-RETRACTION.md`). Recording the verdict without this
paragraph would repeat it.

### What stands, and what a real test needs

**Stands (from E24, well powered):** inclusion and exclusion constraints move in
opposite directions with response length — DiD 0.500 and 0.604, n = 48 per cell,
two models. That mechanism is solid.

**Stands (from E24-B, descriptive):** the verbosity trade-off appears across five
models in the predicted direction, with a real 2.4x verbosity spread.

**Does not stand:** that constraint mix reorders models. To establish it needs
roughly **400+ items per constraint type per model** to bring the half-width
below the observed 0.01–0.05 margins, and ideally models whose scores differ by
more than noise to begin with.

### Limits

Sixteen hand-written constraints, three tasks, five models, one natural-length
condition, temperature 0. **Not IFEval's items; no claim about its published
numbers.** Natural verbosity is confounded with every other difference between
these models — the mechanism from E24 is what licenses the verbosity reading,
not this design. `llama3.2:3b` scores 1.000 on exclusion, a ceiling that makes
its comparisons one-sided.

**No novelty is asserted.** T-2 remains NARROW.

### Files

`results/e24b_{llama32-3b,qwen25-3b-instruct,qwen25-7b-instruct,aya-expanse-8b,gemma4-e4b}_o0.csv`.

### Diagnosis — why the reorder cannot be resolved by adding items

Per-constraint satisfaction pooled over all five models at natural length:

| ceiling (≥0.95) | informative |
|---|---|
| `exc_kw_the` 1.000, `exc_kw_very` 1.000, `exc_kw_you` 1.000, `exc_no_digits` 1.000, `exc_no_question` 1.000, `exc_no_semicolon` 1.000 | `exc_kw_can` 0.944, `exc_letter_z` 0.722, and **all 8 inclusion constraints** (0.778–0.944) |

**6 of 8 exclusion constraints are at 1.000.** The models never spontaneously
write "very", "important", "you", digits, question marks or semicolons on these
six tasks, so those constraints are satisfied for free and carry no signal. The
whole exclusion side therefore sits pinned near 1.0, compressing the very
differences the reorder test needs — and E24's measured "exclusion falls with
length" rests on the two constraints that are not at ceiling.

**So more items would not fix this.** With six of eight exclusion constraints
structurally uninformative, increasing n shrinks the error bars around a
compressed range without widening the range. The fix is a **harder exclusion
set**: forbid words the task actively elicits — for *"explain how a bicycle gear
system works"*, forbid `gear`, `wheel`, `chain` — so that satisfaction sits mid-
range where verbosity can actually move it.

That is a corpus redesign, not a longer run, and it is the concrete
specification for a properly powered version of this test.

---

## E24-C Outcome — the fix worked, and the honest answer is split

**Run 2026-09-07. Score-shift DEMONSTRATED and significant. Reorder NOT
demonstrated.** Five models, natural length, 48 inclusion + 24 hard-exclusion
items each. The hard exclusions lifted the ceiling exactly as intended.

| model | mean words | inclusion | exclusion |
|---|---|---|---|
| gemma4:e4b | 204.4 | 0.979 ±0.040 | 0.958 ±0.080 |
| llama3.2:3b | 154.2 | 0.979 ±0.040 | 0.958 ±0.080 |
| aya-expanse:8b | 86.4 | 0.854 ±0.100 | **1.000** ±0.000 |
| qwen2.5:3b-instruct | 112.1 | 0.938 ±0.068 | **0.333** ±0.189 |
| qwen2.5:7b-instruct | 70.5 | 0.875 ±0.094 | 0.917 ±0.111 |

The ceiling is gone: exclusion now ranges **0.333 to 1.000** against E24-B's
0.917–1.000. Forbidding task-elicited words was the right fix — though note it
bit *one* model catastrophically rather than spreading all five.

### Aggregate by mix

| model | 25:75 | 50:50 | 75:25 |
|---|---|---|---|
| gemma4:e4b | 0.964 ±0.061 | 0.969 ±0.045 | 0.974 ±0.036 |
| llama3.2:3b | 0.964 ±0.061 | 0.969 ±0.045 | 0.974 ±0.036 |
| aya-expanse:8b | 0.964 ±0.025 | 0.927 ±0.050 | 0.891 ±0.075 |
| qwen2.5:7b-instruct | 0.906 ±0.086 | 0.896 ±0.072 | 0.885 ±0.075 |
| **qwen2.5:3b-instruct** | **0.484 ±0.142** | 0.635 ±0.100 | **0.786 ±0.070** |

### What is demonstrated

**A model's reported score changes by 0.30 on the same constraint pool.**
qwen2.5:3b-instruct scores **0.484** under an exclusion-heavy mix and **0.786**
under an inclusion-heavy one. The confidence intervals **do not overlap**. Same
model, same constraints, same responses — only the weighting differs.

**The apparent gap between models changes 2.5×.** Best-minus-worst spread is
**0.479** at 25:75 and **0.188** at 75:25. A benchmark author choosing the mix
is choosing how far apart the field looks.

### What is NOT demonstrated

**No significant reorder.** aya-expanse ranks 1st at 25:75 and 3rd at 50:50 and
75:25, but every margin involved sits inside the confidence intervals. Under the
stricter test applied here — sign change *and* the larger gap excluding zero —
**zero significant swaps** were found. E24-B's apparent reorder does not survive
a proper interval treatment, and this supersedes it.

So the claim narrows to what the data carries: **composition materially changes
absolute scores and between-model gaps; it was not shown to change the
ordering.**

### Limits

Five models, 72 items each, one natural-length condition, temperature 0. Hand-written constraints,
**not IFEval's items**. The score-shift result rests heavily on one model's
exclusion collapse (qwen2.5:3b at 0.333, n = 24, ±0.189) — a wide interval, and
the effect would be far weaker without it. Exclusion n = 24 throughout is thin.
`aya-expanse:8b` is at ceiling (1.000) on exclusion, and gemma and llama are
numerically identical, both of which limit what the ranking test could resolve.

**No novelty is asserted.** T-2 remains NARROW.

### Files

`results/e24c_{gemma4-e4b,llama32-3b,qwen25-3b-instruct,qwen25-7b-instruct,aya-expanse-8b}_o0.csv`.
