# E16 menu diagnostic — is the `never` base rate a menu-selection rate?

**DIAGNOSTIC, NOT A SCREEN. Declared 2026-09-06 with zero outcomes. It tests a
claim this repository made about its own instrument, not a claim about the
world. It bears on no candidate: S-O is retired and stays retired whatever
this returns.**

## What is being tested, and why it matters

On 2026-09-05 the Outcome section of `docs/protocols/E16-zombie-screen.md`
explained why E16's stage-1 `never <= 0.50` gate failed, like this:

> the frozen plan instruction enumerates the whole action vocabulary, so an
> action never mentioned in the dialogue is still an offered menu item, and the
> `never` include rate floors at about |plan| / |vocab|

with this table:

| decider | mean \|plan\| | \|vocab\| | menu chance | observed `never` |
|---|---|---|---|---|
| llama3.2:3b | 4.23 | 6 | 0.705 | 0.646 |
| qwen2.5:3b-instruct | 3.55 | 6 | 0.592 | 0.510 |

**That was computed after the fact, from a single vocabulary size.** Two
readings fit those numbers equally well:

- **H_menu.** The `never` rate is mostly a menu-selection artefact. The model
  emits a roughly fixed number of actions and the offered list sets the
  per-identifier probability. Change \|vocab\|, and the `never` rate moves
  with 1/\|vocab\|.
- **H_base.** The `never` rate is a genuine content judgement — "does this
  case need this action?" — that happens to land near 0.5. Change \|vocab\|,
  and it barely moves.

The consequence is not academic. Under H_menu the gate was near-unreachable
before the first call, and the recorded lesson stands: **no future design may
reuse this plan instruction when it needs a never-stated base rate.** Under
H_base that lesson is wrong, was written into `docs/RESUME.md` and into the
project memory on 2026-09-05, and must be struck.

## Design

The corpus, dialogues, statuses, rotations, decider system prompt, validator,
parse/retry, temperature 0 and full context are all held fixed. `lineage_e16.py`,
`lineage_bench.py` and `e16_zombie_screen.py` are not modified — E16's runner
stays byte-identical now that its outcomes are recorded.

**Only the length of the identifier list changes.**

| arm | \|vocab\| | composition | status |
|---|---|---|---|
| `narrow` | 2–3 | the instance's required-constraint actions only | to run, secondary |
| `base` | 6 | the instance's own actions | **already run** — this *is* E16 stage 1 |
| `wide` | 12 | the instance's own 6 + 6 authored in-domain distractors | to run, primary |

Distractors are authored per domain (`EXTRA_ACTIONS` in
`e16_menu_diagnostic.py`) so that they are semantically plausible members of
the same incident. A cross-domain distractor would be declined for content
reasons and would confound a menu-size manipulation.

Eleven gates in `test_e16_menu_diagnostic.py`, all passing before any call.
The load-bearing one is `test_base_arm_is_the_frozen_instruction_verbatim`:
the diagnostic compares the new `wide` arm against **already-collected**
stage-1 data, which is only legitimate if `menu_plan_instruction` with the
base vocabulary reproduces `lineage_bench.plan_instruction` byte for byte. It
does. Also enforced: no distractor identifier or its prose form occurs in any
of the 144 dialogues; narrow ⊆ base ⊆ wide; every unit action is present in
every arm.

## Point predictions, fixed before the first call

If mean \|plan\| is unchanged by widening, H_menu predicts the `never` rate
falls by the ratio of vocabulary sizes, 6/12:

| decider | base `never` | H_menu predicts at \|vocab\|=12 | H_base predicts |
|---|---|---|---|
| llama3.2:3b | 0.646 | **0.32 – 0.36** | ≳ 0.55 |
| qwen2.5:3b-instruct | 0.510 | **0.26 – 0.30** | ≳ 0.43 |

## Read rule, fixed before the first call

Per decider, comparing the `wide` arm against that decider's `base` arm:

- **H_menu supported** if `never_wide <= 0.60 * never_base`.
- **H_menu refuted, H_base supported** if `never_wide >= 0.85 * never_base`.
- Anything between is **ambiguous** and is recorded as ambiguous. No third
  reading will be invented after the numbers are seen.

**Validity, per arm.** Parse rate ≥ 0.95 and `accepted` include rate ≥ 0.80,
or the arm is void and is reported as void.

**Informativeness.** If mean \|plan\| in the `wide` arm is more than 25 %
larger than in `base`, the model is scaling its plan with the menu, the
1/\|vocab\| arithmetic does not apply, and **the test is uninformative** —
that is a real possible outcome and will be recorded as such, not massaged.

**Competition check.** Mean number of authored distractors appearing in a
`wide` plan. If that is ≈ 0 the distractors were never live options, the menu
did not actually widen in the model's eyes, and the test is weak. Recorded
either way.

**Secondary, direction only.** The `narrow` arm (\|vocab\| 2–3) should push
the `never` rate *up* under H_menu. No numeric threshold is set, because
\|plan\| is capped by \|vocab\| there and the arithmetic is not clean.

**Inference.** Rates are means over 96 `never` units per decider, paired by
(instance, constraint) as in E16 and clustered by instance; instance-level
bootstrap CIs, 2 000 reps, seed 20260906.

## What cannot follow from this

No claim about models, about zombie constraints, or about retrieval. This
decides one question about one prompt in one repository's benchmark, and it
can only confirm or strike a methodological lesson already written down. It is
not preregistered research and will not be presented as such.

## Files

`e16_menu_diagnostic.py`, `test_e16_menu_diagnostic.py`; outputs
`results/e16menu_<model>_<arm>_o0.csv/.json`. Nothing in E1–E14, and nothing
in E16's own code or results, changes.

---

## Outcome

**Run 2026-09-06. Six arms, 720 decider calls (576 new + the 288-call base arm
re-read from E16 stage 1). Declared verdict: UNINFORMATIVE in both deciders.
The secondary direction test came out as H_menu predicts. A post-hoc account
fits all six arms and is recorded as a hypothesis, not a finding.**

Corpus hash `70f136a47f5779c8` asserted at every start. Parse rate 1.000 in
all six arms. Frozen state re-verified after the runs: `verify_claims.py`
167 / 0 / 4, 124 tests.

### All six arms

| decider | arm | \|vocab\| | \|plan\| | chance | `never` | never/chance | `rejected` | `accepted` | acc−rej | distractors used |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen2.5:3b-instruct | narrow | 2.75 | 2.16 | 0.785 | 0.656 | 0.84 | 0.479 | 1.000 | +0.521 | – |
| qwen2.5:3b-instruct | base | 6 | 3.55 | 0.592 | 0.510 | 0.86 | 0.438 | 0.979 | +0.542 | – |
| qwen2.5:3b-instruct | wide | 12 | 5.46 | 0.455 | 0.469 | 1.03 | 0.531 | 0.990 | +0.458 | 1.88 |
| llama3.2:3b | narrow | 2.75 | 2.53 | 0.919 | 0.917 | 1.00 | 0.646 | 0.990 | +0.344 | – |
| llama3.2:3b | base | 6 | 4.23 | 0.705 | 0.646 | 0.92 | 0.177 | 1.000 | +0.823 | – |
| llama3.2:3b | wide | 12 | 6.71 | 0.559 | 0.490 | 0.88 | 0.260 | 0.969 | +0.708 | 3.12 |

### The declared verdict

**UNINFORMATIVE, both deciders**, by the informativeness clause fixed before
the first call: mean \|plan\| grew **×1.54** (qwen) and **×1.59** (llama),
against a declared ceiling of ×1.25. The model does not hold plan length
fixed while the menu grows, so the 1/\|vocab\| arithmetic that both declared
hypotheses assumed does not apply and the primary comparison cannot separate
them. That clause existed precisely to stop this being over-read, and it fired.

**Neither declared hypothesis survives, because they shared a false premise.**

| | predicted `never` at \|vocab\|=12 | observed | |
|---|---|---|---|
| qwen — H_menu | 0.26 – 0.30 | 0.469 | failed |
| qwen — H_base | ≳ 0.43 | 0.469 | satisfied |
| llama — H_menu | 0.32 – 0.36 | 0.490 | failed |
| llama — H_base | ≳ 0.55 | 0.490 | failed |

H_menu is wrong in both. H_base survives in one of two. The data refute the
premise both were built on — that \|plan\| is a fixed budget — rather than
adjudicating between them.

**Secondary test (direction only, declared):** under H_menu the `narrow` arm
should push `never` *up*. It does, in **both** deciders: 0.510 → 0.656 (qwen)
and 0.646 → 0.917 (llama).

### A post-hoc account — NOT preregistered, NOT a finding

Across all six arms the `never` rate sits close to menu chance:
never/chance ∈ **[0.84, 1.03]**, mean ≈ 0.92, over a 4.4× range of vocabulary
size and a 2× range of chance. `never` moves monotonically with chance in both
deciders. The relation that fits is

    never  ≈  0.92 × |plan| / |vocab|,   with |plan| itself elastic in |vocab|

This was not declared in advance and no inference is drawn from it. It is a
hypothesis for a design that **fixes \|plan\| explicitly** — which is a new
prompt and a new declaration, and is not run here.

### What this does to the 2026-09-05 lesson

The lesson written into `docs/protocols/E16-zombie-screen.md`, `docs/RESUME.md`
and the project memory on 2026-09-05 said the `never` rate "floors at about
\|plan\| / \|vocab\|".

- **Its arithmetic form was wrong and is corrected.** It was stated as though
  \|plan\| were a constant of the model. \|plan\| is a function of \|vocab\|,
  so "halve the vocabulary and you halve the rate" does not hold — doubling
  \|vocab\| from 6 to 12 moved chance only 0.592 → 0.455 (qwen, −23 %) and
  0.705 → 0.559 (llama, −21 %), not −50 %.
- **Its practical conclusion stands and is strengthened.** A never-stated base
  rate cannot be recovered from this plan instruction by choosing a vocabulary
  size, because plan length compensates. The rate is pinned near chance across
  every menu size tried.

### The corollary that matters most, and it is uncomfortable

Applying **E16's own stage-1 gates** to the `wide` arm:

| decider | \|vocab\| | parse | accepted | `never` ≤ 0.50 | acc−rej | all four |
|---|---|---|---|---|---|---|
| qwen2.5:3b-instruct | 6 | pass | pass | **0.510 FAIL** | pass | **FAIL** |
| qwen2.5:3b-instruct | 12 | pass | pass | **0.469 pass** | pass | **PASS** |
| llama3.2:3b | 6 | pass | pass | **0.646 FAIL** | pass | **FAIL** |
| llama3.2:3b | 12 | pass | pass | **0.490 pass** | pass | **PASS** |

**Both deciders fail every gate at \|vocab\| = 6 and pass every gate at
\|vocab\| = 12.** The stage-1 gate that ended the E16 screen was measuring a
parameter of the prompt that nobody varied, not a property of the deciders.
Had the benchmark listed twelve identifiers instead of six, E16 would have
carried both deciders to stage 2.

`rejected − never` also moves with the menu: qwen **−0.073 → +0.062**
(sign flip, into the direction S-O predicted) and llama **−0.469 → −0.229**.

**This does not revive S-O, and nothing here should be read as reviving it.**
S-O is retired because its behavioural half is closed by published prior art
(arXiv:2608.12599) and its mechanism half by arXiv:2606.22528 / 2608.11242 /
2604.20911 — an argument that does not depend on any gate. The qwen sign flip
is +0.062 in one decider, from a diagnostic that was not designed to test it,
with no permutation test, no correction, and no preregistration. It is
recorded because concealing it would be worse, not because it means anything.

### The trade-off a future design has to pay

Widening the menu buys base-rate headroom and **costs discrimination**:
acc−rej falls +0.542 → +0.458 (qwen) and +0.823 → +0.708 (llama), and llama's
`accepted` and `proposed` both slip below ceiling (1.000 → 0.969,
0.990 → 0.917). A design cannot simply widen the menu until the base rate
behaves; it trades away the signal it needs.

### Limits

Two deciders, one corpus, three vocabulary sizes, temperature 0, full context.
\|plan\| was **observed, never controlled** — the obvious next design fixes it
and is not run. The `narrow` arm is degenerate by construction (\|plan\| is
capped by \|vocab\|) and carries a direction only. The post-hoc relation is
fitted to six points from two models and must not be quoted as a law. No
claim about models, about zombie constraints, or about retrieval follows.

### Files produced

`results/e16menu_{qwen25-3b-instruct,llama32-3b}_{wide,narrow}_o0.csv/.json`.
The `base` arm is E16 stage 1, unmodified. Nothing in E1–E14, and nothing in
E16's own code or results, changed.

### Operational note

Two background runs of the `llama3.2:3b narrow` arm were killed mid-flight by
the task runner (at 100/144 and 93/144); no partial artifact was written
either time. The arm completed in the foreground. Nothing was lost and no
result in this file comes from a partial run.


---

### Within-arm check — never-unit vs authored distractor. EXPLORATORY, zero new calls

In the `wide` arm the never-status unit and the six authored distractors are
**both unmentioned in the dialogue**. If "never" carries no content signal,
the two should be picked at the same rate. Computed from data already
collected; not declared in advance.

| decider | per-distractor | never-unit | never ÷ distractor | rejected | rejected ÷ distractor |
|---|---|---|---|---|---|
| llama3.2:3b | 0.520 | 0.490 | **0.94** | 0.260 | **0.50** |
| qwen2.5:3b-instruct | 0.326 | 0.469 | **1.44** | 0.531 | **1.63** |

The deciders come apart, and not in a way any earlier reading showed:

- **llama3.2:3b** treats a never-mentioned *required constraint* exactly like a
  never-mentioned *invented distractor* (0.490 vs 0.520). Its `never` rate
  carries essentially no content signal. But it puts a rejected action at
  **half** the unmentioned baseline — genuine, strong suppression.
- **qwen2.5:3b-instruct** includes a **rejected** action *more often than an
  unmentioned one* (0.531 vs 0.326, ratio 1.63). Against this baseline it is
  not suppressing rejection at all; what mostly drives its inclusion is
  whether the action belongs to the instance's own six.

**Confound, and it is a real one.** The distractors are authored by me and may
simply be less plausible than the benchmark's own actions, which would depress
their rate for content reasons and inflate both ratios. That cannot be
separated here. Two things limit the damage: llama's ratio of 0.94 shows the
distractors are genuinely competitive rather than obviously fake, and llama
used 3.12 of 6 per plan. For qwen (1.88 of 6) the 1.44 gap may be plausibility
rather than content signal, and no weight should be put on it.

Nothing here is a claim, and none of it bears on S-O, which is retired on
prior-art grounds.
