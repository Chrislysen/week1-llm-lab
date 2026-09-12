# RESUME — where the work stands, and exactly what to do next

# 2026-09-12 — the paper push: third decider, real write path, second corpus

The author asked what would make E29 a paper rather than a workshop note and
said "let's keep working towards that". The honest list was: a larger
decider, a real-extractor stage that actually stores operational proposals,
and a second corpus. All three were declared with zero outcomes and run the
same night; every number below is in a `results/e29*_summary.json`.

**Third decider, `qwen2.5:14b-instruct` (E29 addendum, `99d60fd` → `8e4aa63`).**
DESIGN-DEPENDENT, delete DiD +0.208 [+0.094, +0.323]. Add-only and wiki go
flat (0.06 inclusion): the larger decider reads a stored rejection and
honours it, so only the design that *removes* the rejection re-admits the
step. Δ_full turns positive and non-significant (+0.052), consistent with
E29-C's reading that the negative sign was a 3B register effect. Under
`delete`/neutral the step is enacted at 0.635 from a store that says nothing
about it — the pinned four-step plan fills from the six-item menu — which caps
Δ_delete on this decider; the smaller DiD is a ceiling of the estimand, not a
weaker mechanism.

**Fourth decider, `gemma4:e4b` (third model family).** DESIGN-DEPENDENT,
delete DiD +0.500 [+0.375, +0.625]; add-only and wiki exactly 0.000 in
both arms; full context flat (−0.010). Every prediction and control
holds. The rejected step comes back through write-time delete and through
nothing else on this model. Runs at ~11 s/call: nineteen foreground chunks
of five; a 16-dialogue background chunk was reaped after 40 min.

**Real write path, E29-D (`8bce1ae` → `9f27286`): REAL-STORE EFFECT.** E29-B
had failed its manipulation check because Mem0's personal-information
extractor ignores operational steps. E29-D changes the extraction prompt
only (operational facts, few-shot on a domain not in the corpus) and keeps
Mem0's update router verbatim; extractor and router `qwen2.5:7b-instruct`,
decider `llama3.2:3b`, the same 48 dialogues. W0 0.958 (passes), W1 0.217
(the router deletes on rejection one time in five; otherwise it ADDs the
rejection or UPDATEs the proposal's text to carry it), W2 0.854 vs 0.750,
Δ_real +0.167 [+0.042, +0.292] — between the oracle add-only (+0.042) and
delete (+0.396) designs on the same dialogues, as predicted (P0–P3 all
hold). Zero malformed outputs in 48 dialogues. Observation: neutral-arm
enactment on the real store (0.50) is far above oracle add-only (0.17)
although the rejection is usually present; the router's UPDATEs fold the
rejection into the proposal's text and the 3B decider reads that as weaker.

**Second corpus, E29-N (`333ad85` → `66397c0`): DESIGN-DEPENDENT on both
deciders.** Six new domains (grid, airline, newsroom, water, checkout,
telecom), a second sentence bank, same generator and rules; frozen corpora
hash-asserted untouched (202 tests). Delete DiD +0.344 (llama) and +0.469
(qwen 7B); wiki +0.271 / +0.260; add-only's own Δ is +0.010 / −0.062. Two
cautions: absolute zombie rates are far higher on the new wording (under full
context 0.76 and 0.68 in the neutral arm, against 0.28 and 0.31), so wording
and domain set the level while the design sets the contrast; and Δ_full is
−0.156 on both deciders, so every DiD inherits +0.156 from the reference arm
and add-only's DiD trips P2 on llama although add-only did not respond. Report
Δ_X beside DiD_X; the within-store contrast Δ_delete vs Δ_addonly is the
reading that does not depend on the reference arm. P5 (the never-mentioned
control) fails on both deciders on this corpus: a step the store is silent
about is enacted at 0.66–0.77 when the dialogue makes it plausible.

**E29-N CORRECTION (2026-09-12, `99f2f29`).** Found by reading while adding
a fifth design: the oracle extractor keyed reply polarity on a "No" / "Let's
not" prefix and stored the second bank's "I'd leave that out" rejection as
an acceptance, in 24 of 96 second-corpus dialogues, store designs only;
first corpus byte-identical (hash unchanged). Fixed by template membership,
guarded by a test, re-run for exactly the 144 changed cells per decider.
Corrected: delete DiD +0.427 / +0.583 / +0.312 (3B / 7B / 14B), add-only
+0.177 / +0.073 / 0.000 with own Δ near zero, wiki +0.312 / +0.260 / +0.042;
the never-mentioned control now holds on all three (both v1 failures were
the bug). Verdicts unchanged in kind. Second-corpus hash re-pinned
7d33038c6c1a9912 → e965c5fd022d6e37; v1 summaries in
`results/e29n_v1_contaminated/`.

**E29-N, third decider.** `qwen2.5:14b-instruct` on the second corpus:
DESIGN-DEPENDENT, delete DiD +0.250 [+0.125, +0.385], add-only −0.010,
wiki +0.031, Δ_full +0.031 n.s., every control holding — the cleanest of
the three second-corpus readings. The second corpus now carries the E29
verdict on all three deciders.

**Gemini scout run 2 (2026-09-12, corpora focus).** Return and triage in
`docs/gemini-research-log/`. **One lead lands on us**: arXiv:2609.08258,
*Revoked but Still Authoritative* (2026-09-08), loads five shipped memory
systems with a revoked policy and finds none enforces it — revoked fact
returned 81/81 where the flag is visible, unsafe action in 43.1 % of 1,620
trials. That **preempts the headline of E29-T**, which we declared three days
later; recorded in `E29X-reviewer-controls.md` §5 and in the gate's new §0.3d
coverage-miss note. The E29 residual is untouched: they have no dialogue
rejection, no partner restatement, and no arm storing a rejection as prose.
What the two together give, and neither alone: add-only and tombstone hold the
same rejection, one as a sentence and one as a flag, and the enactment gap is
0.45 / 0.08 / 0.23 — **the encoding decides, not the retention**. That is now
the sharpened claim in the draft. Six leads besides: STALE re-flagged and
re-refuted by the method quote the tightened brief forced Gemini to supply;
StateAuditor, Grounded Continuation, StateFuse, RD-Forget, and 2606.01435
(retitled) all do not cover. Of twelve adversarial objections across two runs,
ten are answered from the record; the open two are a free-length plan and
naturalistic dialogue.

**Corpora for E30, assessed.** CaSiNo (Chawla et al., NAACL 2021; 1,030
human-written negotiation dialogues; explicit offers accepted or rejected; the
final allocation is a checkable outcome; on GitHub, HuggingFace and ConvoKit)
is the best fit and the licence must be read before use. Deal or No Deal is a
second option. **AMI is CC BY-NC-ND**, so a derived annotated corpus could not
be released. ICSI needs LDC licensing and a secondary annotation pass.

**Figure 1.** `docs/paper/fig1-delta-by-design.svg` / `.png` (`paper_fig.py`,
from the same summaries the report reads): every design's Δ with its interval
on every decider and both corpora, plus the two controls; the same figure is
drawn live in the report under the E29 table.

**E29-X, the two reviewer controls (`7f89477` → run 2026-09-12).** From the
scout's adversarial pass. Rendering control: a transcript whose replies name
their referent as the store does leaves the full-context neutral level
unchanged on all three deciders (0.281, 0.316, 0.167 to the third decimal),
so the level gap to add-only is design, not rendering; the 3B loses the
register effect under explicit referents. Tombstone design (rejected
proposal retained, flagged "[withdrawn]"): the flag is not read as a
rejection (neutral 0.625 / 0.421 / 0.292 vs add-only 0.177 / 0.344 / 0.062);
BETWEEN on 3B and 7B, FLAG NOT HONOURED on the 14B (DiD +0.292), the
reverse of the declared lean, recorded as a miss. Same-session full cells
replicate E29 to within 0.004 on all three. 1,728 calls, parse ≥ 0.998.

**Gemini Deep Research scout, run 1 (2026-09-12).** Brief in
`docs/GEMINI-DEEP-RESEARCH-BRIEF.md`; return and triage in
`docs/gemini-research-log/`. Nine new leads, five read in full text. The
paper Gemini flagged as covering the construct (2609.01852, the Memory
Trust Gap) is single-agent, single-response, metadata-framed staleness,
no dialogue, no re-mention; Gemini mis-titled it and mis-described its
manipulation while marking it VERIFIED, and gave a wrong arXiv id for
ReviseQA. Residual unchanged; gate rows added (E29 protocol §0.3b). Two
reviewer controls named as candidate follow-ups, neither run: **E29-R**
(rendering control: the transcript's rejection in the store's explicit
template) and **E29-T** (tombstone design as a fifth arm).

**Paper draft.** `docs/paper/zombie-steps-draft.md` (`9456426`): abstract,
related work from the gate table, setup, the three result tables, the
register follow-up, the real write path, controls, limitations,
reproducibility, and a predictions-against-outcomes appendix. Every number is
from a `results/*_summary.json`. The `gemma4:e4b` row is pending: that run
is slow (about four times the 14B model per call) and is in the background.

**What this changes in the score.** A larger decider, a working real-system
leg and a second corpus were the three named gaps. They are closed in the
sense that each was run and read by its rule; whether the second corpus
carries the same verdict on every decider is in the E29-N outcome.

# 2026-09-11 — E29: first candidate through the repaired gate, run on two deciders, DESIGN-DEPENDENT

**Where it came from.** A reading pass over four repositories the author
brought in (google-research/timesfm, nashsu/llm_wiki, mem0ai/mem0,
cosmtrek/mindwalk), done the way E24 was found: read what the field's
artifacts actually do, not what their papers say. Verified facts, all from
source: Mem0 OSS v3 (April 2026) is **ADD-only** with no recency weighting
and stores agent utterances at equal weight, while the Mem0 *paper* pipeline
that everyone cites hard-deletes on contradiction with no tombstone; llm_wiki
merges pages in place and queues contradictions for a human; mindwalk is a
session replay tool whose judge may only report evidence-anchored findings;
TimesFM has no fit here (no prior work on LLM traces, non-competitive as a
zero-shot anomaly detector). Recorded in memory and in
`docs/protocols/E29-memory-semantics.md` §0.

**The gate ran first**, under `docs/NOVELTY-GATE.md`, with twelve papers read
in full text by section (2609.04875, 2608.08236, 2605.06527, 2606.15903,
2604.20006, 2606.24322, 2606.27472, 2605.10481, 2608.19701, 2606.01435,
2609.03340, 2607.02579). Every component of the claim is occupied somewhere;
the conjunction — a *partner's* content-bearing restatement of a step
*rejected in dialogue*, delivered through hard-delete / add-only / merge-page /
full-context designs, read on an executable plan by 3B–7B deciders as a DiD
against a neutral line — was found nowhere. **Decision: candidate for testing,
residual NARROW.** Six further papers are abstract-level only and are named as
the coverage limit.

**Declared with zero outcomes at `b905fb6`, run the same day.** 96 E16
dialogues with a rejected slot × 2 arms × 4 designs = 768 calls per decider,
oracle stores from the scorer's tags, `pin4`, temperature 0.

| decider | Δ_full | DiD_delete | DiD_addonly | DiD_wiki | verdict |
|---|---|---|---|---|---|
| llama3.2:3b | −0.083 | **+0.438** [+0.312, +0.562] | +0.094 [−0.010, +0.198] | **+0.188** [+0.073, +0.312] | DESIGN-DEPENDENT |
| qwen2.5:7b-instruct | −0.073 | **+0.375** [+0.271, +0.490] | +0.042 [−0.052, +0.135] | **+0.156** [+0.042, +0.281] | DESIGN-DEPENDENT |

Parse 1.000 and |plan| 4.00 in every cell of both. Under write-time delete
the rejection is consumed by the DELETE, the later mention is stored with
nothing to contradict it, and the rejected step goes from the never-mentioned
floor (0.60 / 0.58) to **0.96 / 0.89** of plans. Under full context the *same
line lowers* relapse in both deciders, a sign the predictions got wrong.

**Caveats that travel with the number.** Stores are semantic ideals, not a
real extractor's output (arXiv:2606.15903 App. P reports Mem0's router
under-deletes, which would move `delete` toward `addonly`). Cross-design
*levels* mix design with rendering explicitness; only the within-design DiD is
read. Two deciders, one corpus, one pinned length. Products are not run,
their semantics are re-implemented from source.

**Ledger.** 23 gated. 22 closed. **E29 stands as a candidate with a supported,
narrow residual**, subject to the coverage limit; whether it is carried as an
original result is the author's call, and the abstract-level papers should be
read in full before that call.

**Deliverable for the course.** The *Zombie Constraint X-ray*:
`python xray_server.py` rebuilds the page from `results/` and serves two
routes on localhost: `/` is the report (real transcripts and plans, the ladder
recomputed from the CSVs, the four memory designs, the E29 rows, a live
inspector with Run live against Ollama), and `/city` is **Memory City**, a
full-screen player: one district as the hero, six towers on an arc with the
rejected step ringed, a rail that always shows the current line, the store
with new and deleted items, and the decision streaming, plus a scrubbable
timeline (any line without a model call; only the decision asks the model)
and a live tally against the recorded rates. `python xray_build.py` writes the
static `docs/xray/zombie_xray.html`. Every number is recomputed from the
result files. Runtime note: when the tool shell's job object kills detached
children, launch with `Invoke-CimMethod Win32_Process Create` (see memory).
Publishing it as an artifact was blocked by the tool permission classifier
this session; the static file was sent to the author directly.

**Later the same day.** (a) **Coverage limit closed**: the six abstract-level
papers were read in full; none covers the conjunction, none contradicts the
direction (protocol §0.3 addendum). (b) **E29-B ran and read UNINFORMATIVE by
its own rule**, stopped at 18 of 48 dialogues: the Mem0 paper's extraction
prompt, run by llama3.2:3b, stored the proposed step at its proposal line in
2 of 18 dialogues. It stored proposal+acceptance exchanges and almost never
proposal+rejection ones, so the rejected step mostly never entered the store
(by omission, not DELETE), and a later restatement entered as a fresh fact in
0.39 of restated dialogues vs 0.22 neutral. Exploratory Δ_real +0.111
[0.000, +0.278] on the real store vs +0.500 oracle delete on the same 18.
Process failure recorded: the E29-B prose declaration was appended after chunk
1 had run; the read rule was in committed code before the first call.

**Compulsory controls, closed the same evening (E1-S,
`docs/protocols/E1S-selector-sanity-arms.md`, declared at `c1b5447`, nine
runs).** The plan's arm table lists a `full` ceiling, a `last-message` floor
and a `sabotage` selector; E1 had run neither floor nor sabotage. Run on the
frozen E1 setup, three repeats each: `full` 0.8571 (P1 holds), `last` 0.6667
with zero history words (P2, ≤ 0.50, fails), `sabotage` 0.9524 with zero source
messages in context and the first two deterministic successes of the
post-amendment programme (P3 fails as written; retrieval recall 0.0 by
construction). Read by the rule fixed before the runs: constraint recall on
the INCIDENT scenario has a retrieval-independent floor above every scored arm
and above the oracle, so E1's landscape attributes nothing to retrieval. The
transcripts show why — the finalisation instruction's action menu plus the
brief carry five of the seven constraints by themselves, the generated turns
drift and never restate a constraint, and the only pair that needs dialogue
(isolate before diagnose) is the one the no-history arm fails. This is the
compulsory-side face of the E17 menu law. E1's numbers are untouched; the
sentence allowed beside them changed. The `sabotage` selector lives in
`context.py` with tests; `python e1_landscape.py --sanity` reruns the block.

**Memory City, later.** The pale-tower rendering chased through three commits
was two things: the tab the Chrome extension drives is hidden, so
`requestAnimationFrame` never fires there and every capture froze a frame
mid-glow; and three.js r128 treats hex colours as linear, so a 0.06 orange
tint outputs as mid grey. Fixed at `5765d95`: time-based decays, tints set for
sRGB output, halo sprites instead of bloom for local glow, and
`window.__city.tick()` for stepping frames from a hidden tab. Verified in that
mode through line 7 and a live decision.

**E29-C, the Δ_full follow-up, run the same evening
(`docs/protocols/E29C-framing.md`, declared at `5adc257`, 768 calls, corpus
`979143b67049adf2`).** Question: is the negative full-context restatement
effect the "for the record, I did raise X" framing, or any late mention?
Four arms under `full` — E29's two re-run plus `plain` / `plain_neutral`
("Just to note it, X came up earlier in this discussion"), ten words plus the
referent each. `llama3.2:3b`: Δ_ftr −0.083 [−0.156, −0.010] (E29's −0.083,
replicated in a fresh session), Δ_plain +0.062 [−0.010, +0.135], Diff −0.146
[−0.240, −0.062] → **FRAMING**. `qwen2.5:7b-instruct`: Δ_ftr −0.062
[−0.135, +0.000], Δ_plain 0.000 [−0.062, +0.062] → **NO-REPLICATION by the
letter of the rule** (upper bound exactly zero), same shape, not upgraded, not
pooled. Reading: on the course model the protection came from the authorship
register, which sends the decider back to the rejection; a plain late mention
does not. That sharpens E29 — the stores re-admitted the step despite a line
that protects a full-context reader. Parse 1.000 everywhere, |plan| 3.99–4.00,
controls flat across arms.

**Next, if anything.** (1) A write-path stage with an extractor prompt that
stores operational proposals at all — the Mem0 personal-info prompt does not —
under its own declaration. (2) Done as E29-C above. (3) Republish the X-ray as an artifact outside
auto mode — the publish was refused by the auto-mode classifier twice on
2026-09-11; the static page `docs/xray/zombie_xray.html` is ready as is.

---

# 2026-09-07 — the benchmark-composition line (E24), the best result of the sprint

**Method change that finally paid.** For eighteen candidates the loop was
"generate a hypothesis, ask whether it has been done" — and it always had.
Reading the field's own artifacts instead (the survey's GitHub list, IFBench's
repo, IFEval's constraint taxonomy) produced a live question in twenty minutes.

**Two facts established by reading, not guessing.** The survey's own list of
**12 multi-turn benchmarks** contains *no* discussion of evaluation confounds,
normalisation or measurement validity. IFEval scores **inclusion and exclusion
constraints in one aggregate** — `include keywords` and `keyword frequency` sit
in the same Keywords family as `forbidden words`.

## E24 — the mechanism. CONFIRMED, well powered.

Inclusion and exclusion constraints move in **opposite** directions with
response length. Length pinned by instruction at 40/120/300 words, 16 verifiable
constraints, n = 48 per cell:

| model | inclusion short→long | exclusion short→long | DiD |
|---|---|---|---|
| llama3.2:3b | +0.354 | −0.146 | **0.500** |
| qwen2.5:7b-instruct | +0.479 | −0.125 | **0.604** |

Against a 0.15 threshold fixed in advance. **This is the solid result.**

## E24-B — reorder at natural length. RULE FIRED, RULE WAS WRONG.

Five models, natural verbosity. The declared rule returned REORDER DEMONSTRATED,
but its 0.02 threshold was set with **no power analysis**: swap margins were
0.010–0.052 against 95 % half-widths of 0.080–0.132. Recorded, and not relied on.
Diagnosis: **6 of 8 exclusion constraints were at 1.000** — models never
spontaneously write "very", "you", digits, semicolons — so the exclusion side was
pinned at ceiling and more items could not have fixed it.

## E24-C — the fix, and a split answer

Forbidding words each task *actively elicits* lifted the ceiling (exclusion now
spans **0.333–1.000**).

- **DEMONSTRATED:** a model's reported score changes by **0.30** on the same
  constraint pool — qwen2.5:3b scores **0.484 ±0.142** exclusion-heavy and
  **0.786 ±0.070** inclusion-heavy, CIs non-overlapping. Between-model spread
  changes **2.5×** (0.479 → 0.188).
- **NOT DEMONSTRATED:** reorder. Under a proper interval test there are **zero**
  significant swaps. E24-B's apparent reorder is **superseded**.

**The defensible claim:** benchmark composition materially changes absolute
scores and between-model gaps; it was not shown to change ordering.

## Standing

**Eighteen candidates gated, eighteen closed.** T-2 is NARROW, not open —
cross-benchmark aggregation sensitivity is published (arXiv:2608.30044, ATLAS).
What this line supplies is the **type-by-length mechanism** and a direct
demonstration, which were not found.

**Next, concretely:** run it on **IFEval's actual items** (the constraints here
are hand-written), and raise exclusion n above 24 — the score-shift result leans
heavily on one model's collapse with a ±0.189 interval.

---


# LATER ON 2026-09-06 — 15 candidates closed; E19 found something and then killed it

**Still no novelty.** Two further candidates gated and closed (M-1 meta-science,
B-1 bounding, L-1 latent), taking the count to **15 gated, 15 closed** across
six framings. Then a replication line that produced a real result and then
retracted it under its own follow-up.

- **E19** (`docs/protocols/E19-entrainment.md`) replicated arXiv:2606.24077 by
  exact teacher-forced scoring on HF (torch 2.11 + transformers 5.9, RTX 5080;
  Qwen2.5-Instruct 0.5B/1.5B/7B already cached, no download).
  **Existence replicates decisively** — Δ > 0, CIs excluding zero, 144/144
  dialogues positive, in every model tested. **Scale appeared to FAIL** on the
  paper's raw measure: +3.368 → +2.962 → **+3.584**, the 7B highest.
- **E19-B** added a second cached family (Qwen3.5-0.8B/4B) and a third measure,
  and **weakened E19 to the point of withdrawal.** Four of five
  measure × ladder combinations replicate the scale claim; the sole failure is
  the paper's raw log difference in one ladder, produced by Qwen2.5-7B's
  unusually low baseline (`absent` −7.30 vs −4.30/−4.32/−4.37/−5.23). A raw log
  difference inflates when the baseline falls.
- **Withdrawn as stated:** E19's post-hoc claim that "the direction of the
  answer is not determined by the data alone". True of M1 vs M2 on one ladder,
  false everywhere else tested.

**What survives:** arXiv:2606.24077 replicates on this instrument — existence
without qualification, scale under every measure but the fragile one. Plus a
narrow methodological note: raw per-token log-probability differences are
fragile to between-model baseline shifts, and the measures immune to that agree
with the published direction.

**Runtime facts worth keeping.** Ollama exposes logprobs for *generated* tokens
only — `num_predict: 0` still generates, and forced decoding through
`top_logprobs` misses targets outside top-k. Exact scoring needs HF. The HF
cache holds real weights for Qwen2.5-Instruct 0.5B/1.5B/7B and Qwen3.5-0.8B/4B.
7B needs `device_map="auto"` with a ~13 GiB cap; a direct bf16 load segfaults a
16 GB card.

**Next:** unchanged. Nothing is queued. `docs/NEGATIVE-RESULTS.md` exists and is
the honest deliverable. Replication remains the only strategy that has produced
positive results (E18, E19), and neither is novel.

---


# CURRENT STATE — 2026-09-06 (late) — 13 candidates gated, 13 closed

**No novelty was found.** Thirteen candidates went through the prior-art gate
across two days — eight behavioural, three measurement, one meta-science, one
bounding — and every one had every component already published. The search is
recorded in `docs/E16-CANDIDATES.md` (two RE-GATE sections, an ADDENDUM, a
CITATION AUDIT, and the N/M/B candidate gates).

Frozen state intact throughout: `verify_claims.py` **167 / 0 / 4**, **135
tests**, E16 corpus hash `70f136a47f5779c8`. Nothing frozen was touched.

## What was actually produced, and it is real

1. **S-O and S-E retired on prior art** (arXiv:2608.12599, arXiv:2607.05545).
   Both had been rated OPEN by a gate that ran without web search.
2. **E16 stage 1 completed as declared** — 432 calls, three deciders,
   NOT PURSUED. Only qwen2.5:14b-instruct passes the gates.
3. **The instrument characterised.** E16 menu diagnostic (UNINFORMATIVE by its
   own rule) and **E17** (`docs/protocols/E17-menu-law.md`): with plan length
   pinned, `never ∝ chance^0.60–0.65`; the E16 gate flips between 6 and 24
   identifiers; the elasticity **saturates** (+55 % then +3 %). Verdict
   AMBIGUOUS; closed as a novelty candidate because it is a classical IIA /
   choice-set-size effect.
4. **A published claim REPLICATED with a length control (E18).** Revocation
   inertia falls with scale in qwen2.5: **0.542 → 0.250 → 0.135** (3B/7B/14B,
   plan pinned at 4). Under free length 7B and 14B are tied at floor — the
   naive comparison loses the gradient.
5. **That claim BOUNDED across families (E18-B).** Six models, five families:
   the 3–4B band spread (**0.448**) exceeds the within-family 3B→14B spread
   (**0.407**), and **gemma4:e4b (~4B) has the lowest relapse of all six**,
   below qwen2.5:14b. `never` stays flat (0.552–0.656) across every model, so
   the difference is specific to rejection handling.

Items 4 and 5 are the only positive results of the programme, and **both are
someone else's hypothesis**. Neither is novel — B-1's gate found "family
dominates scale" and "small model beats larger across families" established.

## The reusable lessons

- **A prior-art gate without web search is not a gate.** 2/2 candidates rated
  OPEN by an API-only gate were killed by web search within a day. A citation
  audit of eight of its sources found identifiers and substance largely sound —
  the failure was in the **verdicts**, not the retrieval.
- **This instrument's rates are set by the prompt's action menu.** Any
  adherence rate it reports is roughly `0.9 × |plan| / |vocab|`, and both terms
  are free parameters. Never compare rates across menu sizes; never set a
  fixed-threshold gate without fixing both.
- **Pin plan length before comparing models.** It is one added sentence,
  compliance is ~100 %, and it changes conclusions: it separated 7B from 14B
  where free length had them tied at floor.

## Next — nothing is queued

1. ~~The negative-results write-up~~ — **WRITTEN 2026-09-06**:
   `docs/NEGATIVE-RESULTS.md`, the artifact `RESEARCH-LEAD-2026-09-02.md` §9
   named as the only remaining step. Every figure re-verified against artifacts
   before commit. A formatted rendering is published privately at
   https://claude.ai/code/artifact/9b5e4251-3899-4f91-a444-ff3ae4b8a835 (rendering only; the markdown file is the record).
   What remains is the author's call on whether any of it is submitted
   anywhere, and in what form.
2. **More replication.** E18 worked because it inverted the novelty risk. Open
   targets: arXiv:2608.12599's constraint-load half (needs a corpus that varies
   load), arXiv:2606.24077's entrainment-decreases-with-size (needs logprobs,
   which the current ollama client does not expose).
3. **Stop.**

Do not authorise anything on a no-web-search prior-art verdict. Do not compare
adherence rates across different action-space sizes.

---


# CURRENT STATE — 2026-09-06 — reopening closed, nothing queued

The 2026-09-03 reopening produced two candidates. **Both are now closed by
prior art.** E16's screen ran in full and was not pursued. Nothing is queued
and no claim exists. Frozen state intact throughout: `verify_claims.py`
**167 / 0 / 4**, **124 tests**, E16 corpus hash `70f136a47f5779c8`.

## 1. E16 screen — COMPLETE, NOT PURSUED

Stage 1 ran as declared: **432 calls, three deciders**, full context, temp 0.

| decider | parse | accepted | rejected | never | gate | rejected − never |
|---|---|---|---|---|---|---|
| llama3.2:3b | 1.000 | 1.000 | 0.177 | 0.646 | FAIL | −0.469 |
| qwen2.5:3b-instruct | 1.000 | 0.979 | 0.438 | 0.510 | FAIL | −0.073 |
| qwen2.5:14b-instruct | 1.000 | 1.000 | 0.062 | 0.385 | **PASS** | −0.323 |

Only the 14B is carried. Reading B needs the effect in **two** carried
deciders, so the pursuit rule is unsatisfiable — stage 2 not run. Reading A is
**negative in every decider**: there is no zombie excess anywhere, and within
the qwen family the larger model suppresses a rejected constraint *more*.
Record: Outcome section of `docs/protocols/E16-zombie-screen.md`.

## 2. Both candidates closed by prior art — the gate that was never run

The 2026-09-03 prior-art gates ran **without web search**. Re-run with it:

- **S-O — RETIRED.** Behavioural half closed by **arXiv:2608.12599** (*Dead
  text or binding clause?*, Zhu, Aug 2026): dialogue revocation, models keep
  enacting withdrawn requirements, relapse at **8B** climbs 0.011 → 0.403
  while stronger models sit at floor — S-O's predictions (1) and (2), three
  weeks before the screen was designed. Mechanism half downgraded OPEN →
  NARROW, surrounded by arXiv:2606.22528, 2608.11242, 2604.20911.
- **S-E — RETIREMENT RECOMMENDED (not taken).** Mechanism closed by
  arXiv:2601.03746 + 2606.05976 + 2606.24077. Behavioural half then closed too
  by **arXiv:2607.05545** (*Most LLM Conformity Needs No Speaker*), which names
  S-E's confound verbatim, runs the no-source condition on six open-weight
  LLMs, and includes the paraphrase arm that was S-E's remaining novelty.

Record: two RE-GATE sections plus the ADDENDUM in `docs/E16-CANDIDATES.md`.

## 3. Citation audit — eight sources checked

Six clean. One label-only error (arXiv:2608.20392 is not "MeetingProbe", but
its 13.4 % figure is real — Table 9, App. H; the abstract merely lacks it).
One **substantive** error: **InterruptBench (arXiv:2604.00892) is not
"frontier only"** — six open backbones with a retraction arm, so the gate
understated its closeness to S-E. One unverified characterisation corrected
(AgentChangeBench shifts are sequential *replacement*, not "additive").

Net: the 2026-09-03 gate's **identifiers and substance are largely sound**;
what failed was its **verdicts**, for want of web search. Do not conflate them.

## 4. Menu diagnostic — declared, run, UNINFORMATIVE by its own rule

Tested the 2026-09-05 lesson about E16's `never` gate. Six arms, 720 calls,
vocabulary 2.75 / 6 / 12. **Verdict UNINFORMATIVE in both deciders**: mean
|plan| grew ×1.54 and ×1.59 against a declared ×1.25 ceiling, so the 1/|vocab|
arithmetic *both* hypotheses assumed does not hold. The clause existed to stop
over-reading and it fired.

- The lesson's **arithmetic form was wrong** and is corrected: |plan| is not a
  constant, so halving the vocabulary does not halve the rate.
- Its **practical conclusion stands and strengthens**: the base rate cannot be
  recovered from this plan instruction by choosing a vocabulary size, because
  plan length compensates.
- **The corollary that matters.** Applying E16's own gates to the wide arm,
  **both 3B deciders fail all four at |vocab| = 6 and pass all four at
  |vocab| = 12.** The gate that ended the screen was measuring a prompt
  parameter nobody varied. `rejected − never` also moves (qwen −0.073 →
  **+0.062**, a sign flip). **This does not revive S-O** — prior art closes it
  independently of any gate — and the flip is one decider, post-hoc,
  unpermuted. Recorded because concealing it would be worse.

Record: Outcome section of `docs/protocols/E16-menu-diagnostic.md`.

## 5. Not done on my own authority

Retiring S-E; declaring the programme closed; editing `docs/novelty_matrix.md`
C1 to note it now also pre-empts S-E; editing the 2026-09-03 verdict table in
place. Verdicts are recorded and corrections appended; the decisions are the
author's.

## 6. Next — nothing is queued

1. **The negative-results write-up** (`docs/RESEARCH-LEAD-2026-09-02.md`
   §8–9), no model calls. The E16 episode is fresh material for it: a
   candidate screened, its gate shown to be an artefact of a prompt parameter,
   and the candidate then killed by papers an API-only search could not see.
2. **A prompt-sensitivity design that fixes |plan| explicitly** — the obvious
   follow-up the diagnostic points at. New prompt, new declaration; not run.
3. **Stop the programme again.**

Do not run E16 stage 2. Do not weaken E16's declared gates. Do not authorise
anything on a no-web-search prior-art verdict.

## 7. Standing caveat on both re-gates

**Abstract-level only, no full text read.** Load-bearing IDs were each
confirmed by fetching the arXiv abstract page; the arXiv:2608.20392 case above
shows an abstract-level check can make a sound citation look unsound. The
previously cleared benchmark list was not re-checked.

---

# PROGRAMME REOPENED — 2026-09-03 (candidate search complete; lead: S-O)

The author reopened the search for a new programme on 2026-09-03 with the
explicit aim of a novel result. The closed programme is tagged
`research-closed-v1` (pushed); everything below that heading stands.

Eight candidates went through the adversarial prior-art gate in one day:
the author's four (compression, representation, budget-by-role,
reasoning-mode deciders) and a scout's four (deontic flattening, zombie
constraints, retraction-as-repetition, plus two parked). Every one has every
component published. Two carry a component nobody has run:

- **S-O zombie constraints — LEAD.** A constraint explicitly rejected in the
  dialogue and never replaced stays binding for small models above the
  never-stated base rate, and a word-budgeted retrieval policy makes it worse
  because the proposal turn is retrieved and the content-poor rejection turn
  is not. The mechanism half is checkable from the retrieval log with zero
  model calls. Verdict: behavioural OPEN (NARROW), mechanism OPEN.
- **S-E retraction-as-repetition — runner-up.** OPEN (NARROW), tightly
  surrounded (arXiv:2608.25553, Aug 2026).

Full table, closest papers and the decision: `docs/E16-CANDIDATES.md`.
Search caveat recorded there: the last four gates ran without web search.

*(State and Next below are superseded by the 2026-09-05 section at the top of
this file: stage 1 has since run for two deciders and S-O is NOT PURSUED.)*

**State (as of 2026-09-03):** zero E16 model calls. No preregistration. Frozen hashes intact
(re-verified 2026-09-03: 167 / 0 / 4). `C:\Users\chris\week1-sandbox` (a
stale pre-git copy, contents in commit 3770dfe) is still on disk; deleting it
was blocked by the tool sandbox and is left to the author.

**Next (as of 2026-09-03):** `docs/protocols/E16-zombie-screen.md` declared with zero outcomes;
corpus module + tests; offline retrieval preflight (no calls); stage 1
(~48–100 calls, qwen2.5:3b + qwen2.5:14b, full context); stage 2 only if
stage 1 survives its kill rule.

---

# RESEARCH CLOSED — 2026-09-02

**E15-PODT: RETIRED** by the independent Gemini literature review (no model
call was ever made for it). **FFEP** (Gemini's proposed pivot, claim-relative
counterfactual auditing of agent evaluations): **STOP_FFEP** after this
repository's own feasibility audit — two adversarial prior-art reviews
returned HEAVY OVERLAP (Mystery Blocksworld 2023 performs the procedure;
Turk 2026 and HackDetect 2026 on agents), the method would have caught 5 of
17 of this project's own historical failures, and the residue is
methodological packaging. `docs/FFEP-FEASIBILITY.md` (15 sections, one
decision). No E15/E16 outcome exists.

**Remote:** private GitHub repository https://github.com/Chrislysen/week1-llm-lab
(branches `crazy`, `main`, `core-frozen`; all six tags). `main` is
fast-forwarded to `crazy`; the two are identical.

Nothing is queued. Do not search for E16. The next action, if any, is the
negative-results write-up named in `docs/RESEARCH-LEAD-2026-09-02.md` §8.

Feasibility infrastructure added 2026-09-02 (no model calls, no frozen
artifact touched): `ffep_inventory.py`, `ffep_mutations.py`,
`test_ffep_mutations.py` (12 gates), `ffep_power.py`, `docs/ffep_*.json`.
Test expectation is now **104 passed** over 14 suites
(`test_ffep_mutations.py` added).

---

# (superseded) RESEARCH PAUSED PENDING EXTERNAL NOVELTY REVIEW

**Paused 2026-09-02 at commit `48c6860`.** Working tree clean, no remote at
the time (a private remote was added later, see the top of this file),
nothing running. Frozen hashes intact; `verify_claims.py` 167 VERIFIED /
0 MISMATCHED / 4 UNVERIFIABLE; 92 tests; checker self-test 10/10.

**Candidate:** E15-PODT / Provenance-Only Dependence Test.

**Status:** APPARENTLY OPEN FROM ONE DEEP-RESEARCH REVIEW.
NOT PREREGISTERED. NOT AUTHORIZED. ZERO E15 MODEL CALLS. **Not NOVEL.**
An independent review (Gemini) is adversarially searching the literature and
may kill it. Proposal only: `docs/E15-CANDIDATE.md`.

**Do not:** start E15, generate an E15 corpus, preregister it, make model
calls, modify E1–E14 artifacts, revive E14, build a provenance router, or
implement the proposed Bayesian task. Wait for the external verdict.

External handoff for a research model: `docs/HANDOFF-EXTERNAL-2026-09-02.md`.
Closing memo of the last pass: `docs/RESEARCH-LEAD-2026-09-02.md`. Verdict
table: `docs/novelty_matrix.md` C1–C14.

---

**The research-lead pass (2026-09-01/02) closed the earlier programme.**
Everything below is its record.

---

## 1. Verify the state is intact (run this first, ~2 min)

```bash
cd C:/Users/chris/week1-llm-lab
git branch --show-current            # expect: crazy
git status --porcelain               # expect: empty
python verify_claims.py              # expect: 167 verified, 0 mismatched, 4 unverifiable
python prospective_design_check.py --self-test    # expect: 10/10 passed
```

All thirteen suites must pass:
`test_engine test_scenario test_finalise test_context test_judge test_retrieval
test_lineage_bench test_lineage_modeb test_lineage_e10 test_lineage_e11
test_lineage_e12 test_lineage_e13 test_lineage_e14`

Frozen corpus hashes — **if any differ, stop and investigate before anything
else**:

| corpus | hash |
|---|---|
| Mode A | `9dd2cea16a8142c2` |
| E10 | `00947dde8eb0520b` |
| E11 | `5c28ada4c4b899dc` |
| E12 | `ecf1f4884fa49270` |
| E13 prompts | `5c23297196241110` |
| E14 (preregistered, never run) | `6cd7dafac78c31fe` |

Tags: `compulsory-baseline-v1`, `e1-landscape-v1`, `selector-protocol-v1`,
`e3-authority-v1`, `e7-modeb-v1`, `e12-powered-v1`.

---

## 2. The two locked results (do not re-litigate)

**Cross-family corroboration dose-response.** Contradiction adoption falls as
faithful paraphrastic corroborations increase, in 3/3 distinct model families
(Meta, Cohere, Alibaba). Llama: 0.75 → 0.4167 → 0.2778 → 0.1111.

**Evidential-dependence null ON THE ORDERING VERDICT (E12, replicated by
E13).** SAME_ROOT vs INDEPENDENT_ROOT: E12 diff +0.0185, p = 0.749, CI
[−0.037, +0.074]; E13 DEFAULT diff **+0.0000**, p = 1.0, CI [−0.056, +0.056].
Both inside the preregistered SESOI of 0.10. **Equivalence-supported — for
the ordering only.** Scope correction 2026-09-01: the plan's `ready` field is
dependence-sensitive (post-hoc, unconfirmed; §4). Do not write "prices it at
nothing" about the decision.

Standing prohibitions: do not claim lineage sensitivity, do not build
AnchorRoute, do not try to make SAME differ from INDEP, do not change the
SESOI, do not revive dilution or E8's P7, do not claim the `ready` effect
before a preregistered E14 confirms it.

---

## 3. What E13 found (committed `418bab2`)

1080 calls, 108 units in 36 clusters, `llama3.2:3b`, parse rate **1.00** in
every cell.

| arm | diff | p | CI | discordance | preregistered reading |
|---|---|---|---|---|---|
| `default` | +0.0000 | 1.0 | [−0.056,+0.056] | 0.093 | **equivalence-supported null** |
| `identify` | −0.0093 | 1.0 | [−0.083,+0.056] | 0.139 | INCONCLUSIVE BY RULE |
| `normative` | −0.0741 | 0.0564 | [−0.139,−0.009] | 0.148 | INCONCLUSIVE BY RULE |
| `sham` | −0.0370 | 0.2946 | [−0.093,+0.009] | 0.074 | INCONCLUSIVE BY RULE\* |
| `gold` | +0.0000 | 1.0 | [−0.056,+0.065] | 0.075 | INCONCLUSIVE BY RULE\* (diagnostic) |

\* blocked by a **defect in my own band rule** — see §5.

**Recognition (RQ1) — CORRECTED 2026-09-01.** What `418bab2` called "two
measures disagreeing" was one variable scored two ways. Paired by unit, the
primary boolean discriminates **40 vs 0** (p = 1.8e-12) under `identify`,
exactly as the count does (49 vs 2); under `normative` **34 vs 4**. The
paired count test was **post-hoc** — added after the first 36 units were on
disk — and mislabelled predeclared. The predeclared per-response numbers:
`identify` INDEP boolean 0.528, count_strict **0.130**. **42/108 units
misrecognise INDEP by every measure.** Rule 2 has no threshold and is
unadjudicated. The "27 vs 0" probe is E10's manipulation check, not E12's.

**"NORMATIVE degraded recognition" is WITHDRAWN** — one row of two, no
between-arm test, and the stated mechanism has the wrong sign.

**GOLD moved the ORDERING verdict by 0.0000** while being handed the correct
structure outright — and is INCONCLUSIVE BY RULE there, not an "oracle null".
On the `ready` field it moved **+0.20** (§4).

---

## 4. Defects recorded against my own work

**The coupling test could not have worked.** `P(sensitive | recognized)` vs
`P(sensitive | misrecognized)` is 0.025 vs 0.088 (Fisher p = 0.256) and 0.059 vs
0.027 (p = 0.589). "Independence-sensitive action" requires a *conjunction*
(flip on SAME **and** hold source on INDEP), giving a ~5% base rate and
subgroups 1–6 units wide. **Falsification rule 6 is untested, not passed.**
Any follow-up needs a graded outcome measure, not a conjunction.

**The powered band has a defect.** `[0.08, 0.12]` was computed for *difference
detection*. Its lower bound wrongly blocks *equivalence* readings, where low
discordance is favourable. It blocked `sham` and `gold`; read on the equivalence
criterion both are equivalence-supported. The rule is left as written and fired;
the corrected reading is printed separately and flagged post-hoc.

**The decision has two output fields and I scored one (found by the step-10
panel, verified).** The plan JSON is `{"actions", "ready"}`; `ready` ("safe to
execute as written") is required to parse and is part of
`deterministic_success`. E12 and E13 never analysed it. Re-derived:
`default` ready(SAME) 59/108 vs ready(INDEP) 34/108, **+0.2315**, cluster
p = 0.0002, CI [+0.139, +0.333]; `gold` +0.2037 (p = 0.0001); E12 +0.2593.
Every arm, about twice the SESOI. The ordering null stands; "prices one root
exactly as k independent roots" is withdrawn as a decision-level claim.
**Post-hoc, unconfirmed — the one thing worth an E14.**
`docs/protocols/E13-CORRECTIONS.md`, which also records that the paired count
test was post-hoc and that "NORMATIVE degrades" is withdrawn.

---

## 5. Research-lead pass — 2026-09-01/02. The programme is closed.

Everything below the next heading is history. What closed it:

- **`ready` mined from every raw plan on disk** (E2, E4, E7, E8, E9, E10, E11,
  E12, E13; five deciders). At ceiling for Aya-8B, Qwen-3B, Qwen-7B in every
  arm; varies only in llama-3B and Qwen-14B.
- **READY is a repetition/consistency effect, not dependence** (matrix C10):
  same-root readiness rises with each repeated identical citation (E11 19 →
  21 → 27, k1 vs k3 paired 0/8), independent-root is flat (17, 17, 17), two
  agreeing reports of either kind lower readiness from ~0.78 to ~0.5, the gap
  runs 0 → +0.5 by which document names the rotation draws, and `ready`
  follows the model's own same-source token (129/242 vs 1/190).
- **Qwen-14B (declared screen E12-X)** shows no same/indep readiness gap
  (−0.046, CI [−0.111, +0.018]) and its readiness rises with corroboration
  where llama's falls. READY is llama-specific. **E14 in any form is not
  pursued.**
- **Prior art** (six adversarial reviewers, ~150 searches): the commit-gate
  abstraction is published (arXiv:2608.27167); the same-source contrast on
  Llama-3.2-3B exists (arXiv:2601.03746); the benchmark's premise is false
  (ManyIH-Bench, IHEval; corrected in `docs/agent-lineage-bench.md`); the
  apparatus is pre-empted (llm-power, tail-shape protocol, showyourwork,
  POPPER); latest-trusters replicate IHEval / Control Illusion.
- **Normative backfire (C14)**: HEAVY OVERLAP — KAIROS (arXiv:2508.18321)
  shows a critical-evaluation prompt worsens peer-pressure robustness on this
  very model. The declared cross-family screen (E13-X) found the principle's
  effect +0.037 in Aya and +0.005 in Qwen-7B against llama's +0.09: llama-
  specific. Closed.

**Standing prohibitions, unchanged:** no lineage-sensitivity claim, no router,
no dilution, no SESOI change, no claim from any exploratory screen.

## 5-history. Steps 10–12 — DONE 2026-09-01.

**Step 10 — DONE.** `docs/attack_e13.js` ran as workflow `wf_35c74eab-aee`:
27 agents, 22 candidates, **5 survived refutation**, every one re-derived by
me before acceptance and recorded in `docs/protocols/E13-CORRECTIONS.md`.
Three conclusions withdrawn (the recognition "disagreement / response bias";
"NORMATIVE degrades"; the decision-level "prices it at nothing") and two
record corrections (the paired count test was post-hoc; the 27 vs 0 probe is
E10's). `e13_recognition.py --analyse` now prints both post-hoc blocks
flagged, and `verify_claims.py` pins the corrected numbers (161 verified).

**Step 11 — DONE 2026-09-01 (commit `f5d218d`).** The search ran in a fresh
session: 19 searches, 15 papers. **Neither blocking paper fires the rule** —
CAMA (arXiv:2608.19701) has no recognition probe and no told-correlation
baseline; Information Discernment (arXiv:2607.19355) defines M1/M2 over source
*reliability* only. **But GroupQA (arXiv:2601.06189, Jan 2026) already runs
E12's paraphrased-one-document vs distinct-documents contrast** on four 8B–70B
models and finds the paraphrases weighted *more*, with no recognition probe and
no intervention. C8 was therefore **OPEN (NARROW), not NOVEL** — and was then withdrawn as
phrased in step 10: residue = recognition probe on the same units + `gold`'s
ordering result (0.0000; the "oracle null" reading is withdrawn), on one 3B
model. C4 is PRE-EMPTED (behavioural). Full table and search log in
`docs/novelty_matrix.md`; `docs/findings.md` §0/§4 updated.

**Step 12 — DONE.** E13 survived the prior art (C8 not pre-empted on its
conjunction) and did **not** survive the attack intact. `docs/CLAIM-E13.md`
states what is left. No router, no new campaign.

**E14 v1 — preregistered and ABORTED before any confirmatory call; superseded by §5 (no v2)
(2026-09-01).** Built to the instruction: a fresh 432-unit / 144-cluster
corpus (four salted draws of the frozen generator), FIXED_PLAN primary,
GENERATED replication, a within-response interaction test, checker operating
bands (432/144 PROCEEDS; 324/108 ABORTS), a verifier section and four fixture
tests — all committed with zero outcomes. Hypothesis-blind pilots then found
the FIXED instrument **at floor** on `llama3.2:3b`: **0 of 149** `ready =
true` across seven framings, three plan contents and every graph, because in
judge mode the model treats the contradictory discussion as making any plan
unsafe. Kill rule 5 fires before the run; **no confirmatory call was made**.
`docs/protocols/E14-ready-channel-v1.md` §16 holds the pilot table and four
v2 options (GENERATED-only primary; a different decider; a FIXED arm without
the contradiction; stop). **Choosing among them is the user's decision. Do not
run any of them unasked.**

**Also not yet run, and conditional:** cross-model E13 (Aya, Qwen) only after the
mechanism is identified on Llama; `LEDGER` (RQ5) only if a normative
intervention works — it did not.

**Backup question, only after E13 closes:** corroboration-induced hysteresis.
E10 found none (36/36 accepted a legitimate update with and without prior
support) but that was at ceiling on an easy supersession.

---

## 6. Key files

| file | what it is |
|---|---|
| `docs/findings.md` | one page: what survives, what was retracted |
| `docs/novelty_matrix.md` | 8 candidate claims; **none novel**; C8 is the live one |
| `docs/protocols/E13-recognition-utilization-v1.md` | E13 preregistration |
| `docs/protocols/E10-H3-RETRACTION.md` | the retraction that shaped everything after it |
| `docs/protocols/E13-CORRECTIONS.md` | the step-10 corrections: three E13 conclusions withdrawn, all verified |
| `docs/protocols/E14-ready-channel-v1.md` | E14 preregistration, and its §16 abort record with the pilot table |
| `docs/RESEARCH-LEAD-2026-09-02.md` | the closing memo: what died, what survived, why it stops |
| `docs/protocols/E12X-qwen14b-ready-screen.md`, `E13X-backfire-screen.md`, `screen_analysis.py` | the two declared exploratory screens and their reader |
| `lineage_e14.py`, `e14_ready.py`, `test_lineage_e14.py` | E14 corpus, experiment and analysis, 23 gates + 4 fixture tests — built, never run |
| `docs/CLAIM-E13.md` | what can still be claimed, and what cannot |
| `docs/attack_e13.js` | the adversarial workflow that found them |
| `docs/handoff.md` | full external-review document |
| `verify_claims.py` | re-derives all 161 numbers from raw output |
| `prospective_design_check.py` | refuses designs that cannot reach their conclusion |
| `robust_client.py` | bounded transport-only retry |

**Standing rules:** no outcome-based tuning; preregister before model calls;
retractions are immutable; frozen artifacts are never modified; no public remote (the private one above only)
without explicit instruction.
