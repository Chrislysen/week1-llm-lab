# E18 — conceptual replication: does revocation inertia fall with scale?

**REPLICATION STUDY. Declared 2026-09-06 with zero E18-specific outcomes.
It tests SOMEONE ELSE'S published claim on this repository's independent
instrument. The contribution, if any, is the replication itself — so a prior-art
gate is not the relevant test here, and no novelty is asserted.**

## The claim being tested

**arXiv:2608.12599** — *Dead text or binding clause? Measuring and restoring
constraint influence in black-box LLM dialogues* (Haoyuan Zhu, 12 Aug 2026).
Multi-turn dialogue in which a user **revokes** a constraint; models keep
enacting the withdrawn requirement, a failure the paper names **behavioural
relapse / revocation inertia**. Reported:

> relapse at an **8B** operating point climbs **0.011 → 0.403** as constraint
> load grows, **while stronger models sit at floor**

This paper is the one that retired candidate S-O on 2026-09-05. Having been
killed by it, the honest next move is to check whether it holds here.

## What is and is not replicated

**Tested:** the *scale* half — does revocation inertia decrease with model size
within a single family?

**Not tested:** the constraint-load half. This corpus has 2–3 required
constraints per instance, fixed; load is not a manipulable factor here.

**This is a CONCEPTUAL replication, not a direct one.** The measure differs:
arXiv:2608.12599 measures relapse in its own dialogues; E18 measures the
inclusion rate of a constraint that was **proposed and then explicitly rejected
in the very next turn and never replaced** (E16's `rejected` status) in a final
plan. Same phenomenon, different instrument and different operationalisation.
A non-replication here would therefore bound the claim's generality, not
falsify the paper.

## Design

The E16 corpus (hash `70f136a47f5779c8`) and the E16 runner, unmodified, at
\|vocab\| = 6. One family, three scales:

| decider | free length | plan length pinned at 4 |
|---|---|---|
| qwen2.5:3b-instruct | **have** (E16 stage 1) | **have** (E17) |
| qwen2.5:7b-instruct | to run | to run |
| qwen2.5:14b-instruct | **have** (E16 stage 1) | to run |

**Both length conditions are run deliberately.** arXiv:2608.17183 and
LabSafety Bench establish that apparent model-size differences in safety and
adherence measures are contaminated by output length — more verbose models emit
more items and so score differently for reasons unrelated to the behaviour. The
`free` ladder is the naive comparison; the `pin4` ladder holds plan length
identical across scales and is the one that can support a scale claim. E17
showed on this very instrument that the `rejected` rate moves with plan length
and menu size, so the uncontrolled comparison is known to be unsafe here.

E16's own declaration and outcome are **unchanged** — its three declared
deciders and its NOT PURSUED verdict stand. E18 adds a fourth model for a
different question and records its results under its own name.

## Predictions, fixed before the first call

Under the claim, revocation inertia falls monotonically with scale:

    rejected(3B) > rejected(7B) > rejected(14B)

in **both** length conditions. Existing points: `free` 0.438 (3B) and 0.062
(14B); `pin4` 0.542 (3B).

## Read rule, fixed before the first call

- **REPLICATES** if `rejected` falls monotonically across 3B → 7B → 14B in the
  `pin4` ladder (the length-controlled one), and the 3B–14B gap exceeds 0.10.
- **FAILS TO REPLICATE** if the `pin4` ladder is non-monotonic, or the 3B–14B
  gap is below 0.10.
- The `free` ladder is reported alongside as the naive comparison. **If the two
  ladders disagree, that disagreement is the result** and is reported as such —
  it would be direct evidence that the length confound matters for this claim.

**Validity.** Parse rate ≥ 0.95 per cell; `pin4` mean \|plan\| within
[3.4, 4.6] or that cell is void.

**Inference.** 96 `rejected` units per cell, clustered by instance;
instance-level bootstrap CIs, 2 000 reps, seed 20260906.

## What cannot follow

Nothing about S-O, which stays retired. No claim of novelty: the hypothesis is
someone else's and is already published. Three scales in one family on one
corpus is a narrow test, and a positive result would show only that the
direction holds here.

## Files

Reuses `e16_zombie_screen.py` (free) and `e17_menu_law.py` (pin4). Outputs
`results/e16_qwen25-7b-instruct_full_o*.csv` and
`results/e17_qwen25-{7b,14b}-instruct_v6_pin4_o*.csv`.

---

## Outcome

**Run 2026-09-06. Verdict: REPLICATES.** Revocation inertia falls monotonically
with scale in the length-controlled ladder, and the 3B–14B gap is far above the
declared 0.10 threshold. Parse rate 1.000 in all six cells; `pin4` mean |plan|
exactly 4.00 in all three.

### The two ladders, \|vocab\| = 6, qwen2.5 family

| arm | size | mean \|plan\| | **`rejected`** | 95 % CI | `never` | `accepted` |
|---|---|---|---|---|---|---|
| `free` | 3B | 3.59 | **0.438** | [0.333, 0.543] | 0.510 | 0.979 |
| `free` | 7B | 2.28 | **0.062** | [0.020, 0.112] | 0.229 | 0.969 |
| `free` | 14B | 2.71 | **0.062** | [0.021, 0.108] | 0.385 | 1.000 |
| `pin4` | 3B | 4.00 | **0.542** | [0.421, 0.656] | 0.573 | 0.969 |
| `pin4` | 7B | 4.00 | **0.250** | [0.162, 0.341] | 0.573 | 0.990 |
| `pin4` | 14B | 4.00 | **0.135** | [0.074, 0.200] | 0.656 | 1.000 |

### Read rule applied

`pin4` ladder: **0.542 → 0.250 → 0.135**, monotone decreasing, 3B–14B gap
**0.407** ≥ 0.10 → **REPLICATES**. The 3B–7B separation is clean (CIs
disjoint); the 7B–14B separation is suggestive only (CIs overlap on
[0.162, 0.200]) and is not claimed as established.

The `free` ladder agrees in direction — 0.438 → 0.062 → 0.062 — but **7B and
14B are tied at floor**.

### The two ladders agree in direction and differ in resolution

This is worth recording because the study was designed to catch exactly this.
Under free length the two larger models are indistinguishable at 0.062: the
naive comparison hits a floor and loses the gradient. Pinning plan length at 4
forces each model to commit four identifiers and **separates them, 0.250 vs
0.135**.

The confound the design was built against is visible in the `free` column:
mean |plan| is **3.59 / 2.28 / 2.71**, *non-monotonic* in scale, and the `free`
`never` rate tracks it (0.510 / 0.229 / 0.385) rather than tracking scale —
exactly the menu-chance behaviour E17 documented. With |plan| pinned, `never`
flattens to 0.573 / 0.573 / 0.656. So the length confound is real and
measurable on this instrument; here it did not reverse the scale conclusion,
but it did erase the 7B–14B difference.

### The effect is specific to revocation, not general inclusion

`never` is **identical at 0.573 for 3B and 7B** under `pin4` while `rejected`
more than halves (0.542 → 0.250). Whatever changes with scale is not a
general shift in how much the model puts in a plan; it is specific to a
constraint that was explicitly rejected. That is the control the claim needs,
and it holds.

### What this does and does not show

It supports the *direction* of arXiv:2608.12599's scale finding — "stronger
models sit at floor" — on an independent instrument, an independent corpus and
a different operationalisation, with plan length controlled.

It does **not** test that paper's constraint-load half, which this corpus
cannot vary. It is three scales in one family on one corpus; the 7B–14B step
is not established. And it asserts **no novelty whatsoever**: the hypothesis is
someone else's, published, and was the paper that retired S-O. The contribution
is the replication and the length control, nothing more.

S-O stays retired.

### Files

`results/e16_qwen25-7b-instruct_full_o0.csv/.json`,
`results/e17_qwen25-7b-instruct_v6_pin4_o0.csv/.json`,
`results/e17_qwen25-14b-instruct_v6_pin4_o{0,72}.csv/.json`. The 3B and 14B
`free` cells are E16 stage 1, unmodified; the 3B `pin4` cell is E17.

---

# E18-B — EXTENSION, declared 2026-09-06 with zero outcomes

E18 tested three scales in **one** family. This extension asks a different
question, so it is declared separately before any call.

**Question.** Is the scale effect large relative to *between-family* variation
at fixed scale? Existing data already shows a gap the scale story does not
predict: at 3B, `rejected` under `pin4` is **0.219 (llama3.2:3b)** versus
**0.542 (qwen2.5:3b-instruct)** — a 2.5× family difference at identical scale
and identical plan length.

**Why it matters.** arXiv:2608.12599 reports relapse falling with capability
("stronger models sit at floor"). If between-family spread at one scale is
comparable to, or larger than, the within-family spread across a 4.7× parameter
range, then capability is not the controlling variable and the rule is weaker
than it reads. This **bounds** a published claim; it does not contradict it.

**Design.** `pin4`, \|vocab\| = 6, corpus and runner unchanged. Adds
`aya-expanse:8b`, `gemma4:e4b` and `qwen3:14b` to the four cells already held
(llama3.2:3b, qwen2.5:3b/7b/14b-instruct). Five families, ~3B–14B.

**Read rule, fixed before the first call.**

- **SCALE DOMINATES** if the spread of `rejected` across families within one
  scale band (3–4B: llama3.2:3b, qwen2.5:3b, gemma4:e4b) is **less than half**
  the qwen within-family 3B→14B spread of 0.407.
- **FAMILY DOMINATES** if that within-band spread is **≥ 0.407**, i.e. at one
  scale the families differ by at least as much as 3B differs from 14B.
- Anything between is **MIXED** and is recorded as mixed.

**Validity.** Parse ≥ 0.95 and `pin4` mean \|plan\| in [3.4, 4.6] per cell, or
the cell is void and is reported void. `qwen3:14b` is a reasoning model and may
emit thinking tokens that break the frozen validator — a void cell there is an
expected and acceptable outcome, not a reason to change the parser.

**No novelty is asserted by this extension either.** Any move toward a claim
requires a fresh adversarial web-search gate on the bounding result itself.

## E18-B Outcome

**Run 2026-09-06. Verdict: FAMILY DOMINATES.** Six models, five families,
3B–14B, all at \|vocab\| = 6 with plan length pinned at 4. Parse rate 1.000 in
every cell; mean \|plan\| 3.99–4.03 in every cell; no cell void.

| model | size | **`rejected`** | 95 % CI | `never` | \|plan\| |
|---|---|---|---|---|---|
| gemma4:e4b | ~4B | **0.094** | [0.033, 0.155] | 0.583 | 4.00 |
| llama3.2:3b | 3B | **0.219** | [0.134, 0.309] | 0.562 | 3.99 |
| qwen2.5:3b-instruct | 3B | **0.542** | [0.421, 0.656] | 0.573 | 4.00 |
| qwen2.5:7b-instruct | 7B | **0.250** | [0.162, 0.341] | 0.573 | 4.00 |
| aya-expanse:8b | 8B | **0.219** | [0.141, 0.295] | 0.552 | 4.03 |
| qwen2.5:14b-instruct | 14B | **0.135** | [0.074, 0.200] | 0.656 | 4.00 |

### Read rule applied

Spread within the 3–4B band: **0.542 − 0.094 = 0.448**, against the qwen
within-family 3B→14B spread of **0.407**. 0.448 ≥ 0.407 → **FAMILY DOMINATES**.

At one scale band, three families differ by **more** than one family differs
across a 4.7× parameter range. The CIs for the band extremes are disjoint
(gemma [0.033, 0.155] vs qwen-3B [0.421, 0.656]), so the band spread is not a
sampling artefact.

### The single most striking fact

**`gemma4:e4b`, the smallest model in the set, has the lowest revocation
inertia of all six — 0.094 — lower than `qwen2.5:14b-instruct` at 0.135 and
five times lower than `qwen2.5:3b-instruct` at the same scale.** Ordered by
parameter count the series is 0.094, 0.219, 0.542, 0.250, 0.219, 0.135: there
is no monotone relation with scale across families.

### What this does to the claim under test

E18 replicated arXiv:2608.12599's scale direction **within** the qwen2.5
family, and that stands. E18-B bounds it: capability is **not** the controlling
variable across families. "Stronger models sit at floor" holds as a
within-family regularity here and fails as a general rule — a ~4B model sits at
the floor while a 3B model from another family sits five times above it.

This **bounds** a published claim on an independent instrument. It does not
contradict the paper, whose within-family and within-benchmark result is not
in question.

### The control holds throughout

`never` is flat across all six models (0.552–0.656) while `rejected` varies
5.8×. With plan length pinned, whatever differs between these models is
specific to handling an explicit rejection, not a general difference in how
much they put in a plan. That is the same control E18 established, now across
five families.

### Limits

One corpus, one pinned length, one menu size, one operationalisation of
revocation. Family and training data are confounded with everything else that
differs between these models — "family" here is a label for that bundle, not a
mechanism. `qwen3:14b` was not run. No mechanism is proposed and none is
implied.

**No novelty is asserted.** "Family matters more than scale" is a common
observation in benchmark work, and this repository's own E13-X already found a
normative-backfire effect to be llama-specific. Any move toward a claim needs a
fresh adversarial web-search gate on the bounding result itself.

### Files

`results/e17_{gemma4-e4b,aya-expanse-8b}_v6_pin4_o*.csv/.json` plus the four
cells already held.

### E18-B addendum — `qwen3:14b` NOT COMPLETED

The declared design named `qwen3:14b` as a sixth family. It was attempted and
**abandoned**, and the cell is reported as not run.

A 12-dialogue pilot parsed cleanly (parse 1.000, mean |plan| 4.00) and gave
`rejected` **0.000 over 7 units** — suggestive against `qwen2.5:14b-instruct`'s
0.135 at the same scale, and interesting because `qwen3:14b` is a reasoning
model. **n = 7 is far too small to report and nothing is concluded from it.**

The arm was abandoned on cost, not on results: `qwen3:14b` runs at ~36 s per
dialogue (~86 minutes for a full arm) with high variance — a 12-dialogue chunk
that took 7m11s on one attempt exceeded the 10-minute harness limit on the
next. Completing it would have taken roughly a dozen sequential foreground
runs for a cell that cannot change the E18-B verdict, which the 3–4B band had
already determined.

The reasoning-vs-non-reasoning comparison at fixed scale is a genuinely
separate question and would need its own declaration, its own gate, and a
runner that tolerates long generations.
