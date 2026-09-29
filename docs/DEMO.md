# Demo guide

A 6–8 minute demo, then the code walk-through you should be able to give line by
line, then the questions you are most likely to be asked. Every command runs from the
repository root on branch `core-frozen`. Ollama must be running for step 2 (`ollama serve`).

## Part 1: the live demo

| # | command | time | what to say |
|---|---|---|---|
| 1 | `python run_incident.py --mock --turns 4 --out transcripts/scratch/demo_mock.json` | instant | "Mock mode proves the plumbing without a model. The mock ignores the prompt, so the final plan comes back as prose: you see attempt 1 rejected, exactly one correction, then a recorded parse failure. The system never guesses." |
| 2 | `python run_incident.py --window 4 --turns 6 --out transcripts/scratch/demo.json` | ~25 s | Walk down the output: the 6 seeded turns carrying the rules, then the generated dialogue, the JSON plan, the deterministic evaluation (which rules held), source coverage (which rule-bearing messages were still in the window), the judge, and the measured cost. |
| 3 | open `transcripts/scratch/demo.json` | – | Show `messages[*].prompt_tokens / completion_tokens / seconds` (every message logged with its cost), `meta.context.calls` (kept and dropped at every call), and `budget.stop_reason`. |
| 4 | `python failure_analysis.py --offline` | < 1 s | "Eight ways of breaking the system, all caught: a runaway loop, broken JSON, a spent budget, a broken judge, no server, and two experiment guards." |
| 5 | show `results/supp_t07/fig_recall_t0_vs_t07.png` | – | "The frozen runs said more context hurts. At temperature 0 the repeats were copies, so I declared a supplementary run with real repeats, and full history came out best. The earliest rules are the ones small windows lose." |
| 6 | `for t in test_*.py; do python $t; done` | ~2 s | Five test files, all "All checks passed". |

If Ollama fails during the demo, say so and show step 1 plus a saved transcript from
`transcripts/exp/`. That is the point of saving evidence.

## Part 2: the code walk-through

Read these in this order. Each is short.

### The model is a function (`llm_client.py`)

`OllamaClient.chat(model, messages, temperature)` posts the message list to Ollama
and returns a `ChatResponse` with the text and the **exact** token counts Ollama reports
(`prompt_eval_count`, `eval_count`). `MockClient` has the same interface and returns
canned replies, so everything can be developed offline.

### One transcript, two views (`engine.py`)

- `Entry` (line 19): one message in the neutral transcript: speaker, content, prompt
  tokens, completion tokens, seconds, turn index.
- `view_for(agent, transcript)` (line 29): builds what one agent sees. System prompt
  first, then every entry with `role = "assistant" if entry.speaker == agent.name
  else "user"` (line 49). The same message is "assistant" to its author and "user"
  to the other agent. That is the whole Week 2 idea.
- `DialogueEngine.run` (line 79): `while not self.budget.exhausted()` (line 90). It picks
  the next speaker by turn parity, builds its view, passes it through `manage_context`
  (the context policy), calls the model, appends an `Entry`, and records the cost on
  the budget (line 107). **The Budget is the only thing that ends this loop.**

### The guardrail (`budget.py`)

`exhausted()` (line 48) returns True once turns, tokens or wall-clock seconds reach
their caps, and records which one fired in `stop_reason`. It is checked *before* each
call, so a call already running is never cut off. The failure analysis shows the
wall-clock cap overrunning by one call for exactly this reason.

### Context management (`context.py`)

- A policy is a callable `messages -> messages` that runs after `view_for`.
- `RecencyWindow.select` (line 104): keep the system prompt plus the last *n*
  messages. Line 107 guards `n = 0` explicitly, because in Python `rest[-0:]` is
  the **whole** list, not an empty one.
- `ContextPolicy.__call__` logs available, kept and dropped on every call, so a saved
  run shows what was actually dropped.
- `preflight` (line 122): would these policies see different things at this length?
  If not, the comparison is **inert** and would measure nothing.

### The final plan and the one retry (`finalise.py`, `structured.py`)

- `finalise` (line 54) asks the Operations Lead for the plan **under the same context
  policy as the dialogue**. The instruction itself sits outside the window, since it is
  the current question, not history.
- `ask_structured` (line 115) is the only retry loop in the project, shared with the
  judge. `while len(result.attempts) < max_attempts and not budget.exhausted()`
  (line 124): at most 2 calls, and never beyond the budget. On a failed parse, the
  model is shown its own reply plus the error and asked once more (line 145). Every
  attempt is kept, including failed ones.
- `extract_json_object` (line 25) finds the first balanced `{...}` while ignoring braces
  inside strings. That is why JSON wrapped in prose or a code fence still parses.

### The deterministic verdict (`evaluate.py`)

- `parse_plan` (line 61): a missing key or wrong type is a parse failure, never guessed.
- `check_constraint` (line 83): "required" means membership, and "before" means
  `actions.index(a) < actions.index(b)` (line 97). An ordering rule whose second action
  is absent is satisfied vacuously. That is why C7 ("restore traffic") exists: without
  it, a plan that proposed nothing would pass every ordering rule.
- `success` requires parsed, `ready`, and zero violations.

### The judge (`judge.py`)

It gets the conversation and the plan, but **nothing that names the condition**, so it
is blind by construction. `parse_judgement` (line 50) validates strictly. Line 64
rejects `True` as a score, because in Python `bool` is a subclass of `int`. The judge
is secondary: the experiment stands without it.

### The experiment (`experiment.py`)

- `condition_config` (line 57) expands every setting a run depends on. The only
  thing that varies is `max_messages`.
- `assert_one_variable` (line 92) diffs the configs and refuses to run if anything
  else differs. It first proves it can catch a difference, using a deliberately
  corrupted pair.
- `row_from_transcript` (line 120): every result row is **re-read from the saved JSON**,
  so the CSV is derived from the evidence, never from memory.

## Part 3: likely questions

**Why no LangGraph / AutoGen?** The brief forbids it, and the point is to show that a
multi-agent system is just a loop over a message function. The loop itself
(`DialogueEngine.run`) is about 20 lines.

**Why is the deterministic evaluator primary and the judge secondary?** A 3B judge can
be wrong, and it was: it never recognised any of the 5 correct plans. An index
comparison cannot be argued with.

**Why are the rules not in the system prompt?** The system prompt survives every
window, so a rule there can never be forgotten, and the experiment would measure
nothing. A test enforces it. The failure analysis breaks this on purpose, and C5
still fails.

**Why does the plan use the same window as the dialogue?** The plan is what gets
scored. If it were written with full history, windowing the dialogue would not matter.

**Why was the token cap set so high?** The budget counts prompt tokens on every call,
so a windowed condition uses fewer tokens per turn and would get more turns under the
same cap. The failure analysis shows 7 turns vs 5. A binding cap would mix context
policy with conversation length, so it is kept non-binding, and all 12 runs stopped on
`max_turns`.

**Your frozen results said more context hurts. Is that true?** Not in general. At
temperature 0 the repeats were copies, so there were only 6 independent runs. With
real repeats (temperature 0.7, declared in advance), full history was best (0.943)
and a 4-message window was worst.

**What happens when the conversation gets longer than the model's context?** Ollama
silently drops the oldest messages, keeps the system prompt, and raises no error. The
failure analysis provokes this with `num_ctx=512`. The frozen runs were not affected
(largest prompt 1 053 tokens, still growing). The fix is to set `num_ctx` and treat
a prompt near it as an error.

**Why only one retry?** A single correction fixed the formatting slip in the frozen
runs, though not the one in the supplementary runs. Unbounded retries would be an
uncapped model loop, which the brief forbids. The retry counts against a Budget like every other call.

**What would you do differently?** Vary where the rules are stated, calibrate the
judge on known plans, set `num_ctx` explicitly, and use temperature above 0 from the
start.
