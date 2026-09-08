# PSD — clean-evidence removal diagnostic

**Status at declaration: ZERO OUTCOMES. No model call has been made.**
Declared 2026-09-08, before any run.

**A NEW diagnostic allocation: 36 attempts = 32 scheduled + 4 transport-only
retries.** PSQ's failed verdict and its records stay frozen; PSQ's 4 unused
reserve attempts are **not** carried here.

**This is a diagnostic, not a qualification gate.** There is no pass threshold.

## Wiring audit completed first (zero model calls)

Required before any further calls, and reported by evidence type:

- **Captured, by intercepting the real code path:** all four assignment payloads
  for fixture 0 are distinct, differ exactly in the fact line, and are byte-equal
  to `render_prompt`. Request options were `{temperature: 0.0, num_predict: 300,
  seed: 0}`.
- **Captured, from the PSQ log:** all 32 rendered inputs distinct; re-scoring
  every logged response reproduces the logged `chosen` and `success`, so scored
  identifiers came from their corresponding responses; latencies 2.12–11.11 s
  show no cache signature.
- **Code inspection only (not execution evidence):** the runner logs the same
  variable it sends; no cache exists anywhere in the client stack.
- **Uninformative:** server-reported `prompt_eval_count` is constant within each
  quartet — expected, since swapping a fact's orientation reorders words without
  changing the token count. It neither confirms nor contradicts.

**No wiring defect found.**

## Precondition checked (zero model calls)

PSQ's full pool was {A, B, C, D}: the two necessary fact messages **plus two
noise messages** carrying no ordering fact. Removable messages therefore exist
and the comparison below has a true premise. Verified for all 16 cells that
deletion **preserves both necessary facts**, removes only the noise, **leaves the
correct answer unchanged**, and leaves the recipient context, option block and
instruction byte-identical.

## Design

- **Fixtures 0–3, all four fact assignments.** These are four **existing
  development fixtures**, not fresh confirmation data.
- **Two conditions per cell:** `full` = {A, B, C, D} (as PSQ delivered) and
  `clean` = {A, B} only. **4 × 4 × 2 = 32 calls.**
- **`clean` is an ORACLE EVIDENCE CONTROL.** The subset is chosen from
  construction metadata — which messages carry the facts — which a deployed
  selector would not have. **It is not a deployable selector and no selection
  method is being evaluated.**
- **Held identical between conditions:** fact wording, task instruction,
  recipient context, option→label mapping, display order, model, decoding and
  scoring. Only the two noise messages are removed.
- **The `full` condition is RE-RUN here.** Historical PSQ outcomes are **not**
  used as the experimental comparator.
- **Collection.** 16 process blocks, one per (fixture, assignment), 2 calls each.
  Condition order is **counterbalanced**: `full` first when
  `(fixture + assignment)` is even, `clean` first otherwise — balanced within
  every fixture (2/2) and within every assignment across fixtures (2/2).
  Literal requests, raw responses, request positions, process identifiers and
  costs are logged.
- **Wrong answers, refusals and malformed outputs are OUTCOMES, not retries.**
  The 4-attempt reserve covers transport failures only; an unresolved transport
  failure is logged as MISSING.

## Reporting

Paired outcomes per cell and **all-four-correct counts by fixture**, for both
conditions. No threshold is applied.

## What a difference would and would not mean

Removal changes **content, length and position together**. A difference would
concern **the removal intervention as a whole** and would **not** isolate a
semantic-distraction mechanism.

- **Clean works while full fails** → a reason to reconsider full-pool
  qualification.
- **Clean also performs poorly** → the report recommends whether qualifying one
  stronger receiver is worth it. That recommendation is not authorisation.
- **Mixed** → reported as mixed.

## Not authorised

No automatic prompt search, no easier fixtures, no full subset campaign, no
Phase C, no larger model, no recovery backend. The research target remains
held-out selection quality at lower execution cost; **this diagnostic
establishes no novelty.** Ledger stays 22 gated, 22 closed.
