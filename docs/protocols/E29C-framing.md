# E29-C — the negative full-context restatement effect: framing, or any late mention?

Declared 2026-09-11 with **zero outcomes**. A follow-up on a secondary
observation inside E29 (`docs/protocols/E29-memory-semantics.md`); not a
novelty candidate, does not enter the ledger, and changes nothing in E29's
verdict either way.

## 0. What is being followed up

E29's P3 predicted that Δ_full — the restatement effect when the decider reads
the whole transcript — would be *small*, because the rejection is visible in
both arms. It was small but **negative on both deciders with intervals that
exclude zero**: the proposer's "For the record, I did raise X earlier in this
discussion" *lowered* enactment of the rejected step X.

| decider | full / restated | full / neutral | Δ_full | 95 % CI |
|---|---|---|---|---|
| `llama3.2:3b` | 0.198 | 0.281 | −0.083 | [−0.167, −0.010] |
| `qwen2.5:7b-instruct` | 0.240 | 0.312 | −0.073 | [−0.146, −0.010] |

Two readings were left open in RESUME. **H-frame**: the sentence is a dispute
about authorship ("I did raise it"), not a request to do X, and it sends the
decider back to the exchange where X was rejected. **H-mention**: any late
mention of a rejected step in a full transcript makes the rejection salient
again, whatever the framing. They predict different things for a plain
mention.

## 1. Design — E29 plus one pair of arms, `full` only

Corpus `lineage_e29c.py`, hash `979143b67049adf2`, pinned in
`e29c_framing.py`. The same 96 E16 dialogues with a rejected slot, the same
speaker (the original proposer), the same slot and tail rule as E29. Four arms;
every line is ten words plus the referent, and the neutral referent has the
action phrase's word count (`NEUTRAL_BY_WORDS`, unchanged):

| arm | line | E29 |
|---|---|---|
| `restated` | For the record, I did raise {action phrase} earlier in this discussion. | byte-identical |
| `neutral` | For the record, I did raise {neutral referent} earlier in this discussion. | byte-identical |
| `plain` | Just to note it, {action phrase} came up earlier in this discussion. | new |
| `plain_neutral` | Just to note it, {neutral referent} came up earlier in this discussion. | new |

The plain line claims no authorship, asks for nothing and carries no "for the
record" register; it differs from `restated` only in framing, and from
`plain_neutral` only in the referent. `test_lineage_e29c.py` asserts the
byte-identity of the two E29 arms, the one-line difference between every pair,
same speaker, same word count, and the tags.

Decider prompt, temperature, client, validator and row format are E29's
(`e29c_framing.py` imports them). Design `full` only: the question is about a
decider reading a transcript, not about a store. Both E29 deciders, the course
model first. The `restated` and `neutral` cells are **re-run**, not copied from
E29, so the replication and the new pair come from the same session.

**Allocation.** 96 × 4 = **384 scheduled calls per decider**, two chunks of
48 dialogues (`--offset 0 --limit 48`, `--offset 48`), each writing
`results/e29c_<model>_o<offset>.csv/.json`. Parse retries per `ask_structured`
and transport retries per `RetryingOllamaClient`, recorded per row.

## 2. Estimands and predictions, fixed before the first call

    Δ_ftr   = P(rejected step in plan | restated) − P(… | neutral)
    Δ_plain = P(… | plain) − P(… | plain_neutral)
    Diff    = Δ_ftr − Δ_plain

- **P1 (replication).** Δ_ftr < 0 with an interval excluding 0 on
  `llama3.2:3b`, near E29's −0.083. If it does not replicate, the question is
  moot and is reported as such.
- **P2 (the question).** H-frame predicts Δ_plain ≈ 0 and Diff < 0. H-mention
  predicts Δ_plain ≈ Δ_ftr < 0 and Diff ≈ 0. No prior is placed on which; the
  author's lean is H-frame, recorded so it cannot be claimed afterwards.
- **P3 (control).** The `never` and `accepted` inclusion rates do not differ
  across arms by more than 0.10; the inserted line should only ever act on the
  rejected step.

## 3. Read rule, fixed before the first call

Unit of independence: the dialogue (96). Paired bootstrap over dialogues, seed
0, B = 2000, percentile 95 % intervals. Implemented in `e29c_analysis.py`.

- **NO-REPLICATION** if Δ_ftr's interval includes 0 or Δ_ftr ≥ 0.
- **FRAMING** if Δ_ftr < 0 (interval excludes 0), Δ_plain's interval includes
  0, and Diff's interval excludes 0.
- **ANY-MENTION** if both Δ_ftr and Δ_plain are < 0 with intervals excluding 0
  and Diff's interval includes 0.
- **UNRESOLVED** otherwise; reported as such, never upgraded.

**Validity.** An arm is VOID if parse rate < 0.95 or mean |plan| outside
[3.9, 4.1]; a VOID arm voids the verdict.

**Power, stated.** Half-widths of about 0.08 for a Δ at n = 96 and about 0.11
for Diff. E29's Δ_full (−0.08) sits at the edge of what a single decider can
resolve; the second decider is run for that reason, and the two are reported
side by side, not pooled.

## 4. What cannot follow

Nothing here bears on E29's DiD verdict, which compares designs within an arm
pair that E29-C keeps intact. A FRAMING result says something about how a
full-context decider reads an authorship claim; an ANY-MENTION result says late
mentions of rejected steps are protective under full context. Neither is a
memory-design result and neither is claimed as novel.

## 5. Outcome

_(empty at declaration)_
