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

*Pending. Zero diagnostic calls at the time of this commit.*
