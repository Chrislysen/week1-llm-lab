# Gemini Deep Research brief — recurring, privacy-preserving

Purpose: use Gemini's Deep Research mode as an outside scout for the field
this project works in, on a regular cadence, without giving away what we
built, how we built it, or what we found. The returns feed
`docs/NOVELTY-GATE.md`: every lead Gemini names is read in full text here
before it counts.

## 1. What never goes into a Gemini prompt

Gemini retains conversations and may use them for training. Treat every
prompt as public. The following stay out, always:

- The name of this repository, the course, the instructor, or the author.
- Experiment identifiers (E-numbers), protocol files, commit hashes, corpus
  hashes, model names we ran, call counts, chunking, or timings.
- **The manipulation.** Do not describe the inserted line, the two-arm
  contrast, the neutral control, the speaker rule, the slot rule, or any
  sentence template.
- **The estimand and read rule.** No difference-in-differences against full
  context, no bands, no bootstrap details, no pre-registered predictions.
- **The results.** No effect sizes, no orderings across designs, no
  decider-size observations, no register finding, no real-router finding,
  no second-corpus finding, no control failures.
- **The store renderings.** How each design's context block is written.
- The names of the four repositories whose source we read, as *ours to
  compare against*. Naming shipped systems as objects of study is fine; the
  fact that we vendored their prompts is not.
- The X-ray, Memory City, or any deliverable.

Rule of thumb: if a sentence would let a reader reconstruct our experiment
or predict our result, it does not go in. Field-level questions go in.

## 2. What may go in

The field's problem statement and vocabulary, which are public: memory
layers between dialogue and decision; write-time conflict resolution;
ADD / UPDATE / DELETE routers; add-only stores; merge-in-place pages;
tombstones; state memory; supersession, retraction, revocation, stale
memory, re-licensing, stale value rates; multi-agent dialogue where
proposals are accepted or rejected; executable plans as outcomes; small
local deciders. Named systems and papers as objects of study. Dates, so
recurring runs return only what is new.

## 3. Cadence and logging

Run the prompt below once a week, or before any write-up. Change only the
`SINCE` date and the rotating focus block (§5). Save each return verbatim to
`docs/gemini-research-log/YYYY-MM-DD.md` with the prompt used, then triage:
every lead with a locator goes through the gate (full-text read, comparison
table row, residual sentence). Nothing Gemini says counts as "found" or
"not found" until it has been read here.

## 4. The prompt (copy from the first line to the last)

```
You are acting as an independent research scout for a small research group
working on memory layers for multi-agent LLM systems. Your job is to map the
frontier of one specific problem, to attack it as a skeptical reviewer would,
and to propose experiments the group has probably not thought of. You are
not being given the group's own method or results, and you should not try
to guess them; work from the public literature and from shipped systems.

THE PROBLEM

Two or more LLM agents talk, then one of them acts through a plan. Between
the dialogue and the decision sits a memory layer that stores extracted
facts and resolves conflicts at write time or at read time. In a dialogue,
proposals get accepted or rejected, and rejected items can be mentioned
again later. We care about SUPERSESSION: whether an item that the
conversation itself retracted, rejected, or revoked can come back into the
decision because of how the memory layer stores, deletes, merges, or
re-admits information. We care about executable outcomes (a concrete plan or
action list), not question answering.

Relevant vocabulary, use it and its neighbours in your searches: write-time
conflict resolution; ADD / UPDATE / DELETE memory routers; add-only or
append-only memory; merge-in-place or entity-page memory; tombstones and
soft delete; state memory; supersession; retraction; revocation; stale
memory; stale value rate; re-licensing of a suppressed item; memory
consolidation; contradiction handling; belief revision in agent memory;
multi-agent dialogue memory; shared memory between agents; long-horizon
agent memory benchmarks; memory for planning agents.

SCOPE AND DATES

Cover arXiv, ACL Anthology, OpenReview, ICLR/NeurIPS/ICML/ACL/EMNLP
proceedings, and engineering sources (release notes, changelogs, design
docs, issue threads) for shipped memory systems. Prioritise work dated on or
after SINCE = 2026-06-01, but include foundational earlier work when a newer
paper builds on it. State the publication date of everything you cite.

TASKS

1. LANDSCAPE. List every paper, benchmark, or system that measures or
   discusses whether a retracted, rejected, revoked, or superseded item
   survives into a later decision through a memory layer. For each: title,
   venue or arXiv id, date, the memory designs it compares, the outcome
   measure, the model sizes, whether the setting is single-agent or
   multi-agent, whether retraction happens inside the dialogue or through an
   external command, and whether a later re-mention of the retracted item
   is manipulated at all. If a column is unknown, write "not stated"; do
   not infer.

2. SHIPPED SYSTEMS. For memory products and libraries used in agent stacks
   (memory routers, agent memory SDKs, knowledge-page or wiki-style
   memories, session memories), report what each does at write time with a
   fact that contradicts a stored one, what it does with a rejection or a
   negation, and whether its semantics changed in 2025 or 2026, with the
   source for each claim. Distinguish documented behaviour from observed
   behaviour reported by third parties.

3. ADVERSARIAL REVIEW. Assume a group ran a controlled experiment comparing
   memory designs on whether a rejected dialogue item re-enters a plan.
   Without knowing their design, write the strongest reviewer objections
   such a study would face: confounds, estimand problems, corpus
   artefacts, decider-size effects, rendering and prompt-format effects,
   ceiling and floor effects from fixed-length plans, and any way the
   result could be true by construction. For each objection, name the
   control or additional arm that would answer it.

4. NEGATIVE SPACE. Name what has NOT been measured in this area as far as
   you can establish, and say explicitly which searches you ran that
   returned nothing. A confident "not found" with the queries listed is
   more useful than a vague "little work exists".

5. FRONTIER. Propose five experiments that would move this problem
   forward, each with the design, the outcome measure, the minimum model
   and data requirements, and the result that would count as a
   breakthrough versus an incremental finding. Prefer experiments that
   distinguish memory-design effects from model-capability effects, and
   experiments that use naturalistic multi-agent dialogue rather than
   templated dialogue.

6. RECENT DELTA. Separately list everything in your answer that is dated
   after SINCE, so that a recurring reader can see only what is new.

OUTPUT RULES

- Tables for tasks 1 and 2, prose for 3 to 5, a dated list for 6.
- Every factual claim carries a locator: arXiv id or DOI plus section,
  table, or figure; or a URL plus the heading. Quotes at most 25 words.
- Mark each claim VERIFIED (you read the source) or INFERRED (from an
  abstract, a citation, or a secondary source). Do not present inferred
  claims as verified.
- Do not pad. Omit background on what LLM memory is.
- If you find a paper that manipulates a later re-mention of a rejected
  dialogue item across memory designs, put it first and flag it.
```

## 5. Rotating focus block

Append one of these to the prompt each run, cycling through them, so the
scout does not return the same map every week:

- **Week A, corpora:** "Focus this run on datasets and benchmarks of
  multi-agent or multi-party dialogue that contain explicit rejections,
  retractions, or reversals of proposals, with executable or checkable
  outcomes. Report licensing and size."
- **Week B, deciders:** "Focus this run on evidence about how model size and
  family change adherence to a stored rejection or negation, in memory or
  retrieval settings, including any results with models under 15B."
- **Week C, real systems:** "Focus this run on measured behaviour of
  shipped memory routers when the extracted fact is a negation or a
  rejection: deletion rates, merge behaviour, and known failure reports."
- **Week D, estimands:** "Focus this run on how published studies estimate
  memory-design effects: reference arms, difference-in-differences,
  bootstrap over dialogues, ceiling effects from fixed-length outputs, and
  critiques of those estimands."

## 6. Reading the return

Gemini's landscape table is a lead list, not a finding. For each row with a
locator: read the section named, fill a row in the gate's comparison table
(`docs/NOVELTY-GATE.md` format), and write the residual sentence. Rows
without locators are discarded. Objections from task 3 are checked against
our recorded controls one by one; any objection we cannot answer from the
record becomes a declared follow-up, never an edit to a result.
