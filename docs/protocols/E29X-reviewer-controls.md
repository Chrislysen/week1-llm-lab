# E29-X — two reviewer controls: rendering (E29-R) and a tombstone design (E29-T)

Declared 2026-09-12 with **zero outcomes**. Source of the two controls: the
adversarial review returned by the first Gemini Deep Research scout
(`docs/gemini-research-log/2026-09-12-triage.md` §3, objections 2 and 4).
Not a novelty candidate; a robustness leg of E29
(`docs/protocols/E29-memory-semantics.md`).

## 0. The two objections, in the reviewer's terms

- **Rendering (objection 2).** "The observed difference may be an artefact
  of how the context block is rendered to the decider." E29 already confines
  its read rule to within-design contrasts for this reason and reports levels
  without comparing them. The control that would let levels be compared: show
  the transcript's rejection with the store's explicitness.
- **True by construction against add-only (objection 4).** "A naive add-only
  baseline cannot retract; the result is trivial. A soft-supersede baseline
  with a tombstone flag is the industry mitigation to compare against." E29's
  result runs the other way (add-only protects; delete re-admits), but the
  tombstone design is a real fifth point between them and is worth a
  measurement on its own terms.

## 1. Design

Corpus: the E29 corpus (hash `187a426616f26598`), 96 dialogues, both arms,
unchanged. Deciders: `llama3.2:3b`, `qwen2.5:7b-instruct`,
`qwen2.5:14b-instruct` (gemma4:e4b if time allows). Prompt, temperature,
validator, read rule and validity rule: E29's. Three designs per dialogue,
run in one session so the reference is fresh:

| design | what the decider sees | code |
|---|---|---|
| `full` | E29's transcript, re-run as the same-session reference | `context_block("full")` |
| `full_explicit` (E29-R) | the transcript with every accept/reject reply's bare referent ("that one", "that", "it") replaced by the store's referent "the proposal to {phrase}"; every other character unchanged; header unchanged | `lineage_e29x.explicit_dialogue` |
| `tombstone` (E29-T) | the delete store with the rejected proposal *retained and flagged* "[withdrawn] …" instead of removed; nothing else stored for the rejection; the restatement ADDed fresh; same header as delete / add-only | `lineage_e29x.store_tombstone` |

Tests (`test_lineage_e29x.py`): the explicit rendering changes only reply
lines and names only its own action; the tombstone store equals the delete
store plus exactly one flagged line and contains no rejection fact; headers
match E29's. The hash over every E29-X block, `aa043cc25c027b1a`, is pinned in `e29x_controls.py`.

**Allocation.** 96 × 2 × 3 = **576 calls per decider**, chunked at 32
dialogues (192 calls) for the 3B and 7B deciders and 16 for the 14B, into
`results/e29x_<model>_o<offset>.csv/.json`. Read with `e29x_analysis.py`.

## 2. Predictions, fixed before the first call

- **R1 (rendering).** If E29's level gap between `full` and `addonly` in the
  neutral arm (3B: 0.281 vs 0.177; 7B: 0.312 vs 0.344; 14B: 0.167 vs 0.062)
  was the explicitness of the rejection's referent, `full_explicit`'s neutral
  level will land closer to add-only's than `full`'s does, and below E29's
  `full` neutral level with an interval that excludes it. Read: **RENDERING**
  if both hold, **DESIGN** otherwise. The author's lean: RENDERING on the 3B
  decider, DESIGN on the 14B, where levels are already low.
- **R2.** Δ_full_explicit stays negative or near zero on the small deciders:
  the register effect (E29-C) is about the inserted line, which is untouched.
- **T1 (tombstone).** Δ_tombstone lies between E29's Δ_addonly and Δ_delete
  for the same decider. Read by E29's SESOI on the DiD against the
  same-session `full`: **FLAG NOT HONOURED** (behaves like delete) if
  |DiD| ≥ 0.15 with an interval excluding 0; **FLAG HONOURED** (behaves like
  add-only) if |DiD| < 0.05 with the interval inside ±0.15; **BETWEEN**
  otherwise. Author's lean: NOT HONOURED on the 3B (a bracket is weaker than
  a sentence saying "rejected"), HONOURED on the 14B.
- **T2 (control).** `never` and `accepted` inclusion within 0.10 across the
  three designs per arm.

## 3. What cannot follow

R1 speaks to the *levels* E29 declined to compare; it does not touch E29's
within-design DiD verdicts, which hold rendering constant by construction.
T1 adds a fifth design; whatever it shows, the E29 residual (a partner's
restatement of a dialogue-rejected step re-enters the plan through hard
delete and not through add-only) is neither widened nor narrowed by it. One
corpus, three deciders, oracle stores.

## 4. Outcome — run 2026-09-12, after `7f89477`

576 calls per decider (llama in four chunks of 24, qwen 7B in four of 24,
qwen 14B in six of 16). Parse 1.000 / 0.998 / 1.000 (one parse failure on the
7B, so 95 complete dialogues there); mean |plan| 3.98–4.00; all cells valid.
`results/e29x_<model>_o*.csv/.json`, `results/e29x_<model>_summary.json`.

Rejected-step inclusion (n = 96, 95, 96) with the same-session `full`
reference; E29's `addonly` and `delete` cells quoted for the level and Δ
comparisons the predictions name.

| decider | design | restated | neutral | Δ | 95 % CI | DiD vs full | 95 % CI |
|---|---|---|---|---|---|---|---|
| `llama3.2:3b` | full (same session; E29: 0.198 / 0.281) | 0.198 | 0.281 | −0.083 | [−0.167, −0.010] | reference | |
| | full_explicit | 0.271 | 0.281 | −0.010 | [−0.063, +0.042] | +0.073 | [+0.000, +0.146] |
| | tombstone | 0.646 | 0.625 | +0.021 | [−0.042, +0.073] | +0.104 | [+0.010, +0.208] |
| | *E29 addonly / delete, neutral* | | *0.177 / 0.604* | *+0.010 / +0.354* | | | |
| `qwen2.5:7b-instruct` | full (E29: 0.240 / 0.312) | 0.242 | 0.316 | −0.074 | [−0.147, +0.000] | reference | |
| | full_explicit | 0.232 | 0.316 | −0.084 | [−0.147, −0.032] | −0.011 | [−0.095, +0.063] |
| | tombstone | 0.463 | 0.421 | +0.042 | [−0.021, +0.105] | +0.116 | [+0.021, +0.221] |
| | *E29 addonly / delete, neutral* | | *0.344 / 0.583* | *−0.031 / +0.302* | | | |
| `qwen2.5:14b-instruct` | full (E29: 0.219 / 0.167) | 0.219 | 0.167 | +0.052 | [−0.021, +0.125] | reference | |
| | full_explicit | 0.156 | 0.167 | −0.010 | [−0.083, +0.052] | −0.062 | [−0.146, +0.021] |
| | tombstone | 0.635 | 0.292 | +0.344 | [+0.250, +0.438] | **+0.292** | [+0.177, +0.396] |
| | *E29 addonly / delete, neutral* | | *0.062 / 0.635* | *+0.000 / +0.260* | | | |

**Replication first.** The same-session `full` cells reproduce E29's to
within 0.004 on all three deciders (0.198/0.281, 0.242/0.316, 0.219/0.167
against 0.198/0.281, 0.240/0.312, 0.219/0.167). That is the third
independent replication of the E29 full cells on the 3B model.

**R1 — DESIGN on all three deciders.** Making every reply's referent explicit
("the proposal to snapshot the store" in place of "that one") leaves the
neutral-arm level of the transcript exactly where it was: 0.281 → 0.281,
0.316 → 0.316, 0.167 → 0.167. The gap to add-only's level (0.104, 0.028,
0.104) does not move. The level difference E29 declined to compare is not the
explicitness of the rejection's referent; it is the design. The author's
lean (RENDERING on the 3B) was wrong. One observation beside the prediction:
on the 3B decider the explicit transcript loses the register effect
(Δ −0.010 against −0.083; DiD +0.073 [+0.000, +0.146]). With referents spelt
out, "for the record, I did raise it" no longer sends the decider anywhere
it has not already been. On the 7B the register effect stays (−0.084).

**R2 holds.** Δ_full_explicit is near zero or negative on the small deciders.

**T1 — BETWEEN on the 3B and 7B, FLAG NOT HONOURED on the 14B.** The
declared lean was the reverse (not honoured on the 3B, honoured on the 14B)
and is recorded as a miss. What the cells show:
- In the *neutral* arm a retained-but-flagged proposal is enacted at 0.625 /
  0.421 / 0.292 — far above add-only's explicit rejection (0.177 / 0.344 /
  0.062) and, on the small deciders, at the same level as delete's absence
  (0.604 / 0.583). A "[withdrawn]" bracket is not read as a rejection; on
  the 3B it is read as nothing at all.
- In the *restated* arm the flagged line blunts the re-admission on the
  small deciders (0.646 / 0.463 against delete's 0.958 / 0.885) but not on
  the 14B (0.635, Δ +0.344, DiD +0.292 with an interval clear of zero). The
  largest decider honours a sentence that says "rejected" (add-only 0.062)
  and does not honour a flag once the step is mentioned again.
- Δ_tombstone lies between Δ_addonly and Δ_delete on all three, as T1's
  first clause predicted.

**T2.** Accepted-step inclusion 0.983–1.000 everywhere. Never-mentioned
inclusion is within 0.10 across designs in every neutral arm; in the
restated arm it drops under tombstone by 0.146 (3B: 0.604 → 0.458) and
0.125 (14B: 0.729 → 0.604), which is displacement: the pinned four-step plan
has one slot fewer once the zombie step takes one. Reported, not explained
away.

**What this changes.** The reviewer's rendering objection is answered
empirically: levels across designs may now be compared, and the ordering
delete > tombstone > full ≈ full_explicit > addonly holds in the neutral arm
on every decider. The reviewer's "true by construction" objection is
answered by adding the mitigation they named: a soft-supersede flag is not a
substitute for storing the rejection; on the largest decider it behaves like
deletion as soon as the step is restated. Nothing here widens the E29
residual; it removes two ways of explaining it away.

## 5. Preemption of T1, recorded 2026-09-12 after the run

The second Gemini Deep Research scout surfaced **arXiv:2609.08258, "Revoked
but Still Authoritative: An Empirical Study of Revocation Enforcement in
Agent-Memory Systems"** (Shen, Toyoda and Leung, submitted **2026-09-08**,
three days before the E29 gate and four days before this run). Read in full.

They load five shipped systems (Graphiti, mem0, Zep, langmem, cognee) with a
revoked policy and its replacement across nine scenarios × nine models × six
defence conditions, and find that no system enforces revocation by default:
on the two systems that expose the flag the revoked fact is returned in 81/81
scenarios, outranks its replacement, and produces the unsafe action in 43.1 %
of 1,620 trials (15–60 % by model). A store-level filter takes it to zero.

**T1's headline is theirs, published first.** "A rejection retained behind an
invalidation flag is not honoured" is their result on shipped systems with
nine models; ours is the same claim on an oracle store with three local
deciders, run four days later and declared without knowledge of it. The
declaration stands as written and is not rewritten; this section is the
correction.

**What survives as this protocol's own, checked against their §C.1 and §C.2.**
They have no later re-mention of the revoked item by any party: §C.1 is the
agent journalling its own decision, §C.2 is three roles querying one store.
So Δ_tombstone under a partner's restatement (+0.021, +0.042, **+0.344**;
DiD +0.104, +0.116, **+0.292** on the 3B, 7B, 14B) has no counterpart there,
and neither does the finding that the flag partly protects the small deciders
in the neutral arm and fails on the largest once the step is restated.
Their failure is also partly a *ranking* failure — the revoked record
outranks its replacement — which cannot arise here, because the whole store is
rendered and nothing is retrieved.

**What the two together support, and neither supports alone.** They test
systems that delete, prune, or flag. None stores the rejection as prose beside
the proposal. This protocol's add-only arm does, and it is the arm that
protects: neutral-arm enactment 0.177 / 0.344 / 0.062 against tombstone's
0.625 / 0.421 / 0.292. The claim that follows is about *encoding*, not
presence, and it is carried into the paper draft:

> A superseded step's fate is decided by how the rejection is written, not by
> whether it is stored. The same rejection carried as a sentence is honoured;
> carried as a metadata flag it is not.
