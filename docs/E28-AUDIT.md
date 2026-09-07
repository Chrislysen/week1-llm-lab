# E28 audit note — every reported number recomputed from raw run records

Sources: `results/e28_power_probe.jsonl` (12 rows), `results/e28d_warmup.jsonl` (5), `results/e28c_order.jsonl` (8).
Model `llama3.2:3b`, turns=8, recency budget=120 words. Model calls in these logged rows: 25 pairs x 16 = **400**. The 16-call smoke
run was not written to JSONL, giving **416** overall (see Correction below).

## ARM H, full-first (the first-pass figures)

| inst | cost_full | cost_budgeted | diff |
|---|---|---|---|
| h0 | 3373 | 2813 | +560 |
| h1 | 3484 | 2948 | +536 |
| h2 | 3687 | 3080 | +607 |
| h3 | 3901 | 2888 | +1013 |
| h4 | 3535 | 2864 | +671 |
| h5 | 3164 | 2681 | +483 |
| h6 | 3214 | 2992 | +222 |
| h7 | 3197 | 2805 | +392 |

mean diff = 4484/8 = **560.5**; sample SD (ddof=1) = **229.5057**; mean full cost = 27555/8 = **3444.4**
relative saving = 560.5/3444.4 = **16.27%**

MDE(n=12) = (t_.025,11 + t_.20,11) x SD/sqrt(12) = (2.201+0.876) x 229.5057/3.464102
         = 3.077 x 66.2526 = **203.86 tokens** = 5.92% of mean run cost

## ARM R (run noise), instance 0

diffs: [475, 169, 169, 169, 169, 169, 169, 169, 169]
declared n=4: mean 245.5, SD 153.0000, ratio to SD_H = 0.6667
pooled  n=9: mean 203.0, SD 102.0000, ratio to SD_H = 0.4444
distinct (full,budgeted) pairs over 9 repeats: [(3057, 2888), (3363, 2888)]

## E28-C counterbalancing (budgeted-first)

| inst | d_full-first | d_budgeted-first | shift |
|---|---|---|---|
| h0 | +560 | +799 | +239 |
| h1 | +536 | +683 | +147 |
| h2 | +607 | +604 | -3 |
| h3 | +1013 | +663 | -350 |
| h4 | +671 | +1108 | +437 |
| h5 | +483 | +683 | +200 |
| h6 | +222 | +479 | +257 |
| h7 | +392 | +471 | +79 |

mean shift = 1006/8 = **+125.8**, SD 232.3770, t(7) = 125.8/(232.3770/sqrt(8)) = **1.531**
two-sided p ~ **0.17** (t=1.53, df=7) -> shift exceeds the declared 50-token threshold but is NOT distinguishable from zero at n=8.

counterbalanced mean saving = **623.4 tokens** = 17.86% of mean run cost 3489.5
SD_H of per-instance counterbalanced means = **182.6219**
MDE(n=12) = 3.077 x 182.6219/sqrt(12) = **162.21 tokens** = **4.65%** of run cost

## Task-quality illustration (Astra)

1 - 0.05^(1/12) = 1 - 0.779078 = **0.2209** = 22.1% one-sided exact 95% upper bound.

## Correction found by this audit

An earlier write-up reported **"212 model calls"** for E28. That figure was
wrong and was quoted onward in external review. Each pair is 2 runs x 8 turns =
16 calls, so the correct counts are: smoke 16, E28 declared run 192 (8 ARM H +
4 ARM R pairs), E28-D 80, E28-C 128 - **416 total**. Corrected in
`docs/protocols/E28-power-probe.md` and `docs/RESUME-SESSION-2026-09-06.md`.

Every other reported figure reproduced exactly from the raw records.

## Standing limits (unchanged by this audit)

Recomputation confirms arithmetic, not design. It does not address that the
contrast is mechanical truncation rather than learned recovery, that n=8 is a
small pilot, that task quality is untested, or that novelty is unresolved.

## Addendum (2026-09-08) — closing two audit limits raised in external review

**1. The 3489.5 denominator IS reconstructible.** The E28-C table above omitted
the cost columns and showed only savings, which is why an external check could
not rebuild it. The reverse-order costs are:

| inst | cost_full | cost_budgeted | diff |
|---|---|---|---|
| h0 | 3605 | 2806 | +799 |
| h1 | 3619 | 2936 | +683 |
| h2 | 3669 | 3065 | +604 |
| h3 | 3551 | 2888 | +663 |
| h4 | 3942 | 2834 | +1108 |
| h5 | 3342 | 2659 | +683 |
| h6 | 3268 | 2789 | +479 |
| h7 | 3281 | 2810 | +471 |

reverse-order full-cost sum = 28277, mean = 28277/8 = **3534.625**
denominator = (3444.375 + 3534.625)/2 = **3489.5** exactly.

So 17.86 % is the order-averaged saving over the mean of the two cohorts'
full-arm costs. Note this is the mean of two *cohort* means, and the cohorts
differ in collection period as well as order.

**2. Record hashes, so a checker verifies the records rather than my
transcription.** SHA-256 (first 32 hex) of the raw JSONL:

| file | sha256 (truncated) | bytes |
|---|---|---|
| `results/e28_power_probe.jsonl` | `bc8a87243c0816bf8d3383d56f6c35af` | 2747 |
| `results/e28d_warmup.jsonl` | `29ce54be5cc0b39bb28ca485c80385f0` | 1150 |
| `results/e28c_order.jsonl` | `69aacfb2dcc0fa20d2a6ee32cab079bd` | 1947 |

**3. On the MDE multiplier.** 3.077 was **fixed in the read rule before any
run**, so the reported MDEs correctly apply the pre-declared factor. Carrying
full-precision quantiles instead (sum 3.076515) gives 203.827 and 162.189 — a
difference with no decision consequence, and using it now would mean changing a
declared constant after seeing the outcome.

**Limit that remains open and cannot be closed from here.** The 16 smoke-run
calls were never written to JSONL. They exist only in the session transcript.
The 400 logged calls are evidenced by the row records above; the 16 are reported
execution only, and that asymmetry should stay visible in any citation of the
416 figure.
