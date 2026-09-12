# E30 — feasibility assessment for a human-written corpus. NOT DECLARED.

Written 2026-09-12. **This is a scoping document, not a protocol.** No
predictions are fixed here and nothing may be run against it. When E30 is
declared it will be a separate file with its own zero-outcome commit.

The paper's standing main limitation is that both corpora are generated from
templates. The second Gemini scout was pointed at corpora for exactly this
(`docs/gemini-research-log/2026-09-12-run2-triage.md` §4). This assesses
whether the best candidate can actually carry the E29 construct.

## 1. The candidate: CaSiNo

Chawla, Ramirez, Clever, Lucas, May and Gratch, NAACL 2021, pages 3167–3185.
1,030 human-human negotiation dialogues in which two participants play
campsite neighbours dividing packages of food, water and firewood, each with
a private preference ordering, ending in an agreed allocation.

**Licence: CC BY 4.0**, read from the repository's own LICENSE file
(`raw.githubusercontent.com/kushalchawla/CaSiNo/main/LICENSE`, "Attribution
4.0 International"), not from a secondary source. A derived annotated corpus
may therefore be released with attribution. That clears the blocker that
rules out AMI, whose CC BY-NC-**ND** licence forbids derivatives.

`fetch_casino.py` downloads it to a gitignored `data/casino/`; the data is
not committed.

## 2. Census, measured 2026-09-12

| quantity | count |
|---|---|
| dialogues | 1,030 |
| dialogues carrying the authors' strategy annotations | 396 |
| free-text utterances (excluding the four deal markers) | 11,919 |
| utterances containing a quantified offer of an issue | 3,604 |
| utterances containing an explicit decline cue | 458 |
| offer-then-decline pairs (partner declines within two turns) | 222 |
| **dialogues with at least one such pair** | **176** |
| structured markers | Submit-Deal 1,181 · Accept-Deal 1,005 · Reject-Deal 167 · Walk-Away 25 |

The decline rule is deliberately narrow and excludes counter-offers, which
are the commonest implicit rejection in negotiation but are a different
speech act. 176 usable dialogues is therefore a lower bound, and it is
already larger than E29's 96.

## 3. How the construct maps, and where it does not

| E29 | CaSiNo |
|---|---|
| a proposed operational step | a quantified offer, "could I have 3 firewood, 1 food" |
| a partner rejecting it | the partner's explicit decline within two turns |
| the executable plan | the agreed final allocation, available as structured `task_data` |
| the outcome, deterministic | whether the declined offer's terms appear in the allocation the decider writes |
| the manipulated line | **has to be inserted.** CaSiNo is observational: the humans cannot be re-run |

**The honest limit.** Inserting the restatement makes that one line synthetic
even though every surrounding line is human. This does not remove the
templating objection, it narrows it from the whole corpus to a single
sentence, and the neutral control is matched to that same sentence. Any E30
write-up must say so in those words.

**A consequence worth noting.** CaSiNo has no scorer tags, so no oracle store
can be rendered from it. E30 is necessarily a real-extractor experiment and
inherits E29-D's machinery, where the operational extraction prompt stored
the proposed step in 0.958 of dialogues. That is a point in its favour: the
leg that most needs naturalistic data is the one already built to run
without oracle tags.

## 4. What would have to be built

1. An annotation pass fixing, per dialogue, the declined offer and its terms
   as a quantity triple. The lexical rule above is the recall filter; the
   terms need parsing, and a sample needs hand-checking against the rule.
2. The restatement and neutral arms: one inserted line by the original
   proposer, matched on length, in the register of the surrounding human text
   rather than in E29's template.
3. A scorer over allocations rather than over an action menu, which also
   removes the pinned-plan and menu-prior artefacts in one step.
4. A prior-art gate pass of its own, run within the fortnight before
   declaration, per the standing lesson in §0.3d of the parent protocol.

Estimated as the largest single piece of work left in the programme, and the
one that would move the paper from a workshop result to a submittable one.

## 5. Not decided

Whether to run it at all is the author's call. The alternative reading is
that E29 plus its six legs is a complete short paper as it stands, and that
E30 is a second paper rather than a section of this one.
