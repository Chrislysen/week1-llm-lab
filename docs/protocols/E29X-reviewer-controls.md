# E29-X — two reviewer controls: rendering (E29-R) and a tombstone design (E29-T)

Declared 2026-09-12 with **zero outcomes**. Source of the two controls: the
adversarial review returned by the first Gemini Deep Research scout
(`docs/gemini-research-log/2026-09-12-triage.md` §3, objections 2 and 4).
Not a novelty candidate; a robustness leg of E29
(`docs/protocols/E29-memory-semantics.md`).

## 0. The two objections, in the reviewer's terms

- **Rendering (objection 2).** "The observed difference may be an artefact
  of how the context block is rendered to the decider." E29 already confines
  its read rule to within-design contrasts for this reason and reports levels
  without comparing them. The control that would let levels be compared: show
  the transcript's rejection with the store's explicitness.
- **True by construction against add-only (objection 4).** "A naive add-only
  baseline cannot retract; the result is trivial. A soft-supersede baseline
  with a tombstone flag is the industry mitigation to compare against." E29's
  result runs the other way (add-only protects; delete re-admits), but the
  tombstone design is a real fifth point between them and is worth a
  measurement on its own terms.

## 1. Design

Corpus: the E29 corpus (hash `187a426616f26598`), 96 dialogues, both arms,
unchanged. Deciders: `llama3.2:3b`, `qwen2.5:7b-instruct`,
`qwen2.5:14b-instruct` (gemma4:e4b if time allows). Prompt, temperature,
validator, read rule and validity rule: E29's. Three designs per dialogue,
run in one session so the reference is fresh:

| design | what the decider sees | code |
|---|---|---|
| `full` | E29's transcript, re-run as the same-session reference | `context_block("full")` |
| `full_explicit` (E29-R) | the transcript with every accept/reject reply's bare referent ("that one", "that", "it") replaced by the store's referent "the proposal to {phrase}"; every other character unchanged; header unchanged | `lineage_e29x.explicit_dialogue` |
| `tombstone` (E29-T) | the delete store with the rejected proposal *retained and flagged* "[withdrawn] …" instead of removed; nothing else stored for the rejection; the restatement ADDed fresh; same header as delete / add-only | `lineage_e29x.store_tombstone` |

Tests (`test_lineage_e29x.py`): the explicit rendering changes only reply
lines and names only its own action; the tombstone store equals the delete
store plus exactly one flagged line and contains no rejection fact; headers
match E29's. The hash over every E29-X block, `aa043cc25c027b1a`, is pinned in `e29x_controls.py`.

**Allocation.** 96 × 2 × 3 = **576 calls per decider**, chunked at 32
dialogues (192 calls) for the 3B and 7B deciders and 16 for the 14B, into
`results/e29x_<model>_o<offset>.csv/.json`. Read with `e29x_analysis.py`.

## 2. Predictions, fixed before the first call

- **R1 (rendering).** If E29's level gap between `full` and `addonly` in the
  neutral arm (3B: 0.281 vs 0.177; 7B: 0.312 vs 0.344; 14B: 0.167 vs 0.062)
  was the explicitness of the rejection's referent, `full_explicit`'s neutral
  level will land closer to add-only's than `full`'s does, and below E29's
  `full` neutral level with an interval that excludes it. Read: **RENDERING**
  if both hold, **DESIGN** otherwise. The author's lean: RENDERING on the 3B
  decider, DESIGN on the 14B, where levels are already low.
- **R2.** Δ_full_explicit stays negative or near zero on the small deciders:
  the register effect (E29-C) is about the inserted line, which is untouched.
- **T1 (tombstone).** Δ_tombstone lies between E29's Δ_addonly and Δ_delete
  for the same decider. Read by E29's SESOI on the DiD against the
  same-session `full`: **FLAG NOT HONOURED** (behaves like delete) if
  |DiD| ≥ 0.15 with an interval excluding 0; **FLAG HONOURED** (behaves like
  add-only) if |DiD| < 0.05 with the interval inside ±0.15; **BETWEEN**
  otherwise. Author's lean: NOT HONOURED on the 3B (a bracket is weaker than
  a sentence saying "rejected"), HONOURED on the 14B.
- **T2 (control).** `never` and `accepted` inclusion within 0.10 across the
  three designs per arm.

## 3. What cannot follow

R1 speaks to the *levels* E29 declined to compare; it does not touch E29's
within-design DiD verdicts, which hold rendering constant by construction.
T1 adds a fifth design; whatever it shows, the E29 residual (a partner's
restatement of a dialogue-rejected step re-enters the plan through hard
delete and not through add-only) is neither widened nor narrowed by it. One
corpus, three deciders, oracle stores.

## 4. Outcome

_(empty at declaration)_
