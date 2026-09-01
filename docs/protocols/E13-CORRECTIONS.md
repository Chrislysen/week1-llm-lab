# CORRECTIONS — E13, 2026-09-01. Three findings from the adversarial panel, all verified.

**Status.** Commits `459fc88` and `418bab2` are left in history unaltered; this
document supersedes three of their conclusions. Found by a 27-agent adversarial
panel (`docs/attack_e13.js`, run `wf_35c74eab-aee`, 22 candidates, 5 survived
refutation, 17 refuted). **I re-derived every number below from the raw files
before accepting it**; the re-derivations are pinned in `verify_claims.py` and
printed, flagged POST-HOC, by `python e13_recognition.py --analyse`.

| # | what was written | status |
|---|---|---|
| C1 | "The two predeclared recognition measures disagree: the boolean shows a RESPONSE BIAS, the count discriminates strongly (49 vs 2), agreeing with E12's frozen probe" | **WITHDRAWN** |
| C2 | "NORMATIVE degraded recognition — the principle made the model worse at seeing the structure" | **WITHDRAWN** |
| C3 | "The model prices k reports from one evidential root exactly as it prices k independent roots" / "sees the redundancy and prices it at nothing" — stated as a claim about *the decision* | **WITHDRAWN as a decision-level claim.** Survives only as a claim about the **ordering verdict**. |

Two further facts about my own record are corrected in §4: the paired count
test was **post-hoc**, not predeclared; and the "27 vs 0" probe is **E10's**
manipulation check, not an E12 probe.

---

## 1. C1 — one variable scored two ways is not two measures disagreeing

The `identify` arm asks for a boolean (`same_underlying_source`) and a count
(`independent_source_count`) in the same JSON object. I scored the boolean
**unpaired** (per-arm accuracy 0.843 / 0.528), scored the count **paired**
(sign test 49 vs 2), and wrote that the primary measure had a response bias
while the secondary "discriminates strongly".

Within a response the two fields move in lockstep. `identify` on SAME_ROOT:
`(True, 1)` × 91, `(False, 4)` × 17 — 108/108. On INDEPENDENT_ROOT:
`(False, 4)` × 44, `(True, 1)` × 42, `(False, 3)` × 12, `(True, 2)` × 7,
`(True, 3)` × 2, `(False, 2)` × 1.

Score the **boolean** paired exactly as the count was scored:

| arm | boolean: same=T & indep=F | reversed | sign p | count: indep > same | reversed | sign p |
|---|---|---|---|---|---|---|
| `identify` | **40** | **0** | 1.8e-12 | 49 | 2 | 1.2e-12 |
| `normative` | **34** | **4** | 6.0e-07 | 36 | 25 | 0.20 |

The fields do not disagree. The "disagreement" was an unpaired statistic on
one field set beside a paired statistic on the other. Under `normative` the
asymmetry runs the other way (boolean discriminates, count does not), which
would have flipped C2 had I paired the boolean instead.

What the data actually show: on `identify` INDEPENDENT_ROOT, **42 of 108 units
answer `same=True` AND `count=1`** — misrecognition by every available
measure. Paired recognition is 40–49 of 108 units (37–45 %). Falsification
rule 2 ("recognition accuracy is weak → the problem is perceptual") has no
threshold in the protocol and **cannot be adjudicated as written**. It is
**UNADJUDICATED**, not dismissed. The "response bias, not absence of
recognition" sentence dismissed it without a rule to dismiss it by.

## 2. C2 — "NORMATIVE degrades recognition" was one row of two, untested, with a sign-reversed mechanism

I reported boolean accuracy on SAME_ROOT falling 0.843 → 0.602 and explained
it as the principle "priming *same source* as the salient answer".

- The INDEPENDENT_ROOT row moves the **other way**: 0.528 → 0.676.
- Raw `same=True` answers fall on **both** levels under `normative`: 91 → 65
  on SAME_ROOT, 51 → 35 on INDEPENDENT_ROOT. The principle primed
  "different", not "same". The stated mechanism has the wrong sign.
- No between-arm test exists anywhere in the repo. `verify_claims.py` pinned
  the number 36 under the label "DEGRADES"; a label is not a test.
- Paired, the boolean under `normative` still discriminates (34 vs 4). What
  moved is the response criterion, not discrimination: the panel's
  signal-detection reading (criterion c −0.47 → +0.10, d′ 1.08 → 0.71) is
  reported by the panel and **not re-derived here**.

Withdrawn. The defensible sentence is: *the principle shifted the boolean's
response criterion away from "same" on both levels; whether it changed
discrimination is untested.*

## 3. C3 — the decision has two output fields and only one was ever scored

The plan JSON the model returns is `{"actions": [...], "ready": true|false}`.
`ready` is defined in the frozen prompt as *"true if you consider the plan safe
to execute as written"*. `lineage_eval.parse_plan` **requires** it for a plan
to parse; `docs/research-design.md` defines `deterministic_success` as
*parsed ∧ ready ∧ zero violations*. By the repo's own definitions it is part
of the executable decision.

E12 and E13 preregistered, scored and reported **only the ordering verdict**
(`source` / `flip`). `ready` was never written to a CSV and never analysed.
Re-derived from the raw plan text with the project's own cluster permutation
and cluster bootstrap (instance-level, 20 000 / 10 000 reps, seed 20260901):

| arm | ready(SAME) | ready(INDEP) | diff | paired same>indep / indep>same | cluster p | 95 % CI |
|---|---|---|---|---|---|---|
| `default` | 59/108 | 34/108 | **+0.2315** | 27 / 2 | 0.0002 | [+0.139, +0.333] |
| `identify` | 36/108 | 18/108 | +0.1667 | 21 / 3 | 0.0051 | [+0.065, +0.269] |
| `normative` | 50/108 | 26/108 | +0.2222 | 29 / 5 | 0.0007 | [+0.111, +0.343] |
| `sham` | 86/108 | 71/108 | +0.1389 | 18 / 3 | 0.0048 | [+0.056, +0.222] |
| `gold` | 63/108 | 41/108 | **+0.2037** | 25 / 3 | 0.0001 | [+0.120, +0.287] |
| **E12** `same_root` vs `indep_root` | 60/108 | 32/108 | **+0.2593** | 30 / 2 | < 0.0001 | [+0.176, +0.343] |

E12's other arms: `filler` 105/108 ready, `bare` 83/108.

Every arm — including the byte-identical `default` and the `gold` oracle —
moves this output by roughly **twice the SESOI**, cluster-robust, and E12's own
raw plans replicate it. The direction: three restatements of **one** record
are declared "safe to execute" **more** often than three **distinct** records.
Whether that is normative or anti-normative is a question about what `ready`
measures (the E12 monotonicity `filler` 105 → `same` 60 → `indep` 32 suggests
it tracks perceived conflict, and distinct records read as more conflict).
What is not a question: **the model does not price one root and three
independent roots identically in its executable output.**

The ordering-verdict null is unchanged: `default` +0.0000, CI [−0.056, +0.056].
Every sentence that generalised it to *the decision* — E13 protocol §1,
`lineage_e13.py` and `e13_recognition.py` docstrings, `findings.md` §0,
`handoff.md` "Final answer", and the C8 claim text "prices them as k
independent confirmations in a downstream executable decision" — is
**withdrawn as written** and re-scoped to the ordering channel.

**This is the E10 failure class in a new place**: a null on one measured
channel generalised to "the decision" while an unmeasured decision field in
the same JSON object contradicts it. The panel's artefact checks (not a proxy
for the flip verdict: 17 vs 2 in `default` among units that held `source` on
both arms; identical seconds per cell; no parse failures; basis rotation
already gated) are reported by the panel; I re-derived the headline numbers
and the E12 replication, not those subsidiary checks.

**Not preregistered, not a result.** The `ready` sensitivity was found by the
attacker after all outcomes existed. It is the strongest candidate for a
preregistered E14 and must not be claimed before one is run.

## 4. Two corrections to my own record

**The paired count test was post-hoc, and I called it predeclared.**
`git show 412ae08:e13_recognition.py` — the preregistration — contains no
paired count test, no sign test, and no "response bias" text. Protocol §3
predeclares boolean accuracy (primary) and strict/lenient count accuracy
(secondary), both per response. The paired block entered in `459fc88`:

| event | time (2026-09-01) |
|---|---|
| `412ae08` preregistration | 20:42:50 |
| `4a961cf` completeness filter — message says "before any E13 number existed" | 20:56:14 |
| `results/e13_llama32-3b_o0.csv` written (36 units, with `recog_count`) | **20:57:12** |
| `459fc88` adds the paired count test, calls it "the predeclared SECONDARY … analysed PAIRED" | **20:59:49** |
| `418bab2` reports the result: "which is why both were predeclared" | 21:32:30 |

The commit message does not say results existed. In the chunk on disk at that
moment the pattern the added text describes was already present (panel
recomputation from `o0` alone: identify boolean 0.36 on INDEP, count sign
19 vs 1). I cannot prove from the repo whether I read the file. The test was
applied only to the field it favoured. The correct label is **post-hoc**, and
the predeclared count numbers I never reported are: `identify` INDEP
count_strict **0.130**, count_lenient 0.537; `normative` INDEP count_strict
**0.083**.

Also: `4a961cf`'s "before any E13 number existed" was literally false — `run()`
prints every unit's verdicts to the terminal as it goes, and the run had been
printing for ~13 minutes. That change was conservative and had zero effect at
parse rate 1.00, but the sentence was wrong.

**"E12's frozen probe, 27 vs 0" is E10's.** The 27/36 vs 0/36 distinct-document
count is `e10_independence.py`'s manipulation check on E10's 36 discussion
texts (`results/e10_manip_check.csv`). E12 has no probe. `e13_recognition.py`,
`RESUME.md`, `novelty_matrix.md` and `418bab2` attributed it to E12. The
model's ability to report shared root **on E13's own units** is shown by the
paired primary boolean above (40 vs 0), not by E10's count.

---

## 5. What survives, stated conservatively

1. **RQ2, on the ordering verdict.** `default` is byte-identical to E12 and
   reproduces its equivalence-supported null: +0.0000, CI [−0.056, +0.056],
   discordance 0.093 inside the powered band. Unchanged.
2. **`gold`, on the ordering verdict.** Point estimate 0.0000, CI
   [−0.056, +0.065]; INCONCLUSIVE BY RULE under the preregistered band,
   equivalence-supported only on the flagged post-hoc reading. It is **not**
   an "oracle null" and the phrase is withdrawn wherever it appears.
3. **Recognition.** The model discriminates SAME from INDEPENDENT on both
   fields, paired, at p ≈ 1e-12 (`identify`), while ~40 % of units
   misrecognise INDEPENDENT by every measure. Rule 2 is unadjudicated.
4. **`identify` / `normative`** remain INCONCLUSIVE BY RULE on the ordering
   verdict. Unchanged.
5. **The `ready` field** is dependence-sensitive in every arm and in E12.
   Post-hoc; unconfirmed; the only new thing in this project worth a
   preregistration.

## 6. Consequences

- **C8 as phrased is contradicted by this project's own data** — the model
  does *not* "price them as k independent confirmations in a downstream
  executable decision". `docs/novelty_matrix.md` C8 is re-scoped to the
  ordering channel and demoted. Residue leg 1 ("recognition probe") now rests
  on the paired primary boolean, which is post-hoc; leg 3 ("oracle null") is
  withdrawn.
- **The claim memo** (`docs/CLAIM-E13.md`) is written to this section, not to
  `418bab2`.
- **No new campaign.** A preregistered confirmation of the `ready` channel
  (E14) is the recorded next step and is **not started**.
- **Refuted candidates that still earned a note** (all 17 refutations verified
  the numbers and found no conclusion affected): the verdict scorer converts a
  single-action omission into a directional `flip`/`source` (R5; every
  preregistered reading unchanged on a reorder-only reanalysis); the modal
  count answer "4" most plausibly means *total messages*, so `count_lenient`
  is a poor recognition measure (R8); `sham`'s two probes have effectively
  constant answers in these materials, so it controls output shape and length
  only (R15); `gold` is included in the Holm family (m = 4), conservatively
  and with no effect (R4); the frozen principle raised contradiction adoption
  overall, an exploratory main effect the panel computed (pooled +0.102) and
  I have **not** re-derived (R16).
