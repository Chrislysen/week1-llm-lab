# E10 — Lineage Independence — protocol v1

**PREREGISTRATION. Committed before any E10 decider call.** Git ancestry is the
evidence: this file and the full corpus, seeds, hashes, gates and verifier
extensions land in a commit containing **zero E10 results**.

---

## 1. The one question

E9 established, on one decider, that replacing irrelevant filler with two
paraphrastic restatements of a source reduces adoption of a later contradiction
(0.5278 → 0.1944, p = 1.831e-03), over and above a separately measured effect of
intervening text (0.9167 → 0.5278, p = 1.221e-04).

That result is **not novel as stated**. "Repeated/corroborated evidence
influences LLM decisions" is heavily pre-empted (see `docs/novelty_matrix.md`).

The narrower question that may still be open:

> When support statements are matched for count, wording, speaker structure,
> order, position and length, does their **evidential dependence** matter?
> Do *k* messages tracing to **one** evidential root behave differently from *k*
> **independent** roots supporting the same proposition?

**This is the load-bearing question. H3 decides the direction's fate.**

---

## 2. How evidential dependence is operationalised

The hard part is making dependence real *in the text* without a lexical
giveaway. Blatant cues ("independently verified", "a separate source confirms")
are forbidden — they would make the manipulation a keyword-detection task.

**Every support message attributes its claim to a named basis** — a document or
record, drawn from a pool shared by all domains and all arms:

```
the vendor runbook · the compliance sheet · last quarter's incident review
the platform spec  · the change-control record · the vendor support note
```

- **SAME_ROOT** — the source and both support messages cite **the same basis**.
  Three statements, one evidential root. They add no independent information;
  they are three reports of one artifact.
- **INDEPENDENT_ROOT** — the source and each support message cite a **different
  basis**. Three statements, three evidential roots that happen to agree.

**Counterbalancing is what makes this safe.** Which basis is "the repeated one"
rotates across instances, so every basis string appears in SAME_ROOT for some
instances and in INDEPENDENT_ROOT for others. Sentence templates are drawn from
one shared pool used by both arms. Therefore **no per-message unigram, bigram or
regex can separate the arms** — gate 18.

What *does* differ, necessarily, is the **within-instance repetition of basis
identity**. That is not an artefact to be scrubbed; it **is** the independent
variable. Documented here per gate 19: the only licensed semantic difference
between SAME_ROOT and INDEPENDENT_ROOT is how many distinct evidential roots the
support set traces to.

**Why this is a better operationalisation than "derived from the source".**
Attribution cues ("as the Ops Lead said") would encode dependence in speaker
reference, which is exactly the confound E9 had to clean up. Basis identity is
counterbalanceable; speaker reference is not.

---

## 3. Arms

Contradiction text is **byte-identical across every arm**. Source text is
byte-identical across every arm. Final planning prompt is byte-identical.
Speakers: `A` = source, `B`/`C` = support or filler, `D` = contradictor —
**`D` is a fresh voice in every arm**, per E9's finding that self-reversal must
not vary across conditions.

| arm | messages | tests |
|---|---|---|
| `bare` | S(A), X(D) | floor |
| `filler` | S(A), F1(B), F2(C), X(D) | H1 vs `bare` |
| `same_root` | S(A,b1), R1(B,b1), R2(C,b1), X(D) | H2 vs `filler` |
| `indep_root` | S(A,b1), R1(B,b2), R2(C,b3), X(D) | **H3 vs `same_root`** |
| `same_root_nospk` | as `same_root`, speaker labels stripped | H4 |
| `indep_root_nospk` | as `indep_root`, speaker labels stripped | H4 |
| `bare_super` | S(A,b1), U(D) | supersession floor |
| `same_root_super` | S(A,b1), R1(B,b1), R2(C,b1), U(D) | H5, hysteresis |
| `indep_root_super` | S(A,b1), R1(B,b2), R2(C,b3), U(D) | hysteresis × independence |

`X` = unsupported contradiction (reverses the ordering, no authority).
`U` = **legitimate supersession** by the authorised reviser, which *changes
ground truth*. The deterministic evaluator scores `U` arms against the
**reversed** relation via the corrected `supersession_closure` semantics. The
historically broken `supersession_respected` metric is **not** reused.

9 arms × 36 instances = **324 decider calls** per model.

---

## 4. Hypotheses — frozen

| # | hypothesis | contrast | if it fails |
|---|---|---|---|
| **H1** | intervening text alone matters | `filler` vs `bare` | E9's length effect did not replicate on a fresh corpus; report |
| **H2** | semantic corroboration beyond spacing | `same_root` vs `filler` | the effect is spacing/length only → **retire the corroboration direction** |
| **H3** | **evidential independence matters** | `indep_root` vs `same_root` | **no lineage sensitivity.** Honest conclusion: repetition/multiplicity, already pre-empted. **Kill the lineage novelty direction.** |
| **H4** | the effect is speaker-mediated | named vs `_nospk` on the C/D contrast | if no difference, describe as context/evidence multiplicity, **not** social or multi-agent source weighting |
| **H5** | legitimate update ≠ unsupported contradiction | `same_root_super` vs `same_root` | model shows evidence inertia, not authority reasoning |
| **H5b** | **hysteresis** | `same_root_super` vs `bare_super` | if prior support *reduces* acceptance of a valid update, that is a finding in its own right |

**Directional commitments are not made for H3.** Either direction is
informative: over-weighting correlated evidence (same-root ≈ independent) and
discounting it (same-root < independent) are both real answers.

### H5 is confounded by construction; H5b is not. Recorded before scoring.

`same_root_super` averages 16.89 words/message against `same_root`'s 13.89,
because a legitimate supersession sentence necessarily says more than a bare
contradiction — it names an authority and announces a change. Equalising them
would mean padding the contradiction, which would stop it being a bare
contradiction.

So **H5 confounds authority framing with tail length** and is reported as a
coarse comparison only. **H5b is the clean test**: `same_root_super` vs
`bare_super` share a byte-identical source *and* a byte-identical supersession
tail, and differ only by the presence of the two support messages. That is
exactly the hysteresis question — *does prior corroboration impair acceptance of
a valid later update?* — and it is the one the campaign brief §6 actually asks.

**Primary supersession result is H5b.** H5 is descriptive.

---

## 5. Kill rules — binding

- `same_root` ≈ `filler` → **it is spacing.** Retire the corroboration claim.
- `same_root` differs from `filler` but `indep_root` ≈ `same_root` → **generic
  repetition, not lineage.** Retire the lineage novelty direction; report as a
  replication of known corroboration effects.
- Effect vanishes speaker-free → reframe as speaker-mediated conformity.
- Survives one model only → model-specific behavioural finding.
- Legitimate supersession blocked as hard as false contradiction → frame as
  **hysteresis/inertia**, not beneficial authority tracking.
- `verify_claims.py` cannot regenerate a number → it is not reported.

---

## 6. Statistics

- **Sampling unit is the task instance.** n = 36. Deterministic repeats are not
  independent samples and are not taken.
- Primary contrasts: **exact paired McNemar**, reported with raw discordant
  counts and the absolute paired difference.
- H3 is the single primary test. H1, H2, H4, H5, H5b form a secondary family of
  5 and are **Holm-corrected**; corrected and uncorrected p are both reported.
- Non-significant results are reported, never hidden. `p > .05` is **not**
  evidence of equivalence.
- **Smallest effect of interest for H3, fixed now: 0.10 absolute difference in
  adoption.** If |Δ| < 0.10 *and* the 95% bootstrap CI over instances excludes
  effects larger than 0.10 in both directions, H3 is reported as
  **equivalence-supported null**, not merely "not significant".

---

## 7. Manipulation check — preregistered, non-decision

H3 failing is ambiguous between *"the model cannot see basis identity"* and
*"the model sees it but does not use it evidentially"*. A separate,
non-decision probe resolves this: the model is shown the same context and asked
**how many distinct documents/records were cited**, answering with a bare
integer.

- If it reports the count accurately and H3 still fails → it perceives
  dependence and does not weight it. **That is the interesting negative.**
- If it cannot report the count → the manipulation was not perceptible and H3 is
  uninformative about evidential reasoning.

This probe never contributes to any decision metric.

---

## 8. Corpus

New corpus, new hash, **historical corpora untouched**. Reuses the frozen formal
machinery of `lineage_bench.py`: 6 domains × 6 constraint graphs, ~6 actions,
6–8 constraints, deterministic evaluator.

**Stated limitation, not discovered later:** the 36 *formal* instances are the
same instances E9 used. Message text, lineage schedule, speakers, basis
attributions and arms are entirely new, but H1 and H2 are therefore **not
instance-independent replications** of E9. H3, H4, H5 are new questions on which
no data exists, so instance reuse does not threaten them. Fixing this would
require a second formal generator and is out of scope for v1.

Mode A only (deterministic template text). Mode B is built **only if H3
survives**, per §12 of the campaign brief.

---

## 9. Gates that must pass before any decider call

All 20 campaign gates, implemented in `test_lineage_e10.py`. The E10-specific
ones:

1. known-good plan passes; known-bad fails the intended constraint; empty plan
   fails; echo-the-prompt-order fails
2. source-only heuristic **fails** the legitimate-supersession arms
3. latest-message heuristic **fails** the unsupported-contradiction arms
4. no formal label (`SOURCE`, `SAME_ROOT`, constraint ids, action ids) leaks
   into any rendered message
5. corpus reproduces bit-identically from seed; hash written before scoring
6. arm registry count asserted (9) — deleting an arm is a test failure
7. same-root arms cite exactly 1 distinct basis; independent-root arms cite
   exactly 3
8. `same_root` and `indep_root` differ **only** in basis tokens: identical
   message count, speaker sequence, contradictor, source text, contradiction
   text, and template skeletons
9. contradiction text hash identical across all contradiction arms; final prompt
   hash identical across all arms
10. no per-message unigram or bigram separates `same_root` from `indep_root`
11. basis strings are counterbalanced: each appears in both arms across the
    corpus
12. word-length distributions of the two arms match within 1.0 word/message
13. every planned primary metric is recomputable by `verify_claims.py` from raw
    output

**If any gate fails, E10 does not run.** Fix, version, regenerate, rehash,
recommit.

---

## 10. Execution order

1. Gates green, corpus hashed, this document committed with zero results.
2. Mode A, `llama3.2:3b`, all 9 arms, 36 instances.
3. Analyse immediately. **If H3 fails → stop lineage work, write the narrow
   result memo.**
4. If H3 survives → replicate the principal contrast across ≥3 distinct model
   families (Llama, Qwen, Gemma/Aya — qwen2.5 at three scales is **one** family).
5. Then Mode B, then supersession extension, then adversarial novelty audit.
