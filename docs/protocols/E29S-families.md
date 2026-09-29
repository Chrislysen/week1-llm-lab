# E29-S+ — the 2×2 on two more model families

Declared 2026-09-29 with **zero outcomes** for these deciders. It is an
addendum to `docs/protocols/E29S-structure.md`, whose blocks, prompts and read
rule it reuses unchanged.

## Why

E29-S's two deciders are two families: Meta (llama3.2:3b) and Alibaba
(qwen2.5:14b-instruct). A structural claim about how language models read a
list should not rest on two families. This addendum adds the two other
families installed locally:
- **Google:** gemma4:e4b, about 4B effective. It is the only decider in the E29
  study that never enacted a step whose rejection it could see (0.000 under
  add-only and wiki).
- **Cohere:** aya-expanse:8b, never run on this setup before.

## Design

Exactly E29-S. The same four stores, both arms, 96 dialogues, 768 calls per
decider, block hash `f25719fc5d4a268c` (asserted by the runner), and
`python e29s_structure.py --model M --resume`. The runs are queued to start
after E29-T's process exits. They are gemma4:e4b then aya-expanse:8b, and
gemma is slow (about 11 s/call).

## Predictions and read rule, fixed before the first call

- **Validity.** E29-S's VOID rule (parse < 0.95 or mean |plan| outside
  [3.9, 4.1]) applies. aya-expanse:8b has never been validated on the pinned
  plan, so a VOID result is a possible, reportable outcome, not a reason to
  change the prompt.
- **Verdict.** E29-S's own rule (`e29s_analysis.py`: SEPARATION / FORM /
  INTERACTION / NULL / PARTIAL), **and** the E29-R conjunction rule
  (`e29r_analysis.reaches`). The conjunction holds when S_flag and S_form_same
  reach 0.15 with intervals excluding 0, and S_merge and S_form_own do not.
- **Author's lean: CONJUNCTION on aya-expanse:8b. On gemma4:e4b the tag cell
  may sit near floor, because gemma honoured every stored rejection it could
  see in E29; if its tag cell is also near zero, the result reads NULL, and
  that is reported as a family that does not show the effect.**
- **Programme reading.** Conjunction on both new families means the structural
  claim holds on four families. On one of them, it holds on three families,
  with the exception named. On neither, it is scoped to the two families of
  E29-S.
