# FFEP — Falsification-First Evaluation Protocol — feasibility audit

**Written 2026-09-02 at commit 3b6a141 + feasibility files. No model was
called. No E15/E16 outcome exists. Frozen E1–E14 artifacts untouched
(every hash re-verifies; 167 VERIFIED / 0 MISMATCHED).**

Gemini's external review retired E15-PODT and proposed a metascientific
pivot: claim-relative counterfactual auditing of LLM-agent evaluations. This
document tries to destroy that pivot before an inference is spent on it,
under the repository's own standards. Its machine-readable companions are
`docs/ffep_inventory.json` (what the artifacts contain),
`docs/ffep_catalogue.json` (every procedural counterfactual the frozen
formal representation can produce, with its validator report),
`ffep_mutations.py` + `test_ffep_mutations.py` (the generator, the validator
and the validator's own falsification tests, 12 passing), and
`ffep_power.py` (attainability).

---

## 1. What the repository actually contains — the sampling inventory

"167 verified" is **167 recomputations that matched a pinned value**, one
`[ OK ]` line each. Classified by what each line checks
(`docs/ffep_inventory.json`, keyword classification, `by_category`):

| verifier line type | count | what it is |
|---|---|---|
| statistical recomputation (rates, differences, p, CI, paired counts) | 100 | a number a document reports, re-derived from raw plan text |
| structural (hash, count, byte-identity, manifest, parse rate) | 28 | the frozen design is what it says |
| control / null policy (echo, empty, source-truster, latest-truster, gates) | 13 | a control that could fail did not |
| other | 26 | mixed descriptions |
| SKIP / UNVERIFIABLE | 4 | E1/E2/E4 scored against earlier corpora; E14 has no outcomes |

**None of the 167 is an agent trajectory.** The trajectories are elsewhere:

| quantity | value | source |
|---|---|---|
| raw model responses stored (`plan_text`) | 7 344 rows; ≈ 7 020 unique (E2's detail file is stored once merged and once chunked) | `results/*.json` |
| (experiment, model) runs with raw output | 22 | inventory `experiment_runs` |
| deciders | 5 local (llama-3B, aya-8B, qwen-3B/7B/14B) | |
| task instances, frozen | **36** = 6 domains × 6 graphs (a crossed design, not 36 independent draws) | `lineage_bench.all_instances()` |
| task instances, generated and never run | 144 (E14 salts) | `lineage_e14.fresh_instances()` |
| propositions (instance, `before` constraint) | 108 in E12/E13 | `lineage_e12.all_units()` |
| conditions | E2 9 exposures; E10 9 arms; E11 10; E12 4; E13 10 cells; E4 4–6 rule variants | |
| repeated runs of the same prompt | E13 `default` is a byte-identical re-run of E12 `same_root`/`indep_root` (108 × 2 prompts) | E13 protocol §2 |
| clusters (the sampling unit every interval and test actually uses) | **36 instances** | E12 protocol §2 |
| successful trajectories, full deterministic evaluator (zero violations ∧ ready) | E2 15/324, E4 44/792, E12 8/864, E13 3/1080 — because E10–E13 prompts show one constraint's messages, full-instance success is not their endpoint | inventory `full_evaluator_pass_zero_violations_and_ready` |
| successful trajectories, the experiments' own endpoint (held the corroborated ordering = `source`) | E12 llama 406/862; E13 llama 751/1080; E11 aya 200/360, llama 203/360, qwen-7B 140/360 | inventory `scored_verdicts` |

**The real eligible pool for a claim-relative audit is therefore not "167"
and not "7 000".** It is the set of (instance, claim-target) pairs on which
(a) a valid discriminating counterfactual exists (§6) and (b) the agent
passed the original target. On the frozen 36 instances that is at most
100 targets for the prerequisite claim and 35 for the authority claim (§6),
before conditioning on original pass; the procedural generator can enlarge it
by salts (144 instances exist unrun).

## 2. The precise scientific question

> How often does an apparently successful agent evaluation identify the
> capability its authors attribute to it — as opposed to a simpler policy
> that produces the same success on the original items?

Operationally: for a capability claim P attached to a benchmark success,
does a minimal, validity-preserving counterfactual on which P and a named
shortcut S predict different outputs show the agent following S?

## 3. Metric claim versus capability claim

- **Metric claim** M: on task distribution D with scorer f, the agent's
  success rate is r. A counterfactual result never makes M false; r was
  observed.
- **Capability claim** C_P: the agent's success is produced by policy
  property P (e.g. *reads the stated prerequisite and orders accordingly*).
- **Shortcut** S: a policy property that (i) also yields success on D at the
  observed rate — observational equivalence on the original — and (ii) does
  not have P (e.g. *emit the identifiers in the order the prompt lists
  them*; *follow the most recent statement*; *emit a fixed domain-plausible
  order*).

A failed counterfactual shows that **E = (D, f) did not distinguish P from
S**, i.e. the original evidence for C_P was also evidence for C_S. The
metric stands; the attribution is underdetermined.

## 4. Formal definition of claim identification

Let π be the agent's input→output map, D the original item distribution,
f the deterministic scorer. Define the hypothesis classes 𝒫 (policies with
P) and 𝒮 (policies with S but not P). E **identifies P against S** iff
∃ x ∈ supp(D) with f-relevant outputs π_P(x) ≠ π_S(x) for all π_P ∈ 𝒫,
π_S ∈ 𝒮. If no such x exists, the likelihood ratio of the observed success
under 𝒫 versus 𝒮 is 1 and E carries **no** evidence between them.

A **discriminating counterfactual** for (x, P, S) is x′ = δ(x) with δ a
minimal intervention such that (1) exactly one formal property differs;
(2) all other formal properties are preserved; (3) 𝒫 and 𝒮 predict
different f-relevant outputs on x′; (4) f(x′) is mechanically known;
(5) x′ is solvable; (6) δ is visible to the agent; (7) no lexical artefact
reveals the answer. **Eligibility:** claim C_P is testable by this method
against S iff such a δ exists and passes (1)–(7) mechanically; otherwise the
verdict is UNTESTABLE-BY-METHOD and the claim is not forced.

Outcome per eligible unit with original pass: π(x′) ∈ 𝒫-consistent,
𝒮-consistent, or neither. The method's report is the paired pattern, not a
pass rate.

## 5. Development set — could a claim-relative audit have caught our own failures?

Strict rule: a behavioural counterfactual gets credit only if the failure is
a behavioural confound or a shortcut, the discriminating intervention is
constructible from the formal representation, and the shortcut would have
had to be in the audit's hypothesis library. Statistical, replication and
prior-art failures are outside the method unless the audit includes those
components — it does not.

| historical claim | failure type | counterfactual-detectable? | minimal discriminator | why | false-positive risk |
|---|---|---|---|---|---|
| E2 v1: echoing the printed identifier order scored 36/36 in every condition | leakage / construct invalidity | **yes** | permute the printed order (`echo` ≠ `P`) | S = echo is an executable policy; the intervention is one property; our validator's check 7 is exactly this | low, mechanical |
| `supersession_respected` = 1.0 for an empty plan | scorer bug | no | — | an evaluator property test, not a behavioural counterfactual | — |
| `source_truster` baseline at 36/36 (overrides deleted, not reversed) | construct invalidity (benchmark rewards the reflex) | **yes** | S = source-truster passes every item → E cannot identify P against S; step 2 of the protocol flags it before any run | that is the protocol's own eligibility test | low |
| SUPERSESSION classifier: `changed\|now` regex scored 36/36 vs 0/468 | lexical leakage | partial | n-gram separability gate (validator check 7) | a lexical audit, not a behavioural one; caught only if the leakage check is part of validation | low |
| BM25 "inversion" = recency (89 % scores exactly 0.0) | retrieval artefact | partial | permute message order, content fixed: relevance-selection invariant, recency-selection changes | claim-relative on the selector, not the agent; needs the recency shortcut in the library | low |
| E4b: "restriction increases revision-following", 5/5 models, p = 0.031 | behavioural confound (speaker labels / unanimity) | **yes** | remove or permute speaker labels | the speaker-free control that killed it is this counterfactual; needs S = "reacts to speaker cues" in the library | medium: depends on library coverage |
| E5 step function, twice | statistical (p = 1.0 read as plateau; corpus change) | no | — | needs a statistical audit | — |
| E7 P2 "length does nothing"; dilution large → moderate → absent | confound (E9) then replication instability | partial | E9's 2×2 (filler vs restatement, speakers fixed) | the confound was found by a counterfactual; the instability across corpora is a replication fact no single counterfactual detects | — |
| E7/E5 identification: corroboration collinear with self-reversal (36/36) | behavioural confound | **yes** | fresh contradictor (E9) | textbook case: P = corroboration, S = "contradictor discredited himself", divergence on one property | medium: S had to be imagined; an adversarial audit, not a gate, found it |
| Mode B corpus v1 dropped 5/36 silently | pipeline error | no | — | data-integrity audit | — |
| E10 "zero weight" reported against its own preregistered output; power 0.14 | statistical | no | — | prospective power, not counterfactuals | — |
| E13 "measures disagree / response bias" | analysis asymmetry | no | — | one variable scored two ways | — |
| E13 "normative degrades recognition" | statistical (one row of two, no test) | no | — | — | — |
| E12/E13 "prices it at nothing" (the `ready` field never scored) | endpoint failure (unmeasured output channel) | no by counterfactual; partial by an output-channel inventory | score every output field | not a counterfactual; a completeness audit | — |
| readiness read as dependence | construct invalidity | **yes** for the construct; no for model-specificity | add one identical citation vs add one distinct citation (E11's nested prefixes) | the dose family discriminated repetition from dependence; the llama-specificity needed a second decider | medium |
| normative backfire generalises | model-specific artefact | no | — | cross-decider replication | — |
| E3 latest-truster (a success, not a retraction) | — | **yes** | word-identical revision, speaker swapped (`mixed`) | the method working by hand: it identified S = latest-truster | low |
| C1/C4/C8/C11–C13 pre-empted | prior-art failure | no | — | — | — |

Tally over the 17 failures: **5 yes, 3 partial, 9 no.** The method covers
the behavioural-confound third of this project's mistakes and none of the
statistical, replication, endpoint or prior-art two thirds. Two of the five
"yes" cases needed a shortcut hypothesis that a library would have had to
contain in advance. Construct validity is therefore **real but narrow**: the
method is a systematiser of control design, not a substitute for the
statistical apparatus that caught the costliest errors.

## 6. Candidate counterfactual families on the frozen formal representation

Built and validated over all 36 instances, no model (`ffep_mutations.py`,
`docs/ffep_catalogue.json`):

| family | intervention | candidates | constructed | pass all 7 checks | discriminates a named non-trivial shortcut | fails closed on |
|---|---|---|---|---|---|---|
| `reverse_before` | reverse one `before` edge; re-render every message about it with the **same template**, verbs swapped; everything else byte-identical | 120 | 120 | **100** in 36/36 instances | 67 (echo 49, mention 39, latest-truster 2) | 9 cycles in the effective set; 11 where the printed order would solve the mutant (leakage) |
| `deauthorise_supersession` | the legitimate override is delivered by a non-authorised speaker; text byte-identical, only the lineage label (hence speaker) and the lifted set change | 36 | 36 | **35** | 35 (latest-truster 33, mention 22, echo 20) | 1 leakage |
| `swap_source_positions` | exchange two SOURCE messages of equal speaker parity; texts, speakers, derivation order preserved | 762 | 249 | 249 | **5** (mention only) | parity, derivation order; and the family rarely changes any shortcut's prediction — **useless, and the validator says so** |
| `required` family (drop/add/swap a required action) | — | — | — | — | — | **no discriminator exists**: the only shortcut that passes `required` items is "include every action", and no item ever penalises inclusion. UNTESTABLE-BY-METHOD, correctly |

The "memorised" shortcut (a fixed plan regardless of stated content) is
discriminated by every edge reversal by construction; it is meaningful only
as "content-blind domain-prior ordering", which should be written as an
executable policy (the authored action order) before it counts.

## 7. Validity requirements, as implemented

`validate()` checks: target changed; every non-target constraint, message,
identifier list, setting and instruction byte-identical; effective
constraints acyclic and a valid plan exists; the mutated message is in the
exposed set; the printed identifier order does not itself solve the mutant;
no duplicated message; each shortcut policy passes the original target and
fails the mutant target. `test_ffep_mutations.py` proves the validator can
fail: a cycle-closing reversal, a tampered unrelated message, a leaky
printed order, a hidden mutation and a cyclic ground truth are all
rejected, and a shortcut that adapts to the mutation (mention order under an
edge reversal) is reported as *not discriminated*. Ground truth is never an
LLM.

## 8. Closest prior art

Two independent adversarial reviewers (one on software-testing and NLP
behavioural-testing lineages, one on agent-evaluation validity and public
tooling), about 70 queries and 100 papers/repositories read. The session's
web-search budget was exhausted mid-review; the second reviewer worked from
the arXiv export API, the GitHub search API and direct fetches, and three
queries (WebArena-, SWE-bench- and fail-closed-specific) were rate-limited
and never answered. Component key: 1 claim-first; 2 named shortcut; 3 minimal,
validated counterfactual; 4 re-execute; 5 mechanical check; 6 identification
linkage; 7 fail-closed.

| work | what it does | components |
|---|---|---|
| **Mystery Blocksworld** — Valmeekam et al. 2023, arXiv:2305.15771 (PlanBench 2206.10498; Corrêa et al. 2511.09378) | "LLMs can plan" → shortcut named (pattern matching on names) → rename actions/predicates only, formally identical to a planner → re-run → VAL → "likely connected to pattern matching rather than reasoning"; 210/600 → 1/600 | **1 2 3 4 5 6** |
| **Reasoning or Reciting** — Wu et al. NAACL 2024, arXiv:2307.02477 (MIT repo) | general-reasoning claim → "narrow, non-transferable procedures" → one default assumption changed → a Counterfactual Comprehension Check validates the variant → exact match → "not sufficient evidence" | **1 2 3(validated) 4 5 6**, not agents |
| **Counterfactual Evaluation Reveals Hidden Capability Profiles** — Turk 2026, arXiv:2605.30590 | clinical LLMs and ReAct agents; pre-registered single-attribute regex mutations, otherwise byte-identical; the constant-output shortcut named; underdetermination argued; **LLM judge** scores; no-op mutations silently dropped | 1 2 3 4 6, not 5, 7 inverted |
| **MemoryPolicy-Bench** — arXiv:2608.17247 (Aug 2026) | byte-identical task families varying only the semantic relation; deterministic reference policies; a named lexical shortcut (TF-IDF at 89.6 %) | 2 3 4 5 6(partial) |
| **ImpossibleBench** — Zhong, Raghunathan, Carlini, arXiv:2510.20270 (MIT, Inspect) | SWE-bench / LiveCodeBench with one test perturbed or made conflicting; a pass is a spec violation by construction | 2 3 4 5 on real agent benchmarks |
| **HackDetect / Protocol Validity** — Shao et al., arXiv:2607.22368 (Jul 2026) | "a benchmark score supports a capability claim only when the evaluation protocol keeps that capability necessary for success"; five exposure sources; an attribution abstention rule; no re-execution | **1 2 6 7(partial)** |
| **Epistematics** — Kalaitzidis, arXiv:2605.14167 | a four-step claim procedure with a "discriminative condition" per claim ("fails the discriminative validity test if a system lacking the target mechanism can satisfy it"); conceptual, no execution | 1 2 3(conceptual) 6 |
| **Auditing Discovery Claims** — Chen et al., arXiv:2608.00981 | matched-budget baselines, solver ablations, a certified negative side "bounded exactly, offline, before any run" | 2 4 5 6 **7** (one domain) |
| **HANS** — McCoy, Pavlick, Linzen ACL 2019 | three executable heuristics; a set where each predicts the wrong label | 2 3(divergence) 4 5 6(qual.) |
| **Contrast sets** — Gardner et al. 2020; **CAD** — Kaushik et al. ICLR 2020; **CheckList** — Ribeiro et al. 2020 | minimal edits that flip the label; INV/DIR tests with programmatic expectations | 3 4 5 (6 partial) |
| **Variant-benchmark family** — GSM-Symbolic, functional benchmarks, MATH-Perturb, RE-IMAGINE, AIW, Ullman 2023, Embers of Autoregression, Lewis & Mitchell | perturbations that separate memorised procedures from general ones; several with explicit prior-claim attacks | 2 3 4 5, some 1 and 6; none 7 |
| **Agent-benchmark exploit line** — BenchJack 2605.12673, Terminal Wrench 2606.08960, SpecBench 2605.21384, BAITBENCH 2608.30724, Agent-ScanKit 2510.00496, SWE-bench+ / PatchDiff / SWE-Bench Illusion | discovered or planted shortcuts on existing agent benchmarks; sensitivity, not directional identification | 2 4 5 |
| **Metamorphic lineage** — METAL 2312.06056, MORTAR 2412.15557, LLMORPH 2603.23611, ReliabilityBench 2601.06112, Semantic Invariance in Agentic AI 2603.13173 | relation templates, mostly invariance; ReliabilityBench has action MRs with end-state equivalence on tool agents | 3 4 5 |
| **Tooling** — checklist, promptbench, giskard, langtest, inspect_ai, promptfoo, WindTunnel ("capture → perturb → diff", mechanical), plumbline (metamorphic conformance with a semantic-equivalence guard), anti-luck-eval ("paired-world invariants", Aug 2026), agent-eval-labs (UNDETERMINED as a first-class outcome, reliability) | perturbation harnesses; none claim-indexed; fail-closed exists only as fragments | 3 4 5, fragments of 7 |
| **Prescription** — Ivanova, arXiv:2312.01276 | "identify alternative strategies … design control conditions to help distinguish these possible strategies" | 1 2 3 5 stated verbatim |

**Strongest killers.** For the procedure: Mystery Blocksworld (2023) runs
components 1–6 with a deterministic validator on a planning claim, and
Reasoning or Reciting adds the validity gate. For agents: Turk 2026 runs
1–4 and 6 with pre-registered byte-identical mutations, conceding only the
LLM judge; ImpossibleBench runs 3–5 on SWE-bench. For the identification
framing: HackDetect states the principle verbatim with an abstention rule.
The field converged on this framing in 2026 (Turk May, Epistematics May,
BenchJack May, HackDetect Jul, Chen et al. Aug, anti-luck-eval Aug).

**Narrowest statement neither reviewer could find.** An executable,
benchmark-agnostic pipeline for tool-using agents in which the shortcut is
written as a policy that reproduces the original pass, the single-property
counterfactual's minimality and P/S divergence are machine-certified before
any agent run, the outcome is scored deterministically, and a claim with no
valid discriminator is emitted as a first-class UNTESTABLE verdict. Both
reviewers call that residue **methodological packaging**, "a systems
contribution, not a conceptual one".

**Also decisive from the external scan (§9):** AppWorld already ships
per-scenario *contrast sets* with a state-based validator and a
"solve-all-variants" metric — the method applied inside a benchmark by its
own authors.

## 9. External benchmark candidates

Twelve benchmarks assessed from their repositories, licences and papers by
a reviewer working from fetched sources only (third-party perturbation
literature could not be searched; "existing control" reflects the
benchmark's own paper/repo). Six strong candidates:

| benchmark (paper) | repo · licence | headline claim | evaluation | model / compute | mutable formal field | shortcut | minimal discriminator | validator | original already has this control? | integration |
|---|---|---|---|---|---|---|---|---|---|---|
| **τ / τ²-bench** (2406.12045; 2506.07982) | sierra-research/tau-bench, tau2-bench · MIT | agents' "ability to follow domain-specific rules" | DB-hash after episode vs replayed ground-truth actions, plus output substrings; deterministic; pass^k; no-user mode in τ² | user-simulator LLM (τ² any provider; no-user mode removes it); 10–30 turns, 20–60 k tokens/task; 7–14B base success likely near zero (UNVERIFIED) | `policy.md` clauses, `db.json` fields, task action lists | comply with the user via the obvious tool; never consult policy | flip one policy clause (or one DB field) so the rule outcome flips; re-derive actions; instruction unchanged | DB hash | partial: pass^k, no-user, oracle-plan, two telecom policy variants — not a single-rule flip with recomputed truth | medium |
| **BFCL** (Gorilla) | ShishirPatil/gorilla · Apache-2.0 | "call functions … accurately" | AST match vs `possible_answer`; v3 multi-turn state comparison; deterministic | vLLM/sglang; Qwen3-8B/14B, Llama-3.1-8B handlers; ~1 k tokens/item | schema `parameters`, `required`, descriptions | lexical slot-filling by parameter name/type | swap two same-typed parameter names or descriptions, or flip one to `required`; question unchanged | AST checker | adjacent: v3 miss_func / miss_param, irrelevance, v4 format sensitivity | low |
| **PlanBench** (2206.10498; 2409.13373) | karthikv792/LLMs-Planning · MIT | "plan generation … falls short" | VAL plan validator; 600 instances/domain | local hooks exist; one prompt + VAL per item | PDDL domain preconditions/effects, problem init/goal | domain-memorised macro (unstack all, rebuild) | flip one precondition in the domain; problem fixed | VAL | **yes, on the obfuscation axis** (Mystery, Randomized), unsolvable items, verification; semantic precondition flips not found | low |
| **ACPBench** (2410.05669; Hard 2503.24378) | IBM/ACPBench · CDLA-Permissive-2.0 | planning-reasoning tasks needed to "orchestrate workflows" | boolean/MCQ accuracy; Hard: per-task validators; PDDL-derived | 7–8B models evaluated in the paper; minutes | PDDL state, action, fact | lexical overlap for applicability; copy add-effects for progression | remove one precondition fact from the state; add one delete effect | PDDL grounder | partial: negatives from delete-relaxation / mutex / static facts | low–medium (generator not confirmed released) |
| **AgentDojo** (2406.13352) | ethz-spylab/agentdojo · MIT | robustness of tool-using agents over untrusted data | `utility()` / `security()` on Pydantic env state; deterministic | local / openai-compatible providers; 5–15 calls/task | `environment.yaml`, task classes | template-match the prompt to a tool, copy arguments verbatim | change one env fact so the correct argument must come from a tool result | `utility()` | different axis (benign vs attacked, defences); no minimal state pairs found | low |
| **NATURAL PLAN** (2406.04520) | google-deepmind/natural-plan · Apache-2.0 code, CC-BY-4.0 data | trip planning: GPT-4 31.1 % | exact match to a unique golden plan; deterministic | single turn, 5-shot; any local model | constraints live only in the prompt text; no generator shipped | order cities by fixed-day events, ignore the flight graph | delete/add one direct-flight edge so the unique solution changes (own CSP solver + uniqueness check needed) | `evaluate_trip_planning.py` | none | low–medium |

Also viable: ALFWorld/TextWorld (MIT; move one object in PDDL init; only
seen/unseen splits as control), BabyAI/BALROG (change the colour word with
the grid fixed), Reasoning Gym (Sokoban cell moves; no agent claim),
Planetarium (abstract/explicit variants already present). **AppWorld**
(Apache-2.0 + data clause) already contains per-scenario contrast sets and
an all-variants metric — prior art, not a target. Rejected with reasons in
the reviewer record: ToolBench, MINT, TheAgentCompany (LLM judges);
AgentBench, OSWorld, WorkArena/WebArena (infrastructure, gated data, judge
subsets); CRMArena (non-commercial licence, live org); GAIA, SWE-bench,
LiveCodeBench, Mind2Web, MLAgentBench, ProcessBench, TextArena, InterCode
(no clean formal variable, not agentic, or cost).

**Kill condition 4 does not fire**: at least six external benchmarks expose
a formal, mutable field with a deterministic validator. Two would be tried
first — τ²-bench (the claim is literally rule-following; the validator is a
DB hash; the closest existing control is not a single-rule flip) and BFCL
(lowest integration cost; strong local-model support; must be positioned
against miss_param/miss_func). The honest caveat on both: 7–14B agents may
pass too few originals to leave an eligible pool.

## 10. Proposed estimand

For target type "single ordering edge" a plan either obeys the stated order
or its reverse (a missing action is the only "neither"), so **a content-blind
fixed policy passes the original at chance and is invisible in any aggregate
pass-rate difference**. The estimand must be conditional and paired:

> **CAR** (Counterfactual Adaptation Rate) = P(plan obeys the *mutant's*
> stated order | plan obeyed the *original's* stated order), over eligible
> units; **SPR** = 1 − CAR is the Shortcut Persistence Rate for a
> content-blind S.

Predictions (mixture model, `q` = shortcut share, `r` = capability
conformity per call): pure P → CAR ≈ r; pure content-blind S → CAR = 0;
random agent → CAR = 0.5 with r = 0.5. Simulated (4 000 reps):

| r | q | expected CAR | expected drop below r |
|---|---|---|---|
| 0.70 | 0.1 / 0.2 / 0.3 / 0.5 | 0.65 / 0.59 / 0.54 / 0.41 | 0.05 / 0.11 / 0.16 / 0.29 |
| 0.85 | 0.1 / 0.2 / 0.3 / 0.5 | 0.80 / 0.74 / 0.68 / 0.54 | 0.05 / 0.11 / 0.17 / 0.32 |

Primary contrast: CAR − r (paired, per unit, instance-level permutation and
bootstrap as E12). Reading: identification supported if the CI on CAR − r
lies inside ±SESOI; underdetermination if CAR − r < −SESOI with CI excluding
0; inconclusive otherwise. For the authority claim (latest-truster S) the
outcome is not binary-symmetric and the simpler π_S framing of `ffep_power.py`
applies. Names are provisional until the estimand is preregistered.

## 11. Prospective sample size

From `ffep_power.py` (exact Clopper–Pearson) and the simulation above, with
clusters = instances and a design effect 1 + (m − 1)·ICC:

- 95 % interval width on a proportion near 0.2: 0.28 at n = 36, 0.16 at
  n = 108, 0.11 at n = 216, 0.09 at n = 324.
- To **detect** a shortcut share q ≈ 0.3 (CAR drop ≈ 0.16) at SESOI 0.15:
  simulated interval half-width at n_eligible = 144 is ≈ 0.10 → adequate;
  q ≈ 0.2 needs n_eligible ≳ 200; q ≈ 0.1 is below any reasonable SESOI.
- To **bound** π_S < 0.10 (identification supported): effective n ≥ 216
  when the truth is 0.02, ≥ 324 when it is 0.05.
- Eligible n = valid targets × original pass rate: on the frozen 36
  instances, prerequisite claim ≈ 100 × 0.7 ≈ 70 units in 36 clusters
  (n_eff ≈ 45–60 at ICC 0.3–0.5); authority claim ≈ 35 × 0.8 ≈ 28 units.
  **The frozen corpus supports detection of a large shortcut share only;
  bounding needs 4–8 salts of fresh instances (≈ 1 000–2 000 calls per
  decider).** Attainable, not cheap.

## 12. Strongest alternative explanation of a positive result

That the mutant is simply harder or out of distribution, so failures are
ordinary fragility rather than shortcut-following (kill condition 5). The
design answers it only if the outcome is scored as S-consistent versus
neither, S is an executable policy named before the run, and the CAR is
compared against the agent's own original conformity r rather than against
1. For binary edge targets "neither" cannot occur, so fragility and
shortcut are separable only through the *sign* of the paired change and
through a second, independent shortcut family agreeing. This is the method's
weakest joint and must be stated as such.

## 13. Cheapest decisive experiment (not authorised, not preregistered)

A construct-validity run, not a finding: on the frozen 36 instances,
(a) `deauthorise_supersession` × 35 targets as a **positive control** — E3
already established by hand that small deciders follow S = latest-truster,
so the method must reproduce that (a miss kills the method);
(b) `reverse_before` × 100 targets for the prerequisite claim with S ∈
{echo, mention, domain-prior} as the first genuine audit. Two deciders with
non-degenerate ordering conformity (llama-3B, qwen-7B). About 2 × (35 + 100)
× 2 = 540 calls. Endpoint CAR − r per claim, SESOI 0.15, instance-level
inference, checker-gated. It would establish whether the method can be run,
not that it is publishable.

## 14. Exact kill criteria, applied

| # | condition | status |
|---|---|---|
| 1 | closest prior art already performs essentially the same claim-relative counterfactual identification | **fires.** Mystery Blocksworld (2023) performs components 1–6 with a deterministic validator; Turk 2026 performs 1–4 and 6 on tool-using agents; HackDetect states the identification principle with an abstention rule; AppWorld ships contrast sets. What remains is packaging. |
| 2 | the formal representation cannot produce valid minimal discriminators | **does not fire**: 100 + 35 validated discriminators; two families fail closed correctly |
| 3 | historical known confounds not detectable by the method | **fires partially**: 5 of 17 failures detectable, 3 partial; the behavioural-confound class is covered, statistical/replication/endpoint/prior-art classes are not |
| 4 | no meaningful external benchmark can be integrated | **does not fire**: six candidates with formal mutable fields and deterministic validators (§9). |
| 5 | the method only produces ordinary adversarial examples | **live weakness**: for binary targets shortcut-following and fragility are separable only by sign and by cross-family agreement (§12) |
| 6 | ground truth needs subjective LLM judgement | **does not fire**: all validators deterministic |
| 7 | valid independent sample pool too small | **fires for the bounding reading** on the frozen corpus (n_eff ≈ 45–60 vs ≥ 216 needed); detection of large shortcut shares is attainable; fresh salts remove it at ≈ 1 000–2 000 calls per decider |
| 8 | the contribution collapses to generic metamorphic testing | **fires in spirit.** The three families built here are metamorphic relations with a named competitor policy; the historical audit (§5) shows the method is what this repository's own control design already did by hand in E3, E4b and E9. The delta over METAL/MORTAR/ReliabilityBench/plumbline is the claim index and the untestable verdict, i.e. systematisation. |

## 15. Novelty status

**HEAVY OVERLAP. Not NOVEL.** Both reviewers, independently, reached the
same verdict and the same residue. Every component is published; 1–6
co-occur in Mystery Blocksworld and Reasoning or Reciting; 3–5 co-occur on
real agent benchmarks in ImpossibleBench and KA-LogicQuery; 1, 2, 6 and
partial 7 co-occur in HackDetect and Epistematics; the field converged on
the framing in 2026. The residue — machine-certified minimality and
divergence, deterministic scoring, and a first-class UNTESTABLE verdict, in
one benchmark-agnostic pipeline — is a methodological packaging
contribution. Under this repository's rule, absence of a located paper for
a packaging delta is not novelty. Gemini's "highly novel" rating does not
survive.

Recorded as **C15** in `docs/novelty_matrix.md`.

---

## Decision

Kill condition 1 fires (the closest prior art performs essentially the same
claim-relative counterfactual identification, on planning in 2023 and on
agents in 2026), kill condition 8 fires in spirit (the method reduces to
claim-indexed metamorphic testing and to the control design this project
already practised), kill condition 3 fires partially (five of seventeen
historical failures detectable; the statistical, replication, endpoint and
prior-art two thirds are not), kill condition 7 fires for the bounding
reading on the frozen corpus, and kill condition 5 is a live weakness for
binary targets. Conditions 2, 4 and 6 do not fire: the formal
representation produces validated discriminators, external benchmarks
exist, and no ground truth needs an LLM. That is a method that *can* be run
and *should not* be claimed.

What is preserved: the inventory, the generator and validator with their
falsification tests, the catalogue of 135 validated discriminators on the
frozen corpus, the estimand analysis (conditional adaptation rate, not an
aggregate difference), and the attainability tables. They are correct and
reusable, and they are not a paper. No E15/E16 outcome exists; no model was
called; every frozen hash re-verifies.

**STOP_FFEP**
