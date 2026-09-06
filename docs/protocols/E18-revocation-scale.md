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

*Pending. Zero E18 calls at the time of this commit.*
