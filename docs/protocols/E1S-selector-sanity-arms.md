# E1-S — the selector sanity arms the plan requires and E1 never ran

Declared 2026-09-11 with **zero outcomes**. Diagnostic, not a novelty candidate;
it does not enter the ledger. It closes a gap in the compulsory part of the
brief: `docs/plan.md` ("The diagnostic arms — controls, never headline results")
lists four arms with expected values, and `docs/research-design.md` §6 repeats
them. E1 (`e1_landscape.py`, tag `selector-protocol-v1`) ran the five scored
selectors plus the `oracle` diagnostic. The `full` ceiling, the `last-message`
floor and the `sabotage` selector were never run. This runs them.

## 1. What is run — nothing new except the arms

Everything is E1 as frozen: `run_incident.main` on the single `INCIDENT`
scenario, `TURNS = 10` generated turns after the seeded opening, both agents at
temperature 0, finalisation under the same context policy as the dialogue,
history budget `W = 250` words with current-message separation ON, the
programmatic evaluator (`constraint_recall`, `deterministic_success`), the
literal source-coverage check (`retrieval_recall`), the secondary judge on
`llama3.2:3b`. Model `llama3.2:3b` throughout. Three repeats per arm, as in E1.

| arm | construction | code |
|---|---|---|
| `full` | no trimming at all; not budget-matched | `FullHistory()` |
| `last` | system prompt + the current message only; `W = 0` | `RecencyBudget(0)` |
| `sabotage` | every planted source message excluded from the candidate pool; the budget is then filled by recency | `SabotageBudget(W, SOURCE_TEXTS)` (new, `context.py`) |

`SabotageBudget` is the oracle's mirror. Like the oracle it is told which message
texts carry the planted constraints and can only return messages already in the
dialogue (`test_context.py` asserts it never returns a source, never overspends
and never injects). It is a diagnostic, not a selector.

Runs go to `transcripts/e1/{arm}_r{n}.json`, rows to `results/e1_sanity.csv`,
the summary to `results/e1_sanity_summary.csv`. They are **never pooled** with
`results/e1_runs.csv`. Mock runs write `*_mock` files only.

Budget: 9 runs. Run one at a time in the foreground
(`python e1_landscape.py --sanity --only ARM --repeat N`); a rerun of the same
arm and repeat replaces its row and is recorded here as a rerun.

## 2. Predictions — the plan's values, verbatim, and how each will be read

From `docs/plan.md` (arm table) and `docs/research-design.md` §6. Reference
values from E1: recency 0.5714, random 0.8095, bm25 0.6190, dense 0.7619,
fusion 0.7619; oracle diagnostic 0.8571; all `parse_rate` 1.0.

| arm | plan's expectation | read as |
|---|---|---|
| `full` | `constraint_recall` ≥ 0.80 | **P1** holds if mean ≥ 0.80. If it does not, the ceiling assumption behind the whole arm table is wrong for this scenario and every budgeted arm is being compared to a ceiling that does not exist. |
| `last` | ≤ 0.50 | **P2** holds if mean ≤ 0.50. If it does not, the scenario leaks its constraints through the last message alone and the budget is not doing the work. |
| `sabotage` | ≈ 0 | **P3, checked in two parts.** (a) `retrieval_recall` must be exactly 0.0 in every run: this is construction, not a finding, and a non-zero value means the arm is broken. (b) `constraint_recall`: the plan writes "≈ 0" and then says "if a selector built to fail does not score near zero, the evaluator is not measuring what the report claims". The honest reading rule, fixed now: if sabotage's mean `constraint_recall` ≤ 0.20, P3 holds as written. If it lands near recency's 0.5714 (within ±0.15) or higher, the plan's expectation was written for *retrieval* recall and does not transfer to *constraint* recall on this scenario, because the dialogue relays constraints forward in the agents' own words (the point `evaluate.source_coverage` already makes). In that case the finding is stated as: **`constraint_recall` has a retrieval-independent floor of about X on this scenario, and the band a retriever can actually move is [sabotage, oracle]**. That is a limit on what E1's numbers mean, and it is reported as such, not explained away. |

No outcome from this block changes E1's numbers, tunes any selector, or enters
the novelty ledger. Its only downstream use is to say, with evidence, what the
E1 metric can and cannot attribute to retrieval.

## 3. Validity

`parse_rate` = 1.0 in every arm (E1 had 1.0 everywhere; a parse failure is a
format failure and is reported, not scored). `retrieval_recall(sabotage)` = 0.0
in every run. `retrieval_recall(full)` = 1.0 in every run. Any breach is a
process failure recorded below before any reading.

## 4. Outcome

_(empty at declaration)_
