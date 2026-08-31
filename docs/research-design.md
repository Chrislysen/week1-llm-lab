# Research design — selective retrieval vs recency under a fixed context budget

Branch `crazy`, from tag `compulsory-baseline-v1`. **No code written yet.**
This document is for review before anything is implemented.

---

## 0. What the frozen baseline actually says

| condition | mean recall | success | src cov | mean prompt tok | violated |
|---|---|---|---|---|---|
| recency-4 | 0.8095 | 1/3 | 0.0 | 4114 | C1\|C2 |
| recency-8 | 0.8571 | 0/3 | 0.0 | 6055 | C5 |
| recency-12 | 0.8571 | 0/3 | 0.4 | 7185 | C5 |
| full *(ceiling)* | **0.7143** | 0/3 | 1.0 | 7647 | C5\|C7 |

Three facts from this drive everything below.

1. **The ceiling is below the windows.** Full history — which contains every
   planted message — scored *worse* than recency-8 and recency-12.
2. **Source coverage 0.0 still yields 0.857 recall.** The two agents relay
   constraints forward in their own words, so information survives windows that
   drop the message which introduced it.
3. **The full-history repeats were byte-identical** (7647 prompt tokens, same
   violations, three times). Run-to-run variance is near zero at temperature 0.

Taken together these say: *more task-critical information in context did not
produce better task outcomes in the baseline.* A research question that assumes
it will is already contradicted by our own data. The design below is built to
find that out cheaply rather than to confirm a hoped-for effect.

### Pool audit (measured, not assumed)

- Candidate pool is **16 messages, ~650 words, ~1050 prompt tokens** total.
- **5 of 16 messages (31%)** carry planted constraints. Random selection at a
  50% budget therefore recovers ~31% of them by chance — that is the bar.
- Source messages mean 37 words; generated messages mean 42–49.
- **Domain vocabulary is not confined to the planted messages.** "failover"
  appears in 0 source messages and 4 generated ones; "backup" in 2 source and 3
  generated; 6 of 10 generated messages contain at least one key term.

That last point is the sharpest problem, and I did not anticipate it before
measuring. A lexical retriever querying on domain terms will surface the recent
*paraphrases*, not the originals — and the recent paraphrases are exactly what
recency already returns. **BM25 may converge on recency's selection**, not
because either is good, but because the agents restate the constraints using the
same words.

---

## 1. Research question

> Under a fixed context budget, does relevance-based selection of individual
> prior messages preserve task-critical information better than plain recency in
> a two-agent dialogue — and if it does, does that translate into better task
> outcomes?

The two halves are deliberately separate. The baseline gives real reason to
expect **yes to the first and no to the second**, and a design that cannot report
that split is not worth running.

## 2. Hypotheses

Pre-registered before any run. Committed on this branch before scoring.

- **H1 (manipulation check, not a finding).** At a budget tight enough that
  recency drops source messages, retrieval-based selection achieves higher
  `retrieval_recall` than recency. A retriever optimises for this almost by
  definition; if H1 fails the implementation is broken, not the hypothesis.

- **H2 (primary).** Higher `retrieval_recall` does **not** produce higher
  `constraint_recall`. Grounded in the baseline: the full-history condition had
  perfect source coverage and the *lowest* recall of any condition.

- **H3.** BM25 alone captures whatever benefit exists; the dense component and
  the fusion add nothing detectable at this scale. Grounded in prior work of my
  own: OpSem documents a boundary on LongMemEval-S where the lexical baseline
  saturates and fusion's gain becomes small and non-significant, and its
  `tune8_adaptive.py` found a query-adaptive weighting failed to beat one global
  constant on 1978 examples.

H2 and H3 are both framed so that the expected outcome is a null. That is
intentional. A confirmed H2 is a more interesting report than a manufactured win.

## 3. Variables

**Independent — one, with five levels:** context-selection policy at a fixed
budget: `recency`, `bm25`, `dense`, `fusion`, `random`.

**Held fixed** (enforced by the existing `experiment.assert_one_variable`
config-diff guard, extended to cover the new policy fields): scenario, both
personas and system prompts, both models, temperatures, dialogue turn budget,
finalisation budget, judge model and budget, context capacity, retrieval query
definition, and the fusion weight.

**Dependent.**

| metric | role |
|---|---|
| `constraint_recall` | **primary** — deterministic, unchanged from baseline |
| `retrieval_recall` | did the source message enter context? |
| `execution_accuracy_given_retrieval` | given it did, was it obeyed? |
| `violations`, `violated` ids | failure pattern |
| `deterministic_success` | parsed ∧ ready ∧ zero violations |
| `parse_rate`, `retries`, `unknown_actions` | instruction-following diagnostics |
| realised prompt tokens, seconds | cost, and the budget-parity audit |
| `judge_score`, `judge_success` | secondary only |

## 4. Fixed-budget definition

**Capacity = W words of dialogue content**, excluding the system prompt and the
final-plan instruction, which are always present for every policy.

Words, not tokens, because there is no tokenizer in the project and adding one
to fill a budget would be new infrastructure for no gain in fairness — a proxy
applied *identically* to every arm gives parity, which is what matters. Absolute
accuracy does not.

**Parity is then audited, not assumed.** Ollama returns `prompt_eval_count`
exactly, and `Entry.prompt_tokens` already records it. If realised prompt tokens
differ materially between arms, any winner is reported as a **paid win**, not a
win. This is the one place the design must not take its own word for it.

Fill is greedy in policy priority order until the next message would exceed W;
selected messages are then **restored to chronological order**. Ties broken by
recency, stated in advance.

Proposed W = **250 words** (≈6 of 16 messages, ≈40% of the pool). The pilot
confirms or moves it. It must be tight enough that recency demonstrably drops
source messages — at window 8 the baseline already showed coverage 0.0.

**Full history is not budget-matched and is not an arm.** It is a diagnostic
ceiling, reported separately, exactly as in the compulsory.

## 5. Selector designs — smallest possible

All four share one shape, already supported by `context.py`: keep the system
prompt, score the dialogue messages, greedy-fill to W, restore chronological
order. Each is a subclass implementing one `score()` method. **The retrieval unit
is the individual message.** No session layer, no late interaction, no max-sim.

| policy | scoring | new lines |
|---|---|---|
| `recency` | position index | ~0 (exists) |
| `bm25` | BM25 over messages, query = current | ~35 |
| `dense` | plain cosine, one vector per message | ~25 |
| `fusion` | `α·z(bm25) + (1−α)·z(dense)`, α = 0.40 fixed | ~10 |
| `random` | seeded shuffle | ~5 |

**Query definition** (a real design choice, fixed in advance): the query is the
message the agent is currently responding to; at finalisation it is the
`FINAL_PLAN_INSTRUCTION`. Alternatives exist and must not be tried after seeing
outcomes.

**Dense encoder:** `all-MiniLM-L6-v2` via `sentence-transformers` — CPU, ~90 MB,
deterministic. This is a **new dependency**. OpSem's numbers used e5-large-v2 and
BGE, so its absolute figures do not transfer and will not be cited as if they do.

**α = 0.40 is fixed a priori** from OpSem's measured global optimum (broad
plateau 0.30–0.45). It will **not** be tuned on these scenarios. OpSem selects α
by leave-one-conversation-out CV and labels the full-data value an overfit
ceiling; there is no CV pool here, so the honest move is to fix it and say so.

## 6. Controls

| control | purpose | expected |
|---|---|---|
| `random` at same W | the bar any retriever must clear | ~31% retrieval recall |
| `oracle` at same W | hands over exactly the source messages | upper bound on any retriever |
| `sabotage` | deliberately excludes source messages | recall must collapse |
| `full` | diagnostic ceiling, not budget-matched | reported separately |

`random` is included because it is trivial and because prior work of my own
records a case where the random arm beat the proposed heuristic at equal budget
(`Argos/lab/alloc_e2e.json`: random top-1 0.9674 vs contribution 0.9518, CI
excluding zero). That is a methodological lesson, not a mechanism, and is the
only thing being carried across.

`oracle` is the load-bearing one — see §8.

## 7. Metrics: retrieved vs used

Reusing `evaluate.source_coverage`, which already computes literal
whole-message presence.

```
retrieval_recall = source messages in the finalisation context
                   / source messages that exist            (5)

execution_accuracy_given_retrieval
                 = constraints satisfied whose source WAS in context
                   / constraints whose source WAS in context
```

Two honest caveats that must appear in the report:

1. The denominator can be **zero** — recency-4 and recency-8 both had coverage
   0.0 in the baseline. Then the statistic is undefined, not 0, and `n` must be
   reported alongside it.
2. Because the agents relay constraints forward, a constraint can be satisfied
   with its source message absent. So `execution_accuracy_given_retrieval` is a
   **lower bound** on what the model actually knew. No paraphrase detection will
   be attempted; the gap between literal coverage and recall is diagnosed by
   reading transcripts.

## 8. Minimum viable pilot

**One question decides whether this project runs at all: is there any headroom?**

Not "does BM25 beat recency" — if an *oracle* that is handed exactly the five
source messages cannot beat recency at the same budget, then no retriever can,
and the correct action is to stop and report why.

**Pilot: 3 arms × 3 repeats = 9 runs, ~5 minutes.**

| arm | at W = 250 |
|---|---|
| `recency` | baseline behaviour |
| `oracle` | upper bound |
| `random` | chance bar |

**Decision rules, declared now:**

- **Oracle ≤ recency on `constraint_recall`** → *stop.* Retrieval cannot help on
  this scenario. Report H2 confirmed on the strongest possible evidence and
  write that up. This is a legitimate outcome, not a failure.
- **Oracle > recency but oracle ≈ random** → the metric is not sensitive to
  *which* messages are kept. Stop and diagnose the scenario.
- **Oracle > recency and oracle > random** → headroom exists. Proceed to build
  BM25, dense and fusion, and run the full comparison.

Also verified in the pilot, cheaply: that W = 250 makes recency drop source
messages; that arms are not inert (`context.preflight`); and that realised
prompt tokens are within tolerance across arms.

**A noise floor is required before any comparison and cannot come from repeats.**
The baseline's full-history runs were byte-identical, so a same-config rerun
gives a spread of ~0.000 — structurally zero and useless. The floor must come
from a real perturbation: sampling temperature, or a scenario paraphrase
preserving constraint structure. That is a separate small run.

## 9. Confounds in the current scenario

Ordered by how badly each threatens the comparison.

1. **The ceiling is below the windows, and nobody knows why.** Until that is
   explained, "more relevant context is better" has no support in our own data.
   Candidate mechanisms: distraction at longer context; or longer context
   producing more elaborate plans that drop a required action — full history
   violated **C7**, meaning the plan never restored service.

2. **Relay.** The agents restate constraints, so windows retain the information
   without retaining the message. Confirmed: coverage 0.0 → recall 0.857. This
   compresses the headroom retrieval could recover.

3. **Retrieval will surface paraphrases, not originals.** Measured above: key
   domain terms occur in 6 of 10 generated messages. BM25's top hits are likely
   to be recent restatements — which is what recency already returns. **BM25 and
   recency may select nearly the same messages.** If so the comparison is close
   to inert even though `preflight` passes, because preflight only checks that
   selections *differ*, not that they differ *meaningfully*.

4. **Tiny candidate pool.** 16 messages, ~1050 tokens total. Differences between
   BM25, dense and fusion at this scale are very likely below noise. This is the
   regime where H3 is nearly guaranteed.

5. **Coarse primary metric.** `constraint_recall` takes values k/7; granularity
   0.143. Baseline runs clustered on exactly two values (0.857, 0.714).

6. **Near-zero run-to-run variance.** Degenerate noise floor (see §8).

7. **`source_coverage` is a literal check.** It measures whether the original
   message survived, not whether the model still knew the fact. Stated as a
   limitation, not fixed.

8. **Budget unit interacts with content.** Source messages are shorter (37 words)
   than generated ones (42–49), so a word budget packs in more of them than a
   message-count budget would. Chosen deliberately; disclosed.

## 10. Prior-work disclosure

To be maintained as `docs/PRIOR_WORK.md` before any code lands.

**Adapted from OpSem** (public, MIT, `github.com/Chrislysen/opsem`, predates this
course, permission requested from Meisam in writing):

| taken | from | form |
|---|---|---|
| BM25 implementation + tokenizer discipline | `lme_maxsim.py` (`_tok`, `class BM25`) | code, ~30 lines |
| per-query z-normalisation | `tune13_interaction.py` (`_z`) | code, ~5 lines |
| weighted linear fusion `α·z(bm)+(1−α)·z(dense)` | `tune13_interaction.py` | code, ~5 lines |
| α = 0.40 as a fixed prior | `analysis_deep.py` measured optimum | a constant |
| "report the boundary where it stops helping" | LongMemEval-S result | methodology |

**Deliberately NOT taken from OpSem:** session-level retrieval unit; turn-level
late interaction / max-sim pooling; leave-one-conversation-out α selection.

Late interaction is excluded on evidence, not preference. OpSem's max-sim runs
over 16–25+ turn vectors inside a session; its released bucket data contains
**zero** evaluated containers under 8 turns, and the measured benefit grows
monotonically with container size because it is a dilution effect. At the
message level there is nothing to pool over. The mechanism has a size
precondition this setting does not meet.

**New for this course:** message-level retrieval unit; word-budgeted greedy fill
with chronological restoration; integration with the `manage_context` hook; the
incident scenario, personas, constraints and deterministic evaluator; the
retrieved-vs-used decomposition; oracle/sabotage/random controls; the whole
harness.

**Methodological only, no code:** the equal-budget-with-random-control design,
after a prior project of mine recorded its random arm beating the proposed
heuristic.

## 11. What I need from you before coding

1. Approve or change **W = 250 words** as the capacity.
2. Approve the **query definition** (current message; instruction at finalisation).
3. Approve **`sentence-transformers` + all-MiniLM-L6-v2** as a new dependency,
   or say to drop the dense and fusion arms and run `recency` vs `bm25` vs
   `random` only.
4. Confirm the **pilot decision rules** in §8 — particularly that "oracle ≤
   recency → stop and write it up" is an acceptable outcome.
5. Confirm Meisam has replied on OpSem reuse. The pilot does not need it; BM25
   does.
