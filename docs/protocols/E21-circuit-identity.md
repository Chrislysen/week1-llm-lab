# E21 — are entrainment heads also revocation-inertia heads?

**MECHANISTIC. Declared 2026-09-06 with zero E21 outcomes. Gated SURROUNDED
(H-1 in `docs/E16-CANDIDATES.md`) and run anyway because the identity question
is causal, cheap on validated infrastructure, and informative either way.
NOT a novelty claim, and the SURROUNDED verdict stands whatever this returns.**

## Question

E20 causally confirmed a ~3 % head set that carries **contextual entrainment**
in Qwen2.5-0.5B. E18 replicated **revocation inertia** — a constraint proposed
then explicitly rejected still influencing the plan. Are these the same circuit?

## Transfer test — no circularity

The head set is taken **unchanged from E20**, where it was selected purely by
its effect on *sentence entrainment scoring*, using **SEARCH** instances 0–17.
E21 applies it to a **different quantity** — the model's preference for a
constrained *action identifier* — on **HELD-OUT** instances 18–35, which the
selection never saw. Nothing about rejection entered the head search.

## Measure

For each E16 unit, teacher-force its action identifier as the first plan entry:

    a(unit) = mean_t log p(id_t | frozen E16 plan prompt + '{"actions": ["')

Aggregated by the unit's status:

- **INERTIA = a(rejected) − a(never)** — persistence of a withdrawn constraint
- **OBEDIENCE = a(accepted) − a(never)** — uptake of an endorsed one
- **MENTION = a(proposed) − a(never)** — bare mention, no verdict

## Read rule, fixed before the first pass

Let I₀, O₀ be baseline and I₁, O₁ the values under ablation of E20's top-10.

- **SHARED CIRCUIT** if (a) INERTIA falls by ≥ 30 % relative, (b) that fall
  exceeds every one of 10 random 10-head controls, and (c) OBEDIENCE falls by
  less than half the relative amount INERTIA does — a selective effect.
- **NON-SELECTIVE** if (a) and (b) hold but (c) fails: the heads carry plan
  preference generally, not rejection specifically.
- **DISSOCIATED CIRCUITS** if (a) fails: entrainment heads do not carry
  revocation inertia, and the two published phenomena have distinct mechanisms.

No fourth reading will be invented after the numbers are seen. **DISSOCIATED is
a perfectly good outcome** and would be reported as one.

## Limits

One model, one corpus, one head set of one size, zero-ablation only. The
identifier is scored at first-plan position, which is not the same quantity as
E16's "included anywhere in the plan" — this is a logit-level proxy for a
behavioural measure, and the two can come apart. INERTIA at baseline may be
near zero or negative, in which case a *relative* fall is ill-defined; if
|I₀| < 0.05 the test is reported **VOID for lack of a baseline effect** rather
than forced into the rule above.

## Files

`e21_circuit_identity.py`; output `results/e21_circuit.json`.
