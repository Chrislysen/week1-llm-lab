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
4. **Degree-2 adequacy (D).** Per decision point, fit the **global
   least-squares** degree-2 projection (Amendment 2 changes this from the
   anchored fit) to that point's own 16-outcome table, then at every budget level
   compare the degree-2 argmax subset against the exact table's argmax. **If the degree-2
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

---

## AMENDMENT 2 — estimator diagnostics and recording, from the research addendum (2026-09-08)

**Recorded BEFORE any outcome exists. Still zero model calls.** No Phase B call
has been made, so nothing here is post-hoc and the original read rules stand
unchanged. Had outcomes existed, these would have been marked post-hoc and
carried to fresh confirmation instead.

### A correction to how the triple-failure result is read

The declared limitation — degree-2 selection missing a third-order requirement —
is a failure **of the anchored estimator**, not of the degree-2 class.

On the *same* authored table `V(S) = 0.8·1{A,B,C ⊆ S} + 0.2·1{D ∈ S}` at budget 3
(verified exactly, `test_agentcom_analysis.py`):

| estimator | selected | true value | decision regret | max reconstruction error |
|---|---|---|---|---|
| anchored degree-2 (11 of 16 cells) | **D** | 0.2 | **0.6** | **0.8** |
| global least-squares degree-2 (all 16 cells) | **A+B+C** | 0.8 | **0** | 0.1 |

The residual is uniformly 1/10, so **exact quadratic reconstruction is
impossible here while the correct budgeted decision remains available.**

- The existing test **keeps its assertions unchanged** and is renamed
  `test_ANCHORED_degree_two_misses_a_third_order_requirement`, documenting its
  scope.
- A **separate** global-fit diagnostic is added (`agentcom_analysis.py`), with
  the normal equations verified exactly in the monomial basis so a basis
  conversion error cannot pass silently.
- **Reconstruction error and decision regret are reported separately.** A large
  anchored residual is **not** on its own grounds to trigger stop rule **D**.

**Stop rule D is amended accordingly, before outcomes:** D is evaluated on the
**global least-squares** fit, not the anchored one, and reports regret and
reconstruction error separately. The anchored figure is retained as a secondary
diagnostic. Everything D produces is **in-sample and exploratory**.

### Cautions that bound what any Phase B table can mean

- **Any single already-known feasible target is additively encodable** (+1 to
  members, −1 to non-members) — so interaction evidence must be about
  learnability and generalisation, never about expressibility at a fixed cell.
  A direct budget-conditioned set selector is therefore a required comparator.
- **Observed adaptation gain is optimistic.** Exact null: identical contexts, six
  equally good actions, one Bernoulli(½) observation each → expected *apparent*
  gain **301/4096 ≈ 7.35 %** with **zero** true gain. One-decode maxima and
  in-table policy fits cannot establish held-out value; more tasks do not remove
  this bias.
- **Interaction claims are scale-dependent.** Probability-scale synergy of 0.2
  becomes exactly zero on the log scale, with identical choices under a hard
  budget. Positive success-scale interaction refutes no comparator that uses a
  monotone link over a submodular latent score.
- **Changing interaction coefficients ≠ valuable recipient adaptation.** Context
  headroom is zero when contexts share an optimal bundle. Feasible sets must be
  matched across contexts before a difference is attributed to recipient state.
- **Conditional noise arithmetic** (independent equal-variance cell noise, correct
  quadratic mean — *neither established for a receiver*): the anchored prediction
  has variance 7σ² at k=3 and 31σ² at k=4; the global fitted mean has 11σ²/16 per
  cell at n=4. The anchored form reads 11 of 16 cells, the global fit all 16, and
  Phase B collects all 16 regardless. This is a reason to **compare procedures**,
  not a measured improvement.

### Recording requirements (additive extension within `agentcom-bundle/1`)

`SubsetOutcome` gains **optional** fields, all defaulting to `None`, so existing
records stay readable and no consumer breaks: `task_family_id`,
`recipient_context_id`, `process_block`, `request_position` (execution order),
`inclusion_order` (canonical serialisation order, recorded **separately** from
execution order), `rendered_input` (the literal delivered prompt), `attempt`
(retries consume the ceiling), `failure`.

**Preserve all 16 subset outcomes per recipient context** together with literal
prompts, candidate/source/version identifiers, rendered word budget,
model/decoding settings, collection block, request position, output, executable
score, failure/retry record, and measured input/output tokens when available.
**Unavailable fields stay explicitly unavailable** — never imputed.

Serialisation is deterministic and canonical (`render_bundle` orders by candidate
id). Randomised collection order controls **request-position** effects; it does
**not** establish invariance to **message order**. Message-order robustness is a
later test, and permutations are **not** independent tasks.

No gold correctness labels or hidden tests may enter selector or receiver prompts.

### Baseline specification updated

`docs/AGENTCOM-BUNDLE-BASELINES.md` adds **Optimal Skill Selection**
(arXiv:2608.19993), **CASE** (ICML 2025) and **OptiSet**, plus GenICL/SetR,
targeted active learning, transductive linear bandits and SPO/decision-focused
learning — alongside the carried-forward RepoShapley, ProxySPEX and semantic
QUBO. **Neither quadratic selection nor active subset exploration is itself new.**
The research target is transferable recipient-conditioned selection at lower
labelling cost, and it is unestablished.

### Unchanged by this amendment

The 288-call ceiling, the fixtures, the schedule, Amendment 1's thresholds Q, S
and H, and the qualification gate on separate fixtures. Phase B still establishes
observability only, authorises no Phase C, and the ledger stays 22 gated,
22 closed.

---

## AMENDMENT 3 — check-level supervision as training signal (2026-09-08)

**Recorded BEFORE any outcome exists. Still zero model calls.** No Phase B call
has been made, so this is not post-hoc and the original read rules and
thresholds Q, S, H, D stand unchanged. **Phase B itself is unchanged**: same
fixtures, same schedule, same 288-call ceiling, same primary outcome.

### What was checked, not assumed

The proposal asked whether the existing scorer exposes check-level distinctions
or whether they must be recovered from saved outputs. **It already exposes
them.** `lineage_eval.PlanCheck.satisfied` / `.violated` are per-constraint, so
the check vector is read directly and no text recovery is needed. Four states
that a bare "failure" label collapses are separable today:

| state | meaning |
|---|---|
| `success` | every check passes and the plan is offered as ready |
| `violation` | a scoreable plan breaking at least one check |
| `refusal` | every check passes but `ready` is false |
| `unparsed` | no scoreable action; **check vector is absent, not all-false** |

The violation/refusal split is not hypothetical: B1 measured **16 of 18 invalid
plans emitted silently as `ready=true`, and only 2 self-flagged.**

### Recording change (additive, `agentcom-bundle/1`)

`SubsetOutcome` gains two **optional, training-only** fields: `check_vector` and
`failure_mode`. Both default to `None`. `check_vector` is `None` — not a row of
zeros — when the output did not parse, because "no scoreable action" and "every
check failed" are different states.

**Deployment boundary.** The selector chooses on **predicted overall task
success under the rendered budget**. Check outcomes are training information
only. The boundary is named in `agentcom_analysis.TRAINING_ONLY_FIELDS` and
enforced by a test asserting the selection path's source reads none of them —
auditable rather than asserted.

### Why the selection objective does not change

Two authored two-check distributions with **identical marginals and identical
expected checks-passed** (3/2 each) have all-pass rates of **3/4 and 1/2**.
So neither multiplying per-check marginals nor rewarding more passed checks
recovers the objective. **The direct task-success objective is retained**, and
check prediction is strictly auxiliary.

### Two table analyses specified now, to run when outputs exist

Prompted by Context-Picker, which mines one sufficient set by repeated removal
and **discards examples where the initial candidate set fails**. Both are
**questions**, not expected outcomes:

1. `working_bundle_multiplicity` — if several *minimal* bundles succeed, "the"
   sufficient set is not well defined and coverage-of-one-set is lossy.
2. `smaller_succeeds_when_full_pool_fails` — if a proper subset succeeds where
   the full pool fails, discarding full-pool failures is not neutral, and more
   evidence is not monotonically better.

These reuse the Phase B executions and **require no additional calls**. They are
descriptive, in-table, and **cannot demonstrate transfer or authorise Phase C**.

### Standing

The auxiliary objective alone establishes **no novelty** — CodeRL+ already
learns from failed-execution information and ContextRL already combines a task
objective with answer-conditioned context discrimination. What would be
substantive is a **measured reduction in execution cost to learn reliable
selection on unseen task families**, which is a Phase C question with its own
fresh data, estimand and margin. Ledger stays 22 gated, 22 closed.
