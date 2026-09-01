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


---

## Research-lead pass — 2026-09-01 (evening). Six adversarial reviewers, two exploratory screens, one latent-variable mining pass

**Method.** Every raw plan artifact on disk (E2, E4, E7, E8, E9, E10, E11, E12, E13; five deciders) was re-parsed for the never-analysed `ready` field. Six independent reviewers were told to destroy, not support: prior art for the READY dissociation, prior art for the instrument, a confound review of READY computed from raw files, the human-cognition literature on dependent evidence, causal design after the FIXED floor, and prior art for the normative backfire. Load-bearing numbers below were re-derived by the lead from raw output before being written here. Two hypothesis-blind exploratory screens were declared in git before running (`E12X-qwen14b-ready-screen.md`, `E13X-backfire-screen.md`); nothing from them can become a claim.

| # | candidate | closest prior work | what prior work demonstrated | what our evidence demonstrates | overlap | remaining distinction | experiment needed | status |
|---|---|---|---|---|---|---|---|---|
| **C9** | *Decision-channel dissociation*: evidential dependence moves execution authorization (`ready`) while the substantive plan (ordering) is invariant | "Calibrated Enough to Know, Not Calibrated to Act" arXiv:2608.27167; Whose Facts Win? arXiv:2601.03746; GroupQA arXiv:2601.06189; Cherry-pick Override arXiv:2606.07834; When Evidence Conflicts arXiv:2605.14115; AgentAbstain arXiv:2607.10059; Reported Confidence Tracks Commitment arXiv:2606.29490 | 2608.27167 publishes and names the abstraction — an evidence property moves the act/commit gate while a separately measured judgment channel does not track it (direction: more evidence → more commitment) — and trains it away in a 3B model. 2601.03746 ran same-source-twice vs two-different-sources on Llama-3.2-3B with an abstention option: answer channel indifferent, abstention at floor (~3 %). 2605.14115 and 2606.29490 establish confidence/commit as a channel distinct from the answer. | llama3.2:3b only: ready(SAME)−ready(INDEP) = +0.26 (E12), +0.23 (E13 default), CI [+0.14, +0.33]; ordering +0.00. Survives identical-plan subsets (11/2, 12/2) but is ~2.5× larger where plans differ. **Aya-8B, Qwen-3B, Qwen-7B: `ready` at ceiling (≥ 358/360) in every arm of E4/E8/E11** — the channel does not exist there. **Qwen-14B (E12-X screen, the only other decider with a varying channel): same − indep = −0.046, CI [−0.111, +0.018], sign reversed; and corroboration *raises* its readiness where it *lowers* llama's.** | HEAVY — the framing is published; the same contrast on the same model exists with a commitment channel present | Only the *direction*: readiness falling as corroboration becomes independent, which no paper reports. But see C10: that direction is an artefact of repetition raising readiness, not independence lowering it | none worth its cost: the best design (three-arm section-locator, 1320 calls) still cannot separate "represents independence" from "reads distinct names as disagreement", on one 3B model | **CLOSED — HEAVY OVERLAP, single-model, and mis-described (C10)** |
| **C10** | *What the READY effect actually is*: repeated identical citation raises one model's readiness; distinct citations leave it flat; both lower it relative to no corroboration | Whose Facts Win? (repetition reverses source preference); illusory truth in LLMs arXiv:2303.06074; Yaniv, Choshen-Hillel & Milyavsky 2009 (interdependent consensus raises confidence without accuracy); Smithson 1999 / Zhu et al. 2025 (conflict aversion); Fernbach et al. 2011 (added supportive material lowers judged probability) | Repetition is persuasive in LLMs; in humans, consensus consistency raises confidence, source conflict lowers commitment, and no dependence effect ever pushes commitment *below* the no-corroboration baseline | E11 nested dose (llama, 36 instances): same_k1 19 → k2 21 → k3 27 ready (k1 vs k3 paired 0/8, p = 0.008); indep_k1 17, 17, 17 (flat). bare > same replicates in E10 (10/2), E11 (11/2, 12/1), E12 (31/8): adding two agreeing reports of either kind *lowers* readiness from ~0.78 to ~0.5. Per-rotation heterogeneity 0 → +0.5 by which document names are drawn (platform spec 24/0; incident review 1/0). `ready = true` in 129/242 responses where the model wrote *same source = true* and **1/190** where it wrote *false*: one latent "these reports are all one thing" readout. First-proposition units ~+0.11 n.s.; 2nd/3rd carry the effect | HEAVY — a repetition/consistency effect on a commitment channel, in one model | none: the corpus cannot separate recognised co-reference from lexical repetition of one string, and the effect is confined to one decider | a paraphrased-same-root arm would separate co-reference from string repetition — but for a single-model consistency heuristic that is not worth a run | **CLOSED — mechanism identified as consistency/repetition, not dependence** |
| **C11** | *AgentLineageBench*: lineage-exact procedural conflict benchmark where both source-trusting and latest-trusting fail | ManyIH-Bench arXiv:2604.09443; IHEval NAACL 2025 arXiv:2502.08745; IH-Benchmark arXiv:2607.25987; Control Illusion AAAI 2025 arXiv:2502.15851; MemoryAgentBench FactConsolidation; SEQUOR arXiv:2605.06353; STALE arXiv:2605.06527; Manufactured Confidence arXiv:2606.29279; relay testbed arXiv:2607.09678; MAP-Graph arXiv:2608.10509; Selective QA over conflicting personal memory arXiv:2605.30087 | Procedurally generated, deterministically scored contexts where privilege — not position — decides (853 and 3,538 items); memory benchmarks that reward the *latest* statement; forged-vs-legitimate authority crossed with ground truth by construction; templated relay corruption with exact provenance; a seeded DGP with an independent audit recovering every label | 36 instances (a 6 × 6 crossed design), six derivation classes with exact `derives_from`, authorised and unauthorised revisions word-identical and resolved only by speaker, partial-order plan scored deterministically, registered null controls | HEAVY — the founding premise "every conflict benchmark treats the source as the answer key" is **false** (corrected in `docs/agent-lineage-bench.md`) | a resource note: word-identical authorised/unauthorised revisions in a multi-party transcript with six lineage classes, positioned against the instruction-hierarchy benchmarks | none | **HEAVY OVERLAP — resource note at most** |
| **C12** | *Falsification apparatus*: raw-recompute verifier, prospective design checker with operating bands, preregistration with zero outcomes, adversarial panels | Kotawala 2026 arXiv:2605.30315 (`llm-power`: paired-design resolution, discordance-dependent McNemar N, cluster design effect); Miller 2024 arXiv:2411.00640; Connor 1987; tail-shape protocol arXiv:2606.16511 (preregistered TOST, precomputed n, synthetic self-validation); showyourwork (every number regenerated from raw in CI); van Miltenburg et al. NAACL 2021; POPPER ICML 2025 arXiv:2502.09858; Sound Agentic Science arXiv:2604.22080; Refute-or-Promote arXiv:2604.19049 | Each component exists, several as packages | The same components, assembled, plus a preserved record of seven results retracted by their own controls | PRE-EMPTED as method | an experience report on a negative-results / reproducibility venue | none | **PRE-EMPTED as methodology** |
| **C13** | *Latest-trusters*: small open models cannot separate legitimate supersession from unauthorised revision; an explicit authority rule barely helps (E3: 5/36 vs 36/36 ceiling; E4: 3B–14B) | IHEval; Control Illusion; ManyIH-Bench; Manufactured Confidence; TAMAS; PRIME arXiv:2606.22470 | Qwen-2 7B 16.4 % / Mistral-7B 15.0 % on conflicts, current-turn conflicts hardest, an explicit priority prompt "does not bring noticeable improvements"; GPT-4o at 63.8 % with emphasised separation; forged, attributed and bare assertions "all grant alike"; PRIME: small models are not uniformly latest-preferring (some prefer the *first* directive) | Five local models 3B–14B: correct-both 4–15/36, latest-reflex 14–23/36, source-reflex 0–4/36; the rule variant moves nothing | PRE-EMPTED | a replication in a new task format, qualified "in this transcript format" | none | **PRE-EMPTED** |
| **C14** | *Normative backfire*: a one-sentence principle about evidential independence raised adoption of an unsupported contradiction indiscriminately | KAIROS arXiv:2508.18321 (critical-evaluation and reflection prompts worsen peer-pressure robustness, Llama-3.2-3B up to −13 pp: "prompting methods tend to worsen robustness overall"); Information Discernment arXiv:2607.19355 (normative Bayesian prompt over-updates); Trust, but Don't Verify arXiv:2606.05403 (skepticism prompts become blanket discounting); Peters & Chin-Yee 2025 arXiv:2504.00025 ("algorithmic ironic rebound"); CogBias arXiv:2604.01366 (debiasing prompts backfire on judgment biases); negation-rebound cluster arXiv:2601.08070, 2511.12381 | On the same 3B model an added critical-evaluation instruction already makes peer pressure worse; normative epistemic prompts already over-update; "blanket skepticism" and "ironic rebound" are named phenomena | E13 re-derived: normative − default +0.1019 pooled over both dependence arms (29 vs 7 of 216 paired units, instance-level p = 0.0064); identify − default +0.0139 (p 0.79); sham +0.0093 (p 0.92); gold −0.0372 (p 0.07). Extra flips concentrate where the model reported *independent* structure with count = 4 — it counts the contradictor as a source and the principle's second sentence gives it weight | HEAVY — the phenomenon is known and named on this very model | only the 2×2 detail: the principle discounts *corroboration* indiscriminately (the mirror image of blanket discounting of the focal claim), with a structure-matched request and a sham both null | none: the E13-X screen found the principle's effect +0.037 in Aya-8B and +0.005 in Qwen-7B against llama's +0.09, so the declared two-of-three rule failed before the third decider was needed | **CLOSED — llama-specific and HEAVY OVERLAP (KAIROS)** |

**Rule outcome for the whole matrix after this pass.** C1 PRE-EMPTED; C2 INVALID; C3 HEAVY OVERLAP; C4 PRE-EMPTED (behavioural) and ordering-channel only; C5 UNKNOWN and weak; C6 exploratory; C7 DEAD; C8 WITHDRAWN AS PHRASED; C9 CLOSED; C10 CLOSED; C11 HEAVY OVERLAP; C12 PRE-EMPTED; C13 PRE-EMPTED; C14 pending. **No row is NOVEL.** The behavioural novelty space around evidential dependence is closed on this project's evidence; the instrument is a resource note; the last row (C14) is a named phenomenon (blanket skepticism / ironic rebound) already shown on this model by KAIROS, and the cross-family screen found it llama-specific. **Every row is now pre-empted, closed, withdrawn, dead or single-model.**

### Search log — 2026-09-01 (evening), by reviewer

- READY dissociation: 43 queries, 32 papers read (list in the reviewer transcript; ids above).
- Instrument: 36 queries, 24 papers fetched in full or abstract (ids above; two summariser-hallucinated claims were checked against PDFs and rejected).
- Human cognition: 12+ queries, 35 papers (Yousif et al. 2019; Connor Desai et al. 2022, 2026; Xie & Hayes 2022; Whalen et al. 2018; Mercier & Miton 2019; Harkins & Petty 1987; Yaniv et al. 2009; Tversky & Shafir 1992; Dhar 1997; Evangelidis et al. 2023; Smithson 1999; Zhu et al. 2025; Cabantous 2007; Fernbach et al. 2011; Nisbett et al. 1981; Couch 2022; Pilditch et al. 2020/2025; Bovens & Hartmann 2003).


---

## C15 — FFEP, claim-relative counterfactual auditing of agent evaluations — 2026-09-02

| # | candidate | closest prior work | what prior work demonstrated | what our evidence demonstrates | overlap | remaining distinction | experiment needed | status |
|---|---|---|---|---|---|---|---|---|
| **C15** | *FFEP*: claim → named shortcut → minimal validated counterfactual → re-run → mechanical check → identification statement → fail-closed | Mystery Blocksworld arXiv:2305.15771; Reasoning or Reciting arXiv:2307.02477; Turk arXiv:2605.30590; HackDetect arXiv:2607.22368; Epistematics arXiv:2605.14167; ImpossibleBench arXiv:2510.20270; MemoryPolicy-Bench arXiv:2608.17247; Chen et al. arXiv:2608.00981; HANS, contrast sets, CheckList; METAL/MORTAR/ReliabilityBench; AppWorld contrast sets; Ivanova arXiv:2312.01276 | components 1–6 with a deterministic validator on planning (2023); 1–4 and 6 on tool agents with an LLM judge (2026); the identification principle with an abstention rule (2026); contrast sets inside a shipped agent benchmark | a working generator and validator on the frozen formal representation (135 validated discriminators, two families that fail closed correctly), an inventory showing the eligible pool is instances not verifier lines, a corrected estimand, attainability tables, and a strict retrospective in which the method would have caught 5 of 17 of this project's own failures | HEAVY — every component published, the conjunction converged on in 2026 | machine-certified minimality/divergence + deterministic scoring + a first-class UNTESTABLE verdict in one pipeline: methodological packaging | none authorised; `docs/FFEP-FEASIBILITY.md` decision STOP_FFEP | **HEAVY OVERLAP — STOP_FFEP** |

Gemini's external review retired E15-PODT and proposed C15; its "highly
novel" rating was not accepted and did not survive two independent
adversarial reviews. Feasibility artefacts (`ffep_inventory.py`,
`ffep_mutations.py`, `test_ffep_mutations.py`, `ffep_power.py`,
`docs/ffep_inventory.json`, `docs/ffep_catalogue.json`) are kept as
reusable, non-experimental infrastructure. No model was called.
