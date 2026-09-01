# E13-X — exploratory cross-family screen of the normative-principle backfire

**EXPLORATORY. Declared before the run, committed with zero E13-X outcomes.
Nothing this produces can become a claim.** It decides one thing: whether an
effect seen post-hoc in one decider is worth a preregistered confirmation.

## The candidate it screens

In E13 (`llama3.2:3b`, frozen E12 units, 108 units in 36 clusters), adding
one frozen sentence of normative principle to the instruction —

> "Multiple reports derived from the same underlying evidence should not be
> treated as multiple independent confirmations. Distinct independent evidence
> may provide additional corroborative weight."

— together with the `identify` structured request, **raised adoption of the
unsupported contradiction** pooled over both dependence arms: +0.1019, 29
units flipped more vs 7 fewer (n = 216 paired units), instance-level
permutation p = 0.0064 (re-derived 2026-09-01 from `results/e13_llama32-3b_o*.csv`).
The same structured request without the principle (`identify`) did nothing
(+0.0139, p = 0.79); the task-irrelevant `sham` did nothing (+0.0093,
p = 0.92); `gold` went the other way (−0.0372, p = 0.07). This was **not a
preregistered E13 contrast** (E13's secondary family compared within-arm
differentiation, not pooled adoption) and it is one model.

## Decider eligibility — hypothesis-blind

Every local decider that has a non-degenerate ordering channel on this
corpus family qualifies; E11 showed `aya-expanse:8b`, `qwen2.5:7b-instruct`
and `llama3.2:3b` all have flip rates between 0.06 and 0.83 across arms.
Screened here: `aya-expanse:8b`, `qwen2.5:7b-instruct`, `qwen2.5:14b-instruct`
(the last for its size; its E8 ordering channel is also non-degenerate).
None is chosen for any intervention difference; none exists yet.

## What is run

`e13x_backfire_screen.py`: E13's frozen prompts and scorer, arms `default`,
`identify`, `normative` × both dependence levels × 108 units = 648 calls per
decider, in three chunks of 36 units. Nothing in E13's code or files changes.

## What is computed, fixed now

Per decider: flip rate per (arm, dependence); paired within-unit
`normative − default`, `identify − default` and `normative − identify` on
the flip indicator, pooled over dependence, with instance-level sign-flip
permutation (20 000 reps, seed 20260901) and instance-level bootstrap CI;
parse rates; the recognition fields as descriptive only.

## How it is read

- `normative − identify` positive and comparable in size (≥ +0.05) in **at
  least two** of the three screened deciders → the backfire is not
  llama-specific; a confirmatory E15 (fresh corpus, preregistered, checker-
  gated, with the principle split into its two sentences as the mechanism
  test) becomes worth costing. This screen contributes nothing to E15's
  statistics.
- Otherwise → recorded as **llama-specific**, not pursued.

No SESOI, no p-threshold decision, no claim.

---

## Outcome — 2026-09-02 (exploratory; no claim)

Read with `python screen_analysis.py --e13x <model>`. Parse ≥ 0.991 in every cell; 0 transport retries.

| decider | normative − default | identify − default | **normative − identify** (the principle) |
|---|---|---|---|
| llama3.2:3b (E13, re-derived) | +0.1019 (29 vs 7, p 0.0064) | +0.0139 (17 vs 14, p 0.79) | **+0.0880 (26 vs 7, n=216, cluster p=0.0058)** |
| aya-expanse:8b | +0.0648 (24 vs 10, p 0.07, CI [0.000, +0.125]) | +0.0278 (19 vs 13, p 0.49) | **+0.037** (12 vs 4, p 0.12, CI [0.000, +0.079]) |
| qwen2.5:7b-instruct | −0.1628 (3 vs 38, p < 0.001) | −0.1667 (4 vs 40, p < 0.001) | **+0.0047** (10 vs 9, p 1.0, CI [−0.042, +0.056]) |

**Reading, per the rule fixed above.** The principle's effect is ≥ +0.05 in
neither Aya (+0.037) nor Qwen-7B (+0.005), so the 'at least two of three' rule
cannot be met whatever Qwen-14B would show; **the Qwen-14B run was not made**
(the rule was already decided, and the decision is recorded here before any
further call). The backfire is **llama-specific** and, with the prior-art
verdict (KAIROS on the same model), C14 is closed.

**Observed and not claimed.** The *structured request itself* (`identify`)
reduces adoption of the unsupported contradiction by 0.17 in Qwen-7B (4 vs
40 units, both dependence arms) while doing nothing in llama (+0.01) or Aya
(+0.03); the principle adds nothing on top of it in Qwen-7B. A metacognitive
prompt that helps one family and not two others is an exploratory
observation with an obvious reviewer (KAIROS/BenchForm report exactly such
model-specific prompt effects) and is not pursued.

`ready` was at ceiling (≥ 0.991) in every cell for both deciders, as expected.
