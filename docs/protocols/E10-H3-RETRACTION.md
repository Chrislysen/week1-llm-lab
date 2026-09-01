# RETRACTION — E10 H3 was reported as a fired kill rule. It was inconclusive.

> **RESOLVED BY E12.** The question this retraction left open has since been
> answered at adequate power. E12 took three propositions per instance — 108
> units in 36 clusters — and found the independence effect at **+0.0185** with a
> cluster-bootstrap 95% CI of **[−0.037, +0.074]**, entirely inside the
> preregistered SESOI of 0.10 (cluster-permutation p = 0.749). That is an
> **equivalence-supported null**: the conclusion E10 asserted, now earned.
> The prediction below — that this benchmark could not supply n = 108 — was
> **wrong**. It could, by treating each eligible `before` constraint as its own
> proposition. See `docs/protocols/E12-powered-independence-v1.md`.

**Status: the claim "the model assigns ZERO decision weight to evidential
dependence" is WITHDRAWN.** Commit `dda7e40` is left in history unaltered; this
document supersedes its conclusion.

Found by an adversarial agent panel pointed at E10 and told to kill it. The
finding was rated *fatal*, and it is correct. I verified every element myself
before accepting it.

---

## What went wrong

The protocol (§6) defined the equivalence-supported null as:

> |diff| < 0.10 **and** the 95% bootstrap CI excludes effects larger than 0.10
> **in both directions**

Observed: diff = +0.0000, CI = **[−0.1111, +0.1111]**.

−0.1111 is not greater than −0.10. **The equivalence branch is false.** My own
preregistered code therefore falls through to its third branch and prints,
verbatim:

```
H3 IS NOT SUPPORTED AND NOT EQUIVALENCE-SUPPORTED. The study
is underpowered for the effect size observed. Do NOT read this
as 'no difference' -- report it as inconclusive at n = 36.
```

And then I wrote a commit saying *"the preregistered kill rule fires"* and
*"assigns ZERO decision weight."* The decision procedure was frozen before any
data existed — `git diff 6df8fd0 HEAD -- e10_independence.py` is empty — so this
is not a protocol ambiguity I resolved badly. **It is a result I reported in
direct contradiction of my own preregistered output, which was sitting in the
terminal in front of me.**

The `KILL RULE FIRES` text lives *inside* the equivalence branch. It is
unreachable from the branch that actually executed.

## The commit also misquoted the kill rule

`dda7e40` presents as a quotation: *"SAME_ROOT differs from FILLER but not
INDEPENDENT_ROOT →…"*. The protocol §5 actually reads *"`same_root` differs from
`filler` but `indep_root` **≈** `same_root`"*. The paraphrase silently replaced
an equivalence relation with mere non-difference — the exact substitution §6
forbids in the sentence *"`p > .05` is **not** evidence of equivalence."*

## This is a repeat offence

`verify_claims.py` lists among its seven motivating retractions: *"the E5 'step
function' was a p = 1.000 null at n = 36."* Two hundred lines later, the same
file made a positive claim from a p = 1.000 null at n = 36 on the same corpus
size. The checker built to prevent this failure mode contained it.

---

## What the design could actually detect

At the observed discordance rate (4 of 36 pairs), simulated power to detect a
true effect **exactly at the preregistered SESOI of 0.10**:

| n instances | power |
|---|---|
| **36 (what was run)** | **0.14** |
| 72 | 0.67 |
| 108 | 0.91 |
| 150 | 0.98 |

The test also could not have reached significance in *either* direction: with
only 4 discordant pairs, even a 4–0 split gives p = 0.125. And the equivalence
branch was **structurally unreachable** — bootstrap differences are multiples of
1/36 = 0.0278, so the attainable bounds jump from ±0.0833 to ±0.1111 and the
SESOI of 0.10 falls strictly between two adjacent achievable values. *A 0.10
SESOI at n = 36 can never be met.* That is a design defect in the SESOI/n pairing,
chosen by me, before scoring.

---

## What survives, stated conservatively

1. **H3 is INCONCLUSIVE.** Not "zero", not "no difference", not a fired kill
   rule. The lineage-independence direction is **UNRESOLVED**, not refuted.
2. **A bound does survive.** The 95% CI excludes |effect| > 0.111, so a *large*
   independence effect is ruled out. An effect at or below the SESOI is not.
3. **A relative-sensitivity statement survives, and needs no equivalence test.**
   On the same instances, in the same instrument, at the same k:

   | contrast | discordant pairs (E11) |
   |---|---|
   | corroboration (`filler` → `same`) | 12–1, **18–0**, **19–0** |
   | independence (`same` → `indep`) | 0–2, 0–1, 1–3 |

   An instrument that moves 18–19 of 36 instances for corroboration moves at
   most 3 for independence. **Whatever the independence effect is, it is far
   smaller than the corroboration effect measured beside it.** That is a
   defensible comparison and it is what should have been written.
4. **The direction is consistent but never significant.** All four independence
   measurements lean the same way — independent roots *slightly more* protective
   — which is the normatively expected direction. It never approaches p < 0.05.

## Consequences

- Method work stays **unauthorised**: gate B needs a demonstrated
  dependence effect, and there is none. Unchanged.
- ~~The lineage direction is not retired on evidence.~~ **Superseded: E12
  retired it on evidence.** The n ≈ 108 this section called for was obtainable
  after all, from the same 36 instances.
- ~~Spending 3x the compute to resolve a pre-empted question is poor
  allocation.~~ **That judgement was wrong too, and cheaply so:** the extra n
  cost one 432-call run, not three corpora, because the propositions were
  already sitting in the benchmark.
- **The corroboration dose-response (E11 H7/H8) is unaffected.** It is
  well-powered (18–0, 19–0), replicated at three levels of k, and is the finding
  worth spending remaining effort on.
