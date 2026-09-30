# E29-W: does a trailing revocation marker work by reading its record?

Declared 2026-09-30 with **zero outcomes**, before any E29-O outcome was read and before any
call on an E29-O prompt in this runtime.

## 0. Why

E29-A: a bracketed revocation placed after the proposal text is honoured, and the same marker
before the text fails, on three model families. E29-O tests six behavioural accounts of that
asymmetry. One of them, BIND, has a mechanistic reading in a causal decoder: a marker can only
read the text before it. So a trailing `[withdrawn]` can pick up which record it qualifies, and
a leading one cannot.

E29-W tests that reading directly, with attention knockout on one model's internals. If the
trailing marker's effect depends on the marker reading its record, then stopping the marker's
tokens from attending to the record's tokens should bring the revoked step back.

**Prior art:**
- Wang et al. (EMNLP 2023, arXiv:2305.14160) blocked information flow from demonstrations into
  the label words that follow them. That hurt in-context learning, most in shallow layers.
  This is the same intervention, applied here to a revocation marker and an action outcome.
- Tang et al. (arXiv:2605.30233) find removal is implemented as a sticky, order-insensitive
  suppression aggregated at the last token.

**A caveat from E29-O's review.** In a leading-marker item the record's tokens come after the
marker and can attend to it. So "a leading marker cannot bind" is too strong. `kf_pre` tests
that route directly: it blocks the record's tokens from reading the leading marker.

## 1. Design (`e29w_knockout.py`, `knockout.py`)

**Model and runtime:**
- Llama-3.2-3B-Instruct in bf16 (`unsloth/Llama-3.2-3B-Instruct`, revision
  `006f5dcd1393c3add266de40994ba96225e9689d`). These are the weights Ollama's `llama3.2:3b`
  quantises.
- transformers 5.9.0, torch 2.11.0+cu128, SDPA attention, greedy decoding. The runner refuses
  other versions.
- The prompt string is exactly what Ollama 0.34.4's llama3.2 template renders. For 300 E29-A
  prompts, the token count matches the `prompt_eval_count` Ollama recorded, 300 of 300.

**Prompts:** E29-O's, on its 192 dialogues (both E29 corpora) in the neutral arm, with E29-O's system prompt, plan
instruction, validator, one corrective retry and plan parsing. The runaway guard is 512 new
tokens.

**Conditions** (all heads; "all" = layers 0–27, "early" = 0–13, "late" = 14–27):

| condition | E29-O cell | knockout | layers |
|---|---|---|---|
| `base_open` | `open` | none | – |
| `base_sentence` | `sentence_short` | none | – |
| `base_pre` | `withdrawn_pre` | none | – |
| `base_post` | `withdrawn_post` | none | – |
| `kb_post` | `withdrawn_post` | the marker's tokens may not attend to the record's tokens | all |
| `kc_post` | `withdrawn_post` | the marker's tokens may not attend to N's tokens (control) | all |
| `kr_post` | `withdrawn_post` | no later token, prompt or generated, may attend to the marker | all |
| `kb_early` | `withdrawn_post` | as `kb_post` | early |
| `kb_late` | `withdrawn_post` | as `kb_post` | late |
| `kf_pre` | `withdrawn_pre` | the record's tokens may not attend to the marker's tokens | all |

**Spans.** Spans are character spans in the user message, mapped to tokens by offset:
- the marker is `[withdrawn]`;
- the record is the proposal sentence `A proposed to X.`;
- N is `The team's office is on the third floor.`

A token that overlaps both the marker and the record counts as the marker's. With this
tokenizer, the record's final `.` and the marker's ` [` are separate tokens.

**The knockout** is a 4D additive mask on the prompt's forward pass, applied in the chosen
layers by a pre-hook on each attention module. Generated tokens attend normally, except in
`kr_post`, where they are also barred from the marker. Retries render the conversation with
the same spans.

**Zero-data tests** (`test_knockout.py`, a tiny random Llama on CPU) assert:
- a plain causal 4D mask reproduces the default logits;
- a knockout changes only later positions;
- cached decoding under a prompt knockout in chosen layers equals recomputing every step
  with explicit per-layer masks, including when generated tokens are also blocked.

**Size:** 10 conditions × 192 dialogues = 1,920 generations. Prompt hash `dc5bf68e6b69c82a`, pinned in
the runner.

## 2. Predictions, fixed before the first call

- **Gate R holds:** in this runtime the leading marker fails more often than the trailing one,
  and the trailing one works.
- **KR is BOUND:** removing all reads of the marker brings the step back, which checks the
  machinery.
- **The reading is AT THE MARKER:** KB is BOUND and KC is FREE.
- **Exploratory:** most of KB's effect comes from the early layers (EARLY larger than LATE),
  following Wang et al.'s shallow-layer aggregation.

## 3. Read rule, fixed before the first call (`e29w_analysis.py`)

Rejected-step inclusion per condition (in `base_open`, the same step, undecided), complete-case
over the ten conditions, paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %).

**Directional classes** for d = P(a) − P(b):
- BOUND if d ≥ 0.15 with an interval excluding 0;
- REVERSED if d ≤ −0.15 with an interval excluding 0;
- FREE if the interval lies inside (−0.15, 0.15);
- UNCLEAR otherwise.

A REVERSED knockout supports no reading (UNCLEAR).

**Gate R** (there is something to explain in this runtime):
- ORDER = P(`base_pre`) − P(`base_post`) must be BOUND;
- WORKS = P(`base_open`) − P(`base_post`) must be BOUND.

If either fails, the reading is NOT READ, and that is reported as the result for this runtime.

**Knockouts on the trailing marker:**
- KR = P(`kr_post`) − P(`base_post`), the positive control;
- KB = P(`kb_post`) − P(`base_post`), the marker may not read its record;
- KC = P(`kc_post`) − P(`base_post`), the control.

| reading | KR | KB | KC |
|---|---|---|---|
| **AT THE MARKER** | BOUND | BOUND | FREE |
| **DOWNSTREAM**: the marker's content is needed, but it is tied to the record later | BOUND | FREE | FREE |
| **NON-SPECIFIC** | BOUND | BOUND | not FREE |
| **UNREADABLE**: the knockout does not remove the marker's effect | not BOUND | | |
| **UNCLEAR** | otherwise | | |

**Also reported:**
- the share of the trailing marker's effect that KB removes,
  (P(`kb_post`) − P(`base_post`)) / (P(`base_open`) − P(`base_post`)), with a bootstrap
  interval;
- exploratory two-sided contrasts: EARLY = P(`kb_early`) − P(`base_post`), LATE =
  P(`kb_late`) − P(`base_post`), and FWD = P(`kf_pre`) − P(`base_pre`) (does the leading
  marker's partial effect travel through the record?).

**Status:**
- **VOID** if a base condition parses below 0.95 or its mean |plan| is outside [3.9, 4.1].
  A knockout condition failing the same test makes its own contrast VOID, not the read.
- **INCOMPLETE** while fewer than 192 dialogues have been attempted.
- **FINAL** otherwise.

The HF base cells are compared with E29-O's Ollama `llama3.2:3b` cells on the same prompts,
descriptively only.

## 4. What each reading would mean, fixed before the first call

- **AT THE MARKER:** in this model, a trailing revocation works because its tokens read the
  record. That is the mechanism BIND proposes, and in a causal decoder a leading marker cannot
  do it.
- **DOWNSTREAM:** the marker is read at plan time and tied to the record there. The leading
  marker's failure then needs another explanation than the marker's own view of the record.
- **NON-SPECIFIC:** blocking any of the marker's reading breaks it. The record is not special.
- **UNREADABLE or NOT READ:** no mechanism claim in this runtime.

This is one model; a mechanism claim here is about Llama-3.2-3B only.
