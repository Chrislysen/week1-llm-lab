# QWQ — receiver qualification on qwen3:14b

**Status at declaration: ZERO OUTCOMES. No generation call has been made.**
Declared 2026-09-08, before any run. Manifest fixed at
`results/qwq_manifest.json` (32 requests, 32 distinct prompt hashes).

**Allocation: 36 attempts = 32 scheduled generation calls + 4 transport-only
retries.** PSQ and PSD verdicts and records stay frozen; their unused reserves
are **not** carried here.

**This qualifies a receiver CONFIGURATION.** It does not isolate a model-size
effect against the historical Llama results: model, quantization, sampling
settings, thinking mode and runtime all differ at once.

## Environment, checked before declaring

| item | value |
|---|---|
| model | `qwen3:14b`, already present locally — **no download needed** |
| digest | `bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8` |
| size / quantization | 9 276 198 565 B (9.3 GB), **Q4_K_M**, gguf, 14.8B |
| runtime | ollama 0.33.3 |
| host RAM | 15.4 GB total; **~2.7–3.2 GB available** (steady state, sampled 4×) |
| disk free | 67.4 GB |
| GPU | Intel integrated, 2 GB — insufficient; CPU inference expected |

**Feasibility is not assumed.** Available RAM is below the model's resident
footprint, so Ollama will rely on mmap paging. The run proceeds block by block
and **latency is measured on the first block**. If it proves unworkable, the
concrete blocker is reported with measured evidence — **no substitution to
another model or a paid API.**

## Design

- **All 8 existing fixtures × all 4 fact assignments = 32 calls**, using **only
  the two necessary messages** (`clean`).
- **`clean` is an ORACLE EVIDENCE CONTROL** on **development fixtures** — the
  subset comes from construction metadata a deployed selector would not have.
- **Preserved:** fact wording, task instruction, recipient context, option→label
  mapping, display order and executable scoring.
- **Verified before declaring, for all 32 cells:** removal keeps both necessary
  facts, drops only the other messages, leaves the correct answer unchanged, and
  leaves the recipient context and the option block byte-identical.

## Request configuration (recorded in full)

Top-level **`think: false`**; the **final answer content** is scored.
Qwen's recommended non-thinking sampling, plus a fixed seed:

```json
{"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0,
 "seed": 0, "num_predict": 300}
```

Every record stores the resolved digest, quantization, runtime version, `think`
flag, the complete options block, `done_reason`, and any `message.thinking`
field returned.

## Pass rule (operational, declared before outcomes)

> **PASS if at least 6 of 8 fixtures succeed on ALL FOUR assignments**, with
> `ready=true` required for success.

**A development feasibility screen, not a general reliability estimate.**
Individual outcomes **and** quartet scores are reported either way.

## Collection and accounting

- 8 process blocks, one per fixture, 4 calls each; assignment order randomised
  per block from a fixed seed; request position, process id, literal request,
  raw output and costs all logged.
- **Wrong answers, refusals, malformed responses and OUTPUT TRUNCATION are
  OUTCOMES**, never retry opportunities. Truncation is detected via
  `done_reason == "length"` and recorded.
- The 4-attempt reserve covers **transport failures only** and is **global across
  blocks**. An unresolved transport failure is logged as **MISSING**.
- **No extra smoke calls. No outcome-driven tuning.**

## Outcome handling

- **Pass** → prepare the subset-observation stage and specify the cheapest
  recipient-aware baseline using **deployment-visible inputs only**. Passing on
  clean evidence must **not** be taken to require success with the full pool.
- **Fail** → pause this experimental setup. Report the tested configuration's
  failure **without** closing the broader selection question and **without**
  declaring a universal receiver limitation.

## Not authorised

No additional models, fixture simplification, prompt search, subset executions or
Phase C. The contribution sought remains transferable selection quality at lower
execution cost; qualifying a receiver is preparation for testing that, and
**establishes no novelty**. Ledger stays 22 gated, 22 closed.
