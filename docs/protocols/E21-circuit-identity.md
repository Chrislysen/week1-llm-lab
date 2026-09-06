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

---

## Outcome

**Run 2026-09-06. Verdict: DISSOCIATED CIRCUITS.** The entrainment heads do
**not** carry revocation inertia. H-1's hypothesis is false in this model.

Baseline |INERTIA| = 0.160 > 0.05, so the declared VOID condition did not fire —
there was a real baseline effect available to reduce.

| condition | accepted | proposed | rejected | never | **INERTIA** | **OBEDIENCE** | MENTION |
|---|---|---|---|---|---|---|---|
| baseline | −0.981 | −1.032 | −1.101 | −1.261 | **+0.1599** | +0.2794 | +0.2290 |
| entrainment heads ablated | −2.359 | −2.381 | −2.407 | −2.597 | **+0.1892** | +0.2372 | +0.2153 |

### Read rule applied

Condition (a) required INERTIA to fall by ≥ 30 %. It **rose**, +0.160 → +0.189.
(a) fails, so the verdict is **DISSOCIATED CIRCUITS** and (b) and (c) are not
reached. The ablated value also sits comfortably inside the random-control
range (INERTIA +0.016 to +0.894 across 10 random 10-head sets), which is
independent confirmation of no specific effect.

### What the ablation actually did

It moved the **level**, not the **structure**. Every status dropped by roughly
1.35–1.4 nats (accepted −0.98 → −2.36, never −1.26 → −2.60), while all three
contrasts stayed nearly fixed (INERTIA +0.16 → +0.19, OBEDIENCE +0.28 → +0.24,
MENTION +0.23 → +0.22).

So the entrainment circuit governs **how strongly the model favours any
identifier that appeared in context**, and not **how it discriminates a
rejected constraint from an unmentioned one**. Those are separable, and
ablating the first leaves the second intact.

### Why this is worth recording

The transfer was clean: heads selected purely by their effect on sentence
entrainment, on instances the test never saw, applied to a different quantity.
E20 showed that same set causally carries entrainment — 41.6 % reduction, past
the random p95. The identical set does nothing to revocation inertia. **One
circuit, confirmed for one phenomenon, demonstrably not responsible for the
other.**

That constrains where the mechanism of arXiv:2608.12599's revocation inertia
can live: not in the entrainment heads of arXiv:2606.24077. A future search for
it has to start somewhere else.

### Limits

One model, one corpus, one head set of one size, zero-ablation only. INERTIA is
measured at first-plan position in logit space, which is a proxy for E16's
behavioural "included anywhere" and can come apart from it. A null under
zero-ablation does not exclude the heads contributing under a different
intervention (mean-patching, resample-ablation, steering). The baseline INERTIA
of +0.16 nats is small in absolute terms, so this is a weak-signal regime and
the dissociation should be read as "not detectably shared here" rather than
"provably distinct".

**No novelty is claimed.** H-1 was gated SURROUNDED before this ran and that
verdict is unchanged; this is a negative mechanistic result on a fresh
instrument.

### Files

`results/e21_circuit.json`.

---

# E22 — the follow-up search for a rejection circuit: NOT RUN, underpowered

E21's dissociation implies *something other than the entrainment heads* carries
the rejected-vs-unmentioned discrimination. The obvious next move is to search
for it. **That search was designed, power-checked, and abandoned before any
sweep.** Recorded because a design that dies on a power check is a result.

## Design-selection measurement (descriptive, HELD-OUT instances 18–35)

Which model discriminates a rejected constraint most strongly, and is it
sweepable? Contrasts of first-plan-position action-identifier log-probability:

| model | INERTIA (rej−never) | **REJECTION EFFECT (prop−rej)** | OBEDIENCE (acc−never) |
|---|---|---|---|
| Qwen2.5-0.5B-Instruct | +0.160 | +0.069 | +0.279 |
| Qwen3.5-0.8B | +0.426 | −0.058 | +0.437 |
| Qwen2.5-1.5B-Instruct | +0.181 | +0.121 | +0.409 |
| Qwen3.5-4B | **−0.117** | **+0.652** | +0.687 |

`REJECTION EFFECT` controls for mention — `proposed` is mentioned with no
verdict, `rejected` is mentioned and refused — so it isolates the rejection.

**Qwen3.5-4B is the only model that scores a rejected action *below* a
never-mentioned one.** The smaller models place it *above*: latent revocation
inertia. The 4B suppresses. Its rejection effect is ~9× the 0.5B's.

**But the strong-signal models are not sweepable here.** Qwen3.5-4B is a
multimodal, hybrid-attention config (`vision_config`, and transformers warns
about `flash-linear-attention`), so the uniform `o_proj`-slice head ablation
validated in E20 does not cleanly apply. Qwen2.5-7B needs CPU offload, making a
784-head sweep hours long. Only Qwen2.5-0.5B and 1.5B are fast and
architecturally standard — and those are exactly the models with the weakest
rejection effect.

## Power check on the only viable substrate (Qwen2.5-1.5B, 336 heads)

Baseline rejection effect **+0.1212**. Eight random 10-head ablations:

    +0.1305  +0.0138  +0.0485  +0.1265  +0.0572  +0.0695  +0.0829  +0.1073

Noise **sd = 0.0405 nats**; signal-to-noise **3.0**. And random ablation is not
neutral — it *already* removes 30–90 % of the effect (mean change −0.043, worst
−0.107). A head set that drove the effect to zero would sit barely outside that
random tail.

## Decision: NOT RUN

A 336-head sweep at 3σ against a control distribution that already eats most of
the effect cannot separate a real circuit from the tail. **This repository has
made exactly that mistake before** — E10 asserted a conclusion at power 0.14
with a structurally unreachable equivalence branch, and it was retracted in
full (`docs/protocols/E10-H3-RETRACTION.md`). Running the sweep and reading
whatever emerged would repeat it.

What would make the search viable: a model with both a large rejection effect
and a standard attention stack (Qwen2.5-3B or -7B with enough VRAM to sweep),
or a corpus manipulation that amplifies the contrast. Neither is available on
this machine tonight.

**The descriptive table above is a real observation and is not a claim.** Four
models, two families, and the largest is architecturally different from the
rest, so "scale" is confounded with architecture and nothing about a scale
trend is asserted.
