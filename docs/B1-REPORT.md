# B1 — bounded exploratory baseline: results

Protocol: `docs/protocols/B1-communication-baseline.md`, declared with zero
outcomes at commit `0b33996`. Harness `b1_baseline.py`, analysis
`b1_analysis.py`, raw records `results/b1_calls.jsonl`,
`results/b1_outcomes.jsonl`, smoke `results/b1_smoke_*.jsonl`.

**EXPLORATORY BASELINE. Not a novelty candidate — it has not passed
`docs/NOVELTY-GATE.md` and is not claimed to.** E27, E28 and C2 remain closed.
**All eight instances are development data.** n=8, one model, one task family:
nothing here establishes general superiority, novelty, or an effect size.

## Calls spent

| item | calls |
|---|---|
| smoke (throwaway instance `agentcom-b1-smoke`, 3 arms) | 15 |
| main comparison, 8 instances × 3 arms × 5 calls | 120 |
| exploratory follow-up | **0** — resolved from cached trajectories |
| **total** | **135 of the 160 cap** (25 unused) |

## Setting actually used

8 fresh instances, `salt="agentcom-b1"`, verified not to collide with the 36
standard ones. Exposure `source_only` → **SOURCE + DISTRACTOR only**: no
supersession, no corrupted relay, no truncation, no steering, no recovery. Every
call saw the whole dialogue. Scoring is `lineage_eval.check_plan` against the
**authored** constraints, programmatic and blind to arm label by construction.
`llama3.2:3b`, temperature 0.7 with per-call deterministic seeds, `num_predict`
400/300, all three arms per instance in one process, arm order counterbalanced
across the 6 permutations, request position logged.

## Outcomes

| instance | solo | independent | communicating |
|---|---|---|---|
| payments-chain | v=1 r=0.83 | v=2 r=0.67 | v=1 r=0.83 |
| robotics-fork | **OK** v=0 | **OK** v=0 | **OK** v=0 |
| pharmacy-join | v=2 r=0.71 | v=1 r=0.86 | v=1 r=0.86 |
| satellite-diamond | v=3 r=0.62 | v=2 r=0.75 | v=2 r=0.75 |
| brewery-twochain | v=3 r=0.57 | v=2 r=0.71 | v=2 r=0.71 |
| rail-star | **OK** v=0 | v=2 r=0.71 | v=1 r=0.86 |
| payments-diamond | **OK** v=0 | v=1 r=0.88 | **OK** v=0 |
| robotics-twochain | v=3 r=0.57 | v=1 r=0.86 | v=3 r=0.57 |

| arm | success | mean violations | mean recall | prompt tok | completion tok | **total tok** | seconds |
|---|---|---|---|---|---|---|---|
| solo | **3/8** | 1.50 | 0.789 | 17 221 | 6 639 | 23 860 | 117 |
| independent | 1/8 | 1.38 | 0.804 | 17 309 | 6 797 | 24 106 | 118 |
| communicating | 2/8 | **1.25** | **0.823** | 20 477 | 7 058 | **27 535** | 121 |

**The two outcome measures rank the arms in opposite directions.** Solo wins on
binary success (3/8); communicating wins on violations and recall. At n=8 both
gaps sit comfortably inside sampling noise — 3/8 vs 1/8 is not distinguishable —
so the honest reading is **no architecture effect is demonstrated either way**,
and the disagreement between measures is itself a caution about reporting a
single headline number.

**Equal calls are not equal cost.** All arms made exactly 40 calls, yet
communicating spent **+15.4 % total tokens over solo** (27 535 vs 23 860), almost
all of it in prompt tokens (+18.9 %) — the peer draft inflates every refine
prompt. This is the concrete demonstration of the protocol's warning.

**Position control.** With order counterbalanced: position 1 → 2/8 success,
position 2 → 1/8, position 3 → 3/8. Arm effects are not confounded with position.

## Main observation: variation is at the INSTANCE level

> **Corrected 2026-09-08** (`docs/B1-GRAPH-SHAPE-ASSESSMENT.md`). This section
> originally read "task structure dominates architecture". That is withdrawn on
> two counts. The per-shape denominators below are **arm runs on 1-2 instances**,
> not independent instances -- three arms on one instance share its wording,
> identifiers and description order, so they are correlated, not replicates; and
> shape is perfectly confounded with domain for four of the six shapes. The
> largest **within**-shape gap (diamond: 0.33 vs 2.33 mean violations) is nearly
> the entire **between**-shape range (0.00 to 2.33). Supported statement: *most
> observed variation sits at the instance level; neither an architecture effect
> nor a shape effect is identified.* Absence of a demonstrated architecture
> difference is not evidence of architectural equivalence. The table below is
> retained as the raw record.

| graph | n | success | mean violations | mean recall |
|---|---|---|---|---|
| **twochain** | 6 | **0** | **2.33** | 0.667 |
| chain | 3 | 0 | 1.33 | 0.778 |
| join | 3 | 0 | 1.33 | 0.809 |
| diamond | 6 | 2 | 1.33 | 0.833 |
| star | 3 | 1 | 1.00 | 0.857 |
| **fork** | 3 | **3** | **0.00** | 1.000 |

The spread across graph structures (0/6 to 3/3) is far larger and more consistent
than the spread across architectures (1/8 to 3/8), and **`twochain` fails in
every arm**. `twochain` is the only structure with **two disjoint dependency
chains** rather than one connected order.

## Reproducible failure: the disjoint-chain interleave

`brewery-twochain` has two independent chains — DRAIN_VESSEL → RESTART_BATCH →
STERILISE_LINE (K1/K2/K3) and RESEED_YEAST → STOP_FERMENT → SAMPLE_GRAVITY
(K4/K5/K6/K7). Violated across all runs: **K5 (11×), K7 (6×), K6 (6×), K3 (5×)** —
concentrated on the *second* chain and on the *terminal* edges of both.

Observed (all three arms, same instance):

```
communicating  refined draft: STERILISE, RESEED, STOP_FERMENT, SAMPLE_GRAVITY, DRAIN, RESTART   v=1
               aggregate:     STERILISE, RESEED, SAMPLE_GRAVITY, STOP_FERMENT, DRAIN, RESTART   v=2
solo           refined draft: DRAIN, RESEED, STERILISE, STOP_FERMENT, SAMPLE_GRAVITY            v=1
               aggregate:     DRAIN, SAMPLE_GRAVITY, STOP_FERMENT, RESEED, STERILISE            v=3
independent    refined draft: RESEED, STERILISE, DRAIN, RESTART, STOP_FERMENT, SAMPLE_GRAVITY   v=1
               aggregate:     RESEED, DRAIN, STERILISE, RESTART, SAMPLE_GRAVITY                 v=2
```

**Observation:** in each arm a refined draft had the ordering right on one more
constraint than the plan that was finally emitted; the aggregation step reordered
across the two chains and broke an edge the draft had satisfied. Aggregation
scored worse than its own best refined draft in **3 of 24 arm-instances, all
three of them on this one instance.**

**Proposed explanation, kept separate from the observation:** when two chains are
independent, many interleavings are valid, so the aggregator is free to reorder —
and reordering across chains is where the within-chain edges get broken. *This is
a hypothesis suggested by three cases on one instance. It is not tested.*

The intermediate-draft scoring uses a post-hoc identifier-scan heuristic (first
occurrence) on free-text drafts and is **exploratory**; the aggregate scores are
the declared programmatic check.

## Is anything unexplained?

Largely, **no**. That LLM planning fails on multi-constraint ordering is
well-established — [PlanBench (arXiv:2206.10498)](https://arxiv.org/abs/2206.10498)
provides PDDL-based tasks with symbolic validation and documents failure modes
including incorrect decomposition and failure to identify subgoals along the
optimal path. A 3B model scoring 6/24 on a 6-action constrained ordering task is
an unremarkable instance of that.

**One thing I could not resolve:** whether the *gradient across dependency-graph
shapes* — disjoint chains strictly hardest, fork trivial — is already
characterised. Four searches did not surface a direct treatment. Under the gate,
**that is UNRESOLVED coverage, not novelty**, and n=8 on development data with
one 3B model cannot support promoting it. It is recorded, not claimed.

## What this is retained as

**Engineering evidence**, per the protocol's own terms: a working, counterbalanced,
cost-instrumented comparison harness with programmatic blind scoring, plus the
concrete finding that at equal call count communicating costs ~15 % more tokens
and buys no demonstrated accuracy on this task.

## At most one next action

**If** anyone pursues the graph-structure gradient, it goes to
`docs/NOVELTY-GATE.md` as a **new candidate** with the field's vocabulary
(topological ordering, precedence-constrained planning, subgoal decomposition,
parallel/disjoint dependency structure), and requires **fresh confirmatory
instances** — every instance here is burned as development data — plus more than
one model. It is not a continuation of B1 and carries no novelty claim from it.
