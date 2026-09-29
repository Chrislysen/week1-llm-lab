# Supplementary run at temperature 0.7: declaration

Written and committed **before any supplementary run**, so the predictions
cannot be adjusted to the outcome.

## Why

At temperature 0 the frozen repeats were mostly copies: 12 runs contain only
6 distinct trajectories (`docs/COMP-ANALYSIS.md` §1). This run repeats the
frozen experiment with independent samples. It is **supplementary**. It does not
replace or pool with the frozen results, which stay as they are at tag
`compulsory-baseline-v1`.

## What changes, and what does not

- **Changed:** both agents' temperature, 0 → 0.7.
- **Unchanged:** the scenario, the 10 dialogue turns, the budgets, the final-plan
  step with one retry, the deterministic evaluator, and the judge (still at temperature 0).
  The runs go through the same `run_incident.main` as the frozen runs.
- **Added:** `recency-0` as a floor control, the counterpart of the full-history ceiling.
- **Design:** 5 conditions (recency-0, 4, 8, 12, full) × 5 repeats = 25 runs.
  Evidence goes to `transcripts/supp_t07/`, tables to `results/supp_t07/`.

## Predictions

Each is checked in code by `supplementary.py --summarise`.

| id | prediction | what it tests |
|---|---|---|
| P1 | at least 4 of 5 dialogues are distinct in every condition | the repeats are now real samples |
| P2 | C5 is broken in at least 3 of 5 full-history runs | C5 is a plan-writing failure, not forgetting |
| P3 | C1 or C2 is broken in more recency-4 runs than full-history runs | the earliest rules are the ones a small window loses |
| P4 | mean recall of recency-0 is below mean recall of full history | context helps at all |

**No prediction** is made about the order of recency-4, 8, 12 and full. The frozen
order (8 > 4 > 12 = full) came from single trajectories and is only described.

**Disclosure:** P2 and P4 are informed by runs already seen. The frozen
experiment showed C5 broken in 11/12. The failure analysis ran one
window-0 case at temperature 0 (recall 0.571) and one rules-in-system-prompt
case (C5 still broken). P1 and P3 are not informed by any temperature-0.7 data.

---

## Results (added after the run; nothing above this line was changed)

25 runs, 2026-09-29. Tables: `results/supp_t07/summary.csv`, `runs.csv`,
`predictions.csv`. Figure: `results/supp_t07/fig_recall_t0_vs_t07.png`.

![Recall per run, frozen vs supplementary](../results/supp_t07/fig_recall_t0_vs_t07.png)

| condition | distinct dialogues | mean recall (sd) | success | C1 | C2 | C4 | C5 | C6 | C7 | invented actions |
|---|---|---|---|---|---|---|---|---|---|---|
| recency-0 (floor) | 5/5 | 0.629 (0.128) | 0/5 | 3 | 3 | 1 | 4 | 0 | 2 | 0/5 |
| recency-4 | 5/5 | 0.457 (0.256) | 0/5 | 3 | 4 | 1 | 2 | 2 | 0 | 2/5 |
| recency-8 | 5/5 | 0.857 (0.101) | 1/5 | 1 | 1 | 0 | 2 | 1 | 0 | 2/5 |
| recency-12 | 5/5 | 0.800 (0.128) | 1/5 | 2 | 3 | 0 | 2 | 0 | 0 | 2/5 |
| full history | 5/5 | **0.943** (0.078) | **3/5** | 0 | 0 | 0 | 2 | 0 | 0 | 2/5 |

C3 was never broken. Violation counts are out of 5 runs.

### Predictions

| id | prediction | result |
|---|---|---|
| P1 | ≥ 4 of 5 dialogues distinct per condition | **holds** (5/5 in every condition) |
| P2 | C5 broken in ≥ 3 of 5 full-history runs | **fails** (2/5) |
| P3 | C1/C2 broken in more recency-4 runs than full | **holds** (4/5 vs 0/5) |
| P4 | recency-0 mean recall below full | **holds** (0.629 vs 0.943) |

### What this changes

1. **With independent samples, full history is best, not worst.** The frozen
   ordering (8 > 4 > 12 = full) came from single temperature-0 trajectories. At
   temperature 0.7, full history has the highest mean recall and the most
   successes (3/5). The full-history runs never overlap the recency-4 runs (lowest
   full run 0.857, highest recency-4 run 0.571).
2. **Forgetting the earliest rules is real.** C1 and C2 (stated at turn 1) broke in
   3–4 of 5 runs with no context or a 4-message window, and never with full history.
3. **C5 is hard at every context size, but not always broken.** C5 broke in 2 of 5 runs
   in every condition that had context, including full history, and 4 of 5 with none. P2
   predicted at least 3 of 5 with full history and fails. The frozen "11 of 12" overstated how
   reliably C5 breaks. What survives is that C5 breaks at a similar rate however
   much context the plan-writer sees. So the context policy does not
   control it.
4. **A 4-message window did no better than no context at all.** Four of five
   recency-4 plans scored 0.571, the same as four of five recency-0 plans, and
   the fifth never parsed. In these runs a 4-message window added nothing
   measurable over no context.
5. **The judge still does not work.** It said `success: false` in all 25 runs,
   including all 5 plans that were perfect, so it never recognised a correct plan. It gave
   its highest score (5) three times: once to a perfect plan and twice to plans that
   broke two rules each (recency-12 r3: C2, C5; r5: C1, C2).
6. **Self-assessment is still meaningless.** All 24 plans that parsed said `ready: true`.

The one parse failure (recency-4 r2) is a natural retry failure. The first reply had a
`// comment` inside the JSON. The corrected reply removed the comment and lost the
closing brace. Two attempts were used and it was recorded as a parse failure, as designed.
