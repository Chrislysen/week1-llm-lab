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

**Run 2026-09-06. EXISTENCE REPLICATES. SCALE FAILS.** 864 scoring passes,
144 dialogues x 2 conditions x 3 sizes, corpus hash asserted.

| Qwen2.5-Instruct | mean Δ | 95 % CI (instance-clustered) | median | Δ > 0 | mean \|S\| | present | absent |
|---|---|---|---|---|---|---|---|
| 0.5B | **+3.3678** | [+3.1769, +3.5518] | +3.6384 | 144/144 | 15.5 | −0.9345 | −4.3023 |
| 1.5B | **+2.9617** | [+2.7611, +3.1575] | +3.0763 | 144/144 | 15.5 | −1.3579 | −4.3196 |
| 7B | **+3.5838** | [+3.3613, +3.7954] | +3.6392 | 144/144 | 15.5 | −3.7123 | −7.2961 |

### Read rule applied

- **EXISTENCE REPLICATES.** Δ > 0 with the CI excluding zero in all three
  models, and positive in **144/144 dialogues in every model**. A sentence
  present in the prompt raises its own probability, decisively, at every size
  tested.
- **SCALE FAILS.** The sequence is **+3.368 → +2.962 → +3.584**: not monotone
  decreasing, and the 0.5B–7B gap is **−0.216**, i.e. the *largest* model shows
  the *most* entrainment. The declared rule required monotone decrease and a
  gap above +0.10.

**The pre-declared insensitivity clause does not apply.** It required all three
models above 3 nats/token with a small spread; 1.5B is 2.96 and the spread is
0.62 nats — six times the decision threshold. More importantly, a copying
ceiling compresses values *toward each other*; it does not produce a
**reversal**. The failure is directional, not a compression artefact.

### A confound in this result, against its own conclusion

The Δ measure is a raw difference of two per-token means, and **both baselines
move with model size**. For the 7B, `present` is −3.71 and `absent` is −7.30,
against −0.93 / −4.30 for the 0.5B. The 7B simply assigns much lower
probability to this sentence in *both* conditions; its larger Δ is produced by
an `absent` score that falls further than its `present` score.

Whether that counts as "more entrainment" depends on a normalisation the
original measure does not make — and arXiv:2606.24077 uses the same raw
per-token mean difference, so this replication is faithful to the published
measure. But a scale comparison of raw differences across models with different
baseline likelihoods is **not clean**, and this caveat cuts against the
conclusion drawn here, not for it. It is recorded because it weakens the
result.

### What this does and does not show

It **bounds** rather than refutes. arXiv:2606.24077's scale claim is a trend
across **26 models from seven families** on two datasets. E19 is **three models
from one family** on one incident-dialogue corpus, in a high-overlap regime
where the target sentence appears verbatim. A within-family non-monotonicity
does not falsify a cross-family trend; it shows the trend does not hold here.

Consistent with E18-B, which found on this same instrument that between-family
variation exceeded within-family scale variation for a different measure: on
this benchmark, **scale is repeatedly not the controlling variable.**

The attention-head claim (2–4 % of heads carry the effect) is untested.

### Runtime note

The 7B was scored with `device_map="auto"` and a 13 GiB GPU cap, spilling some
layers to CPU — 15.2 GB of bf16 weights segfaulted a 16 GB card on a direct
load. Weights are exact bf16 in both cases; offload changes placement, not
numerics. Quantised weights were deliberately **not** used, because int8 would
have introduced a quantisation difference into precisely the scale comparison
under test.

### Files

`results/e19_Qwen2.5-{0.5B,1.5B,7B}-Instruct_o0.csv`. Nothing in E1–E18 changed.

### Sensitivity note — added after a 3-dialogue smoke test, before the full run

A 3-dialogue smoke test on Qwen2.5-0.5B-Instruct returned mean Δ = **+4.52
nats/token** (present −1.27, absent −5.79, 3/3 positive). That is a very large
effect, and it is large for a structural reason: **S appears verbatim in the
PRESENT prompt**, so scoring it as a continuation is close to a copying task.

This is disclosed now, before the full run, because it bears on the **scale**
half. If all three models sit near a copying ceiling, Δ will be compressed and
the 0.10 nats/token gap may fail to appear **for reasons of design
insensitivity rather than evidence about scale**. Should SCALE FAIL with all
three models showing large Δ (> 3 nats/token) and a small spread, it will be
reported as **an insensitive test, not as evidence against arXiv:2606.24077.**

The read rule above is **not changed**. This note only fixes, in advance, how a
null on the scale half is to be interpreted — so that interpretation cannot be
chosen after the numbers are seen.
