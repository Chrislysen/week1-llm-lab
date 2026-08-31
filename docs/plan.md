# Project plan — 4 weeks

Working plan for the multi-agent compulsory. Grounded in the actual starter code
(read 2026-08-29), not assumptions about it.

---

## 0. What the starter code already gives us

Verified by reading the files, not inferred:

| Fact | Consequence |
|---|---|
| `Entry` records `prompt_tokens`, `completion_tokens`, `seconds`, `turn_index` per message | Cost-per-turn data is free. No instrumentation to build. |
| `engine.save()` is complete — writes JSON with `meta`, `agents`, `budget`, `totals`, all messages | Transcript persistence is free. Just choose paths under `transcripts/`. |
| `OllamaClient` reads `prompt_eval_count` / `eval_count` from Ollama | Token counts are **exact**, not estimated. Quality-per-token analysis is defensible. |
| `DialogueEngine.__init__` already accepts `goal_reached` and `manage_context` hooks | Week 3 architecture is pre-wired. Nothing to restructure. |
| `Budget` enforces turns / tokens / seconds, with `stop("goal_reached")` | Cap requirement satisfied by construction. |

### Three constraints that shape everything below

**1. `manage_context` runs AFTER `view_for`, not before.**

The engine docstring specifies:

```python
messages = self.manage_context(view_for(speaker, self.transcript))
```

So `manage_context` receives an already-rendered message list — system prompt
first, then `{"role": "assistant"|"user"}` entries relative to the current
speaker. It must return a valid message list: system message retained at
position 0, remaining messages in chronological order.

Consequence: retrieval selects from role-tagged messages and cannot see speaker
*names*. If speaker-aware retrieval is wanted later, capture the engine or
transcript in a closure rather than changing the hook signature.

**2. `MockClient` ignores `messages` entirely.** It cycles canned replies and
approximates tokens by word count. Therefore:

- mock validates plumbing, `Budget`, `view_for`, `save` — nothing semantic
- **every Week 3/4 measurement must run against the real model**
- token-budget numbers from mock are meaningless

**3. `Budget.record(tokens=reply.tokens)` counts prompt + completion.**

Because the prompt is resent and regrows every turn, cumulative token spend is
roughly quadratic in turn count. At the default `max_tokens: 4000`, a 15-turn
dialogue will stop on `max_tokens` long before `max_turns`.

This is an experimental trap, not just an annoyance: **the arm that uses fewer
context tokens per turn survives more turns.** A truncation arm would out-run a
full-context arm and the comparison would be confounded by dialogue length.

Mitigation: set `max_tokens` high enough that `max_turns` is always the binding
stop, and assert `stop_reason == "max_turns"` on every experimental run. Any run
that stops for another reason is discarded and reported as discarded.

---

## 1. Scenario design

### Why the current debate scenario has to go

"Should universities integrate AI?" cannot measure context management. Two
agents can generate plausible argument forever without ever referring to turn 2.
Under that scenario, truncation and retrieval produce indistinguishable
transcripts — not because retrieval fails, but because nothing is ever needed
from the distant past.

A scenario that tests memory must make **old information necessary later**, and
must make **violations checkable**.

### The scenario: incident recovery planning

Two agents plan recovery from a production outage.

- **Agent A — Operations Lead.** Proposes recovery actions, maintains the plan.
- **Agent B — Safety Auditor.** Challenges the plan, holds it to the constraints
  established earlier.

### Design rule 1: constraints live in the transcript, never in the system prompt

`manage_context` must preserve the system message. So anything placed in a
system prompt is *never forgotten*, by construction, and truncation cannot hurt.

If the constraints live in the system prompt, the experiment measures nothing.

Constraints therefore go into the **conversation body**, injected by pre-seeding
`engine.transcript` with scripted `Entry` objects before calling `run()`. Ground
truth is exact because we wrote it. `next_speaker()` uses
`len(self.transcript) % len(self.agents)`, so seed an even number of entries to
keep Agent A speaking first.

### Design rule 1b: stratify constraint placement, or recency wins by construction

Where a constraint sits decides the answer before any selector runs. A constraint
placed in the last two messages is inside the recency window by definition, so
`recency` scores it every time — and the reported number becomes an arithmetic
identity about position rather than a fact about context selection. Placing every
constraint far back inverts the same bias in favour of retrieval.

So placement is a controlled variable, not a convenience:

- **Stratify** each instance's constraints across distance-from-end bands —
  near (inside any plausible recency window), mid, far.
- Hold the **same distribution across all scenario instances**, so instances stay
  matched.
- **Report per-stratum**, not just pooled. "BM25 beats recency on far constraints
  and ties on near ones" is the actual finding; a pooled average hides it and its
  value depends entirely on a mix that was chosen, not measured.

If the near stratum is where all the score lives, the experiment is measuring the
placement choice.

### Design rule 2: natural dialogue, structured only at the end

Free text cannot be scored deterministically. "Restart the database" and "bring
the DB back up" mean the same thing and no regex catches both.

The tempting fix — force both agents to speak in a closed vocabulary of action
identifiers throughout — is **too synthetic**. It would partly measure whether a
3B model can carry arbitrary tokens across a long context, which is not the
question. The dialogue has to look like a dialogue.

So: the conversation is natural, and each underlying fact carries a *hidden*
evaluator representation that never appears in the prompt.

Spoken in the transcript:

> **Safety Auditor:** We cannot restart the database until the backup has
> completed.
>
> **Operations Lead:** Understood — I'll keep it online until then.

Held by the scorer only:

```python
Constraint(id="C1", before="RUN_BACKUP", after="RESTART_DB")
```

The closed vocabulary appears in exactly one place: the **final plan**. Agent A
is asked to emit the recovery plan as a numbered list of action identifiers, one
per line, from a fixed set given at that moment:

```
RUN_BACKUP  RESTART_DB  FAILOVER_API  NOTIFY_CUSTOMERS  SCALE_WORKERS  ROLLBACK_DEPLOY
```

Checking `index(RUN_BACKUP) < index(RESTART_DB)` is then string and index
comparison. **No LLM judge is required for the primary metric** — directly the
Solon principle that the deciding scorer should not be a model that can declare
itself successful.

**The cost of this choice, stated honestly:** a constraint now has to survive two
hops — retention in context, *and* correct translation from natural language into
an identifier ordering at the end. A failure could be either one.

That is exactly why the **full-context ceiling condition is load-bearing, not
optional**. If full-context scores ~90%, the translation hop demonstrably works,
and any drop under truncation is attributable to context loss. Without the
ceiling, the primary metric is uninterpretable.

### Design rule 3: a structured final turn

After the dialogue completes, one additional scored call asks Agent A to emit
the final plan as a numbered list of identifiers, one per line. That artifact is
parsed and checked against the constraint set.

Compliance is not assumed. **Parse failure rate is itself a reported metric** —
a 3B model may not reliably honour a closed vocabulary, and that number is data,
not an inconvenience.

---

## 2. Metrics

**Primary — deterministic, no judge:**

| Metric | Definition |
|---|---|
| `constraint_recall` | satisfied constraints / applicable constraints |
| `violations` | count of ordering/exclusion breaches in the final plan |
| `parse_rate` | final plans parsing cleanly / runs attempted |

**Secondary — LLM judge, blinded:**

Pairwise comparison of two transcripts from the same seed under different
context methods. The judge sees neither condition label. Position is randomised
so A/B order is not confounded with condition.

Judge model must be **different and larger** than the debaters — `qwen3:14b` or
`qwen2.5:14b-instruct` are already pulled locally. State the choice explicitly.

**Cost — realised, not configured:**

A budget is a **ceiling, not a spend.** Comparing arms on their configured
`budget_tokens` would let an arm win at higher actual cost and still read as a
clean win. What must be reported is what each arm actually put in the prompt.

This needs no new plumbing: `Entry.prompt_tokens` is Ollama's
`prompt_eval_count` — the exact number of tokens the model saw that turn. Report
realised prompt tokens per turn per agent alongside every score delta, and label
a win at materially higher realised spend as a **paid win**, not a win.

---

## 3. Replication unit and comparison

### The starter client cannot seed generations

`llm_client.py` sends only `{"temperature": temperature}` in `options`. Ollama
supports a `seed` field; **this client does not pass it.** So "5 seeds" is not
available without modifying a file the course marks as complete.

That constraint pushes the design somewhere better anyway:

**Replication unit = distinct scenario instances, not RNG seeds.** Five separate
incidents — different services, different constraint content — sharing an
identical structural pattern (6–8 constraints, matched distance-from-end strata,
matched injection positions). Varying the scenario tests whether the effect
*generalises*; varying an RNG seed only tests sampling noise.

**A deterministic rerun is not a noise floor.** *(Correction — an earlier draft
of this plan treated it as one.)* Re-running an identical config at
`temperature = 0` will report a spread of ~0.000. That floor is *structurally*
zero: it measures nothing, and comparing any effect against it would declare
every difference significant.

The floor has to come from a perturbation that is real but shouldn't matter:
raise sampling temperature, or paraphrase the scenario without changing its
constraint structure. If a floor comes back exactly zero, treat that as a
degenerate measurement to be reported and replaced, not as a free win.

If seeded replicates are wanted later, passing `seed` through `OllamaClient.chat`
is a two-line change — disclose it in the report as a modification to supplied
code.

### Compare within instance, never across piles

Report the **paired difference per instance**, not two averages:

```
instance 1:  BM25 − Recency = +0.25
instance 2:  BM25 − Recency =  0.00
instance 3:  BM25 − Recency = +0.50
```

Pairing removes between-instance variance, which will dominate at this sample
size.

**Useful planning fact:** with paired data, a sign test on 5 instances reaches
one-sided *p* = 0.031 **if the effect is unanimous** (0.5⁵). At 4-of-5 it is
*p* = 0.19 — nothing. So five instances suffice for a clean claim only when the
direction is consistent; a mixed result needs ten or more. Run five first, and
let the outcome decide whether to expand.

**Consequence for scenario design: use more constraints per instance than feels
necessary.** A sign test discards tied pairs and shrinks *n* accordingly. With
only 3 constraints, `constraint_recall` can take four values (0, ⅓, ⅔, 1), so
ties between arms are likely — two ties out of five leaves *n* = 3, where even a
unanimous result gives *p* = 0.125 and proves nothing. Six to eight constraints
per instance makes the metric finer, ties rarer, and the test usable at this
sample size. This is cheap to decide now and expensive to fix after the runs.

## 4. Hypotheses — pre-register before running

- **H1** Under a fixed context-token budget, retrieval-based context selection
  preserves task-relevant long-range information better than recency truncation.
- **H2** That improvement shows up in constraint recall and violation counts,
  not merely in retrieval scores.
- **H3** BM25 alone captures most of the benefit; the dense component that helped
  on LoCoMo may not transfer to live multi-agent dialogue.

H3 exists so the project is not designed to prove the earlier paper right.
Confirming H3 is a publishable-shaped negative result and a better outcome for
the report than a clean win.

Commit these before the scoring runs. `git log` makes the ordering checkable —
same discipline as the `probes/` pre-registrations in `secret-loyalty-probe`.

---

## Week 1 — criterion and controls

Deliverable: M1 (two agents, N turns, cap proven, transcript, `docs/design.md`).

1. Rewrite the scenario: incident recovery, both personas, closed action
   vocabulary for the final plan only, **6–8 constraints** stratified by
   distance-from-end (design rules 1b and 2).
2. Rewrite `docs/design.md`:
   - scenario and why
   - both full system prompts
   - **measurable** goal: a rule with a numerator, a denominator, and a threshold
   - how it will be evaluated: the deterministic checker, named
   - H1/H2/H3
3. Port personas into `ping_pong.py` — the file table designates it as the Week 1
   file and a grader may look there.
4. Run the **same-prompt negative control**: both agents given an identical
   system prompt. The criterion must score lower. The course's own pitfalls list
   supplies this control; it costs one config.
5. Commit the criterion **before** the scoring run.

Week 1 still uses the simple labelled-text approach — `engine.py` is Week 2
work. That is intentional: it generates the before/after evidence for Week 2.

**Exit check:** does the criterion score materially lower on the same-prompt
control? If not, the criterion is measuring "text was produced" and must be
rewritten before proceeding.

## Week 2 — role mapping, measured

Deliverable: `view_for` + `DialogueEngine.run`, `test_engine.py` passing.

1. Implement both TODOs. `test_engine.py` defines correctness precisely — mirror
   roles across the two agents, system prompt first, `>= 2` messages on an empty
   transcript, alternating speakers, `turn_index` sequential, non-zero token
   counts, `save()` round-tripping.
2. **Measure the fix.** Week 1's real run already exhibits the bug: the model
   echoing `Dr. Reed:` into its own output, and a leaked meta-note. Count
   label-echo rate and meta-leak rate over N turns, before and after, same seed
   and personas. One variable changed. Report as X/N → Y/N.
3. **Determinism check.** Run the same config twice at `temperature=0` against
   Ollama and diff. This establishes only whether the harness is reproducible —
   it does **not** produce a noise floor. A byte-identical rerun gives a spread of
   zero, which is a degenerate measurement, not a free win. See §3.
4. Raise `max_tokens` until `stop_reason == "max_turns"` on a full-length run.

**Scenario validation gate — the most important step in the plan.**

Before building any retrieval, run two conditions and check that a
memory-dependent signal exists at all:

| Condition | `manage_context` | Pre-declared target |
|---|---|---|
| Ceiling | full history, no trimming | `constraint_recall` ≥ 0.80 |
| Floor | system message + last message only | `constraint_recall` ≤ 0.50 |

Declare the band **before** running it. Then:

- **Both high** (e.g. 0.90 / 0.85) → the scenario doesn't require memory.
  Constraints are too easy or needed too soon after injection. Push them further
  back and add distractor turns.
- **Both low** (e.g. 0.35 / 0.30) → too hard for a 3B model, or the final-plan
  translation is failing. Check `parse_rate` before touching the scenario; a low
  ceiling with a low parse rate is a formatting problem, not a memory problem.
- **Separated** (e.g. 0.90 / 0.40) → there is real headroom for a context method
  to recover. Proceed to Week 3.

Run the gate at **production settings** — same `max_turns`, same constraint
injection positions, same distances. Constraint recall depends on how far back
the fact sits, so a gate run at 6 turns says nothing about an experiment at 16.

Do this in Week 2, while the scenario is still cheap to change. This is the
control that can fail — and the whole project depends on it failing correctly.

## Week 3 — context management and the judge

Deliverable: `manage_context`, judge function, one-parameter-at-a-time experiments.

**Retrieval unit = the individual message.** *(Correction — an earlier draft
proposed grouping messages into 2-message "episodes" so that turn-level
late interaction / max-sim would have something to pool over. That was a
misreading of `opsem`; see `docs/audit.md` §C.1. `opsem`'s max-sim runs over
16–25+ turn vectors inside a session, its released data contains zero evaluated
containers under 8 turns, and the measured benefit grows monotonically with
container size because it is a dilution effect. At 2 messages the formula
survives and the mechanism does not. Late interaction is dropped, and that
exclusion — a mechanism with a size precondition this setting cannot meet — is
itself reportable.)*

**The main comparison — the three compulsory arms:**

1. **recency** — system prompt plus newest messages that fit
2. **bm25** — system prompt, recent 1–2 messages, top-scoring older messages
3. **fusion** — `alpha * z(bm25) + (1 - alpha) * z(cosine)`, **plain cosine
   similarity per message**, `alpha` **fixed a priori** (`opsem`'s global optimum
   was 0.40, with a broad plateau across 0.30–0.45). Do not tune `alpha` on the
   same scenarios being scored, and do not inherit `jarvis-cortex`'s 0.7 — that
   was fitted to a different task. Only if the `opsem` reuse is approved.

**The diagnostic arms — controls, never headline results:**

| Arm | Purpose | Expected |
|---|---|---|
| `full` | ceiling: no trimming at all | `constraint_recall` ≥ 0.80 |
| `last-message` | floor: system + last message only | ≤ 0.50 |
| `oracle` | evaluator hands over exactly the decision-critical messages | ≈ ceiling |
| `sabotage` | deliberately drops constraint-bearing messages | ≈ 0 |

`sabotage` is the evaluator's own sanity check: if a selector built to fail does
not score near zero, the evaluator is not measuring what the report claims and
every number downstream is void.

**Inert-run detection.** If the whole transcript fits inside the context budget,
all selectors return identical messages and the run measures nothing. Assert
`transcript_tokens > budget_tokens` *before* spending a run; anything failing it
is state `INERT`, reported and excluded rather than silently averaged in.

This split is deliberate. Recency vs BM25 is already a complete, interesting
experiment: it tests whether *any* relevance-based selection beats recency under
a fixed budget. Fusion becomes the headline third arm if approved and is dropped
cleanly if not. **The project must not depend on an academic-integrity ruling.**

All arms return messages in chronological order with the system message first.
Identical context-token budget across arms is the controlled variable; without it
the comparison is just more-context vs less-context.

Extend `run_config` in `run.py` to wire `manage_context` and `goal_reached` from
YAML — it currently constructs `DialogueEngine` without either. New config keys,
e.g. `context: {method: recency|bm25|fusion, budget_tokens: N}`. Note
`Agent(**a)` means agent keys must match the `Agent` dataclass fields exactly.

**Judge — supporting evidence, never the backbone.**

Blinded pairwise, condition labels hidden, A/B position randomised. Validate it
against the Week 1 same-prompt control: if the judge rates the degenerate
transcript as goal-reached, the judge is broken and everything it says is noise.

A larger judge model (`qwen3:14b` / `qwen2.5:14b-instruct`, both already pulled)
is methodologically preferable but **is not a requirement**. Practical cost:
alternating between a 3B and a 14B model forces Ollama to unload and reload
weights, so judging must be batched at the end of all runs rather than
interleaved — otherwise wall-clock explodes.

The test to hold: **if the judge disappeared entirely, the experiment should
still stand on `constraint_recall`, `violations`, and `parse_rate` alone.** It
should. That is the design working, not a gap in it.

Matrix: 5 scenario instances × 2 arms (× 3 if fusion is approved). Model,
personas, temperature, token budget, max turns and injection positions all held
fixed. Only `manage_context` changes.

## Week 4 — noise floor, breakage, receipts

Deliverable: failure analysis, numbers from `transcripts/`, report.

1. **Noise floor first — and not from a deterministic rerun.** Perturb something
   real but irrelevant (sampling temperature, or a scenario paraphrase that
   preserves the constraint structure) and measure how much the score moves when
   nothing meaningful has changed. No arm is claimed to beat another unless the
   gap clears that spread. A floor of exactly 0.000 means the perturbation was
   inert — report it and pick a real one.
2. **Break things deliberately:** context window overflow, an agent emitting
   empty output, budget exhausting mid-turn, personas collapsing into agreement,
   the closed vocabulary being ignored entirely.
3. **`verify_claims.py`** — re-derive every number in the report from the saved
   JSON transcripts, not from the file asserting them. Exit non-zero on
   mismatch. Roughly forty lines, and it is the thing no other submission will
   have: the grader can check the report from a fresh clone.
4. Report the boundary. If fusion does not beat BM25, say so plainly and connect
   it to the LongMemEval-S boundary already documented in `opsem`.

---

## Risks

| Risk | Mitigation |
|---|---|
| Scenario doesn't punish forgetting | Week 2 validation gate with a pre-declared band, before retrieval is built |
| `opsem` reuse denied | Fusion is an extension arm; recency vs BM25 stands alone |
| 3B model can't emit the final plan format | `parse_rate` is a reported metric; ceiling condition separates format failure from memory failure |
| `max_tokens` binds before `max_turns`, confounding arms | Assert `stop_reason == "max_turns"`; discard and report others |
| Constraints placed in system prompt | Design rule 1 — they go in the transcript body |
| Constraint placement favours recency by construction | Design rule 1b — stratify by distance-from-end, report per stratum |
| Whole transcript fits the budget, so all arms are identical | Inert-run preflight; state `INERT`, excluded and reported |
| An arm wins at higher actual context spend | Compare realised `Entry.prompt_tokens`; label it a paid win |
| Noise floor read from a deterministic rerun (structurally 0) | Perturb something real; a 0.000 floor is degenerate, not a win |
| Evaluator silently not measuring what is claimed | `sabotage` arm must score ≈ 0 or nothing downstream is valid |
| Client cannot seed generations | Replicate over scenario instances, not RNG seeds |
| Effect real but mixed across instances | Sign test needs unanimity at n=5; expand to 10 if 4-of-5 |
| Wall-clock blowout on hundreds of real-model calls | 5 instances × 2 arms first; batch all judging at the end |
| Judge position bias | Randomised A/B order, condition labels hidden |

## Minimum viable version

If time runs short, this still satisfies every checklist item and keeps the
intellectual line intact:

- new scenario, deterministic constraint checker
- two arms: recency vs BM25 — the spine, not a fallback
- 5 scenario instances, paired comparison
- deterministic metrics only, no LLM judge
- noise floor measured
- `verify_claims.py`

Fusion and the judge are expansions. Neither is load-bearing, and the project
reads as complete without them.

## Academic integrity

- `opsem` method reuse: ask Meisam in writing before implementing; cite either way.
- Ideas and methodology from own prior work: cite where relevant, no permission
  needed — that is ordinary research practice.
- Any *code or text* adapted from a prior repo: disclose it.
