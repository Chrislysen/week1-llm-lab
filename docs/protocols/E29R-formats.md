# E29-R — is the structural result about item structure, or about markdown?

Declared 2026-09-29 with **zero outcomes**, after the prior-art gate
(`docs/protocols/E29R-gate.md`: candidate for testing, residual narrow).
This is the replication the 2026-09-12 proposal for reframing the paper
named as the highest-value next run.

## 0. What E29-S found, and the one thing it could not say

E29-S (`21cff6d`) put the rejection of a proposal into four structures in an
add-only memory and read how often the rejected step still entered the plan
(neutral arm):

| llama3.2:3b | own item | same item | | qwen2.5:14b | own item | same item |
|---|---|---|---|---|---|---|
| proposition | 0.156 | 0.094 | | proposition | 0.052 | 0.042 |
| attribute | 0.198 | **0.594** | | attribute | 0.031 | **0.323** |

The failure lives in one cell: the rejection written as a verb-less tag on
the record it rejects (`- [withdrawn] A proposed to X.`). But every store was
a **markdown bullet list**. That cannot distinguish "a subordinate, verb-less
negation is under-weighted" from "a bracketed prefix on a markdown bullet is
under-weighted".

## 1. Design

The four stores are **E29-S's own** (`lineage_e29s.store_s`), item for item
and character for character. Only the list container changes
(`lineage_e29r.render`):

| format | container |
|---|---|
| markdown | `- item` (E29-S's data, **not re-run**) |
| json | `{"notes": ["item", …]}`, indent 2 |
| xml | `<notes>` / `  <note>item</note>` / `</notes>`, XML-escaped |
| numbered | `1. item` |

The header, system prompt, plan instruction, pinned four-step plan
(`pin4`), temperature, validator and the 512-token runaway guard are all
E29-S's. Zero-call tests (`test_lineage_e29r.py`) assert:
- every rendering parses back to exactly E29-S's items;
- the markdown rendering is byte-identical to the block E29-S sent;
- the merged store has exactly one item fewer in every format.

Corpus: E29, 96 dialogues, both arms (the structural contrasts use the
neutral arm; the restated arm is kept for the restatement effect, as in
E29-S). Deciders: `llama3.2:3b` and `qwen2.5:14b-instruct`, E29-S's two.
3 formats × 4 designs × 2 arms × 96 = **2,304 calls per decider**, checkpointed
per dialogue into `results/e29r_<model>_r*.csv/.json`. The prompt block hash
`8a9412801fc2bae1` is pinned in `e29r_formats.py`.

## 2. Predictions, fixed before the first call

- **P1 (validity).** Every cell has parse ≥ 0.95 and mean |plan| in
  [3.9, 4.1]. Otherwise the cell is VOID, and a format with a VOID cell cannot
  count as a conjunction.
- **P2 (control).** In every format, never-mentioned and accepted-step
  inclusion (neutral arm) stay within 0.10 across the four designs.
- **P3 (the question).** No directional prediction is part of the rule.
  **Author's lean, recorded so it cannot be claimed afterwards: GENERAL on
  both deciders, with the smallest separation in JSON**, where quoted strings
  make every item boundary explicit.

## 3. Read rule, fixed before the first call (`e29r_analysis.py`)

Per decider and format: E29-S's four contrasts on the neutral arm, with a
paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %
intervals). A contrast **reaches** when it is ≥ 0.15 and its interval
excludes zero.

- **CONJUNCTION** holds in a format when S_flag and S_form_same both reach,
  and neither S_merge nor S_form_own does. This is the E29-S pattern, and the
  rule classifies E29-S's markdown data as CONJUNCTION on both deciders.

Per decider:

| verdict | meaning |
|---|---|
| **GENERAL** | CONJUNCTION in all three new formats |
| **FORMAT-DEPENDENT** | CONJUNCTION in one or two |
| **MARKDOWN-SPECIFIC** | CONJUNCTION in none |

Never upgraded after the fact. What each outcome licenses:
- **GENERAL on both deciders:** the structural claim is about item structure,
  and the paper leads with it.
- **FORMAT-DEPENDENT:** the claim is narrowed to the formats where it holds.
- **MARKDOWN-SPECIFIC on both:** the claim is withdrawn as a structural claim,
  and the programme stops here.

## 4. What cannot follow, whatever the outcome

Two deciders ≤ 14B, one synthetic corpus, oracle stores, one tag spelling
(`[withdrawn]`). A GENERAL result says the E29-S pattern survives four list
containers on two open models. It says nothing about frontier models, about
retrieval, or about other tag vocabularies (`is_active: false`,
`invalid_at`). Those are named as the next gaps, not assumed.
