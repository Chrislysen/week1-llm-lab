# E29-A: attachment, the verb, or at-issueness?

Declared 2026-09-30 with **zero outcomes**. E29-S, E29-R, E29-T, E29-K, E29-M and the
E29-S+ family results were known when this was written. A prior-art gate with web search
(54 queries, `docs/protocols/E29A-gate.md`) ran first. An independent methods and
linguistics review of the first draft was applied before the first call; it also found
the E29-S correction below.

## 0. Why

**A correction to E29-S.** E29-S's "attribute, own item" cell is E29-E's status line,
`status(X) = WITHDRAWN; it is not needed for this case.`, and its reason clause has a
finite verb. The tag cell, `[withdrawn] A proposed to X.`, has neither a reason clause nor
a verb. So the tag is the only one of E29-S's four renderings without any finite clause,
and E29-S cannot tell "attached to the record and verb-less" apart from "no finite clause
at all". The paper was corrected to say so (`ffbddb7`).

Three accounts now fit the data:
- **Attachment:** a revocation fails when it is a verb-less attribute on the record, and is
  read when it has its own item, verb or not.
- **The verb:** a revocation needs a finite clause somewhere to be acted on.
- **At-issueness:** a revocation needs to be the main point of a sentence, not an aside.
  Kim and Misra (arXiv:2510.12740, EACL 2026) found models treat sentence-medial
  appositive relative clauses ("The librarian, who likes pasta, is famous!") as not-at-issue
  in dialogue-continuation likelihood, on 300 items. They did not test parentheticals, lists,
  actions or sentence-final appositives, and note that a sentence-final relative "may behave
  more at-issue-like" (see also Syrett and Koev 2015, *J. Semantics* 32(3)).

At-issueness depends on the question under discussion, and here that question ("which steps
go in the plan?") is answered by the rejection whatever its form. So this design manipulates
how the form marks the rejection as secondary, not its discourse status in the full sense.

Closest work: arXiv:2607.20115 patches between controlled rewrites but measures stance on the
statement itself; arXiv:2609.25686 finds a verb-less status line unreliable where a directive
sentence works, changing form and instruction together; arXiv:2406.19898 sweeps 26 paraphrase
types. E29-A keeps a small set of byte-controlled cells, the action-level estimand and the
pinned-plan controls.

## 1. Design (`lineage_e29a.py`, `e29a_at_issue.py`)

E29-T's setup unchanged: E29-S's add-only fact stream, markdown list, system prompt, plan
instruction, pinned four-step plan, temperature 0, validator and runaway guard, **neutral
arm**, 96 dialogues. The rejection is recorded once and nowhere else. A is the proposer, B
the rejector named in E29-S's own rejection sentence, X the rejected step.

| cell | the rejected proposal's rendering | finite clause | marked as secondary |
|---|---|---|---|
| `sentence` | `- A proposed to X.` / `- B rejected the proposal to X; it is not needed for this case.` (E29-S addonly) | yes | no |
| `sentence_short` | `- A proposed to X.` / `- B rejected the proposal to X.` | yes | no |
| `status_long` | `- A proposed to X.` / `- status(X) = WITHDRAWN; it is not needed for this case.` (E29-S addonly_meta) | yes (reason) | no |
| `status_short` | `- A proposed to X.` / `- status(X) = WITHDRAWN.` | **no** | no |
| `tag_prefix` | `- [withdrawn] A proposed to X.` (E29-S addonly_flag) | no | tag |
| `tag_suffix` | `- A proposed to X. [withdrawn]` | no | tag |
| `paren_prefix` | `- (withdrawn) A proposed to X.` | no | tag |
| `paren_suffix` | `- A proposed to X. (withdrawn)` (E29-T withdrawn_suffix) | no | tag |
| `verbal_tag` | `- [B rejected this] A proposed to X.` | yes | annotation |
| `arc_medial` | `- A's proposal, which was rejected by B, was to X.` | yes | medial appositive relative |
| `main_medial` | `- A's proposal was rejected by B; it was to X.` | yes | no |
| `appositive` | `- A proposed to X, a proposal that B rejected.` | yes | weak (sentence-final) |
| `coordination` | `- A proposed to X, and B rejected the proposal.` | yes | no |
| `parenthetical` | `- A proposed to X. (B rejected this.)` | yes | typographic aside |
| `bare_second` | `- A proposed to X. B rejected this.` | yes | no |

The medial pair uses the same words, with the rejection in the same place and X last in
both. "which" can only attach to "A's proposal", and it is a subject relative, so there is
no object extraction. The final pair is worded so that "the proposal" / "a proposal"
cannot attach to a noun inside X.

Zero-call tests (`test_lineage_e29a.py`) assert:
- `sentence`, `status_long` and `tag_prefix` are E29-S's blocks and `paren_suffix` is E29-T's,
  byte for byte, and they match the prompts those runs actually sent (llama3.2:3b,
  qwen2.5:14b-instruct and aya-expanse:8b for E29-S; the first two for E29-T);
- every cell keeps the rest of the add-only stream, in order, untouched, and changes only
  the proposal and rejection items;
- every cell records the rejection exactly once and names X; only `sentence` and
  `status_long` carry the reason clause;
- `status_short` is exactly `status(X) = WITHDRAWN.`;
- the medial pair differs only in the clause link;
- the fifteen cells are distinct.

Deciders: llama3.2:3b (Ollama digest `a80c4f17acd5`), qwen2.5:14b-instruct
(`7cdf5a0187d5`) and aya-expanse:8b (`65f986688a01`), Ollama 0.34.4. The runner refuses to
start on any other digest or version, and records both in every detail row. 15 × 96 = 1,440
calls per decider, 4,320 in all, run in that order, checkpointed per dialogue. Prompt hash
`9bd3597857f3a52e`, pinned in the runner.

**Recognition condition** (`e29a_recognition.py`, hash `20cdf27899b304d1`): E29-K's question
("has the step X been rejected or withdrawn in this discussion?"), answer parsing and control
target, asked on `arc_medial` and `main_medial` in the neutral arm for every decider, 384
short calls each. CONDITION MET if the aside is recognised as a rejection within 0.15 of its
main-clause twin, with parse ≥ 0.95 and the control's "yes" rate ≤ 0.20 (VOID otherwise).

## 2. Predictions, fixed before the first call

- **P1 (anchors).** `sentence`, `status_long` and `tag_prefix` reproduce E29-S within 0.10
  (3B 0.156/0.198/0.594; 14B 0.052/0.031/0.323; aya 0.156/0.031/0.479), and `paren_suffix`
  reproduces E29-T (3B 0.250; 14B 0.135). The position-by-bracket cells are read as explaining
  E29-T's exception only if `paren_suffix` replicates.
- **P2 (specificity).** Accepted and undecided-proposal inclusion stay within 0.10 across the
  fifteen cells. Never-mentioned inclusion is reported, not predicted.
- **P3 (the questions).** Author's lean, scored as follows:
  - H1: ATTACHMENT MATTERS (`status_short` HONOURED) on at least two deciders;
  - H2: AT-ISSUE GATES with the recognition condition met on at least two deciders;
  - the verbal tag helps less than a sentence: `verbal_tag` FAILS against `sentence_short`;
  - bracket type matters more than position: BRP and BRS both EFFECT, and POS and POP both
    not EFFECT.

## 3. Read rule, fixed before the first call (`e29a_analysis.py`)

Per decider, neutral arm, rejected-step inclusion, complete-case over the fifteen cells,
paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %).

**Cell classes** against `sentence_short`: G = P(cell) − P(`sentence_short`); FAILS if G ≥ 0.15
with an interval excluding 0, HONOURED if G's upper bound < 0.15, UNCLEAR otherwise. G against
`sentence` (E29-T's control) is also reported. The classes describe; they change the headlines
only through the gates below.

**H1, attachment or the verb:** the class of `status_short`.

| class | reading |
|---|---|
| HONOURED | **ATTACHMENT MATTERS**: a verb-less line is read when it has its own item |
| FAILS | **THE VERB EXPLAINS IT**: a verb-less line fails even in its own item |
| UNCLEAR | **UNSETTLED** |

**H2, at-issueness**, AM = P(`arc_medial`) − P(`main_medial`):

| class | condition |
|---|---|
| **UNTESTABLE** | `main_medial` is not HONOURED |
| **AT-ISSUE GATES** | AM ≥ 0.15 with an interval excluding 0 |
| **REVERSED** | AM ≤ −0.15 with an interval excluding 0 |
| **NO AT-ISSUE EFFECT** | AM's interval lies inside (−0.15, 0.15) |
| **UNCLEAR** | otherwise |

An AT-ISSUE GATES read counts as at-issue gating only if the recognition condition is met for
that decider.

**Secondary contrasts**, two-sided (EFFECT if |d| ≥ 0.15 with an interval excluding 0, NONE if
the interval lies inside (−0.15, 0.15), UNCLEAR otherwise):
- AT = P(`appositive`) − P(`coordination`), the sentence-final pair, with the stated expectation
  that a sentence-final relative may pattern like a coordination;
- PAREN = P(`parenthetical`) − P(`bare_second`), the brackets alone;
- VT = P(`tag_prefix`) − P(`verbal_tag`), which changes the word, adds a named rejector and adds
  a finite clause at once;
- POS = P(`tag_prefix`) − P(`tag_suffix`) and POP = P(`paren_prefix`) − P(`paren_suffix`),
  position with the bracket held; their difference POS − POP is reported;
- BRP = P(`tag_prefix`) − P(`paren_prefix`) and BRS = P(`tag_suffix`) − P(`paren_suffix`), bracket
  with the position held;
- RSN = P(`sentence_short`) − P(`sentence`) and SRC = P(`status_short`) − P(`status_long`), the
  reason clause; if either is EFFECT, E29-S's pattern is partly an effect of the reason clause
  and is reported as such;
- PWV = P(`paren_suffix`) − P(`parenthetical`), a finite clause inside the same parentheses.

**Programme reading** (`programme()`), over deciders whose read is FINAL (neither VOID nor
INCOMPLETE); no programme reading with fewer than two:
- H1: ATTACHMENT MATTERS on ≥ 2 and THE VERB EXPLAINS IT on none → the structural claim
  survives; THE VERB EXPLAINS IT on ≥ 2 and ATTACHMENT MATTERS on none → E29-S's pattern is the
  missing verb and the conjunction claim is withdrawn; otherwise mixed.
- H2: AT-ISSUE GATES with the recognition condition met on ≥ 2 and REVERSED on none → the
  at-issue account is supported; NO AT-ISSUE EFFECT on ≥ 2 with `arc_medial`, `parenthetical`
  and `verbal_tag` all HONOURED on each → the verb account is supported; UNTESTABLE on ≥ 2 →
  against both; otherwise mixed, reported cell by cell.

A decider's read is **VOID** if any cell parses below 0.95 or its mean |plan| is outside
[3.9, 4.1]. It is **INCOMPLETE** while fewer than 96 dialogues have been attempted; once all 96
have been attempted it is **FINAL**, on the complete-case n, reported. P1 and P2 misses are
reported beside the verdict and do not void it.
