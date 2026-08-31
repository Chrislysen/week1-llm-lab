# Design document

## A note on scope, and what changed

The Week 1 submission used a different scenario: two university advisors debating
whether AI should be integrated into university education. That work is real and
is preserved in this repository's git history (commit `3770dfe`, files
`exercise_a.py`, `exercise_b.py`, `exercise_c.py`, `milestone1.py`).

It was replaced deliberately, for a reason worth recording. **A debate cannot
measure memory.** Two agents can argue about AI in education for twenty turns
without ever needing anything from turn two, so a later comparison of context
strategies would find no difference — not because the strategies are equivalent,
but because the task never punishes forgetting. The scenario below was designed
so that forgetting has a consequence a machine can detect.

---

## Chosen scenario: incident recovery

A production incident is in progress. The payments database on node `db-04` is
failing under load and the customer-facing API is degraded. Two colleagues work
out the recovery plan together in conversation, and one of them ends by writing
the plan down.

The scenario was chosen for three properties:

1. **Facts stated early must still matter later.** Operational dependencies are
   raised in the opening exchange and are only acted on several turns afterwards.
2. **Correctness is objective.** "You cannot restart the database before the
   backup finishes" is either respected or it is not. There is no judgement call,
   and no language model is needed to decide.
3. **It is realistic without being complicated.** Six possible actions, seven
   rules. Small enough to explain line by line; large enough that a plan can be
   wrong in several distinguishable ways.

---

## The two agents

### Agent A — Operations Lead

Responsible for producing a safe recovery plan and restoring service.

> You are the Operations Lead handling a live production incident. You are
> responsible for producing a safe recovery plan and restoring service. Propose
> concrete operational steps and keep track of what has been agreed.
>
> A production incident is in progress. The payments database on node db-04 is
> returning errors under load, and the customer-facing API is degraded. You and
> one colleague are working out the recovery plan together.
>
> Speak naturally, as you would to a colleague. Keep each reply to at most three
> sentences. Respond to what the other person actually said.

### Agent B — Safety Auditor

Challenges unsafe actions and holds the plan to the constraints already raised.

> You are the Safety Auditor handling a live production incident. You challenge
> unsafe actions and hold the plan to the operational constraints that have been
> established. Do not invent new restrictions; hold the line on the ones already
> raised.
>
> A production incident is in progress. The payments database on node db-04 is
> returning errors under load, and the customer-facing API is degraded. You and
> one colleague are working out the recovery plan together.
>
> Speak naturally, as you would to a colleague. Keep each reply to at most three
> sentences. Respond to what the other person actually said.

**Neither system prompt contains any constraint.** This is enforced by a test,
not by intention. A system prompt survives every context-management policy by
construction, so a rule placed there could never be forgotten — and the
experiment this scenario exists to support would measure nothing.

---

## What the agents see, and what the scorer sees

These are deliberately different things.

**The agents see natural language.** The opening exchange is six scripted turns
in which the two colleagues establish the situation, phrased the way people
actually talk:

> **Safety Auditor:** Before anything else, that node has to be isolated — it
> cannot stay on the cluster network while it's in this state. And do not run
> diagnostics on it until the node is isolated, or you'll be reading numbers
> polluted by live traffic.

**The scorer sees rules.** The same fact, in `scenario.py`, hidden from every
prompt:

```python
Constraint(id="C1", kind="required", a="ISOLATE_NODE", ...)
Constraint(id="C2", kind="before", a="ISOLATE_NODE", b="RUN_DIAGNOSTICS", ...)
```

Each constraint records the sentence that conveys it, and a test asserts that
sentence really appears in the turn it claims to come from — so the visible
dialogue and the hidden key cannot drift apart unnoticed.

### The seven rules

| id | rule | meaning |
|---|---|---|
| C1 | required `ISOLATE_NODE` | the failing node must be taken off the network |
| C2 | `ISOLATE_NODE` before `RUN_DIAGNOSTICS` | don't measure a node still taking traffic |
| C3 | required `RUN_BACKUP` | policy: back up before anything destructive |
| C4 | `RUN_BACKUP` before `RESTART_DB` | a restart mid-backup loses both |
| C5 | `FAILOVER_API` before `RESTART_DB` | the restart drops the API with it |
| C6 | `RESTART_DB` before `RESTORE_TRAFFIC` | don't send traffic to a database that isn't up |
| C7 | required `RESTORE_TRAFFIC` | the incident is not over until service is back |

An ordering rule is *vacuously satisfied* when its second action is absent — you
cannot mis-order a step that was never proposed. C7 exists because of that:
without it, a plan proposing almost nothing would satisfy every ordering rule by
default and score perfectly. Requiring the incident to actually be resolved
forces `RESTART_DB` into the plan, which re-arms C4, C5 and C6.

---

## The final answer

After the discussion, the Operations Lead is asked for the plan as JSON. This is
the only point at which the agents ever see the action vocabulary:

```json
{"actions": ["ISOLATE_NODE", "RUN_BACKUP", "FAILOVER_API",
             "RESTART_DB", "RESTORE_TRAFFIC"], "ready": true}
```

Parsing is forgiving about wrapping and strict about content: JSON inside a code
fence or surrounded by prose is accepted, because a 3B model routinely does that
and discarding it would report a memory failure where the truth is a formatting
quirk. A missing key or a wrong type is a parse failure and is recorded as one,
never guessed at.

---

## Goal reached — measurable definition

> **The goal is reached when the final plan parses as valid JSON, contains only
> actions from the defined vocabulary, is declared `ready`, and violates zero of
> the seven constraints — i.e. `constraint_recall == 1.0` and
> `violations == 0`.**

## How success is evaluated

`evaluate.py` recomputes the verdict from the plan text alone: it parses the
JSON, then for each of the seven rules checks membership for `required` and
`index(a) < index(b)` for `before`. It reports `parsed`, `satisfied`,
`violated`, `violations`, `constraint_recall` and `success`.

**No language model takes part in any verdict.** A model can be argued with; an
index comparison cannot. Deliberately faulty plans are checked in
`test_scenario.py` — wrong ordering, missing required action, invented action,
empty plan, and ten malformed-JSON cases — each of which must be caught. A
checker that cannot fail is not a checker.

---

## Known limitation

`constraint_recall` measures whether the rules were respected, not whether the
plan is good. A plan can satisfy all seven rules and still be poor — the metric
has nothing to say about, for instance, whether diagnostics were worth running.
That is the intended scope: this measures whether facts established early in a
conversation survive to influence a decision made later.
