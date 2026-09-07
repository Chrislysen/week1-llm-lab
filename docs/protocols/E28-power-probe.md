# E28 — Power probe for a paired agent-communication cost study

**Status at declaration: ZERO outcomes. No model call has been made.**
Declared 2026-09-07, before any run, per repo protocol discipline.

## Why this exists

The Astra review proposes *AgentCom*: comparing communication protocols on ~12
development instances, estimating **paired differences by task**. Before
building a provenance DAG, a selective-recovery backend, a token/prefill/storage
cost model and a policy search, one number decides whether the pilot can
resolve anything at all.

This is the **E22 move**. E22 designed a rejection-circuit search, power-checked
it (baseline +0.121 against a random-ablation noise SD of 0.041, with random
ablation already removing 30–90 % of the effect), and **did not run it**. That
was the most valuable non-result in this repo. E28 applies the same test to the
proposal before any of it is built.

## The quantity that actually governs power

A paired design cancels between-instance variance in the *levels*. So the
absolute spread of run costs is **not** the relevant number — a point I had
wrong when I first proposed this probe, and correct here. What governs power is
the spread of the per-instance **difference**, which has two components with
**different remedies**:

| component | meaning | remedy |
|---|---|---|
| **SD_H** heterogeneity | instances differ in how much the protocol change saves | more instances |
| **SD_R** run noise | same instance, same protocols, re-run, lands elsewhere | repeats per instance |

A probe reporting one pooled SD cannot separate them, and therefore cannot say
what to buy. E28 measures them separately:

- **ARM H** — 8 instances × {full, budgeted}, once each.
- **ARM R** — instance 1 × {full, budgeted}, repeated 4×.

Both agents are `temperature=0`, so ARM R **measures** the instrument's realised
nondeterminism rather than assuming it away.

## Instrument

Existing `DialogueEngine`, `Budget`, and the `manage_context` hook — the natural
policy injection point, already present. Cost is realised
`prompt_tokens + completion_tokens` per `Entry`, the same quantity a recovery
study counts. Contrast is full transcript vs `RecencyBudget(120 words)`.

**Corpus hygiene:** the 12 seeds are **new**, written for this probe. They are
not the E16 dialogue corpus, which has now been used across nine studies
(E16–E23, E26) and is development material, not a valid confirmatory test set.

## Predictions (fixed before running)

1. **SD_R / SD_H < 0.3** — at temperature 0 the runs are near-deterministic, so
   nearly all spread should be genuine instance heterogeneity.
2. **Mean paired difference positive, 20–40 % of run cost** — context budgeting
   mechanically removes prompt tokens.
3. **MDE at n = 12 below 31 %** — i.e. POWERED. Paired + near-deterministic
   should be tight.

Prediction 3 is the one I expect to be least safe, and it is the one that
decides the build.

## Read rule (fixed before running)

MDE = (t<sub>.025,11</sub> + t<sub>.20,11</sub>) × SD_H / √12 = 3.077 × SD_H / √12,
expressed as a percentage of mean full-protocol cost. Against REVISE's reported
31–56 % model-call reduction:

- **MDE < 31 %** → POWERED
- **31 % ≤ MDE < 56 %** → MARGINAL
- **MDE ≥ 56 %** → UNDERPOWERED — do not build; report the floor instead.

Additionally: **if SD_R / SD_H > 0.7**, the binding constraint is repeats per
instance, not instance count, and any n-only fix is reported as insufficient.

## The limit on what a pass can mean — declared in advance

This contrast is **mechanical**: budgeting deterministically removes context
tokens. Real recovery savings depend on *where* a revision lands in a
trajectory, which is far more variable. So SD_H here is a **lower bound** on the
SD a real AgentCom study would face.

Therefore **POWERED is necessary but not sufficient.** A POWERED verdict does
not validate the proposal; it only fails to kill it. UNDERPOWERED, by contrast,
**is** decisive — if the floor cannot be cleared on the easy mechanical
contrast, the harder one is hopeless. This asymmetry is stated now so a
favourable result cannot be reported later as a green light.

## What this does not test

Revision, recovery, provenance, policy search, or task quality. Cost only.
