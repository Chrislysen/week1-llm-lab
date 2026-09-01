# Research roadmap — Authority Drift in multi-agent context

**Nothing in this document is implemented.** It records a long-term target so
that later work has a stated direction, and so that novelty claims can be
checked against prior art rather than assumed. The frozen compulsory baseline
(`compulsory-baseline-v1`) is untouched and stays that way.

---

## Research question

> When task evidence is repeatedly re-expressed by LLM agents, can
> self-generated derivatives become more retrieval-salient and
> decision-influential than their authoritative sources, and can
> evidence-lineage-aware context routing recover this failure under fixed
> context budgets?

## Why this question, and not a nicer one

It is the question the measurements already point at, rather than one chosen in
advance and then argued for.

The offline selector preflight (21 saved real transcripts, corrected protocol,
no model calls) found that **every** scorer ranks the agents' own restatements
above the authoritative originals those restatements came from:

| selector | mean rank of source msgs | mean rank of generated msgs | gap |
|---|---|---|---|
| bm25 | 10.20 | 6.16 | **+4.04** |
| fusion | 9.48 | 6.75 | **+2.72** |
| dense | 8.43 | 7.51 | **+0.92** |

and that **no selector reaches the chance level of 0.336**:

| | retrieval recall | vs chance |
|---|---|---|
| recency | 0.0667 | −0.27 |
| bm25 | 0.1048 | −0.23 |
| fusion | 0.2762 | −0.06 |
| dense | 0.3333 | −0.003 (at chance) |
| oracle | 1.0000 | — |

**Read that table honestly: it is a null.** Not one selector beats random, and
the best of them merely matches it. An earlier version of this paragraph
concluded "relevance and authority have come apart, and relevance is winning —
that is the phenomenon", which converted a no-better-than-chance result into a
positive claim. That was wrong and is retracted.

What the table supports is narrower and still worth pursuing: relevance-based
selection carries **no measurable advantage over random selection** at
recovering task-critical source information here, and two selectors are
significantly *worse* than random — which is not what a relevance retriever is
supposed to do. Whether that reflects an authority/relevance dissociation or
something duller is exactly what the benchmark below has to establish. It is a
motivating anomaly, not a finding.

**Two E1 results that cut against this programme, recorded because leaving them
out would be selection.** On the task side, E1's `random` arm had the *highest*
mean constraint recall of any arm (0.8095, against bm25 0.619, dense 0.7619,
fusion 0.7619, recency 0.5714) — so the retrieval-side story is not mirrored by
a task-side story. And stage-2 H1 predicted relevance-based selection would beat
recency on retrieval recall; on the E1 numbers it does not, for BM25. The
project applies pre-registration discipline to stage 1 (see research-design.md
§2, where the unsupported H2 is left standing); it must apply the same discipline
here.

---

## Stages

Sequential. Each exists only if the previous one produced a result that
motivates it. None is started.

| # | stage | question it answers |
|---|---|---|
| 1 | **Retrieval landscape** | How does the source-vs-derivative ranking gap behave across budgets, query definitions and relay depths? |
| 2 | **Multi-instance benchmark** | Does the effect survive across structurally matched but lexically distinct incidents, or is it an artefact of one scenario? |
| 3 | **Information-lineage metrics** | Can "this message is a derivative of that one" be measured deterministically, without an LLM judge in the loop? |
| 4 | **Causal corruption** | If a derivative distorts its source, does the distortion propagate into the decision — and is the damage attributable? |
| 5 | **Relay depth** | How does the effect scale with the number of re-expressions between source and decision? |
| 6 | **Evidence-lineage router** | Does routing on lineage rather than similarity recover the loss under the same fixed budget? |
| 7 | **Hostile ablations** | Which parts of the effect survive adversarial attempts to remove it — including a random control and a sabotage arm at every stage? |
| 8 | **Cross-model generalization** | Does it hold beyond `llama3.2:3b`, or is it a small-model artefact? |
| 9 | **Independent claim verification** | Every reported number re-derived from raw artifacts by a checker that exits non-zero on drift. |
| 10 | **Generation-mode validity (Mode B)** | Does the stage-5 effect survive when a *model* writes every relay instead of four templates — or is it a fact about the templates? |

Gate discipline carries over from the compulsory: no stage begins until the
previous one has a result that justifies it, and a stage that returns a null
gets written up as a null.

---

## Non-novelty boundaries — READ BEFORE CLAIMING ANYTHING

These areas have established prior art. Nothing here is claimed as novel, and
any future claim must be positioned against them explicitly rather than around
them.

| already covered | implication |
|---|---|
| **Generic provenance / data lineage** | Tracking where a piece of information came from is a solved and well-published problem in databases, workflow systems and RAG attribution. "We track provenance" is not a contribution. |
| **Generic contradiction handling** | Detecting and resolving conflicting statements in dialogue and in retrieved evidence has extensive prior work in NLI, fact verification and belief revision. |
| **Role-aware / role-conditioned routing** | Routing different context to different agents by role is published — RCR-Router (arXiv:2508.04903) does role-aware routing of non-redundant memory under a strict system-level token budget. |
| **Source reliability / trust weighting** | Weighting evidence by source trustworthiness is long-established in information fusion, multi-source QA and credibility modelling. |
| **Generic multi-hop semantic drift** | Meaning degrading across successive paraphrase or summarisation hops is a known phenomenon with its own literature. |
| **Stale / superseded memory** | Already saturated — MemStrata (arXiv:2606.26511) quantifies stale-serve rates, STALE (arXiv:2605.06527) benchmarks it with a taxonomy, Memora (arXiv:2604.20006) contributes the FAMA metric. |
| **Relevance ≠ utility** | Has a survey (arXiv:2604.08920), a benchmark (UsefulBench), and a counterfactual retrieval-vs-utilisation diagnosis in multi-turn dialogue agent memory (arXiv:2603.02473). |

**Current status of every novelty claim: NONE MADE.** The literature scan for
this project already found four of five candidate research questions fully
pre-empted. The prior assumption should be that any given framing is covered,
until a real search says otherwise.

---

## Prior-art scan on Authority Drift itself (2026-09-01)

The assumption held again. **Two of the four claims are already published, and
one of them under a name this project had never searched for.**

| claim | status | owned by |
|---|---|---|
| Retrievers rank agent restatements above their sources | PARTIALLY_NOVEL | **source bias** — Dai et al., *Neural Retrievers are Biased Towards LLM-Generated Content*, KDD 2024, arXiv:2310.20501 |
| Decision follows a conflicting derived restatement over the source | **ALREADY_KNOWN** | Tan et al., *Blinded by Generated Contexts*, ACL 2024, arXiv:2401.11911 |
| A lineage-labelled benchmark separating retrieval from utilisation failure | **PLAUSIBLY_NOVEL** | composite; gap named by arXiv:2606.04990 |
| Self-generated content is more retrieval-salient than source content | **ALREADY_KNOWN** | Dai et al. 2024; Chen et al., *Spiral of Silence*, ACL 2024, arXiv:2404.10496 |

**The single most damaging paper is Tan et al. (arXiv:2401.11911).** It pairs a
generated context against a retrieved one where only one is correct, and finds
models follow the generated context *even when it is wrong*, with the
similarity-to-query mechanism already diagnosed. That is our decision authority
inversion minus the derivation relation. Our measured 0.4545 is therefore best
described as a **replication of a 2024 result on a new substrate**, not a
discovery.

Also close and very recent: MemIR, *Mitigating Provenance-Role Collapse in
Long-Term Agents* (arXiv:2605.25869), which already names the source-monitoring
failure in agent memory; and arXiv:2603.02473, which already performs the
retrieval-vs-utilisation factorisation, though on write-strategies rather than
lineage.

### What survives, in order of defensibility

1. **Legitimate supersession.** Every conflict benchmark found treats the
   authoritative source as the answer key. A design in which a later derived
   message *should sometimes win* — making "always trust the source" a failing
   strategy — was not found anywhere. This is the one element to build a
   contribution around.
2. **Parent–child rank inversion as the unit of measurement.** Source bias
   compares *populations* of texts; nothing found compares a specific
   restatement to its own specific parent, or treats derivation-chain depth as
   an independent variable.
3. **Retrieval/utilisation factorisation applied to lineage** rather than to
   memory write-format.

### E4b, and why it is NOT a novel claim (2026-09-01)

A candidate emerged with real statistical support and was then retired by its own
control. Recorded in full because a retired candidate is the cheapest thing this
project can hand the next person.

**The finding.** Varying ONE system-prompt sentence, ground truth unchanged:
adding *"only the Duty Manager may revise an agreed procedure"* raised
revision-following in **5/5 models** (mean +0.127, sign test one-sided
p = 0.031), while resistance to the *unauthorised* revision rose only +0.047.
`restrict` beat `permit`, which explicitly allows what `restrict` limits.
`prohibit` never fell below `none`.

**Why it is not novel.** The general effect is published several times over:

| | |
|---|---|
| arXiv:2601.08070 "Semantic Gravity Wells" | Runs the exact restricted-mention vs no-mention contrast on **qwen2.5-7b-instruct** — one of these five models — and finds the restriction raises the restricted output above baseline in 87.5% of violations |
| arXiv:2605.28639 "Attentional White Bear Effect" | Suppression vs concept-absent baseline; mention raises salience regardless of polarity |
| arXiv:2511.12381 (NeurIPS 2025) | ReboundBench: above-baseline ironic rebound, systematically |
| arXiv:2601.21433 "When Prohibitions Become Permissions" | Small open models endorse actions **more** under prohibition framing; 16 models, 3B–14B |
| arXiv:2608.12321 | Owns the second half: prompted mention shifts behaviour **globally, not conditionally** |
| arXiv:2607.05545 | A **60–80% speaker-free revision floor** — most conformity needs no speaker |

**And the control killed the residual.** Re-running with every turn attributed
to a generic "Engineer" — no Duty Manager, nothing for the rule to bind to:

    model                 attributed   anonymous   change
    llama3.2:3b               +0.083      +0.083   +0.000
    qwen2.5:14b-instruct      +0.167      +0.111   -0.056
    qwen2.5:7b-instruct       +0.194      -0.028   -0.222
    positive deltas          3/3          2/3
    mean delta             +0.1481      +0.0556

Unanimity is lost and the mean drops by 62%. The effect is not *purely* generic
priming, but at n=3 with a sign flip it does not establish an authority-specific
mechanism either. The surviving portion is consistent with the published
white-bear effect.

**Status: NOT NOVEL. Do not write this up as a finding.** The honest sentence is
"we replicate the ironic-rebound effect for agent-scoped authority restrictions
in an operational planning task, and a speaker-free control shows most of it does
not require an authority to be named."

### E5, and the null I over-read (2026-09-01)

Seventh candidate, seventh pre-emption — and this one also caught me committing
the error this project criticises elsewhere.

**The finding.** Adoption of an identical contradiction: d1 0.750, d2 0.417,
d3 0.444, d1_padded 0.694, control 0.000. Paired McNemar: d1→d2 p = 0.0005;
d1→d1_padded (length only) p = 0.6250; d1_padded→d2 p = 0.0020.

**Every component is published.**

| component | owned by |
|---|---|
| Corroboration count governs conflict outcomes | Xie et al., ICLR 2024, arXiv:2305.13300 — "predisposition towards answers corroborated by a larger volume of documents"; Jin et al., COLING 2024, arXiv:2402.14409 — "majority rule … evidence that appears more frequently" |
| Corroboration confers resistance to a contradicting bloc | arXiv:2608.11247 reports the Asch dissenter/partner effect in LLMs **by name** |
| A lone ally strengthens the held position | arXiv:2607.21558 Study 3 |
| Saturation after roughly one piece of evidence | arXiv:2601.06189 — flip threshold X_min = 1.27–1.52 documents; arXiv:2510.02657 — first document +16–20%, second +2.8–4.4% |
| Distance / context length does not drive the bias | AMEL, arXiv:2605.22714 — 12 models, 84k calls, OLS slope p = 0.80 |
| Repetition survives paraphrase and survives removing the speaker | arXiv:2607.05545 |

My d1/d2/d3 arms are literally 1:1, 2:1 and 3:1 evidence-frequency contrasts.
The 0.750 → 0.417 drop is the textbook prediction of that literature.

**Two statistics I over-read, and the correction.**

1. **The "step function" is a null with no power.** d2 vs d3 is *4–5 discordant
   pairs, p = 1.000, n = 36, one model*. That is a **failure to reject**, not a
   demonstrated plateau. Describing it as "the second corroboration adds
   nothing" treats absence of evidence as evidence of absence — exactly the move
   this project retracted in §3b and in the vacuous-metric retraction.
   **Retracted.**
2. **"Length does nothing" is an underpowered rediscovery.** d1 vs d1_padded is
   p = 0.6250 at n = 36. AMEL establishes the same thing at 12 models and 84k
   calls. Reporting mine as a finding would be claiming a result someone else
   has 2000× the power for.

**An unbroken confound.** Every corroboration in E5 comes from a *different
speaker*, so corroboration-count and speaker-count are perfectly confounded.
arXiv:2607.05545 shows the effect survives removing the speaker entirely — the
repeated proposition does the work, not the independent voice. A
same-speaker-restates arm was never run, so "independent corroboration" is not
supported by this design.

**Status: NOT NOVEL.** The honest sentence is "we replicate the known
corroboration-count effect on conflict adoption in a dialogue-ordered planning
task, with a length-matched filler control."

### Framings now explicitly forbidden

- "We discover that models prefer self-generated content" — Dai et al. 2024.
- "We discover that retrievers favour model-generated text" — same.
- "We discover that decisions follow generated over retrieved context" —
  Tan et al. 2024.
- Citing the model-collapse / self-consuming-loop literature as the nearest
  prior work. It is training-time distributional degradation, not retrieval
  salience, and reaching for it would be citing the easier baseline.

What the project currently has that is *not* obviously in the literature is an
**instrument**, not a finding: a two-role natural-language dialogue with planted
constraints, a deterministic non-LLM evaluator, and a fixed-budget context
comparison. That is a resource contribution. Claiming more requires stage 2 at
minimum, and a real prior-art search at stage 3.

---

## Standing rules

- The compulsory baseline is frozen. No stage may modify it.
- Protocol changes are amendments: documented, dated, justified by something
  found *before* scoring, and applied uniformly to every arm.
- No method, weight, prompt or budget is tuned on scored outcomes.
- Every stage carries a random control and a sabotage arm.
- A control that cannot fail is not a control.
