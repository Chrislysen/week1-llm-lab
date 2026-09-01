# AgentCom — state of the research branch, for external review

**Purpose of this document.** Everything that happened after the "E1 accepted →
build E2 / AgentLineageBench Mode A" instruction, written so a reviewer who has
not seen the repo can judge where the work should go next. Numbers here are
machine-re-derivable: `python verify_claims.py` recomputes them from raw model
output and exits non-zero on drift (currently **51 verified, 0 mismatched, 3
unverifiable**).

Repo is local only. Branch `crazy`. Nothing pushed to any remote.

---

## 0. Standing constraints in force the whole time

- Compulsory baseline (`compulsory-baseline-v1`) is **frozen**. No stage may
  modify it. `llm_client.py` etc. are course scaffolding and are extended by
  subclassing, never edited.
- E1 artifacts frozen at `e1-landscape-v1`. **Not tuned, not rerun.**
- No method, weight, prompt, threshold or budget is tuned on scored outcomes.
- Protocol changes are amendments: documented, dated, justified by something
  found *before* scoring, and applied uniformly to every arm.
- Every stage carries a null/random control and a sabotage arm. *A control that
  cannot fail is not a control.*
- No GitHub remote. Everything local.
- Academic integrity: prior-work reuse (BM25 adapted from an earlier personal
  project, `lme_maxsim.py`) is disclosed in `docs/PRIOR_WORK.md`. **Open item:**
  the instructor has not yet been asked in writing about that reuse.

---

## 1. The instruction that started this phase, and how each clause was discharged

> *"Proceed to implement E2 / AgentLineageBench Mode A only. Do not implement
> AnchorRoute. Build an initial procedural benchmark of 36 independent
> instances… Before any large benchmark run, implement and execute benchmark
> validation only… Do not run all selectors over all 36 instances yet."*

| required | status | where |
|---|---|---|
| 6 surface domains × 6 formal constraint graphs = 36 instances | done | `lineage_bench.py` |
| ~6 actions, 6–8 constraints per instance | done | 6 actions, 6–8 constraints |
| deterministic hidden evaluator | done | `lineage_eval.py`, no LLM in the loop |
| surface forms from fixed template/paraphrase banks, **not** LLM generation | done for Mode A | `T_BEFORE_*`, `T_REQ_*`, `T_REVISION` banks |
| disjoint vocabularies across domains | done | payments / robotics / pharmacy / satellite / brewery / rail |
| lineage classes SOURCE, FAITHFUL_RELAY, CORRUPTED_RELAY, RECOVERY, DISTRACTOR, SUPERSESSION | done | all six implemented and labelled |
| paired exposure conditions: source only / corruption only / both / neither / legitimate supersession | done, **plus four more** | `faithful_only`, `source_and_faithful`, `both_recovery`, `mixed` |
| record exact presence/selection of every lineage item + final constraint obedience | done | per-instance CSV + raw plan JSON |
| retrieval authority inversion **only** from ranking among eligible source/derived pairs | done as specified | `lineage_retrieval.py` |
| decision authority inversion **only** when both representations are actually in context | done as specified | the `both` condition |
| supersession-respected rate | **implemented, then retracted, then replaced** | see §4 |
| direct-source utilization, faithful-relay utilization, corruption susceptibility, recovery rate | done | `e2` summary columns |
| validation gate before any large run | done, all 10 checks pass | `test_lineage_bench.py` |
| "do not run all selectors over all 36 instances yet" | **honoured** | selectors were never swept; E2 varies *exposure*, not selector |
| "do not implement AnchorRoute" | honoured, then it was **killed on evidence** | see §5, E6 |

**Validation gate output (current):**

```
critical controls (4):  echo 0/36, optimal 36/36, source_truster 0/36, empty 0/36
shape + satisfiability: OK      evaluator good/bad:  OK
lineage consistency:    OK      no hidden-state leakage: OK
n-gram separability:    OK      deterministic regeneration: OK
metric conditioning:    OK      exposure conditions: OK
corpus fixture:         9dd2cea16a8142c2
```

---

## 2. Instructions given after that point

Verbatim intent, in order:

1. *"Then continue working and really push yourself."*
2. *"Keep pushing."*
3. *"Keep working till you get that novel claim."*
4. *"Okay we'll continue working on the crazy idea."*
5. *"I told you to go crazy, truly go crazy and make a novel claim… it needs to
   be ambitious and crazy, look into elements of my other projects if you want
   inspiration."*
6. *"Continue"* (×2).

So after the E2 gate the direction was **open-ended: push toward a defensible
novel claim.** Everything in §3–§6 followed from that, under the §0 constraints.

---

## 3. What was built and run, in order

All experiments use local Ollama models, temperature 0, and a `Budget` cap on
every model-calling loop.

| # | experiment | question | headline outcome |
|---|---|---|---|
| E2 | AgentLineageBench Mode A (`lineage_bench.py`) | build the instrument | 36 instances, 9 exposure conditions, 216 scored calls |
| E2r | retrieval inversion (`lineage_retrieval.py`) | do selectors rank derivatives above sources? | recency 1.00, BM25 0.97, dense 0.40, fusion 0.48 mean inversion rate |
| E3 | supersession vs corruption | can the model tell a legitimate revision from a distortion? | **it cannot** — it is a *latest-truster*, not an authority reasoner |
| E4 | authority rules across 5 models (3B–14B) | does stating who may revise help? | latest-reflex holds 3B→14B; the authority rule is barely read |
| E4b | "restriction increases revision-following" | — | **retired by its own control** (see §4) |
| E5 | relay depth (`e5_depth.py`) | does a distortion travel? | corroboration reduces adoption; shape claim retracted twice |
| E6 | AnchorRoute feasibility (`e6_router.py`) | can a label-free router exploit lineage? | **killed at design stage** (see §5) |
| E7 | Mode B external validity (`e7_modeb.py`) | does E5 survive model-written relays? | all 3 predeclared predictions held |
| E8 | cross-model (`e8_crossmodel.py`) | is it a 3B artefact? | **partially run — see §7** |
| E9 | speaker 2×2 (`e9_speaker.py`) | corroboration, or a self-contradicting speaker? | corroboration survives; E7's length claim does not |

### E2 exposure matrix (36 instances × 9 conditions, Mode A)

```
condition             success  corruption adopted  decision-authority-inversion
source_only            0.0833          –                    –
corruption_only        0.0            45/72 = 0.625         –
both                   0.0                –              0.5694  (31 src / 41 cor)
neither                0.0                –                    –
supersession           0.3056             –                    –
faithful_only          0.0                –                    –
source_and_faithful    0.0833             –                    –
both_recovery          0.0278             –              0.3056
mixed                  0.1389             –              0.5278
```

Read: with the authoritative source **and** a conflicting derivative both
demonstrably in context, the model follows the derivative **57%** of the time. A
recovery message pulls that down to 31%.

### E2 retrieval inversion (mean rank of source minus derived, 108 eligible pairs)

```
selector   inversion rate   fully inverted   gap (derived − source)
recency          1.0000         36/36            −3.46
bm25             0.9722         33/36            −3.55
dense            0.3981          0/36            +0.60
fusion           0.4815          1/36            −0.58
random×20        0.5380          0/36               –
```

**Caveat already applied:** BM25's inversion is largely a *tie-break artefact* —
89% of messages score exactly 0.0, so it degenerates to recency (93.7% pairwise
agreement). This was instrumented and disclosed, not silently fixed, because the
protocol was frozen.

### E5 → E7 → E9, the line that produced the current claim

**Mode A (templated relays), n=36, `llama3.2:3b`:**
```
d1 0.7778   d2 0.6111   d3 0.4167   control 0.0000   d1_padded 0.8000
d1 vs d3  p = 0.0010          (monotone gradient)
d1 vs d1_padded p = 1.0000
```

**Mode B (relays written by `qwen2.5:7b`, certified by `qwen2.5:14b`, decided by
`llama3.2:3b`), corpus `4a2938565a36ee9f`:**
```
d1 0.7778   d2 0.1944   d3 0.1667   control 0.0000   d1_padded 0.6389
d1 vs d2         0-21   p = 9.537e-07
d2 vs d3          3-4   p = 1.0000
d1 vs d3         1-23   p = 2.980e-06
d1 vs d1_padded   3-8   p = 0.2266
d1_padded vs d3  0-17   p = 1.526e-05
```
Direction and the length dissociation replicated; **shape did not** (Mode A
gradient, Mode B step). Predeclaration was committed 5 commits *before* any
decision call, visible in git history.

**E9 (the 2×2 that identified the effect), same corpus, speaker labels are the
only manipulated variable:**
```
arm           adoption   middle messages        contradictor
d1_fresh       0.9167    none                   fresh voice
d1_self        0.8056    none                   reverses himself
d1pad_fresh    0.5278    2 irrelevant filler    fresh voice
d3_fresh       0.1944    2 restatements         fresh voice
d3_self        0.1389    2 restatements         reverses himself

d1_fresh    → d1pad_fresh   14-0   p = 1.221e-04   filler ALONE moves it
d1pad_fresh → d3_fresh      13-1   p = 1.831e-03   corroboration adds MORE
d1_fresh    → d3_fresh      26-0   p = 2.980e-08   both together
d1_fresh    → d1_self        0-4   p = 0.1250      self-reversal: nothing
d3_fresh    → d3_self        0-2   p = 0.5000      self-reversal: nothing
```

---

## 4. The current claim, stated as narrowly as the evidence allows

> Corroborating a source **reduces adoption of a later contradiction, over and
> above the effect of simply putting more text in between.**
> Decomposition with speaker held fixed: **dilution −0.39, corroboration a
> further −0.33.**

The decisive comparison is `d1pad_fresh` vs `d3_fresh`: identical message count,
identical speaker sequence, identical contradictor identity, byte-identical
source and contradiction text. The *only* difference is whether the two middle
messages restate the source or are irrelevant filler.

Guards that distinguish this from the obvious rival explanations:

- **not repetition** — restatements are paraphrases, gated at ≤ 0.75 framing-word
  overlap against the source and every earlier link.
- **not single-voice self-repetition** — the two corroborators are different
  named speakers, neither of whom is the contradictor.
- **not self-preference / source bias** — three different models write, certify
  and decide; the decider wrote none of the text it reads.
- **not "the contradictor discredited himself"** — E9 tested this directly and
  it does nothing.
- **not length** — that factor is now *separately measured*, not assumed away.

**No novelty claim is being made.** See §8.

---

## 5. Everything retracted, with what killed it

The retraction list is longer than the results list. That ratio is the honest
summary of the project.

| claim | why it died | caught by |
|---|---|---|
| E2 v1, entire run | the prompt printed a valid topological order, so an echo policy scored 36/36 in every condition | a null control |
| `supersession_respected` metric | returned 1.0 for an **empty plan** | a null control |
| `source_truster` baseline at 36/36 | overrides *deleted* a constraint instead of reversing it, so the benchmark rewarded the same reflex as all the prior art | a null control |
| SUPERSESSION classifier | a two-word regex `\bchanged\b|\bnow\b` scored 36/36 vs 0/468 | n-gram separability gate |
| BM25 retrieval inversion (as a content signal) | 89% of messages score 0.0 → degenerates to recency | instrumentation |
| E4b authority effect | p = 0.031 across 5/5 models, then **its own speaker-free control** removed unanimity and cut the mean 62% | its own control |
| E5 "step function" | a p = 1.000 null at n = 36 read as a plateau | re-reading the p-value |
| E5 "step function", again | corrected corpus turned the shape into a monotone gradient | `verify_claims.py` |
| AnchorRoute | killed **at design stage**: cos(contradiction, source) = 0.846 > cos(faithful, source) = 0.835, and the contradiction outranks the least-similar faithful relay in 36/36 — embeddings are blind to order inversion | a measurement taken before building it |
| Mode B corpus v1 | two gates were mutually unsatisfiable, silently dropping 5/36 instances | reading *why* instances dropped |
| **E7's P2, "length does nothing"** | predeclared and reported as holding (p = 0.2266). With speakers controlled: **14-0, p = 1.221e-04** | E9 |
| **E5/E7 identification** | the headline was **not identified** — corroboration and "contradictor reverses himself" were perfectly collinear (36/36 at d2/d3, absent at d1) | an adversarial audit, **not any gate** |

### The two most instructive failures

**(a) A deleted null control.** The echo control — which had caught the worst
defect in the project — was silently removed by a later edit whose slice
replacement spanned it. The test suite kept passing for several commits. Fixing
it changed the corpus fixture, which forced an E5 re-run, **and the result
changed shape**. Controls now live in a registry with an asserted count.

**(b) A gate that could not see the thing it existed to prevent.**
`test_corroborators_come_from_more_than_one_speaker` computes
`exposure(...)[1:-1]` — the `[-1]` slices the contradiction out before taking the
speaker set, so it only ever compared L1 to L2. And the Mode A/Mode B equality
check could not help either: Mode B is built by `replace(m, text=...)` on Mode
A's own messages, so a field-for-field equality assertion **guarantees the
confound is reproduced in both modes rather than detected.**
*An equality test between two arms is blind to any defect they share.*

---

## 6. Methodological apparatus now in place

- **`verify_claims.py`** — re-derives every reported number from raw plan text,
  never by reading a stored score back out of the file that asserts it. Three
  outcomes: VERIFIED / MISMATCH / **UNVERIFIABLE** (artifact scored against an
  older corpus — reported, never counted as passing). Falsification-tested:
  mutating plans turns it red, restoring turns it green.
- **Predeclaration in git.** E7's and E8's hypotheses, comparison targets and
  falsification rules were committed with *no results in the tree*, several
  commits before any decision call.
- **Frozen, hashed corpora.** Mode A `9dd2cea16a8142c2`, Mode B
  `4a2938565a36ee9f`. Retired corpora are archived with a written retraction
  note, not deleted.
- **Seeded generation.** Mode B retries are seeded; regenerating a chunk
  reproduced its hash bit-identically.
- **Adversarial review.** A 6-lens panel of independent agents was pointed at E7
  and told to kill it; one finding survived refutation and produced E9.
- 8 test suites + the verifier, all green.

---

## 7. What is unfinished or partial — please treat as open

1. **E8 (cross-model) is ~60% run.** Predeclared and committed. Complete:
   `qwen2.5:3b-instruct`, `aya-expanse:8b`. Half-run: `qwen2.5:7b-instruct`.
   Not started: `qwen2.5:14b-instruct`. **No E8 analysis has been produced yet.**
   Note E8 contains a deliberate **self-preference probe (P7)**: the model that
   *wrote* every contradiction is included as a decider, so source bias becomes
   a measurement rather than a design argument.
2. **E9 has one decider only** (`llama3.2:3b`), so the identified claim currently
   inherits the same small-model caveat E8 was built to remove.
3. **Mode A was never re-run under E9's speaker control**, so the Mode A numbers
   in §3 remain confounded in the way §5 describes.
4. All models are local, open-weights, **under 15B**. Nothing about frontier
   models follows.
5. The exposure schedule is **curated in both modes**. Mode B makes the *text*
   natural, not the *conversation*.

---

## 8. The blocker that gates any novelty claim

**No prior-art scan has been run on the *sharpened* framing.** Earlier scans
covered adjacent framings and pre-empted **four of five** candidate research
questions outright. The current framing is much narrower than any of them:

> *paraphrastic* corroboration (≤ 0.75 framing overlap, so not repetition), by
> *more than one speaker*, of a *single source* rather than independent
> evidence, measured on a *downstream plan* rather than a stated belief, against
> a control matched on *length, speaker sequence and contradictor identity*.

Nearest neighbours that must be checked first:
- repetition / illusory-truth effects in LLMs (arXiv:2601.03746)
- corroboration count in knowledge conflict — Xie et al. ICLR 2024
  (arXiv:2305.13300); Jin et al. COLING 2024 (arXiv:2402.14409)
- source bias — Dai et al. KDD 2024 (arXiv:2310.20501)
- "Blinded by Generated Contexts" — Tan et al. ACL 2024 (arXiv:2401.11911)

The session that built E7–E9 exhausted its web-search budget before this scan
could run. **Assume the framing is pre-empted until a real search says
otherwise.**

---

## 9. Specific questions for the reviewer

1. Given §7, what is the right ordering: finish E8, extend E9 across models, or
   re-run Mode A under speaker control? Which of these most changes what can be
   claimed?
2. Is the §4 claim, with its §5 retractions attached, a defensible contribution
   for a compulsory project — or is the more defensible contribution the
   **instrument** (`AgentLineageBench` + `verify_claims.py` + the retraction
   record)?
3. Is the length/corroboration decomposition (−0.39 / −0.33) better framed as
   *two* findings than one?
4. Does the exploratory shape difference (Mode A gradient vs Mode B step, with
   revision-framing measured at 13/36 vs 3/36) justify a further predeclared
   experiment holding relay text fixed and varying only the contradiction's
   framing?
5. Is anything in §4 already covered by the §8 literature?
