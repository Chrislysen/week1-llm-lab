# External handoff — for an independent research model, 2026-09-02

**State.** Branch `crazy`, commit `48c6860`, paused. Private remote: https://github.com/Chrislysen/week1-llm-lab (main == crazy).
Working tree clean. `verify_claims.py`: 167 VERIFIED / 0 MISMATCHED /
4 UNVERIFIABLE. 92 tests in 13 suites. `prospective_design_check.py
--self-test` 10/10. Every frozen hash intact (table below).

**Why you are reading this.** One deep-research pass has proposed a candidate
direction (`docs/E15-CANDIDATE.md`, status APPARENTLY OPEN, not authorised).
Your job is to challenge it, or to find a stronger direction, from the
literature and from these artifacts. Do not trust this summary where a raw
file can answer the question.

## 1. Scientific timeline (one line each; details in the linked files)

| stage | question | outcome | where |
|---|---|---|---|
| compulsory | two-agent dialogue under a context budget | baseline frozen | tag `compulsory-baseline-v1` |
| E1 | selectors vs recency | no selector beats random on source recall; diagnostic only | tag `e1-landscape-v1`, `docs/research-design.md` |
| E2 | AgentLineageBench Mode A built and validated | 36 instances, 9 exposure conditions; decision follows a corrupted derivative 57 % when both are in context | `lineage_bench.py`, `docs/agent-lineage-bench.md`, `docs/handoff.md` §1–3 |
| E3/E4 | can models tell legitimate supersession from corruption; does an authority rule help | latest-trusters, 3B–14B; rule barely read | tag `e3-authority-v1`, `results/e4_summary.csv` |
| E4b | restriction increases revision-following | **retired by its own control** | `docs/findings.md` §2 |
| E5–E9 | relay depth, Mode B external validity, cross-model, speaker 2×2 | corroboration reduces adoption of a later contradiction; "length does nothing" retracted; dilution unstable | tag `e7-modeb-v1`, `docs/handoff.md` §3–5 |
| E10 | evidential dependence (same root vs independent) | reported as a fired kill rule, **retracted** as underpowered | `docs/protocols/E10-H3-RETRACTION.md` |
| E11 | multiplicity k = 1..3, three families | dose-response replicates in Meta/Cohere/Alibaba; dependence contrast underpowered everywhere | `docs/protocols/E11-multiplicity-v1.md`, `results/e11_*` |
| E12 | powered dependence test, 108 units / 36 clusters | equivalence-supported null on the ordering channel | tag `e12-powered-v1`, `docs/protocols/E12-powered-independence-v1.md` |
| E13 | recognition → utilisation, 5 interventions | default replicates E12 byte-for-byte; interventions inconclusive by rule; three write-up conclusions later **withdrawn**; `ready` field found dependence-sensitive post-hoc | `docs/protocols/E13-*.md`, `docs/CLAIM-E13.md` |
| E14-v1 | confirm the `ready` effect with a FIXED-plan arm | preregistered, then **aborted before any confirmatory call**: the FIXED instrument is at floor (0/149 blind pilot calls) | `docs/protocols/E14-ready-channel-v1.md` §16 |
| research-lead pass | mine `ready` across all raw plans; six adversarial reviews; two declared exploratory screens | `ready` is a single-model repetition/consistency effect; every candidate pre-empted, closed or single-model | `docs/RESEARCH-LEAD-2026-09-02.md`, `docs/novelty_matrix.md` C9–C14, `docs/protocols/E12X-*.md`, `E13X-*.md` |

## 2. Frozen artifacts

| tag / corpus | hash | note |
|---|---|---|
| `compulsory-baseline-v1`, `selector-protocol-v1`, `e1-landscape-v1` | — | course baseline and E1; never rerun |
| Mode A corpus (`lineage_bench.py`) | `9dd2cea16a8142c2` | `verify_claims.py` asserts it |
| Mode B corpus (`e7-modeb-v1`) | `4a2938565a36ee9f` | |
| E3 corpus (`e3-authority-v1`) | `371cedb074d9e4ba` | |
| E10 | `00947dde8eb0520b` | `lineage_e10.corpus_hash()` |
| E11 | `5c28ada4c4b899dc` | `lineage_e11.corpus_hash()` |
| E12 (`e12-powered-v1`) | `ecf1f4884fa49270` | `lineage_e12.corpus_hash()` |
| E13 prompts | `5c23297196241110` | `e13_recognition.corpus_hash(plan_instruction)` |
| E14 (preregistered, never run) | `6cd7dafac78c31fe` | `lineage_e14.corpus_hash()` |

The generator gained an optional `salt` for E14; the default path is asserted
byte-identical by every hash above.

## 3. Retraction map

Read `docs/findings.md` §2 first; it is the longest table in the project and
the honest summary. The load-bearing ones:

| what was reported | what killed it | record |
|---|---|---|
| E2 v1 whole run (echo policy scored 36/36) | a null control | findings §2 |
| E4b authority effect | its own speaker-free control | findings §2 |
| E5 step function (twice) | a p = 1.0 null; then the corrected corpus | findings §2 |
| E7 "length does nothing"; E9/E10 dilution | E9; then E11/E12 | findings §2 |
| E7/E5 identification (corroboration collinear with self-reversal) | an adversarial audit | findings §2 |
| **E10 "the model assigns zero weight to dependence"** | its own preregistered code printed *inconclusive*; power 0.14 | `docs/protocols/E10-H3-RETRACTION.md` |
| **E13 "two recognition measures disagree / response bias"; "normative degrades recognition"; "prices it at nothing" as a decision-level claim** | an adversarial panel; the `ready` field | `docs/protocols/E13-CORRECTIONS.md` |
| **"every conflict benchmark treats the source as the answer key"** | ManyIH-Bench, IHEval, latest-wins memory benchmarks | `docs/agent-lineage-bench.md` (correction in place) |

## 4. What survives

1. **Ordering-channel equivalence null** for same-root vs independent
   corroboration: E12 +0.0185, CI [−0.037, +0.074]; E13 default +0.0000,
   CI [−0.056, +0.056]; SESOI 0.10; instance-level inference. Consistent
   with GroupQA. Not novel.
2. **Corroboration dose-response** in three families (E11): llama 0.75 →
   0.42 → 0.28 → 0.11. Not novel.
3. **Latest-truster behaviour** across five local deciders (E3/E4).
   Replicates IHEval / Control Illusion.

## 5. Dead directions (do not reopen without new evidence)

Lineage sensitivity of the decision (C4, C8); AnchorRoute / any router
(C7, killed on measurement in E6); dilution (C2, does not replicate);
readiness dissociation and readiness-as-dependence (C9, C10: single-model,
repetition/consistency readout; abstraction published in arXiv:2608.27167);
E14 in any form; the benchmark as a headline (C11); the apparatus as
methodology (C12); latest-trusters as a headline (C13); the normative
backfire (C14: llama-specific; KAIROS on the same model). Every verdict with
its closest work is in `docs/novelty_matrix.md`.

## 6. Verifier — run this before believing any number

```
python verify_claims.py                        # expect 167 verified, 0 mismatched, 4 unverifiable
python prospective_design_check.py --self-test # expect 10/10
python -m pytest -q test_engine.py test_scenario.py test_finalise.py test_context.py \
  test_judge.py test_retrieval.py test_lineage_bench.py test_lineage_modeb.py \
  test_lineage_e10.py test_lineage_e11.py test_lineage_e12.py test_lineage_e13.py \
  test_lineage_e14.py                          # expect 92 passed
```

`verify_claims.py` re-derives every reported number from raw model output
(`results/*.json`, field `plan_text`) through the deterministic evaluator; it
never reads a summary CSV as truth; any MISMATCH exits non-zero. UNVERIFIABLE
marks artifacts scored against an earlier corpus (E1/E2/E4) and E14's
outcomes (none exist). The two exploratory screens (`results/e12_qwen25-14b-*`,
`results/e13x_*`) are filtered out of every claim; read them with
`python screen_analysis.py --e12x qwen2.5:14b-instruct` and
`--e13x <model>`.

## 7. Where the raw artifacts are

| experiment | raw responses (`plan_text`) | scored rows |
|---|---|---|
| E2 | `results/e2_matrix_detail*.json` | `results/e2_matrix_runs*.csv` |
| E3 / E4 | `results/e4_*_o*.json` | `results/e3_mixed_runs.csv`, `results/e4_*_o*.csv`, `results/e4_summary.csv` |
| E5 / E7 / E8 / E9 | `results/e5_*.json`, `e7_modeb_*.json`, `e8_cross_*.json`, `e9_speaker_*.json` | matching `*.csv` |
| E10 / E11 / E12 / E13 | `results/e10_*.json`, `e11_<model>_o*.json`, `e12_llama32-3b_o*.json`, `e13_llama32-3b_o*.json` | matching `*.csv`; summaries `e1{0,1,2,3}_*.csv` |
| exploratory screens | `results/e12_qwen25-14b-instruct_o*.json`, `results/e13x_<model>_o*.json` | matching `*.csv` |

Corpora regenerate deterministically from `lineage_bench.py`, `lineage_e10.py`,
`lineage_e11.py`, `lineage_e12.py`, `lineage_e13.py`, `lineage_e14.py`.
Protocols are in `docs/protocols/`; each preregistration was committed with
zero outcomes in the tree (check `git log` around each).

## 8. Novelty matrix

`docs/novelty_matrix.md`. Rows C1–C14; statuses PRE-EMPTED / HEAVY OVERLAP /
ADJACENT / APPARENTLY OPEN / UNKNOWN / CLOSED. The file's rule: APPARENTLY
OPEN is never promoted to NOVEL because a search found nothing; promotion
needs an adversarial search that tried to find the killing paper and failed,
plus a written comparison. No row is NOVEL. Search logs are at the end of
the file and in `docs/RESEARCH-LEAD-2026-09-02.md`.

## 9. Standing rules

No outcome-based tuning; preregister before model calls; retractions are
immutable; frozen artifacts are never modified; no remote; `p > .05` is never
equivalence; repeated observations are never independent; a post-hoc
discovery never becomes a preregistered claim; historical exploratory data
never enters a confirmatory statistic. **E15 is not authorised.**
