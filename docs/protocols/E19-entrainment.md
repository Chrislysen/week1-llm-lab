# E19 — does contextual entrainment decrease with model size?

**REPLICATION. Declared 2026-09-06 with zero E19 outcomes. It tests someone
else's published claim; the contribution, if any, is the replication. A failed
replication is a fully acceptable outcome and would be recorded as one.**

## The claim under test

**arXiv:2606.24077** — *Sentence-Level Contextual Entrainment in Large Language
Models* (Yang Liu, Chenhui Chu; 23 Jun 2026), 26 LLMs from seven families, two
datasets. Two claims, tested separately here:

1. **Existence.** Sentences present in the prompt — "even if they are
   counterfactual statements" — significantly increase their own probability at
   inference, measured as the per-token mean log-probability of the sentence.
2. **Scale.** *"As the model size increases, contextual entrainment gradually
   decreases."*

Its third claim — that 2–4 % of attention heads carry the effect, and ablating
them mitigates it — needs attention access and is **not** tested here.

## Why this runtime, and not ollama

The measure requires scoring a *given* sentence. Ollama exposes logprobs for
**generated** tokens only: `num_predict: 0` still generates (49 tokens in a
probe), so there is no echo/scoring mode, and forced decoding through
`top_logprobs` silently misses targets outside the top-k — after the prefix
"The settlement engine was", the target token `cycled` is absent from the top 20.
That would bias the measurement exactly where it is most sensitive.

`torch` 2.11.0+cu128 / `transformers` 5.9.0 / CUDA on an RTX 5080 give exact
teacher-forced scoring, and the HF cache already holds **Qwen2.5-Instruct at
0.5B, 1.5B and 7B** — one family, 14× parameter range, **no download needed**.

## Measure

For target sentence S and prompt P,

    score(S | P) = (1/|S|) · Σ_t log p(s_t | P, s_<t)

teacher-forced over S's own tokens, and

    Δ = score(S | P_present) − score(S | P_absent)

**S** is the first `proposal` message of an E16 dialogue. **P_absent** replaces
that one message, in place and from the same speaker, with a fixed neutral line
("The incident channel has been quiet for the last few minutes."), so message
count and speaker alternation are preserved and the two prompts differ in
exactly one message. The instruction that follows both — "Write one sentence
about this incident." — never asks for a restatement.

144 dialogues × 2 conditions × 3 model sizes = 864 scoring passes.

## Predictions, fixed before the first run

| | claim 1 (existence) | claim 2 (scale) |
|---|---|---|
| Qwen2.5-0.5B-Instruct | Δ > 0 | largest Δ |
| Qwen2.5-1.5B-Instruct | Δ > 0 | middle Δ |
| Qwen2.5-7B-Instruct | Δ > 0 | smallest Δ |

## Read rule, fixed before the first run

The two halves are read **separately**, and either can fail alone.

- **EXISTENCE REPLICATES** if mean Δ > 0 with an instance-clustered 95 %
  bootstrap CI excluding zero, in **all three** models.
  **EXISTENCE FAILS** if any model's CI includes or sits below zero.
- **SCALE REPLICATES** if mean Δ is **monotone decreasing** across
  0.5B → 1.5B → 7B *and* the 0.5B–7B gap exceeds 0.10 nats/token.
- **SCALE FAILS** if Δ is not monotone decreasing, or the 0.5B–7B gap is
  ≤ 0.10 nats/token.

No third reading will be invented after the numbers are seen. A result where
existence replicates and scale fails is a real possible outcome, is what E18-B
would lead one to expect on this instrument, and would be reported as a
**bounding** of the published claim rather than a contradiction of it.

**Validity.** Corpus hash asserted at start. Token counts for S recorded per
row; S is identical across conditions within a model, so Δ is within-item. Any
model whose mean |S| differs from another's is still internally valid, because Δ
is a within-model difference.

**Inference.** 144 dialogues clustered by instance (36 clusters);
instance-level bootstrap, 2 000 reps, seed 20260906.

## Limits, stated in advance

Conceptual, not direct: the paper uses its own two datasets and 26 models; this
uses one incident-dialogue corpus and three models from one family. The ABSENT
filler is a fixed sentence, matched for position and speaker but **not
token-for-token in length** — a context-length difference of a few tokens
remains between conditions. Three sizes in one family cannot separate scale from
anything else that co-varies with it inside that family.

## What cannot follow

No novelty is asserted; the hypothesis is published. Nothing here bears on any
retired candidate. The attention-head claim is untested.

## Files

`e19_entrainment.py`; outputs `results/e19_<model>_o<offset>.csv`. Nothing in
E1–E18 changes.

---

## Outcome

*Pending. Zero E19 scoring passes at the time of this commit.*
