# Reframing the paper around context structure. A proposal, written 2026-09-12.

Not a protocol and not a result. This argues for reorganising what we have,
and it is written *before* E29-S reports so that the reorganisation cannot be
reverse-engineered from its outcome. Both possible outcomes are covered.

## 1. The problem with the current framing

The draft is organised as a memory-systems paper: four shipped designs, a
restatement manipulation, design dependence. Three things are wrong with
that as a bid for a frontier contribution.

**It is predictable.** If a store deletes the rejection, a decider cannot
honour it. Reviewers will say "of course", and they will be most of the way
right. The result is careful rather than surprising.

**It is a crowded race we are losing on resources.** arXiv:2609.08258
appeared three days before our gate, measured five shipped systems on nine
frontier models, and took the closest claim. We have four local models
between 3B and 14B and a synthetic corpus. On the dimension that field
rewards — coverage of real systems at scale — we cannot win, and chasing it
means adding systems we cannot afford to run.

**The genuinely surprising result is buried in a subsection.** E29-E found
that *re-wording* a rejection changes nothing while *re-positioning* it
changes a great deal. That is not a fact about memory architecture. It is a
fact about how a model reads a structured prompt.

## 2. The claim the paper should lead with

> Whether a language model acts on a negation in its context depends on the
> negation's **structural position** — whether it is a separate item, and
> whether it is a proposition — and not on its wording or its presence.

Supporting shape, already measured:

- Same content, same line, prose versus key-value: no consistent effect
  (+0.052, −0.115, −0.031 across three deciders).
- Same content, collapsed onto the record it negates: large effect
  (+0.385, +0.219, +0.292, all intervals excluding zero).
- The effect survives unpinning the output length (E29-F), on both the
  smallest and largest decider.
- Measured against each cell's own never-mentioned baseline, a written
  rejection puts the step *below* chance while a flagged one puts it *at*
  chance. The model behaves as though the flagged rejection were not there.

E29-S completes the 2×2 and decides which structural variable is operative.
**Either outcome supports the reframing**, because both name a property of
context structure rather than of memory:

- **SEPARATION**: a negation must occupy its own item. The manipulation that
  shows it is byte-identical text with one line break removed, which is about
  as clean as a prompt-structure result gets.
- **FORM**: a negation must be a proposition with a verb; a key-value
  attribute is under-weighted wherever it sits.
- **INTERACTION**: both, which is the least quotable but still structural.

## 3. What the memory result becomes

Motivation and external validity, not the headline. It earns three things the
structural claim cannot supply on its own:

1. **A reason to care.** The designs that ship encode revocation exactly the
   way the structural result says is worst: as an attribute of the record
   being revoked — a validity interval, an `invalid_at` edge, an `is_active`
   flag. The finding is not a curiosity; it is a property of deployed systems.
2. **An action-level outcome.** The effect is measured on an executable plan,
   not on a QA answer, which is what makes it consequential rather than a
   probing artefact.
3. **A partner's restatement.** Still the component no prior work has, and
   still the thing that turns a static store property into a dynamic failure.

## 4. What would have to be added to make it frontier rather than neat

Ranked by value per unit of compute, and honestly assessed:

1. **Format replication.** The result is currently one list format, markdown
   bullets. Repeat the decisive contrast in JSON (`{"facts": [...]}`), in
   XML-tagged items and in a numbered list. If the structural effect survives
   all four, the claim is about item structure rather than about markdown,
   and that is the difference between a finding and a curiosity. Cost: one
   contrast × 4 formats × 96 × 2 arms × 2 deciders ≈ 3,000 calls, about three
   hours. **This is the highest-value next run after E29-S.**
2. **A larger decider.** Everything here is ≤ 14B. A single frontier-model
   replication of the decisive contrast would answer "does this vanish with
   capability?" — which is the first question any reviewer asks. Needs an API
   budget this project does not have; worth naming as the known gap.
3. **Human dialogue.** The CaSiNo assessment stands (`E30-natural-corpus.md`).
   It removes the templating objection but does **not** bear on the structural
   claim, because a memory store is synthetic in every real system. Lower
   priority than it looked before the structural reframe.
4. **A mechanistic probe.** Attention or logit-lens evidence that the merged
   negation is bound to the proposal as a modifier rather than asserted
   independently. Beyond what Ollama exposes; would need transformers locally.

## 5. Compression

The current draft has eight legs (E29, B, C, D, N, X, E, F, S). A submittable
paper has one claim and four supports. Proposed structure:

1. The structural claim, with the 2×2 as Figure 1.
2. Why it matters: the shipped designs all use the losing encoding.
3. Robustness: four deciders, three model families, two corpora, pinned and
   unpinned output, oracle and real extractor.
4. What it is not: no retrieval layer, no frontier model, one format (or four
   after item 4.1), synthetic stores.

E29-B (the uninformative real-extractor attempt), E29-C (the register
effect), and the E29-N correction move to an appendix as process record. They
are what makes the work trustworthy; they are not what makes it interesting.

## 6. The honest ceiling

Even completed, this is a short-paper or workshop contribution, not a
main-conference one, and the reason is not rigour — the rigour is unusual —
but scope: local models, synthetic stores, one task. Its value is that the
claim is *clean*, *pre-registered*, *survives four adversarial controls*, and
*contradicts how every surveyed production system encodes retraction*. That
combination is rare enough to be worth publishing, and honest enough to be
worth trusting.
