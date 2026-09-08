# Next-research screen — one bounded discovery pass

Run 2026-09-08 under `docs/NOVELTY-GATE.md` (repaired this pass, §0 below).
**No model experiments were run. No recovery backend was built.** Existing-code
inspection and cached-data inspection only.

**Ledger going in:** 22 candidates gated, 22 closed, zero established original
results. E27 (controlled replication) and E28 (closed on novelty) are preserved
as decided; nothing here reopens them.

**Outcome of pass 1: no candidate reached "candidate for testing." C2 was
UNRESOLVED and the recommended next action was bounded retrieval.**

**Outcome of pass 2 (2026-09-08, zero model calls): C2 is retired because no distinctive selection mechanism or substantive original contribution has been established. The downstream behavioural interaction remains untested. No model
experiment is recommended. See §§4–8.**

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

## 3. PASS 2 — C2 coverage update (primary sections read)

| source | sections read | what it covers | what it leaves untested |
|---|---|---|---|
| [DelibTrace, arXiv:2606.03032](https://arxiv.org/html/2606.03032v1) | §3.3, §5.5, App. B.4, D.2, D.10 | §3.3 agents receive partial evidence + a prior stance across three topologies, exchanging synchronously, with **no retraction tracking**. §5.5 "Attrition Enables Malicious Injection": **58.9 % of final system outputs carry injected misinformation even when truthful agents collectively hold corrective evidence.** D.2 no-interaction upper bound; D.10 malicious-agent setup. Retention taxonomy: retained facts more abstract than lost (2.73 vs 2.33). | **No retracted/superseded content restated later. No context-selection or compression policy. No budget.** Persistence of a falsehood under consensus is not a retraction being out-selected under a budget. |
| [MemStrata, arXiv:2606.26511](https://arxiv.org/html/2606.26511v1) | §4 | Bi-temporal ledger: "Facts are retired, not deleted", recording `valid_from`, `valid_to`, `superseded_by`. Supersession is **structural, not similarity-based** — triggered by a matching (subject, relation) key with a differing object. Obsolete facts are removed from **active retrieval** before read-time ranking. | **Does not evaluate budget-constrained selection**, and **does not address whether restating an obsolete item refreshes its rank**. It operates on extracted triples, not raw messages; our selector ranks raw messages and we have no extractor. Per the gate's precondition rule, a described temporal-memory mechanism is **not** evidence that our stale-restatement case is handled. Whether a restatement carrying the original object would supersede the *retraction* under its write path is **untested, and not claimed here**. |
| [Zep provenance](https://blog.getzep.com/how-zep-tracks-provenance-in-agent-memory/) | whole post | Every derived artifact is associated with its source episodes at construction time; facts are bi-temporal (`valid_at` / `invalid_at`); "Zep records which episode did the invalidating and when"; invalidated facts are retained with full history. | **No token-budget context selection.** **No guidance on restatement of superseded facts** — the mechanism is described in the invalidation direction only. |

Coverage is better resolved than in pass 1, and **none of the three states C2's
claim**. That turned out not to matter: C2 died on its own mechanism instead.

## 4. PASS 2 — deterministic trace of the real selector (zero model calls)

Reproducible: `python c2_selector_trace.py`. Authored history —
`[system, PROPOSAL, fill, RETRACTION, fill, fill, <variant>, current]` — where the
variant slot holds one of:

- **ECHO** — restates the obsolete proposal and explicitly does *not* authorise a
  new decision ("noting it only as history, not as a new decision"), 22 words;
- **NEUTRAL** — unrelated content **padded to the same 22 words**, same position;
- **ABSENT** — no message at that position.

ECHO vs NEUTRAL isolates semantics with position and length held fixed. NEUTRAL vs
ABSENT isolates ordinary displacement from adding any text. Policies exercised:
`RecencyBudget` and `BM25Budget` (pure numpy, no inference).

### Finding 1 — the original message is not re-dated; the restated content still occupies a newer position

`RecencyBudget.priority` is `range(len(rest)-1, -1, -1)` — **positional over
messages**. A restatement creates a *new* message: the original proposal and its
retraction keep their positions and are not re-ranked, so there is no re-dating
**of the original message**.

Stated precisely, because the pass-1 claim was looser than this: the *content* of
the obsolete proposal does newly appear at a later position, and can therefore be
retained when the original message is not. What is refuted is re-dating of the
original message, not the existence of newer stale content.

### Finding 2 — under recency, ECHO and NEUTRAL select the same *positions* — not the same *inputs*

Identical `selected_ids` at **every** budget tested (W = 20/30/40/50/60). At W=40
both give `ids=[3,4,5]`, `words_history=38`. In the tested cases the selector
gives the stale restatement **no priority advantage** over length-matched neutral
text.

**Identical indices are not identical inputs.** In the ECHO arm the retained slot
carries stale content; in the NEUTRAL arm it does not. The two arms therefore
deliver *different* model inputs while selecting the same positions, so this
finding constrains the **selection** claim only and says nothing about downstream
behaviour.

### Finding 3 — in the tested cases the retraction is dropped by ordinary displacement

NEUTRAL vs ABSENT under recency:

| W | NEUTRAL | ABSENT |
|---|---|---|
| 40 | retraction **dropped** | retraction kept (`ids=[2,3,4]`) |
| 50 | retraction **dropped** | retraction kept |
| 60 | retraction kept, proposal dropped | both kept (`ids=[0,1,2,3,4]`) |

Adding **any** 22-word message at that position pushes the retraction out of a
budget that would otherwise have held it. Displacement, not supersession.

### Finding 4 — source attribution has no effect

With content and position fixed, `role="assistant"` versus `role="user"` gives
identical `selected_ids` under both policies. The deployed selector receives only
`{role, content}`, and only `_split_system` consults `role`, so **attribution
cannot influence selection**. Any provenance-aware variant would be an **oracle
control**, using metadata the deployed selector does not receive.

### Finding 5 — an echo-independent BM25 asymmetry (observation, not a candidate)

At W=20, `BM25Budget` retains the **proposal** and drops the **retraction**
(`prop=Y retr=.`) — and does so **identically in the ABSENT condition**. Both
match the query term "plan"; the proposal is 11 words against the retraction's 16,
and greedy fill prefers the cheaper one. So a relevance-scored budget can keep a
proposal while dropping its own retraction **with no restatement present at all**.

**Not promoted, and scoped to this fixture.** The observation holds for **this
authored history at these budgets** and nowhere else: n=1, dependent on the
retraction being longer than the proposal and on both matching the query term
"plan". No claim is made that relevance-scored budgets generally rank retractions
below proposals. It is also a variant of **C1, which is COVERED**. Recorded so it
is not re-derived; it would need its own gate pass.

Also noted: at W=50 BM25 selects the variant slot in both conditions but for
*different reasons* — ECHO on relevance ("plan"), NEUTRAL on the documented
recency tie-break among score-0 messages. The identical `ids` there are
coincidental, not evidence of equal treatment.

### Infrastructure dependency, reported rather than assumed

`DenseBudget` / `FusionBudget` require `all-MiniLM-L6-v2` embedding inference
(`retrieval.py:127`). **Not run this pass, and this gap is not a reason to
continue.** Whether a dense scorer treats an echo differently from a length-matched
neutral is simply **untested**; an untested arm is not a pending lead, and C2 is
retired on the absence of an established contribution rather than on the tested
arms alone.

## 5. PASS 2 — the three claims, separated

| claim | status after this pass |
|---|---|
| **(a) deterministic selection failure** — the selector keeps the superseded proposal and drops its retraction *because of* the restatement | **No distinctive selection mechanism established in the tested cases.** ECHO and NEUTRAL select the same positions; the retraction is dropped by displacement, which any equal-length filler reproduces. Untested for dense/fusion. |
| **(b) additional model error conditional on an authored stale restatement** | **Untested.** Selecting the same positions does not equalise the inputs — the ECHO arm carries stale content into the model and the NEUTRAL arm does not — so an **echo × compression interaction remains open as an empirical question**. It sits close to E18 revocation inertia and STALE's Implicit Conflict, and would need its own gate pass rather than a resumption of C2. |
| **(c) how often agents spontaneously produce such a restatement** | **Untested and unaddressable by the proposed design.** The finalisation-only experiment authors the restatement, so it cannot estimate a spontaneous rate. That needs free-running dialogue on new instances. |

Claim (a) was the load-bearing one — it is what would have made C2
multi-agent-specific and distinct from single-agent compression work. It is not
established.

## 6. PASS 2 — the estimand, repaired (recorded, not authorised)

Pass 1 said "difference-in-differences" without writing it down. For an error
rate Y, the within-instance interaction is:

> (Y_budget,echo − Y_full,echo) − (Y_budget,control − Y_full,control)

**What it identifies.** The error attributable to the *interaction* of budgeted
selection with the echo, differencing out (i) the model's baseline sensitivity to
echo text, measured on the same instance under full history, and (ii) the harm of
budgeting alone, measured with the length-matched control. Both differences
require matched controls and same-instance full-history outcomes.

**What it leaves unresolved.** It does **not** identify the mechanism. Findings 2
and 3 show the same positions are selected in the tested cases, so a nonzero
interaction would be evidence about the *content* delivered rather than about
priority ordering — it would not, by itself, distinguish those. It does not
estimate the
spontaneous restatement rate, does not establish external validity beyond the
authored instances, and cannot attribute a null to E18.

**E18's standing, corrected.** E18 *motivates* the full-history control; it does
**not** establish a baseline failure rate on new instances. The full-history arm
must be measured, never assumed.

**Outcome definitions, fixed in advance.** *Meaningful:* the interaction CI
excludes zero and its lower bound exceeds a pre-declared practically-relevant
threshold. *Negligible:* the CI excludes that threshold — an informative negative.
*Inconclusive:* the CI spans both — report underpowered and stop. **A
nonsignificant result alone must never be reported as "E18 explains it."** The 24
instances and ~150 calls in §7 were **planning estimates, not established power**;
a declared power probe would come first, as in E22 and E28.

## 7. Pass-1 test sketch — SUPERSEDED by §§4–6, retained for provenance

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

## 8. Decision (pass 2, supersedes pass 1)

**C2 is retired because no distinctive selection mechanism or substantive original contribution has been established. The downstream behavioural interaction remains untested. No model experiment is
recommended. No generator was built and no finalisation experiment was run.**

**What the trace established, at its actual scope.** C2's load-bearing claim was
a *distinctive selection mechanism*: that a partner's restatement causes
recency-ordered selection to keep the obsolete proposal and drop its retraction.
In the tested cases it does not. `RecencyBudget.priority` is positional, so the
original message is never re-dated; ECHO and a length-matched NEUTRAL select the
**same positions** at every budget tested; and the retraction is dropped by
**ordinary displacement**, which any equal-length message reproduces. Source
attribution cannot matter, because the deployed selector never receives it.

**What the trace did not establish.** Identical positions are not identical
inputs: the ECHO arm delivers stale content to the model and the NEUTRAL arm does
not, and restated content occupies a newer position even though the original
message is untouched. **The downstream echo × compression behavioural interaction
is untested.** C2 is retired for want of an established contribution — not on a
demonstration that no downstream effect exists.

This is still the outcome the pass was for: a zero-model-call check removed the
distinctive mechanism before a generator was built or ~150 calls were spent.

**If anyone revisits this, revisit it as a new candidate, not as C2.**

1. The remaining question is **behavioural**, not selectional: does stale content
   surviving compression raise error relative to length-matched neutral content?
   That is adjacent to E18 and to STALE's Implicit Conflict and needs its own gate
   pass.
2. `DenseBudget` / `FusionBudget` are **untested** (they need
   `all-MiniLM-L6-v2` inference). Recorded as a gap, **not** as a reason to
   continue.
3. Claim (c), the spontaneous restatement rate, remains unaddressable by any
   finalisation-only design.

**Prior-art standing, unchanged by the retirement.** DelibTrace, MemStrata and Zep
were read at the specified sections and **none states C2's claim**; C2 did not die
of prior art. Recorded so this file is not later misread as "covered". MemStrata's
bi-temporal supersession is a *candidate solution class* over extracted triples,
and is **not** evidence that our raw-message restatement case is handled.

**Standing observation, deliberately not promoted.** BM25 at W=20 on this fixture
kept the proposal and dropped its retraction **with no restatement present** — a
length-and-greedy-fill artifact, n=1, scoped to this authored history and these
budgets, and a variant of C1 which is COVERED.

**Ledger unchanged: 22 gated, 22 closed, zero established original results.** E27
remains a controlled replication; E28 remains closed. Nothing here reopens either.
