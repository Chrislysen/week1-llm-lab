# E26 — can the unused verdict be RECOVERED by steering?

**Declared 2026-09-07 with zero E26 runs. This tests a prediction I made myself,
against a published negative. Either outcome is informative and both are
recorded.**

## The prediction under test is mine

E23-B/C established that at 0.8B–1.5B the dialogue verdict is **86–94 % linearly
decodable and action-bound** (within-dialogue paired accuracy 0.800 and 0.883,
context byte-identical), while the output distribution barely uses it —
behavioural verdict effect **−0.058** and **+0.121** nats. From that I predicted
that **decoding-time repair should work**. E26 tests it.

## And against a published negative

**arXiv:2603.18353** reports probes at 98.2 % AUROC against 45.1 % output
sensitivity in clinical triage, and finds steering largely **fails** to close the
gap: *"concept bottleneck steering corrected 20 % of missed hazards but disrupted
53 % of correct detections."*

- If steering works here → this is a domain where the knowledge-action gap **is**
  actionable, contrasting with their result.
- If it fails → a **replication of their negative** in a new domain, and my own
  prediction is wrong.

## Method

Fit the same logistic probe E23 used (`rejected` vs `proposed`) at the model's
best layer — **layer 13** for Qwen3.5-0.8B, **layer 18** for Qwen2.5-1.5B — on
**SEARCH** instances only. Take its unit-norm weight vector as the verdict
direction and add `α·ŵ` to that layer's residual-stream output at every token
position. Measure on **HELD-OUT** instances the same quantity as E22/E23:

    VERDICT EFFECT = a(proposed) − a(rejected)

`a()` being the mean per-token log-probability of the unit's action identifier at
first-plan position.

**Controls.** The negative direction `−α·ŵ`, which should move the effect the
opposite way if the direction is real; and **random unit directions** at the same
α, which should not move it at all.

## Read rule, fixed before the first run

Let `e₀` be the baseline verdict effect and `e₊`, `e₋` the effects under `+α` and
`−α` at the best-performing α.

- **STEERING RECOVERS THE VERDICT** if `e₊ − e₀ ≥ +0.15` nats, `e₊ − e₀` exceeds
  every random-direction delta, and `e₋ − e₀` is negative (the direction is
  signed, not a generic perturbation).
- **STEERING FAILS** if `e₊ − e₀ < +0.05`, or if it does not exceed the random
  controls. My prediction is then wrong and arXiv:2603.18353's negative
  replicates here.
- **NON-SPECIFIC** if the effect moves but random directions move it comparably.
- **PARTIAL** otherwise, recorded as partial.

**Validity.** `accepted` must not collapse: if `a(accepted)` degrades by more
than 1.0 nat under steering, the intervention has broken the model rather than
recovered a channel, and the cell is reported as damaged regardless of the
verdict effect. This is the analogue of arXiv:2603.18353's "disrupted 53 % of
correct detections" and is the failure mode most likely to occur.

## Limits, stated in advance

Two models, one corpus, one layer per model, one probe family, a linear steering
vector applied uniformly at all positions. α is searched over a small grid, which
is a multiple comparison; the random controls use only the largest α. A positive
result would show the channel is *usable*, not that this is a good way to use it.

## Files

`e26_steer.py`; outputs `results/e26_steer_<model>.json`.

---

## Outcome

*Pending. Zero E26 runs at the time of this commit.*

---

## Outcome

**Run 2026-09-07. Verdict: STEERING FAILS, in both models. My prediction from
E23-B/C is wrong, and arXiv:2603.18353's negative replicates in this domain.**

### Qwen2.5-1.5B-Instruct (layer 18), baseline verdict effect +0.1212

| α | verdict effect | delta | `accepted` damage |
|---|---|---|---|
| **+10** | +0.0241 | −0.0971 | +0.174 |
| **−10** | +0.1647 | +0.0435 | −0.020 |
| **+30** | **−0.0914** | **−0.2127** | +0.613 |
| **−30** | +0.1747 | +0.0535 | +0.149 |
| random ×3 @30 | — | −0.053, −0.069, **+0.068** | — |

### Qwen3.5-0.8B (layer 13), baseline verdict effect −0.0583

| α | delta |
|---|---|
| +10 / −10 | +0.048 / +0.034 |
| +30 / −30 | +0.054 / +0.057 |
| random ×3 @30 | +0.053, +0.055, **+0.058** |

### Read rule applied

**RECOVERY fails in both.** The recovering direction gives **+0.0535** in the
1.5B — below the declared +0.15 threshold *and* below the largest random delta
(+0.0679). In the 0.8B every intervention, signed or random, moves the effect by
the same ~+0.05, which is **NON-SPECIFIC** by definition: the direction carries
no information the model uses.

The validity condition did not fire — `accepted` degraded by at most 0.613 nats,
under the declared 1.0 limit — so this is a genuine null, not a broken model.

### The one real asymmetry, and it cuts against recovery

In the 1.5B the verdict direction **is causally potent in one direction only**.
Steering *along* it collapses verdict sensitivity to **−0.0914** — a delta of
**−0.213**, three times the largest random perturbation (0.069). Steering
*against* it recovers nothing beyond noise.

**The channel can be destroyed but not amplified.** A linearly decodable,
action-bound representation that a single direction can suppress, and that no
amount of pushing the same direction backwards can make the model use.

### What this does to the E23 line

E23-B/C stand: the verdict **is** 86–94 % decodable and action-bound while
behaviourally unused. That measurement is unaffected.

**The practical inference I drew from it does not.** I wrote that
"decoding-time or steering repair IS worth trying in the 0.8B–1.5B window,
because the verdict is 86–94 % linearly decodable while the output ignores it."
**That prediction is now tested and false**, at least for linear residual-stream
steering along the probe direction. It is withdrawn.

This is a **replication of arXiv:2603.18353's central negative** — probes find
what steering cannot fix — in a new domain (dialogue verdicts rather than
clinical triage) and at a much smaller scale (0.8–1.5B rather than 7–8B). Their
"interpretability without actionability" holds here.

### Limits

Two models, one corpus, one layer each, one probe family, a single linear vector
applied uniformly at all token positions. α was searched over {2, 10, 30}, a
multiple comparison, and random controls were run only at α = 30. Failure of
*this* intervention does not show the channel is unusable by any method —
non-linear probes, per-position steering, attention-level edits or fine-tuning
are untested. What is shown is that the obvious intervention, the one my own
prediction named, does not work.

**No novelty is asserted.**
