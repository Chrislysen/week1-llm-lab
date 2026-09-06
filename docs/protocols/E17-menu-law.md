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

**Run 2026-09-06. Verdict: AMBIGUOUS in both deciders, by the declared rule.
Both declared hypotheses are wrong. The elasticity line does NOT constitute
novelty and is recorded as closed — see "Why this is not a finding" below.**

`pin4` compliance was total: mean |plan| 4.00 / 4.00 / 4.00 (qwen) and
3.99 / 4.00 / 4.00 (llama), with 99.3–100 % of plans containing exactly four
identifiers. Parse rate 1.000 in every cell. The declared void condition did
not fire; the length manipulation worked exactly as intended.

### Results, plan length pinned at 4

| decider | \|vocab\| | chance | `never` | 95 % CI | never ÷ chance | `rejected` |
|---|---|---|---|---|---|---|
| qwen2.5:3b-instruct | 6 | 0.667 | 0.573 | [0.489, 0.663] | 0.86 | 0.542 |
| qwen2.5:3b-instruct | 12 | 0.333 | 0.427 | [0.337, 0.516] | 1.28 | 0.594 |
| qwen2.5:3b-instruct | 24 | 0.167 | 0.250 | [0.173, 0.333] | 1.50 | 0.521 |
| llama3.2:3b | 6 | 0.666 | 0.562 | [0.475, 0.646] | 0.85 | 0.219 |
| llama3.2:3b | 12 | 0.333 | 0.354 | [0.268, 0.442] | 1.06 | 0.271 |
| llama3.2:3b | 24 | 0.167 | 0.229 | [0.143, 0.323] | 1.38 | 0.417 |

### The declared verdict

| condition | threshold | qwen | llama |
|---|---|---|---|
| (b) `pin4` \|plan\| within ±15 % of 4 | — | YES | YES |
| (c) `never` falls 6→24 | **≥ 2.5×** | **2.29×** | **2.45×** |

Chance falls 4.00× in both. **AMBIGUOUS in both deciders** — above the 1.5×
refutation line, below the 2.5× establishment line. Both are near-misses on a
threshold I set myself before seeing any data. **The threshold is not moved,
and no fourth reading is invented**; that was declared in advance precisely to
stop this.

### Both declared hypotheses are wrong

Fitting `never ∝ chance^e` over the three pinned cells:

- qwen2.5:3b-instruct **e = 0.60**
- llama3.2:3b **e = 0.65**

H_menu predicted e = 1 (rate tracks chance); H_base predicted e = 0 (rate
flat). Reality is in between and **replicates across two model families**.
`never ÷ chance` rises monotonically in both deciders (0.86 → 1.28 → 1.50;
0.85 → 1.06 → 1.38): as the menu grows the model does preferentially keep the
instance's own actions over distractors, but far too weakly to hold the rate
steady.

### What that means for measurement, stated without inflation

With plan length **held fixed by instruction**, changing only the number of
offered identifiers moves the measured inclusion rate for an unmentioned
action by **2.29× (qwen) and 2.45× (llama)**. Action-space size is a free
parameter the benchmark author picks.

And there is no simple repair. Raw rates are biased by menu size; dividing by
menu chance **over-corrects**, because the ratio itself climbs with \|vocab\|.
The two obvious analyses are biased in opposite directions.

### Why this is not a finding — the gate, run before writing any of it up

The phenomenon is **a classical choice-set-size effect**: adding alternatives
changes relative selection probabilities sub-proportionally. That is a
violation of **Luce's choice axiom / independence of irrelevant alternatives**
(Luce, 1959), the thing nested logit and mixed logit were built to model, with
a literature stretching back six decades. For LLMs specifically, IIA violation
is already studied in the preference/alignment setting (**arXiv:2312.01057**
*RLHF and IIA: Perverse Incentives*; **arXiv:2501.09254** *Clone-Robust AI
Alignment*; **arXiv:2410.15168**).

An exponent of ~0.6 in plan generation is an **instance of a known class**, not
a discovery. Combined with the 2026-09-06 measurement gate — which rated N-1
SURROUNDED and N-3 PRE-EMPTED — the honest verdict is:

> **The elasticity line yields a real, replicated, quantitative regularity
> about this instrument, and no novelty. It is closed as a novelty candidate.**

What survives is *methodological*, and it is worth keeping: for this benchmark
family, the number of identifiers offered in the plan instruction is a
first-order determinant of every rate the instrument reports, and neither raw
nor chance-normalised comparison is valid across it.

### What cannot follow

Nothing about zombie constraints, retrieval, or any retired candidate. The
exponent is fitted to three points per decider on one corpus at one pinned
length; it is not a law and must not be quoted as one. A pinned length of 4
was chosen once and never varied — the exponent may itself depend on it.

### Files

`results/e17_{qwen25-3b-instruct,llama32-3b}_v{6,12,24}_pin4_o0.csv/.json`.
`free`/6 and `free`/12 are read from E16 stage 1 and the E16 menu diagnostic
(prompt identity enforced by `test_e17_menu_law.py`). `free`/24 is running at
the time of this commit and bears only on condition (a), which the E16
diagnostic already established (|plan| rises 3.59 → 5.56 for qwen and
4.25 → 6.71 for llama as |vocab| goes 6 → 12).
