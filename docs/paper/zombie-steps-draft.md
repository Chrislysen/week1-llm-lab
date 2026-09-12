# Zombie steps: the memory design decides whether a rejected proposal comes back

*Working draft, 2026-09-12. Every number below is in a `results/*_summary.json`
file and re-derives from the committed result CSVs; the protocols in
`docs/protocols/` were declared with zero outcomes before each run. No run is
pending; every table is complete.*

## Abstract

Agents that talk to each other and act through a memory layer face a
supersession problem the memory literature has not measured: a step proposed
in dialogue, rejected by a partner, and later mentioned again by its proposer.
We construct 96 two-speaker incident dialogues with exactly one such rejected
step, in two arms that differ by one line — the proposer's later restatement
of the rejected step, or a length-matched neutral line — and deliver each to a
small local decider through four memory designs read from what is actually
shipped: the full transcript, write-time hard delete (the Mem0 paper
pipeline), add-only (Mem0 OSS v3), and merge-in-place wiki pages (the LLM-wiki
pattern). The decider writes a fixed-length executable plan; the outcome is
whether the rejected step is in it. On four deciders from three model
families (3B, 7B, 14B, and a ~4B-effective Gemma) the restatement's effect is
design-dependent: through hard delete it raises enactment of the rejected step
to near certainty (difference-in-differences against full context +0.44,
+0.38, +0.21, +0.50, intervals excluding zero); through add-only it does
nothing; merge-in-place sits between on the two small deciders and is flat on
the other two. The ordering survives a second corpus of six new
domains and new sentence wording on all three deciders (hard-delete DiD
+0.43, +0.58, +0.31), although absolute rates move by a factor of two with
the wording on the small deciders. A real Mem0 update router fed by an operational
extractor reproduces the mechanism on the same dialogues (+0.17 [+0.04,
+0.29], between the add-only and hard-delete ideals): it deletes on rejection
one time in five and otherwise keeps the proposal, and the restatement enters
as a fresh fact with no rejection attached. Under full context the same
restatement is protective on small deciders, and a follow-up shows this is the
"for the record, I did raise it" register rather than the mention itself. We
release the corpora, protocols, prompts, and every store snapshot.

## 1. Introduction

Multi-agent systems increasingly put a memory layer between the dialogue and
the decision. The three designs that ship do different things with a proposal
that was later rejected. The Mem0 paper's pipeline (arXiv:2504.19413) routes
every extracted fact through ADD / UPDATE / DELETE and, by its own DELETE
example, consumes a rejection by deleting the proposal and storing nothing.
Mem0's open-source v3 (April 2026) dropped that router for an add-only store
with no recency ranking, citing lost context. The LLM-wiki pattern
(nashsu/llm_wiki) merges new information into an existing page for the same
entity and queues contradictions for a human rather than resolving them.

None of these designs was measured on the case that matters for a planning
agent: a step that was proposed, rejected in the conversation, and then
brought up again by its proposer. We call a rejected step that re-enters the
plan a *zombie step*. The question is not whether small models forget
rejections — earlier work on this corpus measured that (revocation inertia,
E18) with the raw transcript in front of the decider — but whether the
*memory design* changes what a later restatement does.

Contributions. (1) A pre-registered experiment on 96 dialogues × 2 arms × 4
designs × 4 deciders (3,072 calls) showing design dependence with the
predicted sign and size for the hard-delete design. (2) Replication on a
second corpus with new domains and wording on the same three deciders (2,304
calls), which preserves the ordering across designs while moving absolute
rates by a factor of two on the small deciders. (3) A
real-system leg: Mem0's update router, verbatim, fed by an extractor that
stores operational facts, reproduces the mechanism on the same dialogues.
(4) Two negative or cautionary results reported as such: the Mem0 paper's own
extraction prompt does not store operational proposals at all, so a first
real-system attempt was uninformative by its declared rule; and under full
context the restatement lowers enactment on small deciders, which a follow-up
attributes to the authorship register of the line rather than the mention.

## 2. Related work

Eighteen papers were read in full text under a written novelty gate before
the first model call (`docs/protocols/E29-memory-semantics.md` §0). The
components of the construct are each occupied; the conjunction was found
nowhere.

*Forgetting Without Restarting* (arXiv:2609.04875) measures ten forget
mechanisms after an operator-issued revocation and finds that deleting the
memory record while the transcript persists does not stop action on the
revoked preference (B1 = B0 = 1.00, Table 3); its re-mention is a same-agent
introspection probe, not a partner's restatement, and it has no add-only or
merge design. *LatticeMind* (arXiv:2608.08236) compares concatenation,
LLM-merge and a state memory under late stale notes and finds concatenation
hurt most (§4.5); the stale notes are not a rejected proposal, the increment
is never isolated, and there is no delete arm or full-context reference.
*STALE* (arXiv:2605.06527) excludes contradictory dialogue by construction
(Axiom 2). *Control-plane placement* (arXiv:2606.15903) compares thirteen
memory configurations including add-only, tombstone and the Mem0 router, at
the retrieval layer, with no full-context arm; its Appendix P reports that the
Mem0 router under-deletes in practice, which our real-system leg confirms at
the action layer. *Memora / FAMA* (arXiv:2604.20006) deliberately excludes
restatements (App. B.5). *MemOps* (arXiv:2607.12893) reports Mem0's stale
value rate at 0.102 against 0.016 for long context with no restatement, the
closest quantitative support for the delete ≫ full ordering we find.
*MemStrata* (arXiv:2606.26511) has a supersede-or-reinforce rule that would
let a re-assertion re-supersede a retraction, but its triple model cannot
record a negation. *MemoryArena* (arXiv:2602.16313) compares full context,
Mem0 and RAG on executable plans without a restatement manipulation.

Three 2026 papers move conflict resolution to the write or commit layer and
are adjacent without overlapping: *TOKI* (arXiv:2606.06240) types four
write-time heuristics as bitemporal operators and keeps the losing fact in
an audit row; *MemTX* (arXiv:2607.23929) gates irreversible tool calls on a
transactional belief state and measures downstream harm on a 90-case
conformance suite with concurrent writers; *Governed Persistent Memory*
(arXiv:2608.12476) makes non-revival after retraction an executable ledger
clause and compares raw-append, latest-first and conflict-preserving
policies by contract match. None constructs a rejection in dialogue or a
partner's restatement. *The Memory Trust Gap* (arXiv:2609.01852) is the
closest on decider size: across Qwen3 0.6B–8B, a stale stored fact is
answered with 0.92–1.00 of the time, and *larger* models collapse most when
metadata makes the stale note look current. Our larger deciders honour an
explicit stored rejection better than the small ones; the two findings
concern different quantities (a stale value framed as current versus a
rejection rendered as a rejection) and are read side by side, not against
each other. On the shipped side, Mem0's own issue tracker records the v3
add-only behaviour we read from source: contradictory facts accumulate in
parallel and the MD5 deduplication catches only exact duplicates (issues
#4896 and #4956, April 2026).

What is new here is the conjunction: a partner's content-bearing restatement
of a step rejected in dialogue, delivered through the designs that ship, read
on an executable plan by small local deciders, as a difference-in-differences
against a length-matched neutral line.

## 3. Setup

**Corpus.** The E16 benchmark generates two-speaker incident dialogues from
six domains × six constraint graphs × four rotations. Each dialogue contains
proposals with an acceptance or a rejection reply, plus noise lines; scorer
tags never enter the prompt. The 96 dialogues carrying exactly one rejected
step form the E29 corpus (hash `187a426616f26598`). Each is rendered in two
arms differing by one line, spoken by the original proposer as late as speaker
alternation allows:

    restated   For the record, I did raise {action phrase} earlier in this discussion.
    neutral    For the record, I did raise {neutral referent of equal word count} earlier in this discussion.

Tests enforce the one-line difference, same speaker, same word count, and that
base lines are byte-identical to the benchmark.

**Designs.** Stores are rendered from the scorer's tags by fixed templates —
the design's semantic ideal, so what is measured is the decider's response to
each design, not an extractor's reliability (the real extractor is §4.4).
`full`: the transcript. `delete`: ADD on proposal, UPDATE on acceptance, on
rejection DELETE the proposal and store nothing; a later restatement is ADDed.
`addonly`: every fact kept in insertion order. `wiki`: one page per action
with chronological bullets plus a discussion-log page. Tests assert, per
dialogue, that under `delete`/neutral no trace of the rejected step remains
and under `delete`/restated exactly one mention and no rejection.

**Decider.** A fixed system prompt (the E10 Operator), the design's context
block, and a frozen plan instruction that pins the plan to four steps from a
six-item action vocabulary (E17 `pin4`), temperature 0. The plan is parsed
deterministically; the outcome per dialogue is whether the rejected step's
identifier is in the plan.

**Estimands and read rule, fixed before the first call.** Δ_X = P(rejected
step in plan | restated, X) − P(… | neutral, X); DiD_X = Δ_X − Δ_full. Paired
bootstrap over dialogues, seed 0, B = 2000, percentile 95 % intervals.
DESIGN-DEPENDENT if some |DiD_X| ≥ 0.15 with an interval excluding 0; a cell
is void if parse rate < 0.95 or mean plan length outside [3.9, 4.1]. Every
cell in every run below parsed at 1.000 with mean length 3.98–4.00.

## 4. Results

### 4.1 Design dependence on three deciders (first corpus)

Rejected-step inclusion, n = 96 dialogues per cell.

| decider | design | restated | neutral | Δ_X | DiD_X | 95 % CI |
|---|---|---|---|---|---|---|
| llama3.2:3b | full | 0.198 | 0.281 | −0.083 | ref | |
| | delete | 0.958 | 0.604 | +0.354 | **+0.438** | [+0.312, +0.562] |
| | addonly | 0.188 | 0.177 | +0.010 | +0.094 | [−0.010, +0.198] |
| | wiki | 0.240 | 0.135 | +0.104 | +0.188 | [+0.073, +0.312] |
| qwen2.5:7b-instruct | full | 0.240 | 0.312 | −0.073 | ref | |
| | delete | 0.885 | 0.583 | +0.302 | **+0.375** | [+0.271, +0.490] |
| | addonly | 0.312 | 0.344 | −0.031 | +0.042 | [−0.052, +0.135] |
| | wiki | 0.354 | 0.271 | +0.083 | +0.156 | [+0.042, +0.281] |
| qwen2.5:14b-instruct | full | 0.219 | 0.167 | +0.052 | ref | |
| | delete | 0.896 | 0.635 | +0.260 | **+0.208** | [+0.094, +0.323] |
| | addonly | 0.062 | 0.062 | +0.000 | −0.052 | [−0.135, +0.021] |
| | wiki | 0.062 | 0.094 | −0.031 | −0.083 | [−0.167, −0.000] |
| gemma4:e4b | full | 0.125 | 0.135 | −0.010 | ref | |
| | delete | 0.979 | 0.490 | +0.490 | **+0.500** | [+0.375, +0.625] |
| | addonly | 0.000 | 0.000 | +0.000 | +0.010 | [−0.062, +0.094] |
| | wiki | 0.000 | 0.000 | +0.000 | +0.010 | [−0.062, +0.094] |

All four deciders read DESIGN-DEPENDENT by the pre-registered rule, carried
by `delete`. On gemma4:e4b, a third model family, the dependence is absolute:
in 384 add-only and wiki cells it never enacts a step whose rejection it can
see, and under hard delete it enacts the step at the never-mentioned rate
(0.49) until the restatement arrives and at 0.98 after it. The predicted size for `delete` on the 3B model (≈ +0.4, derived
from that model's known rates for never-mentioned and proposed-only steps)
landed at +0.354. The larger decider changes two things. Under add-only and
wiki it almost never enacts the rejected step (0.06): it reads a stored
rejection and honours it, where the small deciders partly do not, so only the
design that removes the rejection re-admits the step. And under
`delete`/neutral it enacts the step at 0.635 from a store that says nothing
about it, because a pinned four-step plan over a six-item menu is completed
from the menu (the never-mentioned control in that cell is 0.54). That caps
Δ_delete on the 14B decider; the smaller DiD is a ceiling of the estimand, not
a weaker mechanism.

### 4.2 A second corpus

Six new domains (a grid substation fault, an airline hub disruption, a
newsroom CMS outage, a water-plant fault, an e-commerce checkout failure, a
mobile-core degradation) with new action phrases and a second bank of
sentence templates, generated by the same rules (hash `7d33038c6c1a9912`);
the frozen first corpus is hash-asserted untouched.

| decider | design | restated | neutral | Δ_X | DiD_X | 95 % CI |
|---|---|---|---|---|---|---|
| llama3.2:3b | full | 0.604 | 0.760 | −0.156 | ref | |
| | delete | 0.948 | 0.677 | +0.271 | **+0.427** | [+0.312, +0.552] |
| | addonly | 0.354 | 0.333 | +0.021 | +0.177 | [+0.073, +0.281] |
| | wiki | 0.500 | 0.344 | +0.156 | +0.312 | [+0.198, +0.438] |
| qwen2.5:7b-instruct | full | 0.521 | 0.677 | −0.156 | ref | |
| | delete | 0.958 | 0.531 | +0.427 | **+0.583** | [+0.458, +0.719] |
| | addonly | 0.406 | 0.490 | −0.083 | +0.073 | [−0.052, +0.198] |
| | wiki | 0.438 | 0.333 | +0.104 | +0.260 | [+0.146, +0.385] |
| qwen2.5:14b-instruct | full | 0.552 | 0.521 | +0.031 | ref | |
| | delete | 0.990 | 0.646 | +0.344 | **+0.312** | [+0.187, +0.448] |
| | addonly | 0.146 | 0.115 | +0.031 | +0.000 | [−0.104, +0.104] |
| | wiki | 0.177 | 0.104 | +0.073 | +0.042 | [−0.062, +0.146] |

All three deciders read DESIGN-DEPENDENT on the second corpus as well; the 14B reading is the cleanest, with no prediction and no control failing. The ordering delete ≫ wiki > addonly ≈ 0 holds on the small deciders and delete ≫ addonly ≈ wiki ≈ 0 on the 14B; the levels do not. Under full
context the rejected step comes back at 0.76 and 0.68 (neutral arm) against
0.28 and 0.31 on the first corpus, with never-mentioned controls near 0.5 on
both, so the new rejection wordings ("take that one off", "I'd leave that
out") are honoured far less by small deciders than the first bank's ("drop
that one — it is not needed"). Absolute zombie rates are a property of wording
and domain; the design contrast is not. Two cautions the second corpus makes
visible: the DiD estimand inherits the reference arm's movement, so with
Δ_full at −0.156 every design's DiD sits 0.156 above its own Δ and add-only's
DiD trips the pre-registered band on the 3B model although add-only itself
did not respond (+0.010); we therefore report Δ_X beside DiD_X throughout, and
the within-store contrast Δ_delete vs Δ_addonly (+0.271 vs +0.021, +0.427 vs
−0.083, +0.344 vs +0.031 here; +0.354 vs +0.010, +0.302 vs −0.031, +0.260 vs +0.000 on the first
corpus) is the reading that does not depend on the reference arm.

### 4.3 The full-context register effect

Under full context the restatement *lowered* enactment on the 3B and 7B
deciders (−0.083 and −0.073 on the first corpus, −0.156 on both on the
second), against a prediction of "small". A follow-up (E29-C, 768 calls)
re-ran the two E29 lines beside a plain late mention with no authorship claim
("Just to note it, X came up earlier in this discussion") and its own neutral
control, ten words plus the referent in every arm. On the 3B decider the E29
number replicated to the third decimal (−0.083 [−0.156, −0.010]), the plain
mention did nothing (+0.062 [−0.010, +0.135]), and the difference between the
two framings excluded zero (−0.146 [−0.240, −0.062]): FRAMING by the
pre-registered rule. On the 7B decider the interval's upper bound landed
exactly on zero (−0.062 [−0.135, +0.000]) and the declared verdict is
NO-REPLICATION, not upgraded; the shape is the same. The protective effect,
where it exists, comes from the "for the record, I did raise it" register,
which sends a full-context reader back to the exchange where the step was
rejected. The stores never see that register; they see a fact. This sharpens
the main result rather than qualifying it.

### 4.4 The real write path

**A first attempt that failed by its own rule.** E29-B ran the Mem0 paper's
`FACT_RETRIEVAL_PROMPT` and `DEFAULT_UPDATE_MEMORY_PROMPT` verbatim with a 3B
model on 48 of the dialogues. The manipulation check declared in advance
(the store must mention the proposed step after its proposal line in ≥ 0.5 of
dialogues) failed at 0.11: a personal-information extractor does not store
operational proposals. The stage was stopped at 18 dialogues and recorded as
uninformative.

**E29-D.** One change: an extraction prompt in the same form asking for
operational facts (steps proposed and by whom, decisions on steps resolved
against the step named in the previous message, references back), with
few-shot examples on a domain that appears nowhere in the corpus. The update
router is Mem0's, verbatim, with the whole live store as old memories.
Extractor and router qwen2.5:7b-instruct, decider llama3.2:3b, the same 48
dialogues, every store snapshot kept.

| quantity | value |
|---|---|
| store mentions the proposed step after its proposal line | 0.958 |
| rejection removed the step from the store, given it was there | 0.217 (n = 46) |
| final store mentions the rejected step, restated / neutral | 0.854 / 0.750 |
| router events per dialogue, ADD / UPDATE / DELETE | 6.5 / 3.8 / 0.35 |
| rejected step enacted, restated / neutral | 0.667 / 0.500 |
| Δ_real | **+0.167 [+0.042, +0.292]** |
| E29 oracle delete / addonly / full on the same 48 dialogues | +0.396 / +0.042 / −0.125 |

REAL-STORE EFFECT by the pre-registered rule, with all four predictions
holding: the extractor stores the step; the router under-deletes (one
rejection in five becomes a DELETE, the rest become an ADD of the rejection or
an UPDATE of the proposal's text); the restatement enters as a fresh fact; and
the real store lands between the add-only and hard-delete ideals. One
observation beyond the predictions: neutral-arm enactment on the real store
(0.50) is far above oracle add-only (0.17) although the rejection is usually
present, because the router's UPDATEs fold the rejection into the proposal's
own text and the 3B decider reads the merged line as weaker than a separate
rejection.

### 4.5 Controls

Accepted steps are enacted at 0.97–1.00 in every cell of every run.
Never-mentioned steps are enacted at 0.42–0.73 depending on decider, design
and corpus; that band is the pinned-plan prior over the menu and is the reason
Δ_delete has a ceiling. Under `delete`/neutral the rejected step's inclusion
stays within 0.10 of its cell's never-mentioned rate on both corpora for
every decider run.

## 5. Limitations

Two generated corpora with shared construction rules and three-template
sentence banks, not naturalistic dialogue. Oracle stores are semantic ideals;
the real-system leg uses one extractor prompt of ours, one extractor model,
one decider, no embedder or vector store, and a keyword rule for "mentions"
that undercounts paraphrase. Deciders are 3B–14B local instruct models from three families. The
DiD estimand is sensitive to the full-context reference, which moves with
decider and corpus; we report Δ_X alongside. Levels across designs mix the
design with the explicitness of the rendering (an oracle store spells out the
referent of a rejection where the transcript leaves it to adjacency), so only
within-design contrasts are compared. The compulsory course experiment this
work sits beside (E1) turned out, on its own sanity arms, to be measuring plan
plausibility under an action menu rather than retrieval; we record that there
because it shaped the pinned-plan design here. Two controls a reviewer would
reasonably ask for are not run and are named as follow-ups: a rendering
control that presents the transcript's rejection in the store's explicit
template, so that levels across designs could be compared and not only
within-design contrasts; and a tombstone design (rejection retained but
flagged inactive) as a fifth arm between add-only and hard delete.

## 6. Reproducibility

Every protocol in `docs/protocols/` was committed with zero outcomes before
its first call and appended with the outcome afterwards; commit hashes are
named in each. Corpus hashes: E16 `70f136a47f5779c8`, E29 `187a426616f26598`,
E29-C `979143b67049adf2`, E29-N `7d33038c6c1a9912`; runners refuse to start if
a hash moves. `pytest` runs 203 tests, including the store invariants. One extractor bug
reached a run: the oracle extractor keyed reply polarity on a sentence prefix
and mis-stored one second-corpus rejection wording as an acceptance in 24 of
96 dialogues (store designs only). It was found by reading, fixed by template
membership with a test, and the 144 affected cells per decider were re-run;
the first-corpus blocks were hash-verified byte-identical before and after,
and both versions of every second-corpus number are on disk
(`docs/protocols/E29N-second-corpus.md` §6–7). Runs
re-execute with `python e29_memory_semantics.py --model M [--corpus new]`,
`python e29c_framing.py`, `python e29d_ops_extractor.py`; analyses with the
matching `*_analysis.py`, zero model calls. `python xray_server.py` serves an
interactive report and a replay of any dialogue through any design, with a
live re-run of the decider checked against the record.

## Appendix A. Predictions against outcomes

| protocol | prediction | outcome |
|---|---|---|
| E29 P1 | Δ_delete ≈ +0.4 on the 3B decider | +0.354 |
| E29 P2 | DiD_delete ≥ 0.15, interval excludes 0 | +0.438, +0.375, +0.208, +0.500 on four deciders |
| E29 P3 | Δ_full small | small, but negative on 3B/7B: a miss on sign, followed up in E29-C |
| E29 P4 | 0 ≤ DiD_addonly < DiD_delete | +0.094, +0.042, −0.052, +0.010 |
| E29-B | manipulation check ≥ 0.5 | 0.11: UNINFORMATIVE, stopped |
| E29-C P1 | Δ_ftr replicates on 3B | −0.083 vs −0.083 |
| E29-C P2 | H-frame vs H-mention | FRAMING (3B); NO-REPLICATION at the boundary (7B) |
| E29-D P0–P3 | store ≥ 0.5; W1 < 0.5; 0 ≤ Δ_real < Δ_delete; W2 restated > neutral | 0.958; 0.217; +0.167 < +0.396; 0.854 > 0.750 |
| E29-N P1 | DESIGN-DEPENDENT via delete on each decider | +0.427, +0.583, +0.312 (after the extractor correction; +0.344, +0.469, +0.250 before) |
| E29-N P2 | |DiD_addonly| < 0.15 | holds on 7B (+0.073) and 14B (0.000), fails on 3B (+0.177) through the reference arm |
