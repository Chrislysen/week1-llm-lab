# E12 — Powered independence test — protocol v1

**PREREGISTERED. Committed with zero E12 results in the tree.**

## 1. Why

E10's H3 was reported as a fired kill rule and **retracted**
(`docs/protocols/E10-H3-RETRACTION.md`). At n = 36 the design had **power 0.14**
to detect an effect at its own SESOI of 0.10, and the equivalence branch was
*structurally unreachable* — attainable bootstrap bounds jump from 0.0833 to
0.1111 around 0.10. The load-bearing question was left **unresolved**.

E12 resolves it, or reports that it still cannot.

## 2. How n goes 36 → 108 without inventing an instance

Each formal instance carries 3–4 eligible `before` constraints; E10 and E11 used
only the first. Taking three per instance gives **108 (instance, proposition)
units** from the same frozen benchmark — the n the retraction identified as
giving ~0.91 power.

**The units are clustered and the analysis says so.** Three propositions inside
one instance share a domain, an action vocabulary and a setting. They test
different orderings but are not independent draws. Treating 108 clustered units
as 108 independent ones would manufacture precision — a worse error than the one
being fixed.

| quantity | how it is computed |
|---|---|
| interval | **cluster bootstrap** — resample the 36 *instances* with replacement, carrying all their units |
| test | **cluster permutation** — swap the `same`/`indep` labels for *all* units of an instance together, 20 000 reps |
| naive unit-level McNemar | reported **alongside**, only to expose how much clustering matters. Never the headline. |

## 3. Arms

`bare`, `filler`, `same_root`, `indep_root` — at k = 2, matching the E10
condition that was retracted. 4 × 108 = **432 decider calls**.

## 4. Decision rule — carried over from E10 unchanged

SESOI = **0.10**.

- cluster-permutation p < 0.05 → **effect exists**; E10's null was a power
  failure
- |diff| < 0.10 **and** cluster-bootstrap 95% CI inside ±0.10 →
  **EQUIVALENCE-SUPPORTED NULL**
- otherwise → **still inconclusive**, reported as such, not upgraded

Only the second outcome licenses *"the model does not discount correlated
evidence."* E10 claimed it without earning it. E12 either earns it or does not.

## 5. Gates

Frozen corpora intact (E10 `00947dde8eb0520b`, E11 `5c28ada4c4b899dc`); 108
units in 36 balanced clusters; three *distinct* propositions per instance (or
the extra n is fake); arms differ only in basis tokens; no n-gram separates
them; contradiction byte-identical with a fresh speaker; lengths matched;
deterministic regeneration.
