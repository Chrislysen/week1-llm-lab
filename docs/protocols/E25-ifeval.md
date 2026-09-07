# E25 — does the type-by-length confound appear on IFEval's real items?

**Declared 2026-09-07 with zero E25 generations. Closes the standing objection
to E24/E24-C: those used 16 hand-written constraints. This uses IFEval's actual
541 prompts and its actual instruction types. NOT a novelty claim; T-2 remains
NARROW.**

## Classification, from IFEval's own instruction ids and kwargs

| kind | IFEval instruction ids | n obs |
|---|---|---|
| **inclusion** — easier when longer | `keywords:existence`, `keywords:frequency` (relation *at least*), `length_constraints:number_words` (relation *at least*) | **104** |
| **exclusion** — harder when longer | `keywords:forbidden_words`, `punctuation:no_comma`, `keywords:frequency` (*less than*), `length_constraints:number_words` (*less than*) | **144** |

215 of the 541 prompts carry at least one analysed instruction. Every other
instruction type — formatting, casing, language, structure, combination — is
length-neutral or ambiguous and is **excluded from the analysis rather than
guessed at**.

Scoring is IFEval's **instruction-level** convention: each target instruction is
verified independently, so a prompt with several contributes one observation
each. Verifiers reimplement IFEval's semantics from its `kwargs`.

## Prediction, fixed before the first generation

Across models, mean response length should correlate **positively** with
inclusion satisfaction and **negatively** with exclusion satisfaction.

## Read rule, fixed before the first generation

Over the models run (≥ 4):

- **CONFOUND CONFIRMED ON REAL ITEMS** if the sign of the correlation between
  mean response words and satisfaction is **positive for inclusion and negative
  for exclusion**, and the two type-specific rates are separated by more than
  their 95 % intervals in at least one model.
- **NOT CONFIRMED** if the two correlations share a sign, or neither separates.
- **INCONCLUSIVE** otherwise.

Secondary, descriptive: the aggregate an IFEval-style report would give at
inclusion:exclusion mixes of 25:75, 50:50, 75:25, with intervals, and whether
any model ordering changes beyond those intervals.

## Limits, stated in advance

Response length here is **not manipulated** — it is each model's natural output
on IFEval's own prompts, so length is confounded with everything else that
differs between models. E24 supplies the manipulated-length evidence; E25 tests
whether the pattern shows up on real items. Some IFEval prompts carry an
explicit length instruction, which is itself one of the analysed types; that is
inherent to the benchmark and is not corrected for. Verifiers are a
reimplementation, not IFEval's official harness, so absolute rates are not
comparable to published IFEval numbers — only the between-type contrast is used.

## Files

`e25_ifeval.py`; outputs `results/e25_<model>_o<offset>.csv`.

---

## Outcome

*Pending. Zero E25 generations at the time of this commit.*

---

## Outcome — COMPLETED. Verdict: NOT CONFIRMED. This corrects E24's practical claim.

**Run 2026-09-07. Five models, the same first 45 IFEval prompts, identical
runaway cap. 30 inclusion and 25 exclusion observations per model.**

### The blocker, and the fix

The first attempt stalled repeatedly. Timing each prompt found a single
pathological item — key 1132, *"write the lyrics to a hit song ... in all
capital letters"* — on which small models loop indefinitely, consuming 515 s
before being killed. A **runaway guard** of `num_predict = 1500` (~1100 words,
far above IFEval's longest "at least 500 words" constraint) removed it. Added to
`robust_client.chat` as an **opt-in parameter defaulting to None**, so every
earlier experiment's behaviour is byte-unchanged; 135 tests still pass.
`llama3.2:3b` was re-run under the cap for comparability (306.0 words against
311.7 uncapped — it never hit the cap).

### Results on IFEval's real items

| model | mean words | inclusion | exclusion |
|---|---|---|---|
| llama3.2:3b | 306.0 | 0.967 ±0.064 | 0.960 ±0.077 |
| gemma4:e4b | 302.9 | 0.933 ±0.089 | 1.000 ±0.000 |
| aya-expanse:8b | 275.8 | 0.767 ±0.151 | 0.640 ±0.188 |
| qwen2.5:7b-instruct | 232.6 | 0.633 ±0.172 | 0.920 ±0.106 |
| qwen2.5:3b-instruct | 224.3 | 0.567 ±0.177 | 0.680 ±0.183 |

    Spearman(words, inclusion) = +1.000  p = 0.000   predicted POSITIVE  ✓
    Spearman(words, exclusion) = +0.600  p = 0.285   predicted NEGATIVE  ✗

**NOT CONFIRMED**, by the rule fixed before the first generation.

### What this means — a correction to E24's practical claim

The inclusion half is as strong as it could be: a **perfect rank correlation**
between how much a model writes and how often it satisfies inclusion
constraints, on the benchmark's own items.

The exclusion half fails, and the reason is instructive. **On real items,
verbosity and capability are positively correlated**: the models that write more
are also simply better, so they beat the length penalty on exclusion constraints
rather than succumbing to it. The mechanism E24 established — real, large, and
within-model under *manipulated* length — is **swamped between models** by
capability differences.

So the practical concern is **narrower than E24-C implied**:

> The type-by-length confound bites where response length varies for reasons
> other than capability — length-instructed items, verbosity tuning, decoding
> settings, prompt-format changes. It does **not** distort ordinary model
> rankings on IFEval, because there the more verbose models are also the more
> capable ones.

That is a correction to my own framing, produced by the first test of it on real
benchmark data.

### Secondary: mix does move rank, within noise

    25:75   gemma(0.983) > llama(0.962) > qwen7b(0.848) > aya(0.672) > qwen3b(0.652)
    75:25   llama(0.965) > gemma(0.950) > aya(0.735)    > qwen7b(0.705) > qwen3b(0.595)

gemma and llama swap, and aya passes qwen7b. Both margins are far inside the
confidence intervals above, so nothing is claimed from them — the same
limitation E24-C recorded.

### Limits

45 of 215 analysable prompts, so n = 30/25 per model; the intervals are wide
(±0.06 to ±0.19). Verifiers reimplement IFEval's semantics from its `kwargs`
and are not its official harness, so absolute rates are not comparable to
published IFEval numbers — only the between-type contrast is used, which is what
the design needs. Length is natural, not manipulated, which is the point of the
test and also its main confound. `gemma4:e4b` is at ceiling (1.000) on exclusion.

**No novelty is asserted.** T-2 remains NARROW.

### Files

`results/e25_{llama32-3b,qwen25-3b-instruct,qwen25-7b-instruct,gemma4-e4b,aya-expanse-8b}_o0.csv`.
