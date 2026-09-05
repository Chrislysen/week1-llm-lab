# E16 — exploratory screen: zombie constraints under full context and under budgeted retrieval

**EXPLORATORY. Declared before the run, committed with zero E16 decider
outcomes. Nothing this produces can become a claim.** It decides one thing:
whether the candidate `S-O` in `docs/E16-CANDIDATES.md` is worth a
preregistered confirmation.

## The candidate it screens

A constraint is proposed in the dialogue and, in the very next message,
explicitly rejected and never replaced. Prediction (1): small models still
carry the rejected action in the final plan at a rate above the
never-mentioned base rate. Prediction (2): the excess shrinks with size.
Prediction (3): under a word-budgeted content-scoring retrieval policy the
excess grows, because the action-bearing proposal is retrieved and the
content-poor rejection is not.

Prior-art status (2026-09-03, `docs/E16-CANDIDATES.md`): behavioural half
OPEN (NARROW) — closest *Attention Latch* arXiv:2604.24512 (replacements,
frontier models, LLM judge, no base rate, no retrieval policy); mechanism
half OPEN. That gate ran without web search and must be re-run before any
claim. A screen needs no more than this.

## Corpus — `lineage_e16.py`, hash `70f136a47f5779c8`

36 Mode-A instances × 4 rotations = 144 dialogues. Unit = a `required`
constraint (96 of them); statuses `accepted` / `rejected` / `proposed` /
`never` rotate by (slot + rotation) mod 4, so **every constraint is seen once
under every status** (384 units, 96 per status; paired within constraint,
clustered by instance). Ordering constraints are not rendered (scope limit:
they would pressure inclusion for reasons other than the requirement).
Replies carry no action words; a reply always immediately follows its
proposal from the other speaker; the last message is always noise. Nine
gates in `test_lineage_e16.py`; the three frozen corpora are re-hashed there.

## Decider eligibility — hypothesis-blind

`qwen2.5:3b-instruct` and `qwen2.5:14b-instruct` (the size contrast inside
one family) and `llama3.2:3b` (the project's workhorse). All three have shown
non-degenerate plan channels on this benchmark family (E4, E8, E11). None is
chosen for an expected direction. 144 calls per decider per policy.

## Offline preflight — already run, no model called (`e16_preflight.py`, `results/e16_preflight.csv`)

For every dialogue and budget, which positions each policy keeps at
finalisation (the frozen query: plan instruction + latest message). The
number that matters is the **orphan rate**: proposal kept, its reply dropped.

| budget 35 words (median dialogue 59.5) | P(proposal kept) | P(reply kept) | orphan rate, rejected units |
|---|---|---|---|
| recency-35 | 0.370 | 0.661 | **0.000** |
| random-35 | 0.531 | 0.568 | 0.333 |
| bm25-35 | 0.573 | 0.521 | 0.438 |
| dense-35 | 0.891 | 0.151 | **0.865** |
| fusion-35 | 0.818 | 0.266 | 0.781 |

The mechanism exists at the retrieval level: a dense policy at this budget
keeps 89 % of proposals and 15 % of replies, orphaning 87 % of rejections;
recency keeps or drops the adjacent pair together and orphans none. Stage 2
therefore uses **`dense:35`** as the mechanism arm and **`recency:35`** as the
adjacency control, fixed now. Budgets 25 and 50 are in the CSV for the
record and are not run.

## What is run

`e16_zombie_screen.py`: E10's decider system prompt, E13's validator and
bounded parse/retry, the frozen plan instruction, temperature 0.

- **Stage 1:** `--policy full`, three deciders, 432 calls.
- **Stage 2:** `--policy dense:35` and `--policy recency:35`, on every decider
  that passes the stage-1 gates below, up to 864 calls. What each policy kept
  is recorded per unit (`proposal_in_context`, `reply_in_context`,
  `exposure`), so the read is conditional on realised exposure, not on the
  intended status alone.

## What is computed — `e16_analysis.py`, fixed now

Per decider and policy: parse rate; include rate per status; paired
contrasts per constraint — `rejected − never`, `rejected − proposed`,
`accepted − rejected`, `proposed − never`, `accepted − never` — with
instance-level sign-flip permutation (20 000 reps, seed 20260903) and
instance-level bootstrap CI (2 000 reps); for a budgeted policy, include rate
by (status, exposure).

## How it is read

**Stage-1 gates (validity, per decider).** Parse rate ≥ 0.95;
`accepted` include rate ≥ 0.80 (the decider follows an accepted requirement
at all); `never` include rate ≤ 0.50 (the plan is not padded with the whole
vocabulary, so a base rate is measurable); `accepted − rejected` ≥ +0.10
(the decider can use a rejection when it sees one — otherwise stage 2 has
nothing to orphan). A decider that fails a gate is reported and not carried
to stage 2.

**Reading A (full-context zombie).** `rejected − never` with its cluster p
and CI, per decider, and whether the 3B excess exceeds the 14B excess.
Descriptive; no threshold turns it into a claim.

**Reading B (retrieval-induced zombie) — the pursuit rule.** Under
`dense:35`, among `rejected` units whose realised exposure is
`proposal_only`, the include rate exceeds the include rate of `rejected`
units under `full` by **≥ +0.15**, with cluster p < 0.05, in **at least two
of the carried deciders**, and the same contrast under `recency:35` is
smaller → the candidate is worth a preregistered confirmation (fresh corpus,
a `reinstated` status, more policies and budgets, a prospective power check).
Otherwise → recorded as *not pursued*.

No SESOI, no equivalence reading, no claim. `prospective_design_check.py
--units 96 --clusters 36 --sesoi 0.10` returns power 0.56 and
P(CI inside ±SESOI | true 0) = 0.27: this design cannot support an
equivalence conclusion and none will be drawn from it.

## Files

`lineage_e16.py`, `test_lineage_e16.py`, `e16_preflight.py`,
`e16_zombie_screen.py`, `e16_analysis.py`; outputs
`results/e16_<model>_<policy>_o<offset>.csv/.json` and
`results/e16_preflight.csv`. Nothing in E1–E14's code or files changes.

---

## Outcome

**Stage 1, partial (2 of 3 deciders), run 2026-09-03, read 2026-09-05.
Decision: NOT PURSUED. Exploratory; nothing here is a claim.**

Run: `--policy full --offset 0`, 144 dialogues x 384 unit rows per decider,
temperature 0, corpus hash `70f136a47f5779c8` asserted at start.
`qwen2.5:14b-instruct` was **not run** (see "The 14B arm" below).

### Include rate per status

| decider | parse | accepted | proposed | rejected | never |
|---|---|---|---|---|---|
| llama3.2:3b | 1.000 | 96/96 = 1.000 | 95/96 = 0.990 | 17/96 = **0.177** | 62/96 = **0.646** |
| qwen2.5:3b-instruct | 1.000 | 94/96 = 0.979 | 95/96 = 0.990 | 42/96 = **0.438** | 49/96 = **0.510** |

### Paired contrasts (mean, cluster p, 95 % CI)

`p = 0.0000` is the reader's output at 20 000 sign-flip reps, i.e. p < 1/20 000.

| contrast | llama3.2:3b | qwen2.5:3b-instruct |
|---|---|---|
| rejected - never | -0.469, p 0.0000, [-0.589, -0.340] | -0.073, p 0.358, [-0.196, +0.054] |
| rejected - proposed | -0.813, p 0.0000, [-0.888, -0.731] | -0.552, p 0.0000, [-0.656, -0.443] |
| accepted - rejected | +0.823, p 0.0000, [+0.747, +0.895] | +0.542, p 0.0000, [+0.432, +0.656] |
| proposed - never | +0.344, p 0.0000, [+0.221, +0.468] | +0.479, p 0.0000, [+0.389, +0.570] |
| accepted - never | +0.354, p 0.0000, [+0.239, +0.474] | +0.469, p 0.0000, [+0.374, +0.568] |

### Stage-1 gates

| gate | threshold | llama3.2:3b | qwen2.5:3b-instruct |
|---|---|---|---|
| parse rate | >= 0.95 | 1.000 PASS | 1.000 PASS |
| accepted include | >= 0.80 | 1.000 PASS | 0.979 PASS |
| never include | <= 0.50 | 0.646 **FAIL** | 0.510 **FAIL** (49/96, by one unit) |
| accepted - rejected | >= +0.10 | +0.823 PASS | +0.542 PASS |

Both deciders fail the base-rate gate and are **not carried to stage 2**.

### Reading A (full-context zombie)

`rejected - never` is negative for both deciders: strongly so for llama3.2:3b
(-0.469) and a null for qwen2.5:3b-instruct (-0.073, p 0.358). Prediction (1)
of candidate S-O -- a rejected constraint carried above the never-stated base
rate -- is **not supported at full context** in either decider. The direction
is the opposite one. Descriptive only, as declared.

### Why the base-rate gate failed -- a fault in this screen, not a result

Diagnostic computed after the fact and **not** part of the declared reader;
`e16_analysis.py` was not modified. The frozen plan instruction, reused here
for comparability with E1-E14, *enumerates the whole action vocabulary in the
prompt* (6 identifiers per instance, all 36 instances). A never-mentioned
action is therefore still an offered menu item, and the floor under the
"never" rate is roughly |plan| / |vocab|:

| decider | mean \|plan\| | \|vocab\| | menu chance | observed never |
|---|---|---|---|---|
| llama3.2:3b | 4.23 | 6 | 0.705 | 0.646 |
| qwen2.5:3b-instruct | 3.55 | 6 | 0.592 | 0.510 |

The observed `never` rate sits just *below* menu chance in both deciders. The
`never <= 0.50` gate was set as though "never mentioned" bought substantial
exclusion; given this prompt it buys almost none, and the gate was close to
unreachable before the first call. The gate is doing its job -- it is telling
us `rejected - never` was measured against a near-saturated baseline and is
not interpretable as a zombie rate.

Against the same chance line the deciders **obey rejections**: `rejected` is
0.177 vs 0.705 chance (llama) and 0.438 vs 0.592 (qwen-3b), and
`accepted - rejected` is +0.823 / +0.542. That is the precondition the
orphaning mechanism needs in order to have something to break -- so the
retrieval half, prediction (3), is untested rather than refuted.

### The 14B arm

`qwen2.5:14b-instruct` stage 1 was started on 2026-09-05 and stopped by the
author before any output was written; no partial artifact exists. It is not
needed for the decision. Reading B requires the effect in **at least two of
the carried deciders**; two of the three eligible deciders have already failed
a stage-1 gate, so at most one decider can be carried and the pursuit rule is
unsatisfiable whatever the 14B does. The arm would add descriptive
completeness to Reading A (the size contrast) and nothing else.

### Decision

**Stage 2 is not run. Candidate S-O is recorded as NOT PURSUED by this
screen.** The declared rules were not altered to rescue it, and no equivalence
or absence conclusion is drawn (the design cannot support one: power 0.56).

What this screen does *not* establish: that zombie constraints do not exist.
It establishes that *this* corpus cannot measure them, because its
never-stated baseline is a menu-selection rate. Any redesign would have to
remove the enumerated vocabulary from the plan instruction -- which breaks
comparability with E1-E14 and would need a fresh preregistration, a fresh
prior-art gate with web search (the 2026-09-03 gate ran without it), and a
prospective power check. That is a new screen, not a continuation of this one.

### Files produced

`results/e16_llama32-3b_full_o0.csv/.json`,
`results/e16_qwen25-3b-instruct_full_o0.csv/.json`. Frozen artifacts
untouched: `verify_claims.py` 167 verified / 0 mismatched / 4 unverifiable,
113 tests over 15 suites, both re-run 2026-09-05.
