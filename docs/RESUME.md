# RESUME — where the work stands, and exactly what to do next

**Paused 2026-09-01, mid-campaign, at the end of E13 step 9.** Everything is
committed. Nothing is running. No remote exists.

Start a new session with: *"Read docs/RESUME.md and continue from step 10."*

---

## 1. Verify the state is intact (run this first, ~2 min)

```bash
cd C:/Users/chris/week1-llm-lab
git branch --show-current            # expect: crazy
git status --porcelain               # expect: empty
python verify_claims.py              # expect: 143 verified, 0 mismatched, 3 unverifiable
python prospective_design_check.py --self-test    # expect: 7/7 passed
```

All twelve suites must pass:
`test_engine test_scenario test_finalise test_context test_judge test_retrieval
test_lineage_bench test_lineage_modeb test_lineage_e10 test_lineage_e11
test_lineage_e12 test_lineage_e13`

Frozen corpus hashes — **if any differ, stop and investigate before anything
else**:

| corpus | hash |
|---|---|
| Mode A | `9dd2cea16a8142c2` |
| E10 | `00947dde8eb0520b` |
| E11 | `5c28ada4c4b899dc` |
| E12 | `ecf1f4884fa49270` |
| E13 prompts | `5c23297196241110` |

Tags: `compulsory-baseline-v1`, `e1-landscape-v1`, `selector-protocol-v1`,
`e3-authority-v1`, `e7-modeb-v1`, `e12-powered-v1`.

---

## 2. The two locked results (do not re-litigate)

**Cross-family corroboration dose-response.** Contradiction adoption falls as
faithful paraphrastic corroborations increase, in 3/3 distinct model families
(Meta, Cohere, Alibaba). Llama: 0.75 → 0.4167 → 0.2778 → 0.1111.

**Evidential-dependence null (E12, replicated by E13).** SAME_ROOT vs
INDEPENDENT_ROOT: E12 diff +0.0185, p = 0.749, CI [−0.037, +0.074]; E13
DEFAULT diff **+0.0000**, p = 1.0, CI [−0.056, +0.056]. Both inside the
preregistered SESOI of 0.10. **Equivalence-supported.**

Standing prohibitions: do not claim lineage sensitivity, do not build
AnchorRoute, do not try to make SAME differ from INDEP, do not change the
SESOI, do not revive dilution or E8's P7.

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

**Recognition (RQ1).** The two predeclared measures disagree:
- **boolean (primary)** — response bias: `identify` scores 0.843 on same-root
  but 0.528 on independent-root.
- **count (secondary)** — discriminates strongly: `identify` reports more
  sources for INDEP in **49** units vs **2**, sign p = **1.18e-12**, agreeing
  with E12's frozen probe (27 vs 0, p = 1.5e-08).

The boolean stays primary. Its bias is a reported measurement defect, **not** a
reason to swap measures after the fact.

**NORMATIVE degraded recognition** — boolean same-root 0.843 → 0.602, count
discrimination 36 vs 25 (p = 0.20). Stating the principle made the model *worse*
at seeing the structure.

**GOLD moved behaviour by exactly 0.0000** while being handed the correct
structure outright.

---

## 4. Two defects recorded against my own work

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

---

## 5. NEXT — resume at step 10

**Step 10 — adversarially attack the E13 interpretation.** A workflow script is
already written and ready:

```
C:/Users/chris/AppData/Local/Temp/claude/C--Users-chris-week1-llm-lab/
  4c244fd2-6d3b-4297-82e4-a6ac784bb2d9/scratchpad/attack_e13.js
```

Launch with `Workflow({scriptPath: "<that path>"})`. Five lenses: overclaim,
parse-rate confound, whether the recognition measure is real or lexical,
the coupling statistic, and whether SHAM is difficulty-matched.
*(If the scratchpad has been cleared, the script is small enough to rewrite from
the lens list above.)*

**Step 11 — the blocking prior-art search. THIS IS THE GATE ON EVERYTHING.**
`docs/novelty_matrix.md` C8 is `UNKNOWN` and cannot be promoted without it. The
two questions that decide it:

1. **CAMA, arXiv:2608.19701** — does it already show a *base* LLM correctly
   recognising shared-source dependence yet failing to behaviourally price it?
   If yes, **C8 is pre-empted outright.**
2. **Information Discernment, arXiv:2607.19355** — does its M1/M2 decomposition
   cover source *dependence*, or only source *reliability*? If "apply" already
   covers independence, C8 collapses into it.

Also check: Whose Facts Win? (arXiv:2601.03746), Most LLM Conformity Needs No
Speaker (arXiv:2607.05545), and the human illusion-of-consensus work (Yousif
2019; Connor Desai 2022/2026). Twelve adversarial queries are listed in
`docs/novelty_matrix.md`.

**This session exhausted its web-search budget (200/200), which is why the
search never ran.** A new session gets a fresh budget — run it first.

**Step 12 — stop and report.** Do **not** start another broad campaign. Do not
build a router. If E13 survives the attack *and* the prior art, write a
publication-level claim memo and stop.

**Not yet run, and conditional:** cross-model E13 (Aya, Qwen) only after the
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
| `docs/handoff.md` | full external-review document |
| `verify_claims.py` | re-derives all 143 numbers from raw output |
| `prospective_design_check.py` | refuses designs that cannot reach their conclusion |
| `robust_client.py` | bounded transport-only retry |

**Standing rules:** no outcome-based tuning; preregister before model calls;
retractions are immutable; frozen artifacts are never modified; no remote
without explicit instruction.
