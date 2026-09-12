# Next Gemini Deep Research prompt — run 2 (prepared 2026-09-12)

Paste everything between the fences. SINCE moved to 2026-09-01 so the delta is only what run 1 could not have seen; focus block: Week A (corpora), the gap the paper names first. Save the return as `2026-MM-DD-return.md` beside run 1.

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
after SINCE = 2026-09-01, but include foundational earlier work when a newer
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
  dialogue item across memory designs, put it first and flag it. For any
  paper you flag, quote the sentence from the paper's own method section
  that describes the manipulation; do not flag on abstract wording, and
  give the paper's exact title as printed on the paper.

FOCUS FOR THIS RUN

Focus this run on datasets and benchmarks of multi-agent or multi-party
dialogue that contain explicit rejections, retractions, or reversals of
proposals, with executable or checkable outcomes. Report licensing and
size. Include corpora built for other purposes (meeting transcripts,
negotiation, incident channels, code review threads) if they contain
proposal-then-rejection exchanges that could be annotated.
```

## Run 3 additions (prepared 2026-09-12 after triaging run 2)

Change SINCE to the date of run 2 and append, after the OUTPUT RULES block:

```
- Before claiming a search returned nothing, state the date range you
  searched and confirm you covered the fourteen days before today. Run 2
  omitted from its landscape a paper dated three days before the run that
  its own recent-delta list then named.
```

Focus block for run 3 (Week B, deciders):

```
FOCUS FOR THIS RUN

Focus this run on evidence about how model size and family change
adherence to a stored rejection or negation, in memory or retrieval
settings, including any results with models under 15B. Report, for each,
whether the negation was written as its own record or as an attribute of
the record it negates, since that distinction is rarely stated and
changes what the result means.
```
