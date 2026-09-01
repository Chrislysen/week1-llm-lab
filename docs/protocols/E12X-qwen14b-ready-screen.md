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

---

## Outcome — 2026-09-01 (exploratory; no claim)

432 calls, parse 432/432, 0 transport retries, mean 2.6 s/call. Read with
`python screen_analysis.py --e12x qwen2.5:14b-instruct`.

| arm | ready | ready rate | flip rate |
|---|---|---|---|
| bare | 66/108 | 0.611 | 0.444 |
| filler | 43/108 | 0.398 | 0.556 |
| same_root | 95/108 | 0.880 | 0.028 |
| indep_root | 100/108 | 0.926 | 0.028 |

| contrast (instance-level) | delta | paired | p_two | 95 % CI |
|---|---|---|---|---|
| ready: same_root − indep_root | **−0.046** | 3 vs 8 | 0.28 | [−0.111, +0.018] |
| ready: filler − same_root | −0.481 | 3 vs 55 | < 0.001 | [−0.593, −0.370] |
| ready: bare − filler | +0.213 | 32 vs 9 | 0.003 | [+0.093, +0.333] |
| flip: same_root − indep_root | 0.000 | 2 vs 2 | 1.0 | [−0.037, +0.037] |
| flip: filler − same_root | +0.528 | 57 vs 0 | < 0.001 | [+0.417, +0.639] |

**Reading, per the rule fixed above.** No same/indep readiness difference in
llama's direction (sign reversed, CI includes 0). The READY dissociation is
recorded as **llama-specific**: it is absent in the only other local decider
whose `ready` field varies at all. E14-v2 in any form is not pursued.

**A model reversal, noted and not claimed.** In `qwen2.5:14b-instruct`,
corroboration *raises* readiness (filler 0.40 → same 0.88 → indep 0.93) while
in `llama3.2:3b` it *lowers* it (filler 0.97 → same 0.56 → indep 0.30). The
ordering channel is at floor under corroboration here (3 flips per arm), so
the dependence contrast on ordering is uninformative beyond "at floor".
