# Phase B — recipient snapshot-and-replay observability

**Status: DECLARED, ZERO OUTCOMES, NOT AUTHORISED TO RUN.** No model call has
been made. Declared 2026-09-08, before any run, per repo discipline.

**Nothing here is a learned controller and nothing here is claimed to be novel.**
Phase B measures whether subset effects are *observable and stable enough* to be
worth learning. It fits no coefficients, trains no policy, and makes no
comparison against RepoShapley, QUBO evidence selection, ProxySPEX, or any other
published method. Those comparisons belong to Phase C and are not attempted here.

## Question

At a single recipient decision point, replayed under controlled delivered
subsets:

1. **Qualification.** Can the receiver solve the task at all when given the full
   evidence? If not, the study is about the receiver, not about communication.
2. **Headroom.** Do affordable subsets differ in outcome, or does every subset
   above some trivial size succeed / fail alike?
3. **Approximation error.** Would a degree-2 form, fitted to *this* table, pick a
   different subset than the exact table does? (An in-sample diagnostic of
   representation adequacy — **not** a generalisation result.)

## Instrument (already built, no model calls used)

- `agentcom_bundle.py` — shared schema (`SCHEMA_VERSION = "agentcom-bundle/1"`),
  `Candidate` / `DecisionPoint` / `SubsetOutcome`, rendered-bundle budget
  accounting, exact hard-budget selection, and `SnapshotPolicy`, an **opt-in**
  `ContextPolicy` whose default behaviour is a recording pass-through.
- `test_agentcom_bundle.py` — 13 deterministic mechanism tests, zero model calls.

`context.py`, `engine.py`, `finalise.py`, every frozen protocol, every result
file and the E16 corpus are **unmodified**.

## Design

- **Tasks.** 8 fresh instances from an existing generator with executable
  scoring, held apart from every burned corpus. These are **8 independent
  development units** — recipient contexts, subsets and decoding seeds derived
  from one task are correlated variants of that task, not replicates.
- **Recipient contexts.** 2 per task (e.g. the recipient already holds one
  message's information, or does not), which is the contrast the direction rests
  on.
- **Candidates.** 4 authored messages per decision point → **16 subsets**
  enumerated exhaustively. Authored, so this isolates *delivered information*; it
  measures nothing about spontaneous message generation and supports no
  architecture claim.
- **Scoring.** Executable check on the emitted action, blind to subset by
  construction. Primary outcome is task success; violations and tokens recorded.
- **Budget charge.** `serialised_cost` on the rendered bundle, separators and
  header included. `additive_estimate` is logged alongside so the gap stays
  visible; it is never the charge.
- **Records.** Every call writes a `DecisionPoint` + `SubsetOutcome` pair
  carrying the literal recipient prompt, candidate pool, rendering, model
  revision, decoding options, process/session id, request position and response.
- **Collection discipline.** Within-process randomised subset order, position
  logged, comparable scheduling across conditions — the E28-C lesson applied at
  design time.

## Call accounting — ceiling 288, one receiver model

| item | calls |
|---|---|
| qualification / smoke on separate fixtures | 16 |
| subset table: 8 tasks × 2 contexts × 16 subsets | 256 |
| logged retry / diagnostic reserve | 16 |
| **ceiling** | **288** |

**Every call counts, including failures and retries. There are no unlogged smoke
runs.** Sender generation, further models, repetitions and the length/position
controls each need their own separately counted allocation and are **not** in
this ceiling.

This is an execution estimate, **not** a power analysis and **not** an
authorisation. One completion per subset estimates a *realised* outcome, not a
stable expected effect.

## Read rules, fixed in advance

- **Best-of-subsets from a single realisation is an optimistic observed
  envelope, not an oracle performance estimate.** Any subset that looks best must
  be re-run in a fresh **process** before the gap is treated as real. (Amendment
  1 corrects "fresh decoding realisations": at `temperature 0.0` there are none.)
- **Stop conditions.** If the receiver cannot solve tasks with full evidence, fix
  task/receiver qualification before studying communication. If outcomes differ
  only in constructed pair cases, the scope claim is limited to those. **If
  third-order effects dominate, or the cheapest strong baseline already exhausts
  the headroom, stop this representation** rather than expanding the build.
- **Inconclusive is a permitted result** and is reported as underpowered, not
  re-described as support.

## What Phase B cannot establish

Not a learned controller, not novelty, not an advantage over any published
method, not a prevalence claim about natural agent traffic (subset prevalence is
constructed), and not an end-to-end AgentCom result. Delivered-subset
interventions change content *and* length together; a semantic-interaction claim
additionally requires length- and position-controlled replacements, run on
development contrasts first.

## Gate standing

The direction has **not** passed `docs/NOVELTY-GATE.md`. The specification's own
residual — *whether recipient-conditioned interaction structure buys labelling
efficiency and held-out decision quality over equally-informed coalition
selection* — is unestablished, and Phase B does not test it. E27 remains a
replication; E28, C2 and the graph-shape direction remain closed; the ledger
stays 22 gated, 22 closed.

---

## AMENDMENT 1 — fixtures built, thresholds made exact (2026-09-08)

**Recorded BEFORE any outcome exists. Still zero model calls.** Fixtures,
manifest and schedule are built and validated (`phaseb_fixtures.py`,
`results/phaseb_manifest.json`, `results/phaseb_schedule.jsonl`, 192/192 fixture
checks). The original protocol named stop conditions but **no numeric
thresholds**; that gap is closed here rather than after seeing data.

### Fixtures as actually built

- **8 study tasks**, salt `phaseb-v1`, distinct (domain, graph) pairs. Each has
  4 candidate messages (A–D) and **2 recipient context variants**: `knows_A`
  pre-knows candidate A's constraint, `knows_B` pre-knows B's. All 16 subsets
  enumerated per variant.
- **The 2 variants are NESTED observations on one task.** The unit of
  independence is the **task**: **8 units, not 16.** Both variants share one
  scoring key (the full authored constraint set), so they are the same task seen
  under two recipient states.
- **8 qualification fixtures**, separate salt `phaseb-qual-v1`, disjoint
  (domain, graph) pairs, full evidence only.
- **Scoring** `lineage_eval.check_plan` against authored constraints — executable,
  and blind to variant and subset by construction. Every task has a **verified
  reference solution** that scores `success`; reversed order, dropped actions,
  `ready=false` and unparseable text are all verified to be rejected.
- **Budget unit is RENDERED WORDS**, header and separators included. Model
  prompt/completion tokens are a *different* quantity, recorded only once calls
  occur. All execution fields stay `None` until then, enforced by
  `SubsetOutcome.__post_init__`.

### Call accounting (unchanged ceiling, now exact)

| item | calls | blocks |
|---|---|---|
| qualification: 8 fixtures × 2 realisations | 16 | 16 (one per realisation) |
| subsets: 8 tasks × 2 variants × 16 subsets | 256 | 16 (one per decision point) |
| logged reserve | 16 | — |
| **total** | **288** | 32 scheduled |

Planned 272 + 16 reserve = 288 exactly. **Retries and failures consume the
ceiling. There are no unlogged calls.**

### Thresholds, fixed in advance

1. **Qualification (Q).** PASS if **≥ 6 of 8** fixtures succeed on **both**
   realisations. If < 6/8, the receiver is the bottleneck: **do not interpret any
   subset outcome as a communication effect**; fix task/receiver qualification
   first.
2. **Realisation stability (S).** From the same 16 qualification calls, count
   fixtures whose two realisations disagree. If **≥ 3 of 8 disagree**, single-
   realisation subset outcomes are unstable, and the 256-call table **cannot
   support subset-level comparisons**; report that and stop.
3. **Headroom (H).** A decision point is **informative** if, across its 16
   subsets, at least one succeeds and at least one fails. PASS if **≥ 8 of 16**
   decision points are informative. If < 8/16, subsets do not differentiate on
   this family and the direction stops here.
4. **Degree-2 adequacy (D).** Per decision point, fit `anchored_expansion` to
   that point's own 16-outcome table, then at every budget level compare the
   degree-2 argmax subset against the exact table's argmax. **If the degree-2
   pick has strictly lower true score in > 1/3 of (decision point, budget)
   cells, the representation is inadequate on this family — stop this
   representation.** This is an **in-sample, single-realisation diagnostic**; it
   is not a generalisation result and cannot support any claim about unseen tasks.

All four are computed on development data. None of them establishes novelty, and
passing all four authorises nothing beyond writing up Phase B.

### Inconsistencies found while building, and their resolutions

- **`temperature 0.0` makes same-process repeats vacuous.** Greedy decoding
  returns bit-identical output, so two repeats in one process would measure
  nothing. **Resolved:** each qualification realisation is now its **own process
  block** (16 blocks, 1 call each). Per E28-D this instrument is
  bit-reproducible *within* a process and occasionally shifts *across* processes,
  so cross-process is the instability that matters for a table collected block by
  block.
- **"Fresh decoding realisations" was the wrong phrase** in the original read
  rules. At temperature 0 there are no fresh decoding realisations, only fresh
  **processes**. **Corrected**, with the limitation stated: threshold S measures
  *cross-process* instability only. **Estimating decoding-sampling variability
  would require a non-zero temperature and its own separate call allocation, and
  is not part of this ceiling.**
- **Budget does not gate Phase B.** All 16 subsets are enumerated exhaustively;
  `DecisionPoint.budget` is set to the full-bundle rendered cost so nothing is
  excluded. No selection happens in Phase B. A later reader must not mistake the
  enumerated table for a selector's output.
- **The type guard on `select_bundle` was over-claimed.** Rejecting a utility
  callable **restricts the interface; it does not prove outcome isolation** —
  nothing in the signature can tell whether supplied coefficients were fitted on
  evaluation outcomes. **Resolved:** `CoefficientProvenance` (source, training
  scope, `saw_evaluation_outcomes`) must accompany any coefficients and be
  audited; the wording and its test are corrected.

### Still unresolved (recorded, not silently carried)

- **One completion per subset estimates a realised outcome, not an expected
  effect.** Threshold S bounds cross-process instability but cannot convert a
  single realisation into an expectation. Any interaction term computed from this
  table is a realised finite difference.
- **Constructed prevalence.** Which subsets interact is a property of how these
  fixtures were authored. Phase B cannot support any claim about how often such
  structure occurs in natural agent traffic.
- **Delivered subsets change content and length together.** A semantic-interaction
  claim would additionally need length- and position-controlled replacements,
  which are **not** in this ceiling.
- **Scoring key visibility.** Constraints neither pre-known nor delivered can
  still be satisfied by chance; the by-chance rate is not separately estimated
  and bounds how sharply subset effects can be read.
