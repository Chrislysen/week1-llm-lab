# E29-O: why does a revocation marker work after a record and not before it?

Declared 2026-09-30 with **zero outcomes**. Known when this was written:
- E29-S, E29-R, E29-T, E29-K, E29-M and E29-S+;
- all of E29-A, including its recognition condition (`433e811`).

A prior-art gate with web search (84 queries, `docs/protocols/E29O-gate.md`) ran first:
CANDIDATE WITH NARROW RESIDUAL. An independent methods review of a first draft returned
DECLARE AFTER REQUIRED FIXES. Every required fix is applied (§5).

## 0. Why

**Marker position is E29-A's most robust result.** On all three model families, a bracketed
revocation placed before the proposal text is under-applied: the step is planned more often.
The same marker after the text is honoured, and the bracket makes no difference.

| contrast | 3B | 14B | aya | class |
|---|---|---|---|---|
| POS, square brackets | +0.385 | +0.167 | +0.240 | EFFECT on all three |
| POP, parentheses | +0.302 | +0.156 | +0.323 | EFFECT on all three |
| BRP, BRS (bracket type) | | | | NONE on all three |

**Under-applied, not ignored.** The leading `[withdrawn]` still cuts the step from the
undecided level (0.92–1.00) to 0.60 / 0.31 / 0.49, and E29-K found it recognised as a rejection.
So every account below is graded: it explains why a leading marker is applied less, not why it
is never applied.

**What else is known:**
- **List position (post hoc).** The failure is heaviest where the record opens the list:
  0.96 / 0.44 / 0.84 there, against 0.59 / 0.32 / 0.41 after an ordinary fact. Outside the first
  position, POS is +0.30, +0.16 and +0.11.
- **A backward pronoun.** `[B rejected this]` drops the undecided proposal before it, so E29-O
  uses no pronoun.
- **Field-style markers fail even after the record.** E29-T: `[is_active: false]` 0.906 / 0.729
  and `[invalid_at: …]` 0.812 / 0.896. So "after" is not sufficient.

**The accounts.** Each explains why a leading marker is applied less than a trailing one.

| account | what it says | source |
|---|---|---|
| **NARR** | Text order is read as event order: `[withdrawn] A proposed to X.` reads as withdrawn, then proposed. | narrative bias, Fang et al., Findings NAACL 2024 (arXiv:2305.14970); Yamin et al. (arXiv:2410.23884) |
| **REC** | The last thing an item says about X dominates, whatever it means. | |
| **BIND** | A marker is applied to the record it follows, or to the record it names. | behavioural; a mechanistic version is tested separately (E29-W) |
| **CLAUSE** | A self-contained clause is applied wherever it stands; only a bare marker depends on position. | |
| **PROX** | What matters is the marker's distance to the step's name, not its direction. In `[withdrawn] A proposed to X` it is 3+ words away; in `X. [withdrawn]` it is adjacent. | |
| **META** | A bracketed label or field reads as metadata and is under-applied; a trailing bare word reads as a comment. | suggested by E29-T's failing trailing fields |

**Around them:**
- Order effects among conflicting statements are published (arXiv:2608.20116; Kurfalı and
  Östling, EMNLP 2025; arXiv:2402.08939), as is "an instruction after its input beats one
  before" (arXiv:2308.12097).
- Tang et al. (arXiv:2605.30233) find removal is implemented as a sticky, order-insensitive
  suppression.

**Residual:** no paper found moves a revocation marker from after to before its record's text
inside one item, with the words fixed, and measures whether the model then acts on the record.

## 1. Design (`lineage_e29o.py`, `e29o_order.py`)

**Corpus:** E29's two corpora, 192 dialogues with disjoint instance ids (corpus hashes
`187a426616f26598` and `e965c5fd022d6e37`). Doubling E29-A's n is for power: the reviewer's
simulations put Gate O at risk on the 14B and aya at n = 96.

**Setup:** E29-A's, unchanged: add-only stream, markdown list, system prompt, plan instruction,
pinned four-step plan, temperature 0, validator, 512-token runaway guard, neutral arm. A is the
proposer, B the rejector, X the rejected step, and Xc the step with a capital letter.

**Main block.** The fixed atemporal item N = `The team's office is on the third floor.` is
inserted directly before the record in every cell. So the record never opens the list and always
follows the same item. N appears in no stream. The rejection is recorded once and nowhere else;
`open` records none, which makes X undecided and sets the ceiling.

| cell | the record, after `- N` | test |
|---|---|---|
| `open` | `- A proposed to X.` | ceiling |
| `sentence_short` | `- A proposed to X.` / `- B rejected the proposal to X.` | reference |
| `withdrawn_pre` / `_post` | `[withdrawn] A proposed to X.` / `A proposed to X. [withdrawn]` | Gate O |
| `later_pre` / `_post` | `[subsequently withdrawn] A proposed to X.` / `A proposed to X. [subsequently withdrawn]` | T1 |
| `formally_pre` | `[formally withdrawn] A proposed to X.` | T1 length control |
| `label_pre` / `_post` | `[withdrawn: X] A proposed to X.` / `… [withdrawn: X]` | T3: names X, no verb |
| `clause_pre` / `_post` | `[B rejected the proposal] A proposed to X.` / `… [B rejected the proposal]` | T3: a clause, does not name X |
| `named_pre` / `_post` | `[B rejected the proposal to X] A proposed to X.` / `… [B rejected the proposal to X]` | T3: a clause that names X |
| `xfirst_pre` / `_post` | `[withdrawn] Xc (proposed by A).` / `Xc (proposed by A). [withdrawn]` | T4: distance reversed |
| `field_pre` / `_post` | `[status: withdrawn] A proposed to X.` / `A proposed to X. [status: withdrawn]` | T5: field form |

**Top block.** The same items, with the record moved to the top of the list and N left where the
record was: `first_sentence`, `first_pre` (`[withdrawn] A proposed to X.`) and `first_post`
(`A proposed to X. [withdrawn]`). This tests the record being first in the list within
dialogue; E29-A only observed it across dialogues. The move bundles serial position, having
nothing before the record, distance to the instruction and what follows the record.

**Why these markers:**
- In `xfirst`, the leading marker is adjacent to the step's name and the trailing one is 4+
  words from it. So PROX predicts the opposite sign to every other account.
- `[formally withdrawn]` has the same word count as `[subsequently withdrawn]` but carries no
  time.
- The label, clause and named cells cross "names X" with "is a clause".
- `[status: withdrawn]` holds the word fixed and changes only the form.
- N is a state, not a timed event, so "subsequently" has no event right before it to anchor to.

**Zero-call tests** (`test_lineage_e29o.py`) assert:
- both corpora hash as declared, and all 192 dialogues are distinct;
- in the main block the record directly follows N and never opens the list; in the top block
  it opens the list;
- N is in no stream;
- the rest of the stream keeps its order, untouched;
- the top block holds the same items as its twin, only the record moved;
- the rejection is recorded exactly once (never in `open`);
- each pre/post twin holds the same words;
- every marker is exactly as declared;
- the length control matches the temporal cue's word count;
- without N, three cells are E29-A's byte for byte;
- the twenty cells are distinct.

`test_e29o_analysis.py` builds synthetic data for each account and checks the read rule returns
that account and only that one. It also checks that:
- a length-only rescue fits no account;
- NOT RESCUED needs the end-state condition;
- the premise probe refutes NARR;
- reversed and uninformative outcomes refute what they contradict;
- the scaled classes follow each decider's order effect;
- the programme reading needs two agreeing deciders and no refutation.

**Deciders:** llama3.2:3b (digest `a80c4f17acd5`), qwen2.5:14b-instruct (`7cdf5a0187d5`) and
aya-expanse:8b (`65f986688a01`), on Ollama 0.34.4. The runner refuses any other digest or
version, and records both in every detail row.
- **Size:** 20 × 192 = 3,840 calls per decider, 11,520 in all, run in that order and
  checkpointed per dialogue.
- **Prompt hash:** `cebbddd2378f205f`, over every system and user message, pinned in the runner.
- **Transport:** requests go to `127.0.0.1`. On this machine `localhost` adds 2.04 s to every
  request (IPv6 fallback); the payload and server are the same.

**Probes** (`e29o_recognition.py`, hash `1ab20d15e0e747be`): same system prompt and blocks,
one question instead of the plan instruction, temperature 0, 8 tokens, 4,224 short calls per
decider. Every row records the digest and Ollama version.

- **Probe K** is E29-K's question, parsing and control target: "has the step X been rejected
  or withdrawn in this discussion?". It is asked on `withdrawn_pre`, `withdrawn_post`,
  `later_pre`, `named_pre`, `label_pre`, `clause_pre` and `field_post`. It is descriptive:
  whether each marker is understood as a rejection (hit rate R, control "yes" C, J = R − C).
- **Probe E** is the end state:
  `Question: at the end of this discussion, was the step "X" still proposed, or had it been withdrawn? Answer with exactly one word: proposed or withdrawn.`
  - The option order swaps on odd-indexed dialogues.
  - It is asked on `withdrawn_pre`, `withdrawn_post`, `later_pre` and `later_post`.
  - The control is a step that was not withdrawn: the undecided proposal if the dialogue has
    one, else the accepted one.
- **Validity** (each probe): all 192 dialogues answered (otherwise INCOMPLETE); parse ≥ 0.95;
  control hit rate ≤ 0.35 in every cell; and J on `withdrawn_post` ≥ 0.40, that is, balanced
  accuracy ≥ 0.70 where the marker is known to work. Otherwise VOID.
- **T1's end-state condition** (probe E valid): **MET** if `later_pre` draws "withdrawn" ≥ 0.80
  and no more than 0.15 below `later_post`, otherwise **NOT MET**.
- **NARR's premise** (probe E valid):
  - REFUTED if `withdrawn_pre` draws "withdrawn" ≥ 0.80;
  - SUPPORTED if it draws 0.15 or more below `withdrawn_post`;
  - otherwise UNCLEAR.

## 2. Predictions, fixed before the first call

Allowed outcomes per test and account (`PREDICTIONS` in `e29o_analysis.py`; "–" = no
prediction):

| test | NARR | REC | BIND | CLAUSE | PROX | META |
|---|---|---|---|---|---|---|
| T1 temporal cue | RESCUED | NOT RESCUED | NOT RESCUED | NOT RESCUED | NOT RESCUED | NOT RESCUED |
| T3 label (names X, no verb) | BOUND | BOUND | FREE | BOUND | FREE | UNINFORMATIVE |
| T3 clause (does not name X) | BOUND | BOUND | BOUND | FREE | BOUND | FREE |
| T3 named (both) | – | BOUND | FREE | FREE | FREE | FREE |
| T4 distance reversed | DIRECTION | DIRECTION | DIRECTION | DIRECTION | PROXIMITY | DIRECTION |
| T5 field form | WORKS | WORKS | WORKS | WORKS | WORKS | FAILS |
| T0 NARR's premise | SUPPORTED | – | – | – | – | – |

NARR makes no prediction for `named`, because "the proposal to X" presupposes an earlier
proposal.

- **P2 (specificity):** accepted and undecided-proposal inclusion stay within 0.10 across the
  twenty cells. Never-mentioned inclusion is reported beside every cell, because with four of
  six identifiers required, X is also a filler candidate.
- **P3 (author's lean), scored:**
  - Gate O is ORDER on at least two deciders;
  - the account is BIND on at least two;
  - the record-first interaction FPI is a positive EFFECT on at least two.

  The reviewer's power estimate is recorded beside the lean: at n = 96, Gate O was probably
  ORDER only on the 3B.

## 3. Read rule, fixed before the first call (`e29o_analysis.py`)

Per decider, neutral arm: inclusion of the rejected proposal's step (in `open`, the same step,
undecided), complete-case over the twenty cells, paired bootstrap over dialogues (seed 0,
B = 2000, percentile 95 %).

**Cell classes** against the reference REF, whichever of `sentence_short` and
`withdrawn_post` has the lower rate:
- FAILS if G ≥ 0.15 with an interval excluding 0;
- HONOURED if G's upper bound < 0.15;
- UNCLEAR otherwise.

**Gate O**, POS = P(`withdrawn_pre`) − P(`withdrawn_post`):

| class | condition |
|---|---|
| **ORDER** | POS ≥ 0.15, lower bound > 0 |
| **NO ORDER EFFECT** | interval inside (−0.15, 0.15) |
| **REVERSED** | POS ≤ −0.15, upper bound < 0 |
| **UNCLEAR** | otherwise |

The accounts are read only under ORDER.

**Scaled tests.** A test's difference d is judged against the decider's own order effect:
D = d − POS/2, bootstrapped jointly with POS, so "more than half of the order effect" is the
bar. A fixed 0.15 bar is out of reach where POS itself is near 0.15.

**T1, the temporal cue.** RESCUE = P(`withdrawn_pre`) − P(`later_pre`); LEN =
P(`withdrawn_pre`) − P(`formally_pre`).

| outcome | condition |
|---|---|
| **RESCUED** | RESCUE's D interval above 0, and LEN's below 0 |
| **LENGTH** | both above 0 |
| **NOT RESCUED** | RESCUE's D interval below 0, and probe E's end-state condition MET |
| **UNINTERPRETABLE** | RESCUE's D interval below 0, but the end-state condition not MET |
| **UNCLEAR** | otherwise |

**T3, per marker** m ∈ {label, clause, named}, d = P(`m_pre`) − P(`m_post`):
- UNINFORMATIVE if `m_post` FAILS;
- UNCLEAR if `m_post` is UNCLEAR;
- otherwise REVERSED if d ≤ −0.15 with an upper bound < 0, BOUND if D's interval lies above 0,
  FREE if it lies below 0, and UNCLEAR otherwise.

**T4, distance reversed:** PX = P(`xfirst_pre`) − P(`xfirst_post`). DIRECTION if the interval
lies above 0, PROXIMITY if below 0, UNCLEAR otherwise.

**T5, field form:** FF = P(`field_post`) − P(`withdrawn_post`), judged against half the trailing
marker's own effect, W = P(`open`) − P(`withdrawn_post`). FAILS if the interval of FF − W/2
lies above 0, WORKS if it lies below 0, UNCLEAR otherwise.

**T0:** NARR's premise from probe E.

**Account.** An account is refuted when an interpretable outcome of any test lies outside its
row of the table in §2. UNCLEAR, UNINTERPRETABLE and NOT READ are not interpretable. The verdict
is:
- the one account left;
- **NONE FITS** if none is left;
- **UNRESOLVED** (listing the survivors) if more than one is.

The read also reports the verdict under the draft's recognition rule (§5). Any verdict that
exists only under the amended rule is flagged.

**Descriptives, reported beside the verdict:**
- OPN = P(`open`) − P(`withdrawn_pre`);
- each cell against never-mentioned inclusion;
- POSL, PF, FPP, FPQ and FPS;
- FPI = (P(`first_pre`) − P(`withdrawn_pre`)) − (P(`first_post`) − P(`withdrawn_post`)), the
  record-first interaction.

**Programme reading** (`programme()`), over FINAL deciders; there is none with fewer than two:
- **Order:** ORDER on ≥ 2 and NO ORDER EFFECT or REVERSED on none → the order effect survives
  list-position control. NO ORDER EFFECT on ≥ 2 and ORDER on none → it does not. Otherwise mixed.
- **Account:** an account is SUPPORTED if it is the verdict on ≥ 2 deciders read under ORDER and
  refuted on none of them. Otherwise mixed.
- **Record first:** FPI ≥ 0.15 with an interval above 0 on ≥ 2 deciders, and ≤ −0.15 below 0 on
  none → the leading marker fails most when the record is first in the list. Otherwise mixed or
  unclear. No null reading is declared: a difference of four cells is too imprecise at this n for a
useful one.

**Status:**
- **VOID** if any cell parses below 0.95 or its mean |plan| is outside [3.9, 4.1].
- **INCOMPLETE** while fewer than 192 dialogues have been attempted.
- **FINAL** otherwise.

## 4. What each reading would mean, fixed before the first call

| reading | meaning | design rule for agent memory |
|---|---|---|
| **BIND** | A marker is applied to the record it follows or names; its direction, not its distance or form, decides. | Put a revocation after the record, or make it name the record. |
| **CLAUSE** | A self-contained clause works anywhere; only bare markers depend on position. | Write revocations as clauses. |
| **PROX** | The marker's distance to the step's name decides. | Put the marker next to the name. |
| **REC** | Whatever an item says last wins. | The revocation must come last. |
| **NARR** | Text order is read as event order, and an explicit time word repairs it. | Sequence revocations explicitly. |
| **META** | Bracketed labels and fields read as metadata and are under-applied. | Revocations as statements, not fields (E29-M's fix). |
| **NONE FITS / UNRESOLVED / mixed** | Reported test by test; no account is claimed. | |

The order effect failing to survive list-position control would mean E29-A's position effect
was mostly a record-first effect.

A mechanism arm (E29-W, `docs/protocols/E29W-knockout.md`) is declared in the same commit. It
tests on one model whether a trailing marker works by attending to its record.

## 5. Independent review and amendments before the first call

**The review.** An independent methods review of the draft (15 cells, 96 dialogues, three
accounts) returned DECLARE AFTER REQUIRED FIXES. How each point was handled:

| # | review point | disposition |
|---|---|---|
| 1 | a clause marker could return BIND on its own | now separated by the label / clause / named cross; each needs its post twin to work |
| 2 | FREE was one-sided | FREE is below-half and not reversed; REVERSED is its own outcome and refutes the accounts it contradicts |
| 3 | fixed 0.15 bars for tests capped by POS | scaled tests (D = d − POS/2) |
| 4 | the recognition check did not test time | probe E, the end-state question, carries T1's condition and tests NARR's premise |
| 5 | N was a timed event | now atemporal (`The team's office is on the third floor.`) |
| 6 | BIND strained by E29-A's own numbers | all accounts are graded; the mechanism is not claimed here and is tested in E29-W |
| 7 | proximity reproduced BIND's column | the `xfirst` pair reverses distance (T4) |
| 8 | `programme()` let a contradicting decider pass | a refutation on any decider read under ORDER blocks the account |
| 9 | incomplete recognition could feed a final read | INCOMPLETE below 192; digest and version per row |

**Recommendations taken:**
- the `[invalid]` pair is replaced by the unnamed clause pair;
- the HONOURED reference is the lower of `sentence_short` and `withdrawn_post`;
- FPI has no null reading;
- never-mentioned inclusion is reported beside every cell;
- run files sort naturally, and the system prompt is hashed;
- a length control (`[formally withdrawn]`) is added.

**Also added by the author:**
- the field pair (T5, META), because E29-T's trailing fields fail;
- the second corpus, for power.

**The recognition-rule amendment, disclosed.**
- **Trigger.** E29-A's recognition condition used a hard cap: VOID if the control's "yes" rate
  exceeds 0.20. It came out VOID on two deciders that discriminated almost perfectly:
  - llama3.2:3b: R 0.792 / 0.771, control 0.198 / 0.250;
  - aya-expanse:8b: R 1.000 / 1.000, control 0.115 / 0.208.
- **Old rule** (the draft of this protocol, verbatim): "CONDITION MET if the prefix
  `[subsequently withdrawn]` is recognised as a rejection no worse than 0.15 below the prefix
  `[withdrawn]`, with parse ≥ 0.95 and the control's 'yes' rate ≤ 0.20. VOID otherwise."
- **New rule:** as in §1. It uses probe E, a control cap of 0.35 and J ≥ 0.40.
- **Direction.** The change can only turn an UNINTERPRETABLE T1 into NOT RESCUED, which feeds
  REC, BIND, CLAUSE, PROX and META rather than NARR. The read therefore reports every verdict
  under both rules and flags any verdict that exists only under the new one.
- **Timing.** The amendment was made before any E29-O data existed. It is in the declaration
  commit.

E29-A's own recognition condition stays VOID where it was declared VOID. A J-based re-read of
E29-A would be exploratory.
