# Novelty gate — the procedure to run before opening any candidate

Adopted 2026-09-08, after the E27 originality withdrawal. Drafted in external
review (Astra) around the specific failure that let E27 stand as "the one
original result" through a full review cycle. **Ledger at adoption: 22 candidates
gated, 22 closed, zero established original results.**

Repair this gate before opening another candidate.

## What this gate decides

Whether a candidate has a **specific, presently unsupported contribution worth
testing**. No search procedure can prove that no prior work exists, so record
search coverage and remaining uncertainty explicitly.

Keep four judgements separate: originality, implementation correctness,
experimental validity, and practical usefulness. A replication can be useful; a
novel proposal can fail; a sound fixed-intervention comparison can have limited
scope. **Retiring an originality claim does not require making the experiment
sound worse than its design supports** — a lesson learned by getting it wrong:
E27's closure was first argued on a magnitude confound that its unit-norm design
made impossible.

## 1. Describe the construct before searching the claim

State the contribution in plain language, then record its **objects, operations,
objective/estimand, intervention, and assumptions**. For empirical comparisons
include normalisation, tuning, data splits, readout, and the intended scope of
the conclusion.

Build a **vocabulary map** from those operations to the field's names: common
acronyms, earlier method names, mathematical equivalents, the nearest established
task. The repo's experiment IDs and my own phrasing **must not be the only search
terms**. Expand the map as sources reveal new terminology.

> E27 failed here. Its gate asked "has anyone shown estimator choice flips
> nulls?" — my framing. The field calls the same objects MoD / PoD / PoE / CoE
> and asks "which steering method should be used, and why?"

## 2. Resolve supplied leads before giving any verdict

Keep a lead list for every citation from a user, reviewer, or source. Resolve
identifiers directly; on failure try title+author, alternate versions, the venue,
and the authors' publication pages.

**A failed retrieval is UNRESOLVED, with the route tried recorded. It is never
evidence that the work does not exist.** A credible unresolved lead that could
cover the core claim leaves the gate **incomplete**. Give priority to citations
that threaten the preferred result.

> E27 failed here too. An earlier audit marked "Im and Li" unverifiable; one
> search finds arXiv:2502.02716. A false negative was recorded as absence, on the
> single citation most damaging to my own claim.

## 3. Search the field's problem and methods

Search the underlying question *and* alternative method names. Inspect primary
papers, their relevant references, and directly relevant citing work. Abstracts
and snippets help you *retrieve*; a **verdict requires reading the pertinent
definitions, experiments, or proofs**.

Log: the actual query, search date, source identifier **and version**, sections
read, and what each source covers. Set a bounded retrieval effort in advance.
When that budget ends with a material lead unresolved, **report incomplete
coverage — never convert a budget limit into novelty evidence.**

## 4. Compare the strongest prior work against the actual claim

Fill this in **before** collecting outcomes. Do not infer equivalence from shared
terminology, or difference from differing terminology.

| proposed contribution | closest prior result + section | same mechanism, estimand, assumptions? | substantive difference | what would test that difference |
|---|---|---|---|---|

- For an algorithm assembled from known parts, compare against a **straightforward
  composition of those parts** under the same objective and resources.
- For an empirical claim, distinguish a **fixed-intervention** comparison from a
  comparison of **separately tuned** methods.
- For a theorem, **retain its objective and assumptions** when translating its
  conclusion. (Im & Li's Theorem 3.1 minimises an embedding-matching MSE — it is
  not universal behavioural optimality.)
- **Precondition check — applies symmetrically to OPENING and CLOSING a
  direction.** Before any imported result, confound, bound, theorem, or effect
  size is used as an argument — *for* novelty or *against* it — do all three:
  1. **Identify its assumptions** (normalisation, tuning regime, objective,
     data, units, operating point, model class).
  2. **Verify each holds in our implementation**, by inspecting our code or
     data, not by analogy.
  3. **State the conclusion actually supported** once the non-holding
     assumptions are struck out.

  An argument that fails this check is withdrawn regardless of which direction it
  points. Closing a direction on an inapplicable confound is the same error as
  opening one on an inapplicable guarantee, and it is *easier* to miss, because
  the conclusion feels appropriately modest.

  > Both errors happened here. E27's first closure argument imported Im & Li's
  > per-method magnitude confound into a design that normalises every direction
  > to unit norm at identical α — the confound could not apply
  > (`e27_estimator.py:135`, `:141`). Earlier, the unlearning bound of
  > arXiv:2609.04875 was cited as bounding AgentCom's achievable contribution
  > when it bounds worst-case *exact reconstruction* over transitions, not
  > decoded tokens, under a specific operation set.

A different name, threshold, model, dataset, or unit does not by itself
establish a contribution. Conversely, an omitted baseline or imperfect experiment
does not prove the question has no original answer.

## 5. State the residual and how it could fail

Complete both sentences before proposing any implementation:

> The closest work establishes ____. This candidate would additionally establish
> ____ under ____, which matters because ____.

> The claimed additional contribution would be unsupported if ____.

The second must describe an **informative counter-result**, not merely missing an
arbitrary point threshold. Any later experiment needs its own estimand,
uncertainty treatment, quality criteria, and resource plan.

## 6. Record exactly one decision

| decision | meaning and next action |
|---|---|
| **Covered / replication** | Prior work covers the contribution, or none is identified. Retire originality; keep any useful replication record. |
| **Unresolved** | Material retrieval, interpretation, or comparison work remains. Finish it before any originality verdict. |
| **Candidate for testing** | A substantive residual is specified and material leads addressed. **This licenses experiment design — not a claim of novelty or success.** |

Attach the vocabulary map, lead dispositions, search log, comparison table, and
residual sentences to the decision. Revisit when a new direct competitor appears.

## Regression checks

| case | required behaviour |
|---|---|
| same comparison described with different names | map the terminology, inspect the competitor; wording differences are not novelty |
| a supplied competitor cannot be retrieved | record UNRESOLVED coverage; issue no novelty verdict |
| prior paper uses different normalisation or objective | preserve the distinction; do not import its confounds or guarantees unchanged |
| a new threshold is the only identified difference | require a substantive additional conclusion before "candidate for testing" |

These are **specifications for gate behaviour, not a measured guarantee** that the
procedure finds every relevant paper. The E27 retrospective demonstrates a
retrieval route for a case whose answer was already known; it does not estimate
success on unseen cases.
