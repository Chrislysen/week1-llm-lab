# Novelty matrix

**Rule of this file: `APPARENTLY OPEN` is never promoted to `NOVEL` because a
search found nothing.** Absence of a hit is absence of evidence. Promotion
requires an adversarial search that actively tried to find the killing paper and
failed, plus a written comparison against the closest work found.

**Current blocker (B1).** The session that produced E7–E11 exhausted its
web-search budget (200/200) before any adversarial prior-art pass could run. So
every row below whose status depends on literature is `UNKNOWN`, not `OPEN`.
This project's own base rate is that **four of five** candidate research
questions came back fully pre-empted.

Adversarial queries to run when search is available — searching for what would
**kill** each claim, never for support:

```
same-source vs independent-source evidence LLM
correlated evidence LLM belief revision
duplicate dependent evidence language models
source independence LLM corroboration
pseudo-corroboration agents
paraphrase multiplicity evidence weighting LLM
independent evidence vs repeated assertion LLM
evidence double counting language models
belief revision source correlation LLM
corroboration hysteresis LLM
repetition blocks legitimate correction LLM
LLM Bayesian source dependence
```

---

## Claims and their status

| # | candidate claim | closest known work | overlap | remaining distinction | status |
|---|---|---|---|---|---|
| C1 | Repeated/corroborated evidence reduces adoption of a later contradiction | corroboration count in knowledge conflict (Xie et al. ICLR 2024, arXiv:2305.13300; Jin et al. COLING 2024, arXiv:2402.14409); repetition / illusory truth (arXiv:2601.03746) | **near-total** | measured on a downstream *plan* rather than a stated belief; paraphrastic rather than verbatim | **PREEMPTED** |
| C2 | Intervening text alone (dilution) reduces adoption | — | — | — | **INVALID — does not replicate.** Large in E9 (p=1.2e-04), moderate in E10 (p=7.8e-03), **absent in E11** at all three k. Withdrawn. |
| C3 | Same-source memories can manufacture a false evidential majority | CAMA / Beyond Memory Majority (arXiv:2608.19701); TMA-NM / manufactured corroboration (arXiv:2606.24322); MemLineage (arXiv:2605.14421) | **heavy** — the campaign brief lists this phenomenon as already unsafe to claim | ours is a *decision-level* measurement on a formal planning task with a deterministic evaluator | **HEAVY OVERLAP** |
| C4 | ~~The dependence discount is exactly zero~~ **RETRACTED, see `docs/protocols/E10-H3-RETRACTION.md`.** What remains: the independence effect is *bounded* at 0.111 and is far smaller than the corroboration effect measured in the same instrument (18–19/36 discordant vs at most 3/36). The model does distinguish 1 root from 3 at p = 1.5e-08. | as C3, plus source bias (Dai et al. KDD 2024, arXiv:2310.20501) | unknown — the *perception/use dissociation* was not found in earlier scans, but earlier scans did not look for it | a **bounded** effect plus a manipulation check, not a phenomenon claim. The bound (≤0.111) and the relative-sensitivity comparison are what is defensible; "no discount" is not | **UNKNOWN, and weakened by the retraction** |
| C5 | Prior corroboration does **not** create hysteresis against a legitimate authoritative update | stale/superseded memory work — MemStrata (arXiv:2606.26511), STALE (arXiv:2605.06527), Memora (arXiv:2604.20006) | moderate | a *null* on an explicit, easy supersession, at ceiling (36/36 both arms) | **UNKNOWN, and weak** — ceiling effect; tests only an easy update |
| C6 | Removing speaker labels reverses the independent-root advantage (exploratory) | speaker-free / paraphrastic conformity (arXiv:2607.05545) | unknown | not predeclared; a mundane account (lexical diversity → recency fallback) is not excluded | **UNKNOWN — exploratory, not claimed** |
| C7 | AnchorRoute / lineage-aware routing | RCR-Router (arXiv:2508.04903); governed shared memory (arXiv:2606.24535) | high | — | **DEAD.** Killed on measurement in E6 (embeddings are blind to order inversion). E10/E11 do NOT add a second kill -- they are inconclusive on whether the decider uses dependence -- but they supply no demonstrated effect for a router to exploit either. |

---

## What the experiments actually licence

**Retired.** C1 as a novelty claim (pre-empted). C2 (does not replicate). C7
(killed on measurement in E6).

**The only rows worth a literature pass are C4 and C5**, and both are *negative*
results. C4 was the strongest thing this project had until an adversarial panel
showed the conclusion exceeded its own preregistered decision procedure
(`docs/protocols/E10-H3-RETRACTION.md`). What is left of it — a bound of 0.111
and a relative-sensitivity comparison — is much weaker, and still needs the
search before any claim is made.

**Method work is not authorised.** The §13 gate requires a DEMONSTRATED
dependence-related effect the decider uses. E10/E11 do not demonstrate one, and
after the retraction they do not demonstrate its absence either. Building
witness-preserving routing now would be building a method for a problem that has
not been shown to exist.

---

## E13 candidate claim, and the two papers closest to killing it

**C8 — RECOGNITION–UTILIZATION DISSOCIATION FOR EVIDENTIAL DEPENDENCE.**
A model that *correctly reports* that k corroborating messages share one
evidential root nevertheless prices them as k independent confirmations in a
downstream executable decision; and this can be moved (or not) by routing the
recognised structure into the reasoning step.

Status: **UNKNOWN — and it must stay unknown until the two boundary questions
below are answered against the actual papers.** This is not a generic
"models know but don't use" claim; that framing is already crowded. The only
defensible scoping is the conjunction:

> evidential **dependence** (not reliability, not credibility, not repetition)
> **+** a direct recognition probe **+** a downstream *executable* decision
> **+** a within-instance causal intervention.

| # | closest work | the question that decides whether C8 survives | status |
|---|---|---|---|
| B-CAMA | CAMA / Memory Correlation Bias, arXiv:2608.19701 | **Does CAMA show a base LLM correctly RECOGNISING shared-source dependence and still failing to price it?** CAMA models correlated vs independent memories and builds a mitigation. If it already reports the recognition/behaviour gap in a base model, C8 is pre-empted outright. If it only shows the *behavioural* bias and fixes it architecturally, the recognition probe and the intervention ladder are the remaining distinction. | **UNRESOLVED — blocking** |
| B-L2D | Information Discernment in LLMs, arXiv:2607.19355 | **Does its M1/M2 decomposition cover source DEPENDENCE, or only source RELIABILITY?** M1/M2 separates failing to *estimate* source quality from failing to *apply* it — structurally the same shape as C8. If "apply" already covers independence/dependence, C8 collapses into it. If M1/M2 is strictly about reliability/trustworthiness of individual sources, then independence structure is a different quantity. | **UNRESOLVED — blocking** |
| B-WFW | Whose Facts Win?, arXiv:2601.03746 | Does it manipulate evidential *independence*, or only credibility and repetition count? | UNRESOLVED |
| B-CONF | Most LLM Conformity Needs No Speaker, arXiv:2607.05545 | Does it probe knowledge/use of source dependence, or only speaker-free conformity magnitude? | UNRESOLVED |
| B-HUMAN | Illusion of consensus — Yousif et al. 2019; Connor Desai et al. 2022/2026 | Humans become *more* independence-sensitive when causal source relations are made transparent. Does explicit transparency similarly rescue LLM action selection? | **EXPLORATORY ONLY** — the human/LLM contrast is not preregistered as a test and may not be reported as one |

**Rule for C8, fixed now:** if either B-CAMA or B-L2D answers "yes, already
shown", C8 is **PREEMPTED** and E13 becomes an internal replication with no
novelty claim. Neither question can be answered from this session — the
adversarial search budget is exhausted (B1) — so **C8 cannot be promoted above
UNKNOWN no matter how clean E13's result is.**
