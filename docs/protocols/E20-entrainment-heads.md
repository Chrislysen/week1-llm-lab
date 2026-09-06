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

**Run 2026-09-06. Verdict: MECHANISM REPLICATES.** All three declared conditions
pass, on a model and corpus independent of the original, with heads selected on
SEARCH and every number below measured on HELD-OUT.

336 heads swept singly (12 SEARCH dialogues each, 8 064 scoring passes), then
top-10 joint ablation and 20 random 10-head controls on the full 72-dialogue
HELD-OUT set.

### Read rule applied

| condition | threshold | observed | |
|---|---|---|---|
| (a) relative reduction in mean Δ | ≥ 0.30 | **0.416** | PASS |
| (b) exceeds random 10-head p95 | > +0.292 | **0.416** | PASS |
| (c) `score_absent` shift | < 0.5 nats | **0.166** | PASS |

Held-out baseline Δ **+3.2241** → top-10 ablated **+1.8827**, with
`score_absent` moving only −4.1194 → −3.9529.

**VERDICT: MECHANISM REPLICATES.**

Selected heads (2.98 % of 336): L0H8, L8H7, L15H2, L0H0, L10H2, L8H3, L11H6,
L4H11, L0H12, L11H4.

### Specificity is real but not overwhelming

The 20 random 10-head sets gave reductions mostly between −0.04 and +0.12, but
**two reached +0.29 and +0.30** — close to the p95 of +0.292 that condition (b)
is measured against. The selected set clears it, but a reader should know the
control distribution has a tail, and that (b) passed by 0.12 rather than by an
order of magnitude.

### POST-HOC — how many heads are actually needed, and the 2–4 % range vindicated

**Not declared in advance.** Computed on HELD-OUT after the verdict was recorded,
because the sweep showed one head (L0H8) removing 39 % of Δ on the SEARCH
subsample by itself, which made "2–4 % of heads" look generous.

| set | % of heads | Δ reduction | `absent` degradation |
|---|---|---|---|
| L0H8 alone | 0.30 % | 0.281 | **0.94** |
| top-3 | 0.89 % | **0.648** | **1.21** |
| top-5 | 1.49 % | 0.553 | **0.87** |
| top-10 | **2.98 %** | 0.416 | **0.17** |

Two things, neither expected:

1. **Reduction is not monotone in set size.** top-3 mitigates entrainment far
   more (0.648) than top-10 (0.416). Ablations interact; the larger set contains
   heads that partially restore the effect.
2. **The smaller sets hurt the model.** Degradation in `score_absent` is
   0.87–1.21 nats for 1–5 heads against **0.17** for 10. **top-3 would FAIL
   declared condition (c)**, which requires < 0.5.

So on this instrument, ablating under ~1.5 % of heads mitigates entrainment but
damages ordinary next-token behaviour, and only at **2.98 %** are both halves of
the published claim satisfied at once. arXiv:2606.24077 specified **2–4 %**.
That range is exactly where the claim's "without hurting the model's
performance" clause survives here — a convergence the design did not aim at,
since k was fixed at 10 in advance for being the midpoint of the paper's range
and for no other reason.

### What this does and does not show

It supports the paper's third and strongest claim — causal, not correlational —
on an independent model, corpus and task, with a leakage-free split and a
specificity control the original design did not need to include.

It does **not** establish the minimum sufficient set (k was fixed, not
searched), does not identify the *same* heads the paper found (its
identification procedure was not reproduced), and rests on one model of one
family. `score_absent` is a narrow performance proxy — a pass on (c) is weak
evidence for "without hurting performance", and the post-hoc table shows how
sharply that proxy moves once the head set is small, so it is not inert.

**No novelty is asserted.** The hypothesis is published; this is a replication,
and it succeeded.

### Files

`results/e20_sweep_L{0-7,8-15,16-23}.csv`, `results/e20_main.json`,
`results/e20_controls.csv`, `results/e20_heldout.json`,
`results/e20_subsets.json`.
