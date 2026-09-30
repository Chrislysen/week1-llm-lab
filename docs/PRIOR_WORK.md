# Prior work ledger

What in this project is adapted from work that predates the course, what is new,
and where the line falls. Maintained on the `crazy` branch, where the adapted
code lives. The frozen compulsory baseline (`compulsory-baseline-v1`) contains
**none** of it.

---

## OpSem — `github.com/Chrislysen/opsem`

Public, MIT, authored before this course. Paper: *Training-Free Lexical–Dense
Fusion for Conversational-Memory Retrieval* (Lysenstøen, 2026). Not submitted
for credit elsewhere. Reuse raised with the course instructor in writing.

### Adapted, as code

| what | source | lands in | size |
|---|---|---|---|
| Tokenizer discipline — lowercase, `[a-z0-9][a-z0-9\-_']{1,30}`, stopword list, drop < 3 chars | `lme_maxsim.py::_tok` | `retrieval.tokenize` | ~10 lines |
| Okapi BM25 — tf/df/idf, `k1=1.5`, `b=0.75` | `lme_maxsim.py::BM25` | `retrieval.BM25` | ~35 lines |
| Per-query z-normalisation within the candidate set | `tune13_interaction.py::_z` | `retrieval.zscore` | ~6 lines |
| Weighted linear fusion `α·z(bm) + (1−α)·z(dense)` | `tune13_interaction.py` | `retrieval.fuse` | ~2 lines |

### Adapted, as a constant

`ALPHA = 0.40` — OpSem's measured global optimum on LoCoMo, with a broad plateau
across 0.30–0.45 (`analysis_deep.py`). **Fixed a priori and never tuned here.**
OpSem selects α by leave-one-conversation-out CV and explicitly labels the
full-data value an overfit ceiling. This project has one scenario family and so
no CV pool; the honest move is to fix the constant and say so rather than tune it
on the runs being scored.

### Adapted, as methodology only

- Report the regime where the method *stops* helping. OpSem documents a
  LongMemEval-S boundary where the lexical baseline saturates and fusion's gain
  becomes small and non-significant.
- `tune8_adaptive.py`'s null result — a query-adaptive fusion weight failed to
  beat one global constant across 1978 examples — is cited as prior evidence
  against adaptivity, not as a mechanism.

### Deliberately NOT taken, and why

**Session-level retrieval unit** and **turn-level late interaction / max-sim
pooling.**

This is an evidence-based exclusion, not a preference. OpSem's max-sim runs over
the turn vectors *inside a session*; its released bucket data
(`results/analysis-deep-*/analysis.json`) contains **zero** evaluated containers
under 8 turns, and the paper's own mechanism argument is that the late-minus-early
gap grows monotonically with container length because it is a *dilution* effect
(e5-large-v2: +19.4 → +22.4 → +27.1 pp across length buckets). At the message
level there is nothing to pool over — algebraically, max over one element is the
identity. The mechanism has a size precondition this setting does not meet.

Also not taken: leave-one-conversation-out α selection (no CV pool here).

Note further that OpSem itself **credits** turn-level late interaction to
Nano-Memory (Wu et al., 2026) and does not claim it. OpSem's own contribution is
that BM25 fusion adds *over* late interaction.

---

## Argos — `github.com/Chrislysen/Argos`

**Nothing taken.** An adversarial audit of the claim that Argos motivates
adaptive context allocation returned REFUTED at high confidence: its allocator is
a one-shot offline grid search over a memory-capacity constraint, it explicitly
declines to optimise context, and its one conserved-budget non-uniform allocator
lost to a random control with a bootstrap CI excluding zero
(`lab/alloc_e2e.json`: random top-1 0.9674 vs contribution 0.9518).

One methodological lesson carried, no code: **include a random-selection control
arm at equal budget.** That lesson has already paid — see below.

---

## Everything else

`jarvis-cortex`, `solon`, `fleet-command`, `secret-loyalty-probe`, `trusttune`,
`SLO-Guard`, `heimdall-demo`: **no code taken.** Where their ideas influenced the
design (deterministic non-LLM scoring, controls that can fail, budget-parity
reporting, run-validity states), they are reimplemented from scratch for this
course and are visible in `evaluate.py`, `experiment.py` and the test suites.

---

## New for this course

Everything not listed above, including: the incident scenario, both personas,
the seven planted constraints and the hidden evaluator key; the deterministic
evaluator and its falsification tests; the message-level retrieval unit; the
word-budgeted greedy fill with chronological restoration; the frozen query
definitions; integration with the `manage_context` hook; the finalisation and
bounded-retry machinery; the judge; the oracle / sabotage / random controls; the
retrieved-vs-used metric decomposition; and the whole experimental harness.

---

## Where the borrowed lesson already changed the outcome

The Argos-derived insistence on a random control was not decorative. In the
offline selector preflight, **random retrieval recall (0.419) beat both recency
(0.038) and BM25 (0.057)** — the two policies a reader would assume are the
serious ones. Without a random arm, BM25's 0.057 would have been compared only
against recency's 0.038 and could have been written up as a modest win. It is in
fact far below chance.
