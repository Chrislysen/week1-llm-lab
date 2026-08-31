# E1, first execution — PRESERVED, DO NOT USE

This run is kept as evidence that it happened, not as a result.

`meta.source_coverage` in these artifacts is WRONG for the bm25, dense and
fusion arms. `run_incident` recomputed the finalisation context with
`policy.select(view)` and no query, so those selectors derived
`query_for_turn` while `finalise` had actually used `query_for_finalisation`.
The recorded coverage therefore describes a context that was never sent.

The symptom is visible in the raw table: rows showing `sel_source 2` next to
`retrieval_recall 0.0`. `sel_source` was read from the policy's own call log
and is correct; `retrieval_recall` was not.

Fixed by reading the finalisation selection back from `policy.calls[-1]`
instead of re-selecting, which makes the two impossible to disagree. E1 was
then re-run in full under the same frozen protocol and the same predeclared
seeds. Nothing about any selector, prompt, budget or alpha changed.
