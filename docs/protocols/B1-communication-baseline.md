# B1 — bounded exploratory baseline: does communication help or harm plan construction?

**Status at declaration: ZERO outcomes. No model call has been made.**
Declared 2026-09-08, before any run.

**This is an EXPLORATORY BASELINE STUDY, not a novelty candidate.** It has not
passed `docs/NOVELTY-GATE.md` and is not claimed to. E27, E28 and C2 remain
closed and are not reopened. Eight instances cannot establish general
superiority, novelty, or a scaling claim. **Every instance here is development
data.**

## Goal

Observe where communication between two agents helps or harms completion of a
task with an independently checkable outcome, and identify **at most one**
unexplained failure worth a separate research assessment.

## 1. Setting (smallest usable; nothing new built)

Existing task family: `lineage_bench.generate_instance` + `lineage_eval.check_plan`.

- **Task.** Read a short dialogue; emit `{"actions": [...], "ready": bool}` — an
  ordered plan over 6 action identifiers satisfying every constraint stated in
  the dialogue.
- **Fresh instances (8).** `salt="agentcom-b1"`, ids `<domain>-<graph>~agentcom-b1`.
  Verified not to collide with the 36 standard instances:
  payments-chain, robotics-fork, pharmacy-join, satellite-diamond,
  brewery-twochain, rail-star, payments-diamond, robotics-twochain.
- **Stable facts, full context.** Exposure `source_only` = lineages
  `("SOURCE", "DISTRACTOR")`. **No supersession message, no corrupted relay** —
  therefore no retraction. No truncation, no steering, no recovery: every call
  receives the whole dialogue.
- **Scoring.** `check_plan(text, instance, constraints=instance.constraints)`.
  Authored constraints are the ground truth *because* no override is exposed;
  `effective_constraints` (which reverses the superseded rule) would be the wrong
  key here and is not used. Primary outcome **`success` = no violated constraint
  AND `ready` is true**. Also recorded: `parsed`, `violations`,
  `constraint_recall`, `unknown_actions`.
- **Independence of scoring.** The scorer is programmatic and receives only the
  plan text and the instance. It never sees the arm label, so it is blind by
  construction. Verified before any run: a reference topological order scores
  `success=True`; its reverse scores `success=False` with 4 violations.

**No new benchmark is built.** If this family had lacked an independent scorer,
the blocker would have been reported instead of running.

**Why an additional run is justified.** The nearest existing records (E16 and
its successors) run a *single* finalisation call per condition on the E16 corpus,
under supersession, and were built to study lineage and revocation — not
multi-agent communication topology, and not with a compute-matched solo arm.
No existing record compares solo / independent / communicating at equal call
count. Those corpora are also development material across nine studies.

## 2. Arms — three configurations, five calls each

Every arm ends with the **same** aggregation prompt emitting the JSON plan, so
scoring is identical throughout.

| arm | calls |
|---|---|
| **solo** | draft₁ → refine₁ → draft₂ → refine₂ → aggregate (one persona; draft₂ does not see draft₁) |
| **independent** | A.draft, B.draft → A.refine (own only), B.refine (own only) → aggregate |
| **communicating** | A.draft, B.draft → A.refine (**sees B's draft**), B.refine (**sees A's draft**) → aggregate |

**The clean contrast is independent vs communicating.** They are identical in
call count, personas, prompts and aggregation; they differ **only** in whether
the refinement prompt contains the peer's draft. That isolates peer-message
access as closely as this harness allows.

**Unavoidable differences, documented.** `solo` additionally differs in persona
identity (one voice, not two). It is a compute-matched reference point, **not**
part of the isolated contrast. Held fixed across all arms: base model, dialogue
text, action vocabulary, tools (none), generation caps, scoring.

## 3. Sampling, limits, logging — fixed before running

- **Model.** `llama3.2:3b`, already configured locally. No paid services.
- **Sampling.** `temperature=0.7` with a **deterministic per-call seed** derived
  from `sha256(instance_id | arm | call_index)`, set on the client before each
  call. Diversity is the point of an ensemble, so temperature 0 would collapse
  the two threads; seeding keeps it reproducible. Seed logged per call.
- **Generation caps.** `num_predict=400` for draft/refine, `300` for aggregate,
  applied identically in every arm.
- **Cost.** Equal call counts do **not** imply equal compute. Actual
  `prompt_tokens` / `completion_tokens` / `seconds` are recorded per call and
  reported per arm.
- **Blocking and order.** All three arms for a given instance run **inside one
  process**. Arm order is **counterbalanced** across instances by a fixed
  rotation of the 6 permutations, and **request position within the process is
  logged** — the E28-C lesson applied at design time rather than after.
- **Logging.** Every call's prompt, response, seed, position, tokens and seconds
  is written to `results/b1_calls.jsonl`; per-arm scored outcomes to
  `results/b1_outcomes.jsonl`. Full trajectories preserved.

## 4. Hard budget cap

**160 model calls total**, counting smoke tests, retries, judges and any
diagnostic follow-up.

| item | calls |
|---|---|
| smoke (1 throwaway instance, salt `agentcom-b1-smoke`, all 3 arms) | 15 |
| main comparison 8 × 3 × 5 | 120 |
| **committed subtotal** | **135** |
| reserve for at most ONE exploratory follow-up | 25 |

If the reserve is exhausted the study stops and reports what it has.

## 5. What will be reported

Task outcomes per arm, actual token cost per arm, and **behaviour, not only
averages**: located cases where a correct intermediate plan becomes wrong, where
an error is corrected, and where aggregation loses information. Observations are
recorded separately from proposed explanations.

At most **one** informative case is followed up within the reserve, and any such
follow-up is **labelled exploratory**.

## 6. What this cannot establish, stated in advance

Not general superiority of any architecture, not novelty, not a scaling claim,
not an effect size for a future confirmatory study. n=8, one model, one task
family, development data throughout. Any hypothesis that survives requires a
**separate gate assessment and fresh confirmatory instances**. If everything
observed is already explained by known results, that is the finding, and the
comparison is retained as engineering evidence.
