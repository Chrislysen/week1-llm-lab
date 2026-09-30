# E29 — does a partner's restatement of a rejected step raise enactment by an amount that depends on the memory design?

**Declared 2026-09-11 with zero E29 model calls.** Gated under
`docs/NOVELTY-GATE.md` the same day (§0 below). **Decision: CANDIDATE FOR
TESTING with a NARROW residual.** That licenses this experiment; it is not a
novelty claim and not a prediction of success. Ledger going in: 22 gated, 22
closed.

Corpus `lineage_e29.py`, hash **`187a426616f26598`** on top of the E16 corpus
`70f136a47f5779c8`. Runner `e29_memory_semantics.py`. Read rule
`e29_analysis.py`. Tests `test_lineage_e29.py` (10, all passing).

---

## 0. Prior-art gate (run first, 2026-09-11)

### 0.1 The construct, before any search

**Objects.** A two-agent dialogue in which a step is *proposed* and then
*explicitly rejected* in the next line and never replaced (E16's `rejected`
status); a later single line by the original proposer that *restates* the
step as a mention, or a length-matched *neutral* line; a *memory design* that
turns the dialogue into what the decider sees; a decider that writes a
four-step plan from a six-identifier menu; a deterministic scorer that reads
whether the rejected step is in the plan.

**Operations.** Four designs, three of them the write/read semantics of shipped
systems, read from their source:

| design | write time | read time | source read |
|---|---|---|---|
| `full` | none | raw transcript | E17/E18 |
| `delete` | facts extracted; an LLM chooses ADD/UPDATE/DELETE/NONE per fact against retrieved memories; a contradiction **DELETEs** the old fact and the DELETE example stores nothing new; no tombstone; the update prompt sees only live memories | live facts | Mem0 paper arXiv:2504.19413; `mem0/configs/prompts.py` `DEFAULT_UPDATE_MEMORY_PROMPT` (fetched 2026-09-11) |
| `addonly` | every extracted fact ADDed; no UPDATE/DELETE exists; agent utterances stored "with equal weight" | similarity only, no recency weighting; `attributed_to` stored but unused; temporal features raise in OSS | Mem0 OSS v3 (April 2026): `mem0/memory/main.py` "V3 PHASED BATCH PIPELINE", migration doc, v3 blog |
| `wiki` | one page per entity, "merge old + new instead of clobbering"; contradictions become review items for a human, never resolved in the page | the page | nashsu/llm_wiki `src/lib/ingest.ts`, `page-merge.ts`; Karpathy's LLM-wiki gist |

**Estimand.** For design X, Δ_X = P(rejected step in plan | restated, X) −
P(… | neutral, X); the contrast of interest is **DiD_X = Δ_X − Δ_full**.

**Intervention.** One inserted line, restated vs neutral, differing only in its
referent (same speaker, position, word count). **Fixed-intervention** comparison:
nothing is tuned per design.

**Assumptions, stated.** (1) Stage 1 uses **oracle extraction**: each store is
rendered from the scorer's tags by a fixed template, so it is the design's
semantic ideal, not an extractor's output. (2) The decider's response to the
store is the quantity measured, not the store's fidelity. (3) The `delete`
arm assumes the DELETE fires; arXiv:2606.15903 App. P reports that Mem0's LLM
router in practice "prioritises link-and-keep over delete-old", so a real
router pushes `delete` toward `addonly`. That is a stage-2 question.

### 0.2 Vocabulary map

| our term | the field's terms searched |
|---|---|
| rejected proposal, zombie constraint | revoked / retracted / superseded instruction, knowledge update, memory invalidation, stale memory, forgetting, unlearning, obsolete plan |
| partner restatement | echo, recap, re-mention, re-assertion, restated stale note, elicitation probe, memory contagion, write-back amplification, manufactured corroboration, memory majority |
| memory design | write-time vs read-time conflict resolution, ADD/UPDATE/DELETE router, append-only / add-only store, tombstone, soft vs hard delete, merge-in-place, control-plane placement, bi-temporal ledger, state memory |
| plan enactment | downstream action, executable plan, provider pick, tool-call parameters, implicit policy adaptation, constraint drift |

### 0.3 Leads resolved — full text read, sections cited

| paper | read | rejection in dialogue | partner restatement | design contrast | executable action | small local decider | verdict |
|---|---|---|---|---|---|---|---|
| **2609.04875** Forgetting Without Restarting | full PDF | no: operator/user *revocation event* | no: same-agent *introspection probe* re-licenses (0.87–1.00, Elicitation §) | B0–B9 forget mechanisms; B1 memory-delete leaves transcript; no add-only / merge / memory-only channel | yes: provider pick, Table 3, **B1 = B0 = 1.00** act on revoked preference | Llama-3.1-8B, Qwen2.5-7B, Mistral-7B | **PARTIAL** |
| **2608.08236** LatticeMind | full PDF | no: simultaneous incompatible claims | yes, of stale notes, not of a rejected proposal, no with/without contrast (A.4–A.5) | Concat / LLM-Merge / LLM-Merge-Inc / StateMemory (§4.5, Table 2); no delete, no full context | token-checked answers; planning benchmarks only for aggregation | no: Qwen3-Max; 14B only as learned operator | **PARTIAL** |
| **2605.06527** STALE | full HTML | **excluded by construction**, Axiom 2 §3.2 | no: single user | plain full context vs LightMem/Zep/LiCoMemory/A-mem/mem-0 on one backbone (§4.1, Table 2) | IPA, LLM-judged free text | no | **PARTIAL** |
| **2606.15903** Control-Plane Placement | full HTML+PDF | no: API `supersede/release/purge` calls | no | 13 configs incl. add-only (MemPalace, `infer=False`), tombstone (Lethe), router (Mem0 `infer=True`); **no full-context arm** | no: top-10 retrieval blob | no: embeddings + API judges | **PARTIAL** |
| **2604.20006** Memora / FAMA | full HTML | yes: user-expressed deletions | **deliberately excluded** (App. B.5) | full-context LLMs vs six memory agents as black boxes | no: text answers, 3 LLM judges | 32B only | **PARTIAL** |
| **2606.24322** TMA-NM | full HTML | no | echo via trusted tool, adversarial content | authorization classes on one store | consequential-action rate | no | PARTIAL (echo half) |
| **2606.27472** Supersede | full PDF | no: value updates | no: off-topic distractors | full context vs one bounded rewrite memory | no: QA | Qwen2.5-3B (9.0 → 16.7 % after GRPO) | does not cover |
| **2605.10481** Constraint Drift | full HTML | no | no | none varied; replay of privacy traces | leakage admit/block | no | does not cover |
| **2608.19701** CAMA | full HTML | no | write-back amplification, unmanipulated | none | QA | no | does not cover |
| **2606.01435** Freshness recipe | full HTML | no | no | append-only + serial recency vs LLM freshness | QA | no | does not cover |
| **2609.03340** PlanFence | HTML | version drift, not rejection | no | validation policies over one store | deterministic | no | does not cover |
| **2607.02579** GovMem | HTML | no | motivational only; pilot unrun | promotion policies | precision/recall | no | does not cover |

**Abstract-level only (coverage limit, recorded):** 2607.12893 MemOps,
2606.10677 Infini Memory, 2605.12978 Useful Memories Become Faulty, 2606.26511
MemStrata, 2507.05257 MemoryAgentBench FactConsolidation, 2602.16313
MemoryArena. All are single-agent, QA or task-score, with no restatement
manipulation by their abstracts; they occupy the *design-contrast* component,
which is conceded as occupied regardless.

**Coverage limit CLOSED, 2026-09-11, after the E29 outcomes were recorded.**
All six read in full text by section. None constructs a rejection in
dialogue, a partner restatement, or a with/without-restatement contrast; none
contradicts the E29 direction. Details that matter: MemOps Table 3 has Mem0's
Stale Value Rate at 0.102 against 0.016 for GPT-4o long context with no
restatement at all, the closest quantitative support for delete ≫ full;
MemStrata's §4.1 rule ("same key, different object → supersede; same object →
reinforce") would let a re-assertion of the old value re-supersede the
retraction, the flip E29 measures, but its triple model cannot record a
negation so the rejection would never enter its ledger; MemoryAgentBench SF
is serial-numbered sentences, Mem0 18.0 vs long context 45–78 (Table 3);
MemoryArena is PARTIAL on the executable-plan-under-memory-design half only
(full context vs Mem0 vs RAG, §4.1, Table 3) and the "pass^5" attributed to it
in this session's search notes is not in the paper; Infini's merge-vs-append
ablation is LongMemEval-only (§4.3.1, Table 2), not the selective-forgetting
split as the search summary said; Useful Memories finds agent-chosen pruning
*helps* relative to append-only in a trajectory store with no re-mention
(§6.4, Table 5), which does not touch E29's write-time-delete-then-restatement
mechanism. The gate's coverage is now full-text on all eighteen named papers.

Search log: 19 field-vocabulary queries by the gate agents plus 9 in this
session, 2026-09-11; queries and returns recorded in the session transcript
and summarised in the table above.

### 0.3b Leads from the first Gemini Deep Research scout, triaged 2026-09-12

Nine new leads; the one Gemini flagged as covering the construct does not.
Full-text reads marked.

| paper | read | rejection in dialogue | partner restatement | design contrast | executable action | small local decider | verdict |
|---|---|---|---|---|---|---|---|
| **2609.01852** Memory Trust Gap (Hu, Ramachandran, 2026-09-01) | full HTML | no: stale stored fact vs authoritative tool, single response | no: 2×2×2×2 over metadata features (date, label, position, framing) | no_memory / clean / stale / explicit_conflict; no store designs | yes: constrained action | Qwen3 0.6–8B, Llama 1–8B | **does not cover**; opposite scale direction under a different manipulation (framing fools larger models; our larger deciders honour an explicit rejection) |
| **2607.23929** MemTX | full HTML | no: retraction events in a write trace | **no** | Cordon, Verified Concurrency, MemState, Collaborative Memory, TOKI vs MemTX | downstream harm on tool calls | Qwen3-8B, Qwen2.5-14B among five | does not cover |
| **2608.12476** GPM | full PDF | no: single-user ledger | **no** | raw append / latest-first / flat conflict-preserving / GPM, contract match | no: deterministic release; LLM only as ungoverned comparison | Qwen2.5-7B (ungoverned arm) | does not cover |
| **2606.06240** TOKI | full HTML | no | **no** | four write-time heuristics as bitemporal operators | no: LoCoMo QA | not stated | does not cover |
| 2606.24535 · 2606.22030 · 2606.09483 · 2607.01071 | abstract | no | no | yes (various) | no | various | do not cover by abstract; none names a restatement |
| ReviseQA (OpenReview Z4KBiAYXlI; Gemini's arXiv id was wrong) | abstract | premise edits, single agent | no | none | no | GPT-4o | does not cover |

Coverage stays full-text on every lead that could plausibly overlap. The
residual in §0.5 is unchanged.

### 0.3c Leads from the second Gemini Deep Research scout, triaged 2026-09-12

SINCE = 2026-09-01, corpora focus. Seven leads. One lands on a follow-up,
none on the E29 residual.

| paper | read | rejection in dialogue | partner restatement | design contrast | executable action | small local decider | verdict |
|---|---|---|---|---|---|---|---|
| **2609.08258** Revoked but Still Authoritative (Shen, Toyoda, Leung, 2026-09-08) | full HTML | no: developer-set expiry field, or an extractor detecting supersession in prose | **no**: §C.1 is agent write-back, §C.2 is cross-role retrieval; neither re-raises a rejected proposal | Graphiti / mem0 / Zep / langmem / cognee; soft revocation vs overwrite vs prune. **No arm stores the rejection as prose** | yes: one unsafe action per policy scenario | no: nine API and mid-tier models, smallest open weight Gemma-3-27B | **does not cover the residual; PREEMPTS the headline of E29-T.** Exposure 81/81 on the two exposed systems, unsafe-action 43.1 % pooled, store filter → 0. See §0.3d |
| **2605.06527** STALE, re-flagged | the quoted method line | no | **no**: Premise Resistance is a misleading *query* presupposing a stale state | frontier LLMs, LiCoMemory, CUPMem | no: text answers | Qwen3.5-27B, Gemini-3.1-pro | does not cover; the run-1 row stands |
| **2608.01619** StateAuditor | abstract | no | no | draft-anchored audit vs predecessor | no: draft responses, VTA | GPT-4o, gpt-5.5 | does not cover |
| **2605.14175** Grounded Continuation | abstract | retraction as one of eight epistemic operations, single user | no | verifier vs budget-matched retrieval | no: QA | Qwen2.5-7B/14B among five | does not cover |
| **2607.05844** StateFuse | abstract | no | no | flat multi-value / raw-log / provenance / collapsed / StateFuse | no: MemoryAgentBench QA | not stated | does not cover |
| **2609.10263** RD-Forget | abstract | no | no | retained archive vs query-conditioned view | no | four models | does not cover |
| **2606.01435** (retitled *Reliable Post-Retrieval Assembly for Agent Memory*, v2 2026-08-02) | abstract | no | no | two-stage assembly vs entangled generation | no: QA | GPT-4o, GPT-4o-mini | does not cover; corrects the title carried in §0.3 |

### 0.3d Coverage miss, recorded 2026-09-12

arXiv:2609.08258 was on arXiv from 2026-09-08. This gate ran 2026-09-11 over
eighteen papers and did not surface it. It does not change this protocol's
verdict or residual: it has no dialogue rejection, no partner restatement, and
no arm that stores a rejection as prose, so every component of the conjunction
in §0.5 stands. It does preempt the headline of the tombstone control declared
the following day (`docs/protocols/E29X-reviewer-controls.md` §5), which is
recorded there. The standing lesson from memory applies for the third time: a
gate that has not searched the current fortnight has not searched.

### 0.4 Comparison against the strongest prior work

| proposed contribution | closest prior result + section | same mechanism, estimand, assumptions? | substantive difference | what would test that difference |
|---|---|---|---|---|
| A partner's content-bearing restatement of a dialogue-rejected step raises plan enactment by a design-dependent amount | 2609.04875, Table 3 (B1 = B0 = 1.00) and Elicitation § (introspection probe re-licenses 0.87–1.00, condition-dependent) | No. Their revocation is an operator event, the re-mention is a same-agent recall probe carrying no content, the transcript stays in context under B1, and there is no neutral-line control or DiD | rejection arises *in dialogue*; the restatement is a *partner's* content-bearing line; the decider sees the memory artifact *only*; add-only and merge designs; length-matched neutral control; DiD | exactly this experiment |
| Add-only vs merge-page vs hard-delete under a stale restatement | LatticeMind §4.5 (Concat < LLM-Merge < StateMemory under late stale notes) | Partly: their stale notes are not a rejected proposal, the increment is never isolated, no delete arm, no full context, frontier model | delete arm; full-context reference; isolated increment; 3B–7B deciders; plan scorer | this experiment |
| Memory-design changes whether a superseded item survives to the decision | 2606.15903 (retrieval blob), STALE Table 2, Memora | Same direction of question, different layer (retrieval vs action) and no dialogue | action-level, dialogue-sourced | this experiment |

### 0.5 Residual, and how it fails

> The closest work establishes that deleting a memory record while the
> transcript persists does not stop action on a revoked preference, that a
> same-agent recall probe re-licenses a suppressed value in a
> mechanism-dependent way, and that late stale notes in a shared store hurt
> concatenation more than status-aware memory. This candidate would
> additionally establish whether a **partner's content-bearing restatement** of
> a step **rejected in dialogue** raises plan enactment by an amount that
> **depends on the memory design** the decider reads through (hard-delete,
> add-only, merge-page, full context), as a difference-in-differences against
> a length-matched neutral line, on small local deciders with a deterministic
> plan scorer, which matters because these are the three designs actually
> shipped and Mem0 moved from the first to the second in April 2026 citing lost
> context, with no published measurement of the supersession cost.

> The claimed additional contribution would be unsupported if every DiD_X lies
> inside the SESOI band: then the restatement effect is E18 revocation inertia
> plus known corroboration effects, and the memory design does not modulate
> it. It would also be unsupported, as *novelty*, if a paper is found that
> manipulates a partner restatement of a dialogue-rejected item across
> memory designs; the coverage limit in §0.3 names the papers not read in full.

**Decision: CANDIDATE FOR TESTING.** Residual NARROW. Two corrections to the
candidate as first phrased, forced by reading: Lethe (2606.15903) is a tombstone
design, not a hard-deleter; and the paper-pipeline router under-deletes in
practice (App. P), so the `delete` arm is the design's *semantic ideal*.

---

## 1. Design

**Corpus.** The 96 E16 dialogues that carry a `rejected` slot, each in two
arms that differ in exactly one line spoken by the original proposer, as late
as speaker alternation allows, with the dialogue still ending on noise:

    restated   For the record, I did raise {action phrase} earlier in this discussion.
    neutral    For the record, I did raise {neutral referent of equal word count} earlier in this discussion.

39 of 96 dialogues need the domain's fourth noise line appended to keep the
proposer's turn; both arms share that structure. Tests enforce: one-line
difference, same speaker, same word count, base lines byte-identical to E16.

**Stores (oracle extraction), one fact per line by fixed template.**
`delete`: ADD on proposal/noise/restate/neutral; UPDATE the proposal on
acceptance; on rejection DELETE the proposal and store nothing. `addonly`: every
fact, insertion order. `wiki`: a page per action with chronological bullets,
plus a discussion-log page. `full`: the transcript. The tests assert, for every
dialogue: under `delete`/neutral no trace of the rejected step; under
`delete`/restated exactly one mention and no rejection; under `addonly` proposal
+ rejection (+ restatement); under `wiki` proposal and rejection bullets on one
page.

**Decider prompt.** E10's system prompt, unchanged. The user block is the
design's context block followed by E17's frozen `pin4` plan instruction at
|vocab| = 6. The block header differs by design (DISCUSSION / MEMORY NOTES FROM
THE DISCUSSION / WIKI PAGES BUILT FROM THE DISCUSSION); the DiD compares arms
*within* a design, so the header is constant within every contrast.

**Deciders.** `llama3.2:3b` (the course model) first; `qwen2.5:7b-instruct`
second if the first completes. Temperature 0. Eight cells per dialogue run in
one process block in fixed order (designs inside arms).

**Allocation.** 96 × 2 × 4 = **768 scheduled calls per decider**, plus parse
retries per `ask_structured` and transport retries per `RetryingOllamaClient`,
both recorded per row. Chunked with `--offset/--limit` per the runtime note in
memory; each chunk writes its own `results/e29_<model>_o<offset>.csv/.json`.

## 2. Predictions, fixed before the first call

From the store semantics and E18's `pin4` rates for `llama3.2:3b`
(`never` 0.562, `proposed` 0.990, `rejected` 0.219):

- **P1.** Δ_delete is large and positive. Under `delete`/neutral the store holds
  nothing about the step, so inclusion ≈ the `never` rate; under
  `delete`/restated it holds a bare mention with no rejection, so inclusion ≈
  the `proposed` rate. Predicted Δ_delete ≈ +0.4.
- **P2.** DiD_delete ≥ 0.15.
- **P3.** Δ_full is small: the rejection is visible in every full-context arm.
- **P4.** 0 ≤ DiD_addonly < DiD_delete: the restatement adds a copy of the stale
  step but the rejection copy is present.
- **P5.** DiD_wiki ≈ DiD_addonly: same content, grouped by entity. A gap in
  either direction is reported as an observation, not a claim.
- **P6 (control).** Under `delete`/neutral the rejected step's inclusion is
  within ±0.10 of that cell's `never` rate.

## 3. Read rule, fixed before the first call

Unit of independence: the dialogue (96). Paired bootstrap over dialogues,
seed 0, B = 2000, percentile 95 % intervals. Implemented in `e29_analysis.py`.

- **DESIGN-DEPENDENT** if, for at least one design X ≠ full, |DiD_X| ≥ 0.15
  and its interval excludes 0.
- **NULL** if every |DiD_X| < 0.05 and every interval lies within [−0.15, +0.15].
- **PARTIAL** otherwise; reported as partial, never upgraded.

**Validity.** A cell is VOID if parse rate < 0.95 or mean |plan| outside
[3.9, 4.1]. A VOID `full` cell voids the verdict.

**Power, stated.** At n = 96 paired dialogues the interval half-width for a
DiD is roughly 0.10–0.14. The P1/P2 prediction (~0.4) is far above it; effects
in the 0.05–0.15 band will land PARTIAL and are **not** to be read as absent.

## 4. What cannot follow

- Nothing about real extractors: the stores are semantic ideals. A real-extractor
  stage needs its own declaration.
- Nothing about the Mem0 or llm_wiki *products*: their semantics are
  re-implemented from source, their code is not run.
- No model-size claim from one or two deciders.
- No novelty claim beyond §0.5's residual, and none at all if the coverage limit
  in §0.3 is closed by a paper not yet read.

## 5. Files

`lineage_e29.py`, `test_lineage_e29.py`, `e29_memory_semantics.py`,
`e29_analysis.py`; outputs `results/e29_<model>_o*.csv/.json` and
`results/e29_<model>_summary.json`. Outcome section to be appended below this
line after the run, never edited above it.

---

## Outcome — `llama3.2:3b`, run 2026-09-11

**Verdict by the declared rule: DESIGN-DEPENDENT.** 768 of 768 scheduled calls
completed in five foreground chunks (`results/e29_llama32-3b_o{0,20,40,60,80}.csv/.json`,
logs alongside). Parse rate **1.000** in all eight cells; mean |plan| **4.00**
in seven cells and 3.99 in one; no cell VOID; 0 parse retries; 96 of 96
dialogues complete on all eight cells. Read by `e29_analysis.py`, summary in
`results/e29_llama32-3b_summary.json`.

### Rejected-step inclusion, n = 96 paired dialogues per cell

| design | restated | neutral | Δ = restated − neutral | 95 % CI | **DiD vs full** | 95 % CI |
|---|---|---|---|---|---|---|
| full | 0.198 | 0.281 | −0.083 | [−0.167, −0.010] | reference | |
| **delete** | **0.958** | 0.604 | **+0.354** | [+0.260, +0.458] | **+0.438** | **[+0.312, +0.562]** |
| addonly | 0.188 | 0.177 | +0.010 | [−0.062, +0.094] | +0.094 | [−0.010, +0.198] |
| **wiki** | 0.240 | 0.135 | +0.104 | [+0.031, +0.177] | **+0.188** | **[+0.073, +0.312]** |

Paired bootstrap over dialogues, seed 0, B = 2000.

### Predictions against outcome

- **P1 confirmed.** Δ_delete = +0.354; predicted ≈ +0.4 from the `never` and
  `proposed` rates. Under `delete`/restated the step is in **0.958** of plans:
  the store carries a bare mention and no rejection, and the decider treats it
  as a live proposal.
- **P2 confirmed.** DiD_delete = +0.438, interval [+0.312, +0.562], far above
  the 0.15 threshold.
- **P3 partly wrong.** Δ_full is small, as predicted, but **negative**: with the
  transcript visible, the proposer's late "for the record, I did raise X" line
  *lowered* relapse from 0.281 to 0.198, interval excluding zero. The prediction
  said "small", not "negative". Recorded as a miss on sign. No mechanism is
  claimed; one reading is that the line points the decider back at the
  rejection block, another is that a mention flagged as history reads as
  closed. Neither is tested here.
- **P4 confirmed.** DiD_addonly = +0.094 with an interval touching zero:
  inside the partial band, below the delete effect, not read as absent.
- **P5 not confirmed.** DiD_wiki = +0.188 against DiD_addonly = +0.094. The
  same facts grouped by entity, with "noted again" directly under "rejected",
  produced a larger restatement effect than the same facts in a chronological
  list. Reported as an observation; the interval overlap between the two is
  substantial and no claim is made about the gap.
- **P6 confirmed.** Under `delete`/neutral the rejected step's inclusion is
  0.604 against that cell's `never` rate of 0.562, inside ±0.10: the design
  has forgotten the rejection *and* the proposal, and the step behaves as if
  never mentioned.

### Controls

`accepted` is 0.983–1.000 in every cell and `never` sits at 0.542–0.667, so
the eight cells differ in their handling of the rejected step and not in how
much they put in a plan. Mean |plan| is pinned throughout.

### What this establishes, and what it does not

**Establishes**, for this decider on these 96 dialogues with oracle stores:
the restatement's effect on relapse is set by the memory design it passes
through. Under write-time delete the rejection is consumed by the DELETE, the
later mention is stored with nothing to contradict it, and relapse goes from
the never-mentioned floor to near certainty. Under full context the same line
does nothing harmful. Add-only and merge-page sit between, with the merge-page
effect clearing the threshold and the add-only effect not.

**A rendering caveat that limits cross-design comparison of *levels*.** Under
the neutral arm, `addonly` (0.177) and `wiki` (0.135) show *lower* relapse than
`full` (0.281). The oracle store spells out the referent of a rejection
("rejected the proposal to snapshot the store") where the transcript leaves it
to adjacency ("No, drop that one"). Levels across designs therefore mix the
design with the explicitness of the rendering. **The read rule uses only the
within-design DiD**, which holds rendering constant; the levels are reported,
not compared.

**Does not establish.** Anything about real extractors, whose failure to
DELETE (arXiv:2606.15903 App. P) would move `delete` toward `addonly`.
Anything about the Mem0 or llm_wiki products. Any model-size claim. The
residual in §0.5 is **supported for `delete` and `wiki`** and **partial for
`addonly`** on one decider; originality remains as narrow as §0.5 states, and
the abstract-level coverage limit in §0.3 stands.

### Second decider

`qwen2.5:7b-instruct` is declared above and is run next under the same
allocation; its outcome is appended below when complete.

---

## Outcome — `qwen2.5:7b-instruct`, run 2026-09-11

**Verdict by the declared rule: DESIGN-DEPENDENT.** 768 of 768 scheduled calls
in six foreground chunks (`results/e29_qwen25-7b-instruct_o{0,16,32,48,64,80}.csv/.json`,
logs alongside). Parse rate **1.000** in all eight cells; mean |plan| 4.00 in
seven cells and 3.99 in one; no cell VOID; 0 parse retries; 96 of 96 dialogues
complete. Summary in `results/e29_qwen25-7b-instruct_summary.json`.

### Rejected-step inclusion, n = 96 paired dialogues per cell

| design | restated | neutral | Δ | 95 % CI | **DiD vs full** | 95 % CI |
|---|---|---|---|---|---|---|
| full | 0.240 | 0.312 | −0.073 | [−0.146, −0.010] | reference | |
| **delete** | **0.885** | 0.583 | **+0.302** | [+0.208, +0.396] | **+0.375** | **[+0.271, +0.490]** |
| addonly | 0.312 | 0.344 | −0.031 | [−0.094, +0.031] | +0.042 | [−0.052, +0.135] |
| **wiki** | 0.354 | 0.271 | +0.083 | [+0.000, +0.177] | **+0.156** | **[+0.042, +0.281]** |

### Predictions against outcome

P1, P2, P4, P6 confirmed as for the 3B (Δ_delete +0.302; DiD_delete +0.375;
DiD_addonly +0.042 inside the partial band and below delete; `delete`/neutral
0.583 against that cell's `never` 0.625, inside ±0.10). **P3 wrong on sign
again**: Δ_full = −0.073 with an interval excluding zero. **P5 not confirmed
again**: DiD_wiki +0.156 against DiD_addonly +0.042, though the wiki interval
[+0.042, +0.281] only just clears the 0.15 threshold at the point estimate.

### The two deciders agree

| | Δ_full | DiD_delete | DiD_addonly | DiD_wiki |
|---|---|---|---|---|
| llama3.2:3b | −0.083 | +0.438 | +0.094 | +0.188 |
| qwen2.5:7b-instruct | −0.073 | +0.375 | +0.042 | +0.156 |

Same ordering, same signs, in two families. The write-time delete effect is
the large one in both; the merge-page effect clears the declared threshold in
both but sits near it; add-only is partial in both; and in both the same
restatement line *lowers* relapse when the whole transcript is visible.

### Standing

Two deciders, two families, one corpus, oracle stores, one pinned length. The
residual in §0.5 is **supported for `delete` and `wiki` in both deciders** and
**partial for `addonly` in both**. The rendering caveat, the extractor caveat
and the coverage limit stated for the 3B all stand unchanged. Nothing here is a
model-size claim, and nothing here runs a real extractor or a shipped product.
No further arm is authorised by this protocol.

---

# E29-B — the same write path, run for real by a small model

**Declared 2026-09-11, after both E29 outcomes above were recorded.** E29's
`delete` store was an oracle: the DELETE always fired. E29-B replaces the
oracle with the Mem0 paper pipeline's own prompts, run by `llama3.2:3b`, line
by line, and lets the decider read the store the extractor actually produced.
Runner `e29b_real_extractor.py`; prompts vendored verbatim in
`mem0_vendored.py`; read rule `e29b_analysis.py`.

**Process failure, recorded.** The read rule, manipulation check and design
were committed in code at `7e4dd63` before the first call, and the commit
message states the declaration. This prose section was meant to go in at the
same time; its append failed on a mismatched anchor and the failure was not
noticed until after chunk 1 (6 dialogues, 144 write and decider calls) had
run. The **predictions P7–P9 below were therefore not committed before the
first call** and are reported as expectations written down after 6 of 48
dialogues had been seen, not as pre-registered predictions. The read rule is
unaffected: it is the one in the committed code.

## Questions

- **W1** Given the proposal made it into the store, does the rejection line
  remove it? (mem0's DELETE rule: "if the retrieved facts contain information
  that contradicts the information present in the memory, then you have to
  delete it.")
- **W2** Does the final store mention the rejected step more often in the
  restated arm than in the neutral arm?
- **D** On the real store, does the decider's relapse move with the
  restatement (Δ_real), and how does that compare with the oracle Δ_delete and
  the full-context Δ on the same dialogues?

## Design

Every second E29 dialogue in E29 order, **48 dialogues**, both arms. For each
line: extraction with `FACT_RETRIEVAL_PROMPT` on the latest exchange (previous
line + this line, mem0's `parse_messages` format), then, if any facts, one
update call built by mem0's `get_update_memory_messages` with the whole live
store as old memories (a superset of mem0's top-k), events applied as mem0
applies them, malformed output counted and treated as no-op. The common prefix
of the two arms is processed once and the store forked. Decider: E29's prompt,
`pin4`, temperature 0, reading the store rendered exactly as E29's `delete`
design rendered its oracle store. Store snapshots kept after every line.

**Deviations from mem0, stated:** temperature 0 (OSS default 0.1); no
embedding retrieval; one line per `add()`. "Mentions" is a keyword rule (all
content words of the action phrase present in a live fact); paraphrases that
drop a content word count as absent, a stated limit.

**Allocation.** At most 2 write calls per line plus 1 decider call per arm:
≈ 24 calls per dialogue, **≈ 1,150 scheduled calls**, chunked 6 dialogues at a
time; transport retries per the client, parse retries only for the decider.

## Read rule (committed in code before the first call)

**Manipulation check.** The store must mention the step after its proposal
line in ≥ 0.5 of dialogues, or the stage is **UNINFORMATIVE**: a
personal-preferences extractor may simply not extract ops steps, which is a
finding about the prompt, not about supersession.

Paired bootstrap over dialogues, seed 0, B = 2000. **REAL-STORE EFFECT** if
Δ_real ≥ 0.15 with the interval above 0; **NULL** if |Δ_real| < 0.05 with the
interval inside ±0.15; **PARTIAL** otherwise. Validity as in E29 (decider
parse ≥ 0.95, mean |plan| in [3.9, 4.1]).

## Expectations (written after chunk 1, see the process note)

- **P7** The extractor under-deletes: W1 < 0.5 (arXiv:2606.15903 App. P;
  Mem0's own v3 rationale).
- **P8** The real store behaves between E29's `addonly` and `delete`:
  0 < Δ_real < oracle Δ_delete on the same dialogues.
- **P9** W2 is higher in the restated arm than the neutral arm regardless of W1.

## What cannot follow

Nothing about the Mem0 product as shipped (no vector store, no embedder, one
temperature); one extractor model; the keyword mention rule. W1 and W2 are
descriptive and are reported with their denominators, not tested.

## Outcome — `llama3.2:3b`, run 2026-09-11, STOPPED at 18 of 48 dialogues

**Verdict by the declared rule: UNINFORMATIVE.** The manipulation check
failed: the store mentioned the step after its own proposal line in **2 of 18
dialogues (0.111)** against the 0.5 floor, across payments, robotics and
pharmacy (`results/e29b_llama32-3b_o{0,6,12}.csv/.json`, logs alongside,
summary `results/e29b_llama32-3b_summary.json`). Decider parse 1.000 in both
arms, mean |plan| 4.00 / 3.96.

**Stopped early, and why.** The check is declared over 48 dialogues. Passing
it from 2/18 would need 22 of the remaining 30, and three domains had shown
the same behaviour. The remaining 30 dialogues were not run; their allocation
is unspent and not carried forward. Spent: at most 13.8 + 13.4 write calls per
dialogue per arm (the shared prefix is counted in both arms, so the unique
total lies below 18 × 27.2 ≈ 490) plus 36 decider calls.

**What the extractor actually did** (from the line-by-line snapshots in the
`.json` files). The Mem0 paper's `FACT_RETRIEVAL_PROMPT` is a personal
information organiser; on an operations dialogue, run by a 3B model, it
stored almost nothing from a proposal line on its own. It stored the
proposal + *acceptance* exchange in several dialogues ("Cycle the settlement
engine to the plan for this one") and stored nothing from the proposal +
*rejection* exchange in all but two. So the rejected step mostly never entered
the store, not because a DELETE fired (0.17 DELETEs per dialogue, W1 = 0/2 where
the step had been stored) but because the extractor did not write it. In the
restated arm the late mention was then written as a fresh fact ("Did raise
snapshot the store earlier in this discussion") with nothing beside it: the
final store mentioned the rejected step in **0.389** of restated dialogues
against **0.222** of neutral ones (W2, n = 18 each). Malformed update output
ran 1.1–1.6 per dialogue and was treated as no-op, as mem0 does.

**Exploratory, not a verdict.** On the real store the decider's relapse was
0.722 restated vs 0.611 neutral, Δ_real **+0.111 [+0.000, +0.278]** at n = 18,
against **+0.500** under E29's oracle delete and **−0.111** under full context
on the same 18 dialogues. Direction as expected P8, magnitude between add-only
and delete; the interval touches zero and the stage is uninformative by rule,
so this is recorded and not claimed.

**What this does to E29.** Nothing to its verdicts, which were about oracle
stores and say so. It sharpens the extractor caveat: with this prompt and this
model the paper pipeline realises the "rejection leaves no trace, restatement
re-enters clean" shape by **omission at write time** rather than by DELETE. A
stage that tests the write path as a supersession mechanism needs an extractor
prompt that stores operational proposals in the first place, which is a
different declaration and not this one.

---

## Note added 2026-09-11 while building the X-ray (zero calls)

**Invented identifiers.** The plan validator accepts identifiers outside the
six offered, and the scorer reads only whether each unit's own action is
present, so an invented identifier never counts as a rejected-step inclusion
but does occupy one of the four pinned slots. Counting from the recorded
outputs: **67 of 1,536** E29 plans (4.4 %) and **22 of 876** E17/E18 `pin4`
plans (2.5 %) contain at least one such identifier, typically lifted from a
noise line ("BOOK_POST_INCIDENT_REVIEW"). This is symmetric across arms by
construction and small, and it is not corrected for in any table above; it is
recorded because the X-ray shows the raw plans and marks these identifiers
as not offered.

## Addendum — further deciders, declared 2026-09-11 (evening) with zero outcomes

§1 named two deciders. Both completed and agreed. To find out whether the
design dependence survives a larger decider and a third model family, E29 is
re-run unchanged — same corpus (`187a426616f26598`), prompts, temperature,
runner, read rule and validity rule — on:

1. `qwen2.5:14b-instruct` (the largest instruct model installed; same family
   as the second decider, five times its size);
2. `gemma4:e4b` (a third family), only if the first completes and its `full`
   cells are valid.

**Predictions, fixed before the first call.** For each decider: P1 and P2 as
in §2 (Δ_delete large and positive; DiD_delete ≥ 0.15 with an interval
excluding 0); P3 as in §2 with the sign left open, since E29-C (framing) found
the negative Δ_full to be a register effect on the 3B model that did not
replicate by the rule on the 7B one. No prediction is placed on whether the
larger decider shows a *smaller* DiD_delete; that would be an observation.

**Allocation.** 768 scheduled calls per decider, chunked at 16 dialogues
(`--offset k --limit 16`, 128 calls per chunk), each chunk writing its own
`results/e29_<model>_o<offset>.csv/.json`. Read with `e29_analysis.py`
unchanged. Outcomes appended below, one section per decider, never pooled
with the first two.

### Outcome — `qwen2.5:14b-instruct`, run 2026-09-12 (just after midnight), after `99d60fd`

768 of 768 calls in six chunks of 16 dialogues, parse 1.000 in every cell,
mean |plan| 3.99–4.00, all cells valid. `results/e29_qwen25-14b-instruct_o{0,16,32,48,64,80}.csv/.json`,
`results/e29_qwen25-14b-instruct_summary.json`.

| design | restated | neutral | Δ | 95 % CI | DiD vs full | 95 % CI |
|---|---|---|---|---|---|---|
| full | 0.219 | 0.167 | +0.052 | [−0.021, +0.125] | reference | |
| delete | 0.896 | 0.635 | +0.260 | [+0.167, +0.354] | **+0.208** | [+0.094, +0.323] |
| addonly | 0.062 | 0.062 | +0.000 | [−0.031, +0.031] | −0.052 | [−0.135, +0.021] |
| wiki | 0.062 | 0.094 | −0.031 | [−0.083, +0.010] | −0.083 | [−0.167, −0.000] |

**Verdict by the declared rule: DESIGN-DEPENDENT, delete DiD +0.208.** P1
holds (Δ_delete +0.260, interval above 0), P2 holds (DiD_delete ≥ 0.15,
interval excludes 0). P3: Δ_full is small and its sign is now positive
(+0.052, interval includes 0); read with E29-C, the negative sign on the 3B
decider was a register effect that does not carry to larger deciders. P4:
DiD_addonly is inside the SESOI band (−0.052). P5: wiki and addonly agree
(both flat); wiki's interval touches 0 on the negative side and is reported as
an observation. P6: under `delete`/neutral the rejected step's inclusion
(0.635) sits within 0.10 of that cell's `never` rate (0.542).

**What the larger decider changes.** Three things, all observations:
1. Under `addonly` and `wiki` the 14B decider almost never enacts the rejected
   step (0.06), where the 3B and 7B deciders did so at 0.18–0.35. A larger
   decider reads the stored rejection and honours it; the smaller ones
   partly do not. The design dependence therefore sharpens with model size:
   only the design that *removes* the rejection re-admits the step.
2. Under `delete`/neutral the rejected step is enacted at 0.635 although the
   store says nothing about it: with a pinned four-step plan and a six-item
   vocabulary, a sparse store is completed from the menu (the `never` control
   in that cell is 0.54). That caps Δ_delete on this decider at about
   1 − 0.635, so the smaller DiD (+0.21 vs +0.44 and +0.38) is a ceiling
   effect of the estimand, not a weaker mechanism.
3. Δ_full changes sign across deciders (−0.083, −0.073, +0.052), consistent
   with E29-C: a register effect specific to the 3B model.

### Outcome — `gemma4:e4b`, run 2026-09-12 (morning), after `99d60fd`

768 of 768 calls in nineteen foreground chunks of five or six dialogues
(this model runs at about 11 s per call here; a first 16-dialogue chunk was
killed by the background-task reaper after 40 minutes with nothing written and
was re-run in the foreground). Parse 1.000 in every cell, mean |plan| 4.00,
all cells valid. `results/e29_gemma4-e4b_o*.csv/.json`,
`results/e29_gemma4-e4b_summary.json`.

| design | restated | neutral | Δ | 95 % CI | DiD vs full | 95 % CI |
|---|---|---|---|---|---|---|
| full | 0.125 | 0.135 | −0.010 | [−0.094, +0.062] | reference | |
| delete | 0.979 | 0.490 | +0.490 | [+0.385, +0.583] | **+0.500** | [+0.375, +0.625] |
| addonly | 0.000 | 0.000 | +0.000 | [+0.000, +0.000] | +0.010 | [−0.062, +0.094] |
| wiki | 0.000 | 0.000 | +0.000 | [+0.000, +0.000] | +0.010 | [−0.062, +0.094] |

**Verdict by the declared rule: DESIGN-DEPENDENT, delete DiD +0.500.** P1
and P2 hold with the largest Δ_delete of any decider (+0.490). P3 holds:
Δ_full is −0.010, not significant. P4 holds (DiD_addonly +0.010). P5 holds
(wiki = addonly = 0.000 exactly). P6 holds: under `delete`/neutral the
rejected step's inclusion (0.490) is within 0.10 of that cell's `never` rate
(0.500). This decider never enacts a step whose rejection it can see, in 384
add-only and wiki cells, and enacts a step whose rejection was deleted at
the never-mentioned rate until the restatement arrives, after which it
enacts it almost always. The design dependence is absolute on this model:
the rejected step comes back through write-time delete and through nothing
else.

**Standing after four deciders.** DESIGN-DEPENDENT on every decider run
(3B, 7B, 14B, and a third family at ~4B effective), carried each time by
`delete` (DiD +0.438, +0.375, +0.208, +0.500), with add-only inside the band
every time (+0.094, +0.042, −0.052, +0.010) and wiki positive on the two
small deciders and flat on the two larger ones. The residual claim in §0.5
stands as stated there; nothing in the addendum widens it.
