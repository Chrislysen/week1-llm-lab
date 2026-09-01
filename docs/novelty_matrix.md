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
| C4 | **The dependence discount is exactly zero, and it is not a perception failure**: the model distinguishes 1 evidential root from 3 at p = 1.5e-08 yet prices that distinction at ~0.00–0.06 in the decision, across k = 1, 2, 3, with a demonstrated working dose-response | as C3, plus source bias (Dai et al. KDD 2024, arXiv:2310.20501) | unknown — the *perception/use dissociation* was not found in earlier scans, but earlier scans did not look for it | a **quantified null with a manipulation check**, not a phenomenon claim: prior work shows correlated evidence misleads; this measures *how much* discount is applied (none) and shows it is not because the model cannot see the correlation | **UNKNOWN** |
| C5 | Prior corroboration does **not** create hysteresis against a legitimate authoritative update | stale/superseded memory work — MemStrata (arXiv:2606.26511), STALE (arXiv:2605.06527), Memora (arXiv:2604.20006) | moderate | a *null* on an explicit, easy supersession, at ceiling (36/36 both arms) | **UNKNOWN, and weak** — ceiling effect; tests only an easy update |
| C6 | Removing speaker labels reverses the independent-root advantage (exploratory) | speaker-free / paraphrastic conformity (arXiv:2607.05545) | unknown | not predeclared; a mundane account (lexical diversity → recency fallback) is not excluded | **UNKNOWN — exploratory, not claimed** |
| C7 | AnchorRoute / lineage-aware routing | RCR-Router (arXiv:2508.04903); governed shared memory (arXiv:2606.24535) | high | — | **DEAD.** Killed twice: embeddings are blind to order inversion (E6), and E10/E11 show the decider does not use dependence, so a router cannot exploit it. |

---

## What the experiments actually licence

**Retired.** C1 as a novelty claim (pre-empted). C2 (does not replicate). C7
(killed on measurement, then killed again by E10/E11).

**The only rows worth a literature pass are C4 and C5**, and both are *negative*
results. C4 is the strongest thing this project has, and it is a null with a
manipulation check — which is precisely why it needs the adversarial search
before any claim is made. A quantified "the discount is zero" is easy to
scoop with a paper that already reported "LLMs double-count correlated
evidence."

**Method work is not authorised.** The §13 gate requires a dependence-related
effect the decider actually uses. E10 and E11 show it does not. Building
witness-preserving routing on top of a null would be building a method for a
problem the model does not have.
