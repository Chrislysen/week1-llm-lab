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
