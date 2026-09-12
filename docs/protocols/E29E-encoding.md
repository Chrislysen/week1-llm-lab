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

## 5. Outcome — run 2026-09-12, after `687c138`

576 calls per decider (3B and 7B in four chunks of 24, 14B in six of 16),
1,728 calls in total. Parse 1.000 in every cell, mean |plan| 3.96–4.00, no
VOID cell, zero transport retries.
`results/e29e_<model>_o*.csv/.json`, `results/e29e_<model>_summary.json`.

Rejected-step inclusion, n = 96 dialogues per cell.

| decider | design | restated | neutral | Δ | 95 % CI | DiD vs add-only | 95 % CI |
|---|---|---|---|---|---|---|---|
| `llama3.2:3b` | addonly | 0.177 | 0.156 | +0.021 | [−0.052, +0.094] | reference | |
| | addonly_meta | 0.146 | 0.208 | −0.062 | [−0.125, −0.010] | −0.083 | [−0.187, +0.021] |
| | addonly_flag | 0.615 | 0.594 | +0.021 | [−0.052, +0.094] | +0.000 | [−0.094, +0.104] |
| `qwen2.5:7b-instruct` | addonly | 0.323 | 0.354 | −0.031 | [−0.104, +0.042] | reference | |
| | addonly_meta | 0.198 | 0.240 | −0.042 | [−0.104, +0.010] | −0.010 | [−0.104, +0.083] |
| | addonly_flag | 0.469 | 0.458 | +0.010 | [−0.062, +0.073] | +0.042 | [−0.042, +0.135] |
| `qwen2.5:14b-instruct` | addonly | 0.042 | 0.062 | −0.021 | [−0.062, +0.021] | reference | |
| | addonly_meta | 0.031 | 0.031 | +0.000 | [+0.000, +0.000] | +0.021 | [−0.021, +0.062] |
| | addonly_flag | 0.562 | 0.323 | **+0.240** | [+0.156, +0.333] | **+0.260** | [+0.167, +0.354] |

Encoding contrasts in the **neutral** arm, where all three stores contain the
rejection and no restatement is present:

| decider | G_meta (metadata vs prose, same line and position) | G_flag (prefix vs its own prose line) | G_fm (the extra line alone) | verdict by the declared rule |
|---|---|---|---|---|
| `llama3.2:3b` | +0.052 [−0.042, +0.146] | +0.438 [+0.333, +0.542] | **+0.385** [+0.281, +0.500] | PARTIAL |
| `qwen2.5:7b-instruct` | −0.115 [−0.198, −0.031] | +0.104 [+0.010, +0.198] | **+0.219** [+0.135, +0.302] | PARTIAL |
| `qwen2.5:14b-instruct` | −0.031 [−0.073, +0.010] | +0.260 [+0.167, +0.354] | **+0.292** [+0.198, +0.385] | **LENGTH** |

**P1 fails on all three, and it was the reason the leg was run.** The
prediction was that re-wording the rejection from a verb phrase to a
key-value assertion would raise enactment by at least 0.15. It does not move
it on the 3B (+0.052, interval spanning 0) or the 14B (−0.031, spanning 0),
and on the 7B it moves it in the *opposite* direction (−0.115, interval
excluding 0: the key-value line is more protective than the sentence). There
is no consistent wording effect. The encoding hypothesis as stated in the
E29-X write-up is **withdrawn**.

**What replaces it, and it is the same quantity on every decider.** G_fm —
the contrast that holds the wording metadata-like and changes only whether
the negation occupies its own line — is positive and excludes zero on all
three: +0.385, +0.219, +0.292. So does G_flag, the contrast against the prose
line: +0.438, +0.104, +0.260. **The negation has to be its own record.** Once
the same invalidation rides as a prefix on the record it invalidates, the step
is enacted at 0.59, 0.46 and 0.32 against 0.16, 0.35 and 0.06 for the store
that spends a separate line on it. P2 (G_flag ≥ G_meta) holds on all three.

**The restatement effect returns with the prefix encoding, on the largest
decider.** Add-only on the 14B is the most immune cell in the whole
programme: 0.062 neutral, 0.042 restated, Δ −0.021. Change nothing except
moving the rejection onto the proposal line as a prefix, and the same store
gives 0.323 / 0.562 with Δ +0.240 [+0.156, +0.333] and DiD +0.260 [+0.167,
+0.354]. That reproduces E29-T's tombstone reading (DiD +0.292) with the
line-count confound removed, and it locates the mechanism precisely: a
decider that fully honours a rejection written as its own proposition stops
honouring it when the identical content becomes an attribute of the thing it
negates, and a partner's restatement then re-admits the step.

**P3 holds: a fourth replication.** Δ_addonly is +0.021, −0.031, −0.021
against E29's +0.010, −0.031, +0.000 — within 0.03 on every decider, on
byte-identical prompts run in a separate session.

**P4 fails on two deciders and is reported.** Never-mentioned inclusion across
the three designs within an arm spreads 0.146 and 0.188 on the 3B (restated,
neutral) and 0.125 on the 14B restated arm, against the declared 0.10; the 7B
is within tolerance at 0.042 and 0.084. The `addonly_flag` cells carry the
lowest never rates wherever the spread is largest, which is displacement in a
pinned four-step plan: the zombie step takes a slot a never-mentioned step
would otherwise have filled. Accepted-step inclusion is 0.983–1.000
everywhere.

**Standing.** Two of three deciders read PARTIAL by the declared rule and one
reads LENGTH; none reads ENCODING. The rule is not upgraded. The cross-decider
observation — G_fm positive with an interval excluding zero on all three — is
reported as an observation, which is what it is, and it is the finding this
leg contributes. Its deployment reading is direct and uncomfortable: the
soft-delete designs surveyed in §0 of the parent protocol, and the five
shipped systems measured in arXiv:2609.08258, all encode revocation as an
attribute of the record being revoked — a validity interval, an `invalid_at`
edge, an `is_active` flag. On this evidence that is the encoding a small
decider is least likely to honour.
