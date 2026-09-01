# CLAIM MEMO — E13, written 2026-09-01 after the attack and the prior-art search

**Bottom line.** This project makes **no novelty claim**. What E12/E13
establish is narrower than what was written on 2026-09-01 at 21:32, and one
of the things the adversarial panel found — that the plan's `ready` field is
dependence-sensitive — is more interesting than anything the project set out
to show, and cannot be claimed because it is post-hoc.

Every number below re-derives from raw model output via `python
verify_claims.py` (161 verified, 0 mismatched). Provenance: E12 `966f58c`,
E13 `418bab2`, corrections `docs/protocols/E13-CORRECTIONS.md`, prior-art
log `docs/novelty_matrix.md`.

---

## 1. What can be claimed, with its evidential status

| # | statement | status |
|---|---|---|
| S1 | On a planning task scored by a deterministic evaluator, `llama3.2:3b`'s **action ordering** is indifferent to whether three corroborating reports trace to one evidential root or three: E12 diff +0.0185, cluster-bootstrap CI [−0.037, +0.074]; E13 `default` (byte-identical prompt) diff +0.0000, CI [−0.056, +0.056]; both inside a preregistered SESOI of 0.10. | **Preregistered, replicated, equivalence-supported.** |
| S2 | Under an instruction to state the evidence structure first, the same model reports it correctly in about 40 % of paired units (`identify`: boolean 40 vs 0 reversed; count 49 vs 2) and misreports the independent case in about 40 % of units by every measure (42/108 answer *same source, one record*). | **Post-hoc pairing** of predeclared fields. The predeclared per-response accuracies are 0.843 (SAME) / 0.528 (INDEP) boolean, 0.130 count_strict. |
| S3 | Requiring the model to state the structure (`identify`), adding a normative principle (`normative`), a matched sham burden, or stating the correct structure outright (`gold`) did **not** move the ordering verdict detectably — but every one of those contrasts is **INCONCLUSIVE BY THE PREREGISTERED RULE** (observed discordance outside the powered band). | **Not null. Inconclusive.** |
| S4 | The plan's `ready` field ("safe to execute as written") **is** dependence-sensitive: one repeated record is declared safe more often than three distinct records, in every E13 arm and in E12 (E12 +0.26; E13 `default` +0.23, CI [+0.139, +0.333]; `gold` +0.20; all cluster p < 0.001). | **Post-hoc. Found by the attacker. Unconfirmed.** Reportable only as a hypothesis for a preregistered E14. |

## 2. What cannot be claimed

- "The model prices one root exactly as k independent roots" / "sees the
  redundancy and prices it at nothing" as statements about *the decision*.
  Withdrawn: S4 contradicts them on the decision's other field.
- "The two recognition measures disagree; the boolean shows a response bias."
  Withdrawn: one variable scored two ways.
- "The normative principle degraded recognition." Withdrawn: one row of two,
  untested, wrong-sign mechanism.
- "`gold` is an oracle null / the structure is behaviourally inert."
  Withdrawn: inconclusive by rule on ordering; moves `ready`.
- Any recognition→utilisation *dissociation*. The within-unit coupling test
  (protocol rule 6) was untestable at a ~5 % conjunction base rate, and S2
  and S3 are measured on different channels from S4.
- Novelty of S1. GroupQA (arXiv:2601.06189, Jan 2026) already contrasts
  paraphrases of one document with distinct documents on four 8B–70B models
  and finds no discount — indeed a preference for the paraphrases.

## 3. Where this sits against the closest prior work

| work | what it has | what it lacks that this project has |
|---|---|---|
| GroupQA, arXiv:2601.06189 | the paraphrased-vs-distinct manipulation; the behavioural finding, on larger models | a recognition probe; an executable decision; a second decision field |
| Information Discernment, arXiv:2607.19355 | the "estimate, then apply" template (M1/M2), for source *reliability*; a reliability prompt that helped | the *dependence* quantity |
| Whose Facts Win?, arXiv:2601.03746 | a "repetition should not influence you" prompt that mostly failed | dependence as distinct from repetition; recognition |
| CAMA, arXiv:2608.19701 | the phenomenon asserted and an architectural fix | any base-model recognition or told-correlation baseline |

The only thing in this project that none of them contains is S4 — and S4 is
the one thing this project did not preregister.

## 4. The one open lead, and its gate

**E14 — the `ready` channel, preregistered.** Outcome: `ready`, per unit,
SAME_ROOT vs INDEPENDENT_ROOT, E12's 108 units unmutated. Direction
predeclared (+ = one root declared safe more often). What `ready` is taken to
measure must be stated in advance: the E12 monotonicity (`filler` 105/108 →
`same_root` 60 → `indep_root` 32) suggests it tracks perceived conflict, in
which case "distinct records read as more conflict" is the hypothesis, and
its normative status is a separate question. `prospective_design_check` must
pass for a *difference* at SESOI 0.10 at the observed discordance (~0.27,
outside the ordering design's band) **before any model call**. Nothing else
is authorised: no router, no cross-model run before the mechanism is fixed on
Llama, no LEDGER.

## 5. What the process record shows

Seven experiments, four adversarial panels, five retractions or corrections
of my own conclusions — three of them found by panels pointed at work I
believed was clean, two of them the same failure class (a null on one measured
channel generalised past what was measured). The instrument that caught the
most was not a statistical test; it was a reader with the raw files and an
instruction to find the next one.
