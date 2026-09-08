# QWQ — qwen3:14b receiver qualification: FAILED

Run 2026-09-08 under `docs/protocols/QWQ-qwen3-receiver-qualification.md`
(declared at commit `68e4415`, zero outcomes; manifest `results/qwq_manifest.json`).

## Verdict

**FAILED. 0 of 8 fixtures succeeded on all four assignments**, against the
declared threshold of ≥6/8.

**32 of 36 attempts spent.** 0 transport retries, 0 missing — qualification is
**complete**. 4 reserve attempts unused, not carried forward. 7 072 + 416 =
**7 488 tokens**, 85 s.

## Configuration actually used

| item | value |
|---|---|
| model | `qwen3:14b`, digest `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8` |
| size / quantization | 9 276 198 565 B, **Q4_K_M**, gguf, 14.8B |
| runtime | ollama 0.33.3 |
| `think` | **false** (top level) — honoured: **0/32** responses carried a `thinking` field |
| options | `temperature 0.7, top_p 0.8, top_k 20, min_p 0, seed 0, num_predict 300` |
| condition | `clean` — the two necessary messages only (oracle evidence control) |

**Feasibility resolved empirically.** Despite ~2.7–3.2 GB available RAM against a
9.3 GB model, Ollama ran it: 12.7 s for the first call (load), then a steady
**~2.3 s/call**. No blocker; no substitution was made or needed.

## The response contract was clean

32/32 parsed, 32/32 `ready=true`, **0 truncated** (`done_reason` was `stop` on
all 32), completion length exactly **13 tokens** on every call — the bare JSON.
Malformed output, refusal and truncation contributed nothing to the failure.

## All 32 outcomes

| fixture | domain | score | chosen (assignments 0–3) | correct |
|---|---|---|---|---|
| 0 | payments | 1/4 | P4 P4 P4 P4 | P4 P1 P3 P2 |
| 1 | robotics | **2/4** | P2 P4 P2 P4 | P2 P4 P1 P3 |
| 2 | pharmacy | **2/4** | P4 P4 P1 P1 | P4 P2 P1 P3 |
| 3 | satellite | **2/4** | P3 P4 P3 P3 | P2 P4 P3 P1 |
| 4 | brewery | 1/4 | P3 P3 P3 P3 | P2 P3 P4 P1 |
| 5 | rail | 1/4 | P4 P4 P4 P4 | P2 P4 P3 P1 |
| 6 | payments | 1/4 | P2 P2 P2 P2 | P2 P4 P1 P3 |
| 7 | robotics | 1/4 | P1 P1 P3 P3 | P3 P1 P2 P4 |

**Quartet scores: 1, 2, 2, 2, 1, 1, 1, 1. Fixtures at 4/4: 0/8.**
Total **11/32 = 0.344** (a fixed-choice responder scores exactly 8/32 = 0.250).

## The one substantive change from the previous configuration

**In 4 of 8 quartets the decoded choice varied with the fact assignment**
(distinct labels per quartet: 1, 2, 2, 2, 1, 1, 1, 2). Within a quartet the only
thing that changes is the two fact sentences, so this is **observed conditioning
on the delivered messages** — the thing that was absent before, where 7 of 8
quartets were invariant.

But it is **partial and never sufficient**: no quartet reached 4/4, and the
varying quartets alternated between two labels rather than tracking all four.

**This is a configuration comparison, not a model-size effect.** Model,
quantization, sampling settings, thinking mode and runtime all differ at once
from the earlier runs, and PSQ additionally used the *full* pool while this used
*clean*. The closest like-for-like is PSD's clean arm on fixtures 0–3: llama
scored **7/16** there with one fixture at 4/4; qwen scored **7/16** on the same
four fixtures with none at 4/4. Same total, different distribution — **no
configuration is shown to be better on that comparison.**

## What this establishes, and what it does not

**Establishes.** On these 8 development fixtures, with clean evidence and this
fully recorded configuration: well-formed output throughout, **partial observed
conditioning on the delivered facts in half the quartets**, and **no fixture
answering all four assignments correctly**.

**Does not establish.**

- **Not a universal receiver limitation.** One model, one quantization, one
  sampling setting, one prompt, one display order per fixture, 8 development
  fixtures.
- **Not a model-size effect** — too many factors moved together.
- **Not that the broader selection question is closed.** It is not.
- Not headroom, not transfer, not novelty.

## Consequence, per the declared rule

**This experimental setup is paused.** The tested configuration did not qualify.

No subset-observation stage is prepared and no recipient-aware baseline is
specified — the protocol made both conditional on passing.

What is now known across three runs: the receiver task admits clean, well-formed
responses; conditioning on the delivered messages is **present but partial** in
the stronger configuration; and no configuration tested reaches the reliability a
subset study would need, since a study of *which bundle helps* needs decisions
that track the bundle on more than half of cases.

## Standing

Generation stops here. PSQ and PSD verdicts and records stay frozen; Phase B
stays frozen. No additional models, fixture simplification, prompt search, subset
executions or Phase C are authorised or implied. The contribution sought remains
transferable selection quality at lower execution cost; **this run establishes no
novelty.** Ledger stays 22 gated, 22 closed.
