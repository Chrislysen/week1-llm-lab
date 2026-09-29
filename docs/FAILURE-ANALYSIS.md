# Intentional failure analysis

Week 4 of the brief: break things on purpose and record what happens. Every case
lives in `failure_analysis.py`. It states in code what it expects before it runs,
saves its evidence to `transcripts/failures/`, and writes one row of
`results/failures/summary.csv`.

    python failure_analysis.py --offline     # 8 cases, no model, under a second
    python failure_analysis.py               # all 15 cases, ~4 minutes with Ollama

The frozen experiment is never touched. The real-model cases use `llama3.2:3b` at
temperature 0, one run each: they demonstrate behaviour, they do not estimate rates.

## Summary

| # | case | what was broken | what happened | verdict |
|---|---|---|---|---|
| 1 | runaway_loop | a goal that never arrives | Budget stopped it at exactly 50 turns, 50 calls | guard worked |
| 2 | plan_retry_recovers | first plan reply is prose | rejected ("no JSON object found"), one correction, accepted, 7/7 | guard worked |
| 3 | plan_retry_gives_up | both plan replies are prose | exactly 2 calls, `parse_failed`, success False, nothing guessed | guard worked |
| 4 | plan_no_budget | finalisation budget already spent | 0 calls, `budget_exhausted`, recorded as "no attempt made" | guard worked |
| 5 | judge_garbage | judge replies in prose, then `{"score": 7, "success": "yes"}` | both rejected, score None; deterministic verdict unaffected | guard worked |
| 6 | ollama_down | no model server | clear `RuntimeError: Cannot connect to Ollama`, no result row | guard worked |
| 7 | guard_config_diff | two conditions differ in a second setting | experiment refuses: "differ in more than max_messages: ['agent_b_temperature']" | guard worked |
| 8 | guard_inert | windows 20/30/40 on a 16-message dialogue | experiment refuses: conditions are INERT | guard worked |
| 9 | token_cap_full | `max_tokens=2500`, full history | stopped after **5** of 10 turns | worked, but see A |
| 10 | token_cap_recency4 | the same cap, window 4 | stopped after **7** of 10 turns | worked, but see A |
| 11 | wall_clock_cap | `max_seconds=3` | stopped after 2 turns at **4.8 s** | worked, but see B |
| 12 | context_overflow | full history, Ollama `num_ctx=512` | prompt silently cut to ~500 tokens every turn; recall 0.429 | **weakness**, see C |
| 13 | overflow_probe | a planted secret (system prompt) and codename (first message), `num_ctx=256` | secret kept, codename lost, no error | finding, see C |
| 14 | window_zero | the agents see only their system prompt | plan still scores recall **0.571** | finding, see D |
| 15 | rules_in_system_prompt | the rules copied into both system prompts | C5 still broken; recall 0.857 | finding, see E |

All eight guards (1–8) did exactly what they were built to do. The interesting
results are the seven cases that probe the system's limits.

## What the probes revealed

### A. The token cap favours the cheaper condition

The Budget counts prompt + completion tokens of every call. Each call resends the
growing conversation, so under full history the running total grows roughly
quadratically. With the same 2 500-token cap, full history got 5 turns and
recency-4 got 7.

If the experiment had used a binding token cap, the windowed conditions would have
had **longer conversations**, and the comparison would mix two variables: context
policy and dialogue length. The frozen experiment avoids this. `max_tokens` is set to
100 000, and all 12 frozen runs stopped on `max_turns` (checked in every
transcript's `budget.stop_reason`).

### B. The wall-clock cap is soft by one call

The Budget is checked **between** model calls. A call already running is never
interrupted, so a 3-second cap stopped at 4.8 s. The overrun is bounded by one call's
duration, which is fine for a safety cap. It does mean `max_seconds` cannot
guarantee a hard deadline. That would need a request timeout on the HTTP call
itself (the client's `timeout=300` is the only one).

### C. Ollama silently truncates a prompt that does not fit (the important one)

The frozen client never sets Ollama's context size (`num_ctx`). This case sets it to
512 with full history. Ollama reported these prompt sizes:

| turn | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | plan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen full history (fits) | 402 | 464 | 529 | 588 | 645 | 699 | 739 | 796 | 829 | 903 | 1 053 |
| `num_ctx=512` | 402 | 459 | 492 | 484 | 494 | 478 | 459 | 478 | 472 | 507 | 504 |

From turn 8 on, the prompt stops growing. Ollama drops the **oldest messages** to make
it fit, keeps the system prompt, and raises **no error**. The `overflow_probe` case
confirms the rule directly. With a 4 096-token window the model recalls both a secret
in the system prompt and a codename from the first user message. With 256 tokens it
still recalls the secret but has lost the codename (219 prompt tokens reported, no error).
The engine believes it sent full history. In effect, Ollama ran its own recency window, which nobody configured and nobody logged. This run
scored the lowest recall of any case (0.429, breaking C1, C2, C4 and C5).

Two consequences:

- **The frozen results are not affected.** Every frozen full-history prompt kept
  growing turn by turn with no plateau, up to 1 053 tokens at the final plan. Truncation
  would show as the prompt size levelling off, as it does in the table above.
- **Fix, if the conversation were longer:** set `num_ctx` explicitly in the client and
  treat `prompt_eval_count` close to `num_ctx` as a failure. The Entry already records
  `prompt_tokens`, so the check is one comparison.

### D. With no context at all, the plan still scores 0.571

With a window of 0, every call sees only the system prompt. The agents never see the
rules, and the plan-writer sees only the brief and the action list. The plan still
satisfied 4 of 7 rules (C3, C4, C6, C7), because a sensible default order (back up
before restart, restart before restoring traffic) gets them right without being told.
The supplementary run confirms this floor with five samples: mean recall 0.629.

This matters for reading every result. Recall starts at about 0.6 with no
information at all. With no context, the rules broken most often were C1, C2 and C5
(3, 3 and 4 of 5 supplementary runs), while C3 and C6 were never broken. **Most of
the room for context to help is in C1, C2 and C5.**

### E. C5 fails even when the rules can never be forgotten

Design rule 1 keeps every rule out of the system prompts, so that a window can remove
it. This case breaks that rule on purpose. All rule-bearing seed sentences are copied
into both system prompts, with a 4-message window. Every rule was therefore in view at
every call. The plan still put `RESTART_DB` before `FAILOVER_API` (C5), while every
other rule held.

So C5 is not only a memory problem. The supplementary run shows the same: C5 broke in
2 of 5 runs even with full history. The model has a strong habit of "restart, then
fail over", and having the rule in view does not reliably override it.

## Failures that happened on their own

These were not provoked. They appeared in the frozen and supplementary runs, and each
one was caught and recorded by the system rather than hidden.

| failure | where | how it was handled |
|---|---|---|
| plan returned objects instead of strings | frozen recency-4 r1 | rejected by the validator; the corrective retry fixed it |
| `// comment` inside the JSON | supplementary recency-4 r2 | rejected; the retry removed the comment but lost the closing brace; recorded as `parse_failed` after 2 calls |
| plan wrapped in a ```` ``` ```` code fence | 7/12 frozen plans | accepted by design: the extractor is forgiving about wrapping, strict about content |
| invented action names (`REMOVE_NODE_FROM_NETWORK` …) | 7/12 frozen, 8/25 supplementary | recorded in `unknown_actions`; not counted as failure (see `evaluate.py`) |
| `ready: true` on plans that break rules | every parsed plan (12/12 frozen, 24/24 supplementary) | not trusted: success requires zero violations as well |
| the judge never recognises a correct plan | 0 of 5 perfect supplementary plans judged successful | the judge is secondary evidence; the deterministic evaluator decides |
| topic drift (an invented colleague "Alex", a stress-test team, a load balancer) | most dialogues | not handled; see `docs/COMP-ANALYSIS.md` §6 |
