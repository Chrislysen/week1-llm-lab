# E29-S — item separation or propositional form? The 2×2 behind the own-record effect

Declared 2026-09-12 with **zero outcomes**. The confound-removal leg for
E29-E, and the experiment this programme's strongest claim actually rests on.

## 0. What E29-E established and what it conflated

E29-E held an add-only store fixed and varied how the rejection of the
rejected proposal was written. Two results:

- **Wording does not matter.** Re-writing the rejection from a proposition to
  a key-value assertion, in the same position on its own line, moved
  enactment by +0.052, −0.115 and −0.031 on the 3B, 7B and 14B deciders. No
  consistent direction, never reaching the threshold.
- **Collapsing it onto the proposal does matter.** +0.385, +0.219, +0.292,
  every interval excluding zero.

But the collapse changed **two things at once**: the negation stopped being a
separate list item *and* stopped being a proposition with a verb. E29-E's
write-up calls the survivor "the own-record effect", which names one of the
two without having separated them. This leg separates them.

## 1. Design — the 2×2, over the same add-only fact stream

Corpus: the E29 corpus (hash `187a426616f26598`), 96 dialogues, both arms.
Prompt, temperature, validator, validity rule, **pinned `pin4` plan**: E29's.
Only the store's structure varies.

| | **own item** | **same item as the proposal** |
|---|---|---|
| **proposition** | `addonly` — "- A proposed to X." / "- B rejected the proposal to X; it is not needed for this case." | `addonly_merged` — **NEW** — "- A proposed to X. B rejected the proposal to X; it is not needed for this case." |
| **attribute** | `addonly_meta` — "- status(X) = WITHDRAWN; it is not needed for this case." | `addonly_flag` — "- [withdrawn] A proposed to X." |

**The critical property.** `addonly` and `addonly_merged` contain
**byte-identical text**. The entire manipulation is that one `"\n- "` becomes
`" "`, so two propositions share a bullet instead of occupying two. No word
is added, removed or changed anywhere in either store. A test asserts that
the two stores are identical after whitespace is stripped, and that the
merged store has exactly one bullet fewer.

Deciders: `llama3.2:3b` and `qwen2.5:14b-instruct`, the extremes of the
range. 96 × 2 × 4 = **768 calls per decider**, run resumably with per-dialogue
checkpoints into `results/e29s_<model>_r*.csv/.json`. The block hash `f25719fc5d4a268c` is
pinned in `e29s_structure.py`.

## 2. Estimands and predictions, fixed before the first call

All four contrasts are taken in the **neutral** arm, where every store
contains the rejection and no restatement is present:

    S_merge     = P(addonly_merged) − P(addonly)        separation, proposition held
    S_flag      = P(addonly_flag)   − P(addonly_meta)   separation, attribute held
    S_form_own  = P(addonly_meta)   − P(addonly)        form, own item held
    S_form_same = P(addonly_flag)   − P(addonly_merged) form, same item held

- **P1.** S_form_own is small: this is E29-E's null, re-measured in-session,
  and must reproduce within 0.10 of +0.052 (3B) and −0.031 (14B).
- **P2.** Δ_addonly reproduces E29's add-only restatement effect within 0.10.
- **P3, the question.** No directional prediction is fixed, because the two
  live hypotheses make opposite ones and the author's leans in this
  programme have been wrong four times out of five. **The author's lean,
  recorded so it cannot be claimed afterwards: S_merge is small — a
  proposition with a verb keeps working even when it shares a bullet — so the
  verdict will be FORM or INTERACTION rather than SEPARATION.**
- **P4 (control).** `never` and `accepted` inclusion within 0.10 across the
  four designs per arm.

## 3. Read rule, fixed before the first call

Paired bootstrap over dialogues, seed 0, B = 2000, percentile 95 % intervals,
in `e29s_analysis.py`. A cell is VOID on parse < 0.95 or mean |plan| outside
[3.9, 4.1].

- **SEPARATION** if both S_merge and S_flag ≥ 0.15 with intervals excluding 0,
  and neither form contrast does.
- **FORM** if both form contrasts ≥ 0.15 with intervals excluding 0, and
  neither separation contrast does.
- **INTERACTION** if at least one of each reaches the threshold.
- **NULL** if none does. **PARTIAL** otherwise. Never upgraded.

## 4. Why this matters beyond memory systems

If SEPARATION holds, the finding is that a model's response to a negation
depends on whether it occupies its own item in a list, with the text held
byte-identical. That is a claim about how context is parsed, not about memory
architecture, and it would apply to retrieved chunks, tool results and policy
lists as much as to a memory store. If FORM holds, the finding is that the
negation must be a proposition with a verb, and a key-value attribute is
under-weighted wherever it sits — also a claim about context, and also
general. Either way the result stops being about Mem0 and starts being about
how these models read a structured prompt.

**What still cannot follow.** Two deciders, one corpus, oracle stores, one
list format (markdown bullets). A finding here would need replication across
formats (JSON, XML, numbered) before any general claim about context
structure is made, and that replication is named here as the obvious next
step rather than assumed.

## 5. Outcome

_(empty at declaration)_
