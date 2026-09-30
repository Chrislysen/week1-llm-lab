# Revoked, but still planned: where and how an agent's memory writes a revocation decides whether a language model obeys it

*Working draft, restructured 2026-09-29 around the structural claim; retitled 2026-09-30 after E29-A.
Status: paused 2026-09-30, with E29-O and E29-W declared (§8). Every number below is in a
`results/*_summary.json` file and re-derives from the committed per-call CSVs
(`verify_claims.py`). Every protocol in `docs/protocols/` was committed with
zero outcomes before its first call, except E29-B, whose written predictions were added after 6 of its 48
dialogues had run (its read rule was committed in code first).*

## Abstract

Agent memories and tool registries mark a revoked record in place: a validity
interval, an `invalid_at` edge, an `is_active` flag, a `[withdrawn]` or
`[DEPRECATED]` prefix. We find that small open deciders act as though they had not
seen most of these in-place, verb-less encodings.
Written as `[is_active: false]` or `[invalid_at: …]`, a rejection leaves the
rejected step in the plan 73–91 % of the time, against 6–16 % when the same
rejection is a sentence.

Over one add-only memory we cross two properties of the rejection of a
proposal: whether it occupies its own list item, and whether it is a
proposition or an attribute.
- Merging the rejection sentence onto the proposal's item changes nothing. The
  text is byte-identical; one line break is removed.
- Rewriting the rejection as a status line in its own item changes nothing.
  That line, `status(X) = WITHDRAWN; it is not needed for this case.`, keeps a
  reason clause with a finite verb, so it is not verb-less (a correction made
  after the fact; §2.3).
- Doing both, so the rejection is a tag on the rejected record, raises
  enactment of the rejected step from 0.09–0.20 to 0.59 on llama3.2:3b, and
  from 0.03–0.05 to 0.32 on qwen2.5:14b-instruct.

The pre-registered verdict is INTERACTION on both deciders, and again on a third model
family (aya-expanse:8b, §4.6). Because the own-item status line carried a verb, that
design could not separate attachment to the record from the plain absence of a verb.
E29-A (§2.8) did, and attachment is not what decides it: a verb-less status line in its
own item fails on two of three deciders. What replicates on all three families is
position. `[withdrawn]` placed before the proposal text leaves the rejected step in 31–60 %
of plans; the same tag after the text leaves it in 15–25 %. Field-style markers fail even
after the text. Two follow-ups are declared: E29-O on why position matters (six accounts,
one prediction table) and E29-W on the mechanism (attention knockout). Both are paused
before a full run.

The finding came out of a memory-design study that motivates it. Across four
deciders from three model families, a partner's later restatement of a
rejected step re-admits it through write-time hard delete (difference-in-
differences against full context +0.21 to +0.50) and not through add-only. A
store that keeps the rejected proposal flagged `[withdrawn]` is not read as a
rejection, and on the largest decider it behaves like the deletion. The design
dependence survives a second corpus, an unpinned plan and a real Mem0 update
router. The 2×2 replicates in JSON, XML and numbered lists on both deciders, so
the effect is about list structure, not markdown. Of five revocation idioms in
deployed use, four fail on the 3B and three on the 14B. The exception, a
trailing `(withdrawn)`, shows that the structure alone does not decide it.
Appending one sentence ("The proposal to X was withdrawn.") when the record is
rendered removes 79–91 % of the effect on both deciders, and the field does no harm
once the sentence is there.
We release
the corpora, protocols, prompts and every store snapshot.

## 1. Introduction

Systems that let an agent act on remembered facts have to represent the fact
that something is no longer true. The designs that ship do it in place, as an
attribute of the record that was revoked:
- a validity interval or `invalid_at` edge on a knowledge-graph fact;
- an `is_active` or `deleted` field on a row;
- a status label beside a memory entry;
- a `[DEPRECATED]` prefix on a tool description.

Concurrent work shows this does not stop agents: on five shipped memory
systems, a visible revocation label left the revoked policy retrievable and
acted on in 43.1 % of trials (arXiv:2609.08258). Practitioners report the same
for deprecated tools in 2026 (§6). Neither isolates **how** the revocation is
written from **whether** it is visible.

We ask that question directly. Holding the information fixed, does the
*structure* of a revocation decide whether a model honours it? The answer comes
from a fixed-intervention 2×2 in which one cell is byte-identical text to
another. It is yes: a revocation is ignored when it is written as a verb-less
attribute on the record it revokes, and honoured when it is a sentence, whether
that sentence has its own item or not. E29-A (§2.8) then showed that attachment
is not what decides it. A verb-less line in its own item also fails on two of three
deciders, and the same `[withdrawn]` tag is honoured when it follows the record instead
of leading it. The attached, verb-less form is the industry
default, and the fields that implement it (`is_active`, `invalid_at`) are the worst we
tested (§2.5). The form is not sufficient on its own: one spelling of it, a
trailing `(withdrawn)`, is mostly read.

**Contributions.**
1. Where and how a revocation is written decides whether it is obeyed, pre-registered and
   replicated on three model families: fields and leading tags fail, while trailing words and
   sentences work (§2.3, §2.5, §2.8).
2. The setting that makes it consequential: *zombie steps*, rejected proposals
   that re-enter an executable plan when the proposer restates them. They come
   back through memory designs that delete a rejection or flag the rejected
   record, and not through designs that keep the rejection as a sentence (§3).
3. A read-time fix that removes most of the effect without changing storage, and
   evidence that the model recognises the tag it ignores (§2.6–2.7).
4. Robustness across four list formats (§2.4) and five deployed revocation
   idioms (§2.5), four deciders from three families, two corpora, pinned and
   unpinned output, and oracle and real write paths (§4).
5. Negative and cautionary results reported as such (Appendix A and B).

## 2. The structural result

### 2.1 Setup

**Corpus.** The E29 corpus (hash `187a426616f26598`) is 96 two-speaker incident
dialogues, each carrying exactly one proposal that the partner rejects, plus
accepted proposals and unrelated lines. Scorer tags never enter the prompt.

**Store.** Every store in this section is add-only: every fact from the
dialogue kept in order, rendered from the scorer's tags by fixed templates. So
the manipulation is the rejection's structure and nothing an extractor did. It
is shown to the decider as a list under the header `MEMORY NOTES FROM THE
DISCUSSION`.

**Decider.** A fixed system prompt (the E10 Operator), the store, and a frozen
plan instruction. The instruction pins the plan to four identifiers from a
six-item menu (E17 `pin4`), at temperature 0. The plan is parsed
deterministically, and the outcome per dialogue is whether the rejected step's
identifier is in it.

**Arm.** Every contrast in this section uses the *neutral* arm, where no line
brings the rejected step up again, so every store contains the rejection and
nothing that contradicts it.

**Read rule, fixed before the first call.** A paired bootstrap over dialogues,
seed 0, B = 2000, percentile 95 % intervals. A cell is void if its parse rate is
< 0.95 or its mean plan length falls outside [3.9, 4.1]. Every cell in every run
parsed at 1.000.

### 2.2 First pass: it is not the wording

E29-E held the store fixed and changed only how the rejection was written.
- `addonly` writes it as a sentence: "Safety Auditor rejected the proposal to
  snapshot the store; it is not needed for this case".
- `addonly_meta` puts a key-value line in the same position with the same
  trailing clause: "status(snapshot the store) = WITHDRAWN; it is not needed
  for this case".
- `addonly_flag` removes that line and prefixes the proposal with
  "[withdrawn] ".

Three deciders, 1,728 calls:

| decider | prose line | key-value line | prefix, no line | wording effect | own-line effect |
|---|---|---|---|---|---|
| llama3.2:3b | 0.156 | 0.208 | 0.594 | +0.052 [−0.042, +0.146] | **+0.385** [+0.281, +0.500] |
| qwen2.5:7b-instruct | 0.354 | 0.240 | 0.458 | −0.115 [−0.198, −0.031] | **+0.219** [+0.135, +0.302] |
| qwen2.5:14b-instruct | 0.062 | 0.031 | 0.323 | −0.031 [−0.073, +0.010] | **+0.292** [+0.198, +0.385] |

Figure 1 (`fig2-encoding.svg`). We had predicted a large positive wording
effect, and that hypothesis is withdrawn: re-wording spans zero on two deciders
and runs the other way on the third. What survives is the contrast that
changes only whether the negation has a line of its own. But that contrast
changed two things at once: the negation lost its item boundary *and* its verb.

### 2.3 The 2×2

E29-S separates the two properties over the same add-only fact stream
(Figure 2, `fig3-structure-2x2.svg`):

| | **own item** | **same item as the proposal** |
|---|---|---|
| **proposition** | `- A proposed to X.` / `- B rejected the proposal to X; …` | `- A proposed to X. B rejected the proposal to X; …` |
| **attribute** | `- status(X) = WITHDRAWN; …` | `- [withdrawn] A proposed to X.` |

The two proposition cells contain **byte-identical text**. The whole
manipulation is that one `"\n- "` becomes `" "`, and a test asserts it. Two
deciders, the extremes of the range, 1,536 calls, parse 1.000.

**A correction, made after the fact.** The own-item attribute cell is E29-E's status
line, `status(X) = WITHDRAWN; it is not needed for this case.`, and its reason clause
has a finite verb. The tag cell has no reason clause and no verb. So the "attribute"
row is verb-less only in the tag cell, and the 2×2 cannot tell "attached and
verb-less" apart from "no finite clause at all". The cell numbers below stand. E29-A
(§2.8) added a truly verb-less line in its own item (`status(X) = WITHDRAWN.`). It fails
on two of three deciders, so the conjunction below does not survive as a general claim.
What replicates is the marker's position: the same tag after the record is honoured.

Rejected-step inclusion, neutral arm, n = 96 per cell:

| | own item | same item | | own item | same item |
|---|---|---|---|---|---|
| **llama3.2:3b** | | | **qwen2.5:14b-instruct** | | |
| proposition | 0.156 | 0.094 | | 0.052 | 0.042 |
| attribute | 0.198 | **0.594** | | 0.031 | **0.323** |

| contrast | isolates | llama3.2:3b | qwen2.5:14b-instruct |
|---|---|---|---|
| S_merge | separation, proposition held | −0.062 [−0.125, −0.010] | −0.010 [−0.031, +0.000] |
| S_flag | separation, attribute held | **+0.396** [+0.281, +0.510] | **+0.292** [+0.198, +0.385] |
| S_form_own | form, own item held | +0.042 [−0.052, +0.135] | −0.021 [−0.062, +0.021] |
| S_form_same | form, same item held | **+0.500** [+0.396, +0.604] | **+0.281** [+0.188, +0.375] |

Three cells are indistinguishable and one is three to ten times higher, on
both deciders. The pre-registered rule returns INTERACTION on both.
- The byte-identical pair differs by one line break and agrees, which rules
  out token count, position and length. On the 3B, merging is marginally
  *more* protective.
- The attribute cell in its own item changes the words without changing the
  structure, and it agrees too, which rules out phrasing.

What remains is the conjunction:

> A retraction is ignored when it is written as a **non-propositional
> attribute of the record it retracts**. Give it its own item, or give it a
> verb, and it is honoured. Remove both and the model acts as though it were
> not there.

*(Superseded by §2.8: the verb-less line in its own item fails on the 3B and on aya,
and the tag fails because it leads the record.)*

Nothing in the manipulation is specific to memory. It is a list of statements
in a prompt, and what varies is whether one of them is a separate item and
whether it has a verb. So the result bears on retrieved chunks, tool results and
policy lists as much as on a store, provided it is not a fact about markdown.

### 2.4 Four list formats (E29-R)

Every store in §2.3 is a markdown bullet list, so the pattern could be a fact
about markdown. E29-R was declared in `5a36082`, after a prior-art gate with web
search (`docs/protocols/E29R-gate.md`). It re-renders E29-S's four stores, item
for item and character for character, as a JSON string array, as XML `<note>`
items and as a numbered list. Everything else is E29-S's, and the markdown
column is E29-S's own data. A test asserts that every rendering parses back to
E29-S's items, and that the markdown rendering is byte-identical to the
prompts E29-S sent. That is 4,608 calls, and every cell passes the validity
rule.

Neutral-arm rejected-step inclusion, the tagged cell against the other three
(Figure 3, `fig4-formats.svg`, drawn by `paper_fig_formats.py`):

| format | llama3.2:3b tag | other three | qwen2.5:14b tag | other three |
|---|---|---|---|---|
| markdown (E29-S) | **0.594** | 0.094–0.198 | **0.323** | 0.031–0.052 |
| JSON array | **0.604** | 0.094–0.177 | **0.354** | 0.031–0.073 |
| XML items | **0.510** | 0.052–0.135 | **0.302** | 0.031–0.052 |
| numbered list | **0.625** | 0.094–0.302 | **0.354** | 0.031–0.062 |

By the declared rule, the conjunction holds in all three new formats on both
deciders: S_flag and S_form_same reach 0.15 with intervals excluding zero,
and S_merge and S_form_own do not. The verdict is **GENERAL** on both.
- S_flag (JSON, XML, numbered) is +0.427, +0.375 and +0.323 on the 3B, and
  +0.323, +0.271 and +0.323 on the 14B.
- S_merge is negative in every format on both deciders, and on the 3B its
  interval excludes zero in all three new formats (for example, JSON −0.083
  [−0.146, −0.021]). Writing the rejection as a sentence on the proposal's
  own line does not raise enactment; it lowers it. Subordination is harmful
  only without a verb.

Two things are reported plainly. In the numbered list on the 3B, the status
line alone is somewhat less honoured (S_form_own +0.115 [+0.031, +0.208]).
That is below the threshold and does not change the read, but it is a real
form effect in that one format. And the never/accepted control (P2) misses its
0.10 band in three format-by-decider cells, by up to 0.025. This is the same
pinned-plan displacement as E29-E and E29-S.

The recorded lean was GENERAL, which held. Its guess that JSON would separate
least was wrong: JSON's S_flag is the largest of the three new formats on the
3B.

### 2.5 The idioms shipped systems use (E29-T)

E29-S measured one spelling of an in-place revocation, a `[withdrawn] ` prefix.
Deployed designs use others. E29-T was declared in `4d8bff1` with zero
outcomes. It keeps E29-S's add-only stream and records the rejection only as
one idiom on the rejected proposal's own item, with nothing else recording
it. Tests assert two things:
- the sentence control and the prefix anchor are E29-S's blocks byte for byte;
- every other idiom's store differs from the anchor's on exactly one item.

This is the neutral arm, 96 dialogues and 1,344 calls. Every cell is valid
(parse 1.000, mean |plan| 4.00). Figure 4 (`fig5-idioms.svg`, drawn by
`paper_fig_idioms.py`) shows the table below.

| the rejection, written as | llama3.2:3b | qwen2.5:14b |
|---|---|---|
| its own item, `- B rejected the proposal to X; …` (control) | 0.156 | 0.062 |
| `- [withdrawn] A proposed to X.` (E29-S's tag, anchor) | 0.604 fails | 0.312 fails |
| `- A proposed to X. (withdrawn)` | 0.250 unclear | 0.135 honoured |
| `- A proposed to X. [status: revoked]` | 0.469 fails | 0.156 unclear |
| `- A proposed to X. [is_active: false]` | **0.906** fails | **0.729** fails |
| `- A proposed to X. [invalid_at: 2026-09-12 10:04]` | **0.812** fails | **0.896** fails |
| `- ~~A proposed to X.~~` | 0.417 fails | 0.375 fails |
| *for scale: a step proposed and never decided* | *0.93–0.98* | *0.95–1.00* |

The classes follow the declared rule, with G = P(idiom) − P(control):
- **fails:** G ≥ 0.15 with an interval excluding zero;
- **honoured:** the interval's upper bound is below 0.15;
- **unclear:** anything else.

Four of the five real-world idioms fail on the 3B and three on the 14B. That
is **MOST-FAIL on both deciders**, which by the declared rule leaves the
deployment reading standing for the idioms in use (§3.5).
- **The machine-readable fields are the worst on both deciders.** With
  `[is_active: false]` or `[invalid_at: …]` the rejected step is planned at
  0.73–0.91. That is close to where a step nobody rejected sits (0.93–1.00),
  so the rejection barely registers. The `[withdrawn]` tag, by comparison,
  is partly read.
- **Strikethrough fails on both**, although it is markdown's own mark for
  deleted text.
- **One idiom fails on neither decider: the `(withdrawn)` suffix.** It is the
  anchor's own word, placed after the proposal in parentheses, and it is
  honoured on the 14B and unclear on the 3B. This is a limit on the
  structural claim. In E29-S the tag is the only one of four renderings that
  fails (with §2.3's caveat that the separated status line kept a verb). E29-T
  shows that the attached, verb-less form is not sufficient, because the
  spelling decides how much is lost. The suffix cell changes position
  and bracket together, so which of the two matters is not identified.
- **`[status: revoked]` splits:** it fails on the 3B and is unclear on the
  14B.

Two things are reported plainly. P2 misses on both deciders: never-mentioned
inclusion spans 0.479–0.667 (3B) and 0.500–0.708 (14B) across the seven
cells, against a 0.10 band, while accepted inclusion is 0.983–1.000. P1
holds: the anchor and the control reproduce E29-S within 0.011. The recorded
lean was MOST-FAIL, with `invalid_at` the most ignored and strikethrough the
most honoured. The verdict held. `invalid_at` was the most ignored on the 14B
only, and strikethrough was not the most honoured on either decider.

### 2.6 The model knows (E29-K)

Two explanations fit the tag result: the model does not read `[withdrawn]` as a
rejection, or it reads it and plans the step anyway. E29-K (declared in `7b2cf20`
with zero outcomes) asks the same decider, with the same system prompt and the same
four E29-S stores, one direct question instead of the plan instruction: "has the step
X been rejected or withdrawn in this discussion?" It asks about the rejected step and
about a step that was not rejected, as a control for a bias toward "yes".

Neutral arm, n = 96 per cell; "yes" rates for the rejected step and for the
control step, beside the planning rate from E29-S:

| store | 3B says "rejected" | 3B control "yes" | 3B plans it | 14B says "rejected" | 14B control "yes" | 14B plans it |
|---|---|---|---|---|---|---|
| sentence, own item | 0.812 | 0.052 | 0.156 | 0.990 | 0.000 | 0.052 |
| sentence, merged | 0.729 | 0.073 | 0.094 | 0.948 | 0.000 | 0.042 |
| status line, own item | 1.000 | 0.115 | 0.198 | 0.594 | 0.000 | 0.031 |
| `[withdrawn]` tag | 0.865 | 0.146 | **0.594** | 0.969 | 0.000 | **0.323** |

On both deciders the tag is recognised as a rejection as often as the sentence (gap
−0.052 [−0.146, +0.042] on the 3B, +0.021 [+0.000, +0.052] on the 14B), yet the tagged
step is planned far more often. By the declared rule the verdict is **READ-NOT-USED on
both**: the failure lies between knowing and acting, not in reading the tag. The
recorded lean was NOT-READ on the 3B (wrong) and READ-NOT-USED on the 14B (right).

Three caveats. Recognition and planning are different prompts, so this is a
dissociation across tasks, not a mechanism. It also runs the other way: the 14B calls
the status line a rejection only 0.594 of the time, yet plans that step at 0.031, so
what the question-and-answer probe measures is not what drives the plan. And on the 3B
the control's "yes" rate is highest for the tag store (0.146, under the declared 0.20
limit); on the 14B it is 0.000 everywhere.

### 2.7 A one-sentence fix (E29-M)

If the failure is in the form of the revocation, a memory system should be able to
fix it when it renders a record into the prompt, without changing its storage. E29-M
(declared in `3a2d54b` with zero outcomes, after an independent methods review) writes
the revoked record's field as a sentence, "The proposal to X was withdrawn.", either
replacing the field (rewrite) or keeping it (annotate). The rewrite store is E29-T's
control with one item re-worded in place. Neutral arm, 96 dialogues, 1,152 calls;
every cell parses 1.000, and the control and both anchors reproduce E29-T to the third
decimal. Figure 6 (`fig6-fix.svg`, drawn by `paper_fig_fix.py`):

| the rejected record is rendered as | llama3.2:3b | qwen2.5:14b |
|---|---|---|
| its own sentence (control) | 0.156 | 0.062 |
| `[is_active: false]` | 0.906 | 0.729 |
| `[invalid_at: …]` | 0.812 | 0.896 |
| field removed, sentence added (rewrite) | 0.292 partial | 0.135 fixed |
| `[is_active: false]` kept, sentence added | 0.292 partial | 0.146 partial |
| `[invalid_at: …]` kept, sentence added | 0.250 partial | 0.135 fixed |

Read by the declared rule, the rewrite is **FIXED on the 14B and PARTIAL on the 3B**,
so the declared "FIXED on both" is not reached. On both deciders:
- the sentence removes 0.79–0.91 of the anchors' excess over the control (E from
  +0.52 to +0.76, every interval excluding zero);
- the field does nothing once the sentence is present: D = +0.000 and −0.042 on the
  3B, +0.010 and +0.000 on the 14B, all INERT;
- no other step moves: accepted inclusion stays at 0.983–1.000 and undecided
  proposals at 0.950–1.000 across the six cells (P2 holds).

What remains on the 3B is a wording gap: the fix's sentence (8 words, no rejector, no
reason, passive) sits at 0.292 against the control's 0.156 (G +0.135 [+0.052,
+0.219]). That contrast changes four things together, so which one matters is not
identified. The practical reading is that a system which marks revocation with a field
can keep its storage and append one sentence when it renders the record. With E29-K,
the picture is consistent: the model can tell that a tagged record was revoked, but it
acts on a revocation that is stated as a sentence. The lean was FIXED on both deciders,
PARTIAL for the annotate cells and a competing field; the first held on the 14B only,
the second held except for the 14B's `invalid_at` cell, and the third was wrong on
both.

### 2.8 Position, not attachment (E29-A)

§2.3's correction left three accounts of E29-S's pattern:
- **attachment:** a verb-less revocation fails only when it is written onto the record;
- **the verb:** any revocation without a finite clause fails;
- **at-issueness:** a revocation fails when it is marked as an aside.

E29-A (declared in `a5cd6cd` with zero outcomes, after a 54-query prior-art gate and an
independent review) renders the one rejection fifteen ways over E29-S's add-only stream. It
runs on all three deciders: 4,320 calls, every cell parsing ≥ 0.95. Rejected-step inclusion
in the neutral arm, n = 96 per cell:

| the rejected proposal is rendered as | 3B | 14B | aya |
|---|---|---|---|
| `- A proposed to X.` / `- B rejected the proposal to X; <reason>.` (E29-S) | 0.156 | 0.062 | 0.125 |
| `- A proposed to X.` / `- B rejected the proposal to X.` (reference) | 0.302 | 0.167 | 0.385 |
| `- A proposed to X.` / `- status(X) = WITHDRAWN; <reason>.` (E29-S) | 0.208 | 0.031 | 0.021 |
| `- A proposed to X.` / `- status(X) = WITHDRAWN.` | **0.760** | 0.188 | **0.604** |
| `- [withdrawn] A proposed to X.` (E29-S's tag) | **0.604** | 0.312 | 0.490 |
| `- A proposed to X. [withdrawn]` | 0.219 | 0.146 | 0.250 |
| `- (withdrawn) A proposed to X.` | **0.531** | 0.302 | **0.552** |
| `- A proposed to X. (withdrawn)` (E29-T's suffix) | 0.229 | 0.146 | 0.229 |
| `- [B rejected this] A proposed to X.` | **0.906** | **0.667** | **0.833** |
| `- A proposed to X. (B rejected this.)` | 0.115 | 0.104 | 0.167 |

Bold cells FAIL against the reference, by the declared rule. The E29-S anchors reproduce
within 0.011 on the 3B and 14B and within 0.031 on aya.

**Attachment against the verb: mixed.** A truly verb-less status line in its own item
(`status(X) = WITHDRAWN.`) fails on the 3B and on aya (THE VERB EXPLAINS IT) and is honoured
on the 14B (ATTACHMENT MATTERS). By the declared programme rule, that is **mixed**, and §2.3's
conjunction does not survive as a general claim. E29-S's status line worked on all three
because of its reason clause: dropping "it is not needed for this case" raises inclusion by
+0.55, +0.16 and +0.58 (EFFECT on all three).

**At-issueness: not testable.** The medial main-clause control is itself not honoured on the
14B or aya, so the declared reading is UNTESTABLE there. The 3B's aside-versus-main-clause
contrast came out AT-ISSUE GATES. It does not count, because its recognition condition is
VOID: the model said "yes" about the control step 0.250 of the time, above the declared 0.20.

**What replicates on all three families is the marker's position.** The same `[withdrawn]`
before the proposal text and after it gives POS = +0.385, +0.167 and +0.240. With
parentheses, POP = +0.302, +0.156 and +0.323. All six are EFFECT, and bracket type never
matters (BRP and BRS NONE on all three). This explains E29-T's exception: the `(withdrawn)`
suffix worked because it trails the record, not because of its brackets. A clause inside the
leading tag is the worst rendering on every decider.

**Two confounds**, found after the fact and not declared (`docs/protocols/E29O-gate.md`):
- **List position.** The leading tag's failure is concentrated where the rejected proposal
  opens the list: 0.96, 0.44 and 0.84 there, against 0.59, 0.32 and 0.41 after an ordinary
  fact. Position was not manipulated.
- **A pronoun that points back.** `[B rejected this]` drops the undecided proposal just
  before it (5, 9 and 9 of 17, against 14 or more of 17 in every other cell). That cell
  measures misattribution, not order. P2 misses on undecided proposals on all three for this
  reason.

**A limit on "position decides".** E29-T's field-style markers also trail the record, and
they fail: `[is_active: false]` 0.906 and 0.729, `[invalid_at: …]` 0.812 and 0.896. So a
trailing position is not enough; what works is a revocation word or clause after the record.
E29-O asks why position matters, with list position controlled (§8). Figure 7
(`fig7-position.svg`, drawn by `paper_fig_position.py`) shows the pairs.

## 3. Why it matters: zombie steps

### 3.1 The memory designs

The structural result was found inside a study of what memory layers do with a
proposal that was rejected in dialogue. We call a rejected step that re-enters
the plan a *zombie step*. Three shipped designs treat that proposal
differently:
- The Mem0 paper's pipeline (arXiv:2504.19413) routes every extracted fact
  through ADD / UPDATE / DELETE, and by its own DELETE example consumes a
  rejection by deleting the proposal and storing nothing.
- Mem0's open-source v3 (April 2026) replaced that router with an add-only
  store.
- The LLM-wiki pattern (nashsu/llm_wiki) merges new information into one page
  per entity and queues contradictions for a human.

Each E29 dialogue is rendered in two arms differing by one line, spoken by the
original proposer as late as speaker alternation allows:

    restated   For the record, I did raise {action phrase} earlier in this discussion.
    neutral    For the record, I did raise {neutral referent of equal word count} earlier in this discussion.

Tests enforce the one-line difference, the same speaker and the same word
count.

The designs, as oracle stores rendered from the scorer's tags:
- `full`: the transcript.
- `delete`: ADD on a proposal, UPDATE on an acceptance, and on a rejection
  DELETE the proposal and store nothing. A later restatement is ADDed.
- `addonly`: every fact in insertion order.
- `wiki`: one page per action, with chronological bullets.

The estimands are Δ_X = P(rejected step in plan | restated, X) − P(… |
neutral, X) and DiD_X = Δ_X − Δ_full. A decider is DESIGN-DEPENDENT if some
|DiD_X| ≥ 0.15 with an interval excluding zero.

### 3.2 Design dependence on four deciders

Figure 5 (`fig1-delta-by-design.svg`). n = 96 dialogues per cell.

| decider | design | restated | neutral | Δ_X | DiD_X | 95 % CI |
|---|---|---|---|---|---|---|
| llama3.2:3b | full | 0.198 | 0.281 | −0.083 | ref | |
| | delete | 0.958 | 0.604 | +0.354 | **+0.438** | [+0.312, +0.562] |
| | addonly | 0.188 | 0.177 | +0.010 | +0.094 | [−0.010, +0.198] |
| | wiki | 0.240 | 0.135 | +0.104 | +0.188 | [+0.073, +0.312] |
| qwen2.5:7b-instruct | full | 0.240 | 0.312 | −0.073 | ref | |
| | delete | 0.885 | 0.583 | +0.302 | **+0.375** | [+0.271, +0.490] |
| | addonly | 0.312 | 0.344 | −0.031 | +0.042 | [−0.052, +0.135] |
| | wiki | 0.354 | 0.271 | +0.083 | +0.156 | [+0.042, +0.281] |
| qwen2.5:14b-instruct | full | 0.219 | 0.167 | +0.052 | ref | |
| | delete | 0.896 | 0.635 | +0.260 | **+0.208** | [+0.094, +0.323] |
| | addonly | 0.062 | 0.062 | +0.000 | −0.052 | [−0.135, +0.021] |
| | wiki | 0.062 | 0.094 | −0.031 | −0.083 | [−0.167, −0.000] |
| gemma4:e4b | full | 0.125 | 0.135 | −0.010 | ref | |
| | delete | 0.979 | 0.490 | +0.490 | **+0.500** | [+0.375, +0.625] |
| | addonly | 0.000 | 0.000 | +0.000 | +0.010 | [−0.062, +0.094] |
| | wiki | 0.000 | 0.000 | +0.000 | +0.010 | [−0.062, +0.094] |

All four deciders read DESIGN-DEPENDENT, carried by `delete`. On gemma4:e4b,
a third model family, the dependence is absolute: in 384 add-only and wiki
cells it never enacts a step whose rejection it can see. Under hard delete it
enacts the step at the never-mentioned rate (0.49) until the restatement
arrives, and at 0.98 after it.

The 14B decider almost never enacts a rejected step it can read (0.06 under
add-only and wiki). Under `delete`/neutral it enacts the step at 0.635 from a
store that says nothing about it, because a pinned four-step plan over a
six-item menu is completed from the menu (the never-mentioned control there is
0.54). That caps Δ_delete on the 14B. The smaller DiD is a ceiling of the
estimand, not a weaker mechanism.

### 3.3 A flag behaves like a deletion

The soft-supersede design an outside review proposed as the industry
mitigation (E29-X) keeps the rejected proposal flagged "[withdrawn]" and
stores nothing else for the rejection. In the neutral arm the flagged proposal
is enacted at 0.625, 0.421 and 0.292 on the 3B, 7B and 14B, against add-only's
0.177, 0.344 and 0.062. A bracket is not read as a rejection.

With the restatement present, the small deciders are partly protected by the
flag (0.646 and 0.463, against delete's 0.958 and 0.885). The 14B is not
(0.635; DiD +0.292 [+0.177, +0.396]). We had predicted the reverse size
ordering and record the miss.

That a visible flag is not enforced was published four days before this arm
ran, on shipped systems (arXiv:2609.08258), and is theirs. What §2 adds is
*which property of the flag* makes it fail.

### 3.4 The restatement effect lives in the tagged cell

On the 14B, a partner's restatement moves enactment only in the tagged cell of
the 2×2: Δ +0.240 [+0.156, +0.333], from 0.323 to 0.562. In the other three
cells it is within noise of zero (−0.010, −0.010, 0.000). Read through an
add-only store with the rejection as its own sentence, this decider enacts the
rejected step 0.052 of the time and ignores the restatement (Δ −0.010). Move
the same rejection onto the proposal as a tag, and the restatement becomes a
zombie trigger.

On the 3B the restatement raises no cell. The tagged cell is already at 0.594
without it (0.615 with it).

### 3.5 The deployment reading

Every soft-delete design we surveyed encodes revocation as an attribute on the
record being revoked: a validity interval, an `invalid_at` edge, an
`is_active` flag. So does every one of the five shipped systems measured by
arXiv:2609.08258. That is the losing cell of the 2×2, and E29-T tests those
idioms directly (§2.5).
- `[is_active: false]` and `[invalid_at: …]` are the two worst on both
  deciders (0.73–0.91).
- A trailing `(withdrawn)` is the one idiom that does not fail on either.

Writing the retraction as its own statement costs one line, and on the 14B
it moves enactment of a restated zombie step from 0.56 to 0.04.

## 4. Robustness

### 4.1 A second corpus

Six new domains (grid substation, airline hub, newsroom CMS, water plant,
e-commerce checkout, mobile core), with new action phrases and a second bank
of sentence templates, generated by the same rules (hash `e965c5fd022d6e37`, after the
extractor correction in Appendix B.3).

| decider | design | restated | neutral | Δ_X | DiD_X | 95 % CI |
|---|---|---|---|---|---|---|
| llama3.2:3b | full | 0.604 | 0.760 | −0.156 | ref | |
| | delete | 0.948 | 0.677 | +0.271 | **+0.427** | [+0.312, +0.552] |
| | addonly | 0.354 | 0.333 | +0.021 | +0.177 | [+0.073, +0.281] |
| | wiki | 0.500 | 0.344 | +0.156 | +0.312 | [+0.198, +0.438] |
| qwen2.5:7b-instruct | full | 0.521 | 0.677 | −0.156 | ref | |
| | delete | 0.958 | 0.531 | +0.427 | **+0.583** | [+0.458, +0.719] |
| | addonly | 0.406 | 0.490 | −0.083 | +0.073 | [−0.052, +0.198] |
| | wiki | 0.438 | 0.333 | +0.104 | +0.260 | [+0.146, +0.385] |
| qwen2.5:14b-instruct | full | 0.552 | 0.521 | +0.031 | ref | |
| | delete | 0.990 | 0.646 | +0.344 | **+0.312** | [+0.187, +0.448] |
| | addonly | 0.146 | 0.115 | +0.031 | +0.000 | [−0.104, +0.104] |
| | wiki | 0.177 | 0.104 | +0.073 | +0.042 | [−0.062, +0.146] |

All three deciders read DESIGN-DEPENDENT. The ordering holds and the levels do
not. Under full context the rejected step comes back at 0.76 and 0.68 (neutral
arm), against 0.28 and 0.31 on the first corpus, so the new rejection wordings
("take that one off", "I'd leave that out") are honoured far less by small
deciders. Absolute zombie rates are a property of wording and domain; the
design contrast is not.

With Δ_full at −0.156, every DiD sits 0.156 above its own Δ, and add-only's
DiD trips the band on the 3B although add-only itself did not respond
(+0.021). The within-store contrast Δ_delete vs Δ_addonly does not depend on
the reference arm:

| | 3B | 7B | 14B |
|---|---|---|---|
| second corpus | +0.271 vs +0.021 | +0.427 vs −0.083 | +0.344 vs +0.031 |
| first corpus | +0.354 vs +0.010 | +0.302 vs −0.031 | +0.260 vs +0.000 |

### 4.2 An unpinned plan

E29-F removes the four-step pin on the smallest and largest deciders (1,536
calls).
- Design dependence survives: DiD_delete +0.284 [+0.168, +0.400] on the 3B and
  +0.323 [+0.208, +0.437] on the 14B.
- The own-record effect survives: the flagged store exceeds the prose store by
  +0.537 [+0.442, +0.632] and +0.219 [+0.135, +0.302] in the neutral arm.

The cleanest reading is the excess over each cell's own never-mentioned rate,
which no ceiling argument can reach:
- Under add-only the rejected step sits 0.58 and 0.25 *below* a step the
  dialogue never mentioned.
- Under the flag encoding it sits at +0.05 and −0.12, that is, at chance.
- Under hard delete with the restatement present it sits 0.29 and 0.38
  *above* chance.

A written rejection suppresses; a flagged one does not; a deleted one plus a
restatement promotes.

One prediction failed. The 14B writes *shorter* plans when unpinned (2.3–3.0
against the pinned 4), so on that decider the pin was padding the plan, not
crowding it. One prompt drove the 3B into an unbounded generation. It was
bounded by a declared cap five times the largest completion otherwise
observed, and surfaces as one parse failure.

### 4.3 A real update router

E29-D feeds Mem0's update router, verbatim, from an extraction prompt of ours
that asks for operational facts, with few-shot examples on a domain absent
from the corpus. Extractor and router are qwen2.5:7b-instruct, the decider is
llama3.2:3b, on 48 dialogues.

| quantity | value |
|---|---|
| store mentions the proposed step after its proposal line | 0.958 |
| rejection removed the step from the store, given it was there | 0.217 (n = 46) |
| final store mentions the rejected step, restated / neutral | 0.854 / 0.750 |
| router events per dialogue, ADD / UPDATE / DELETE | 6.5 / 3.8 / 0.35 |
| rejected step enacted, restated / neutral | 0.667 / 0.500 |
| Δ_real | **+0.167 [+0.042, +0.292]** |
| E29 oracle delete / addonly / full on the same 48 dialogues | +0.396 / +0.042 / −0.125 |

REAL-STORE EFFECT by the pre-registered rule, with all four predictions
holding. The router under-deletes: one rejection in five becomes a DELETE.
Otherwise it ADDs the rejection or UPDATEs the proposal's text to carry it.
The restatement enters as a fresh fact.

Neutral-arm enactment on the real store (0.50) is far above oracle add-only
(0.17), although the rejection is usually present. The router's UPDATEs fold
the rejection into the proposal's own text, which is the losing structure of
§2 arising on its own.

### 4.4 Rendering

A transcript in which every accept and reject reply names its referent as the
store does ("No, drop the proposal to snapshot the store") leaves the
neutral-arm full-context level exactly where the plain transcript had it on
three deciders (0.281 → 0.281, 0.316 → 0.316, 0.167 → 0.167). The gap between
full context and add-only is not an artefact of how explicitly the referent is
rendered.

### 4.5 Controls

Accepted steps are enacted at 0.95–1.00 in every cell with a pinned plan (the lowest,
0.950, is qwen2.5:7b under delete in the neutral arm). Never-mentioned steps are
enacted at roughly 0.4–0.73 with a pinned plan, depending on decider, design and
corpus, and lower with an unpinned plan (down to 0.23 in E29-F). That band is the pinned-plan prior over the menu. The never/accepted
balance across the 2×2's four stores misses its ±0.10 band by 0.004 (3B) and
0.025 (14B). This is a displacement in a pinned plan, reported as such.

### 4.6 More model families (E29-S+)

E29-S's two deciders come from two families (Meta, Alibaba). E29-S+ (declared in
`4d30b5a` with zero outcomes) runs the same 2×2, byte for byte (block hash
`f25719fc5d4a268c`), on two more: aya-expanse:8b (Cohere) and gemma4:e4b (Google). The
read is E29-S's own rule plus E29-R's conjunction rule.

| aya-expanse:8b, neutral arm | own item | same item |
|---|---|---|
| proposition | 0.156 | 0.052 |
| attribute | 0.031 | **0.479** |

On aya-expanse:8b the verdict is **INTERACTION**, and the conjunction holds: S_flag
+0.448 [+0.344, +0.552] and S_form_same +0.427 [+0.333, +0.521] reach the threshold,
while S_merge −0.104 [−0.177, −0.042] and S_form_own −0.125 [−0.198, −0.052] do not.
Every cell parses 1.000 with mean |plan| 3.99–4.03. As on the 14B, the restatement
effect sits in the tag cell only (+0.177 [+0.094, +0.260]; the other three cells
+0.031 to +0.052, intervals including zero). The recorded lean (CONJUNCTION on aya) was
right. The structural result now holds on three families.

On gemma4:e4b the read is **VOID** by the declared rule: every cell parses (0.989–1.000),
but the mean plan length is 2.84–3.47 against the required [3.9, 4.1], so gemma did not
follow the pinned four-step plan. The cause is a change in the runtime, not in the
experiment. The user prompt E29-S+ sent is byte-identical to the one E29 sent for the same
dialogue and store on 2026-09-11, when gemma answered all 768 calls with a four-step plan;
on 2026-09-30, at temperature 0, it answered the same prompt with a one-step plan. The
Ollama version at the later date was 0.34.4; the earlier version was not recorded. The
same runtime reproduced llama3.2:3b's and qwen2.5:14b's E29-S cells to the third decimal
(E29-T, E29-M), so the change is specific to gemma. Descriptively, gemma's tag cell is
again the only high one (0.232 against 0.011–0.032), but the tag cell also has the longest
plans, which gives the rejected step more room; this is not counted. The structural claim
therefore rests on three families, with the fourth unreadable in this setup.

## 5. What this is not

- **Scope.** Two to four local deciders of 3B–14B from three families, no
  frontier model. The first question a reviewer will ask, whether the effect
  vanishes with capability, cannot be answered here without an API budget.
  arXiv:2609.08258's nine API-scale models failing on visible flags suggest it
  does not vanish, but they did not vary the encoding.
- **Corpora.** Two generated corpora with shared construction rules and
  three-template sentence banks, not naturalistic dialogue. The CaSiNo corpus
  (CC BY 4.0, 176 dialogues with an explicit offer-then-decline pair) is
  assessed as the human-dialogue replication and has not been run.
- **Stores.** Oracle stores are semantic ideals. The real-system leg uses one
  extractor prompt, one extractor model, one decider, and no retrieval layer.
- **Format.** Four list containers (markdown, JSON, XML, numbered). Prose
  paragraphs, tables and tool-call schemas are untested.
- **Tag spelling.** Seven spellings on two deciders, in markdown lists, in
  the neutral arm only (§2.5). Why a trailing `(withdrawn)` is read while a
  leading `[withdrawn]` is not (position, bracket, or both) is not
  identified. The formats of §2.4 were run with the prefix only.
- **The fix.** One sentence wording, in the neutral arm and markdown lists only. A
  record-agnostic sentence that does not restate the proposal was not tested, and
  E29-K's recognition-versus-planning dissociation is across two different prompts.
- **Runtime drift.** Local runtimes change. gemma4:e4b answered a byte-identical prompt at
  temperature 0 with a four-step plan on 2026-09-11 and a one-step plan on 2026-09-30
  (§4.6). Model digests and the Ollama version should be recorded with every run; this
  programme recorded them only from E29-M on.
- **Levels.** Levels across memory designs mix the design with the
  explicitness of the rendering, so only within-design contrasts are compared.

## 6. Related work

**Revocation in agent memory.** *Revoked but Still Authoritative*
(arXiv:2609.08258, 2026-09-08) is the closest. It loads five shipped memory
systems with a revoked policy and its replacement. Where the revocation label
is visible to the retrieval layer, the revoked fact is returned, outranks its
replacement, and yields the unsafe action in 43.1 % of 1,620 trials across nine
models. Prompt hardening reduces that only to 37.2 %, and a store-level filter
removes it. It varies whether the label is exposed, never how it is encoded.
It explains the failure by the two policies' equal standing and the revoked
one's more absolute phrasing. Our §2 is the controlled encoding comparison it
does not run, and our §3.3 reproduces its central observation on oracle
stores.

**Status lines, notes and the fix.** *How Strongly Should Task State Influence an
LLM Agent?* (Zhang, Kweon and Han, arXiv:2609.25686, 2026-09-22) is concurrent and
consistent with our result: a verb-less status on a checklist item ("- s10:
DONE") is unreliable, and a directive sentence raises strict success from 0.55 to
0.84 on Qwen3-235B. Their design changes form and instruction together. *Dead text or
binding clause?* (Zhu, arXiv:2608.12599, 2026-08-12) is a precedent for §2.7: a
one-sentence "tombstone" note cuts relapse from 0.135 to 0.087, against 0.140 for an
equal-length irrelevant note. Our E29-M adds the controlled comparison of removing the
field, keeping it, and neither, and the finding that the field is inert once the
sentence is present.

**Knowing without using.** *LLMs Know the Constraint But Do Not Use It* (Li, Krishnan
and Padman, arXiv:2608.12321, 2026) shows, for constraints that must be inferred, that
a probe decodes the constraint while the model's output ignores it, and that patching
from a donor stating the constraint as one declarative sentence repairs it on one of
two models. *Model-Adaptive Tool Necessity Reveals the Knowing-Doing Gap in LLM Tool
Use* (Cheng et al., arXiv:2605.14038, 2026) names the same gap for tool calls. Our
E29-K (§2.6) is a behavioural analogue for a revocation that is stated explicitly; we
make no mechanistic claim. *Hey, wait a minute: on at-issue sensitivity in Language
Models* (Kim and Misra, arXiv:2510.12740, EACL 2026) finds that models treat
not-at-issue content (asides such as appositive relative clauses) differently from the
main point, which offers a candidate explanation of why a revocation attached to its
record is ignored.

**Memory designs.** Eighteen papers were read in full text under the E29
novelty gate (`docs/protocols/E29-memory-semantics.md` §0), each occupying a
component of the construct without the conjunction:
- *Forgetting Without Restarting* (arXiv:2609.04875): revocation with
  same-agent re-mention.
- *LatticeMind* (arXiv:2608.08236): late stale notes, concatenation hurt most.
- *STALE* (arXiv:2605.06527): excludes contradiction by construction.
- *Control-plane placement* (arXiv:2606.15903): thirteen configurations at the
  retrieval layer. Its Appendix P reports that the Mem0 router under-deletes,
  which our §4.3 confirms at the action layer.
- *MemOps* (arXiv:2607.12893): stale value rate, Mem0 0.102 vs long context
  0.016.
- *MemStrata* (arXiv:2606.26511): cannot record a negation.
- *TOKI* (arXiv:2606.06240), *MemTX* (arXiv:2607.23929) and *Governed
  Persistent Memory* (arXiv:2608.12476): write- and commit-layer resolution.
- *The Memory Trust Gap* (arXiv:2609.01852): Qwen3 0.6–8B answer a stale stored
  fact 0.92–1.00 of the time, and metadata helps capable models.

**Deprecation and negation.** Practitioner reports from 2026 (Tian Pan, "MCP
Tool Deprecation", May; "The Deprecation Notice Your Agent Can't Read", July)
describe `[DEPRECATED]` tags on tool descriptions being under-read and a
separate explicit line helping, without controlled measurement. The 2×2
refines that folklore: merging a sentence onto the record is harmless, and only the
attached, verb-less tag fails; whether a separate verb-less line would also fail is
E29-A's question (§2.3).

For code models, *LLMs Meet Library Evolution* (arXiv:2406.09834, ICSE'25)
inserts a natural-language deprecation comment into the prompt (fixing 25.7–
97.2 % of deprecated uses across models) but has no annotation-on-item
condition. The negation literature establishes that language models are weak
on negation and its scope (arXiv:2306.08189, arXiv:2408.03070). None of it
varies a revocation's structural position in a list context.

The prior-art gate for §2, with its search log, is
`docs/protocols/E29R-gate.md`.

## 7. Reproducibility

Every protocol in `docs/protocols/` was committed with zero outcomes before
its first call, except E29-B, whose written predictions were added after 6 of its 48
dialogues had run (its read rule was committed in code first). Most were appended with the outcome afterwards; the E29-R and
E29-T outcomes are recorded in this draft and in `results/`. Commit hashes are
named in each.

Corpus hashes: E16 `70f136a47f5779c8`, E29 `187a426616f26598`, E29-C
`979143b67049adf2`, E29-N `e965c5fd022d6e37` (after the extractor correction;
`7d33038c6c1a9912` before it). Prompt-block hashes: E29-S
`f25719fc5d4a268c`, E29-R `8a9412801fc2bae1`, E29-T `69c8d207f3993086`, E29-K `e9ef529280d358bb`, E29-M
`ecb2edf1dd1f84b9`. Runners refuse to start if a hash moves. `verify_claims.py` re-derives the headline numbers from the per-call CSVs.

Runs re-execute with the matching runner (`e29_memory_semantics.py`,
`e29e_encoding.py`, `e29s_structure.py`, `e29r_formats.py`, `e29t_idioms.py`,
`e29k_recognition.py`, `e29m_fix.py`, `e29d_ops_extractor.py`), and analyses with the matching `*_analysis.py`, with
zero model calls. `python xray_server.py` serves a side-by-side view of any
dialogue through any two memory designs, and a live re-run of the decider
checked against the record.

## 8. Status and next experiments

The programme is paused as of 2026-09-30. Two follow-ups are declared and public (`0281990`,
pushed before any call):

- **E29-O** (`docs/protocols/E29O-order.md`) asks why a revocation marker works after a record
  and not before it.
  - **Size:** twenty cells on both corpora (192 dialogues) and the three deciders.
  - **Accounts:** narrative order, last mention, attachment direction, a self-contained clause,
    distance to the step's name, and field form.
  - **Read rule:** a prediction table in which an account is refuted by any interpretable
    outcome outside its row. An independent methods review's nine required fixes are applied
    before the first call.
- **E29-W** (`docs/protocols/E29W-knockout.md`) tests the mechanism in one model:
  Llama-3.2-3B, with attention knockout in Hugging Face transformers. Does a trailing
  `[withdrawn]` work because its tokens read the record?

**Where the run stopped.** A first E29-O run was stopped by the local job runner after 151 of
192 dialogues on llama3.2:3b. Those rows are committed and have not been read. The declared
read uses only complete runs, and a resumed run continues from them:
`python run_queue.py --log results/e29o_run.log -- "python -u e29o_order.py --all" "python -u e29o_recognition.py --all" "python -u e29w_knockout.py --run"`.

**Next in line: tool registries.** The same question applies there. Does `[DEPRECATED]`
before a tool's description stop an agent calling it as reliably as the same tag after the
description? A prior-art gate returned CANDIDATE WITH NARROW RESIDUAL
(`docs/protocols/TOOLS-gate.md`):
- appended negative cues and list-position bias in tool selection are published;
- no study found moves a status marker within a tool's description, with the words held
  fixed.

It is not declared.

**Not tested at all:** frontier models.

## Appendix A. Predictions against outcomes

| protocol | prediction | outcome |
|---|---|---|
| E29 P1 | Δ_delete ≈ +0.4 on the 3B decider | +0.354 |
| E29 P2 | DiD_delete ≥ 0.15, interval excludes 0 | +0.438, +0.375, +0.208, +0.500 on four deciders |
| E29 P3 | Δ_full small | small, but negative on 3B/7B: a miss on sign, followed up in E29-C (Appendix B.2) |
| E29 P4 | 0 ≤ DiD_addonly < DiD_delete | +0.094, +0.042, −0.052, +0.010 |
| E29-B | manipulation check ≥ 0.5 | 0.11: UNINFORMATIVE, stopped (Appendix B.1) |
| E29-C P1 | Δ_ftr replicates on 3B | −0.083 vs −0.083 |
| E29-C P2 | H-frame vs H-mention | FRAMING (3B); NO-REPLICATION at the boundary (7B) |
| E29-D P0–P3 | store ≥ 0.5; W1 < 0.5; 0 ≤ Δ_real < Δ_delete; W2 restated > neutral | 0.958; 0.217; +0.167 < +0.396; 0.854 > 0.750 |
| E29-N P1 | DESIGN-DEPENDENT via delete on each decider | +0.427, +0.583, +0.312 (after the extractor correction; +0.344, +0.469, +0.250 before) |
| E29-N P2 | \|DiD_addonly\| < 0.15 | holds on 7B (+0.073) and 14B (0.000), fails on 3B (+0.177) through the reference arm |
| E29-X R1 | explicit referents move the full-context level toward add-only (lean: yes on 3B) | no, on all three: level unchanged to the third decimal |
| E29-X T1 | tombstone between add-only and delete; lean: flag not honoured on 3B, honoured on 14B | between on 3B and 7B; NOT honoured on 14B (DiD +0.292): the lean was reversed |
| E29-E P1 | re-wording the rejection as a key-value line raises enactment by ≥ 0.15 | fails on all three: +0.052, −0.115, −0.031. The encoding-as-wording hypothesis is withdrawn |
| E29-E P2 | G_flag ≥ G_meta | holds on all three |
| E29-E P3 | Δ_addonly reproduces E29's within 0.10 | within 0.03 on all three; fourth replication |
| E29-E P4 | never/accepted within 0.10 across designs | fails on the 3B (0.146, 0.188) and the 14B restated arm (0.125); displacement in a pinned plan, reported |
| E29-F F1 | unpinning lengthens plans | holds on the 3B (3.9-4.8), fails on the 14B, which writes *shorter* plans unpinned (2.3-3.0 vs the pinned 4) |
| E29-F F2 | DiD_delete >= 0.15 unpinned | +0.284 and +0.323, both intervals excluding 0 |
| E29-F F3 | the own-record effect survives unpinning | +0.537 and +0.219, both intervals excluding 0 |
| E29-F F4 | accepted inclusion >= 0.95 | 0.983 minimum |
| E29-S P1 | S_form_own reproduces E29-E within 0.10 | +0.042 vs +0.052, -0.021 vs -0.031 |
| E29-S P2 | Delta_addonly reproduces E29 within 0.10 | +0.031 and -0.010; fifth replication |
| E29-S P3 | lean: S_merge small, so FORM or INTERACTION | correct: S_merge -0.062 and -0.010; INTERACTION on both |
| E29-S P4 | never/accepted within 0.10 across designs | misses by 0.004 and 0.025, same displacement as E29-E |
| E29-R P1 | every cell valid (parse ≥ 0.95, \|plan\| in range) | holds: no VOID cell on either decider |
| E29-R P2 | never/accepted within 0.10 across designs, per format | misses by up to 0.025 in three cells (3B JSON and numbered, 14B numbered); pinned-plan displacement, reported |
| E29-R P3 | lean: GENERAL, smallest separation in JSON | GENERAL on both deciders (conjunction in 3/3 formats each); JSON separated most on the 3B, not least |
| E29-T P1 | anchor and control reproduce E29-S within 0.10 | holds: within 0.011 on both deciders |
| E29-T P2 | never/accepted within 0.10 across the seven cells | misses on both: never spans 0.479–0.667 (3B) and 0.500–0.708 (14B); accepted 0.983–1.000 |
| E29-T P3 | lean: MOST-FAIL on both; `invalid_at` most ignored; strikethrough most honoured | MOST-FAIL on both (4/5, 3/5); `invalid_at` most ignored on the 14B only (the 3B: `is_active`); strikethrough fails on both, and the `(withdrawn)` suffix is the most honoured |
| E29-K lean | NOT-READ on the 3B, READ-NOT-USED on the 14B | READ-NOT-USED on both (3B gap −0.052 [−0.146, +0.042], tag recognised 0.865; 14B gap +0.021 [+0.000, +0.052], tag recognised 0.969): wrong on the 3B, right on the 14B |
| E29-M P1 | control and anchors reproduce E29-T within 0.10 | holds exactly on both deciders |
| E29-M P2 | accepted and undecided inclusion within 0.10 across the six cells | holds on both (accepted 0.983–1.000; undecided 0.950–1.000) |
| E29-M P3 | lean: rewrite FIXED on both; annotate PARTIAL; field COMPETES | rewrite FIXED on the 14B, PARTIAL on the 3B (0.79–0.91 of the excess removed); annotate PARTIAL except the 14B's invalid_at cell (FIXED); field INERT on both |
| E29-S+ lean | CONJUNCTION on aya; gemma may read NULL near floor | aya-expanse:8b: INTERACTION, conjunction holds (lean right); gemma4:e4b VOID (mean plan 2.84–3.47), neither NULL nor a read; runtime drift, §4.6 |
| E29-A P1 | anchors reproduce E29-S and E29-T within 0.10 | holds on all three deciders (largest gap 0.031, aya's sentence cell) |
| E29-A P2 | accepted and undecided inclusion within 0.10 across the fifteen cells | misses on undecided proposals on all three (3B 0.733–0.983, 14B 0.867–1.000, aya 0.767–0.983): `[B rejected this]` drops the proposal before it |
| E29-A lean, H1 | ATTACHMENT MATTERS on at least two deciders | wrong: MIXED (the verb explains it on the 3B and aya; attachment matters on the 14B) |
| E29-A lean, H2 | AT-ISSUE GATES, recognition met, on at least two | wrong: UNTESTABLE on the 14B and aya; the 3B's AT-ISSUE GATES does not count (recognition VOID); programme reading AGAINST BOTH |
| E29-A lean, verbal tag | `[B rejected this]` FAILS against the reference | right on all three (0.906, 0.667, 0.833) |
| E29-A lean, bracket | bracket type matters more than position | wrong, the reverse: POS and POP EFFECT on all three, BRP and BRS NONE |

## Appendix B. Process record

These legs make the work trustworthy rather than interesting. They are kept
whole here, not in the argument.

### B.1 A real-extractor attempt that failed by its own rule (E29-B)

E29-B ran the Mem0 paper's `FACT_RETRIEVAL_PROMPT` and
`DEFAULT_UPDATE_MEMORY_PROMPT` verbatim with a 3B model on 48 of the dialogues.
The manipulation check declared in advance required the store to mention the
proposed step after its proposal line in ≥ 0.5 of dialogues, and it failed at
0.11. A personal-information extractor does not store operational proposals.
The stage was stopped at 18 dialogues and recorded as uninformative. E29-D
(§4.3) is the leg that replaced it.

### B.2 The full-context register effect (E29-C)

Under full context the restatement *lowered* enactment on the 3B and 7B
deciders (−0.083 and −0.073 on the first corpus, −0.156 on both on the
second), against a prediction of "small".

E29-C (768 calls) re-ran the two E29 lines beside a plain late mention with no
authorship claim ("Just to note it, X came up earlier in this discussion") and
its own neutral control. On the 3B:
- The E29 number replicated to the third decimal (−0.083 [−0.156, −0.010]).
- The plain mention did nothing (+0.062 [−0.010, +0.135]).
- The difference between the two framings excluded zero (−0.146 [−0.240,
  −0.062]): FRAMING by the pre-registered rule.

On the 7B the interval's upper bound landed exactly on zero (−0.062 [−0.135,
+0.000]), so the declared verdict is NO-REPLICATION, not upgraded. The
protective effect, where it exists, comes from the "for the record, I did raise
it" register, which sends a full-context reader back to the exchange where the
step was rejected. The stores never see that register; they see a fact.

### B.3 The second-corpus extractor correction (E29-N)

One extractor bug reached a run. The oracle extractor keyed reply polarity on
a sentence prefix, and mis-stored one second-corpus rejection wording as an
acceptance in 24 of 96 dialogues (store designs only). It was found by reading,
and fixed by template membership with a test. The 144 affected cells per
decider were re-run. The first-corpus blocks were hash-verified byte-identical
before and after, and both versions of every second-corpus number are on disk
(`docs/protocols/E29N-second-corpus.md` §6–7).
