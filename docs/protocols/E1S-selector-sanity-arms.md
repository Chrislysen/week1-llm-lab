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

## 4. Outcome — run 2026-09-11, the same day, after `c1b5447`

Nine runs, three foreground calls (one arm each, about 90 s per arm), zero
reruns, zero transport retries. `results/e1_sanity.csv`,
`results/e1_sanity_summary.csv`, `transcripts/e1/{full,last,sabotage}_r{1,2,3}.json`.

**Validity: all checks pass.** `parse_rate` 1.0 in every arm.
`retrieval_recall(sabotage)` = 0.0 in all three runs; `retrieval_recall(full)`
= 1.0 in all three. One run (`full` r2) parsed but invented four action
identifiers outside the menu (`NOTIFY_OPS_AND_DB_TEAM`,
`MONITOR_CLUSTER_PERFORMANCE`, `TEST_API_STABILITY`,
`DOCUMENT_RESULTS_IN_INCIDENT_LOG`); `unknown_actions` is a reported column and
the row stands.

| arm | n | `constraint_recall` per run | mean | `deterministic_success` | `retrieval_recall` | history words | plan's expectation | verdict |
|---|---|---|---|---|---|---|---|---|
| `full` | 3 | 0.8571 · 0.8571 · 0.8571 | **0.8571** | 0/3 | 1.0 | 632 | ≥ 0.80 | **P1 holds** |
| `last` | 3 | 0.5714 · 0.7143 · 0.7143 | **0.6667** | 0/3 | 0.0 | 0 | ≤ 0.50 | **P2 fails** |
| `sabotage` | 3 | 0.8571 · 1.0 · 1.0 | **0.9524** | **2/3** | 0.0 | 247 | ≈ 0 | **P3(a) holds by construction; P3(b) fails** |

For reference, E1's scored arms (never pooled, quoted only): recency 0.5714,
bm25 0.6190, dense 0.7619, fusion 0.7619, random 0.8095; oracle 0.8571; all
with `deterministic_success` 0/3.

**Reading, by the rule fixed in §2.** Sabotage's mean is not ≤ 0.20 and it is
more than 0.15 above recency, so the second reading applies — and it applies in
its strongest form, because sabotage (0.9524) is above the oracle (0.8571) and
above `full` (0.8571). The pre-registered sentence therefore reads:
**`constraint_recall` has a retrieval-independent floor of at least 0.95 on this
scenario, which is above every scored arm and above the oracle, so the band a
retriever can move is empty.** E1's landscape (0.5714 – 0.8095, oracle 0.8571)
sits entirely inside the range spanned by the two arms that were built to
carry *no* source information (0.6667 with no history at all; 0.9524 with every
source message removed). Nothing in E1's ordering can be attributed to
retrieval of the planted source messages. This is a limit on E1, stated as one.

**What the transcripts show the metric is actually measuring.** The generated
turns 6–15 of every run drift away from the incident — standby capacity,
changelogs, deployment scripts, read-only replicas — and do not restate the
constraints; the sabotage context (turns 11–14 plus the current message) carries
none of them, in the literal check or on reading. The plans are nevertheless
near-perfect because the finalisation instruction hands the decider the action
menu (`ISOLATE_NODE RUN_DIAGNOSTICS RUN_BACKUP FAILOVER_API RESTART_DB
RESTORE_TRAFFIC`) and the system prompt carries the brief, and the model's prior
over that menu — backup before restart, failover before restart, traffic last —
already satisfies C3–C7. The `last` arm, with no dialogue at all, produced
`[RUN_DIAGNOSTICS, RUN_BACKUP, FAILOVER_API, RESTART_DB, RESTORE_TRAFFIC]` twice
and failed only C1/C2 (isolate the node before diagnosing it), the one pair
that needs dialogue information. `full`, with all 632 history words, failed C5
(failover before restart) in every run and invented identifiers once: more
drifting dialogue in context pulled the plan *away* from the menu prior.

This is the compulsory-side face of the E17 menu law recorded in
`docs/protocols/E17-menu-law.md`: adherence rates on this scenario are set by
the prompt's action menu, not by what the context policy keeps. It also
explains the two E1 anomalies `docs/research-roadmap.md` records without
explaining them — the random arm scoring highest, and BM25 below recency — as
run-to-run variation in a metric that was not moving with retrieval.

**What this does and does not change.**
- E1's numbers are untouched and still reported as declared; the tag
  `selector-protocol-v1` stands. What changes is the sentence allowed next to
  them: E1 is a landscape of `constraint_recall` under six policies, not
  evidence about retrieval on this scenario.
- The plan's arm table used one expectation ("≈ 0") for two different
  quantities. For retrieval recall it holds by construction (0.0). For constraint
  recall it does not hold on a scenario whose action menu encodes most of its
  constraints, and no scenario-level ceiling can be read from `full` while a
  no-source arm scores above it.
- A scenario on which the compulsory arms *would* separate needs constraints
  the menu cannot carry (which action, not just which order) and generated
  turns that do not drift. That is a scenario change, declared separately if it
  is ever wanted; nothing here is tuned.
- n = 3 per arm, one scenario, temperature 0 with Ollama-level nondeterminism
  (the `last` arm's three runs produced two different plans). The direction is
  not in doubt at this n — both floor arms sit at or above the scored arms —
  but no interval is claimed.
