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

- **Best-of-subsets from a single decoding realisation is an optimistic observed
  envelope, not an oracle performance estimate.** Any subset that looks best must
  be re-run on fresh decoding realisations before the gap is treated as real.
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
