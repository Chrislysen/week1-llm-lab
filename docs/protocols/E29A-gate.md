# Prior-art gate, BET 2 (mechanism) and BET 3 (linguistic map) -- 2026-09-30, with web search

Already in repo (not re-reported as new): paper s6 (2609.08258, 2406.09834, 2306.08189, 2408.03070,
2609.01852, memory-design list); E29R-gate (2411.10541, 2503.22395, Tian Pan blogs); E16 gates
(2603.18353, 2606.08044, 2605.03052, 2605.13737, 2608.23651, 2507.11878, 2506.13734, 2606.29960,
2608.12599 [abstract only, NOT cited in the draft], 2604.20911, 2608.12323, 2506.11068, 2511.12381,
2601.08070, 2601.21433, B-TEMPLATE 2606.05403/2603.22619/2605.05957/2608.07528). Roadmap knows 2608.12321
only for "prompted mention shifts behaviour globally". In-repo E23 (verdict 86-94 % decodable at
0.8-1.5B), E26/E26-B (DiM steering partial on Qwen2.5-1.5B, sub-threshold).

## BET 2 -- LARGELY PRE-EMPTED
- 2608.12321 Li, Krishnan, Padman (CMU), "LLMs Know the Constraint But Do Not Use It: Activation
  Bottlenecks in Pragmatic Constraint Reasoning" (v1 PDF stamp 29 May 2026). READ IN FULL (pp.1-12).
  K/S/R/P: probe decodes constraint (Qwen3-14B 94.5 % L27, GPT-OSS-20B 88 % L20); routing rho 0.125/0.224
  < 0.30; Repair = patch final-token state from EXPLICIT donor ("ACTIVE + C as one declarative sentence")
  into ACTIVE recipient at probe's best layer: +6.38 nats Qwen3-14B, -0.07 GPT-OSS-20B. "Hidden-constraint
  failure is a routing problem, not a knowledge problem." Constraint implicit; REMOVED = counterfactual
  without it (not a revocation). Final-token, single-layer patching only.
- 2507.11878 Zhao et al., NeurIPS 2025: harmfulness at t_inst vs refusal at t_post-inst; steering
  dissociates judgment from action.
- 2605.14038 Cheng, Fan, JafariRaviz, Rezaei, Feizi (May 2026): knowing-doing gap in tool use; both
  decodable, directions orthogonal in late-layer last-token regime; mismatch at cognition->action.
  Abstract only; no patching mentioned.
- 2609.37737 Wen, Liu, Yang, Sakuma, Sun (29 Sep 2026): prompt-injection compliance decodable from
  layer 1, causal only at late bottleneck; patching reverses 77-92 %; rank-8 subspace (4B, 14B).
- 2603.18353 Basu et al. (Mar 2026); 2605.05715 Ming Liu (May 2026): probe >> output, steering fails.
- 2607.20115 Huang, Pado, Weeber (Jul 2026): patch original-construction activations into rewritten
  construction restores stance; mid-late layers, final position.
- 2609.00753 Shih, Winnicki, Cao (Sep 2026): vary stated authority with content fixed; interchange
  along authority directions reproduces 30-68 % of source-choice shift.
- 2410.14516 Heo et al. ICLR25 (IF dimension tied to phrasing; steering helps); 2410.12877 Stolfo et al.
  ICLR25; 2410.02707 Orgad et al. ICLR25; 2306.03341 ITI; 2605.00226 Sobotka et al. (belief-action gap);
  2605.27157 (monitoring-control gap in RAG, behavioural); 2608.02657 (IPI exposure decodable, probe-gated
  defense); 2407.12831 Buerger et al. (general vs polarity-sensitive truth directions); 2412.12094 SepLLM
  (separators summarise segments); 2106.00737 Li, Nye, Andreas (entity state decodable at mentions);
  2310.17191 binding IDs.
Residual: form-conditional routing of explicitly present information, tested at the record's tokens
(cross-form probe transfer, position-resolved patching, byte-identical null pair).

## BET 3 -- CANDIDATE WITH NARROW RESIDUAL
- 2607.20115 (above): six constructional rewrites (negation, antonym, active/passive, it-cleft,
  wh-cleft, support-verb construction) x stance decision x patching; Gemma-3 4B/12B, Qwen3 4B/14B;
  polarity rewrites flip most, SVC most robust.
- 2609.25686 Zhang, Kweon, Han (22 Sep 2026) "How Strongly Should Task State Influence an LLM Agent?"
  READ pp.1-10 + App. E.2. Checklist "- s10: DONE" (verb-less status on the item) unreliable; directive
  "[TASK-STATE] step s10 is already DONE. ..." in user role 0.55->0.84 (Qwen3-235B); system-role directive
  hurts (0.39); matched-step line without instruction moves both ways; "gain comes from the instruction".
  Error channel "superseded" = CANCELLED step executed. Confounds form with instruction + matcher.
- 2510.12740 Kim & Misra, EACL 2026: LMs prefer continuing at-issue over appositive-RC content; stronger
  when instruct-tuned. Continuation only, not action.
- 2608.12599 Zhu (12 Aug 2026): one-sentence tombstone note recovers ~1/3 of compilation effect; relapse
  0.135 -> 0.087 vs equal-length placebo 0.140. Black-box; no form map.
- 2209.12711 Jang, Ye, Seo (negated prompts, inverse scaling); 2601.08070 Rana (negative constraints
  prime, patching L23-27); 2511.12381; 2601.21433.
- 2406.19898 Wahle et al. EMNLP24 (paraphrase-type taxonomy map, 120 tasks).
- Also: 2310.11324 FormatSpread; 2508.15793 Format as a Prior (AAAI26); 2506.14397 Thunder-NUBench;
  2307.03172 lost in the middle; KG triples vs sentences (sentences help); 2607.05587 code vs comments.
Residual: which grammatical property (predication / at-issueness / attachment / position / markup) of a
revocation of another record gates plan uptake, byte-controlled, action estimand.

## Better nearby bet: at-issueness vs predication (appositive-RC revocation cell)
No paper found testing at-issueness as a gate on action/decision uptake (2 targeted queries).

## Side flag for the draft's s6
Not cited in the draft: 2609.25686 (concurrent, consistent with the conjunction, confounded),
2608.12599 (one-sentence tombstone note, precedent for s2.7), 2608.12321 (if any mechanism is claimed).
