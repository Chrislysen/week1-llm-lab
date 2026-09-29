# Prior-art gate for the E29-S structural claim (before E29-R)

Run 2026-09-29 under `docs/NOVELTY-GATE.md`, **with web search**, before any
E29-R call. This gate licenses (or refuses) experiment design only. It is not
a claim of novelty or success.

## 1. The construct, stated before searching

**Plain claim (from E29-S, `21cff6d`).** In a structured context, a language
model ignores a revocation of a record **only when the revocation is both
subordinate to the record it revokes and verb-less**. Written as a tag on the
revoked record (`- [withdrawn] A proposed to X.`), the revoked step enters an
executable plan at 0.594 (llama3.2:3b) and 0.323 (qwen2.5:14b-instruct). The
other three encodings stay at 0.031–0.198:
- a separate proposition (`- B rejected the proposal to X; …`);
- the same proposition merged onto the proposal's item (byte-identical text,
  one line break removed);
- a separate verb-less status line (`- status(X) = WITHDRAWN; …`).

| part | this construct |
|---|---|
| objects | a proposal record and its revocation, inside a list-structured context (memory store) the decider reads |
| operations | render the revocation in one of four structures (own item × merged, proposition × attribute), all other text fixed |
| estimand | inclusion of the revoked step in a generated four-step executable plan (neutral arm: no later restatement) |
| intervention | fixed-intervention comparison, same 96 dialogues, paired, temperature 0, oracle stores |
| assumptions / scope | two local deciders (3B, 14B); one corpus; markdown bullets only (so far); no retrieval layer |

**Vocabulary map.** The field's terms for the underlying question
(*does a model honour a revocation, and does it matter how the revocation is
written?*):
- revocation, retraction, invalidation, supersession, soft delete, tombstone;
- status flag, `is_active`, `invalid_at`, bi-temporal edge, validity interval;
- deprecation marker/annotation (`@deprecated`, `[DEPRECATED]`);
- stale or outdated fact, knowledge update, knowledge conflict;
- negation cue and scope, negation neglect;
- metadata versus content, verbalised triples versus sentences;
- prompt format sensitivity (JSON / XML / markdown);
- completion marker (`[x]`).

## 2. Leads and dispositions

| lead | route | disposition |
|---|---|---|
| arXiv:2609.08258 *Revoked but Still Authoritative* (Shen, Toyoda, Leung; v1 2026-09-08) | arXiv HTML, §3.1–3.2, §4.1–4.3, Tables 3, 6–8, 13 | **read; closest; does not cover the residual** (see §4) |
| Tian Pan, *The Deprecation Notice Your Agent Can't Read* (blog, 2026-07-05) | fetched | read; practitioner claim, no controlled data (see §4) |
| Tian Pan, *MCP Tool Deprecation: Why the Model Still Calls the Old Name* (blog, 2026-05-14) | fetched | read; anecdotal (≈3 % of calls), no comparison run |
| arXiv:2406.09834 *LLMs Meet Library Evolution* (Wang et al., ICSE'25, v3) | arXiv HTML, the INSERTPROMPT section | read; tests an inserted natural-language comment only; **no annotation-on-item condition** |
| arXiv:2609.01852 *The Memory Trust Gap* (Hu, Ramachandran) | search snippet + prior reading in E29 §0 | stale value vs current evidence; metadata helps capable models; **no encoding manipulation**; already cited in the draft |
| arXiv:2411.10541 *Does Prompt Formatting Have Any Impact on LLM Performance?* | abstract level | whole-prompt format effects; not revocation or negation; background only |
| negation literature: arXiv:2306.08189 (*not naysayers*), arXiv:2408.03070 (negation scope probing), arXiv:2503.22395 | abstract level | models are weak on negation and scope; none varies a revocation's structural position in a list context |
| agent issue trackers on ignored `[x]` completion markers | search snippets | anecdotal; no controlled comparison |

No lead that could cover the core claim is left **unresolved**.

## 3. Search log (2026-09-29; budget of about 15 queries and 8 reads, set in advance)

Queries, in order:
1. `"Revoked but Still Authoritative" arXiv 2609.08258`
2. `LLM ignores revocation flag metadata status field still uses revoked fact in context`
3. `negation encoded as attribute versus sentence prompt structure language model ignores key-value status`
4. `LLM agents call deprecated tools despite deprecation marker in tool description`
5. `"Memory Trust Gap" arXiv 2609.01852 stale fact metadata`
6. `language models cite retracted papers despite retraction notice in context`
7. `LLM outdated fact labeled "outdated" or "superseded" in retrieved context still answered knowledge conflict`
8. `strikethrough markdown deleted text LLM treats crossed out text as valid`
9. `prompt structure list item boundaries modifier binding LLM inline tag vs separate statement experiment 2026`
10. `LLM agent processes cancelled order despite "status": "cancelled" field in JSON context tool result`
11. `soft-deleted records is_deleted flag retrieval augmented generation model uses deleted documents`
12. `negation cue outside clause scope language models tag prefix "[withdrawn]" or "not" metadata marker ignored`
13. `LLMs misread unified diff removed lines minus prefix treated as present code change understanding`
14. `knowledge graph triples versus verbalized sentences in prompt LLM uses facts differently negated relation`
15. `prompt formatting sensitivity JSON vs markdown vs XML list effect on LLM decisions 2025 2026 study`
16. `agent redoes task already marked done checkbox "[x]" in plan context LLM ignores completion marker`

Reads: arXiv:2609.08258 (HTML, sections above), arXiv:2406.09834v3 (HTML,
INSERTPROMPT section), both Tian Pan posts. Everything else was read at
abstract or snippet level. That was enough to rule each one out, because none
manipulates how a revocation is encoded.

## 4. Strongest prior work against the actual claim

| proposed contribution | closest prior result + section | same mechanism, estimand, assumptions? | substantive difference | what would test that difference |
|---|---|---|---|---|
| a revocation tag on the revoked record is ignored at the action level | 2609.08258 §4.1: with the revocation label visible, agents take the unsafe action in 43–44 % of trials, on 9 frontier-class models | same failure family (visible label, still acted on); different systems and models | 2609.08258 varies **whether** the label is exposed, not **how** the revocation is encoded. No condition holds the text fixed while moving or rewording the mark (its §4.3 blames the equal standing and more absolute phrasing of the revoked policy) | a fixed-intervention encoding manipulation on one set of dialogues: **E29-S did this** |
| the failure needs **both** subordination **and** verb-lessness | none found | — | the dissociation itself: separating the mark alone, or making it a proposition alone, each restores compliance | the E29-S 2×2 (done, markdown) and **its replication across formats (E29-R)** |
| deprecation tags are under-read and an explicit separate line helps | Tian Pan blogs (2026-05, 2026-07): practitioner reports, no controls | same direction for a tool registry | anecdote, not measurement. The blog predicts that **separation alone** fixes it; E29-S says a separate verb-less status line works too, and it is the *conjunction* that fails | E29-S already contradicts the "separation alone" reading in markdown; E29-R tests it in other formats |
| inserted natural-language guidance reduces deprecated use | 2406.09834, INSERTPROMPT: fixed 25.7–97.2 % across models | an inserted proposition only | no annotation-on-item condition, so no attribute-versus-proposition contrast | — |

## 5. Residual and how it could fail

> The closest work establishes that agents act on revoked memory records even
> when a revocation label is visible (arXiv:2609.08258), and practitioners
> report that deprecation tags on tool descriptions are under-read. This
> candidate would additionally establish, in a fixed-intervention design with
> byte-identical text, that the failure is **specific to the conjunction** of
> the mark being subordinate to the revoked record **and** verb-less. Moving the
> mark to its own item, or writing it as a proposition, each restores
> compliance, **under** two open deciders (3B, 14B), one synthetic corpus and
> oracle stores. This matters because shipped memory systems and tool
> registries encode revocation in exactly that conjunction (validity flags,
> `invalid_at` edges, `is_active`, `[DEPRECATED]` prefixes), and the fix is a
> one-line change in how the context is serialised.

> The claimed additional contribution would be unsupported if the conjunction
> pattern does not replicate outside markdown bullets. For example: in a JSON
> string array, XML-tagged items or a numbered list the tagged cell is honoured
> like the others, or a separate status line fails as often as the tag. Then
> the result would be a fact about markdown bullets, not about structure.

## 6. Decision

**Candidate for testing — residual NARROW.** This licenses E29-R, the format
replication named in `docs/paper/reframe-v2.md` §4.1. It is not a novelty
claim. The concurrent paper (2609.08258) owns the shipped-system finding, and
the practitioner observation predates us. What is ours, if E29-R holds, is the
controlled dissociation and its format generality. Revisit if a controlled
encoding study appears.
