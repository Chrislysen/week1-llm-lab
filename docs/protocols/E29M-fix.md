# E29-M: does rendering the revocation field as a sentence fix it?

Declared 2026-09-30 with **zero outcomes**. E29-T's results (MOST-FAIL on both
deciders) and E29-K's llama3.2:3b read (READ-NOT-USED) were known when this was
written, and it builds on them. An independent methods review of this declaration
was applied before the first call.

## 0. Why

E29-T showed that the fields deployed memory systems use to mark a revoked record,
`[is_active: false]` and `[invalid_at: ...]`, leave the rejected step in the plan at
0.73–0.91, while the same rejection written as its own sentence gives 0.06–0.16.
If the structure of the rejection is what fails, a system should be able to fix it at
read time, without changing how it stores records: when it renders a revoked record
into the prompt, write the revocation as a sentence. This tests that fix directly.
It is an applied check on this setup, not a novelty claim; rendering structured
records as text is common practice.

## 1. Design (`lineage_e29m.py`, `e29m_fix.py`)

E29-T's setup unchanged: the add-only fact stream, markdown list, system prompt, plan
instruction, pinned four-step plan, temperature 0, validator and runaway guard, neutral
arm, 96 dialogues. Six cells:

| cell | the rejected proposal's rendering |
|---|---|
| `sentence` (control) | E29-T's control, byte for byte: `- A proposed to X.` then `- B rejected the proposal to X; it is not needed for this case.` |
| `is_active_false` (anchor) | E29-T's cell, byte for byte: `- A proposed to X. [is_active: false]` |
| `invalid_at` (anchor) | E29-T's cell, byte for byte: `- A proposed to X. [invalid_at: 2026-09-12 10:04]` |
| `rewrite` (the fix) | `- A proposed to X.` then `- The proposal to X was withdrawn.` (field removed) |
| `annotate_is_active` | `- A proposed to X. [is_active: false]` then `- The proposal to X was withdrawn.` |
| `annotate_invalid_at` | `- A proposed to X. [invalid_at: …]` then `- The proposal to X was withdrawn.` |

The rewrite produces the same store whichever field it starts from, so one `rewrite`
cell is read against both anchors. In all 96 dialogues, in both arms, the control's
rejection item directly follows the proposal, so the `rewrite` store is the `sentence`
store with one item re-worded in place: same index, same item count. G for the rewrite
(section 3) is therefore a one-item wording contrast that changes four things
together: the rejector is dropped, the reason is dropped, active "rejected" becomes
passive "was withdrawn", and the item is about half as long. A PARTIAL does not
identify which of these matters. E29-E found that re-wording a rejection within its own
item moved inclusion by at most 0.115, which is the basis for the lean below.

The fix's sentence names no one and gives no reason, but it restates the proposal's
action. A system can do that only if it can parse the record as a proposal (here, a
regex on the `A proposed to X.` template), and it drops `invalid_at`'s timestamp. A
record-agnostic sentence such as `(This note is no longer active.)` is not tested.

Zero-call tests (`test_lineage_e29m.py`) assert:
- the control and both anchors are the prompts E29-T actually sent
  (`results/e29t_*_r0.json`), byte for byte;
- the rewrite is the control with exactly one item re-worded in place;
- the rewrite is identical from either field, removes the field and adds exactly one
  sentence right after the record;
- the annotate cells keep the field and add the same sentence;
- no fixed cell contains the original rejection sentence.

Deciders: llama3.2:3b (Ollama digest `a80c4f17acd5`) and qwen2.5:14b-instruct
(`7cdf5a0187d5`). 6 × 96 = 576 calls per decider, checkpointed per dialogue. Prompt
hash `ecb2edf1dd1f84b9`, pinned in the runner.

## 2. Predictions, fixed before the first call

- **P1 (anchors).** The control and both anchors send E29-T's prompts byte for byte, so
  they reproduce E29-T within 0.10: `sentence` 0.156/0.062, `is_active_false`
  0.906/0.729, `invalid_at` 0.812/0.896 (3B/14B). Every contrast is within-run and
  paired, so a P1 miss is reported and does not void the read.
- **P2 (specificity).** The fix names one proposal, so it should move nothing else:
  accepted inclusion and undecided-proposal inclusion (status `proposed`) stay within
  0.10 across the six cells (E29-T: 0.983–1.000 and 0.933–1.000). Never-mentioned
  inclusion is reported, not predicted: under the pinned plan it takes the rejected
  step's slot. A miss is reported beside the verdict; a FIXED fix cell with a miss is a
  fix with collateral, not a clean fix.
- **P3 (the question).** Author's lean: the rewrite is FIXED on both deciders, the
  annotate cells are PARTIAL, and D says the field COMPETES on both deciders.

## 3. Read rule, fixed before the first call (`e29m_analysis.py`)

Per decider, neutral arm, rejected-step inclusion, complete-case over the six cells,
paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %). Fix rows: the
`rewrite` against each anchor (it is the same store from either field),
`annotate_is_active` against `is_active_false`, and `annotate_invalid_at` against
`invalid_at`. For fix F with anchor A:

- a row is read only if its anchor still fails in this run by E29-T's rule
  (P(A) − P(sentence) ≥ 0.15 with an interval excluding 0); otherwise it is
  **UNTESTABLE**;
- E = P(A) − P(F), how far the fix lowers inclusion from the anchor (an absolute
  difference, not a share; the share E / (P(A) − P(sentence)) is reported as a
  description only);
- G = P(F) − P(sentence), how far the fix stays above the sentence control.

| class | condition |
|---|---|
| **FIXED** | E ≥ 0.15 with an interval excluding 0, and G's upper bound < 0.15 |
| **PARTIAL** | E ≥ 0.15 with an interval excluding 0, and G's upper bound ≥ 0.15 |
| **NOT FIXED** | otherwise |

The headline verdict per decider is the weaker of the two `rewrite` rows. **FIXED on
both deciders** means the read-time rewrite brings the rejected step to within 0.15
(absolute) of the sentence control on this setup. On the 14B, whose control is 0.062,
that margin admits about twice the control's rate (E29-T's `(withdrawn)` suffix was
HONOURED there at 0.135, with G's interval excluding zero). Anything else is reported
as it comes out, including NOT FIXED.

Secondary: for each annotate cell, D = P(annotate) − P(`rewrite`). The two stores
differ only by the field on the proposal, so D is the field's effect with the sentence
present: **COMPETES** if D ≥ 0.15 with an interval excluding 0, **INERT** if its upper
bound < 0.15, **UNCLEAR** otherwise. D does not enter the headline; a claim that the
field competes rests on D, not on the annotate cells' classes.

A decider's read is **VOID** if any cell parses below 0.95 or its mean |plan| is
outside [3.9, 4.1], and **INCOMPLETE** (provisional) while fewer than 96 dialogues
are complete in all six cells.
