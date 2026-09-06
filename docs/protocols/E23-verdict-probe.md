# E23 — is the dialogue verdict ABSENT, or PRESENT BUT UNREAD?

**Declared 2026-09-06 with zero E23 outcomes. Gated SURROUNDED (A-1) and run
anyway because the ANSWER is unknown and decision-relevant. NOT a novelty
claim; the SURROUNDED verdict stands whatever this returns.**

## Why the answer matters

**arXiv:2608.23651** decomposes small-model repetition of a failed call
behaviourally: *"the failed call's surface form accounts for 83 % of the damage,
while the semantic contribution of marking it failed is small."* That is equally
consistent with two situations it cannot distinguish, because it is behavioural:

- **ABSENT** — the model never computes the verdict.
- **PRESENT BUT UNREAD** — it computes it, and the output distribution ignores it.

If present-but-unread, revocation inertia is addressable at decoding time. If
absent, it is not. E21 and E22 established the behavioural fact on this
instrument (verdict effect +0.069 at 0.5B against +0.652 at 4B) but cannot tell
these apart either.

The knowledge-action gap itself is published — **arXiv:2603.18353** measures
probes at 98.2 % AUROC against 45.1 % output sensitivity, a 53-point gap — but
in **clinical triage**, on 7–8B models, with no dialogue or constraint verdicts.

## Design

For each of the 384 E16 units: the frozen plan prompt, then `{"actions": ["`,
then the unit's own action identifier. Residual-stream activation at the **last
token of that identifier**, so the representation is specific to that action in
that dialogue. Label = the unit's status. 96 units per status, exactly balanced.

Three pairs, of which the first is decisive:

| pair | what it isolates |
|---|---|
| **rejected vs proposed** | identical context except the verdict — mention held constant |
| rejected vs accepted | the wider verdict contrast |
| rejected vs never | mention-plus-verdict against no mention |

Logistic regression per layer, **GroupKFold by instance** (36 groups, 6 folds),
so no dialogue from a training instance appears in test. AUROC reported per
layer; the headline is the best layer.

Models: **Qwen2.5-0.5B-Instruct** (behavioural verdict effect **+0.069**, near
zero) and **Qwen3.5-4B** (**+0.652**, large).

## Read rule, fixed before extraction

Read on the **rejected vs proposed** pair, against that model's behavioural
verdict effect:

- **PRESENT BUT UNREAD** if best-layer AUROC ≥ **0.75** while the behavioural
  verdict effect is < **0.15 nats**. The information is there and the output
  distribution does not use it.
- **ABSENT** if best-layer AUROC ≤ **0.60** — at or near chance, nothing to read.
- **PARTIAL** for anything between, recorded as partial.
- For a model with a large behavioural effect (Qwen3.5-4B), a high AUROC is
  **expected and uninformative** — it is included as a positive control that the
  probe and pipeline work at all, not as a test.

No fourth reading will be invented after the numbers are seen.

## Limits, stated in advance

A linear probe finding information does not show the model *could* use it, only
that it is linearly available at that site. Best-layer selection across ~25
layers is a multiple-comparison over layers; the full per-layer curve is
reported so the peak can be judged against the rest. One corpus, one prompt
position, two models. Probing at the identifier's last token is one choice of
site among many. AUROC above chance on `rejected vs proposed` could reflect
surface features of the reply template rather than a verdict representation —
the templates differ in wording, and this design cannot rule that out.

## Files

`e23_verdict_probe.py`; outputs `results/e23_probe_<model>.json`.

---

## Outcome

*Pending. Zero E23 extractions at the time of this commit.*

---

## Outcome

**Run 2026-09-06. Verdict on the declared rule: PARTIAL for Qwen2.5-0.5B —
but the informative result is the pattern across the two models, which points
away from "present but unread".**

| model | rejected vs **proposed** (verdict) | rejected vs accepted | rejected vs **never** (presence) | behavioural verdict effect |
|---|---|---|---|---|
| Qwen2.5-0.5B-Instruct | **0.6393** (L2) | 0.6555 (L19) | **0.9978** (L16) | **+0.069 nats** |
| Qwen3.5-4B | **0.9998** (L16) | 0.9992 (L16) | **1.0000** (L12) | **+0.652 nats** |

### Read rule applied

Qwen2.5-0.5B's decisive AUROC is **0.639** — above the 0.60 "ABSENT" line and
below the 0.75 "PRESENT BUT UNREAD" line. **PARTIAL**, recorded as partial. No
fourth reading is invented.

Qwen3.5-4B was declared a **positive control**, and it passes: 0.9998 with a
large behavioural effect. The pipeline can find a verdict representation when
one is there.

### What the pattern shows: a correspondence, not a gap

Within the same activations at the same site, the 0.5B decodes **presence at
0.998** and the **verdict at 0.639**. So the weak verdict AUROC is not a probe
or pipeline failure — the identical probe on the identical vectors reads
presence essentially perfectly.

And across the two models, representation and behaviour move **together**:

    verdict AUROC   0.639  ->  0.9998
    verdict effect  +0.069 -> +0.652 nats

This is the **opposite** of the knowledge-action gap that arXiv:2603.18353
measures in clinical triage (probes 98.2 % AUROC against 45.1 % output
sensitivity, a 53-point gap). Here there is **no gap to exploit**: the small
model's output ignores the verdict because the verdict is barely encoded, not
because it is encoded and unread.

### Why that is worth knowing

arXiv:2608.23651 established behaviourally that for small models "the failed
call's surface form accounts for 83 % of the damage, while the semantic
contribution of marking it failed is small", but a behavioural decomposition
cannot say **why** the semantic contribution is small. These two candidate
explanations have opposite practical consequences:

- *present but unread* → addressable at decoding time, by reading the existing
  representation out;
- *barely represented* → **not** addressable that way; the information is not
  there to read.

On this instrument the evidence favours the second. **Decoding-time or
steering-style fixes for revocation inertia should not be expected to work at
this scale**, which is a concrete negative prediction that follows from the
measurement.

### The confound I declared in advance, and how it fares

I stated before extraction that AUROC on `rejected vs proposed` could reflect
**surface features of the differing reply templates** rather than a verdict
representation. That confound is not excluded, and it is the main threat here.

It is, however, weakened by the within-model comparison: both templates are
equally present in context for both models, and the 0.5B reads *presence* from
the same vectors at 0.998 while reading *verdict* at 0.639. Pure surface
availability would not produce that split. It is not eliminated, because the
presence cue sits at the scored identifier's own position while the verdict cue
sits in a different message, so the two differ in retrieval difficulty as well
as in kind.

### Limits

Two models, one corpus, one probe site, one prompt position. Best-layer
selection is a multiple comparison over 25 and 33 layers — the full per-layer
curves are in the result files, and for the 0.5B the peak (0.639 at L2) is
barely above the final layer (0.619), so there is no sharp localised signal to
over-read. A probe finding information does not show the model *could* use it.
The two models differ in family and architecture as well as scale, so this is
**not** a scale claim.

**No novelty is asserted.** A-1 was gated SURROUNDED before this ran and that
verdict is unchanged.

### Files

`results/e23_probe_Qwen2.5-0.5B-Instruct.json`,
`results/e23_probe_Qwen3.5-4B.json`.

---

# E23-B — does the correspondence hold across a curve? DECLARED, zero outcomes

E23 rested on **two** models that differ in family and architecture as well as
scale, so "representation tracks behaviour" was a suggestive pair, not a curve.
E23-B fills it in.

**Models.** Qwen2.5-Instruct **0.5B / 1.5B / 7B** and Qwen3.5 **0.8B / 4B** —
two within-family ladders, so scale is separable from family for the first time
in this line.

**The two quantities**, both already defined and both measured on the same
corpus: probe AUROC on `rejected vs proposed` (representation) and the
behavioural verdict effect `proposed − rejected` in nats (behaviour).

**Read rule, fixed before the new runs.**

- **CORRESPONDENCE HOLDS** if across the five models the two quantities are
  monotonically related (Spearman ρ ≥ 0.80) **and** within the three-point
  Qwen2.5 ladder they move in the same direction.
- **CORRESPONDENCE FAILS** if any model shows a genuine **gap** — probe AUROC
  ≥ 0.85 together with a behavioural verdict effect < 0.15 nats. That model
  would be a knowledge-action gap of the kind arXiv:2603.18353 reports, and
  would overturn E23's conclusion for this phenomenon.
- **INCONCLUSIVE** otherwise, recorded as such.

A CORRESPONDENCE FAILS outcome is the more interesting one and is actively
sought: it would mean the information *is* present and unread in some model,
and that decoding-time repair is worth trying after all.

**Limits.** Five models, two families, one corpus, one probe site. Spearman on
n = 5 is weak; the within-family direction check carries most of the weight.
The reply-template surface confound from E23 applies unchanged.

## E23-B Outcome

**Run 2026-09-06. Verdict: CORRESPONDENCE FAILS. Two models show a genuine
knowledge-action gap, and E23's conclusion is corrected.**

| model | **verdict AUROC** (rej vs prop) | presence AUROC (rej vs never) | **behavioural verdict effect** | gap? |
|---|---|---|---|---|
| Qwen2.5-0.5B-Instruct | 0.6393 | 0.9978 | +0.069 | — |
| Qwen3.5-0.8B | **0.8630** | 0.9992 | **−0.058** | **YES** |
| Qwen2.5-1.5B-Instruct | **0.9353** | 1.0000 | **+0.121** | **YES** |
| Qwen3.5-4B | 0.9998 | 1.0000 | +0.652 | — |

Gap = probe AUROC ≥ 0.85 with behavioural verdict effect < 0.15 nats, as
declared. Spearman(AUROC, behaviour) = 0.800, p = 0.200 on n = 4 — the HOLDS
branch is not reached and would not have been convincing at this n anyway; the
**FAILS** branch fires on the gap models and does not depend on Spearman.

### The correction to E23

E23 concluded, from two models, that the verdict is *barely represented* rather
than *present but unread*, and drew the practical inference that decoding-time
repair should not be expected to work. **With the curve filled in, that is
wrong.** It was an artefact of having sampled only the two endpoints: 0.5B
(low AUROC, low behaviour) and 4B (high, high). The two intermediate models
sit exactly where E23 assumed nothing was.

### What the four models actually show

**Presence is fully represented at every scale** — AUROC 0.998, 0.999, 1.000,
1.000. It never varies. Whatever changes with scale, it is not whether the
model encodes that an action was mentioned.

**Verdict representation saturates far earlier than verdict behaviour:**

    verdict AUROC    0.639  ->  0.863  ->  0.935  ->  0.9998
    behaviour (nats) +0.069 -> -0.058  -> +0.121  -> +0.652

By 1.5B the verdict is **93.5 % decodable** while the output distribution moves
it only **+0.121 nats**. Qwen3.5-0.8B is starker: **86.3 % decodable** with a
behavioural effect of **−0.058** — the information is there and the output
does not use it at all.

**So there is a scale window in which the verdict is present and unread.** That
is a knowledge-action gap of exactly the kind arXiv:2603.18353 reports in
clinical triage (98.2 % AUROC against 45.1 % output sensitivity), now observed
for dialogue verdicts, and located: it opens once representation saturates and
closes when behaviour catches up.

### Why this matters for arXiv:2608.23651

That paper tests models of **135M–1.7B** and finds "the failed call's surface
form accounts for 83 % of the damage, while the semantic contribution of marking
it failed is small". **Its entire range sits inside the gap window measured
here.** Its finding is about *behaviour*, and the natural reading — that the
semantics are not computed — is the reading E23 initially took and E23-B
overturns. On this instrument the semantics *are* computed in that range; they
are not used.

That reverses the practical prediction. **Decoding-time or steering repair is
worth trying in the 0.8B–1.5B window**, because the verdict is 86–94 %
linearly decodable while the output ignores it. E23's opposite prediction is
withdrawn.

### Limits

Four models, two families, one corpus, one probe site; no 7B point, so the
Qwen2.5 ladder has two points rather than three and the declared within-family
check is weaker than intended. Extraction for Qwen2.5-7B-Instruct segfaulted at
a 13 GiB cap and ran at 9 GiB but at roughly 12 s per unit — about a dozen
sequential foreground runs — and was abandoned on cost once the FAILS branch was
already determined by two models.

The **reply-template surface confound declared in E23 still applies and is now
more pressing**, because the claim rests on high AUROC: the probe may be reading
the differing wording of acceptance and rejection replies rather than a verdict
representation. Against that, presence AUROC is ~1.0 in every model while
verdict AUROC varies from 0.64 to 1.00, so the probe is not simply reading
"something differs in context" — but a template-driven account is not excluded
and would need a paraphrase-matched corpus to rule out.

Spearman on n = 4 is not evidence. The gap classification depends on thresholds
I chose in advance; both gap models sit clearly inside them, but 0.8630 is near
the 0.85 line.

**No novelty is asserted.** A-1 remains SURROUNDED. What this adds is a located
mechanism and a reversed practical prediction for a two-week-old paper.

### Files

`results/e23_probe_{Qwen2.5-0.5B-Instruct,Qwen3.5-0.8B,Qwen2.5-1.5B-Instruct,Qwen3.5-4B}.json`.
