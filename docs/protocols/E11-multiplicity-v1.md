# E11 — Multiplicity sweep — protocol v1

**PREREGISTRATION. Committed before any E11 decider call**, with zero E11
results in the tree.

---

## 1. What this discriminates

E10 found `same_root` and `indep_root` identical at **exactly k = 2** support
messages (paired difference +0.0000, p = 1.0) and concluded that the model
assigns zero decision weight to evidential dependence.

That conclusion has one serious competing explanation:

> **Two agreeing messages already saturate resistance, so no manipulation at
> k = 2 could have shown anything. The null is a fact about the number 2, not
> about the model.**

E11 exists solely to discriminate those two. It varies k ∈ {1, 2, 3}.

This is **an attack on E10's own conclusion**, not a rescue attempt for the
hypothesis E10 killed. Both possible outcomes narrow or confirm a negative;
neither can revive lineage sensitivity on its own.

---

## 2. Design

| arm | messages | roots |
|---|---|---|
| `bare` | source | 1 |
| `filler_k1/2/3` | source + k irrelevant messages | 1 |
| `same_k1/2/3` | source + k support messages, **all citing b0** | 1 |
| `indep_k1/2/3` | source + k support messages, **citing b1..bk** | k+1 |

10 arms × 36 instances = **360 decider calls**.

**The construction is nested.** Templates, bases, speakers and filler frames are
drawn once per instance at full length and then truncated to k, so `k=1` is a
strict prefix of `k=2` is a strict prefix of `k=3`. A change across k is
therefore the effect of *adding a message*, never of showing different messages.
Without nesting the curve would be uninterpretable.

Contradiction is byte-identical everywhere and always spoken by a voice that has
not yet spoken, at every k and in every arm.

**E10's corpus is not modified.** `lineage_e11.py` imports E10's template pools
and builds its own corpus with its own hash; E10's `00947dde8eb0520b` still
reproduces, and a gate asserts it.

---

## 3. Hypotheses — frozen

**H7 is checked FIRST, because it decides whether H6 is interpretable at all.**

| # | hypothesis | contrast | meaning |
|---|---|---|---|
| **H7** | **dose-response exists** | `same_k1` vs `same_k2` vs `same_k3` | does adding correlated support keep moving the decision? |
| **H6** | **evidential independence matters at some k** — PRIMARY | `same_k` vs `indep_k`, for k = 1, 2, 3, Holm-corrected over 3 | the E10 question, across multiplicity |
| **H8** | dilution has its own dose-response | `filler_k1/2/3` | separates "more text" from "more support" at each k |

---

## 4. Kill rules — binding, and one of them retracts E10

**If H7 is flat** — `same_k1 ≈ same_k2 ≈ same_k3` with no significant step —
then resistance is saturated across the whole tested range, **E10's null is
uninformative**, and the claim *"the model assigns zero weight to evidential
dependence"* must be **retracted and replaced** with *"the E10 design could not
have detected a dependence effect."* This is the outcome that costs the most and
it is written down first on purpose.

**If H7 shows dose-response but H6 is null at every k** — the manipulation
demonstrably has room to move the decision, and independence still does nothing.
E10's conclusion is **confirmed and strengthened**, now across k = 1, 2, 3.

**If H6 is significant at some k** — E10's null was k-specific. The conclusion
narrows to *"no dependence effect at k = 2"* and the lineage direction is
reopened **only** at the k where it appears, pending replication.

---

## 5. Effective evidence count

Descriptive, computed only if H7 shows dose-response. For each k, report the
flip rate of `same_k` and locate the k′ at which `indep_k′` matches it. If the
two curves are superimposed, then **k correlated restatements are worth exactly
k independent sources** and the dependence discount is zero over the tested
range. No parametric model is fitted; direct curves and paired contrasts only.

---

## 6. Statistics

Sampling unit is the task instance, n = 36. Exact paired McNemar throughout,
with raw discordant counts and absolute paired differences. H6 is a family of 3,
Holm-corrected; H7 and H8 are reported with raw p and are descriptive of whether
the manipulation moves at all. Bootstrap CIs resample **instances**, fixed seed.
`p > .05` is never read as equivalence; the SESOI of 0.10 from E10 carries over
for any equivalence statement.

---

## 7. Gates before any decider call

1. E10's corpus hash still reproduces (`00947dde8eb0520b`) — E11 must not
   disturb it
2. nesting: `exposure(k=1)` is a strict prefix of `k=2` of `k=3`, in every arm
   family and every instance
3. `same_k` cites exactly 1 basis; `indep_k` cites exactly k+1, all distinct
4. `same_k` and `indep_k` are identical after replacing basis strings
5. no per-message unigram/bigram separates `same_*` from `indep_*`
6. contradiction byte-identical across all arms; always a fresh speaker
7. no formal label, constraint id or action id leaks into rendered text
8. arm registry count asserted (10)
9. corpus regenerates bit-identically
10. word-length match between `same_k` and `indep_k` at each k
