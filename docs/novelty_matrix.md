# Novelty matrix

**Rule of this file: `APPARENTLY OPEN` is never promoted to `NOVEL` because a
search found nothing.** Absence of a hit is absence of evidence. Promotion
requires an adversarial search that actively tried to find the killing paper and
failed, plus a written comparison against the closest work found.

**Blocker B1 — discharged 2026-09-01.** The sessions that produced E7–E13
exhausted their web-search budgets (200/200) before any adversarial prior-art
pass could run, so every literature-dependent row sat at `UNKNOWN`. A fresh
session ran the pass on 2026-09-01: 19 adversarial searches, 15 papers read
against the questions below (full text where arXiv HTML existed, abstract
otherwise). The per-paper verdicts are in the **search log at the end of this
file**. This project's own base rate is that **four of five** candidate
research questions came back fully pre-empted; the fifth (C8) came back
pre-empted in every component and open only on the conjunction.

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
| C4 | ~~The dependence discount is exactly zero~~ **RETRACTED, see `docs/protocols/E10-H3-RETRACTION.md`.** What remains: the independence effect is *bounded* at 0.111 and is far smaller than the corroboration effect measured in the same instrument (18–19/36 discordant vs at most 3/36). The model does distinguish 1 root from 3 at p = 1.5e-08. | as C3, plus source bias (Dai et al. KDD 2024, arXiv:2310.20501); **GroupQA (arXiv:2601.06189, Jan 2026)** contrasts "rephrased variations of a single supporting document" with "unique, distinct supporting documents" and finds the paraphrases weighted *more* on 4 models (Table 4) | **heavy** — GroupQA §4.4 is E12's manipulation, on larger models, with the anti-normative direction detected | E12 adds clustering, a preregistered SESOI and an equivalence reading; GroupQA has none of those, but it has the phenomenon. E12/E13 are an internal refinement of a published result | **PRE-EMPTED (behavioural), 2026-09-01; and re-scoped to the ordering verdict the same day** — the `ready` field is not indifferent (`docs/protocols/E13-CORRECTIONS.md` §3) |
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
search before any claim is made. **Update 2026-09-01: the
search ran. C4's behavioural content is pre-empted by GroupQA
(arXiv:2601.06189); what survives of it is folded into the C8 residue below.**

**Method work is not authorised.** The §13 gate requires a DEMONSTRATED
dependence-related effect the decider uses. E10/E11 do not demonstrate one, and
after the retraction they do not demonstrate its absence either. Building
witness-preserving routing now would be building a method for a problem that has
not been shown to exist.

---

## E13 candidate claim — the search ran on 2026-09-01

**C8 — RECOGNITION–UTILIZATION DISSOCIATION FOR EVIDENTIAL DEPENDENCE.**
A model that *correctly reports* that k corroborating messages share one
evidential root nevertheless prices them as k independent confirmations in a
downstream executable decision; and this can be moved (or not) by routing the
recognised structure into the reasoning step.

**Status: WITHDRAWN AS PHRASED (2026-09-01, step-10 attack). The
ordering-channel remainder is OPEN (NARROW) and not NOVEL.** The claim text
says the model prices dependent reports "as k independent confirmations in a
downstream executable decision". On this project's own data that is false for
the decision's `ready` field, which moves ~+0.2 with dependence in every arm
(`docs/protocols/E13-CORRECTIONS.md` §3); it holds for the ordering verdict
only. On prior art, the fixed rule below fired neither way:
B-CAMA and B-L2D both answer "no", so C8 is not PREEMPTED — but the same search
found a paper (B-GQA) that already runs E12's manipulation and finds the
behaviour, and a genre of papers that already own the "decodable but unused"
template. What is left is the residue defined after the table.

The only defensible scoping remains the conjunction:

> evidential **dependence** (not reliability, not credibility, not repetition)
> **+** a direct recognition probe **+** a downstream *executable* decision
> **+** a within-instance causal intervention.

| # | closest work | the question that decided it | answer, from the paper | status |
|---|---|---|---|---|
| B-CAMA | CAMA / Beyond Memory Majority, arXiv:2608.19701 | Does CAMA show a *base* LLM correctly RECOGNISING shared-source dependence and still failing to price it? | **No.** Full text: there is no probe asking a plain LLM whether memories share an upstream source; no baseline where the LLM is *told* memories are correlated; no statement of a recognition/behaviour gap; the neural dependency-inference module's own accuracy is not reported. Baselines are systems (Vanilla RAG, Majority Voting, HippoRAG, Mem0, MAD, MADAM-RAG); tasks are memory-arbitration QA (MemoryAgentBench, LongMemEval, LoCoMo); models DeepSeek-V4-Flash and Qwen3.6-27B. CAMA asserts the behavioural bias and fixes it architecturally. | **DOES NOT PRE-EMPT** |
| B-L2D | Information Discernment / Learn2Discern, arXiv:2607.19355 | Does M1/M2 cover source DEPENDENCE or only RELIABILITY? | **Reliability only.** §9: *"models mis-estimate source reliability (M1), or models fail to apply their reliability estimates when updating (M2)."* Each trial is one source (132 news domains, popularity via Open PageRank × reliability); nothing on independence, redundancy or double counting. **But the template is theirs**: elicit the property first (Appendix F.5, `RELIABILITY_SCORE`), then test whether the update uses it — structurally E13's `identify` arm — and their "Reliability" prompt *improved* source discernment. | **DOES NOT PRE-EMPT the quantity; PRE-EMPTS the template** |
| B-WFW | Whose Facts Win?, arXiv:2601.03746 (ACL 2026) | Independence manipulated, or only credibility and repetition? | **Credibility × verbatim repetition only.** But a normative prompt was tested — *"identify which sources support each option and assess the credibility of those sources before deciding. Simple repetition of information should not influence your choice"* — and was insufficient to restore the source hierarchy except on the largest model. | **PRE-EMPTS the generic form of RQ4** ("a stated principle does not fix repetition weighting") |
| B-CONF | Most LLM Conformity Needs No Speaker, arXiv:2607.05545 | Dependence probed, or only speaker-free conformity? | **No dependence probe.** §3.4 compares one speaker repeating k times against k distinct speakers: repetition is *more* persuasive (one repeated line 91.6% vs one distinct speaker 51.3%; six repeated 74.7% vs six distinct 62.7%). No recognition measure, no intervention. §5 heading: *"Agreement is not independent evidence."* | DOES NOT PRE-EMPT |
| **B-GQA** (new) | GroupQA — *Rational Synthesizers or Heuristic Followers? Analyzing LLMs in RAG-based QA*, arXiv:2601.06189 (8 Jan 2026) | Has anyone already contrasted k paraphrases of ONE document with k DISTINCT documents? | **Yes — this is E12's manipulation.** §4.4: *"Redundancy (Paraphrased): Accumulation of rephrased variations of a single supporting document"* vs *"Informational Diversity (Distinct): Accumulation of unique, distinct supporting documents."* Table 4, flip rate distinct → paraphrased: DeepSeek-R1-8B 67.6 → 76.5; Gemini-2.5-FL 63.7 → 75.6; Llama-3.1-70B 62.9 → 69.8; Qwen3-32B 67.3 → 73.7. Paraphrases are unattributed (Appendix D.3 rewrite prompt), the task is binary yes/no QA, there is **no recognition probe and no intervention**; the one instruction tested ("treat all documents fairly") has no reported effect analysis. Framed as the Illusory Truth Effect. | **PRE-EMPTS the behavioural half of C4 and C8** |
| B-TEMPLATE (new) | Trust, but Don't Verify (arXiv:2606.05403); Know–Act Gap (arXiv:2603.22619); Knowing but Not Correcting (arXiv:2605.05957); Knowing–Saying Gap (arXiv:2608.07528) | Is "decodable in isolation, unused in the generative/synthesis step" already a genre? | **Yes** — for numeric validity of statistics, flawed scientific inputs, false claims embedded in task requests, and corrupted context respectively. None touches evidential dependence. | crowds the framing; C8 must not be pitched as "models know but don't use" |
| B-HUMAN | Connor Desai, Xie & Hayes 2022 (*Cognition*); *Explaining away the illusion of consensus* (*Memory & Cognition*, 2025) | LLM application? | **None found.** The human illusion arises when people are unsure whether the primary sources are independent; making the causal source relation transparent reduces it. No paper applies this to an LLM. | EXPLORATORY ONLY — unchanged |

Also checked and cleared (no dependence content): Mandela-effect MAS (arXiv:2602.00428),
Manufactured Confidence (arXiv:2606.29279), TMA-NM (arXiv:2606.24322),
MemLineage (arXiv:2605.14421), Epistemic Independence Training
(arXiv:2602.01528 — "independence" there means independence from bias cues),
α-Law of belief revision (arXiv:2603.19262), BeliefTrack (arXiv:2605.30219),
Diverse Evidence Better Forecasts (arXiv:2607.01661 — inter-agent error
correlation, no recognition probe), byte-exact / cross-attention RAG
deduplication (arXiv:2605.09611, 2607.24332 — engineering, no probe).

### What is left of C8 after the search — the residue

Three things appear in none of the papers above:

1. **A direct recognition probe on the same units as the decision.** E10's
   manipulation check (27/36 vs 0/36, on E10's texts) and E13's paired
   primary boolean (40 vs 0, p = 1.8e-12 — a post-hoc pairing) show the model
   *reports* the structure in ~40–45 % of units and misreports INDEPENDENT in
   ~40 % by every measure. GroupQA, WFW, CONF and CAMA never ask.
2. **An executable decision scored deterministically**, not a yes/no answer.
   (The matrix already discounts this distinction for C3; it is a task-format
   difference, not a phenomenon.)
3. ~~**An oracle arm.**~~ **WITHDRAWN 2026-09-01.** `gold` moved the
   ordering verdict by 0.0000 but is INCONCLUSIVE BY RULE there, and on the
   `ready` field it moved **+0.20** (cluster p = 0.0001). There is no oracle
   null. What has no counterpart in the found literature is instead the
   post-hoc `ready` sensitivity — which this project cannot claim until a
   preregistered E14 confirms it.

### What the residue does not license

- `identify` and `normative` are **INCONCLUSIVE BY RULE** (discordance outside
  the powered band). The intervention-ladder leg of C8 is therefore untested,
  not null.
- `gold` is **diagnostic only, never pooled**, and its powered-band reading is
  blocked by the band defect (`docs/RESUME.md` §4); the equivalence reading is
  post-hoc.
- One decider, `llama3.2:3b`. GroupQA's four models are 8B–70B and detect an
  *anti-normative* preference for paraphrases; E13 NORMATIVE's −0.074
  (CI [−0.139, −0.009]) points the same way but is inconclusive by rule. E13
  is consistent with GroupQA, not additive to it, on the behaviour.
- The recognition analyses that discriminate are post-hoc pairings; the
  predeclared per-response measures put INDEP recognition at 0.528 (boolean)
  and 0.130 (count_strict). Rule 2 is unadjudicated.

**Verdict.** C8 is not pre-empted by the fixed rule, is not promotable to
NOVEL, and is contradicted as phrased by the `ready` field. Its honest size is
*a recognition probe on the same units as an ordering-channel null, on one
small model, attached to a behavioural finding GroupQA already published — plus
a post-hoc, unconfirmed dependence effect on a second decision field that none
of the papers above reports and this project cannot yet claim*. The claim memo
(`docs/CLAIM-E13.md`) is scoped to exactly that.

---

## Search log — 2026-09-01

Fresh session, fresh budget. 19 `WebSearch` calls, 15 `WebFetch` reads.
Searches were phrased to find the *killing* paper; the twelve queries listed
at the top of this file were all run, verbatim or in a tighter form, plus
seven targeted at the recognition/intervention conjunction:

```
LLM recognizes correlated sources shared origin but still double counts evidence
same-source vs independent-source evidence LLM belief revision double counting
"source independence" OR "evidential independence" large language models corroboration redundancy
knowing vs using gap LLM "knows" but fails to "apply" source dependence provenance
duplicate OR near-duplicate retrieved passages RAG LLM "same source" redundancy bias
"pseudo-corroboration" OR "manufactured corroboration" OR "false majority" LLM agents memory
paraphrase multiplicity evidence weighting LLM independent evidence vs repeated assertion
"illusion of consensus" language model OR LLM independent sources dependent sources
LLM Bayesian source dependence correlated testimony "conditionally independent" witnesses
corroboration hysteresis LLM repetition blocks legitimate correction update superseded
LLM "circular reporting" OR "citation cascade" OR "echo" sources knowledge conflict provenance
"correlated evidence" OR "dependent evidence" language model belief revision shared origin
LLM knowledge conflict number of documents vs number of distinct sources paraphrased duplicates
Connor Desai illusion of consensus 2026 dependent sources large language models
telling LLM that documents share a source OR "same origin" prompt instruction redundant evidence
multi-agent debate agents share same retrieved evidence illusory consensus correlated agents
"evidence double counting" OR "double-counting" language models retrieved documents provenance
"paraphrased" evidence "distinct" evidence LLM redundancy detection prompt intervention GroupQA
LLM identifies sources are not independent OR "shared source" yet still treats as corroboration
belief revision source correlation LLM duplicate dependent evidence language models
"source independence" LLM corroboration provenance graph "independent confirmations" agent memory
redundancy-aware OR dependence-aware prompting LLM "same underlying" evidence count independent sources
```

Papers read against the boundary questions, with the verdict each earned:

| paper | read | verdict |
|---|---|---|
| CAMA, arXiv:2608.19701 | full text | no recognition probe, no told-correlation baseline |
| Information Discernment, arXiv:2607.19355 | full text | M1/M2 = reliability only; template pre-empted |
| Whose Facts Win?, arXiv:2601.03746 | abstract + search excerpts of the prompting section | repetition ≠ independence; normative prompt tested and mostly failed |
| Most LLM Conformity Needs No Speaker, arXiv:2607.05545 | full text | repetition > distinct speakers; no probe, no intervention |
| GroupQA, arXiv:2601.06189 | full text, two passes | **E12's manipulation; paraphrased > distinct; no probe, no intervention** |
| Trust, but Don't Verify, arXiv:2606.05403 | abstract | dissociation template, numeric validity |
| Know–Act Gap, arXiv:2603.22619 | abstract | dissociation template, flawed inputs |
| Knowing but Not Correcting, arXiv:2605.05957 | abstract | dissociation template, embedded false claims |
| TMA-NM, arXiv:2606.24322 | abstract | enforcement, no probe |
| MemLineage, arXiv:2605.14421 | abstract | enforcement, no probe |
| Epistemic Independence Training, arXiv:2602.01528 | abstract | different sense of "independence" |
| Mandela effect in MAS, arXiv:2602.00428 | abstract | no dependence manipulation |
| α-Law belief revision, arXiv:2603.19262 | abstract | no dependence |
| Manufactured Confidence, arXiv:2606.29279 | abstract | register, not dependence |
| BeliefTrack, arXiv:2605.30219 | abstract | no dependence |

Limits of this pass: abstract-only reads can miss an appendix experiment;
WFW's prompting result was taken from search excerpts of the paper rather than
a full-text read. Neither limit changes the verdict, because the killing
finding (B-GQA) was read in full and is unambiguous.
