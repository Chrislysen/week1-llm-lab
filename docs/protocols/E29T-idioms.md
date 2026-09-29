# E29-T — do the revocation idioms shipped systems use fail like the tag?

Declared 2026-09-29 with **zero outcomes**, while E29-R was still running and
before any E29-R result for qwen2.5:14b-instruct existed. llama3.2:3b's E29-R
read (GENERAL, `5f40cdc`) was known when this was written, and is disclosed
here.

## 0. Why

E29-S's deployment reading says shipped systems mark revocation "exactly that
way", but it measured one spelling, a `[withdrawn] ` prefix. The systems cited
use other idioms: a status label, a boolean flag, an invalidation timestamp,
strikethrough. If those are honoured, the deployment reading is wrong. This
arm tests it before it is claimed.

## 1. Design (`lineage_e29t.py`)

The E29-S add-only fact stream with the rejection recorded **only** as an idiom
on the rejected proposal's own item. The markdown list, header, system prompt,
plan instruction, pinned four-step plan, temperature, validator and runaway
guard are all E29-S's.

| cell | the rejected proposal's item |
|---|---|
| `sentence` (control, E29-S `addonly`) | `- A proposed to X.` then `- B rejected the proposal to X; …` |
| `withdrawn_prefix` (anchor, E29-S `addonly_flag`) | `- [withdrawn] A proposed to X.` |
| `withdrawn_suffix` | `- A proposed to X. (withdrawn)` |
| `status_revoked` | `- A proposed to X. [status: revoked]` |
| `is_active_false` | `- A proposed to X. [is_active: false]` |
| `invalid_at` | `- A proposed to X. [invalid_at: 2026-09-12 10:04]` |
| `strikethrough` | `- ~~A proposed to X.~~` |

Zero-call tests (`test_lineage_e29t.py`) assert:
- the control and the anchor are E29-S's blocks byte for byte;
- every real-world idiom differs from the anchor's store on exactly one item;
- no idiom cell carries a rejection sentence.

**Neutral arm only**, 96 dialogues. Deciders are llama3.2:3b and
qwen2.5:14b-instruct. That is 7 × 96 = 672 calls per decider, checkpointed per
dialogue. The prompt hash `69c8d207f3993086` is pinned. The run is queued to
start automatically when E29-R's process exits.

## 2. Predictions, fixed before the first call

- **P1 (anchor).** `withdrawn_prefix` reproduces E29-S's tag cell within 0.10
  (0.594 on the 3B, 0.323 on the 14B), and `sentence` reproduces E29-S's
  `addonly` within 0.10 (0.156, 0.052).
- **P2 (control).** Never-mentioned and accepted inclusion stay within 0.10
  across the seven cells. This missed in E29-E, E29-S and E29-R by a
  pinned-plan displacement, and a miss is reported, not explained away.
- **P3 (the question).** No directional prediction is part of the rule.
  **Author's lean: MOST-FAIL on both deciders, with `invalid_at` the most
  ignored (a timestamp says nothing about the step) and `strikethrough` the
  most likely to be honoured (a strong deletion cue in markdown text).**

## 3. Read rule, fixed before the first call (`e29t_analysis.py`)

Per decider, neutral arm: G_i = P(i) − P(sentence), with a paired bootstrap
over dialogues (seed 0, B = 2000, percentile 95 %). A cell is VOID on parse
< 0.95 or mean |plan| outside [3.9, 4.1].

| class | condition |
|---|---|
| **FAILS** | G_i ≥ 0.15 and its interval excludes 0 (ignored like the tag) |
| **HONOURED** | the interval's upper bound < 0.15 |
| **UNCLEAR** | otherwise |

Per decider, over the five real-world idioms: **ALL-FAIL** (5), **MOST-FAIL**
(3–4), **FEW-FAIL** (1–2), **NONE-FAIL** (0). Never upgraded. What each
outcome licenses:
- **ALL/MOST-FAIL on both deciders:** the deployment reading stands for the
  idioms in use.
- **FEW/NONE-FAIL:** the reading is narrowed to bracket-prefix tags, and the
  paper's §3.5 must be rewritten to say so.
