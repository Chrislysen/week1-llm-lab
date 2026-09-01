# E12-X — exploratory cross-decider screen of the READY channel

**EXPLORATORY. Declared before the run, committed with zero E12-X outcomes.
Nothing this produces can become a claim.** It exists to answer one
design-gating question: *is the readiness sensitivity seen in `llama3.2:3b` a
single-model artefact?*

## Why

A latent-variable pass over every raw plan artifact (2026-09-01) found that
the plan field `ready` ("true if you consider the plan safe to execute as
written") is at **ceiling** for `aya-expanse:8b`, `qwen2.5:3b-instruct` and
`qwen2.5:7b-instruct` in every arm of E4, E8 and E11 (35–36 of 36
everywhere), so it carries no information for those deciders. It has dynamic
range in exactly two local deciders: `llama3.2:3b` (the only decider ever run
on the dependence corpus; E12 same_root 60/108 vs indep_root 32/108) and
`qwen2.5:14b-instruct` (E8: control 36/36, d1 21/36, d2 28/36, d3 23/36; E4:
23–28/36 across rule variants). `qwen2.5:14b-instruct` has never seen the
dependence corpus.

## Decider eligibility — hypothesis-blind

`qwen2.5:14b-instruct` is chosen **because its `ready` field varies** in
already-collected data (E4, E8), which is independent of any dependence
outcome. It is not chosen for any arm difference; none exists yet.

## What is run

`python e12_powered.py --model qwen2.5:14b-instruct` over the frozen E12
corpus (`ecf1f4884fa49270`), all four arms, 108 units, three chunks of 36 —
the same code, prompt, temperature (0) and parsing as E12. No code changes.
432 calls. Output: `results/e12_qwen25-14b-instruct_o{0,36,72}.{csv,json}`.
The E12 verifier section filters on `llama3.2:3b` and is unaffected.

## What is computed, fixed now

Per arm: ready rate; ordering flip rate. Paired same_root vs indep_root on
`ready` and on `flip`, with the E12 cluster permutation and cluster bootstrap
(36 instance clusters). Reported as **exploratory** beside llama's numbers.

## How it is read

- If `ready` shows no same/indep difference (or the opposite direction) while
  llama's stands: the READY dissociation is recorded as **llama-specific**;
  E14-v2 in any form is not pursued on this basis.
- If `ready` shows the same direction at a comparable size: the direction is
  **not** llama-specific among deciders with a working channel, and a
  confirmatory design (preregistered separately, fresh corpus, checker-gated)
  becomes worth costing. This screen contributes **nothing** to that design's
  statistics.
- The ordering channel at 108/36 is underpowered for equivalence in one
  decider (E10 retraction); its estimate and CI are reported, never read as a
  null.

No SESOI, no p-threshold decision, no claim. Seed and reps as E12.
