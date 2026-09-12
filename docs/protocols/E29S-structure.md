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

## 5. Outcome — run 2026-09-12/13, after `5165467`

768 calls per decider, 1,536 in total, run resumably with per-dialogue
checkpoints. Parse 1.000 in every cell on both deciders, mean |plan|
3.99–4.00, no VOID cell.
`results/e29s_<model>_r*.csv/.json`, `results/e29s_<model>_summary.json`.

### The 2×2, neutral arm, n = 96 per cell

Rejected-step inclusion. Every store contains the rejection; only its
structure differs.

**`llama3.2:3b`**

| | own item | same item as the proposal |
|---|---|---|
| **proposition** | 0.156 | 0.094 |
| **attribute** | 0.198 | **0.594** |

**`qwen2.5:14b-instruct`**

| | own item | same item as the proposal |
|---|---|---|
| **proposition** | 0.052 | 0.042 |
| **attribute** | 0.031 | **0.323** |

| contrast | what it isolates | `llama3.2:3b` | `qwen2.5:14b-instruct` |
|---|---|---|---|
| S_merge | separation, proposition form held | −0.062 [−0.125, −0.010] | −0.010 [−0.031, +0.000] |
| S_flag | separation, attribute form held | **+0.396** [+0.281, +0.510] | **+0.292** [+0.198, +0.385] |
| S_form_own | form, own item held | +0.042 [−0.052, +0.135] | −0.021 [−0.062, +0.021] |
| S_form_same | form, same item held | **+0.500** [+0.396, +0.604] | **+0.281** [+0.188, +0.375] |

### Verdict by the declared rule: INTERACTION, on both deciders

Neither main effect explains the table. Three of the four cells are
indistinguishable from one another (0.094–0.198 on the 3B, 0.031–0.052 on the
14B); the fourth is three to ten times higher. The effect lives entirely in
the conjunction.

**P3's recorded lean was right, for once.** S_merge was predicted small and
is small — on the 3B it is in fact slightly *negative* with an interval
excluding zero, meaning that folding a full rejection sentence into the same
bullet as the proposal it negates is, if anything, marginally more protective
than leaving it on its own line. A proposition with a verb keeps working
wherever it is put.

**P1 holds.** S_form_own is +0.042 and −0.021 here against E29-E's +0.052 and
−0.031, comfortably inside the 0.10 tolerance, re-measured in-session.

**P2 holds.** Δ_addonly is +0.031 and −0.010 against E29's +0.010 and +0.000.
Fifth independent replication of the add-only cells.

**P4.** Never-mentioned inclusion spreads 0.104 and 0.125 across the four
designs within an arm on the 3B and the 14B respectively, just outside the
declared 0.10, in the same displacement direction recorded for E29-E: the
`addonly_flag` cells carry the lowest never rates because the zombie step
occupies a slot in a pinned four-step plan. Reported, not repaired.

### What this establishes

The operative variable is neither of the two the E29-E write-up offered. It
is their conjunction:

> A retraction is ignored when it is written **as a non-propositional
> attribute of the very record it retracts**. Give it its own item, or give
> it a verb, and it is honoured; take both away and the model behaves as
> though it had not been written.

Two properties of the measurement make this unusually clean. The
proposition/own-item and proposition/same-item stores are **byte-identical in
content** — the entire difference is one `"\n- "` becoming `" "` — and they
give the same answer, which rules out any account based on token count,
position or surface length. And the attribute/own-item store, which changes
the wording without changing the structure, also gives the same answer, which
rules out any account based on phrasing. Only the cell that removes both the
item boundary and the verb behaves differently.

**The restatement effect tracks the same cell.** Δ is +0.031, 0.000 and
−0.010 in the three protective cells on the 14B and +0.240 [+0.156, +0.333]
in the attribute/same-item cell. A partner's restatement re-admits the
rejected step only where the retraction was structurally defused first.

### Why this is not a fact about memory systems

Nothing in the manipulation is specific to a memory store: it is a list of
statements in a prompt, and what changes is whether one statement is a
separate item and whether it has a verb. The finding therefore speaks to
retrieved chunks, tool results and policy lists as much as to a memory store.

It is, however, exactly how deployed memory systems encode revocation. Every
soft-delete design surveyed in §0 of the parent protocol, and every one of
the five shipped systems measured independently in arXiv:2609.08258, marks a
revoked record with an attribute *on that record* — a validity interval, an
`invalid_at` edge, an `is_active` flag. That is the losing cell of this 2×2,
and it is the industry default.

### What cannot follow

Two deciders, one corpus, oracle stores, and **one list format**: markdown
bullets. The claim as stated is about item structure, and a markdown bullet
is one way of making an item. Replicating the S_form_same contrast in JSON,
in XML-tagged items and in a numbered list is the necessary next step and is
named in `docs/paper/reframe-v2.md` §4.1; until it is run, the honest scope
is "in a markdown list". No frontier model was tested, so whether the effect
survives capability is open.
