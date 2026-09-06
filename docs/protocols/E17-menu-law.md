# E17 — does pinning plan length restore 1/|vocab| scaling?

**INSTRUMENT STUDY. Declared 2026-09-06 with zero outcomes. Not a screen, not
preregistered research, not a claim about the world. It exists to ESTABLISH OR
KILL one specific thing, and killing it is a fully acceptable outcome that
will be recorded as such.**

## What it settles

The 2026-09-06 measurement gate (`docs/E16-CANDIDATES.md`) found candidates
N-1 and N-3 pre-empted or surrounded. One component was **not** found anywhere:

> **Elasticity.** \|plan\| is *endogenous* to \|vocab\|. Doubling the menu
> 6 → 12 cut per-item chance by only ~22 % (qwen 0.592 → 0.455) and ~21 %
> (llama 0.705 → 0.559), not 50 %, because the model lengthened its plan
> (×1.54, ×1.59). If real, **normalising an adherence rate by action-space
> size does not fix the confound**, because the numerator moves with the
> denominator.

Evidence so far is three menu sizes, two deciders, one corpus, and
\|plan\| **observed, never controlled** — which is exactly why the E16 menu
diagnostic returned UNINFORMATIVE. E17 controls it by instruction.

## Design — 3 × 2, fully crossed

| \|vocab\| | composition |
|---|---|
| 6 | the instance's own actions |
| 12 | + 6 authored in-domain distractors (`EXTRA_ACTIONS`) |
| 24 | + 18 authored in-domain distractors (`EXTRA_ACTIONS_2`) |

| length | instruction |
|---|---|
| `free` | the frozen plan instruction, unmodified |
| `pin4` | one sentence added: ``` `actions` must contain exactly 4 identifiers.``` |

`free`/6 **is** E16 stage 1 and the menu diagnostic's base arm; `free`/12 is
its wide arm. Both are re-read, not re-run. Four new cells per decider
(576 calls): `free`/24, `pin4`/6, `pin4`/12, `pin4`/24.

Ten gates in `test_e17_menu_law.py`, all passing before any call. The
load-bearing two: `free`/6 reproduces `lineage_bench.plan_instruction` byte for
byte, and `pin4` differs from `free` by **exactly one line** — so the length
manipulation is not confounded with a wording change.

## The decisive comparison

Under `pin4`, \|plan\| is fixed by instruction at 4, so menu chance is
**4/\|vocab\| = 0.667 / 0.333 / 0.167** — a clean 4× fall from 6 to 24.

Applying the ratio band the menu diagnostic observed (never ÷ chance ∈
[0.84, 1.03], centre ≈ 0.92):

| \|vocab\| | chance under `pin4` | H_menu predicts `never` | H_base predicts |
|---|---|---|---|
| 6 | 0.667 | **0.56 – 0.69** | ≈ 0.5, flat |
| 12 | 0.333 | **0.28 – 0.34** | ≈ 0.5, flat |
| 24 | 0.167 | **0.14 – 0.17** | ≈ 0.5, flat |

## Read rule, fixed before the first call

Per decider:

- **ELASTICITY ESTABLISHED** if all three hold —
  (a) in `free`, mean \|plan\| rises monotonically with \|vocab\| (6 → 12 → 24);
  (b) in `pin4`, mean \|plan\| is approximately constant across \|vocab\|
      (every cell within ±15 % of 4.0);
  (c) in `pin4`, `never` falls from \|vocab\| 6 to 24 by a factor **≥ 2.5×**
      (chance falls 4×; slack allowed for the ratio band).
- **MENU ACCOUNT REFUTED** if (b) holds but `never` in `pin4` falls by
  **< 1.5×** from 6 to 24 — i.e. with plan length genuinely fixed the rate does
  not track the menu. The whole line dies here and is recorded as dead.
- Anything else is **AMBIGUOUS**, recorded as ambiguous. No fourth reading
  will be invented after the numbers are seen.

**Validity, per cell.** Parse rate ≥ 0.95, or the cell is void.

**Compliance, `pin4` only.** Report the fraction of plans containing exactly 4
identifiers. If mean \|plan\| in a `pin4` cell falls outside [3.4, 4.6], the
model did not obey the length instruction, condition (b) fails, and **the
comparison is void for that decider** — reported, not worked around. This is a
real risk at 3B and is declared as a possible outcome now.

**Inference.** 96 `never` units per cell, paired by (instance, constraint),
clustered by instance; instance-level bootstrap CIs, 2 000 reps, seed 20260906.

## Deciders

`llama3.2:3b` and `qwen2.5:3b-instruct` (both have the two `free` cells
already). Extended to `qwen2.5:7b-instruct` and `qwen2.5:14b-instruct` only if
the 3B result is not void — scale is secondary here.

## What cannot follow from this

Nothing about zombie constraints, retrieval, or any candidate; S-O and S-E stay
retired. A positive result does **not** by itself constitute novelty — the
2026-09-06 gate rated N-1 SURROUNDED, and establishing the elasticity would at
most restore one unfound component. Any move toward a claim requires a fresh
adversarial prior-art gate **with web search** on the elasticity specifically.

## Files

`e17_menu_law.py`, `test_e17_menu_law.py`; outputs
`results/e17_<model>_v<size>_<length>_o0.csv/.json`. Nothing in E1–E14, E16 or
the menu diagnostic changes.

---

## Outcome

*Pending. Zero E17 calls at the time of this commit.*
