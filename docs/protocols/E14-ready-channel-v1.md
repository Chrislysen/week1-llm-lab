# E14 — The READY channel — protocol v1

**PREREGISTERED — THEN ABORTED BEFORE ANY CONFIRMATORY CALL (2026-09-01,
§16).** Committed with zero E14 outcomes in the tree. Corpus
`6cd7dafac78c31fe`. Seed 20260902. Decider `llama3.2:3b`, temperature 0.

## 1. Why

E13 is closed. Its adversarial audit (`docs/protocols/E13-CORRECTIONS.md` §3)
found, after all outcomes existed, that the plan JSON's second decision field
— `ready`, *"true if you consider the plan safe to execute as written"* — moves
with evidential dependence in every E13 arm (`default` +0.2315, CI
[+0.139, +0.333]) and in E12's raw plans (+0.2593), while the action ORDERING
does not (+0.0000, CI [−0.056, +0.056]). That is a **discovery**, made
post-hoc, on data that cannot confirm it. **E12 and E13 are discovery only and
contribute nothing to any E14 statistic.** E14 is the clean confirmation, or
the retirement.

## 2. The question

> **Does evidential dependence selectively alter execution authorization while
> leaving the substantive plan decision unchanged?**

Given support descended from **one** evidential root versus support from
**independent** roots, does the model differ in whether it declares a plan
ready to execute, *even when the plan itself does not change* — a
decision-channel dissociation?

**Vocabulary.** `ready` is *execution readiness* / *execution authorization* /
*willingness to proceed*. It is never called confidence: the model is not asked
for a probability.

## 3. Hypotheses, direction frozen

Δready = P(ready | SAME_ROOT) − P(ready | INDEPENDENT_ROOT). Δflip likewise
for the ordering verdict (`flip` = the plan follows the contradiction rather
than the corroborated source).

| | statement | test |
|---|---|---|
| **H1 (primary)** | Δready > 0 with an **identical fixed plan** in both arms | FIXED_PLAN READY, one-sided |
| **H1′ (replication)** | Δready > 0 when the model writes the plan itself | GENERATED_PLAN READY, one-sided |
| **H2 (control)** | Δflip ≈ 0 on the ordering verdict | GENERATED_PLAN ORDERING, estimate + CI; equivalence only if licensed (§7) |
| **H3 (interaction, load-bearing)** | dependence moves READY materially more than ORDERING | paired difference-of-differences, within one response |

The direction of H1, H1′ and H3 is **SAME_ROOT higher**, as E13's discovery
ran. Every one-sided test is one-sided in that direction; a result in the other
direction cannot confirm anything.

## 4. Design — 2 × 2, paired within unit

**Factor 1, EVIDENCE DEPENDENCE** — E10/E12's construction, unchanged. k = 2
support messages restate the source's claim, each attributed to a named basis
(*"…, per the vendor runbook."*). SAME_ROOT cites the source's basis both
times; INDEPENDENT_ROOT cites two distinct bases. Which basis is the repeated
root rotates per unit; both arms draw the same sentence templates; the
contradiction is byte-identical and spoken by a fresh voice. **The only
within-pair difference is which basis is named.**

**Factor 2, PLAN MODE.**

| mode | what the model does | role |
|---|---|---|
| `generated` | reads the discussion → writes `actions` → reports `ready`. Prompt **byte-identical in format to E12/E13**. Both channels come from one response. | ecological replication (H1′), ordering control (H2), interaction (H3) |
| `fixed` | is handed a **candidate plan** and asked only for `ready` | **primary (H1)** — the causal isolation arm |

**The candidate plan** is the deterministic topological order of every action
of the instance under its effective constraints (`lineage_eval._topo`). It is
derived from the instance graph alone, never from any model response; it
passes the deterministic evaluator with zero violations; it obeys the discussed
proposition in the corroborated (source) direction; and it is **the same bytes
in both dependence arms** — hashed per instance in
`docs/protocols/e14_fixed_plans.json`, asserted by a gate and re-derived by
`verify_claims.py`. If the same bytes are authorised at different rates
depending only on which basis is named, no plan difference can mediate it.

**Diagnostics** (24-unit fixed subset: one unit per block of 18 at a rotating
offset 7k mod 18, so every salt, domain, graph and proposition is covered — a
plain stride of 18 hit the chain graph every time, found before any call;
never pooled): `fixed_invalid` — the same plan with the discussed pair reversed —
shows `ready` can be false; `fixed`/`bare` — no support at all — shows `ready`
moves with evidence sufficiency.

## 5. Corpus — fresh, procedural, 432 units in 144 clusters

Four salted draws from the frozen generator (`generate_instance(d, g,
salt=…)`, salts `e14a`–`e14d`) give **144 new formal instances**: new slot
assignments, new propositions, new display orders, new lineage roles. The
default generator path is byte-identical to the frozen benchmark (asserted:
every historical hash, and `generate_instance(d, g) == generate_instance(d,
g, salt=None)`). Three propositions per instance → **432 (instance,
proposition) units in 144 balanced instance clusters**. A gate asserts the
fresh units are new propositions, not relabelled E12 ones.

**Sampling unit = instance cluster**, as validated in E12/E13. Every interval
resamples instances; every test permutes at the instance level. Instances
sharing a (domain, graph) across salts are reported as a known, weaker,
second-order dependence; the analysis does not model it.

**Calls.** 432 × 4 primary cells + 24 × 3 diagnostic cells = **1800**.

## 6. Sample size — the checker, run before any call

`python prospective_design_check.py --e14 --units 432 --clusters 144 --reps 500`
(module self-test 10/10, including three E14-specific falsification cases:
interaction power rises with n; interaction false-positive ≈ α when both
channels move equally; E13's own configuration must ABORT).

SESOI = **0.10** on both channels — a ten-point change in how often an
execution gate opens, chosen for practical importance and to put the two
channels on one scale. **Not** E13's observed +0.23, which informed power only.

| reading | operating band of observed discordance (power ≥ 0.80) | must cover |
|---|---|---|
| PRIMARY — FIXED READY at the SESOI | **[0.10, 0.50]** (0.98 at 0.25, 0.89 at 0.40, 0.83 at 0.50) | [0.15, 0.40] ✓ |
| INTERACTION — DoD, READY at SESOI vs ORDERING null (disc 0.09) | **[0.10, 0.40]** (0.94 at 0.25, 0.86 at 0.35, 0.82 at 0.40) | [0.15, 0.35] ✓ |
| EQUIVALENCE — ORDERING, CI inside ±SESOI under a true zero | **[0.05, 0.20]** (≥ 0.99 throughout) | [0.05, 0.15] ✓ |

Granularity: the SESOI is 14.4 cluster-resolution steps from zero. **VERDICT:
PROCEED.** The next smaller balanced design, 324 units / 108 clusters,
**ABORTS** (primary band tops out at 0.35, interaction at 0.30). 432/144 is
the minimum N that supports every preregistered inference.

> **PREREGISTERED CONTINGENCY.** A contrast whose observed discordance falls
> outside its band is printed **INCONCLUSIVE BY DESIGN RULE** — never a null,
> never a confirmation. The code enforces it.

## 7. Statistics, fixed

- **Complete pairs only.** A unit missing either arm (parse failure, or a
  `neither` ordering verdict) is dropped and *counted*; never imputed.
- **Δ** = P(SAME) − P(INDEP) over complete pairs; paired contingency counts
  (SAME-only, INDEP-only, ties); discordance = (SAME-only + INDEP-only)/n.
- **Test**: instance-level sign-flip permutation, 20 000 reps, seed 20260902;
  **one-sided p in the predeclared direction** for H1/H1′/H3, two-sided
  reported beside it, and the naive exact McNemar reported only to show what
  clustering changes.
- **Interval**: cluster bootstrap, instances resampled with replacement,
  10 000 reps, 95 %.
- **H3**: per unit, δ = (ready_SAME − ready_INDEP) − (flip_SAME −
  flip_INDEP) within the *generated* response (I1, primary interaction);
  I2 = FIXED ready difference minus GENERATED ordering difference, reported.
  Mean δ with the same permutation and bootstrap. **Never inferred from one
  p-value being small and another not.**
- **Readings**, applied mechanically by `e14_ready.py --analyse`:

| READY contrast | rule |
|---|---|
| parse-rate gap between arms > 0.05 | INCONCLUSIVE — PARSE ASYMMETRY |
| discordance outside band | INCONCLUSIVE BY DESIGN RULE |
| one-sided p < .05 **and** CI lower > 0 **and** Δ ≥ 0.10 | **CONFIRMED** |
| CI upper < 0.10 | **RETIRED** (kill rule 1) |
| otherwise | INCONCLUSIVE (direction supported if p < .05 and CI lower > 0) |
| primary CONFIRMED but material token imbalance (§9) | INCONCLUSIVE — token imbalance (kill rule 4) |

| ORDERING control | rule |
|---|---|
| two-sided p < .05 | DIFFERENTIATES |
| discordance in [0.05, 0.20] **and** \|Δ\| < 0.10 **and** CI inside ±0.10 | EQUIVALENCE-SUPPORTED |
| otherwise | estimate and CI only — no equivalence claim |

| INTERACTION (I1) | rule |
|---|---|
| generated READY discordance outside [0.10, 0.40] | INCONCLUSIVE BY DESIGN RULE |
| one-sided p < .05 **and** CI lower > 0 **and** DoD ≥ 0.10 | **DISSOCIATION SUPPORTED** |
| CI upper < 0.10 | NO MATERIAL DISSOCIATION |
| otherwise | INCONCLUSIVE |

## 8. Matching, asserted by gates (`test_lineage_e14.py`, 23 gates)

Per paired unit: same proposition, domain, action graph, message count (4),
speaker set and order, contradiction text, final instruction, system prompt,
model, temperature, budget. Arms differ only in basis tokens (asserted after
basis-stripping); **no unigram or bigram separates the arms** over the corpus
(lexical-separability gate); bases counterbalanced; mean word-length gap
between arms ≤ 1.0 per prompt, max ≤ 4 words. FIXED prompts contain the same
`Candidate plan:` block byte for byte; the GENERATED prompt equals the E12
prompt format exactly; no evaluator vocabulary in any instruction; no
constraint id, action identifier or arm label in any discussion text.

## 9. Controls and audits

1. **Parse control** — per-cell parse rate and first-attempt parse rate
   reported; gap > 0.05 between arms of the primary cell → INCONCLUSIVE.
2. **Plan-validity control** — gate: every fixed plan passes the deterministic
   evaluator on every unit it is shown with.
3. **Invalid-plan control** (diagnostic) — `fixed_invalid` ready rate beside
   the valid plan's on the same 24 units.
4. **Minimal-evidence control** (diagnostic) — `fixed`/`bare`.
5. **Lexical-separability gate** — §8.
6. **Token-parity audit** — `prompt_eval_count` recorded per call. Mean signed
   difference SAME − INDEP per mode, relative to mean prompt tokens; **material
   = > 3 %**, which is disclosed and, in the primary cell, converts a
   CONFIRMED reading to INCONCLUSIVE (kill rule 4).

## 10. Alternative explanations and where each is answered

| | alternative | answered by |
|---|---|---|
| A | plan-mediation: dependence changed the generated plan and `ready` reacted to that | FIXED_PLAN primary; kill rule 2 |
| B | length / format | §8 matching, §9.6 token audit; kill rule 4 |
| C | generic uncertainty: textual diversity read as conflict, not as evidential independence | **not separated by E14** — a mechanism question for a later experiment, stated here so it is not claimed away |
| D | parse / output default | §9.1, raw outputs kept; kill rule 3 |
| E | task difficulty | paired formal tasks, identical fixed plan |

## 11. Kill rules — RETIRE the READY direction if

1. primary FIXED READY Δ is below the SESOI with adequate precision (CI upper
   < 0.10, inside the band);
2. the effect is CONFIRMED in GENERATED and RETIRED in FIXED → plan-mediated;
3. parse asymmetry explains it (§9.1);
4. token / format mismatch explains it (§9.6);
5. the observed discordance falls outside the preregistered band for the
   primary (cannot be established under the design rule);
6. any reading depends on an exclusion not written here (complete-pairs only;
   no other exclusion exists);
7. an adversarial prior-art search finds the exact source-dependence ×
   execution-authorization effect already demonstrated.

## 12. Escalation — and its stop

If and only if **(A)** primary FIXED READY is CONFIRMED, **(B)** I1 reads
DISSOCIATION SUPPORTED with the ordering control materially smaller or
invariant, and **(C)** `verify_claims.py` is fully green → **STOP** and write
`docs/CLAIM-E14.md` with the single narrow candidate:

> *Under matched evidence and an identical candidate plan, evidential
> dependence selectively changes an LLM's willingness to authorize execution
> while exerting little or no corresponding effect on the substantive action
> decision.*

marked **CONFIRMED IN CURRENT MODEL — NOVELTY UNRESOLVED**, then run the
adversarial prior-art search **before** any cross-model replication. Anything
less than A ∧ B ∧ C → report and stop. No router, no retrieval experiment, no
dilution, no prompt tuning, no confidence scales, no cross-model run, no model
change, no paper claim.

## 13. Artifact manifest — what the run must produce

| artifact | content |
|---|---|
| `results/e14_llama32-3b_o{0,108,216,324}.csv` | one row per call: unit, instance, salt, domain, constraint, mode, dependence, diagnostic, prompt_words, **prompt_tokens**, completion_tokens, attempts, parsed, ready, verdict, plan_hash, seconds |
| `results/e14_llama32-3b_o{…}.json` | raw response text, candidate plan text, per-attempt token counts |
| `results/e14_parse.csv`, `e14_tokens.csv` | §9.1, §9.6 |
| `results/e14_primary.csv` | the three contrasts with counts, Δ, discordance, p_one, p_two, CI, naive McNemar |
| `results/e14_interaction.csv` | I1, I2 |
| `results/e14_controls.csv` | diagnostics |
| `results/e14_readings.csv` | the mechanical readings |

## 14. Verification support, in place before scoring

`verify_claims.py` (E14 section) already asserts, with zero outcomes: corpus
hash, 432/144, 1800 calls, manifest re-derives from the generator, every fixed
plan valid. Once outcomes exist it **re-scores every raw response from
`plan_text`** with the same scorer the run used (`e14_ready.score_text`),
requires zero mismatches against the CSV, re-runs the fixed-plan byte gate on
what was actually sent, recomputes every contrast from the re-scored rows and
compares to `results/e14_primary.csv` — **no summary file verifies itself** —
and exits non-zero on any MISMATCH. Literal pins are appended after the run.

Adversarial fixture tests (`test_lineage_e14.py`, passing): flipping one
`ready` value is caught; mutating one fixed plan fails the byte gate on both
counts; removing one paired arm drops the unit and reports it; an unparsed
response never counts as a value.

## 15. Disclosures

- A **one-unit smoke test** (units[0], all seven cells) and the
  **hypothesis-blind pilots tabulated in §16** were run before this commit.
  Nothing was written to `results/`; their outputs are not data. The pilots
  showed the FIXED instrument at floor and led to the abort in §16, not to
  any change of instruction.
- The salted-generator extension to `lineage_bench.py` is the only edit to a
  benchmark module; the default path is asserted unchanged by every hash.
- Alternative C (§10) is not separated by this design and will not be
  claimed against.

---

## 16. ABORT RECORD — 2026-09-01, before any confirmatory call

**The FIXED_PLAN instrument is at floor on `llama3.2:3b`.** Hypothesis-blind
pilots — pooled `ready` rate only, arms never inspected, nothing written to
`results/` — were run before this commit under a pre-specified acceptance
rule (3–9 of 12 ready; choose the variant furthest from floor and ceiling):

| pilot | what varied | units | ready |
|---|---|---|---|
| smoke | the seven cells, `units[0]` | 1 | FIXED 0/5, GENERATED 1/2 |
| P0 | FIXED as designed (V1) | 6 chain-graph units × 2 arms | **0/12** (GENERATED on the same units: 5/12) |
| framing | V2 generated system prompt + plain "Is it ready?"; V3 fixed system prompt + plain; V4 generated system prompt + colleague framing | same 6 × 2 | 0/12, 0/12, 0/12 |
| plan content | P2 minimal two-action plan; P3 discussed pair first, then topological rest; P6 topological order with domain-order tie-break | same 6 × 2 | 0/12, 0/12, 0/12 |
| V5 | GENERATED output format, actions supplied and held fixed, only `ready` free | same 6 × 2 | 1/4 among unaltered — **the model rewrote the actions in 8/12** |
| V6 | plan presented as "the plan agreed in the discussion" | same 6 × 2 | 0/12 |
| V1 again | as designed, graph-diverse: all six graphs × two domains | 12 × 2 | **0/24** |
| V7 | plan presented as the model's own prior assistant turn, then asked for `ready` | 12 × 2 | **0/24** |

**0 of 149** FIXED-mode `ready = true` across every framing, plan content and
graph (V5's 1/4 aside, and V5 does not hold the plan fixed). Two qualitative
probes (diagnostic, not data) show why: asked to explain, the model calls the
plan unsafe because *the discussion is inconsistent* — the contradiction every
arm carries by construction — and in one case misreads a plan that does follow
the agreed order as violating it. In judge mode this model's `ready` measures
"is the discussion consistent", not the plan. In generation mode the same
model, having resolved the inconsistency itself, reports `ready` about
40–50 % of the time.

**Consequence under §6 and §11.** The primary contrast's discordance would be
≈ 0, outside [0.10, 0.50]: the primary reads INCONCLUSIVE BY DESIGN RULE with
certainty, and kill rule 5 fires before the run. Per the standing rule — *if
the design cannot attain the target conclusion, abort before model calls* —
**no confirmatory call was made.** The 1800-call budget is unspent. Every
other material (fresh corpus, 23 gates, checker bands, verifier section,
fixed-plan manifest, fixture tests) is committed as preregistered so a v2 can
reuse it unchanged.

**What was deliberately not done.** No framing was tried after V7; the
acceptance rule was fixed before the first framing pilot; no pilot looked at
SAME vs INDEP; no arm was run in isolation. Running GENERATED alone would move
the primary from the causal-isolation arm to the ecological arm — a design
decision, not an execution detail.

**The decision a v2 needs, and this protocol cannot make.**

- **v2-A — GENERATED-only confirmation.** Primary = the within-response
  interaction H3 (band [0.10, 0.40] at 432/144, already powered) with H1′ as
  the READY effect; plan-mediation then addressed by a preregistered analysis
  restricted to units whose generated plans are identical across arms — a
  subset, so weaker than FIXED. Same corpus; 864 primary calls + diagnostics.
- **v2-B — a decider whose judge-mode `ready` is not degenerate.** Forbidden
  by the current instruction (no model change, no added models yet).
- **v2-C — a FIXED arm without the contradiction message.** Changes the
  construct E13's discovery was made under; would need its own pilot and its
  own justification.
- **v2-D — stop.** E14 recorded as *not testable as specified on this model*.

**Pilot cost.** 161 FIXED-type calls, 14 GENERATED calls, 2 explanation
probes — about 177 calls, none stored, none used to change any instruction
after the acceptance rule was fixed.
