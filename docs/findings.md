# Findings — what is established, what is retracted, what is unclaimed

One page, kept current. Every number here re-derives from raw artifacts via
`python verify_claims.py`, which exits non-zero on drift (currently **37
verified, 0 mismatched, 3 unverifiable**).

Read the retraction table first. It is longer than the results table, and that
ratio is the honest summary of this project.

---

## 1. The one result that has survived every control

**Corroboration of a source, not the amount of text separating it from a later
contradiction, is what determines whether the contradiction gets adopted into a
plan.**

Two arms, identical in message count, corruption position, and — in Mode B — to
within 0.0 words of total length. They differ in one thing: whether the two
intervening messages *restate the source* or are *irrelevant filler*.

| arm | intervening messages | Mode A | Mode B |
|---|---|---|---|
| `d1` | none | 0.7778 | 0.7778 |
| `d1_padded` | 2 × irrelevant filler | 0.8000 | 0.6389 |
| `d3` | 2 × faithful restatement | 0.4167 | 0.1667 |

*(adoption = corruption / (source + corruption); ambiguous plans excluded from
the ratio, never silently counted as either. `neither` = 0 in all Mode B cells.)*

Mode B, paired McNemar, n = 36:

```
d1  vs d1_padded    3-8    p = 0.2266      filler does not protect
d1_padded vs d3    0-17    p = 1.526e-05   corroboration does
d1  vs d3          1-23    p = 2.980e-06
control                    0.0000          36/36 follow the source when
                                           nothing contradicts it
```

**Why this is not simply "repetition helps".** The restatements are *paraphrases*
— a gate enforces ≤ 0.75 framing-word overlap against the source and against
every earlier link — and they come from *more than one speaker*, also gated.
Verbatim repeats and single-voice self-repetition are both excluded by
construction, and both would have been the more mundane explanation.

**Why it is not self-preference.** In Mode B three different models are used:
`qwen2.5:7b-instruct` writes every relay, `qwen2.5:14b-instruct` certifies each
one in isolation, `llama3.2:3b` decides. The decider wrote none of the text it
reads, so source bias (Dai et al., KDD 2024) cannot be the mechanism.

**What replicates across generation modes, and what does not.**

| | replicates |
|---|---|
| direction (`d1` > `d3`) | yes, both modes |
| length dissociation (P2) | yes, and *stronger* in Mode B, whose control is genuinely length-matched |
| **shape** | **no.** Mode A declines gradually (0.78 → 0.61 → 0.42); Mode B steps at the first link and the second adds nothing (`d2` vs `d3` p = 1.0000) |

The two corpora differ measurably in how the contradiction is worded — revision
framing appears in 13/36 Mode A corruptions against 3/36 in Mode B — which is a
candidate explanation for the differing magnitudes. It is measured, not tested.
Consistency is not evidence.

---

## 2. Retracted — reported, then withdrawn

| claim | why it died | caught by |
|---|---|---|
| E2 v1, whole run | the prompt printed a valid topological order, so echoing it scored 36/36 in every condition | a null control |
| E5 "step function" | a p = 1.000 null at n = 36 read as a plateau | re-reading my own p-value |
| E5 step function, again | corrected corpus turned the shape into a monotone gradient | `verify_claims.py` |
| `supersession_respected` | returned 1.0 for an empty plan | a null control |
| BM25 retrieval inversion | 89% of messages score exactly 0.0, so it had degenerated to recency (93.7% agreement) | instrumentation |
| `source_truster` at 36/36 | overrides *deleted* a constraint instead of reversing it, so the benchmark rewarded the same reflex as all the prior art | a null control |
| SUPERSESSION classifier | a two-word regex `\bchanged\b\|\bnow\b` scored 36/36 vs 0/468 | n-gram separability gate |
| E4b authority effect | p = 0.031 across 5/5 models, then its own speaker-free control removed unanimity and cut the mean 62% | its own control |
| AnchorRoute | killed at design stage: cos(contradiction, source) = 0.846 > cos(faithful, source) = 0.835, and the contradiction ranks above the least-similar faithful relay in 36/36 — embeddings are blind to order inversion | a measurement made before building it |
| Mode B corpus v1 | two of its gates were mutually unsatisfiable, dropping 5/36 instances | reading *why* instances dropped |

Two of these were caught **after** being written up. That is the reason
`verify_claims.py` exists, and the reason its first run is described below.

---

## 3. What the instrument caught in itself

- **A deleted null control.** The echo control — which caught the worst defect in
  this project — was silently removed by a later edit whose slice replacement
  spanned it. The suite kept passing for several commits. `grep -c` returned 0.
  Controls now live in a registry with an asserted count, so removing one is
  itself a test failure.
- **A length control that was never length-matched.** `d1_padded` carries the
  headline; it held message *count* but not *length*, running ~10 words (20%)
  shorter than the arm it is matched against. The confound points the wrong way,
  so the reading survives — but "points the wrong way" is weaker than "is
  absent," and E5 was written as though it were the second.
- **A corroboration test that had removed corroboration.** Mode B assigned
  speakers per class, turning two parties agreeing into one person repeating
  himself. Every count-and-lineage assertion passed.
- **A verifier catching what no string check could.** `qwen2.5` code-switched
  into Chinese under temperature sampling; all four deterministic gates passed
  the message because the surviving ASCII stems matched. The 14B verifier,
  reading the sentence alone, reported the wrong ordering. Now a cheap
  deterministic gate, with the real failure text kept as a regression case.

---

## 4. Unclaimed — the blocker

**No novelty claim is made.** `docs/research-roadmap.md` blocker **B1**: the
prior-art scan on the *sharpened* framing has not been run. The framing that
survives the controls is much narrower than anything scanned so far —
paraphrastic corroboration, multi-speaker, of a single source rather than
independent evidence, measured on a downstream plan rather than a stated belief,
against a length-matched filler control. The nearest neighbours to check first
are repetition / illusory-truth effects, corroboration count in knowledge
conflict (Xie et al. ICLR 2024; Jin et al. COLING 2024), and source bias (Dai et
al. KDD 2024).

This project's own base rate is that **four of five** candidate research
questions came back fully pre-empted. Assume this one is too until a real search
says otherwise.

---

## 5. Scope — what none of this shows

- One decider model (`llama3.2:3b`, 3B parameters) for the depth experiments.
- Synthetic incidents, six domains × six constraint graphs.
- The exposure schedule is **curated in both modes**. Mode B makes the *text*
  natural, not the *conversation*: a real dialogue decides for itself how often a
  claim gets restated. This is the difference between the result above and a
  claim about deployed systems.
- Adoption is measured on action ordering in a plan, not on a stated belief.
