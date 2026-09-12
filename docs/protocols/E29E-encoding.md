# E29-E — does the *encoding* of a rejection decide whether the step comes back?

Declared 2026-09-12 with **zero outcomes**. A confound-removal leg of E29
(`docs/protocols/E29-memory-semantics.md`). Not a novelty candidate on its
own, and it is declared in the knowledge that the closest published result,
arXiv:2609.08258 (2026-09-08), already shows that a flagged revocation is not
enforced on shipped systems; what that paper cannot separate, and this can, is
the wording from the length.

## 0. Why

E29-X compared add-only (the rejection stored as a sentence) with a tombstone
store (the rejection stored as a `[withdrawn]` prefix) and found neutral-arm
enactment of 0.177 / 0.344 / 0.062 against 0.625 / 0.421 / 0.292 on the 3B,
7B and 14B deciders. The tempting reading is that the *encoding* decides. The
comparison does not support it: add-only holds 8.28 store lines on average and
the tombstone store 6.66, because add-only also keeps each acceptance as its
own fact. The gap could be the wording, the length, or the merged
acceptances. This leg removes all three alternatives but one at a time.

## 1. Design — three add-only stores, one difference each

Corpus: the E29 corpus (hash `187a426616f26598`), 96 dialogues, both arms,
unchanged. Prompt, temperature, validator, validity rule: E29's. All three
designs are add-only stores over the same oracle fact stream with the same
header; every line other than the rejection is byte-identical across them.

| design | how the rejection of the rejected proposal is written | lines |
|---|---|---|
| `addonly` | as a sentence, exactly as E29 stored it: "{B} rejected the proposal to {phrase}; it is not needed for this case." | *n* |
| `addonly_meta` | as a key-value assertion in the same position with the same trailing clause: "status({phrase}) = WITHDRAWN; it is not needed for this case." | *n* |
| `addonly_flag` | the line removed; the proposal it negates prefixed "[withdrawn] " | *n* − 1 |

`addonly` vs `addonly_meta` changes the wording and nothing else: same line
count, same position, same justification clause. `addonly_meta` vs
`addonly_flag` changes only whether the negation occupies its own line.
`addonly` is byte-identical to E29's add-only store, asserted by test.

Deciders: `llama3.2:3b`, `qwen2.5:7b-instruct`, `qwen2.5:14b-instruct`.
Tests in `test_lineage_e29e.py`; the block hash `1cdd60a9a4ad61c1` is pinned in
`e29e_encoding.py`.

**Allocation.** 96 × 2 × 3 = **576 calls per decider**, chunked at 24
dialogues for the 3B and 7B and 16 for the 14B, into
`results/e29e_<model>_o<offset>.csv/.json`. Read with `e29e_analysis.py`.

## 2. Estimands and predictions, fixed before the first call

In the **neutral** arm, where all three stores contain the rejection and no
restatement is present:

    G_meta = P(step in plan | neutral, addonly_meta) − P(… | neutral, addonly)
    G_flag = P(… | neutral, addonly_flag) − P(… | neutral, addonly)
    G_fm   = P(… | neutral, addonly_flag) − P(… | neutral, addonly_meta)

and, for continuity, Δ_X and DiD_X against the same-session `addonly`.

- **P1.** G_meta ≥ 0.15 with an interval excluding 0 on at least one decider.
  This is the author's lean and the reason the leg is run: a small decider
  reads "rejected the proposal to X" as an instruction and
  "status(X) = WITHDRAWN" as a field it may ignore.
- **P2.** G_flag ≥ G_meta: removing the line as well should not protect more
  than re-wording it.
- **P3.** Δ_addonly reproduces E29's add-only Δ (+0.010, −0.031, +0.000 on the
  three deciders) within 0.10, since the cells are the same prompts.
- **P4 (control).** `never` and `accepted` inclusion within 0.10 across the
  three designs per arm.

## 3. Read rule, fixed before the first call

Paired bootstrap over dialogues, seed 0, B = 2000, percentile 95 % intervals,
in `e29e_analysis.py`. A design is VOID if parse < 0.95 or mean |plan| outside
[3.9, 4.1]; any VOID cell voids that decider.

- **ENCODING** if G_meta ≥ 0.15 with an interval excluding 0.
- **LENGTH** if |G_meta| < 0.05 with its interval inside ±0.15 *and*
  G_flag ≥ 0.15 with an interval excluding 0.
- **NULL** if both |G_meta| and |G_flag| < 0.05 with intervals inside ±0.15 —
  in which case the E29-X gap was the merged acceptances or the cross-session
  difference, and the encoding hypothesis is withdrawn.
- **PARTIAL** otherwise; reported as such, never upgraded.

## 4. What cannot follow

Three oracle stores on one corpus with three local deciders. A result here is
about how a decider reads a rejection it has been handed, not about any
shipped system's retrieval; arXiv:2609.08258 owns the shipped-system claim. An
ENCODING verdict would say that the negation must be written as a proposition
for a small decider to act on it, which is a claim about prompt semantics with
a direct deployment reading, not a claim about memory architecture. It does
not widen the E29 residual.

## 5. Outcome

_(empty at declaration)_
