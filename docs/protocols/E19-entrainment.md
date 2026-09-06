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

### POST-HOC — the direction is normalisation-dependent

**Not declared in advance. Computed from the same 864 scoring passes after the
declared read rule had been applied and recorded, prompted by the baseline
confound noted above.**

The confound was tested rather than merely disclaimed. Dividing each dialogue's
Δ by the magnitude of its own `absent` score — how much of the available
headroom the context closes — gives:

| Qwen2.5-Instruct | raw Δ *(the paper's measure)* | Δ ÷ \|absent\| |
|---|---|---|
| 0.5B | +3.3678 [+3.177, +3.552] | **0.7737** [0.758, 0.788] |
| 1.5B | +2.9617 [+2.761, +3.158] | **0.6699** [0.652, 0.687] |
| 7B | +3.5838 [+3.361, +3.795] | **0.4806** [0.463, 0.497] |
| | **+3.368 → +2.962 → +3.584** — non-monotone | **0.774 → 0.670 → 0.481** — monotone, CIs disjoint |

**Same data. Opposite conclusions.** On the published measure the scale claim
fails here; on a normalised version of the identical numbers it holds cleanly,
with tight non-overlapping CIs and a monotone decrease across the whole 14×
range.

**What this means, stated carefully.**

- The declared verdict **stands as recorded**: on arXiv:2606.24077's own
  measure — a raw per-token mean log-probability difference — the scale claim
  **does not replicate on this corpus**. That was decided by a rule fixed
  before the first pass and is not revised.
- The normalised analysis is **post-hoc and is one choice among several**
  (dividing by the absent baseline). Others are possible and were not tried.
  It is not evidence that the paper is right; it is evidence that **the
  direction of the answer is not determined by the data alone.**
- The defensible statement is therefore narrow and about measurement:
  **on this instrument, whether entrainment decreases with scale depends on a
  normalisation the measure does not specify.** Raw differences across models
  with different baseline likelihoods conflate "how much context helps" with
  "how unlikely the sentence was to begin with".

This is the same shape as E17's finding about menu size, and as E18-B's about
family versus scale: a published directional claim turning on a free parameter
of the measurement rather than on the models. Three times now, on this
instrument, **the measurement decided the answer.**

No novelty is asserted for the entrainment phenomenon itself, which is
published and replicated decisively here. What is recorded is a
**measure-sensitivity result about a specific published scale claim**, on three
models from one family, in a high-overlap regime — a narrow finding that would
need a fresh adversarial gate, more families and more normalisations before it
could be called anything more.

---

# E19-B — is the measure-dependence general? DECLARED with zero outcomes, 2026-09-06

E19 found that arXiv:2606.24077's scale claim fails on its own measure and
holds on a normalised version of the same numbers. **That was three models from
one family and one normalisation.** E19-B asks whether the flip is a general
property or an artefact of that particular pair.

**Additions, no downloads.** `Qwen3.5-0.8B` and `Qwen3.5-4B` are already in the
HF cache — a second, later-generation ladder. Five models total across two
families. All five are re-scored so every measure is computed from one run.

**Three measures, all from the same passes.**

| measure | definition | status |
|---|---|---|
| **M1 raw** | mean_t log p(s_t \| present) − mean_t log p(s_t \| absent) | the paper's |
| **M2 headroom** | M1 ÷ \|mean_t log p(s_t \| absent)\| | E19's post-hoc normaliser |
| **M3 linear** | mean_t p(s_t \| present) − mean_t p(s_t \| absent) | new; probability space, not log space |

M3 is added because M1 and M2 are both log-space and could share a bias; a
linear-space difference is bounded in [−1, 1] and cannot be inflated by a very
low baseline the way a log difference can.

**Read rule, fixed before the first pass.**

- **MEASURE-DEPENDENCE GENERALISES** if, within the Qwen3.5 ladder
  (0.8B → 4B), at least two of M1/M2/M3 **disagree in the sign** of the change
  with size — i.e. the same data says entrainment rises under one measure and
  falls under another, in a family independent of the one that produced the
  original flip.
- **MEASURE-DEPENDENCE IS SPECIFIC** if all three measures agree in sign in the
  Qwen3.5 ladder. The E19 flip would then be a property of the Qwen2.5 ladder,
  not of the measurement, and would be reported as such — weakening E19's
  conclusion.
- The Qwen2.5 ladder is re-reported under all three measures for completeness.
  With only two points, Qwen3.5 supports a **sign**, never a monotone trend, and
  no monotonicity will be claimed from it.

**Validity.** Corpus hash asserted. Identical prompts, filler, instruction and
seed as E19. Any model whose scoring differs from E19's recorded values on the
overlapping cells invalidates the re-run and will be reported.

**Limits.** Two families, five models, one corpus, one high-overlap regime,
three measures out of many possible. A sign flip between measures shows the
answer is measure-determined **here**; it does not establish which measure is
correct, and none of the three is argued to be.

## E19-B Outcome

**Run 2026-09-06. Verdict: MEASURE-DEPENDENCE IS SPECIFIC — the declared
outcome that WEAKENS E19. Five models, two families, 1 440 scoring passes.**

Validity check passed: re-scoring reproduced E19's recorded values exactly
(0.5B +3.3678, 1.5B +2.9617, 7B +3.5838).

| ladder | size | M1 raw *(the paper's)* | M2 headroom | M3 linear |
|---|---|---|---|---|
| Qwen2.5 | 0.5B | +3.3678 [+3.177,+3.552] | 0.7737 [0.758,0.788] | +0.4988 [+0.471,+0.524] |
| Qwen2.5 | 1.5B | +2.9617 [+2.761,+3.158] | 0.6699 [0.652,0.687] | +0.4232 [+0.396,+0.450] |
| Qwen2.5 | 7B | **+3.5838** [+3.361,+3.795] | 0.4806 [0.463,0.497] | +0.3385 [+0.320,+0.357] |
| Qwen3.5 | 0.8B | +3.3965 [+3.189,+3.602] | 0.7675 [0.754,0.780] | +0.5291 [+0.504,+0.554] |
| Qwen3.5 | 4B | +3.1260 [+2.969,+3.272] | 0.5910 [0.574,0.606] | +0.4898 [+0.467,+0.512] |

### Read rule applied

In the Qwen3.5 ladder all three measures move the **same** way with size —
M1 −0.271, M2 −0.176, M3 −0.039, all DOWN. The rule required at least two
measures to disagree in sign for the dependence to generalise. They agree.
**MEASURE-DEPENDENCE IS SPECIFIC to the Qwen2.5 ladder.**

### This substantially weakens E19, and that is the finding

Across the five measure × ladder combinations, **four replicate the scale
claim**:

| | M1 raw | M2 headroom | M3 linear |
|---|---|---|---|
| Qwen2.5 (3 points) | **not monotone** | monotone ↓ | monotone ↓ |
| Qwen3.5 (2 points) | ↓ | ↓ | ↓ |

The single failure is **M1 in the Qwen2.5 ladder**, and it is produced by one
model: Qwen2.5-7B-Instruct, whose baseline is far lower than the rest
(`absent` −7.30 against −4.30 / −4.32 / −4.37 / −5.23). A raw log difference
grows when the baseline falls, so that one model inflates M1 and nothing else.

**E19's headline verdict — "SCALE FAILS" — therefore stands only on the
paper's own measure, in one ladder, on the strength of one model's baseline.**
It was reported as a bounding rather than a refutation, which was right, but
E19-B shows it is narrower still: **arXiv:2606.24077's scale claim replicates
on this instrument** under two of three measures in one family and all three in
the other.

The claim in the E19 post-hoc section — that "the direction of the answer is
not determined by the data alone" — is **withdrawn as stated**. It is true of
M1 versus M2 on the Qwen2.5 ladder and false everywhere else tested. What
survives is much smaller and purely methodological:

> A raw per-token log-probability difference is fragile to baseline shifts
> between models. Where one model assigns much lower probability to the target
> in both conditions, its raw Δ is inflated, and a scale comparison built on
> raw Δ can inherit that inflation. Two of the three measures here are immune
> to it and both agree with the published direction.

### What survives from E19 and E19-B together

- **Contextual entrainment exists, decisively** — mean Δ > 0 with CIs excluding
  zero in **all five models**, positive in **144/144 dialogues in every one**.
  arXiv:2606.24077's existence claim replicates without qualification here.
- **Its scale claim also replicates**, under every measure except the one
  fragile case above.
- **No novelty.** The attempt to find a measure-dependence result did not
  survive its own follow-up. This is recorded as a closed line.

### Limits

Two families, five models, one corpus, one high-overlap regime, three measures.
Qwen3.5 has two points and supports a sign only — no monotone trend is claimed
from it. The attention-head claim remains untested.

### Files

`results/e19_{Qwen2.5-0.5B-Instruct,Qwen2.5-1.5B-Instruct,Qwen2.5-7B-Instruct,Qwen3.5-0.8B,Qwen3.5-4B}_o0.csv`.
