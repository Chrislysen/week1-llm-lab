# E29-D — the Mem0 write path, run for real, with an extractor that stores operational proposals

Declared 2026-09-12 (just after midnight) with **zero outcomes**. The stage E29-B could
not deliver: E29-B ran the Mem0 paper's own `FACT_RETRIEVAL_PROMPT` and found
that a personal-information extractor does not store operational proposals
(the store mentioned the proposed step after its proposal line in 2 of 18
dialogues), so its declared manipulation check failed and it stopped,
UNINFORMATIVE. Not a novelty candidate on its own; it is the real-system leg
of E29 (`docs/protocols/E29-memory-semantics.md`).

## 0. What changes, and what does not

**Changed: the extraction prompt only.** `OPS_FACT_PROMPT` in
`e29d_ops_extractor.py`, committed with this declaration, is written in the
same form as Mem0's (`{"facts": [...]}` JSON, few-shot examples, "latest
exchange only") but asks for operational facts: steps proposed and by whom,
decisions on steps (accepted / rejected, resolved against the step named in
the previous message), references back to earlier steps, other operational
context. Its examples use a domain (a CDN rollout) and wordings that appear
nowhere in the corpus, so the extractor is not shown the corpus's templates.

**Unchanged: everything else.** The update router is Mem0's
`DEFAULT_UPDATE_MEMORY_PROMPT` verbatim via `get_update_memory_messages`,
with the whole live store as old memories, events applied as Mem0 applies
them (`Mem0WritePath.update`, reused from `e29b_real_extractor.py`). The 48
dialogues are E29-B's declared subset (every second E29 dialogue). The common
prefix is processed once and forked. Store snapshots are kept after every
line. The decider reads the final store rendered exactly as E29's `delete`
design rendered its oracle store, with E29's prompt, `pin4`, temperature 0.
"Mentions" is E29-B's keyword rule.

**Models.** Extractor and router: `qwen2.5:7b-instruct` (E29-B used the 3B
model for both write steps; the 7B model is chosen for extraction reliability
and is declared, not tuned). Decider: `llama3.2:3b`, the course model, so
Δ_real compares with E29's oracle `delete` cells on the same 48 dialogues and
the same decider. A second decider is not planned in this stage.

**Deviations from Mem0, stated (as in E29-B):** temperature 0 for both write
steps (OSS default 0.1); no embedding retrieval, the whole store is shown; one
line per `add()`; one extractor model.

## 1. Questions

- **W0 (manipulation check).** Does the store mention the proposed step after
  its proposal line? Required ≥ 0.5 of dialogues, or the stage is
  UNINFORMATIVE, as in E29-B.
- **W1.** Given the step is in the store, does the rejection line remove it
  (Mem0's DELETE rule), or does the router keep it and add the rejection?
- **W2.** Does the final store mention the rejected step more often in the
  restated arm than in the neutral arm?
- **D.** On the real store, does the decider's enactment move with the
  restatement (Δ_real), and where does it sit relative to E29's oracle
  Δ_delete (+0.354 on all 96; recomputed on these 48) and E29's Δ_addonly?

## 2. Predictions, fixed before the first call

- **P0.** W0 ≥ 0.5: an extractor asked for operational facts stores them. If
  this fails the stage is UNINFORMATIVE and the extractor prompt, not
  supersession, is what was measured.
- **P1.** The router under-deletes: W1 < 0.5 (arXiv:2606.15903 App. P; Mem0's
  own v3 rationale for dropping the router). Most rejections will land as ADD
  or UPDATE, not DELETE.
- **P2.** Because of P1 the real store behaves between E29's `addonly` and
  `delete`: 0 ≤ Δ_real < oracle Δ_delete on the same dialogues.
- **P3.** W2 is higher in the restated arm than in the neutral arm regardless
  of W1: the restatement enters as a fresh fact, as E29-B saw (0.39 vs 0.22).

## 3. Read rule, fixed before the first call

Paired bootstrap over dialogues, seed 0, B = 2000, percentile 95 % intervals,
in `e29d_analysis.py`. Unit: the dialogue (48).

- **UNINFORMATIVE** if W0 < 0.5.
- **REAL-STORE EFFECT** if Δ_real ≥ 0.15 with the interval above 0.
- **NULL** if |Δ_real| < 0.05 with the interval inside ±0.15.
- **PARTIAL** otherwise; reported as such.

W1 and W2 are descriptive, reported with denominators. Validity as in E29
(decider parse ≥ 0.95, mean |plan| in [3.9, 4.1]); malformed extractor or
router outputs are counted per dialogue and reported, and treated as no-ops
as in E29-B.

**Allocation.** At most 2 write calls per line plus 1 decider call per arm:
about 24 calls per dialogue, **about 1,150 scheduled calls**, chunked 6
dialogues at a time (`--offset k --limit 6`), each chunk writing
`results/e29d_<extractor>_<decider>_o<offset>.csv/.json`. Transport retries
per the client; parse retries only for the decider.

## 4. What cannot follow

Nothing about the Mem0 product as shipped (no vector store, no embedder, one
temperature). One extractor prompt of the author's, so a REAL-STORE EFFECT
here is "a Mem0-router store fed by an operational extractor", not "Mem0". The
keyword mention rule undercounts paraphrases. 48 dialogues, one corpus.

## 5. Outcome — run 2026-09-12, after `8bce1ae`

48 of 48 dialogues in eight foreground chunks of six (about 6–7 minutes
each), extractor and router `qwen2.5:7b-instruct`, decider `llama3.2:3b`.
Zero malformed extractor outputs, zero malformed router outputs, zero
transport retries. Decider parse 1.000 in both arms, mean |plan| 4.00.
`results/e29d_qwen25-7b-instruct_llama32-3b_o{0,6,…,42}.csv/.json` (every
store snapshot, every router event, every decider prompt and output),
`results/e29d_qwen25-7b-instruct_llama32-3b_summary.json`.

| question | value | prediction | verdict |
|---|---|---|---|
| **W0** store mentions the step after its proposal line | **0.958** of 48 | ≥ 0.5 | **P0 holds; stage informative** |
| **W1** rejection removed the step, given it was there | **0.217** (n = 46) | < 0.5 | **P1 holds** |
| **W2** final store mentions the rejected step | restated **0.854** · neutral **0.750** | restated > neutral | **P3 holds** |
| router events per dialogue (ADD / UPDATE / DELETE) | restated 6.54 / 3.81 / 0.35 · neutral 6.62 / 2.92 / 0.35; store size 6.2 | — | — |
| **D** rejected-step inclusion on the real store | restated **0.667** · neutral **0.500** · Δ_real **+0.167 [+0.042, +0.292]** | 0 ≤ Δ_real < oracle Δ_delete | **P2 holds** |
| E29 oracle `delete`, same 48 dialogues, same decider | 0.958 · 0.562 · +0.396 | | |
| E29 oracle `addonly`, same 48 | 0.208 · 0.167 · +0.042 | | |
| E29 oracle `full`, same 48 | 0.083 · 0.208 · −0.125 | | |

**Verdict by the declared rule: REAL-STORE EFFECT** (Δ_real ≥ 0.15, interval
above 0).

**What the real write path did.** Asked for operational facts, the extractor
stored the proposed step almost always; the manipulation check that E29-B
failed at 0.11 passes at 0.96 with a prompt change and nothing else. Mem0's
router then behaved as arXiv:2606.15903 App. P and Mem0's own v3 rationale
say it does: on the rejection line it DELETEd the proposal in about one
dialogue in five and otherwise ADDed the rejection or UPDATEd the proposal's
text to carry it. The rejected step therefore survived in three quarters of
neutral-arm stores, and the restatement pushed that to 0.85 by entering as a
fresh fact.

**Where the real store sits.** On enactment it lands between the two oracle
designs, as predicted: +0.167 against +0.042 (add-only) and +0.396 (delete).
One observation beyond the predictions: the neutral-arm enactment on the real
store (0.500) is far above the oracle add-only cell (0.167) although the
rejection is usually present in both. The oracle store renders the rejection
by a fixed template; the router's UPDATEs rewrite the proposal's text to fold
the rejection in ("… proposed X; … said it is not needed"), and the 3B decider
reads such merged lines as weaker than a separate rejection. Whether that is
the rewrite or the wording is not tested here.

**What this adds to E29.** E29's DiD was measured on semantic ideals. This
stage shows that a real Mem0-router store fed by a fit-for-purpose extractor
re-admits a dialogue-rejected step when a partner restates it, by an amount
that is smaller than the hard-delete ideal and larger than add-only, and that
the mechanism is the one E29 named: the restatement enters the store as a
fact with no rejection attached. Limits as declared: one extractor prompt of
the author's, one extractor model, one decider, no embedder or vector store,
48 dialogues of one corpus, a keyword mention rule.
