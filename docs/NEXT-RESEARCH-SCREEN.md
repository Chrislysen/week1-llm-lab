# Next-research screen — one bounded discovery pass

Run 2026-09-08 under `docs/NOVELTY-GATE.md` (repaired this pass, §0 below).
**No model experiments were run. No recovery backend was built.** Existing-code
inspection and cached-data inspection only.

**Ledger going in:** 22 candidates gated, 22 closed, zero established original
results. E27 (controlled replication) and E28 (closed on novelty) are preserved
as decided; nothing here reopens them.

**Outcome of this pass: no candidate reached "candidate for testing." One
candidate (C2) is UNRESOLVED and is the only one worth further work. The
recommended next action is a bounded retrieval step, not an experiment.**

---

## 0. Gate repair (done first)

The gate's precondition rule was stated only inside the "compare prior work"
step, which reads as advice for *closing*. It now applies **symmetrically to
opening and closing**, with the three-part check required for any imported
result, confound, bound, theorem or effect size: identify its assumptions,
verify each against our code or data rather than by analogy, and state the
conclusion actually supported once non-holding assumptions are struck out.

Both failure directions are recorded there as worked examples: E27's first
closure argument imported a per-method magnitude confound into a design that
normalises to unit norm at identical α (`e27_estimator.py:135`, `:141`), and the
unlearning bound of arXiv:2609.04875 was earlier cited as bounding achievable
contribution when it bounds worst-case *exact reconstruction* over transitions.
Closing on an inapplicable confound is the same error as opening on an
inapplicable guarantee, and is easier to miss because it feels modest.

## 1. What this project can actually measure

| capability | status |
|---|---|
| two-agent dialogue, per-agent views, budget stops | `engine.py` — exists |
| per-turn realised cost (`prompt_tokens`, `completion_tokens`, `seconds`) | `engine.Entry` — exists |
| in-loop context selection, word-budgeted | `context.py` — recency / random / oracle / BM25 / dense / fusion, with `_last` telemetry |
| verifiable structured finalisation | `finalise.py:55`, `lineage_bench.plan_instruction:676` — exists, no LLM judge needed |
| supersession / statuses (accepted, rejected, proposed, never) | `lineage_e16` — exists, but the corpus is **scripted** |
| provenance over model calls, selective recovery | **absent** (confirmed again this pass) |

**Data already used for development:** the E16 corpus (144 dialogues, hash
`70f136a47f5779c8`) has informed nine studies and is development material. The 70
generated transcripts under `transcripts/` come from `scenario.py`, whose
constraints are *stated*, never *retracted* — so they carry no supersession
structure. **Any supersession claim needs newly generated instances.**

## 2. Candidates investigated

### C1 — Supersession-blind compression: the selector keeps the proposal, drops its retraction

*Field terms:* stale memory, knowledge conflict, outdated context, memory
invalidation, context eviction.

| closest prior work | what it establishes |
|---|---|
| [STALE (arXiv:2605.06527)](https://arxiv.org/abs/2605.06527) | benchmark for whether agents know their memories are invalid; names **Implicit Conflict**; reports a **pervasive gap between retrieving updated evidence and acting on it**, best model 55.2% |
| [Plans Don't Persist (arXiv:2606.22953)](https://arxiv.org/abs/2606.22953), Mehta & Datta, §§1, 4, 8 | plan info is **context-time not weight-time**, decays 4–12× within one step; **naive eviction of critical content cuts ALFWorld success 34.7pp and probe-gated re-surfacing does not recover it** |

STALE's retrieve-vs-act gap is the same shape as this repo's E23 finding, already
published. Plans Don't Persist already establishes that evicting critical content
is harmful and not repairable by re-surfacing. The residual — that *scoring
functions rank a proposal above its own retraction* — is a special case of
"important content gets evicted," with no additional consequence identified.

**Status: COVERED.** No substantive residual specified.

### C2 — Restatement re-dates superseded content, defeating recency-ordered selection

*The claim:* in multi-agent dialogue, a partner's spontaneous restatement of an
already-retracted proposal becomes the **most recent mention** of it, so
recency-ordered (and recency-correlated) context selection retains the
superseded proposal while its retraction falls outside the budget. Single-agent
compression work cannot exhibit this: there is no partner to re-date the content.

*Field terms:* conversational grounding, common ground, factual attrition,
recapitulation, multi-turn degradation, coordination failure.

| closest prior work | what it establishes | why it is not the same claim |
|---|---|---|
| [Deliberative Illusion (arXiv:2606.03032)](https://arxiv.org/abs/2606.03032) | in multi-agent deliberation facts attrit; retained facts are **more abstract** than lost ones; common ground becomes "individually factual but collectively misleading" | attrition and abstraction of *surviving* content — not re-dating of *superseded* content |
| [MAST / Why Do Multi-Agent LLM Systems Fail? (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657) | failure taxonomy incl. conversation reset, coordination over already-shared information | taxonomy of observed failures; no context-selection mechanism |
| [LLMs Get Lost in Multi-Turn Conversation (arXiv:2505.06120)](https://arxiv.org/abs/2505.06120) | multi-turn degradation; uses **turn-level recapitulation** as a *mitigation* | restatement as a fix, not as a mechanism that defeats supersession |

**Status: UNRESOLVED — and honestly so.** Four searches; the closest paper
(2606.03032) was **not** read in primary text, only via search summary. Under the
gate, that is incomplete coverage, and **no novelty verdict may be issued.**

**The strongest internal objection is this repo's own E18.** E18 established
*revocation inertia*: models keep acting on retracted proposals **with full
context**. If the baseline failure rate is already high, a compression-induced
increment may be small and hard to separate. Any test must therefore estimate a
**difference-in-differences against a full-history arm**, not a raw stale-action
rate — and the effect must clear an already-large baseline.

### C3 — Query self-match in agentic retrieval

*The claim:* where the retrieval query is derived from recent context, the
current message is itself a candidate and matches itself, inflating measured
retrieval quality. This repo measured it offline: BM25 scored the current message
**+45.38 against a next-best +12.71** (`context.py:187–190`), and fixed it with
the current-message separation amendment.

*Field terms:* query–document leakage, near-duplicate contamination,
self-retrieval, agentic RAG evaluation.

Four searches surfaced no direct treatment. **Status: UNRESOLVED, low value.**
The residual is a methodological pitfall this repo has already fixed; to matter
it would have to be demonstrated *in published systems*, which needs
infrastructure this pass cannot justify. Recorded so it is not re-derived.

## 3. Cheapest informative test — designed for C2, NOT authorised to run

Conditional on C2's coverage being resolved first.

- **Hypothesis.** Partner restatement of a retracted proposal increases the rate
  at which the finalised plan contains that retracted action, *over and above*
  full-context revocation inertia, and does so more under budgeted context
  selection than under full history.
- **Design.** 2×2 within-instance: {restatement absent, restatement present} ×
  {full history, `RecencyBudget`}. Restatement is **scripted** into the dialogue,
  which buys exact control of its position relative to the retraction.
- **Why it is cheap.** Following E16's pattern, the dialogue is authored and only
  **finalisation** is a model call. Cost is one call per (instance × arm).
- **Primary outcome.** Retracted-action inclusion rate in the finalised plan —
  verifiable by `finalise.py` + `lineage_bench.plan_instruction`, no LLM judge.
- **Estimand.** The **interaction** (difference-in-differences), never the raw
  rate. E18's inertia is the baseline, not the effect.
- **Strongest baseline / what would retire the claim.** Full-history arm. If the
  restatement × budget interaction is null while full-context inertia is high,
  the phenomenon is E18 revocation inertia and **not** a context-management
  effect — the contribution is retired.
- **Inconclusive outcome.** If the interaction CI spans both zero and a
  practically relevant effect, report **underpowered** and stop; do not
  re-describe it as a positive. Declare the power check before the run, as E22
  and E28 did.
- **Separation of claims.** Cost (tokens), task quality (plan validity), and
  novelty are three separate judgements and must be reported separately.
- **Untouched data.** Requires **newly generated instances**; E16's 144 dialogues
  are development material and cannot serve as a confirmatory set.
- **Build dependencies.** A retraction+restatement dialogue generator. Engine,
  context policies and finaliser already exist. **No recovery backend.**
- **Derived budget.** 24 new instances × 4 arms × 1 finalisation call = **96
  calls**, plus a declared power probe (~48) ≈ **150 model calls**. A spontaneous-
  restatement *descriptive* arm, if wanted, needs free-running dialogue: 12
  instances × 8 turns ≈ 96 further calls.

## 4. Decision

**No candidate reached "candidate for testing." No experiment is recommended
this pass.**

The single recommended next action is **bounded retrieval to resolve C2**: read
arXiv:2606.03032 in primary text, plus two targeted searches on
grounding/repetition re-dating superseded content. Estimated 30–60 minutes, zero
model calls.

**Why this has the best information value for its cost.** C2's entire worth
depends on a coverage question that costs an hour to answer and nothing to run,
while the experiment costs ~150 model calls plus a generator build. Running
before resolving coverage is precisely the E27 failure — that direction was
carried as original through a full review cycle because a decisive paper was
marked "unverifiable" and never chased. The gate forbids a novelty verdict on
unresolved coverage, and this pass will not make an exception for its own
candidate.

**Unresolved retrieval limits, stated plainly.** Four to five searches per
candidate; one primary source read in full (2606.22953), one partially
(2502.02716, from the prior pass). C2's closest competitor was **not** read in
primary text. C1's verdict rests on search summaries of STALE plus the primary
text of Plans Don't Persist. **None of these is proof of absence**; C2 and C3 are
recorded as unresolved coverage, not as open novelty.

**Nothing here is a discovery.** C2 is an unresolved candidate with a specified
internal threat, not a finding.
