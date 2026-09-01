# Findings — what is established, what is retracted, what is unclaimed

One page, kept current. Every number here re-derives from raw artifacts via
`python verify_claims.py`, which exits non-zero on drift (currently **95
verified, 0 mismatched, 3 unverifiable**).

Read the retraction table first. It is longer than the results table, and that
ratio is the honest summary of this project.

---

## 0. The result, as it stands after E11 — read this first

Two experiments (E10, E11) were run under falsification-first preregistration
after E9. They changed the picture twice, both times against earlier claims of
mine.

**What survives, and it is one thing:**

> **Paraphrastic corroboration of a source reduces adoption of a later
> contradiction, in a dose-dependent way, relative to length-matched irrelevant
> filler.** E11, `llama3.2:3b`, n = 36, at three levels of k:
> `filler → same-root` p = 3.4e-03 (k=1), 7.6e-06 (k=2), 3.8e-06 (k=3).
> Flip rate falls 0.75 → 0.4167 → 0.2778 → 0.1111 as correlated support is added.

**What does *not* survive:**

- **Evidential independence does nothing.** One document restated *k* times is
  worth what *k+1* independent documents are worth, to within 0.03–0.06 at every
  k. Paired difference at k=2 is **+0.0000** (p = 1.0). The preregistered kill
  rule fired and the lineage direction is **retired**.
- **And that null is not a perception failure.** A preregistered non-decision
  probe on the same corpus shows the model reports more distinct documents for
  the independent arm in **27/36** and fewer in **0/36** (sign test
  p = 1.5e-08). **It sees the redundancy and prices it at zero.**
- **The dilution/length effect does not replicate.** §1 below reported it as
  established. E11 finds `bare → filler` null at all three k (p = 1.0, 1.0,
  0.34). Across three experiments it is large (E9), moderate (E10), then absent
  (E11). **Withdrawn.** The E9 decomposition "dilution −0.39, corroboration
  −0.33" overstated dilution.

The saturation objection to the null was tested and killed: E11's dose-response
shows the design had ample room to move (0.75 → 0.11), so a null in the
independence contrast is informative rather than a ceiling artifact.

**Nothing here is claimed as novel.** See `docs/novelty_matrix.md`: the
surviving effect (C1) is pre-empted, and the interesting null (C4) cannot be
assessed because the adversarial prior-art search is blocked.

---

## 1. The result as it stood after E9 — superseded by §0, kept for the record

**Corroborating a source reduces adoption of a later contradiction, over and
above the effect of simply putting more text in between.** Both factors are
real. An earlier version of this page said length did nothing; that was wrong
and is retracted in §2.

The decisive comparison is E9's `d1pad_fresh` vs `d3_fresh`. These two arms have
**identical message count, identical speaker sequence, identical contradictor,
and byte-identical source and contradiction text.** They differ in exactly one
thing: whether the two middle messages restate the source or are irrelevant
filler.

| arm (E9, all with a *fresh* contradictor) | middle messages | adoption |
|---|---|---|
| `d1_fresh` | none (2 messages total) | 0.9167 |
| `d1pad_fresh` | 2 × irrelevant filler | 0.5278 |
| `d3_fresh` | 2 × faithful restatement | 0.1944 |

```
d1_fresh    -> d1pad_fresh   14-0   p = 1.221e-04   filler ALONE moves it
d1pad_fresh -> d3_fresh      13-1   p = 1.831e-03   corroboration adds MORE
d1_fresh    -> d3_fresh      26-0   p = 2.980e-08   both together
```

*(adoption = corruption / (source + corruption); ambiguous plans excluded from
the ratio, never silently counted as either. `neither` = 0 in every E7 and E9
cell.)*

So the honest decomposition, with speaker held fixed throughout: **dilution
−0.39, corroboration a further −0.33.** The corroboration effect survives, but it
is roughly half the size the E7 write-up implied, because E7 attributed the whole
drop to it.

**Why this is not simply "repetition helps".** The restatements are *paraphrases*
— a gate enforces ≤ 0.75 framing-word overlap against the source and against
every earlier link — and in E9 they come from two *different* named speakers,
neither of whom is the contradictor. Verbatim repeats and single-voice
self-repetition are excluded by construction.

**Why it is not self-preference.** Three different models: `qwen2.5:7b-instruct`
writes every relay, `qwen2.5:14b-instruct` certifies each in isolation,
`llama3.2:3b` decides. The decider wrote none of the text it reads, so source
bias (Dai et al., KDD 2024) cannot be the mechanism.

**Why it is not "the contradictor discredited himself".** See §2 — this was a
live and unnoticed confound until an adversarial audit found it, and E9 exists to
settle it. Self-reversal has no detectable effect: `d1_fresh` vs `d1_self`
p = 0.1250, `d3_fresh` vs `d3_self` p = 0.5000, mean shift +0.083.

**What replicates across generation modes, and what does not.**

| | replicates |
|---|---|
| direction (`d1` > `d3`) | yes, both modes |
| length dissociation (P2) | *appeared* to, and **later failed** — see §0; E11 finds no dilution effect at all |
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
| **E7's P2, "length does nothing"** | superseded twice: E9 showed length DOES matter (p=1.2e-04), then E11 showed it does not replicate at all | E9, then E11 |
| **E9/E10's dilution effect** | reported as established in §1. E11: `bare` vs `filler` null at k=1,2,3 (p = 1.0, 1.0, 0.34). Large in E9, moderate in E10, absent in E11 -- unstable across corpus realisations | E11 |
| **The lineage-independence hypothesis (H3)** | preregistered as load-bearing; paired difference **+0.0000**, p = 1.0, and null again at every k in E11. Kill rule fired, direction retired | E10, confirmed by E11 |
| **AnchorRoute, second death** | already killed on embedding geometry (E6); E10/E11 kill it again from the other side -- the decider does not use evidential dependence, so no router can exploit it | E10/E11 |
| **E7's P2, "length does nothing"** | predeclared and reported as holding (`d1` vs `d1_padded`, p = 0.2266). With speakers controlled the same comparison is **14-0, p = 1.221e-04** — filler alone moves adoption 0.9167 → 0.5278. E7 attributed the entire drop to corroboration; roughly half of it is dilution. | E9 |
| **E7/E5 identification** | the headline was *not identified*: in every arm, corroboration and "the contradictor is reversing his own just-stated position" were perfectly collinear (36/36 at `d2` and `d3`, absent at `d1`) | an adversarial audit, not any gate |

### The confound that nearly took the headline

Six independent agents were pointed at E7 and told to kill it. One found this,
and it was real:

| arm | corroboration | contradictor reverses himself |
|---|---|---|
| `d1` | no | no |
| `d1_padded` | no | no |
| `d2` | yes | **yes, 36/36** |
| `d3` | yes | **yes, 36/36** |

Those columns are identical, so `d1_padded` vs `d3` — the load-bearing
comparison at p = 1.526e-05 — moved *both* factors at once. The rival account is
ordinary: a colleague who states an ordering and then asserts the opposite two
messages later is contradicting himself, and a reader may discount him for that
alone.

**The gate that existed to prevent this could not see it.**
`test_corroborators_come_from_more_than_one_speaker` computes
`ch.exposure(MAX_DEPTH, True)[1:-1]` — the `[-1]` slices the contradiction out
before the speaker set is taken, so it only ever compared L1 against L2. And the
Mode A/Mode B equality check cannot help either: Mode B is built by
`replace(m, text=...)` on Mode A's own messages, so a field-for-field equality
assertion *guarantees the confound is reproduced in both modes rather than
detected*. **An equality test between two arms is blind to any defect they
share.**

E9 settles it by crossing the two factors. Corroboration survives; self-reversal
has no detectable effect. The audit's finding was right about the design and
wrong about the data — which is exactly what an adversarial check is for, and why
its statistical support was verified rather than accepted (the agent's Fisher
test, and my first attempt to check it, both used a wrong row sum).

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
