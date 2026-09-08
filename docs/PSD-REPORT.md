# PSD — clean-evidence removal diagnostic: MIXED

Run 2026-09-08 under `docs/protocols/PSD-clean-evidence-diagnostic.md` (declared
at commit `88193ab`, zero outcomes). **A diagnostic, not a qualification gate —
no pass threshold was applied.**

**33 of 36 attempts spent** (1 transport retry, 0 missing, 32/32 parsed). 8 092
tokens, 125 s. 3 attempts unused and not carried forward.

## Paired outcomes — all 16 cells

| fixture | assignment | full | clean | chosen full/clean | correct |
|---|---|---|---|---|---|
| 0 | 0 | ✗ | ✗ | P2 / P2 | P4 |
| 0 | 1 | ✗ | ✗ | P2 / P2 | P1 |
| 0 | 2 | ✗ | ✗ | P2 / P2 | P3 |
| 0 | 3 | ✓ | ✓ | P2 / P2 | P2 |
| 1 | 0 | ✓ | ✓ | P2 / P2 | P2 |
| 1 | 1 | ✗ | ✗ | P2 / P2 | P4 |
| 1 | 2 | ✗ | ✗ | P2 / P2 | P1 |
| 1 | 3 | ✗ | ✗ | P2 / P2 | P3 |
| 2 | 0 | ✗ | ✗ | P1 / P1 | P4 |
| 2 | 1 | ✗ | ✗ | P1 / P1 | P2 |
| 2 | 2 | ✓ | ✓ | P1 / P1 | P1 |
| 2 | 3 | ✗ | ✗ | P1 / P1 | P3 |
| **3** | **0** | ✗ | **✓** | **P3 / P2** | P2 |
| 3 | 1 | ✓ | ✓ | P4 / P4 | P4 |
| 3 | 2 | ✓ | ✓ | P3 / P3 | P3 |
| **3** | **3** | ✗ | **✓** | **P3 / P1** | P1 |

**Totals: full 5/16, clean 7/16.** Two discordant pairs, **both clean-better,
none full-better**.

## All-four-correct counts by fixture

| fixture | domain | full | clean | all four correct |
|---|---|---|---|---|
| 0 | payments | 1/4 | 1/4 | full ✗ · clean ✗ |
| 1 | robotics | 1/4 | 1/4 | full ✗ · clean ✗ |
| 2 | pharmacy | 1/4 | 1/4 | full ✗ · clean ✗ |
| **3** | satellite | 2/4 | **4/4** | full ✗ · **clean ✓** |

**Fixtures with all four correct: full 0/4, clean 1/4.**

## The one informative cell

Fixture 3 under `clean` chose **P2, P4, P3, P1** across assignments 0–3 — exactly
the correct label each time. That is the **only** place in PSQ or PSD where the
decoded choice tracked the fact orientation. Under `full` the same fixture gave
P3, P4, P3, P3.

Fixtures 0–2 returned a **fixed label under both conditions**: removal changed
nothing there.

## Verdict: MIXED, and the caveats are load-bearing

- **Both discordant pairs come from the same fixture.** The unit of independence
  is the fixture, so this is **one fixture of four**, not two independent wins.
  An exact sign test on 2 discordant pairs gives p = 0.5 even before that
  dependence is accounted for. **Nothing here is statistically distinguishable
  from noise.**
- **Clean was never worse.** That is the direction, on 4 development fixtures.
- **Removal changes content, length and position together.** Any difference
  concerns **the removal intervention as a whole** and does **not** isolate a
  semantic-distraction mechanism. The two noise sentences differ from the facts
  in topic, in length, and in where the facts then sit.
- These are **four existing development fixtures**, not fresh confirmation data.
- `clean` is an **oracle evidence control** — the subset was chosen from
  construction metadata a deployed selector would not have. **No selection method
  was evaluated, and none is validated by this.**

## What it does establish

**The fixture family is solvable by this receiver.** Fixture 3 under clean
evidence went 4/4 with the choice tracking the facts. So the construction, the
scoring, the response contract and the prompt are not the blocker, and PSQ's
0/8 was not an artefact of an unsolvable task.

**But three of four fixtures showed a fixed choice even with clean evidence.**
Removing the noise was not sufficient there.

## Recommendation

**Yes — qualifying one stronger receiver is worth it, and it is the cheapest
remaining discriminator.** The reasoning:

- The task is now demonstrably solvable in this exact setup (fixture 3, clean),
  so a further failure could no longer be blamed on fixture construction.
- The remaining explanation for 3/4 fixtures is receiver capability, and that is
  directly testable with a single small qualification arm.
- Everything downstream — any subset study, any selector comparison — needs a
  receiver whose decisions move with the messages. Without one there is nothing
  to select for, and no amount of fixture work supplies it.

Scope: one receiver, one declared qualification arm, its own allocation. If a
stronger receiver also shows fixed choices on these fixtures, the direction
should be reported as blocked at the receiver and stopped rather than repaired
again.

**This is a recommendation, not an authorisation.** No larger model, prompt
search, easier fixtures, subset campaign or Phase C is authorised or implied.

## Standing

Model calls stop here. PSQ's failed verdict and records stay frozen; Phase B
stays frozen. The research target remains held-out selection quality at lower
execution cost. **This diagnostic establishes no novelty.** Ledger stays 22
gated, 22 closed.
