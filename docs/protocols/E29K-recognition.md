# E29-K — does the decider know the tagged step was rejected?

Declared 2026-09-29 with **zero outcomes**.

## 0. The question E29-S leaves open

A rejection written as a verb-less tag on the proposal is enacted at 0.594
(3B) and 0.323 (14B), against 0.03–0.20 for the same rejection written any
other way. Two explanations fit:
- **Not read.** The model does not take `[withdrawn]` on a record to mean the
  step was rejected.
- **Read, not used.** The model knows the step was withdrawn, and the planner
  includes it anyway.

These call for different fixes (serialisation versus decoding), and they are
separable by asking.

## 1. Design (`e29k_recognition.py`)

- **Same prompt, different question.** The same deciders, the same system
  prompt, and the same four E29-S stores in the neutral arm, with the plan
  instruction replaced by: `Question: has the step "{phrase}" been rejected or
  withdrawn in this discussion? Answer with exactly one word: yes or no.`
- **Two questions per store:**
  - about the **rejected step**;
  - about a **control step** that was not rejected. This is the accepted step
    where the dialogue has one, otherwise the proposed-only step, otherwise the
    never-mentioned step. Its correct answer is "no".
- **Scale and settings.** 96 dialogues × 4 stores × 2 questions = 768 calls per
  decider. Temperature 0, at most 8 tokens, and the first word is parsed as
  yes or no. Prompt hash `e9ef529280d358bb`.

## 2. Read rule, fixed before the first call

Take R_X, the rate of "yes" (rejected) for the rejected step in store X, and
the gap R_addonly − R_addonly_flag, with a paired bootstrap (seed 0,
B = 2000).
- **VOID** if any cell's parse rate is < 0.95, or the control step draws
  "yes" more than 0.20 of the time (a yes-bias makes the probe uninformative).
- **NOT-READ** if the gap is ≥ 0.15 with an interval excluding 0: the tag is
  not recognised as a rejection.
- **READ-NOT-USED** if the gap's upper bound is < 0.15 and R_addonly_flag
  ≥ 0.80: the tag is recognised like the sentence, and the E29-S enactment
  rate is then a gap between knowing and acting.
- **UNCLEAR** otherwise.

**Author's lean: NOT-READ on the 3B, READ-NOT-USED on the 14B.**
