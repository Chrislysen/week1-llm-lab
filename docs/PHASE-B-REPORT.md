# Phase B — outcome: qualification gate FAILED, campaign stopped

Run 2026-09-08 under `docs/protocols/PHASE-B-bundle-observability.md` with
Amendments 1–3, authorised at a ceiling of 288 model-call attempts.

## Headline

**Gate Q failed 0/8 against its declared ≥6/8 threshold. The declared stop rule
fired, so the 256 subset evaluations were NOT run.** The receiver cannot solve
this task family at full evidence, so no subset outcome could have been read as a
communication effect.

**24 of 288 attempts spent. 264 unspent.**

## Call accounting

| item | attempts | note |
|---|---|---|
| qualification (8 fixtures × 2 realisations, own process block each) | **16** | declared |
| subset evaluations | **0** | **not run — stop rule fired** |
| exploratory diagnostic (from the 16-call reserve) | **8** | see §4 |
| **total** | **24 / 288** | 0 transport retries, 0 failed attempts |

Cost: 7 069 prompt + 1 001 completion = **8 070 tokens**, 63 s wall clock. Mean
rendered bundle at full evidence: **52.9 words**. Every attempt is logged in
`results/phaseb_calls.jsonl` with rendered input, output, check vector, failure
mode, request position, process block and token counts. `check_vector` is present
on every call (nothing went unparsed).

## 1. Gate Q — FAILED

| fixture | r1 | r2 | agree | both succeed |
|---|---|---|---|---|
| brewery-chain | violation/2 | violation/2 | Y | · |
| payments-fork | violation/1 | violation/1 | Y | · |
| pharmacy-star | violation/1 | violation/1 | Y | · |
| pharmacy-twochain | violation/2 | violation/2 | Y | · |
| rail-diamond | violation/3 | violation/3 | Y | · |
| robotics-chain | violation/2 | violation/2 | Y | · |
| satellite-fork | violation/2 | violation/**3** | **N** | · |
| satellite-join | violation/1 | violation/1 | Y | · |

**0 of 8** fixtures succeeded on both realisations. Threshold was ≥6/8.
Mean violations at full evidence **1.81**; mean constraint recall **0.736**.

## 2. Gate S — PASSED, which makes the failure interpretable

**1 of 8** fixture pairs disagreed across processes (threshold: stop if ≥3/8).
Cross-process instability is low, so **the 0/8 is not decoding noise** — the
receiver reproducibly fails. Recall these realisations ran in *separate
processes* precisely because `temperature 0.0` makes same-process repeats
bit-identical (Amendment 1).

## 3. What kind of failure it is — ordering, not comprehension

| signal | value |
|---|---|
| outputs that parsed | **16 / 16** |
| unknown action names | **0** |
| duplicated actions | **0** |
| required actions missing | 1 fixture (pharmacy-star), deterministic across both runs |
| violations by kind | **27 `before` (ordering) vs 2 `required`** |
| `ready=true` while violating | 8 / 16 — the silent-failure half again |

The receiver emits valid JSON, uses only the offered identifiers, includes almost
all required actions, and **puts them in the wrong order**. This is the same
constrained-ordering failure B1 recorded and that PlanBench documents; the
failure mode taxonomy added in Amendment 3 is what makes it readable — a bare
"failure" label would have shown 16 identical zeros.

By graph: diamond 3.0, chain 2.0, twochain 2.0, fork 1.8, join 1.0, star 1.0 mean
violations. **n = 1–4 fixtures per graph; this is description, not a shape effect.**

## 4. Reserve diagnostic — EXPLORATORY, does not revive the gate

The stop rule directs "fix task/receiver qualification first". B1 obtained 6/24
with a **five-call** pipeline whereas Phase B is **single-shot**, so the one
question worth 8 reserve calls was whether the single-call design is the binding
constraint. Each fixture's own full-evidence answer was fed back with an explicit
instruction to check every ordering rule one at a time.

**Result: 1 of 8 recovered**, and that one (pharmacy-star) was the
*missing-required* case, not an ordering case. Mean violations moved 1.750 →
1.625. Two fixtures got worse.

**A self-check refinement step does not fix this receiver on this task.** This is
exploratory, is not part of the declared table, and the Q verdict stands.

## 5. What the evidence establishes — and what it cannot

**Establishes.** `llama3.2:3b` at temperature 0, single-shot, on 6-action
constrained ordering with full evidence: 0/8, reproducibly (S passed), failing on
ordering rather than parsing, vocabulary or omission, and not rescued by
self-checking.

**Does not establish anything about communication.** No subset table exists.
Gate H (headroom) is **unanswered, not answered negatively** — it required the
256 calls the stop rule forbade.

**On whether selection headroom remains: unknown, and deliberately not guessed.**
The tempting inference — full evidence is the most-informed condition, so
subsets must also fail — is exactly the monotonicity assumption Amendment 3
added `smaller_succeeds_when_full_pool_fails` to *test*. Asserting it here would
import the assumption the analysis exists to check.

**A protocol tension worth recording.** The stop rule forbids collecting the
subset table until qualification is fixed; that table is also the only thing that
could show whether a smaller bundle succeeds where the full pool fails. The rule
is still right — a floor-level receiver makes every subset comparison
uninterpretable — but the ordering means the non-monotonicity question cannot be
asked until the receiver clears the floor.

**Design observation, not a cause.** Under `knows_A`, candidate A's constraint
appears in both the recipient context and the bundle, so the full-evidence
qualification prompt carries one redundant line. That is by design (it is the
redundancy contrast), it removes no information, and ordering violations
dominate — but a future qualification arm should use a variant without the
duplication.

## 6. Concrete next step

**One step, and it is not more calls on this receiver.** The study is about
communication; it is currently measuring an ordering-capability floor. Before any
subset table is worth collecting, qualification must pass, which means changing
the *task difficulty* or the *receiver*, then re-running the 16-call gate:

1. **Reduce ordering load** — fewer actions or shallower chains, so the receiver
   clears the floor while the message-combination structure is preserved. Cheapest
   and keeps the family. Requires new fixtures and a re-declared gate.
2. **A larger receiver** — likely sufficient, but **explicitly outside this
   authorisation**: the protocol puts further models in their own separately
   counted allocation.
3. **Redefine the decision point as a multi-call pipeline** — but §4 shows one
   refinement step does not clear it, and this changes what "a recipient decision"
   means, so it needs its own declaration.

Option 1 is the recommendation. **264 attempts remain unspent under this ceiling
and are not carried into any new gate** — a re-declared qualification arm gets its
own accounting.

## Standing

Phase B established observability machinery and a receiver floor; it established
**no** communication result, **no** headroom finding and **no** novelty. Phase C
remains unauthorised and is further away than before, not closer. Frozen
artifacts untouched, corpus `70f136a47f5779c8` unchanged. Ledger stays 22 gated,
22 closed.
