# E20 — do 2–4 % of attention heads carry contextual entrainment?

**MECHANISTIC REPLICATION. Declared 2026-09-06 with zero E20 outcomes. It tests
someone else's published claim. A failed replication is an acceptable outcome
and would be recorded as one. No novelty is asserted.**

## The claim under test

**arXiv:2606.24077** — *Sentence-Level Contextual Entrainment in Large Language
Models* (Liu & Chu, 23 Jun 2026), third claim:

> "contextual entrainment is controlled by 2 % to 4 % of the attention heads.
> Turning off these attention heads can effectively mitigate contextual
> entrainment without hurting the model's performance."

E19 replicated the paper's **existence** claim decisively and E19-B its
**scale** claim. This is the one claim left untested, and it is the strongest of
the three: it is causal and mechanistic, not correlational.

## Model and heads

`Qwen2.5-0.5B-Instruct`: 24 layers × 14 attention heads = **336 heads**, so
2–4 % is **7–13 heads**. Ablation is by zeroing a head's slice of the `o_proj`
input (`head_dim` = 64) through a forward pre-hook — verified to change logits
and to restore exactly on removal.

## Design

The entrainment measure is E19's, unchanged: Δ = mean per-token log-probability
of the target sentence with it present in the prompt minus with it absent.

**Instance-level split, no leakage.** The 144 dialogues are 36 instances × 4
rotations. Instances 0–17 (dialogues 0–71) are the **SEARCH** set; instances
18–35 (dialogues 72–143) are **HELD-OUT**. Heads are selected on SEARCH only and
every reported effect is measured on HELD-OUT.

1. **Sweep.** For each of the 336 heads individually, ablate it and recompute
   mean Δ on a 12-dialogue subsample of SEARCH. Rank heads by Δ reduction.
2. **Ablate together.** Take the top **k = 10** heads (**2.98 %**, the midpoint
   of the paper's 2–4 %) and ablate them jointly. Measure mean Δ on the full
   72-dialogue HELD-OUT set.
3. **Specificity control.** 20 random sets of 10 heads, each measured on
   HELD-OUT, giving a null distribution for "any 10 heads".
4. **Performance check.** Mean `score_absent` on HELD-OUT under the top-10
   ablation against baseline — the model's ordinary next-token behaviour with
   no target sentence in context.

## Read rule, fixed before the first sweep pass

Let Δ₀ be baseline mean Δ on HELD-OUT and Δ_k that under top-10 ablation.

- **MECHANISM REPLICATES** if all three hold:
  **(a)** relative reduction (Δ₀ − Δ_k)/Δ₀ ≥ **0.30**;
  **(b)** that reduction exceeds the **95th percentile** of the 20 random
  10-head sets;
  **(c)** mean `score_absent` degrades by less than **0.5 nats/token**.
- **MECHANISM FAILS** if (a) fails — a small head set does not mitigate
  entrainment here.
- **SPECIFICITY FAILS** if (a) holds but (b) does not: the effect is real but
  any 10 heads would do it, which is a different claim from the paper's.
- **PERFORMANCE COST** if (a) and (b) hold but (c) does not: entrainment is
  mitigated, but not "without hurting the model's performance".

No fifth reading will be invented after the numbers are seen.

## Limits, stated in advance

One model, one family, one corpus, one high-overlap regime. k is fixed at 10
rather than searched, so no claim is made about the *minimum* sufficient set.
Ablation is zeroing at `o_proj` input; other ablation conventions (mean-patching,
resample-ablation) may behave differently and are not tried. The paper's own
head-identification procedure is not reproduced — only its claim's substance.
`score_absent` is a narrow performance proxy, not a benchmark suite, so (c) is a
weak test of "without hurting performance" and a pass on it should not be read
as a strong one.

## Files

`e20_heads.py`; outputs `results/e20_sweep_*.csv`, `results/e20_heldout.json`.
Nothing in E1–E19 changes.

---

## Outcome

*Pending. Zero E20 passes at the time of this commit.*
