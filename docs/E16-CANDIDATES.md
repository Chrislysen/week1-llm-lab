# E16 candidates — programme reopened 2026-09-03

**Status (2026-09-05): S-O RETIRED — screened (NOT PURSUED) and then closed
by a web-search re-gate; see the RE-GATE section at the foot of this file.
S-E was re-gated on 2026-09-06 and is ALSO recommended for retirement (its
mechanism dissociation is published). The reopened programme has no live
candidate; see the two RE-GATE sections at the foot of this file.**

*(superseded header)* **Status: CANDIDATE SEARCH COMPLETE (2026-09-03). Lead candidate S-O
selected for an exploratory screen. No candidate is preregistered. Zero E16
model calls. Nothing here is a claim.**

## Why this file exists

The first programme closed on 2026-09-02 at tag `research-closed-v1`
(`docs/RESEARCH-LEAD-2026-09-02.md`, `docs/FFEP-FEASIBILITY.md`). On
2026-09-03 the author reopened the search for a new programme, with the
explicit aim of a result that is novel rather than a negative-results
write-up. That decision overrides the "do not search for E16" line in
`docs/RESUME.md`; everything else in that file stands.

The author's own brainstorm words were: *binary, a different coding
language, memory allocation, compression, anything that would qualify as a
breakthrough.* This file maps each onto the sharpest testable candidate on
the existing instrument and sends it through the same gate every earlier
candidate went through: an adversarial prior-art search **before** any model
call. The project's base rate is thirteen of fourteen rows pre-empted,
closed, withdrawn or dead, so every candidate below is presumed pre-empted
until a search says otherwise.

## Rules carried over unchanged

- Frozen artifacts (`compulsory-baseline-v1`, E10–E14 corpora, every hash in
  `docs/RESUME.md` §1) are not touched. New work reads them, never rewrites.
- No model call before a declared protocol is committed with zero outcomes.
- Every experiment carries a random control and a sabotage/oracle control
  that can fail.
- Every reported number is re-derivable from raw output by `verify_claims.py`
  or a sibling.
- A conjunction of separately published components is at best OPEN (NARROW),
  never NOVEL.

## Directions already killed in this repository (not re-opened)

| the author's word | nearest earlier row | why it is dead |
|---|---|---|
| memory allocation (across turns) | audit RQ2 | MT-PingEval arXiv:2602.24188 ran fixed-total-split-across-turns: flat/decreasing |
| memory allocation (by role, routing) | audit RQ3, C7 | RCR-Router arXiv:2508.04903; AnchorRoute killed on measurement (E6) |
| compression of inter-agent messages | audit RQ5 | arXiv:2506.19209 — the claim's wording is the paper's title |
| adaptive budget allocators | Argos audit | conserved-budget allocator lost to a random control |
| provenance-metadata tags | E15-PODT | retired by the external review 2026-09-02 |

## The four candidates sent to the gate

### E16-A — Compression-mediated corroboration (*compression*)

A lossy context compressor (LLM summariser, extractive selection, or
token-level compression) sits between the evidence and the decider. The
corroboration dose-response (E11: 0.75 → 0.42 → 0.28 → 0.11 over k = 0..3)
is altered because the compressor changes the *effective* dose: it collapses
k paraphrases into one statement, or writes "several reports confirm", or
erases the same-root/independent distinction. The would-be claim: memory
compression is a causal, measurable modulator of evidence weighting, and the
compressor's provenance-collapsing behaviour predicts downstream adoption.

Testable on the frozen E11/E12 corpora by inserting a compression stage;
deterministic ordering evaluator; preregistered equivalence bounds.

### E16-B — Representation-dependence of evidence weighting (*binary*, *a different coding language*)

The same evidence set delivered as (i) natural language, (ii) structured
records (JSON / log lines / a table), (iii) a compact formal protocol or
code, (iv) opaque encodings (base64, hex, content hashes) where content is
unreadable but identity and multiplicity are visible. Three predictions:
(1) the dose-response weakens as the encoding becomes less linguistic;
(2) with opaque blobs, adoption of the contradiction still tracks the *count*
of blobs — corroboration without comprehension; (3) a formal encoding with
explicit identity makes the same-root discount appear where natural language
did not (E12/E13 null; GroupQA).

### E16-C — Asymmetric context budget between adversarial roles (*memory allocation*)

A fixed total context budget split unequally between the Operations Lead and
the Safety Auditor (the base instrument, `context.py` policies, deterministic
constraint evaluator). Prediction: giving the constraint-guarding role the
larger share protects planted constraints more than an equal or reversed
split at identical total cost. Differs from RQ2 (across turns) and RQ3
(routing content by role) in that it varies *capacity* by role, not content.

### E16-D — Reasoning-mode deciders and the dependence discount

All five deciders so far are non-reasoning instruct models. `qwen3:14b`
(hybrid thinking) and `gemma4:e4b` are local and unused. Prediction: with
thinking on, the same-root vs independent-root gap becomes non-zero in the
normative direction; with thinking off on the same model it does not; the
corroboration dose-response flattens under thinking. This is the "new
programme with a new decider" that `docs/RESEARCH-LEAD-2026-09-02.md` §6
named as the strongest remaining threat to the closing verdict.

### Scout

A fifth reviewer searched for open questions this instrument can answer that
none of the above names, favouring phenomena where a small open model is a
feature rather than a limitation.

## Verdicts — the author's four words (2026-09-03)

Five reviewers ran in parallel, 31–60 searches each, arXiv IDs verified by
fetch unless marked. Full reports are condensed here; the search logs are in
the reviewers' transcripts and the closest papers are listed so the search
can be re-run.

| candidate | verdict | closest work | what remains |
|---|---|---|---|
| **E16-A** compression-mediated corroboration | **PARTIAL** — headline pre-empted | *Memory Contagion* arXiv:2606.23195 (oracle vs LLM-summarisation consolidation arms, downstream agent measured, −84 % attenuation of a stored bias); *When Summaries Distort Decisions* arXiv:2606.29251 (decision-flip rate under LLMLingua and summarisers); *Governance Decay* arXiv:2606.22528 (violation tracks the summariser, not the agent; 1 323 episodes); *Recalling Too Well* arXiv:2606.10949; *Manufactured Confidence* arXiv:2606.29279; *Epistemic Sybil Resistance* arXiv:2609.01873 (2026-09-01: one root re-extracted n = 1..32); Astute RAG ACL 2025 App. E; *When Not to Write Memory* arXiv:2607.02579; arXiv:2601.04889 | compressor × k-paraphrase dose with an audited effective-k mediator. Reviewer: even a positive result is a substitution into Memory Contagion's template; a replication note, not a claim. |
| **E16-B** representation-dependence | **PARTIAL, leaning HEAVY** | *Whose Facts Win* arXiv:2601.03746 ACL 2026 ran repetition **in Markdown tables** with verbatim same-source duplicates on 13 open models: repetition still wins (contradicts prediction 3 outright); *Format as a Prior* arXiv:2508.15793 AAAI 2026 (text/table/KG/infobox × conflict, Qwen3 8B–32B, Gemma-2); ConflictQA arXiv:2604.11209 SIGIR 2026; CodeCrash arXiv:2504.14119 NeurIPS 2025; *Mixture of Encodings* arXiv:2504.07467 (base64 is not comprehended: MGSM 53 → 5); CUE-R arXiv:2604.05467 | count of **non-decodable** blobs (SHA-256 hex) vs length-matched unrelated filler. Reviewer: any effect is anchoring-by-volume, not corroboration; identical blobs trigger copy behaviour; a mechanism note at most. |
| **E16-C** asymmetric budget by role | **PARTIAL → OPEN (NARROW)** | RCR-Router arXiv:2508.04903 defines role budget offsets `β_role` verbatim but only sweeps budgets **uniformly**; ZEBRA arXiv:2605.20485 (fixed total split across phases, skewed optimum); DACS arXiv:2604.07911; Phase Transition arXiv:2601.17311; Khan et al. arXiv:2402.06782 (symmetric word budgets); *Omission Constraints Decay* arXiv:2604.20911; *Remembering More, Risking More* arXiv:2605.17830 (more memory → more violations: contra-directional) | kill condition (d) did not fire: no per-role context allocation study on constraint adherence exists. Mechanism is RCR-Router's; two 2026 papers make the sign uncertain; a null is the modal outcome. |
| **E16-D** reasoning-mode deciders | **HEAVY OVERLAP** | GroupQA arXiv:2601.06189 already includes `deepseek-r1-0528-qwen3-8b` and `qwen3-32b`: paraphrased-vs-distinct flip 76.5 vs 67.6 and 73.7 vs 67.3 — the **opposite** direction; prompted CoT shifts belief < 0.5 %; *Trust, but Don't Verify* arXiv:2606.05403 (Qwen 32B think vs no-think: dissociation "not corrected" by reasoning); ConflictQA (thinking variants degrade more); *Reasoning or Rambling* arXiv:2509.21054 v3; arXiv:2605.27773; *Inverse Scaling in Test-Time Compute* arXiv:2507.14417 | native think on/off (not prompted CoT) with a trace-stripping ablation on `qwen3:14b`, 540 calls on the frozen E12 design. Prior strongly negative; expected to kill. |

**Reading.** The author's four words map onto directions where 2026 has
already arrived: memory-compression-as-modulator has three papers since June,
format-as-prior has an AAAI paper, and the reasoning-model contrast was in
GroupQA's own tables. None of the four clears the project's bar.

## The scout's candidates (2026-09-03)

The fifth reviewer looked for questions the base dialogue instrument can
answer that the literature has not, favouring phenomena where a small model
is a feature. It dropped five directions as pre-empted before listing
(turn-count vs token-distance forgetting arXiv:2603.22608; thinking ×
distractors DistractionIF arXiv:2605.29491; retriever × reader-scale
crossover arXiv:2603.11513; omission vs confabulation arXiv:2411.06037,
arXiv:2506.11440; recall-vs-adherence DriftBench arXiv:2604.28031) and
listed five, each with its own kill searches:

| id | candidate | one-line prediction | scout's P(pre-empted) |
|---|---|---|---|
| **S-A** deontic flattening | rotate each constraint through must / should / ideally / you-may-want-to; 3B compliance is flat (hedge-blind over-constraining), 14B shows a gradient | 0.25 |
| **S-O** zombie constraints | constraints proposed-then-rejected in the dialogue stay binding for small models; lossy retrieval (BM25/dense) makes it worse because the content-rich proposal turn is retrieved and the short rejection turn is not — checkable from the `manage_context` retrieval log | 0.30 |
| **S-E** retraction-as-repetition | on the frozen clusters, a same-root retraction moves the decision less than an independent contradiction at 3B because lexical overlap reads as corroboration | 0.40 |
| S-B role-tag dependence | constraint retention depends on which role stated it; disappears with tags stripped, inverts when swapped | 0.45 |
| S-L code-switched constraint | one constraint in Norwegian; decompose loss into retrieval miss vs reader miss with the oracle policy | 0.40 |

S-A, S-O and S-E were sent to the same adversarial gate as E16-A–D on
2026-09-03. **Search caveat:** the session's web-search budget was exhausted
during the first four reviews, so these three gates ran through the arXiv
export API, arXiv site search, OpenAlex, Crossref, HuggingFace papers and
direct page fetches, under heavy rate limiting. Their verdicts are weaker
than E16-A–D's and must be re-run with web search before any *claim*; they
are sufficient for a declared exploratory screen, which cannot become a claim.

## Verdicts — the scout's candidates (2026-09-03)

| candidate | verdict | closest work | what remains |
|---|---|---|---|
| **S-A** deontic flattening | **PARTIAL** — gradient component heavy | *Why Do AI Agents Break Rules?* arXiv:2608.12323 (same regulation phrased mandatory / informational / discretionary, content fixed, deterministic vendor-choice outcome, 12 open models 24B–1T; "no consistent pattern correlating model size with phrasing robustness"); *Deontological Keyword Bias* ACL 2025 arXiv:2506.11068 (must .86 > ought .83 > should .79 > have to .64; with no modal, Llama-3.1-8B .98 and Gemma-2-9B .90 vs GPT-4o .06 — small models saturate obligation); Control Illusion arXiv:2502.15851; arXiv:2602.21223; Harness-IF arXiv:2608.11727 | only the sub-24B slope across the hedged middle rungs (should / ideally / you may want to). "Flat at small scale" is already predicted by both closest papers. ~240 calls. |
| **S-O** zombie constraints | **behavioural: PARTIAL → OPEN (NARROW); retrieval mechanism: OPEN** | *Attention Latch* arXiv:2604.24512 (agents "remain anchored to obsolete constraints despite explicit contradictory instructions"; updates are *replacements*, frontier models only, LLM judge, no base-rate arm, no retrieval policy); MeetingProbe arXiv:2608.20392 ("overstated decision finality" 13.4 % of failures, QA); RefuteBench 2.0 arXiv:2502.18308 (forgetting direction only); AgentChangeBench arXiv:2510.18170 (additive shifts, no cancellation); the negation-blind retrieval line (single-turn IR; does not fire). Cleared: Multi-IF, StructFlowBench, MT-Eval, SysBench, MultiChallenge, MT-Bench-101, CFBench, PrefEval, PersonaMem. | a constraint **explicitly rejected and never replaced** stays binding above the never-stated base rate; the excess shrinks with size; under a word-budgeted BM25/dense policy it grows because the proposal turn is retrieved and the content-poor rejection turn is not — no published work links a retrieval policy to over-compliance via a per-turn retrieval log. Drop accepted-vs-proposed from the headline. Stage-gated: ~48 calls behavioural, +48 mechanism. |
| **S-E** retraction-as-repetition | **OPEN (NARROW)**, tightly surrounded | *When Stale Constraints Go Unchecked* arXiv:2608.25553 (Aug 2026: a constraint's own source withdraws it; 26 models decide stale-consistently 74–77 %; no independent-source arm, no lexical manipulation); InterruptBench arXiv:2604.00892 (same-user retraction arm, frontier only); *Self-Correction Illusion* arXiv:2606.05976; PI-LLM arXiv:2506.08184; *Sentence-Level Contextual Entrainment* arXiv:2606.24077 (entrainment decreases with size); Supersede arXiv:2606.27472; *Memory Trust Gap* arXiv:2609.01852; MemOps arXiv:2607.12893. No LLM-subject continued-influence-effect paper exists on arXiv. | a high-overlap same-root retraction moves a 3B decider *less* than a content-matched independent-root contradiction, and the deficit is driven by overlap, not source deference. Needs an overlap manipulation (hi / lo) and a stance-swapped sabotage arm. ~290 calls on the frozen clusters. |

**Citation housekeeping raised by the S-E reviewer.** Every index resolves
arXiv:2601.03746 to *Whose Facts Win? LLM Source Preferences under Knowledge
Conflicts* (ACL 2026). This repository cites it in `docs/novelty_matrix.md`
row C1 as "repetition / illusory truth". The paper is about repetition
reversing source preference, so the *content* of the C1 pre-emption stands;
the "illusory truth" label is loose and should read "repetition (Whose Facts
Win)". No verdict changes.

## Decision — 2026-09-03

Nothing is OPEN in the strong sense; the base rate held again (eight of eight
candidates have every component published). Two candidates carry a component
nobody has run, and both are cheap and stage-gated on the existing instrument:

1. **S-O zombie constraints — LEAD.** Chosen because (i) its mechanism half
   is the one OPEN verdict of the day and is checkable from the retrieval log
   with **zero model calls** (an offline selector preflight decides whether
   stage 2 is even possible before a token is spent); (ii) it lives on the
   base dialogue instrument — the part of this repository the first audit
   called the actual unclaimed contribution; (iii) the kill rules are cheap
   (~48 calls per stage). Internal evidence to carry in: E4 already shows
   models follow an explicit *lifting* of a constraint 0.53–0.94 of the time
   at full context (`results/e4_summary.csv`, `exercised`), so the
   full-context zombie excess may be small; the retrieval interaction is
   where the effect, if any, is expected.
2. **S-E retraction-as-repetition — RUNNER-UP.** Held until S-O's stage 1 is
   read. Reuses the frozen E12 units with two new template banks.
3. **Parked:** S-A (only a hedged-middle-rung slope remains), E16-C (mechanism
   is RCR-Router's, null modal), S-B, S-L.
4. **Closed:** E16-A, E16-B, E16-D.

Next artifact: `docs/protocols/E16-zombie-screen.md`, an exploratory screen
declared with zero outcomes, plus its corpus module and tests; then the
offline retrieval preflight; then stage 1.


---

# RE-GATE WITH WEB SEARCH — 2026-09-05 — S-O RETIRED

The 2026-09-03 gates for S-A / S-O / S-E ran **without web search** (budget
exhausted; arXiv export API, OpenAlex, Crossref and direct fetches only). That
caveat is recorded above and made the verdicts provisional. The gate was
re-run for **S-O** on 2026-09-05 with web search, after stage 1 had been read.

**It returns a worse verdict than the one that authorised the screen.**

## Verdict change

| half | 2026-09-03 (no web search) | 2026-09-05 (web search) |
|---|---|---|
| behavioural | PARTIAL → **OPEN (NARROW)** | **CLOSED — HEAVY OVERLAP** |
| retrieval mechanism | **OPEN** | **NARROW** — surrounded on three sides |

## What closed the behavioural half

**arXiv:2608.12599** — *Dead text or binding clause? Measuring and restoring
constraint influence in black-box LLM dialogues* (Haoyuan Zhu, 12 Aug 2026).
Multi-turn dialogue in which users **revoke** constraints; models keep
enacting withdrawn requirements, "occasionally beneath comments asserting
their removal". The paper names the failure **behavioural relapse / revocation
inertia**. Reported: relapse at an **8B operating point climbs 0.011 → 0.403**
as constraint load grows, **while stronger models sit at floor**, under
matched token and attempt budgets.

That is S-O prediction (1) *and* prediction (2) — the carried-over rejected
constraint, and the shrinking of the excess with model size — published in
dialogue, on a small model, three weeks before this screen was designed.

Not a literal duplicate: its comparison condition is a *no-ledger
verifier-retry baseline*, which is a system baseline rather than a
never-mentioned base rate, and the abstract does not say whether revocations
are replaced or left standing. Those residues are not enough to carry a
behavioural claim.

## What surrounds the mechanism half

- **arXiv:2606.22528** — *Governance Decay: How Context Compaction Silently
  Erases Safety Constraints in Long-Horizon LLM Agents* (Shiyang Chen,
  21 Jun 2026, rev. 27 Jun). In-context governance constraints an agent obeys
  **while visible** are silently removed by compaction / summarization /
  eviction, and the agent then performs the prohibited action. ConstraintRot
  compares the same trigger with the policy **present, compacted, absent and
  pinned**; 1,323 episodes, seven model families; violation 0 % → 30 % (59 %
  worst case). Constraint Pinning restores 0 %.
  *This is the exposure-conditional read S-O proposed as its novel move.*
- **arXiv:2608.11242** — *Lost in Compaction: Evaluating Side-Constraint Loss
  under Context Compaction* (Wang, Zhang, Lee, Yang, 31 Jul 2026). Session
  Constraints are silently dropped by compaction; the COMPINT suite finds
  current compactors **retain only 17 % of injected SCs**, most performing
  worse than no compaction at all.
- **arXiv:2604.20911** — *Omission Constraints Decay While Commission
  Constraints Persist in Long-Context LLM Agents* (Yeran Gamage, 22 Apr 2026).
  **Security-Recall Divergence**: prohibition-type constraints decay under
  context pressure while requirement-type constraints persist; 12 models,
  8 providers; omission compliance 73 % at turn 5 → 33 % at turn 16, commission
  at 100 %; "schema semantic content accounts for 62-100 % of the dilution
  effect". *A content-richness account of exactly the negative-vs-positive
  asymmetry S-O rests on* — applied to dilution rather than to retrieval.

The sentence in the 2026-09-03 table — "no published work links a retrieval
policy to over-compliance via a per-turn retrieval log" — **is no longer
defensible as written.** The defensible residue is narrower: no published work
links a *word-budgeted scoring* retrieval policy (BM25 / dense / fusion /
recency) to over-compliance with a *cancelled* constraint, read off a per-turn
selection log. Two things distinguish it and neither is large:

1. The dropped item is a **second speaker's rejection of a proposal**, not a
   standing operator policy. The behavioural sign is inverted — over-compliance
   with a cancelled action, rather than violation of a live prohibition.
2. The policy is a scoring retrieval budget with a logged selection, not an
   LLM compactor; the offline preflight predicts orphaning **before any model
   call** (dense-35 orphans 86.5 % of rejections, recency-35 orphans 0 %).

## Citation housekeeping

**arXiv:2604.24512 is not titled *Attention Latch*.** Its title is *Beyond the
Attention Stability Boundary: Agentic Self-Synthesizing Reasoning Protocols*
(Dahlia Shehata, Ming Li, University of Waterloo, 27 Apr 2026); "Attention
Latch" is the failure mode named inside it. The content cited above stands
verbatim ("causing agents to remain anchored to obsolete constraints despite
explicit contradictory instructions"). It evaluates GPT 5.4, Gemini 3.1 Pro,
Claude Sonnet 4.6 and DeepSeek V3.2 on MultiWOZ 2.2 across 9K trajectories, in
three tiers **including a shallow recency-based retrieval pilot** — so
"no retrieval policy" was already too strong for the closest paper.

This is the second such correction, after the arXiv:2601.03746 / "illusory
truth" label noted above. Both are label errors, not verdict errors.

**arXiv:2603.19997** (*When Contextual Inference Fails: Cancelability in
Interactive Instruction Following*, Bila, Naszádi, Mayn, Monz) surfaced on the
word "cancelability" and **does not fire**: it is Gricean cancelability of
implicature in a block-building task, not constraint retraction.

## Decision

**S-O is RETIRED.** The behavioural half is closed by prior art and was in any
case unsupported by stage 1 (`rejected - never` negative in both deciders); the
mechanism half is narrow, surrounded, and would need the redesign already
described in `docs/protocols/E16-zombie-screen.md` — a fresh corpus without an
enumerated action menu, breaking comparability with E1-E14 — to be measurable
at all. Screen plus re-gate cost 288 model calls and no claim; that is the
gate working, not a loss.

**S-E is NOT cleared by this pass.** Its 2026-09-03 verdict has the same
no-web-search caveat, and its closest paper (arXiv:2608.25553, Aug 2026) sits
in the same August-2026 cluster as arXiv:2608.12599 and arXiv:2608.11242 found
here. Re-gate S-E with web search before spending anything on it.

## Limits of this pass — read before relying on it

- Every verdict here is **abstract-level**. No full text was read. A full-text
  read could move any of these either way.
- Load-bearing IDs (2604.24512, 2606.22528, 2604.20911, 2603.19997, 2608.12599,
  2608.11242) were each confirmed by fetching the arXiv abstract page. The
  ConstraintRot detail "constraint survives the summary → 0 % violation,
  dropped → 38 %" came from **search synthesis, not from the fetched
  abstract**, and is unverified.
- The previously cleared benchmark list (Multi-IF, StructFlowBench, MT-Eval,
  SysBench, MultiChallenge, MT-Bench-101, CFBench, PrefEval, PersonaMem) was
  **not** re-checked this pass, nor were MeetingProbe, RefuteBench 2.0 or
  AgentChangeBench re-verified.
- No model calls were made for this re-gate.


---

# RE-GATE WITH WEB SEARCH — S-E — 2026-09-06 — RETIRE RECOMMENDED

Run after S-O was retired, for the same reason: the 2026-09-03 verdict
(**OPEN (NARROW)**, "tightly surrounded") came from a gate with no web search.

**S-E's claim.** A high-overlap **same-root retraction** moves a 3B decider
*less* than a content-matched **independent-root contradiction**, and the
deficit is driven by **lexical overlap**, not **source deference**.

## Verdict change

| half | 2026-09-03 (no web search) | 2026-09-06 (web search) |
|---|---|---|
| mechanism (overlap, not source deference) | part of **OPEN (NARROW)** | **CLOSED — the dissociation is published** |
| behavioural (same-root vs independent-root at 3B) | **OPEN (NARROW)** | **NARROW residue**, a recombination of published parts |

## The three papers that close the mechanism

- **arXiv:2601.03746** — *Whose Facts Win? LLM Source Preferences under
  Knowledge Conflicts* (Schuster, Gautam, Markert; 7 Jan 2026, rev. 17 Apr).
  13 open-weight LLMs, synthetic sources, tightly controlled. LLMs prefer
  institutionally-corroborated sources, **"however, these source preferences
  can be reversed by simply repeating information from less credible
  sources"** — plus a mitigation reducing repetition bias by 79.2 %.
  **This is S-E's dissociation.** Repetition overriding source credibility,
  with source under experimental control, already published on 13 models.
  *This repository has cited this paper since the C9-C14 pass* — in
  `docs/novelty_matrix.md` row C1, under the loose label "illusory truth",
  corrected on 2026-09-03 to "repetition (Whose Facts Win)". The S-E gate did
  not connect its own citation to S-E's mechanism.
- **arXiv:2606.05976** — *The Self-Correction Illusion: Role Relabeling Gates
  Explicit Error Flagging in Large Language Models* (Chen, Su, Lin, Li,
  Chiang; 4 Jun 2026, rev. 31 Jul). Keeps the erroneous claim
  **byte-identical** and varies **only the chat-template message role**
  (`<thought>` / user / tool / `<memory>`); relabelling to an external role
  raises explicit correction by **23-93 percentage points**, significant in
  10 of 12 model-domain settings, from 70B-class down to smaller families.
  S-E wanted to argue the effect is *not* source deference. Source deference,
  content held byte-identical, is now a large and well-identified published
  effect. S-E would have to beat this, not merely gesture past it.
- **arXiv:2606.24077** — *Sentence-Level Contextual Entrainment in Large
  Language Models* (Liu, Chu; 23 Jun 2026). 26 LLMs, seven families.
  Sentences present in the prompt — **"even if they are counterfactual
  statements"** — significantly raise their own probability at inference;
  **"as the model size increases, contextual entrainment gradually
  decreases"**; the effect is carried by **2-4 % of attention heads**, and
  ablating them mitigates it without hurting performance.
  That is S-E's proposed mechanism, S-E's prediction (2), and a causal
  localisation S-E cannot reach, all published.

## What the 2026-09-03 verdict got right

- **arXiv:2608.25553** confirmed, and its scope confirmed as recorded. Full
  title *When Stale Constraints Go Unchecked: Budgeted Verification Failures
  in Inherited Agent Memory* (Kazuki Nakayashiki). It is inherited agent
  memory under a two-record verification budget, with supersession by a newer
  authoritative record; stale-consistent decisions in **77.3 / 74.7 / 74.7 %**
  across a primary run, a fresh-wording replication and a held-out domain.
  No independent-source arm, no lexical manipulation, as recorded. It does
  **not** close S-E on its own.
- **"No LLM-subject continued-influence-effect paper exists on arXiv"** —
  survives this pass. Web search returns human-subject CIE work and LLM
  misinformation-susceptibility work, but no CIE study with LLMs as subjects.

## Newly surfaced, partial

- **arXiv:2606.01637** — *Easier to Mislead Than to Correct: Harmful and
  Beneficial Revision in LLM Conformity* (Qu, Fu, Hu; 1 Jun 2026). Four
  open-weight LLMs, seven QA datasets; manipulates **consensus structure and
  authority labels**; peer agreement makes it far easier to mislead a correct
  model than to correct a wrong one, and authority labels move the model
  regardless of correctness. Adjacent on the source/authority axis; no
  same-root-vs-independent-root retraction, no overlap manipulation.

## Recommendation — the author's call, not the gate's

**Retire S-E.** What remains is the behavioural pairing itself: a same-root
retraction against a content-matched independent-root contradiction, in a
two-speaker dialogue, on 3B deciders, on the frozen clusters. Nobody has run
exactly that. But every component is published — repetition-beats-source
(2601.03746), source-gates-correction (2606.05976), overlap-raises-probability
with a size gradient and head-level cause (2606.24077) — and "every component
published, the combination unrun" is the bar this programme set for itself and
has now failed to clear eight times out of eight.

**With S-O retired and S-E recommended for retirement, the 2026-09-03
reopening has no live candidate.** S-A, S-B, S-L and E16-C were parked for
weaker reasons and carry the same no-web-search caveat; none was rated better
than these two. The honest next artifact is the negative-results write-up in
`docs/RESEARCH-LEAD-2026-09-02.md` §8-9.

## Housekeeping

`docs/novelty_matrix.md` row C1 cites arXiv:2601.03746 for a different claim.
Its finding is now **also** the pre-emption for S-E's mechanism; the row
should say so. Not changed here — it is a frozen-adjacent doc and the edit is
the author's.

Minor: arXiv:2606.05976's v1 title appears as *The Self-Correction Illusion:
LLMs Correct Others but Not Themselves*; the current abs page reads *Role
Relabeling Gates Explicit Error Flagging in Large Language Models*. Same
paper, retitled between versions.

## Limits of this pass

Same as the S-O re-gate and no better. **Abstract-level only, no full text.**
Load-bearing IDs (2601.03746, 2606.05976, 2606.24077, 2608.25553, 2606.01637)
each confirmed by fetching the arXiv abstract page. The remaining IDs from the
2026-09-03 S-E row (2604.00892, 2506.08184, 2606.27472, 2609.01852,
2607.12893) were **not** re-verified this pass. No model calls were made.


---

# CITATION AUDIT — 2026-09-06 — the 2026-09-03 gate's sources, checked

Two label errors had already turned up (arXiv:2601.03746 "illusory truth",
arXiv:2604.24512 "Attention Latch"). Both re-gates recorded, as a limit, that
the remaining IDs in the S-O and S-E rows were never re-verified. They have
now been checked — eight of them, by fetching the arXiv page.

| cited as | ID | verdict |
|---|---|---|
| *MeetingProbe* | 2608.20392 | **label wrong, substance right** |
| RefuteBench 2.0 | 2502.18308 | confirmed, including "forgetting direction only" |
| AgentChangeBench | 2510.18170 | title/authors confirmed; "additive, no cancellation" **unverified** |
| InterruptBench | 2604.00892 | retraction arm confirmed; **"frontier only" is WRONG** |
| PI-LLM | 2506.08184 | confirmed |
| *Supersede* | 2606.27472 | confirmed |
| *Memory Trust Gap* | 2609.01852 | confirmed |
| MemOps | 2607.12893 | confirmed |

## The one that matters — InterruptBench

**arXiv:2604.00892** is *When Users Change Their Mind: Evaluating
Interruptible Agents in Long-Horizon Web Navigation* (Henry Peng Zou and 18
co-authors, 1 Apr 2026). It builds InterruptBench from WebArena-Lite with
**"three realistic interruption types, including addition, revision, and
retraction"**, and evaluates **"six strong LLM backbones"**.

The S-E row recorded it as "same-user retraction arm, **frontier only**". The
retraction arm is right; *frontier only* is not — the evaluation is not
restricted to frontier or closed models. The 2026-09-03 gate therefore
**understated** how close this paper sits to S-E. It is a further reason to
retire S-E, not a lesser one.

## The one that looked worse than it is

**arXiv:2608.20392** is *Evaluation-as-Search: Adaptive Discovery of Grounding
Failures in Meeting Assistants* (Khairy, Hosseinkashi, Gopal, Cutler, 30 Jun
2026), not "MeetingProbe". Its **abstract does not contain** the figure this
repository attributed to it, and on an abstract-level check the citation
looked invented. It is not. The full text carries it in Table 9, Appendix H:
**"Overstated decision finality — 141 — 13.4 %"**, defined as presenting
"an outcome as explicitly decided or agreed upon when the transcript shows
only tentative discussion or unresolved deliberation", one of eight
grounding-error categories. The substance recorded on 2026-09-03 is correct.

*This is a caution about the two re-gates above, which were abstract-level.
An abstract-level check can make a sound citation look unsound. Nothing in
those verdicts rested on a missing figure, but the limit is real.*

## Also noted

**arXiv:2609.01852** (*The Memory Trust Gap*, Hu & Ramachandran, 1 Sep 2026)
tests **Qwen3 0.6B–8B** and finds smaller models rely on stale facts while
**larger models fail catastrophically** once stale content carries
contemporary markers — "removing a label amplifies over-trust at every size,
and a recency feature fools the larger models harder". Any future design in
this space that assumes an effect simply "shrinks with size" should read this
first; the size relation is conditional, not monotone.

## Standing

Of eight sources checked: six clean, one label-only error, one substantive
mischaracterisation, one characterisation still unverified. Adding the two
already known, the 2026-09-03 gate carries **three label errors and one
substantive error across its citations** — its *identifiers and substance are
largely sound*; what failed was its **verdicts**, for want of web search. Those
are separate failures and the record should not conflate them.

Not corrected in place: `docs/novelty_matrix.md` and the 2026-09-03 verdict
table above are left as written, with these corrections appended. Editing the
originals is the author's call.


---

# ADDENDUM — 2026-09-06 — S-E's behavioural half closes too

The citation audit above turned up a paper the S-E re-gate had not reached.
It is the closest thing in the literature to S-E, and it closes the half the
re-gate had left as a "narrow residue".

**arXiv:2607.05545** — *Most LLM Conformity Needs No Speaker: Measuring the
Speaker-Free Floor in Peer-Pressure Benchmarks* (Yibo Hu, Jiaming Qu,
6 Jul 2026; same group as arXiv:2606.01637).

It states S-E's confound in S-E's own terms:

> "standard conformity prompts mix two cues at once, the presence of a speaker
> and the repeated wrong answer itself. Existing benchmarks vary these cues
> together, so they cannot tell how much of the revision actually depends on
> the speaker."

and then resolves it with the design S-E was going to build:

- a **no-source condition** — the same asserted answer with the explicit
  speaker removed — across **six open-weight LLMs** and seven datasets;
- that condition alone produces harmful revision in **66.5 %** of initially
  correct cases against **10.3 %** under a plain re-ask;
- **"the effect also remains when the repeated answer is paraphrased"** — a
  lexical-overlap manipulation, which the 2026-09-03 row listed as the thing
  S-E still needed ("needs an overlap manipulation (hi / lo)");
- source framing **modulates** the floor rather than producing it: "Source
  attribution still matters, but it should be measured as an increment above
  this speaker-free floor."

Its stated methodological lesson is S-E's hypothesis: *"without this step,
benchmarks may mistake repeated text for social influence."*

**S-E is therefore closed on both halves, not one.** What is left is the
framing alone — a two-speaker incident dialogue, a retraction of a proposed
constraint, 3B deciders on the frozen clusters. The content-matched
same-source-versus-independent-source contrast that was S-E's remaining
distinctness is subsumed by the speaker-free-floor design, done on open
weights with a paraphrase arm.

| S-E half | 2026-09-03 | 2026-09-06 re-gate | this addendum |
|---|---|---|---|
| mechanism | OPEN (NARROW) | CLOSED | CLOSED |
| behavioural | OPEN (NARROW) | NARROW residue | **CLOSED** |

## Correction carried over from the audit

**arXiv:2510.18170 (AgentChangeBench)** was recorded on 2026-09-03 as
"additive shifts, no cancellation". The full text shows goal shifts are
**sequential replacement** — `goals: [g1, g2, ... g{k+1}]`, one active goal at
a time, each superseding the last — evaluated on GPT-4o, Claude-3.7-Sonnet and
Gemini-2.5-Flash, with Qwen2.5-14B-Instruct in a single-run appendix.

"Additive" is wrong. The operative distinction for S-O nevertheless survives:
AgentChangeBench always supplies a **successor** goal, whereas S-O's case was a
constraint **rejected and never replaced**. Wrong word, right conclusion — and
S-O is retired regardless.

## Standing after the addendum

Both candidates of the 2026-09-03 reopening are closed by prior art, and each
was closed by a paper the original gate could not see because it had no web
search. Nothing is queued. The recommended artifact remains the
negative-results write-up (`docs/RESEARCH-LEAD-2026-09-02.md` §8-9).


---

# MEASUREMENT CANDIDATES N-1/N-2/N-3 — GATED 2026-09-06 — none clears

After both behavioural candidates died, the search moved from *behaviour* to
*measurement*, on the reasoning that the behavioural space (small model,
multi-turn dialogue, constraint) is the most heavily worked area of 2026 and
this repository's real asset is a frozen, verified instrument. Three
candidates were formed from the menu diagnostic's own data and gated with web
search **before any model call**.

| candidate | claim | verdict |
|---|---|---|
| **N-1** | constraint-adherence rates are pinned to menu chance \|plan\|/\|action space\|, so a benchmark's pass/fail verdict flips with action-space size | **SURROUNDED** — core unfound, every component published |
| **N-2** | the sign of an explicit-rejection effect flips with action-space size | unfound, but evidence is one decider, +0.062, post-hoc, unpermuted |
| **N-3** | reported model-size effects in constraint adherence are output-length artefacts | **PRE-EMPTED** |

## N-3 is pre-empted

**arXiv:2608.17183** *Benchmarking the Benchmarks: Evaluating Automated Safety
Benchmarks for Small Language Models* (Shaik, Li, Luo, 17 Aug 2026), 26
open-source SLMs: ambiguity rate "increases with lexical density, output
perplexity, and output length", named a **capability-safety confound that
mixes model capability with apparent safety**. And **LabSafety Bench**
(arXiv:2410.14182) already ran the decisive experiment — more verbose models
generate more candidate hazards and so match ground truth more often, and
**when output constraints were applied the performance inversion disappeared**.
That is N-3's mechanism and N-3's control, published.

## N-1 is surrounded

Nothing found states the claim. Everything it is built from is published:

- **numerator** — the verbosity confound above;
- **denominator** — tool-catalog size degrades selection and shifts scores
  (practitioner literature; τ-bench uses 13–15 APIs, and the recommended
  protocol is already "small-catalog baseline, grow the catalog, realistic
  semantic distractors, stable cases" — which is this diagnostic's design);
- **genre** — benchmark-validity audits are active: **arXiv:2607.02577**
  (*Benchmarking the Benchmarks: A Validity Audit of Tool-Calling Evaluation*,
  18.5 % evaluator-human misalignment, an 18.9-point spread across identical
  reruns "large enough to flip leaderboard conclusions") and
  **arXiv:2605.10448** (*Can Agent Benchmarks Support Their Scores?*).
- **adjacent, does not fire** — BiasBusters arXiv:2510.00307 is *which* tool is
  chosen (position/metadata), not how many; arXiv:2406.11634's "base-rate
  effect" is MMLU answer-label priors; arXiv:2608.24569 (*When "Must" Becomes
  "Maybe"*) varies compression, not action-space size; arXiv:2604.28031
  (*Models Recall What They Violate*) is a recall/adherence dissociation with
  no chance baseline and no option-set scaling.

**By this repository's own bar — "every component published, the combination
unrun" is not novelty — N-1 does not clear.** That is the bar that killed
E16-A–D, S-A, S-B, S-L, S-O and S-E. It is not moved for a candidate generated
in-house.

## The one component that was NOT found

**Elasticity.** \|plan\| is *endogenous* to \|vocab\|: doubling the menu from
6 to 12 identifiers cut per-item chance by only ~22 % (qwen 0.592 → 0.455) and
~21 % (llama 0.705 → 0.559), not 50 %, because the model lengthens its plan in
response (×1.54, ×1.59). The consequence is that **the obvious remedy —
normalise the rate by action-space size — does not work**, because the
numerator moves with the denominator. No source in this pass states that.

Evidence for it is currently three menu sizes and two deciders (plus one
14B point at \|vocab\| = 6), all from one corpus, with \|plan\| never
controlled. That is not enough to carry it, and the honest next step is not to
write it up but to **establish it or kill it**: a pinned-length dose-response
(`docs/protocols/E17-menu-law.md`), which is also the follow-up the menu
diagnostic already named. If pinning \|plan\| by instruction restores clean
1/\|vocab\| scaling, the mechanism is causal and the elasticity claim has a
basis; if it does not, the whole line dies and that is recorded.

**No candidate is preregistered. No claim exists. Zero model calls were made
for this gate.**
