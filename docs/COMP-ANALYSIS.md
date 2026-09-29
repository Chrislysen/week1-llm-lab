# Compulsory experiment: detailed analysis

Analysis of the 12 frozen compulsory runs (tag `compulsory-baseline-v1`, branch
`core-frozen`). **Zero new model calls.** `comp_analysis.py` first checks each
transcript is byte-identical to the tagged copy, then derives everything below.
The generated tables are in `results/comp_analysis/tables.md`, with one CSV per
table beside them. Nothing frozen was modified.

Reproduce with `python comp_analysis.py`.

---

## 0. The headline numbers (unchanged from the frozen results)

| condition | runs | mean constraint recall | success | parsed | mean prompt tokens | judge score |
|---|---|---|---|---|---|---|
| recency-4 | 3 | 0.762 | 0/3 | 3/3 | 4 569 | 3, 3, 3 |
| recency-8 | 3 | **0.857** | 0/3 | 3/3 | 6 237 | 3, 3, 3 |
| recency-12 | 3 | 0.714 | 0/3 | 3/3 | 7 186 | 3, 3, 3 |
| full history (ceiling) | 3 | 0.714 | 0/3 | 3/3 | 7 647 | 3, 3, 3 |

No run succeeded. Recall does not rise with context: the 8-message window scored
highest, and full history tied the 12-message window for lowest. The sections below
explain why. The short answer is that most of the failures are not memory failures.

> Provenance note: the commit message on the frozen tag gives recency-4 as recall
> 0.8095, success 1/3, 4 114 tokens. Those numbers are stale. The transcripts and
> `results/summary.csv` agree on **0.7619, 0/3, 4 569**. Use these.

---

## 1. The repeats are not independent

All agents ran at temperature 0. So the three repeats in a condition are mostly
replays, not new samples.

| condition | runs | distinct dialogues | distinct final action lists |
|---|---|---|---|
| recency-4 | 3 | 3 | 3 |
| recency-8 | 3 | **1** | **1** |
| recency-12 | 3 | **1** | **1** |
| full | 3 | **1** | **1** |

recency-8, recency-12 and full history each produced a **byte-identical
dialogue** in all three repeats. The 12 runs therefore contain **6 distinct
trajectories**: 3 for recency-4 and 1 each for the others.

Temperature 0 was not perfectly deterministic either. Two pieces of direct evidence:

- The first generated turn (turn 6) of recency-4 receives an identical prompt in every
  repeat (316 tokens, same seed, same window). r1 still differs from r2 and r3
  at that turn ("traffic *won't be restored until* the database is back online" vs
  "traffic *will be restored once* …"). r2 and r3 then split at turn 8.
- recency-8's three repeats share one dialogue. Given the identical
  final-plan prompt, r1 wrapped its JSON in a code fence and r2/r3 did not. The actions were identical.

The cause of this residual nondeterminism was not established.

**Consequence for the report:** the comparison between recency-8, recency-12 and full is
one trajectory against one trajectory against one. No statistical test is
meaningful here, and "n = 3" overstates the evidence for every condition except
recency-4. Report the results as descriptive.

## 2. The context policies are identical until the window fills

At temperature 0, two conditions produce the same conversation for as long as they
put the same messages in the prompt. The first generated turn that differs from the
full-history run:

| condition | first turn differing from full history | why |
|---|---|---|
| recency-4 | 6 (the first generated turn) | the 6 seed messages already exceed 4 |
| recency-8 | 9 | turn 9 is the first with more than 8 messages available |
| recency-12 | 13 | turn 13 is the first with more than 12 messages available |

So recency-12 is literally the full-history conversation up to turn 12, and it only
differs for the last three turns and the final plan. Figure 2 shows the same thing
in token terms: the lines coincide until each window fills.

![Prompt tokens per model call](../results/comp_analysis/fig_prompt_tokens.png)

## 3. Which rules broke

![Which rules each final plan broke](../results/comp_analysis/fig_constraints.png)

| condition | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|---|---|
| recency-4 | 1/3 | 2/3 | 0/3 | 0/3 | 2/3 | 0/3 | 0/3 |
| recency-8 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 | 0/3 | 0/3 |
| recency-12 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 | 0/3 | 3/3 |
| full | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 | 0/3 | 3/3 |

The rules: C1 isolate the node · C2 isolate before diagnostics · C3 back up ·
C4 back up before restart · **C5 fail the API over before restarting the database** · C6
restart before restoring traffic · C7 restore traffic.

C3, C4 and C6 were never broken. **C5 broke in 11 of 12 runs**, the only exception being
recency-4_r1. C7 broke only with the largest contexts. C1 and C2 broke only with the
smallest window.

## 4. Most violations are not forgetting

If a violation were caused by the context policy dropping a rule, the rule's source
message should be missing from the context the plan was written in. Often it was
not missing. In Figure 1, outlined cells are those where the message that stated the rule was
still in the final-plan context.

| sample | broken, source in context | broken, source gone | kept, source in context | kept, source gone |
|---|---|---|---|---|
| all 12 runs (84 rule checks) | 12 | 8 | 18 | 46 |
| 6 distinct trajectories (42 rule checks) | 4 | 6 | 6 | 26 |

In the 6 distinct trajectories, a rule broke **4 times in 10 (40%) when its source was visible**
and **6 times in 32 (19%) when it was gone**. Having the rule in view did not
protect it.

**C5 is the clearest case.** In every one of the 12 runs, the Operations Lead's
*first* generated turn (turn 6) restates the rule correctly:

> "Got it, so we need to fail over the API to a standby instance before restarting
> the database." *(recency-4)*
>
> "Got it, so we need to fail over the API to a standby node, and then restart the
> database." *(recency-8, recency-12, full)*

In recency-12 and full history, the original seed sentence (turn 5) was still in the
prompt when the plan was written. The plan still put `RESTART_DB` before
`FAILOVER_API`. The final-plan instruction even lists the vocabulary with
`FAILOVER_API` before `RESTART_DB`, so the model actively reversed that order. The
agents knew the rule and said it, but it was lost when **turning the
conversation into the structured plan**, not in memory.

## 5. Where forgetting does appear

C1 and C2 (both stated at turn 1, the earliest rule) broke only under recency-4, in 2
of 3 runs. In recency-4:

- turn 1 is out of the window at every generated turn;
- the generated dialogue **never** mentions isolation. The keyword check finds 0
  mentions in all three recency-4 dialogues, so nothing relayed the rule forward;
- r2's plan drops `ISOLATE_NODE` entirely, and r1's plan puts it after
  `RUN_DIAGNOSTICS`.

This is the one place the data looks like the memory effect the experiment was designed
to measure. It is weak evidence, though. recency-8 also lost turn 1 and also had no
isolation mention in its final context (turns 8–15), yet its one trajectory kept C1
and C2. Losing the source may be necessary for these violations, but it was not sufficient.

## 6. Topic drift, invented content, and why more context scored worse

**The agents drift off the task.** Between 20% and 60% of generated turns (2 to 6 of
10 per run) mention none of the six plan actions (keyword check). The conversations
move to things the scenario never contained:

- recency-4: a "stress test team", a load balancer, session persistence, a
  30-minute backup estimate, customer communications;
- recency-8/12/full: a colleague called "Alex", a "network team", documentation and
  stakeholder summaries.

**The Safety Auditor endorses invented steps.** Its prompt says "do not invent new
restrictions; hold the line on the ones already raised". At turn 6 the Operations
Lead invents a step (remove the isolated node from the cluster network). At turn 7
the Auditor replies "That's the plan, and I'll coordinate with the network team to
ensure the node is removed from the cluster network…" in all 9 of those runs.

**The invented content ends up in the plans.** 7 of 12 plans contain action names
outside the closed vocabulary (`REMOVE_NODE_FROM_NETWORK`,
`REMOVE_NODE_FROM_CLUSTER_NETWORK`, `RESTART_API_SERVER`,
`RESTART_LOAD_BALANCER`). This happened even though the instruction says "using only these
identifiers". The evaluator records these and deliberately does not count them as failure
(see the comment in `evaluate.py`). But in recency-12 and full history the invented
step **took the place of `RESTORE_TRAFFIC`**, and that is the C7 violation.

**Full history wrote down exactly what was agreed. The problem was what was agreed.**
At turn 14 of the full-history run, the Operations Lead summarises:

> "we'll isolate the faulty node, take a backup, restart the database, fail over
> the API to a standby node, and then remove the isolated node from the cluster
> network."

At turn 15 the Auditor answers "Sounds good to me, it's a solid recovery plan". The
final plan is that summary, step for step: `ISOLATE_NODE > RUN_BACKUP >
RESTART_DB > FAILOVER_API > REMOVE_NODE_FROM_CLUSTER_NETWORK`. It has the wrong C5 order and no
traffic restore.

**Why recency-8 beat full history: the smaller window forgot a bad idea.** The
invented node-removal step comes from turns 6–7, which the three larger-context
trajectories share. Whether those turns were still visible when the plan was
written lines up exactly with C7:

| trajectory | final-plan context | removal step visible? | plan includes it? | `RESTORE_TRAFFIC` kept? |
|---|---|---|---|---|
| recency-8 | turns 8–15 | no | no | **yes** |
| recency-12 | turns 4–15 | yes | yes | no (C7 broken) |
| full | turns 0–15 | yes (and restated at turn 14) | yes | no (C7 broken) |

Here, more context gave the plan-writer more of the drifted conversation to copy,
and dropping it helped. With one trajectory per condition, this explanation fits
the data but is not a demonstrated mechanism.

## 7. The final plans

| run(s) | plan | broke |
|---|---|---|
| recency-4_r1 | DIAGNOSTICS > BACKUP > ISOLATE > FAILOVER > RESTART > RESTORE | C2 |
| recency-4_r2 | DIAGNOSTICS > BACKUP > RESTART > FAILOVER > RESTORE | C1 C2 C5 |
| recency-4_r3 | ISOLATE > DIAGNOSTICS > BACKUP > RESTART > *RESTART_API_SERVER* > *RESTART_LOAD_BALANCER* > RESTORE > FAILOVER | C5 |
| recency-8 ×3 | ISOLATE > DIAGNOSTICS > BACKUP > RESTART > FAILOVER > RESTORE | C5 |
| recency-12 ×3 | ISOLATE > DIAGNOSTICS > BACKUP > RESTART > FAILOVER > *REMOVE_NODE_FROM_NETWORK* | C5 C7 |
| full ×3 | ISOLATE > BACKUP > RESTART > FAILOVER > *REMOVE_NODE_FROM_CLUSTER_NETWORK* | C5 C7 |

*Italic* = invented action name. Other properties:

- **`ready: true` in 12 of 12 plans**, including every plan that broke a rule. The
  model's own safety judgement carries no information.
- **Parsing:** 12/12 parsed. 7 of 12 accepted replies were wrapped in a ```` ``` ````
  code fence, which the forgiving extractor accepted as designed. One retry was used
  (recency-4_r1): the first attempt returned objects (`{"action": …,
  "description": …}`) instead of strings, and the corrective prompt fixed it.
  Without the retry that run would have counted as a parse failure rather than
  scoring 6/7.

## 8. Cost

| condition | prompt tokens (whole run) | share of full | completion tokens | seconds | recall |
|---|---|---|---|---|---|
| recency-4 | 4 569 | 0.60 | 753 | 29.7 | 0.762 |
| recency-8 | 6 237 | 0.82 | 637 | 28.7 | 0.857 |
| recency-12 | 7 186 | 0.94 | 532 | 26.6 | 0.714 |
| full | 7 647 | 1.00 | 554 | 26.7 | 0.714 |

The window caps prompt growth as designed. Under full history the prompt grows by about
56 tokens per turn on average (402 → 903 over turns 6–15), while under recency-4 it
stays between 316 and 449 (Figure 2). Token counts are Ollama's own exact counts, not
estimates. Wall time is almost flat (26.6–29.7 s). recency-4 is the slowest despite
the smallest prompts, and it also produced the most completion tokens and includes
the only retry. With a 16-turn dialogue, the saving is modest: recency-8 costs 82% of
full history.

## 9. The judge

| | |
|---|---|
| score | **3 in all 12 runs** |
| success | **false in all 12 runs** |
| agreement with the deterministic evaluator | 12/12, but trivial: every run failed, so there was nothing to disagree on |

The score has zero variance, so it cannot rank conditions. The one-sentence
reasons are more informative than the score:

- **5/12 name the real dominant failure**, the failover/restart order (C5):
  e.g. "API failover is not explicitly ordered before database restart"
  (recency-8_r1), "Missing API failover step before database restart"
  (recency-4_r3), and "API failover is not clearly ordered in the plan" (full, ×3).
- **5/12 are vague**: "Missing explicit ordering of actions".
- **2/12 cite details the agents invented as if they were requirements**: "plan misses the
  dependency on a 'green light' notification from the stress test team" and
  "…on standby instance warming up".
- None mentions the missing `RESTORE_TRAFFIC` (C7) or the invented action names.

The judge is the same 3B model as the agents. With a single-class outcome (all failed),
its accuracy cannot be measured from these runs. That would need known-good and
known-bad plans with known answers.

---

## 10. Limitations

- **Effective sample size:** 6 distinct trajectories, 1 per condition except recency-4
  (see §1). Differences between conditions are descriptive.
- **One scenario, one model** (`llama3.2:3b` for both agents and the judge).
- **Rule position is fixed.** All seven rules are stated in turns 1–5, so window size
  and "which rules are still visible" are the same variable. recency-12 sees turns
  4–15, which includes the sources of C5, C6 and C7 but not C1–C4.
- **The concept check is a keyword heuristic.** It detects word use, not whether a
  rule was stated correctly.
- The evaluator measures rule compliance, not plan quality (as stated in
  `docs/design.md`).

## 11. What to do differently next time

1. **Get independent repeats:** use temperature > 0, or vary a seed or the scenario
   wording, so three repeats are three samples.
2. **Separate forgetting from plan-writing errors:** also score the final
   plan with every rule placed back in context. Failures that remain are not memory
   failures (this is what C5 already shows).
3. **Vary where the rules are stated**, so that window size and rule position are
   not the same variable.
4. **Check the judge first:** give it planted plans with known answers
   before trusting its scores. Consider a different or larger model than the agents.
5. **Test the drift fix directly:** have the Auditor restate the open rules before the
   plan is written, and see whether C5/C7 recover.
