# PSQ — plan-selection qualification

**Status at declaration: ZERO OUTCOMES. No model call has been made.**
Declared 2026-09-08, before any run.

**A NEW allocation.** The failed Phase B campaign stays frozen and its 264
unspent attempts are **not** carried here. Ceiling: **36 attempts = 32 scheduled
calls + 4 transport-only retries.**

**What this run is for.** Whether the *repaired receiver task* is usable. The
research target is unchanged and untouched by this run: transferable
recipient-conditioned bundle selection at lower execution cost.

## Design

- **Cases.** The 8 existing repair fixtures (`plansel_fixtures.build_quartet`),
  each evaluated at **all four assignments** of the two binary ordering facts:
  **8 × 4 = 32 calls.**
- **Held fixed within a fixture:** the option→label mapping, the display order,
  the action identifiers and descriptions, and the unrelated distractor text.
  **Only the two fact orientations change**, and they change consistently
  everywhere they appear — in the delivered message text *and* in the constraints
  used for scoring.
- **Consequence, verified not assumed:** because the label map and display order
  are fixed bijections, the four assignments make **four different options
  correct, at four different display positions**. Verified for all 8 quartets.
- **Both facts arrive through the message interface.** Recipient context is
  `knows_neither`; the delivered bundle is the **full pool {A, B, C, D}** —
  the two fact messages plus the two distractors. This is the ceiling condition
  of the intended subset study, and it is the same convention Phase B's
  qualification used.
- **Label assignment and display order are independently generated across
  fixtures** (separate seeds), so answer identity and answer position are not
  the same variable.
- **No answer is revealed** by fixture ids, filenames, recorded metadata or
  prompts. The collection schedule carries **no** correct label; the scorer
  recomputes it from the constraints at scoring time.

## Receiver and collection

- **Same receiver and decoding as Phase B:** `llama3.2:3b`, `temperature 0.0`,
  `num_predict 300`. **Each case is a fresh conversation** — one user message, no
  history.
- **8 process blocks, one per fixture, 4 calls each.** Assignment order inside a
  block is randomised from a fixed seed; realised **request position** is
  recorded, along with process identity, literal input, literal output and token
  costs.
- **These are DIFFERENT INPUTS, not repeated realisations.** Gate S is not reused
  and no independence is inferred from them.

## Qualification rule (operational, declared before outcomes)

> **PASS if at least 6 of the 8 fixtures succeed on ALL FOUR assignments.**
> Success requires executable validity **and** `ready=true`.

**This threshold is a feasibility choice.** It is not a power calculation and it
is not a threshold established by any cited paper.

Reported regardless of verdict: **all 32 outcomes** and the **8 quartet scores**
(0–4 each). **Assignment variants are not independent task families** and are
never counted as 32 units.

## Attempt accounting

| item | attempts |
|---|---|
| scheduled calls | **32** |
| transport-only retry reserve | **4** |
| **ceiling** | **36** |

- **Wrong answers, refusals and malformed outputs are OUTCOMES, not retry
  opportunities.** They are scored as failures and never re-run.
- **The reserve covers transport failures only** (connection/5xx). Every retry is
  logged and consumes the ceiling.
- **An unresolved transport failure is reported as MISSING**, and qualification is
  marked **INCOMPLETE** — never attributed to receiver capability.
- **No smoke calls.** Construction was validated with zero model calls.
- **No prompt or fixture tuning between outcomes.**

## What passing does and does not establish

Passing establishes **observed performance on these plan-selection contrasts**
with this receiver and these settings. It does **not** establish:

- message-selection **headroom** (that needs the subset table),
- **robustness across option permutations** (only one display order per fixture
  is tested),
- **transfer** to other tasks, receivers or families,
- **novelty** of anything.

Failing means the repaired task is still not usable and the next change is again
to the task or the receiver — not to the analysis.

## Standing

No Phase C, no larger model, no recovery backend and no further campaign is
authorised. The direction has not passed `docs/NOVELTY-GATE.md`. Ledger stays
22 gated, 22 closed.
