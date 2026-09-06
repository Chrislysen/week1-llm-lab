# A negative-results record from a small AI-assisted research programme

**Status: a record, not a findings paper.** This document makes no novelty
claim. It exists because the interesting thing this project produced is not a
result about language models — it is a fully instrumented account of a research
programme that failed to produce one, with every failure dated, attributed to
whatever caught it, and re-derivable from artifacts on disk.

Written 2026-09-06. Everything below re-derives via `python verify_claims.py`
(**167 verified / 0 mismatched / 4 unverifiable**) and `pytest` (**135 tests,
17 suites**). The frozen corpus hashes are asserted at the start of every run.

---

## 1. What survives

One behavioural result, and it is narrow:

> **Paraphrastic corroboration of a source reduces adoption of a later
> contradiction, dose-dependently, relative to length-matched irrelevant
> filler.** E11, `llama3.2:3b`, n = 36, at three levels of k:
> `filler → same-root` p = 3.4e-03 (k=1), 7.6e-06 (k=2), 3.8e-06 (k=3). Flip
> rate falls 0.75 → 0.4167 → 0.2778 → 0.1111 as correlated support is added.

It is **PREEMPTED** in `docs/novelty_matrix.md` row C1: corroboration count
under knowledge conflict is published (Xie et al., ICLR 2024; Jin et al.,
COLING 2024), as is the repetition effect (arXiv:2601.03746). The only thing
this repository adds is that the measurement is taken on a downstream *plan*
rather than a stated belief.

Also established, and also not new: an **equivalence-supported null** on the
ordering verdict (E12; difference +0.0185, cluster p = 0.749, 95 % CI
[−0.037, +0.074], inside a preregistered SESOI of 0.10, 108 units in 36
clusters). It took two attempts — E10 asserted the same conclusion at n = 36
where power at the SESOI was 0.14 and the equivalence branch was structurally
unreachable. That claim was retracted in full.

**One surviving pre-empted result, against nineteen retractions.** That ratio
is the honest summary, and it is the subject of this document.

---

## 2. The retraction ledger, and what actually caught the errors

`docs/findings.md` §2 records nineteen reported-then-withdrawn items, each with
the thing that caught it. Tallying that column mechanically:

| what caught it | n |
|---|---|
| **Designed-in checks** — null controls (3), an experiment's own control, `verify_claims.py`, instrumentation, an n-gram separability gate, a measurement taken before building, reading *why* instances dropped | **9** |
| **Adversarial review** — agent panels (4), one audit that no gate could have replaced | **5** |
| **A subsequent experiment** — E9, E11, E10/E11 | **4** |
| **The author re-reading his own p-value** | **1** |
| | **19** |

Three observations, in descending order of how uncomfortable they are.

**(a) Designed-in checks caught fewer than half.** Null controls are the single
most productive device in the ledger — three kills, including the worst defect
in the project (E2 v1 scored 36/36 in every condition because the prompt
printed a valid topological order, so echoing it passed). But 10 of 19 errors
were caught by something other than the machinery built to catch errors.

**(b) The gate designed to prevent the near-miss could not see it.** Six agents
were pointed at E7 and told to kill it. One found that corroboration and "the
contradictor reverses his own just-stated position" were perfectly collinear —
36/36 in both `d2` and `d3`, absent in `d1` — so the load-bearing comparison
moved two factors at once. The existing gate,
`test_corroborators_come_from_more_than_one_speaker`, computed
`ch.exposure(MAX_DEPTH, True)[1:-1]`; the `[-1]` sliced the contradiction out
before the speaker set was taken. And the Mode A/Mode B equality check could not
help either, because Mode B is built by `replace(m, text=...)` on Mode A's own
messages: **an equality test between two arms is blind to any defect they
share.** E9 settled it by crossing the factors; corroboration survived,
self-reversal had no detectable effect.

**(c) Two of the nineteen were caught only after write-up.** That is why
`verify_claims.py` exists.

### The instrument's defects, found by the instrument

- **A deleted null control.** The echo control — which caught the worst defect
  in the project — was silently removed by a later edit whose slice replacement
  spanned it. The suite kept passing for several commits. Controls now live in
  a registry with an asserted count.
- **A length control that was never length-matched.** `d1_padded` carried a
  headline while running ~20 % shorter than its comparison arm. The confound
  points the wrong way, so the reading survived — but "points the wrong way" is
  weaker than "is absent", and E5 was written as though it were the second.
- **A corroboration test that had removed corroboration.** Mode B assigned
  speakers per class, turning two parties agreeing into one person repeating
  himself. Every count-and-lineage assertion passed.
- **A deterministic gate fooled by code-switching.** `qwen2.5` switched into
  Chinese under sampling; all four gates passed the message because the
  surviving ASCII stems matched.

---

## 3. The novelty search: thirteen candidates, thirteen closed

Across 2026-09-03 → 2026-09-06, thirteen candidates went through an adversarial
prior-art gate. **All thirteen closed.** Every one had every component already
published.

| family | candidates | outcome |
|---|---|---|
| behavioural | E16-A–D, S-A, S-B, S-L, S-O, S-E | all closed; S-O and S-E were screened first, then retired |
| measurement | N-1, N-2, N-3 | N-3 pre-empted, N-1 surrounded, N-2 unfound but unevidenced |
| meta-science | M-1 | pre-empted |
| bounding | B-1 | pre-empted |

### The finding inside the search: gate configuration decided the verdict

The 2026-09-03 gate ran **without web search** — its budget was exhausted, so it
used the arXiv export API, arXiv site search, OpenAlex, Crossref and direct
fetches. It rated the two lead candidates **OPEN**.

Re-run **with web search** two days later, both died within a day:

- **S-O** killed by arXiv:2608.12599 (*Dead text or binding clause?*, Aug 2026)
  — dialogue revocation, models still enacting withdrawn requirements, relapse
  at 8B climbing 0.011 → 0.403 while stronger models sit at floor. That is the
  candidate's predictions (1) and (2), published three weeks before the screen
  was designed.
- **S-E** killed by arXiv:2607.05545 (*Most LLM Conformity Needs No Speaker*),
  which states the candidate's confound verbatim and runs its intended design —
  a no-source condition on six open-weight LLMs, with the paraphrase arm.

**A citation audit of eight of the API-only gate's sources found its
identifiers and substance largely sound**: six clean, one label-only error
(arXiv:2608.20392 is not titled "MeetingProbe", but its 13.4 % figure is real,
in Table 9 Appendix H), one substantive error (InterruptBench is not
frontier-only — six open backbones with a retraction arm, which *understated*
its proximity to S-E), one characterisation unverified.

So the failure was **not retrieval**. It was **judgment**: the gate found real
papers, described them roughly correctly, and reached the wrong verdict about
what they pre-empted.

That dissociation is itself pre-empted as a claim — arXiv:2606.12071 documents
the "novelty mirage" in LLM-as-judge novelty assessment, and the AI-Scientist
critique literature documents the exact default-to-novel mechanism (Semantic
Scholar top-10 keyword retrieval; *"if such a decision is not reached, the idea
is automatically considered novel"*). This programme's contribution is an
instance with a paper trail, n = 2, uncontrolled. **It is an anecdote, not an
ablation**, and is recorded as one.

---

## 4. Turning the instrument on itself

The E16 screen ended because two of three deciders failed a stage-1 validity
gate: the "never-mentioned" base rate had to be ≤ 0.50 and came in at 0.646 and
0.510. Investigating why produced the most useful methodological result here.

**The plan instruction enumerates the whole action vocabulary.** A
never-mentioned action is therefore still an offered menu item, and its
inclusion rate is roughly `|plan| / |vocab|` — both of which the benchmark
author sets.

Two studies pinned this down.

**E16 menu diagnostic** varied `|vocab|` ∈ {2.75, 6, 12} at free length. Its
declared read rule returned **UNINFORMATIVE**, and correctly: `|plan|` grew
×1.54 and ×1.59, so the 1/|vocab| arithmetic both hypotheses assumed did not
apply. The escape hatch was declared in advance and it fired.

**E17** pinned plan length by instruction (exactly 4 identifiers; ~100 %
compliance, parse 1.000). With length fixed:

| `|vocab|` | chance | qwen2.5:3b `never` | llama3.2:3b `never` |
|---|---|---|---|
| 6 | 0.667 | 0.573 | 0.562 |
| 12 | 0.333 | 0.427 | 0.354 |
| 24 | 0.167 | 0.250 | 0.229 |

Chance falls 4.00×; the rate falls 2.29× and 2.45× — below the declared 2.5×
line, so the verdict is **AMBIGUOUS** and the threshold was not moved. Both
declared hypotheses are wrong: `never ∝ chance^0.60` and `^0.65`, replicated
across two families. The elasticity also **saturates** (`|plan|` +55 % from 6→12,
then +3 % from 12→24).

**The consequence that matters.** Applying E16's own stage-1 gates to the
24-identifier arm, **both deciders fail all four gates at |vocab| = 6 and pass
all four at |vocab| = 12.** The gate that ended the screen was measuring a
prompt parameter nobody varied.

This too is not novel — sub-proportional response to added alternatives is a
violation of Luce's choice axiom / IIA (1959), which nested and mixed logit
exist to model, and IIA violation in LLMs is studied in the alignment setting
(arXiv:2312.01057). It is recorded as a **property of this instrument**, which
is all it is:

> For this benchmark family, the number of identifiers offered in the plan
> instruction is a first-order determinant of every rate the instrument
> reports. Never compare rates across menu sizes. Never set a fixed-threshold
> gate without fixing both `|plan|` and `|vocab|`.

---

## 5. What replication bought

After thirteen closures, the programme changed strategy: stop hunting for an
unclaimed hypothesis, test a claimed one. Replication inverts the novelty risk
by construction.

**E18** conceptually replicated arXiv:2608.12599's scale claim on this
repository's independent instrument and corpus, with plan length pinned:

| qwen2.5 | `rejected` | 95 % CI |
|---|---|---|
| 3B | 0.542 | [0.421, 0.656] |
| 7B | 0.250 | [0.162, 0.341] |
| 14B | 0.135 | [0.074, 0.200] |

**REPLICATES.** And the length control earned its place: under *free* length,
7B and 14B are tied at floor (0.062, 0.062) and the gradient disappears —
because free `|plan|` is 3.59 / 2.28 / 2.71, non-monotonic in scale.

**E18-B** bounded it across five families at identical pinned length. The 3–4B
band spread (**0.448**) exceeds the within-family 3B→14B spread (**0.407**), and
`gemma4:e4b` (~4B) has the lowest relapse of all six models — below
`qwen2.5:14b-instruct`. `never` stays flat (0.552–0.656) across every model, so
the difference is specific to rejection handling, not general verbosity.

Both are real. Neither is novel: B-1's gate found "family dominates scale" and
"a small model beats a much larger one across families" both established
(arXiv:2608.17183 documents non-monotonic size trends and inverse scaling
*within* families).

---

## 6. What a reader can and cannot take from this

**Can:**

1. A small, heavily instrumented programme produced **1 surviving pre-empted
   result against 19 retractions**, and the retractions are the more
   informative half.
2. **Null controls are the highest-yield device** in the ledger — but
   designed-in checks caught fewer than half the errors, and the gate built to
   prevent the worst near-miss was structurally blind to it. *An equality test
   between two arms cannot detect a defect they share.*
3. **Adversarial review caught 5 of 19**, including one thing no gate could
   have.
4. **Gate configuration determined novelty verdicts.** An API-only prior-art
   gate rated two candidates OPEN that web search killed in a day, while its
   citations stayed largely sound. Retrieval competence and novelty judgment
   came apart.
5. **Benchmark rates can be artefacts of free prompt parameters.** Here a
   pass/fail gate flips entirely between 6 and 24 offered identifiers, and a
   model-size comparison loses its gradient unless output length is pinned.

**Cannot:**

- Any general claim about language models. Every behavioural result here is
  pre-empted, single-model, or retracted.
- Any quantitative claim about research methodology. n = 19 retractions from
  one programme by one author with AI assistance, categorised by that author's
  own free-text notes, is not a study. The gate comparison is n = 2 and
  uncontrolled.
- That the instrument generalises. One corpus, one task family, one plan
  format, models 3B–14B.

---

## 7. Reproduction

```bash
python verify_claims.py     # expect 167 verified / 0 mismatched / 4 unverifiable
python -m pytest -q         # expect 135 passed
```

Primary records: `docs/findings.md` (results and the retraction ledger),
`docs/novelty_matrix.md` (claims C1–C15 and their pre-emption status),
`docs/E16-CANDIDATES.md` (the thirteen-candidate search, two RE-GATE sections,
the citation audit, and the N/M/B gates), and the protocols in
`docs/protocols/` — every one declared with zero outcomes before its first
model call, each with its read rule fixed in advance.

**Nothing in this document is offered as novel.** The programme's own verdict,
recorded on 2026-09-02 and unchanged since: *the reviewers rated the
methodology components pre-empted, so the value would be the record, not the
method.*
