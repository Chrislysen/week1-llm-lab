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
