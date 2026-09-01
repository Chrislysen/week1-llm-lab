# E15-PODT — Provenance-Only Dependence Test — CANDIDATE ONLY

**Status: APPARENTLY OPEN FROM ONE DEEP-RESEARCH REVIEW.**
**NOT PREREGISTERED. NOT AUTHORIZED. ZERO E15 MODEL CALLS. NOT NOVEL.**

This file records a proposal and nothing else. It contains no corpus, no
code, no design decisions, no results. An independent review (Gemini) is
adversarially searching the literature for the paper that already answers
the question; **that review may kill this candidate without a model call**,
and if it does, this file stays as the record of a direction that was
considered and closed. If the review concludes the question remains open,
both reviews will be used to design a preregistered experiment. If it finds
a stronger direction, E15 is not started.

## The question

> When evidence text, order, speakers and reliability are held fixed, can
> an LLM use trusted metadata describing evidential dependence to make a
> normatively correct decision?

## Motivation, from this repository's own evidence

- E12 (108 units, 36 clusters) and E13 `default` (byte-identical
  replication) established that `llama3.2:3b`'s substantive decision is
  indifferent to dependence **inferred from citation structure**: whether
  two corroborations cite one document or two changes the action ordering
  by +0.0185 (CI [−0.037, +0.074]) and +0.0000 (CI [−0.056, +0.056]),
  inside a preregistered SESOI of 0.10. GroupQA (arXiv:2601.06189) reports
  the same manipulation on four 8B–70B models with the paraphrases weighted
  *more*.
- E13 shows the same model can partly *report* that structure when asked
  (paired primary boolean 40 vs 0; about 40 % of units misreport the
  independent case by every measure).
- PODT asks a different question from both: not "does the model infer
  dependence from the text" but "given dependence as **trusted metadata**,
  with everything else fixed, does the decision move the normative way".

## Existing evidence in this repository that bears on it — read before designing anything

- **E13 `gold` is the closest in-repo precedent and it is discouraging.**
  `gold` appended a provenance-only sentence to the discussion, in plain
  language and without benchmark vocabulary: *"For reference: the supporting
  reports above all draw on the same single underlying record"* /
  *"… each draw on a different underlying record."* On `llama3.2:3b` the
  ordering difference was **0.0000** (CI [−0.056, +0.065]), INCONCLUSIVE BY
  RULE under the preregistered discordance band, and `gold` versus `default`
  pooled was −0.037 (cluster p 0.07). One 3B decider, one phrasing, one
  placement; not a test of PODT, but any PODT design must be powered against
  the possibility that told dependence does nothing on small deciders.
- **The readiness channel is not a usable outcome** (matrix C9–C10): it is
  at ceiling in three of five local deciders and a repetition readout in
  llama.
- **Model-specific prompt effects are real here** (E13-X): the structured
  "state the structure first" request cut contradiction adoption by 0.17 in
  Qwen-7B and did nothing in llama or Aya. A PODT result on one decider is a
  result about one decider.

## Closest blockers, for the external review to test

| work | what to check |
|---|---|
| GroupQA, arXiv:2601.06189 | any condition where provenance is *stated* rather than inferred from paraphrase structure; any normative-correctness scoring |
| CAMA, arXiv:2608.19701 | the earlier pass found no baseline in which the LLM is *told* memories are correlated; confirm on the full paper and appendices, and check whether N_eff or provenance priors are ever exposed to the base model as input |
| Information Discernment / L2D, arXiv:2607.19355 | metadata given is source *reliability*; check whether any variant supplies *dependence* or *shared-origin* metadata |
| TMA-NM, arXiv:2606.24322 | provenance/origin labels are enforced by the system; check whether any experiment gives the model the labels and measures its own use of them |
| MemLineage, arXiv:2605.14421 | derivation DAG is machine-enforced; same question — is the DAG ever handed to the model as input |
| attribution / provenance-metadata work | Source-Aware Training (arXiv:2404.01019); Trusted Source Alignment (arXiv:2311.06697); MAP-Graph (arXiv:2608.10509 — provenance fields incl. poisoned/revoked given to a 7B model with deterministic scoring); credibility-aware generation; Manufactured Confidence (arXiv:2606.29279 — attribution framings "all grant alike"); Whose Facts Win? (arXiv:2601.03746 — source metadata × repetition). Check whether any supplies *derivation* (this restates that) rather than *authorship* or *credibility*, holds text fixed, and scores a normatively correct decision |
| Bayesian-testimony and "told independence" work | Pilditch, Hahn & Lagnado 2020/2025 (humans); any LLM replication of the Connor Desai 2022 "independence made transparent" manipulation |

## Why the distinction might remain

None of the works above appears to (a) hand a base model **trusted
dependence metadata** — that report B restates report A — while (b) holding
text, order, speakers and reliability fixed, and (c) scoring whether the
downstream decision moves in the normatively correct direction. CAMA and
MemLineage engineer the use of provenance instead of measuring the model's
own use of it; L2D and Whose Facts Win supply reliability and authorship,
not derivation; MAP-Graph is the nearest on metadata-as-input but scores
allow/block/redact policy, not evidential weighting. **That is the whole
case, and it is a case of absence of a located paper, which is exactly what
the matrix's rule says is not novelty.**

## What this file is not

No hypothesis is frozen. No endpoint, unit, SESOI, decider, power condition,
exclusion or kill rule is proposed. No corpus exists. No call has been made.
Nothing here may be cited as a finding.
