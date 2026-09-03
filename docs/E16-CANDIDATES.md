# E16 candidates — programme reopened 2026-09-03

**Status: CANDIDATE SEARCH COMPLETE (2026-09-03). Lead candidate S-O
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
