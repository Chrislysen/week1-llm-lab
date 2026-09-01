# E2 design — Agent Lineage Bench

**DESIGN ONLY. Nothing here is implemented.** No code, no instances, no runs.
This document exists so that E2 can be reviewed before it is built, and so that
any later novelty claim can be checked against what was actually planned.

The compulsory baseline (`compulsory-baseline-v1`) and the frozen selector
protocol (`selector-protocol-v1`) are untouched by anything described here.

---

## 1. Why E2 exists

E1 and the offline preflight established, on **one** scenario, that every
selector ranks the agents' own restatements above the authoritative originals
those restatements came from. That is suggestive and it is not enough. Three
things are missing:

1. **One scenario.** The effect could be a property of `db04-payments` rather
   than of multi-agent dialogue.
2. **No lineage ground truth.** In E1 the relays are LLM-generated, so nothing
   knows whether turn 8 faithfully restates turn 3 or quietly distorts it.
   Without that, "derived" is a position in the transcript, not a relationship.
3. **Retrieval and decision are confounded.** A wrong plan may follow a derived
   statement *because* the source was never retrieved. That is a retrieval
   failure wearing a decision failure's clothes.

E2 is the instrument that separates these. It is a benchmark, not a result.

## 2. The two inversions, defined so they can be told apart

**Retrieval authority inversion.** Under a fixed context budget, a selector
ranks derived agent statements above the authoritative evidence they derive
from.

> Measured on the *selection*, before any decision exists. Already measurable
> today: mean rank of source messages minus mean rank of derived messages.

**Decision authority inversion.** With the authoritative source **and** a
conflicting derived representation **both present in context**, the decision
follows the derived representation.

> Measured on the *plan*, conditioned on both being retrieved. The conditioning
> is what makes it a decision failure rather than a retrieval failure.

These can dissociate in all four combinations, and a benchmark that cannot
report the 2×2 is not measuring the phenomenon:

| | decision follows source | decision follows derivative |
|---|---|---|
| **source retrieved, derivative retrieved** | no inversion | **decision authority inversion** |
| **source not retrieved** | n/a | retrieval failure, not decision failure |

## 3. Procedural instance generation

Instances are generated from a grammar, not written by hand, so that they are
**structurally matched and lexically distinct**. Hand-written instances would
let scenario-specific vocabulary leak into the results — exactly the confound
that produced the E1 pool-audit surprise.

### 36 instances is a 6 × 6 crossed design, not n = 36

The 36 are every (domain, graph) pair, fully crossed and deterministic: **6
independent surface draws and 6 independent structures**, not 36 independent
samples. An effect present in all 36 is consistent with a single domain-axis
effect, a single graph-axis effect, or both — it is not 36 confirmations.

This is the same error the project already caught and fixed once, in
`research-design.md` §3b: a single random seed reproduced an identical selection
pattern on 21 transcripts, which was *n = 1 presented as n = 21*. Any aggregate
over the 36 must therefore be reported with a per-axis breakdown (by domain and
by graph) and with dispersion, never as a bare mean over 36.

Each generated instance fixes:

- a **domain skin**: service names, host names, entity nouns, drawn from
  disjoint vocabularies per instance so no lexical overlap survives across
  instances;
- an **action vocabulary** of fixed size, used only in the final structured plan;
- a **hidden formal constraint set** over that vocabulary — `before(a, b)` and
  `required(a)`, as in the compulsory, with a fixed count and a fixed
  dependency-graph shape across instances;
- a **lineage graph**: which message derives from which, with matched
  source→decision distances across instances.

Structure is held constant; surface form varies. Two instances differ in every
word and in no measurable structural property.

## 4. Message classes and lineage labels

Every message carries an explicit label. Labels are **hidden from every agent
and every selector**; they exist only for the scorer, exactly as the constraint
key does today.

```
{ msg_id, speaker, text,
  lineage: SOURCE | FAITHFUL_RELAY | CORRUPTED_RELAY | RECOVERY
         | DISTRACTOR | SUPERSESSION,
  derives_from: [msg_id, ...] | null,
  asserts: [{constraint_id, faithful: bool, asserted_form}],
  authoritative_at: [turn_range] }
```

| class | what it does | why it is needed |
|---|---|---|
| **SOURCE** | first authoritative statement of a constraint | the ground truth |
| **FAITHFUL_RELAY** | restates a source without distortion | the E1 baseline behaviour; a system must not penalise it |
| **CORRUPTED_RELAY** | restates a source with a *specific, known* distortion that conflicts with it | the instrument for decision authority inversion |
| **RECOVERY** | later message that restores the source's correct content after a corruption | tests whether the damage is repairable in-dialogue |
| **DISTRACTOR** | plausible, on-topic, constraint-irrelevant | stops "retrieve everything operational" from scoring well |
| **SUPERSESSION** | later information that *legitimately* overrides an earlier source | see below — the most important class |

### SUPERSESSION is now the whole contribution, not just a control

The prior-art scan (`research-roadmap.md`) found that decision authority
inversion is already published — Tan et al., ACL 2024, arXiv:2401.11911 — and
that retrieval-side preference for generated text is "source bias", Dai et al.,
KDD 2024. What it did **not** find anywhere is a conflict benchmark in which the
authoritative source is *not* always the answer key.

Every conflict dataset located treats the source as ground truth, so
"always trust the source" is a winning strategy in all of them. SUPERSESSION
breaks that, and it is the one element with no located prior art. The reasoning
below was written as a design argument; it now also carries the contribution.

> **CORRECTION, 2026-09-01.** The sentence above is **false** and is left in place
> as the record of what was believed. An adversarial prior-art pass found that the
> instruction-hierarchy benchmarks already build contexts where neither position
> heuristic can win because privilege, not position, decides -- ManyIH-Bench
> (arXiv:2604.09443, 853 procedurally composed tasks, deterministic scoring) and
> IHEval (NAACL 2025, arXiv:2502.08745, 3,538 items, all programmatic) -- and that
> a whole family of memory benchmarks rewards the *latest* statement
> (MemoryAgentBench FactConsolidation, LongMemEval updates, SEQUOR arXiv:2605.06353,
> STALE arXiv:2605.06527), while Manufactured Confidence (arXiv:2606.29279) crosses
> forged authority against legitimate in-session correction with ground truth by
> construction. Supersession is therefore not the class 'with no located prior
> art'. What is not found assembled elsewhere is narrower: a multi-party transcript
> with six derivation classes and exact `derives_from`, in which an authorised
> override and an unauthorised revision are word-identical and only the speaker
> resolves them, scored as a partial-order plan. See `docs/novelty_matrix.md` C11.

### Why SUPERSESSION is the load-bearing class

Without it, "later derived statement disagrees with earlier source" is *always*
wrong, and a trivial policy — always prefer the earliest authoritative
statement — scores perfectly while learning nothing. That policy is also
actively harmful in any real incident, where conditions change and later
information genuinely does override earlier information.

Including legitimate supersession means the correct behaviour is not "trust
sources" but "trust the currently-authoritative statement", and the two are
distinguishable only with lineage. **This is the class that makes the benchmark
non-trivial, and any candidate router must be scored on it.**

`authoritative_at` encodes the time range over which each statement holds, so
"which statement is authoritative right now" is a deterministic lookup rather
than a judgement.

## 5. Conditions

Presence of source and corruption is **controlled**, not left to the selector,
so the decision measurement is not contaminated by retrieval:

| condition | source in context | corruption in context |
|---|---|---|
| `both` | yes | yes | ← where decision authority inversion is measured |
| `source-only` | yes | no |
| `corruption-only` | no | yes |
| `neither` | no | no |
| `selector` | whatever the selector chose | whatever the selector chose |

The first four are oracle-controlled contexts at matched budget. The fifth is
the realistic one. Comparing `selector` against `both` separates "the selector
failed to retrieve" from "the model failed to reason".

## 6. Metrics

**Retrieval side**

- `source_retrieval_recall`
- `corruption_retrieval_rate`
- `authority_rank_gap` = mean rank(derived) − mean rank(source), per selector
- `distractor_selection_rate`

**Decision side** — all conditioned on the `both` condition

- `decision_follows_source`
- `decision_follows_corruption`
- `decision_follows_neither`
- `decision_authority_inversion_rate` = follows_corruption ÷ (follows_source + follows_corruption), reported with its denominator
- `recovery_effectiveness` — does a later RECOVERY message undo a corruption?
- `supersession_respected_rate` — does the decision follow a legitimately superseding statement? **A system that always prefers sources must score badly here.**

**Cost and parity** — unchanged from the compulsory: realised prompt tokens,
history words, seconds. Any win at higher realised spend is a paid win.

## 7. Controls

Carried forward, non-negotiable:

- **random** selection at matched budget, averaged over many seeds — E1 showed a
  single-seed random arm is n=1 dressed as n=21;
- **sabotage** — a selector that deliberately excludes sources; the scorer must
  collapse or the scorer is not measuring what is claimed;
- **oracle** — upper bound, diagnostic only, never pooled with scored arms;
- **no-corruption instances** — the corruption rate must be ~0 where no
  corruption was planted, or the metric is detecting noise.

## 8. Two generation modes, and the honest tension between them

Explicit lineage labels require scripted relays. Scripted relays make the
dialogue synthetic. Both facts are true and neither is dismissable.

- **Mode A — scripted lineage.** All messages generated procedurally. Lineage is
  exact. Both inversions measurable without any judge. Dialogue is synthetic.
- **Mode B — agent-generated.** Agents produce their own relays, as in E1.
  Dialogue is natural. Lineage must be inferred, so labels are noisy.

**E2 is Mode A.** That is what makes it a benchmark. Mode B is its external
validity check: if the effect measured in Mode A does not also appear in Mode B,
the benchmark is measuring an artefact of scripting, and that must be reported
rather than explained away.

### 8.1 Mode B as built (`lineage_modeb.py`, `e7_modeb.py`)

Mode B as specified above says lineage "must be inferred, so labels are noisy."
The implementation takes a narrower and stronger option: **natural text with
known parentage.** A model writes each relay, but we know `L2` derives from `L1`
because we handed it `L1` and asked for a restatement. Nothing is inferred, so
nothing is noisy — and the one property the check exists to vary, the *wording*,
is fully in the model's hands.

The price is that Mode B tests scripted *wording*, not scripted *conversation*.
The exposure schedule is still curated: a real dialogue decides for itself how
many times a claim gets restated. Mode B makes the text natural, not the
conversation. That limit is stated in `e7_modeb.py` and is not a hedge — it is
the difference between this and a claim about deployed systems.

Three models, none marking its own work: `qwen2.5:7b-instruct` writes,
`qwen2.5:14b-instruct` certifies each message *shown alone*, `llama3.2:3b`
decides (E5's model, unchanged). Because the decider wrote none of the text it
reads, source bias — a model preferring its own generations, Dai et al. KDD 2024
— is ruled out without needing an extra arm.

**Gates that enforce vs gates that measure.** Mode A can compel its generator;
Mode B cannot compel a model, so half of Mode A's guarantees become
measurements, and which is which is stated at each gate:

| enforced | measured |
|---|---|
| length bounds; both actions mentioned; no action *identifier* leaked into prose; filler mentions neither action; links mutually distinct (≤ 0.75 content-word overlap); one corruption wording reused at all three depths; filler and links length-matched | keyword separability of faithful vs corrupted (Mode A forbids it by construction — Mode B can only report it); paraphrase drift from the source across L1/L2/L3; verifier disagreement rate |

**What building it cost, and what that bought.** Three defects that every
existing gate passed: relays that were verbatim-identical at every depth
(temperature 0 makes restating a minimal sentence a fixed point, so depth 3
would have measured *repetition*); speakers assigned per class, which turned two
parties corroborating into one person repeating themselves; and a shape check
that was vacuously true on an uncertified chain. All three are recorded in the
commit history rather than tidied away.

**It also found a limitation in Mode A.** `d1_padded` is the arm carrying E5's
headline — it holds message count and corruption position at the `d3` values
while swapping corroborating links for filler. It held the count; it never held
the length. Mode A's filler averages 7.6 words against its links' 12.4, so
`d1_padded` runs ~11 words (20%) shorter than `d3`. The confound points the
wrong way for a text-volume account — `d1_padded` is *shorter* and shows *less*
adoption — so the reading survives, but "the confound points the wrong way" is
weaker than "the confound is absent," and E5 was written as though it were the
second. Mode B matches the pair to ~1 word, making its length control strictly
stronger than the one it was built to validate.

## 9. What would earn AnchorRoute

**AnchorRoute is not designed here and must not be implemented until the
benchmark says it is warranted.** The gates, declared in advance:

1. **Retrieval inversion generalises.** `authority_rank_gap > 0` across
   instances, not just `db04-payments`.
2. **Decision inversion exists.** `decision_authority_inversion_rate` measurably
   above zero in the `both` condition, with a reported denominator.
3. **It is not just retrieval.** The `selector` condition must be worse than
   `both` — otherwise the fix is a better retriever, not a lineage-aware one.
4. **Lineage carries information a lineage-blind method cannot get.** A strong
   lineage-blind baseline at the same budget must fail where lineage would
   succeed. If relevance alone recovers it, there is nothing to route.
5. **Supersession is not broken by the fix.** Any candidate must not degrade
   `supersession_respected_rate` — the trivial "always trust the source" policy
   is the thing to beat, not the thing to become.

Fail any gate → do not build the router; report why.

## 10. Novelty position: still NONE claimed

Per `docs/research-roadmap.md`, generic provenance, contradiction handling,
role-aware routing, source reliability weighting, multi-hop semantic drift,
stale/superseded memory and relevance-vs-utility all have prior art. E2 is a
**measurement instrument**, and the honest description of a completed E2 is "a
benchmark that separates retrieval authority inversion from decision authority
inversion with deterministic lineage ground truth" — a resource contribution.

A real prior-art search is a prerequisite for E2 stage 3, not a formality. The
project's own literature scan already found four of five candidate research
questions fully pre-empted; the prior should be that this one is too.

## 11. Open questions for review

1. **Instance count and shape.** How many instances, and how many corruptions
   per instance? Too few and nothing is measurable; too many and each instance
   becomes an unnatural pile-up of distortions.
2. **Corruption severity.** Should a corruption invert a constraint
   (`before(a,b)` → `before(b,a)`), drop a precondition, or weaken it to a
   suggestion? These are probably not equally detectable and may need to be a
   reported factor rather than a fixed choice.
3. **Who speaks the corruption?** The Operations Lead corrupting its own
   recollection is a different phenomenon from the Safety Auditor doing so, and
   role may interact with authority.
4. **Does the scripted dialogue still need two live agents?** If every message
   is scripted up to the decision, Mode A may be a single-call benchmark with a
   dialogue-shaped prompt — cheaper, but further from the setting it claims to
   describe.
5. **Budget.** Keep W = 250 for continuity with E1, or scale it to instance size?
   Continuity is worth something; comparability across instance sizes is worth
   more.
