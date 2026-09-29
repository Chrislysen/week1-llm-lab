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
