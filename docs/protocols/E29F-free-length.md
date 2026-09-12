# E29-F — do the effects survive when the plan length is not pinned?

Declared 2026-09-12 with **zero outcomes**. The last adversarial objection
the record could not answer. Not a novelty candidate; a robustness leg of E29
(`docs/protocols/E29-memory-semantics.md`) and of E29-E
(`docs/protocols/E29E-encoding.md`).

## 0. The objection

Both Gemini Deep Research passes raised it, the second in these words: "If
the target executable plan adheres to strict structural or length
constraints, a high-volume memory system that faithfully retrieves dense
historical context might naturally crowd out rejected items due to simple
token-limit truncation or attention dilution" — the improvement could be an
artefact of a saturated, fixed-size output
(`docs/gemini-research-log/2026-09-12-run2-triage.md` §3, objection 3).

Every E29 result so far pins the plan to four identifiers from a six-item
menu. That pin is why the never-mentioned control sits at 0.42–0.73: with
four slots and six candidates the menu prior fills the plan. It is also, as
recorded, the ceiling on Δ_delete. The objection is fair and this leg removes
the pin.

## 1. Design — E29 with one word changed

Corpus: the E29 corpus (hash `187a426616f26598`), 96 dialogues, both arms,
unchanged. Prompt, temperature, validator, stores: E29's. **The only change is
the plan instruction: E17's `free` mode instead of `pin4`**, which drops the
sentence "`actions` must contain exactly 4 identifiers." and leaves the
decider to choose the length. `free` at |vocab| = 6 reproduces the frozen
benchmark instruction byte for byte, asserted by an existing E17 test.

Four designs, chosen because they carry the whole argument:

| design | what it tests |
|---|---|
| `full` | the reference arm, as in E29 |
| `delete` | the main E29 effect: hard delete re-admits the restated step |
| `addonly` | the protective store: the rejection on its own line |
| `addonly_flag` | E29-E's failing encoding: the same rejection as a `[withdrawn]` prefix |

Deciders: `llama3.2:3b` and `qwen2.5:14b-instruct`, the two extremes of the
range. 96 × 2 × 4 = **768 calls per decider**, chunked at 24 and 16
dialogues, into `results/e29f_<model>_o<offset>.csv/.json`.

## 1a. Amendment, 2026-09-12, after 44 of 96 dialogues on the first decider

**What happened.** Unpinning the plan length let one prompt send the 3B
decider into a runaway generation. Across the 352 calls completed to that
point the median completion was 50 tokens, the 95th percentile 61 and the
maximum 99; the median call took 2.5 s and the slowest ever recorded 7.0 s.
Yet `pharmacy-twochain` rotation 3, restated arm, add-only store did not
return in three separate attempts of 300, 540 and 540 s. This is a
consequence of the manipulation, not an incident: the pinned plan was also
bounding generation, and removing the pin removed that bound.

**The amendment.** From this point every call is made through a wrapper that
sets `num_predict = 512`. `ask_structured` does not expose the parameter, so
the cap is applied by wrapping the client; nothing else changes.

**Why it cannot affect a result.** 512 is 5.2 times the longest completion
observed in the uncapped calls. No well-formed answer in this experiment
comes near it. The cap's only effect is to bound a generation that has
already run away, and a truncated response fails JSON validation and is
counted as a parse failure in the validity table like any other, where it is
visible rather than hidden.

**What this means for the record.** The first 44 dialogues on `llama3.2:3b`
ran uncapped and the remainder capped. The result files carry every call, so
the split is recoverable; the outcome section states it. The cap is an
operational bound on a pathology, not a change to the prompts, the stores or
the scoring, and the block hash is unchanged.

**Reported as a finding in its own right.** That a 3B decider can be driven
into an unbounded generation by removing a length constraint is worth one
line in the paper: it is a cost of unpinning that the pinned design hid.

## 2. Estimands and predictions, fixed before the first call

Unpinning raises inclusion for everything, so every headline quantity is
reported raw **and** net of the same cell's never-mentioned rate:

    Delta_X       = P(rejected in plan | restated, X) − P(… | neutral, X)
    DiD_X         = Delta_X − Delta_full
    Excess_X,arm  = P(rejected | arm, X) − P(never-mentioned | arm, X)
    G_flag        = P(rejected | neutral, addonly_flag) − P(… | neutral, addonly)

- **F1.** Mean |plan| exceeds 4 and the never-mentioned rate rises relative to
  the pinned runs. Descriptive; it is the reason the leg exists.
- **F2 (the objection).** DiD_delete ≥ 0.15 with an interval excluding 0 on at
  least one decider. If it fails, E29's design dependence was a ceiling
  artefact of the pinned plan and must be reported as one.
- **F3 (E29-E's robustness).** G_flag > 0 with an interval excluding 0. If it
  fails, the own-record effect was an artefact of the pin.
- **F4 (control).** Accepted-step inclusion stays ≥ 0.95.

**Author's lean, recorded:** F2 holds and is *larger* unpinned, because the
pin caps Δ_delete; F3 holds and is *smaller*, because a longer plan has room
for the zombie step without displacing anything. Both leans have been wrong
before in this programme.

## 3. Read rule, fixed before the first call

Paired bootstrap over dialogues, seed 0, B = 2000, percentile 95 % intervals,
in `e29f_analysis.py`. **The validity rule changes**, because |plan| is now an
outcome and cannot gate: a cell is VOID if parse < 0.95 **or** the
never-mentioned rate reaches 0.95, the latter meaning the decider is listing
the whole menu and the measure is saturated.

- **SURVIVES** if F2 and F3 both hold.
- **PARTIAL** if exactly one holds.
- **CEILING-DEPENDENT** if neither holds.
- **REVERSED** if DiD_delete ≤ −0.15 or G_flag < 0, either with an interval
  excluding 0.

## 4. What cannot follow

One corpus, two deciders, oracle stores. A SURVIVES verdict removes the
pinned-plan objection for these effects; it says nothing about plan lengths a
different instruction would produce, and nothing about the E29-C register
result or the second corpus, which stay pinned.

## 5. Outcome

_(empty at declaration)_
