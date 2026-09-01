# RESUME — where the work stands, and exactly what to do next

# RESEARCH CLOSED — 2026-09-02

**E15-PODT: RETIRED** by the independent Gemini literature review (no model
call was ever made for it). **FFEP** (Gemini's proposed pivot, claim-relative
counterfactual auditing of agent evaluations): **STOP_FFEP** after this
repository's own feasibility audit — two adversarial prior-art reviews
returned HEAVY OVERLAP (Mystery Blocksworld 2023 performs the procedure;
Turk 2026 and HackDetect 2026 on agents), the method would have caught 5 of
17 of this project's own historical failures, and the residue is
methodological packaging. `docs/FFEP-FEASIBILITY.md` (15 sections, one
decision). No E15/E16 outcome exists.

**Remote:** private GitHub repository https://github.com/Chrislysen/week1-llm-lab
(branches `crazy`, `main`, `core-frozen`; all six tags). `main` is
fast-forwarded to `crazy`; the two are identical.

Nothing is queued. Do not search for E16. The next action, if any, is the
negative-results write-up named in `docs/RESEARCH-LEAD-2026-09-02.md` §8.

Feasibility infrastructure added 2026-09-02 (no model calls, no frozen
artifact touched): `ffep_inventory.py`, `ffep_mutations.py`,
`test_ffep_mutations.py` (12 gates), `ffep_power.py`, `docs/ffep_*.json`.
Test expectation is now **104 passed** over 14 suites
(`test_ffep_mutations.py` added).

---

# (superseded) RESEARCH PAUSED PENDING EXTERNAL NOVELTY REVIEW

**Paused 2026-09-02 at commit `48c6860`.** Working tree clean, no remote at
the time (a private remote was added later, see the top of this file),
nothing running. Frozen hashes intact; `verify_claims.py` 167 VERIFIED /
0 MISMATCHED / 4 UNVERIFIABLE; 92 tests; checker self-test 10/10.

**Candidate:** E15-PODT / Provenance-Only Dependence Test.

**Status:** APPARENTLY OPEN FROM ONE DEEP-RESEARCH REVIEW.
NOT PREREGISTERED. NOT AUTHORIZED. ZERO E15 MODEL CALLS. **Not NOVEL.**
An independent review (Gemini) is adversarially searching the literature and
may kill it. Proposal only: `docs/E15-CANDIDATE.md`.

**Do not:** start E15, generate an E15 corpus, preregister it, make model
calls, modify E1–E14 artifacts, revive E14, build a provenance router, or
implement the proposed Bayesian task. Wait for the external verdict.

External handoff for a research model: `docs/HANDOFF-EXTERNAL-2026-09-02.md`.
Closing memo of the last pass: `docs/RESEARCH-LEAD-2026-09-02.md`. Verdict
table: `docs/novelty_matrix.md` C1–C14.

---

**The research-lead pass (2026-09-01/02) closed the earlier programme.**
Everything below is its record.

---

## 1. Verify the state is intact (run this first, ~2 min)

```bash
cd C:/Users/chris/week1-llm-lab
git branch --show-current            # expect: crazy
git status --porcelain               # expect: empty
python verify_claims.py              # expect: 167 verified, 0 mismatched, 4 unverifiable
python prospective_design_check.py --self-test    # expect: 10/10 passed
```

All thirteen suites must pass:
`test_engine test_scenario test_finalise test_context test_judge test_retrieval
test_lineage_bench test_lineage_modeb test_lineage_e10 test_lineage_e11
test_lineage_e12 test_lineage_e13 test_lineage_e14`

Frozen corpus hashes — **if any differ, stop and investigate before anything
else**:

| corpus | hash |
|---|---|
| Mode A | `9dd2cea16a8142c2` |
| E10 | `00947dde8eb0520b` |
| E11 | `5c28ada4c4b899dc` |
| E12 | `ecf1f4884fa49270` |
| E13 prompts | `5c23297196241110` |
| E14 (preregistered, never run) | `6cd7dafac78c31fe` |

Tags: `compulsory-baseline-v1`, `e1-landscape-v1`, `selector-protocol-v1`,
`e3-authority-v1`, `e7-modeb-v1`, `e12-powered-v1`.

---

## 2. The two locked results (do not re-litigate)

**Cross-family corroboration dose-response.** Contradiction adoption falls as
faithful paraphrastic corroborations increase, in 3/3 distinct model families
(Meta, Cohere, Alibaba). Llama: 0.75 → 0.4167 → 0.2778 → 0.1111.

**Evidential-dependence null ON THE ORDERING VERDICT (E12, replicated by
E13).** SAME_ROOT vs INDEPENDENT_ROOT: E12 diff +0.0185, p = 0.749, CI
[−0.037, +0.074]; E13 DEFAULT diff **+0.0000**, p = 1.0, CI [−0.056, +0.056].
Both inside the preregistered SESOI of 0.10. **Equivalence-supported — for
the ordering only.** Scope correction 2026-09-01: the plan's `ready` field is
dependence-sensitive (post-hoc, unconfirmed; §4). Do not write "prices it at
nothing" about the decision.

Standing prohibitions: do not claim lineage sensitivity, do not build
AnchorRoute, do not try to make SAME differ from INDEP, do not change the
SESOI, do not revive dilution or E8's P7, do not claim the `ready` effect
before a preregistered E14 confirms it.

---

## 3. What E13 found (committed `418bab2`)

1080 calls, 108 units in 36 clusters, `llama3.2:3b`, parse rate **1.00** in
every cell.

| arm | diff | p | CI | discordance | preregistered reading |
|---|---|---|---|---|---|
| `default` | +0.0000 | 1.0 | [−0.056,+0.056] | 0.093 | **equivalence-supported null** |
| `identify` | −0.0093 | 1.0 | [−0.083,+0.056] | 0.139 | INCONCLUSIVE BY RULE |
| `normative` | −0.0741 | 0.0564 | [−0.139,−0.009] | 0.148 | INCONCLUSIVE BY RULE |
| `sham` | −0.0370 | 0.2946 | [−0.093,+0.009] | 0.074 | INCONCLUSIVE BY RULE\* |
| `gold` | +0.0000 | 1.0 | [−0.056,+0.065] | 0.075 | INCONCLUSIVE BY RULE\* (diagnostic) |

\* blocked by a **defect in my own band rule** — see §5.

**Recognition (RQ1) — CORRECTED 2026-09-01.** What `418bab2` called "two
measures disagreeing" was one variable scored two ways. Paired by unit, the
primary boolean discriminates **40 vs 0** (p = 1.8e-12) under `identify`,
exactly as the count does (49 vs 2); under `normative` **34 vs 4**. The
paired count test was **post-hoc** — added after the first 36 units were on
disk — and mislabelled predeclared. The predeclared per-response numbers:
`identify` INDEP boolean 0.528, count_strict **0.130**. **42/108 units
misrecognise INDEP by every measure.** Rule 2 has no threshold and is
unadjudicated. The "27 vs 0" probe is E10's manipulation check, not E12's.

**"NORMATIVE degraded recognition" is WITHDRAWN** — one row of two, no
between-arm test, and the stated mechanism has the wrong sign.

**GOLD moved the ORDERING verdict by 0.0000** while being handed the correct
structure outright — and is INCONCLUSIVE BY RULE there, not an "oracle null".
On the `ready` field it moved **+0.20** (§4).

---

## 4. Defects recorded against my own work

**The coupling test could not have worked.** `P(sensitive | recognized)` vs
`P(sensitive | misrecognized)` is 0.025 vs 0.088 (Fisher p = 0.256) and 0.059 vs
0.027 (p = 0.589). "Independence-sensitive action" requires a *conjunction*
(flip on SAME **and** hold source on INDEP), giving a ~5% base rate and
subgroups 1–6 units wide. **Falsification rule 6 is untested, not passed.**
Any follow-up needs a graded outcome measure, not a conjunction.

**The powered band has a defect.** `[0.08, 0.12]` was computed for *difference
detection*. Its lower bound wrongly blocks *equivalence* readings, where low
discordance is favourable. It blocked `sham` and `gold`; read on the equivalence
criterion both are equivalence-supported. The rule is left as written and fired;
the corrected reading is printed separately and flagged post-hoc.

**The decision has two output fields and I scored one (found by the step-10
panel, verified).** The plan JSON is `{"actions", "ready"}`; `ready` ("safe to
execute as written") is required to parse and is part of
`deterministic_success`. E12 and E13 never analysed it. Re-derived:
`default` ready(SAME) 59/108 vs ready(INDEP) 34/108, **+0.2315**, cluster
p = 0.0002, CI [+0.139, +0.333]; `gold` +0.2037 (p = 0.0001); E12 +0.2593.
Every arm, about twice the SESOI. The ordering null stands; "prices one root
exactly as k independent roots" is withdrawn as a decision-level claim.
**Post-hoc, unconfirmed — the one thing worth an E14.**
`docs/protocols/E13-CORRECTIONS.md`, which also records that the paired count
test was post-hoc and that "NORMATIVE degrades" is withdrawn.

---

## 5. Research-lead pass — 2026-09-01/02. The programme is closed.

Everything below the next heading is history. What closed it:

- **`ready` mined from every raw plan on disk** (E2, E4, E7, E8, E9, E10, E11,
  E12, E13; five deciders). At ceiling for Aya-8B, Qwen-3B, Qwen-7B in every
  arm; varies only in llama-3B and Qwen-14B.
- **READY is a repetition/consistency effect, not dependence** (matrix C10):
  same-root readiness rises with each repeated identical citation (E11 19 →
  21 → 27, k1 vs k3 paired 0/8), independent-root is flat (17, 17, 17), two
  agreeing reports of either kind lower readiness from ~0.78 to ~0.5, the gap
  runs 0 → +0.5 by which document names the rotation draws, and `ready`
  follows the model's own same-source token (129/242 vs 1/190).
- **Qwen-14B (declared screen E12-X)** shows no same/indep readiness gap
  (−0.046, CI [−0.111, +0.018]) and its readiness rises with corroboration
  where llama's falls. READY is llama-specific. **E14 in any form is not
  pursued.**
- **Prior art** (six adversarial reviewers, ~150 searches): the commit-gate
  abstraction is published (arXiv:2608.27167); the same-source contrast on
  Llama-3.2-3B exists (arXiv:2601.03746); the benchmark's premise is false
  (ManyIH-Bench, IHEval; corrected in `docs/agent-lineage-bench.md`); the
  apparatus is pre-empted (llm-power, tail-shape protocol, showyourwork,
  POPPER); latest-trusters replicate IHEval / Control Illusion.
- **Normative backfire (C14)**: HEAVY OVERLAP — KAIROS (arXiv:2508.18321)
  shows a critical-evaluation prompt worsens peer-pressure robustness on this
  very model. The declared cross-family screen (E13-X) found the principle's
  effect +0.037 in Aya and +0.005 in Qwen-7B against llama's +0.09: llama-
  specific. Closed.

**Standing prohibitions, unchanged:** no lineage-sensitivity claim, no router,
no dilution, no SESOI change, no claim from any exploratory screen.

## 5-history. Steps 10–12 — DONE 2026-09-01.

**Step 10 — DONE.** `docs/attack_e13.js` ran as workflow `wf_35c74eab-aee`:
27 agents, 22 candidates, **5 survived refutation**, every one re-derived by
me before acceptance and recorded in `docs/protocols/E13-CORRECTIONS.md`.
Three conclusions withdrawn (the recognition "disagreement / response bias";
"NORMATIVE degrades"; the decision-level "prices it at nothing") and two
record corrections (the paired count test was post-hoc; the 27 vs 0 probe is
E10's). `e13_recognition.py --analyse` now prints both post-hoc blocks
flagged, and `verify_claims.py` pins the corrected numbers (161 verified).

**Step 11 — DONE 2026-09-01 (commit `f5d218d`).** The search ran in a fresh
session: 19 searches, 15 papers. **Neither blocking paper fires the rule** —
CAMA (arXiv:2608.19701) has no recognition probe and no told-correlation
baseline; Information Discernment (arXiv:2607.19355) defines M1/M2 over source
*reliability* only. **But GroupQA (arXiv:2601.06189, Jan 2026) already runs
E12's paraphrased-one-document vs distinct-documents contrast** on four 8B–70B
models and finds the paraphrases weighted *more*, with no recognition probe and
no intervention. C8 was therefore **OPEN (NARROW), not NOVEL** — and was then withdrawn as
phrased in step 10: residue = recognition probe on the same units + `gold`'s
ordering result (0.0000; the "oracle null" reading is withdrawn), on one 3B
model. C4 is PRE-EMPTED (behavioural). Full table and search log in
`docs/novelty_matrix.md`; `docs/findings.md` §0/§4 updated.

**Step 12 — DONE.** E13 survived the prior art (C8 not pre-empted on its
conjunction) and did **not** survive the attack intact. `docs/CLAIM-E13.md`
states what is left. No router, no new campaign.

**E14 v1 — preregistered and ABORTED before any confirmatory call; superseded by §5 (no v2)
(2026-09-01).** Built to the instruction: a fresh 432-unit / 144-cluster
corpus (four salted draws of the frozen generator), FIXED_PLAN primary,
GENERATED replication, a within-response interaction test, checker operating
bands (432/144 PROCEEDS; 324/108 ABORTS), a verifier section and four fixture
tests — all committed with zero outcomes. Hypothesis-blind pilots then found
the FIXED instrument **at floor** on `llama3.2:3b`: **0 of 149** `ready =
true` across seven framings, three plan contents and every graph, because in
judge mode the model treats the contradictory discussion as making any plan
unsafe. Kill rule 5 fires before the run; **no confirmatory call was made**.
`docs/protocols/E14-ready-channel-v1.md` §16 holds the pilot table and four
v2 options (GENERATED-only primary; a different decider; a FIXED arm without
the contradiction; stop). **Choosing among them is the user's decision. Do not
run any of them unasked.**

**Also not yet run, and conditional:** cross-model E13 (Aya, Qwen) only after the
mechanism is identified on Llama; `LEDGER` (RQ5) only if a normative
intervention works — it did not.

**Backup question, only after E13 closes:** corroboration-induced hysteresis.
E10 found none (36/36 accepted a legitimate update with and without prior
support) but that was at ceiling on an easy supersession.

---

## 6. Key files

| file | what it is |
|---|---|
| `docs/findings.md` | one page: what survives, what was retracted |
| `docs/novelty_matrix.md` | 8 candidate claims; **none novel**; C8 is the live one |
| `docs/protocols/E13-recognition-utilization-v1.md` | E13 preregistration |
| `docs/protocols/E10-H3-RETRACTION.md` | the retraction that shaped everything after it |
| `docs/protocols/E13-CORRECTIONS.md` | the step-10 corrections: three E13 conclusions withdrawn, all verified |
| `docs/protocols/E14-ready-channel-v1.md` | E14 preregistration, and its §16 abort record with the pilot table |
| `docs/RESEARCH-LEAD-2026-09-02.md` | the closing memo: what died, what survived, why it stops |
| `docs/protocols/E12X-qwen14b-ready-screen.md`, `E13X-backfire-screen.md`, `screen_analysis.py` | the two declared exploratory screens and their reader |
| `lineage_e14.py`, `e14_ready.py`, `test_lineage_e14.py` | E14 corpus, experiment and analysis, 23 gates + 4 fixture tests — built, never run |
| `docs/CLAIM-E13.md` | what can still be claimed, and what cannot |
| `docs/attack_e13.js` | the adversarial workflow that found them |
| `docs/handoff.md` | full external-review document |
| `verify_claims.py` | re-derives all 161 numbers from raw output |
| `prospective_design_check.py` | refuses designs that cannot reach their conclusion |
| `robust_client.py` | bounded transport-only retry |

**Standing rules:** no outcome-based tuning; preregister before model calls;
retractions are immutable; frozen artifacts are never modified; no public remote (the private one above only)
without explicit instruction.
