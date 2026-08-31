# AgentCom — research and repository audit

Date: 2026-08-31. Evidence: direct reading of the local starter code, and a 12-agent
audit that shallow-cloned and read all nine prior repositories, including two
adversarial verifiers tasked with *refuting* the project's two load-bearing technical
claims, plus a prior-art scan of the five crazy-branch research questions.

Headline: **both load-bearing claims were wrong or overstated, and four of the five
crazy-branch research questions are already published.** Details in C, F, G.

---

## A. Current state

### There is no repository

| Check | Result |
|---|---|
| `.git` in project | **absent** |
| Commits / branches / remote | **none** |
| AgentCom or KIUA repo on GitHub | **does not exist** (searched all 21 repos) |

Meisam's instruction — "push that to one branch of your GitHub repository, and then
create another branch called `crazy`" — currently has nothing to push, nothing to
branch from, and nothing to freeze. Everything in §H depends on infrastructure that
does not yet exist.

### `.gitignore` would discard the evidence

The supplied `.gitignore` contains `transcripts/*.json`. The compulsory requires
"saved transcripts backing every reported number." If `git init` runs as-is, every
scored transcript is untracked and `verify_claims.py` has nothing to re-derive from
on a fresh clone. Scored runs must be committed; only exploratory ones ignored.

### Files

| File | State |
|---|---|
| `budget.py` | Complete, supplied. Three caps + `stop("goal_reached")`. |
| `llm_client.py` | Complete, supplied. Exact Ollama token counts. **Cannot pass `seed`.** |
| `agents.py` | Complete, supplied. |
| `engine.py` | `Entry` + `save()` done. `view_for` and `run` **raise NotImplementedError**. |
| `run.py` | Complete, but constructs `DialogueEngine` **without** `manage_context` / `goal_reached`. |
| `test_engine.py` | **Fails** at `engine.py:46`. |
| `ping_pong.py` | **Untouched starter** — still `Pro`/`Con` on banning cars. |
| `exercise_a.py` | Works. Correct 3-call statelessness demo. Hardcodes `mock=False`, blocks on `input()`. |
| `exercise_b/c.py`, `milestone1.py` | Week 1 debate scenario. `c` and `milestone1` byte-identical. |
| `docs/design.md` | Week 1 doc, debate scenario, non-measurable success criterion. |
| `docs/plan.md` | Written before this audit. **Contains errors — see §C.5.** |
| `configs/debate.yaml` | 1 config. Compulsory needs 3+. |
| `transcripts/` | `.gitkeep` only. |
| `requirements.txt` | `requests`, `PyYAML`. No `numpy`, `rank_bm25`, `sentence-transformers`. |

Week 1 is substantially complete on the wrong scenario. **Weeks 2, 3 and 4 have not
been started.**

---

## B. Core gap analysis

| Requirement | Where it lives | Status |
|---|---|---|
| Two agents, distinct system prompts | `milestone1.py` | DONE (wrong scenario) |
| One neutral transcript | `engine.Entry` | BLOCKED on `run` |
| Correct role mapping via `view_for()` | `engine.view_for` | **NOT DONE** |
| Own orchestration loop | `DialogueEngine.run` | **NOT DONE** |
| Budget on every model loop | `budget.py` | DONE |
| max turns / tokens / wall-clock | `Budget` | DONE |
| Every message logged w/ tokens+time | `Entry`, `save()` | Ready, unreachable |
| Config not hardcoding | `configs/` | 1 of 3+ |
| `manage_context()` | hook exists | **NOT DONE** |
| Long-context handling | — | **NOT DONE** |
| `judge()` → score/success/reason | — | **NOT DONE** |
| Structured JSON + parse/retry | — | **NOT DONE** |
| 3+ configs, one variable | `configs/` | **NOT DONE** |
| Saved transcripts back every number | `transcripts/` | **NOT DONE** + gitignored |
| Failure analysis | — | **NOT DONE** |
| Report + demo | — | **NOT DONE** |

---

## C. Prior repository findings

| Repo | Rel | Cx | Recommendation | The one thing worth taking |
|---|---|---|---|---|
| `fleet-command` | 4 | 2 | **USE_NOW** | Cost-parity verdict taxonomy (PAID-WIN) |
| `secret-loyalty-probe` | 4 | 2 | **USE_NOW** | `verify_claims.py` engine (~120 lines) |
| `jarvis-cortex` | 4 | 2 | **USE_NOW** | `fusion.py` (146 lines, standalone) + BM25 |
| `SLO-Guard` | 4 | 2 | **USE_NOW** | Interleaved resumable multi-seed harness |
| `trusttune` | 4 | 2 | **USE_NOW** | Rerun-the-winner majority gate |
| `opsem` | 3 | 2 | IDEA_ONLY (~60 lines of code) | BM25 + z-norm fusion |
| `solon` | 3 | 2 | IDEA_ONLY | The planted `negative_result` arm |
| `Argos` | 3 | 2 | **CRAZY_ONLY / effectively EXCLUDE** | A negative result (§F) |
| `heimdall-demo` | 3 | 2 | IDEA_ONLY | Precedence ladder (~10 lines) |

### C.1 The opsem episode adaptation is a misreading — verdict PARTIALLY_SUPPORTED

The first half is right. In opsem the retrieval unit is the **session**
(`locomo.iter_examples`, hit@1 over session ids); BM25 scores the whole concatenated
session (`ConvStats` + `score_classic`); the dense score is `max_t cos(q, turn_t)`
over per-turn vectors (`pool_max` in `tune13_interaction.py`); fusion is
`alpha*_z(bm) + (1-alpha)*_z(dense)` with alpha by leave-one-conversation-out CV.

**The 2-message-episode adaptation is wrong.** Evidence:

- opsem's released bucket data (`results/analysis-deep-.../analysis.json`) has
  **n=0 examples with a container under 8 turns**. Buckets are 8–15 (n=186),
  16–25 (n=1123), 26+ (n=669).
- The paper's own mechanism argument is that late-minus-early **grows monotonically
  with container length** — it is a *dilution* effect. e5-large-v2: +19.4 → +22.4 →
  +27.1 pp. Extrapolated to 2 turns, the gap is ~zero.
- Algebraically, for a 2-turn episode `max = mean + |s1-s2|/2`. The contrast is
  bounded by half the similarity spread of two adjacent messages.
- The proposal **inverts opsem's own control**. `tune13_interaction.py` header: *"The
  lever is the INTERACTION FUNCTION, not the unit."* The proposal changes the unit
  specifically to manufacture a slot for the interaction function.
- opsem does not do budgeted selection or chronological restoration at all. It ranks
  and stops. That layer is **new work**, not adaptation.
- opsem **credits late interaction to Nano-Memory (Wu et al., 2026)** and explicitly
  does not claim it. Its own contribution is that BM25 fusion adds *over* late
  interaction.

**Take:** drop late interaction; say why (the mechanism has a size precondition this
setting does not meet — that is itself a defensible finding). Keep ~60 lines:
`BM25` from `lme_maxsim.py` (~30), `_z` + weighted fusion from `tune13_interaction.py`
(~6), `cboot_hit` cluster bootstrap (~15). Retrieval unit = the individual message,
dense score = plain cosine.

**Alpha discipline:** opsem picks alpha by LOCO-CV and labels the full-data alpha an
overfit ceiling. With one scenario family there is no CV pool — either fix alpha a
priori (opsem's global optimum was **0.40**, curve broad over 0.30–0.45) or hold out
scenarios. Do not inherit `jarvis-cortex`'s `alpha=0.7` either; it was tuned on
LongMemEval-S for a different task.

### C.2 The most valuable single idea: a budget is a ceiling, not a spend

From `fleet-command`. The plan says "identical context-token budget across arms." A
budget is a **cap**; what matters is what each arm *actually put in the prompt*.
Instrument realized tokens per turn per agent, report the realized ratio next to every
delta, and adopt the verdict taxonomy: a win at higher realized spend is a
**PAID-WIN**, never a clean WIN.

### C.3 Three traps that would have invalidated the experiment

**Inert-experiment preflight** (`fleet-command`). If the whole transcript fits inside
the context budget, recency, BM25 and fusion select *identical* messages and the
experiment measures nothing. Assert `transcript_tokens > budget` before spending runs.

**The tautological verifier** (`secret-loyalty-probe`). If a planted constraint sits
in the last two turns, **recency wins by construction** — the score becomes an
arithmetic identity about position, not a fact about context selection. Stratify
planted constraints by distance-from-end and report per-stratum.

**The degenerate noise floor** (`fleet-command`). At `temperature=0` the naive
"re-run the identical config" floor reads 0.000 — structurally zero, and useless.
*This corrects `docs/plan.md`, which treated a deterministic rerun as a free win.*
Perturb something real instead (sampling temperature, scenario paraphrase) and
measure how much the score moves when nothing meaningful changes.

### C.4 Cheap high-value additions

- **Sabotage arm** (`solon`): a selector that deliberately drops constraint-bearing
  turns. The evaluator **must** score it near zero. If it doesn't, the evaluator is
  not measuring what the report claims.
- **Trivial baseline arms** (`fleet-command`): FULL-TRANSCRIPT and
  TRUNCATE-TO-BUDGET. If BM25 and fusion cannot beat plain recency by more than the
  measured floor, *that is the finding*.
- **Precedence ladder** (`heimdall-demo`, ~10 lines): an invalid run outranks an
  apparent task failure. Note the audit found heimdall has **no run-state enum** —
  the predicate is duplicated in two files. The lesson there is negative.
- **Rerun the winner** (`trusttune`): re-run the apparent winner N times under fresh
  sampling, require a majority to keep the win.
- **Variance as the finding** (`SLO-Guard`): with `llama3.2:3b` at n=5, the arms will
  probably **not** separate on means. Pre-commit to reporting mean±std with per-seed
  points so "the means tie, the spread differs" is a publishable outcome rather than
  a disappointment.
- **`verify_claims.py`** (`secret-loyalty-probe`): the audit *ran* the original from a
  fresh clone (239 verified, exit 0), then flipped one float and confirmed it goes red
  with exit 1. The engine is three functions plus a counter — ~120 lines here.

### C.5 Errors in `docs/plan.md` that this audit corrects

1. Fusion arm specified as "BM25 ⊕ turn-level max-sim" — **wrong**, use plain cosine (C.1).
2. Determinism check framed as a free noise floor — **wrong**, that floor is degenerate (C.3).
3. Missing: realized-token cost parity, inert-experiment preflight, constraint
   distance-from-end stratification, sabotage arm, trivial baseline arms.

---

## D. Research architecture

Smallest thing that carries the core, the first crazy experiment, and later work
without a rewrite. Roughly 500 new lines total.

```
engine.py          view_for + run                       (~40 lines, Week 2)
scenario.py        incident instances, planted          (~120)
                   constraints w/ hidden evaluator
                   representation + distance-from-end
context.py         manage_context selectors:            (~120)
                   full | recency | bm25 | fusion
                   | oracle | sabotage
                   -- all return (messages, realized_tokens)
evaluate.py        parse final JSON plan, check         (~100)
                   constraints, run-state ladder
judge.py           required LLM judge, secondary        (~50)
experiment.py      interleaved resumable runner,        (~80)
                   one JSONL row per (scenario, arm)
verify_claims.py   re-derive every reported number      (~120)
```

Two interface decisions that prevent later rewrites:

- `manage_context` must return **realized token count** alongside messages, or C.2 is
  unmeasurable retroactively.
- Selectors are **named strings in config**, so adding an arm never touches the engine.

Note `manage_context(messages)` runs **after** `view_for`, so it receives role-tagged
messages and cannot see speaker names. Capture the transcript in a closure if
speaker-aware selection is ever needed.

---

## E. Experimental plan

**Variable:** `context.method`. Everything else fixed — model, temperature, personas,
system prompts, incident, constraint positions, max turns, final-output instructions,
context-token budget.

**Arms:** `full` (ceiling) · `last-message` (floor) · `oracle` · `sabotage` ·
`recency` · `bm25` · `fusion` (only if approved). The first four are diagnostics,
not results.

**Replication unit:** distinct scenario instances, **not** RNG seeds — `llm_client.py`
cannot pass `seed`. Five instances, matched structure, different services and facts.

**Constraints per instance: 6–8, not 3.** A sign test discards ties; with 3
constraints the metric takes four values and ties are likely. Two ties out of five
leaves n=3, where even unanimity gives p=0.125.

**Metrics.** Primary deterministic: `constraint_recall`, `violations`, `parse_rate`.
Decomposition: `retrieval_recall` (was the constraint-bearing message in context?) vs
`execution_accuracy_given_retrieval` (was it obeyed once present?) — this separates a
retrieval failure from a reasoning failure and is the most informative thing the
harness can produce. Cost: realized prompt tokens per turn per agent.

**Run states:** `VALID` · `VALID_TASK_FAILURE` · `PARSE_FAILED` · `BUDGET_CONFOUNDED`
· `MODEL_ERROR` · `INERT` (transcript fit inside budget). Precedence ladder; never
average invalid runs.

**Budget confound.** `Budget.record()` counts prompt+completion, and the prompt
regrows every turn, so spend is ~quadratic. At the default `max_tokens: 4000` a
15-turn run dies on tokens. Worse, **the arm using less context per turn survives more
turns**. Set `max_tokens` so `max_turns` always binds; assert
`stop_reason == "max_turns"`; anything else is `BUDGET_CONFOUNDED` and is reported,
not dropped.

**Gate before any headline comparison** (pre-declare the band, then run at production
`max_turns`):

| Condition | Target |
|---|---|
| `full` ceiling | `constraint_recall` ≥ 0.80 |
| `last-message` floor | `constraint_recall` ≤ 0.50 |
| `oracle` | ≈ ceiling |
| `sabotage` | ≈ 0 |

Both high → scenario doesn't need memory. Both low → check `parse_rate` first; a low
ceiling with low parse rate is a formatting problem, not a memory problem. Oracle poor
→ retrieval is not the bottleneck. Sabotage not near zero → the evaluator is broken.

**Statistics.** Paired within scenario instance. Sign test or Wilcoxon on paired
differences; bootstrap CI over instances. Report `n`, mean delta, CI, and
WIN / PAID-WIN / LOSS / TIE / UNDERPOWERED. At affordable n this will often return
UNDERPOWERED, which is a defensible result.

---

## F. Argos — verdict REFUTED, high confidence

**Do not cite Argos for adaptive context allocation.** The verifier read the source
and found:

- `plan/allocate.py::allocate` is a **static, offline, exhaustive nested grid search**
  run once from a CLI before the model loads. Its own docstring: *"Search is exhaustive
  over a discrete grid… there is no reason to be clever."* No time axis, no state
  between decisions, no re-planning.
- "Budget" everywhere means **bytes of resident state** — a capacity constraint fixed
  for the whole run. There is no accumulator, no spent-vs-remaining ledger.
- No bandit, no marginal-value estimator, no controller, no stopping rule anywhere in
  `src/`. The README's "elastic re-planning / reasoning-budget governor" is listed
  under *Planned components* and greps to zero hits.
- **Directly adverse:** `allocate.py` documents `context_len` as *"a constraint, not a
  preference… in every quality model anyone has published it buys nothing."* Argos
  explicitly declines to optimise context, on the stated grounds that context utility
  has never been measured. That is the opposite of what the claim needs.
- **Decisive** (verified directly from `lab/alloc_e2e.json`): the one genuine
  equal-budget non-uniform allocator, `state/theory.py::allocate_bits_by_contribution`,
  **loses to a random control at the same budget**:

  | arm | top1 |
  |---|---|
  | random | **0.9674** |
  | amplification | 0.9609 |
  | none (all int8) | 0.9609 |
  | contribution | 0.9518 |

  `bootstrap_vs_random` for contribution is `[-0.0156, -0.0273, -0.0026]` — CI entirely
  below zero. Nothing beat random. This is the load-bearing evidence.

### Two corrections to an earlier draft of this section

**`lab/31_frontload.py` is NOT a fixed-budget reallocation experiment**, and an earlier
version of this audit wrongly described it as one. Its docstring asks *"Is the damage
the prefill pack, or the steady state?"* — it crosses pack-width × step-width to
attribute quantisation error, and states plainly: *"This buys no memory by itself…
the split exists to attribute the error, not to save bytes."* Total is not held fixed.
The `STEPS DOMINATE` verdict concerns where to spend engineering effort. Suggestive by
analogy only; do not cite it as a prior negative result for budget allocation.

**Argos does contain one working adaptive closed loop.** `lab/62_autoreseed2.py`
triggers an expensive state reseed when `max over layers of per-layer median scale
ratio > tau = 1.5`, checked every 16 steps, with outcome windows pre-registered in the
docstring. It worked on the second attempt after v1 (`lab/61`) missed. Caveats:
`grep reseed src/` returns nothing — lab-only, never shipped — and it is a
**maintenance trigger, not an allocator**: firing a reseed takes budget from nothing
and no total is conserved.

**The one honest Argos lineage available**, if a Rung-C-shaped idea is wanted later:
not fixed-budget reallocation, but the *autoreseed shape* — a cheap signal the runtime
already has, crossing a threshold, triggering expensive work, with the windows
registered before the run. ~15 lines in `manage_context`. It is "when to spend", not
"how to divide a fixed pot".

Second, independent strike: opsem's `tune8_adaptive.py` fits a query-adaptive fusion
weight and it **fails to beat one global constant** on 1978 examples. Two of your own
prior projects tested adaptivity against a fixed policy and adaptivity lost both times.

**Honest formulation:** "The adaptive-context-budget idea is independent. It is not
derived from Argos." The only defensible prior-work sentence is methodological:
*the equal-budget comparison design — hold total fixed, vary only which tokens,
include a random-selection control — follows `lab/17_alloc_e2e.py`, where the random
control beat the proposed heuristic.*

**What Argos actually gives this project: the random control arm.** Take that. Drop
Rung C.

---

## G. Frontier plan — the literature is against four of five

| RQ | Status | Killer prior work |
|---|---|---|
| 1. Relevance ≠ decision utility | **ALREADY_KNOWN** | Survey arXiv:2604.08920; UsefulBench arXiv:2604.15827; **arXiv:2603.02473** — counterfactual retrieval-vs-utilisation diagnosis in multi-turn *dialogue agent memory* |
| 2. Non-uniform budget across turns | **PARTIALLY_NOVEL** | SelfBudgeter arXiv:2505.11274; **MT-PingEval arXiv:2602.24188** ran the exact fixed-total-split-across-turns protocol and found performance **flat or decreasing** |
| 3. Complementary role-specific memory | **ALREADY_KNOWN** | **RCR-Router arXiv:2508.04903** — role-aware routing of non-redundant memory under a strict system-level token budget, ~30% token reduction at equal quality. Near line-for-line. |
| 4. Stale / superseded memory | **ALREADY_KNOWN** | MemStrata arXiv:2606.26511 (quantifies 15–40% stale-serve); STALE arXiv:2605.06527 (taxonomy separating it from retrieval miss); Memora arXiv:2604.20006 (FAMA metric) |
| 5. Structured state-delta comms | **ALREADY_KNOWN** | arXiv:2506.19209 — *the claim's wording is the paper's title* |

Ranked by remaining room: **2 > 1 > 3 > 5 > 4.** RQ4 should be deleted as a claim and
kept only as a validation check that the testbed reproduces a known effect. RQ3 needs
RCR-Router cited in the first paragraph. RQ2 must be read against MT-PingEval **before**
running anything — if their flat/decreasing result holds here, the claim is false, not
novel.

**What is actually unclaimed: the instrument.** A two-role natural-language
incident-recovery dialogue with planted constraints and a **deterministic, non-LLM-judge**
evaluator under a system-level context budget. Comparable work (τ²-bench, IntellAgent,
SOTOPIA-TOM) leans on LLM user-simulators and judges; AsymPuzl is deterministic but is
a puzzle, not dialogue. Deterministic grading of free-form two-agent dialogue is
genuinely uncommon.

That is a **resource contribution, not a discovery contribution** — and for this course
it is the honest and stronger framing: *build the instrument, replicate two or three
known effects to validate it, and report the one place the controlled setting disagrees
with the published result.* Do not lead with a novelty claim on any of the five.

---

## H. Branch plan

**Now (before anything else):** `git init`, commit the current state as the honest
starting point, create the GitHub repo, push `main`. Delete `week1-sandbox` once
branches exist — a branch is strictly better than a parallel directory. Fix
`.gitignore` so scored transcripts are tracked.

**Freeze `core` when** every row in §B reads DONE: `test_engine.py` green, 3+ configs,
`manage_context` implemented, `judge()` returning score/success/reason, structured JSON
behind parse/retry, transcripts committed, failure analysis written, report drafted.
Tag it `core-submitted`. That tag is the guaranteed submission and must never be
rewritten.

**Create `crazy` from that tag**, not from `main`. Never merge `crazy` → `core`.

---

## I. Stop list

- **Citing Argos as the ancestor of fixed-budget non-uniform context allocation.**
  Refuted (§F) — its only conserved-budget allocator lost to a random control.
  The idea itself is not disproven; the *lineage* is. The autoreseed trigger shape is
  the one defensible Argos descendant.
- **Turn-level max-sim / late interaction.** No container large enough (§C.1).
- **RQ4 stale-memory as a novelty claim.** Three 2026 papers cover it fully.
- **RQ5 comms compression.** The claim's wording is a paper title.
- Any orchestration from `fleet-command`; any of `solon`'s taint/fabrication machinery;
  importing `jarvis-cortex`'s memory system beyond `fusion.py` + BM25; a run-state enum
  copied from `heimdall` (there isn't one).
- Vector DB, RL, model training, dashboards, more agents, LangGraph/AutoGen/CrewAI.
- Tuning alpha on the same scenarios you score.

---

## J. Next action — one step

**Prerequisite (5 minutes, not the step):** `git init` + first commit + push, and
remove `transcripts/*.json` from `.gitignore`.

**The step: implement `view_for` and `DialogueEngine.run` in `engine.py`.**

Why this one and nothing else:

- GATE 0 says an incomplete core stops all research work. This is the core's blocker.
- Both TODOs are ~40 lines and `test_engine.py` already defines correctness exactly —
  mirror roles, system prompt first, ≥2 messages on an empty transcript, alternating
  speakers, sequential `turn_index`, non-zero token counts, `save()` round-trip.
- Every arm, every metric, every crazy rung calls through `run()`. Nothing downstream
  can be built or tested until it exists.
- It is immediately verifiable: `py test_engine.py` prints `All checks passed.` or it
  does not.

Do not write the scenario, the selectors, or the evaluator until that test is green.
