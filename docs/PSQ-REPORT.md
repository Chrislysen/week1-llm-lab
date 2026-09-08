# PSQ — plan-selection qualification: FAILED

Run 2026-09-08 under `docs/protocols/PSQ-plan-selection-qualification.md`
(declared at commit `9114db0`, zero outcomes). Allocation: 36 attempts.

## Verdict

**FAILED. 0 of 8 fixtures succeeded on all four assignments**, against the
declared threshold of ≥6/8.

**32 of 36 attempts spent.** 0 transport retries, 0 missing, 0 unresolved
failures — qualification is **complete**, not incomplete. 4 reserve attempts
unused. 7 984 prompt + 416 completion = **8 400 tokens**, 78 s.

## All 32 outcomes, by quartet

| fixture | domain | score | chosen (assignments 0–3) | correct |
|---|---|---|---|---|
| 0 | payments | 1/4 | P2 P2 P2 P2 | P4 P1 P3 P2 |
| 1 | robotics | 1/4 | P2 P2 P2 P2 | P2 P4 P1 P3 |
| 2 | pharmacy | 1/4 | P1 P1 P1 P1 | P4 P2 P1 P3 |
| 3 | satellite | **2/4** | P4 P4 P3 P3 | P2 P4 P3 P1 |
| 4 | brewery | 1/4 | P3 P3 P3 P3 | P2 P3 P4 P1 |
| 5 | rail | 1/4 | P3 P3 P3 P3 | P2 P4 P3 P1 |
| 6 | payments | 1/4 | P3 P3 P3 P3 | P2 P4 P1 P3 |
| 7 | robotics | 1/4 | P2 P2 P2 P2 | P3 P1 P2 P4 |

Total **9 / 32 = 0.281**. A responder that ignores the messages entirely and
picks one fixed label per fixture would score **0.25** by construction, since the
correct label rotates over all four options within each quartet.

**Assignment variants are not independent task families.** The unit is the
fixture: **8 units**, scored 1,1,1,2,1,1,1,1.

## The repair worked for what it was for — and the failure moved

**The generation burden is gone.** 32/32 parsed, 32/32 `ready=true`, zero
malformed outputs, zero unknown identifiers.

**Corrected (2026-09-08).** An earlier draft said Phase B's ordering-violation
mode "does not appear". That is wrong: a wrongly selected plan **is** a
constraint violation — its sequence violates F1 and/or F2 exactly as a
mis-ordered constructed plan would, and `score_option` records those violations.
What disappeared is the requirement to **generate** the sequence, not the
violation itself.

**The decoded choice did not change with the delivered facts.** In **7 of 8
quartets the receiver returned the identical label for all four assignments.**

**Narrowed (2026-09-08).** Unchanged decoded labels bound the **observed output**;
they do **not** establish a complete absence of conditioning. The facts could
shift the distribution without moving the arg-max, and this design records only
the decoded label. An earlier draft's "does not respond to the delivered facts"
is withdrawn in favour of the observational statement. Verified at
zero cost that within a quartet the *only* prompt differences are the two fact
lines — the option block is byte-identical, and every within-quartet diff is a
fact sentence:

```
-We cannot cycle the settlement engine until we shift routing to the spare region.
+We cannot shift routing to the spare region until we cycle the settlement engine.
```

Those two sentences are exactly what determines the answer. The chosen label
does vary *across* fixtures (P3 ×14, P2 ×12, P1 ×4, P4 ×2), so the decoded output
tracks something held constant within a quartet — options, action names,
distractors — while showing **no observed variation** with the message content
the task turns on.

## What this establishes, and what it does not

**Establishes.** On these 8 plan-selection fixtures, with this receiver
(`llama3.2:3b`, `temperature 0.0`, single call, full pool delivered): choices
were well-formed, and the **decoded label was unchanged across the four fact
assignments in 7 of 8 quartets**. Observed success 9/32, near the 0.25 a
message-ignoring responder would obtain.

**PSQ did not test message REMOVAL.** Every one of the 32 calls delivered the
**full pool**; which messages were present never varied. So PSQ says nothing
about whether removing messages changes performance, and nothing about
message-selection of any kind.

**Does not establish.**

- Not that the receiver *cannot* use such messages — a different phrasing,
  prompt, decoding setting or model may differ. One display order per fixture
  was tested; **robustness across option permutations is untested**.
- Not a position law. Chosen options sat at display positions 4, 2 and 3 and
  never at 1, but the choice is constant within a quartet, so these are **8
  fixture-level observations, not 32** — far too few for a position claim.
- Not message-selection **headroom** — message presence was never varied.
- Not **transfer**, not **novelty**.
- Not a statement about larger receivers, which this allocation excludes.

## Consequence for the research target

The target — transferable recipient-conditioned bundle selection at lower
execution cost — **presupposes that the receiver's decision responds to which
messages it receives.** On this instrument no such response was observed: the
decoded choice did not change under a manipulation that changed the correct
answer every time.

That is the more useful negative. Phase B said the receiver could not *construct*
a valid plan; PSQ adds that with construction removed entirely, the decoded
choice still showed no observed variation with the delivered facts. A subset
study measures which bundles help, which is hard to read while the observed
choice does not move with the bundle. Whether it moves at all under *removal*
is untested here — see the PSD diagnostic.

**No subset study is prepared.** The protocol's instruction to prepare one was
conditional on passing, and it did not pass.

## Standing

Receiver calls stop here. The declared allocation is closed at 32 of 36 attempts;
the 4 unused reserve attempts do **not** carry forward. Phase B stays frozen.
No Phase C, larger model, recovery backend or further campaign is authorised, and
none is implied by this result. The direction has not passed
`docs/NOVELTY-GATE.md`; the ledger stays 22 gated, 22 closed.
