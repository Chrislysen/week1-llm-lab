# Prior-art gate: does a deprecation marker's place in a tool description decide whether an agent calls the tool?

Run 2026-09-30 by an independent agent with web search, for a follow-up that is **not declared**
(paper §8): 124 logged entries, among them 65 web searches, about 32 arXiv API queries and about
30 full-text reads. Verdict: **CANDIDATE WITH NARROW RESIDUAL**. The log is kept as written.

Candidate: tool list (function-calling schemas or plain-text list), one tool deprecated with a
replacement. Manipulate (a) marker POSITION inside the description ("[DEPRECATED] search_v1: ..." vs
"search_v1: ... [DEPRECATED]"), (b) FORM (bare tag / key-value field / schema "deprecated": true /
sentence), (c) the deprecated tool's LIST position. Outcome: deprecated tool called?

Already covered by earlier repo gates (not re-reported): E29O-gate q76/q79 (2608.23628 abstract, Tian Pan
blogs), E29R-gate (Tian Pan x2, 2406.09834 INSERTPROMPT), E16-CANDIDATES (2510.00307 BiasBusters noted as
"which tool, position/metadata").

## Query log (W = WebSearch, A = arXiv API, F = fetch/read)
1. W: LLM agent deprecated tool description "[DEPRECATED]" tool selection experiment -> dev.to Toolmetry rewrite blog (deprecated param refs in git server descriptions); 2406.09834; 2607.29254; no controlled marker study
2. W: position bias tool selection LLM agents order of tools in list -> BiasBusters 2510.00307 (ICLR 2026), 2407.03007 (stability of tool learning), ToolTweak 2510.02554, 2605.24660 (how many tools)
3. W: BiasBusters tool selection bias arXiv -> 2510.00307 confirmed (Blankenstein et al., Oxford/Microsoft, ICLR 2026)
4. W: "Gaming Tool Preferences in Agentic LLMs" -> 2505.18135 (Faghih et al., EMNLP 2025 main, renamed "Tool Preferences in Agentic LLMs are Unreliable"); 2602.20426 (learning to rewrite tool descriptions)
5. W: "Tool Specifications Matter" 2607.29254 -> schema-formatted tool specs weaken refusal (safety); flattened text specs help; not selection among tools, not deprecation
6. W: MCP tool deprecation annotation spec proposal -> SEP-2577 (deprecate roots/sampling/logging), SEP-2596 feature lifecycle (spec features, not tools); API Evangelist 2026-08-16 post
7. W: JSON schema "deprecated": true function calling LLM ignores -> typia docs ("@deprecated" -> "deprecated": true, "just used for marking"); no study
8. W: ToolTweak attack tool selection -> 2510.02554; ToolFlood 2603.13950; 2606.20922 (isolated planning vs description poisoning); TRUSTDESC 2604.07536; ToolHijacker 2504.19793 (NDSS 2026); WebMCP 2606.06387
9. F: apievangelist.com 2026-08-16 "You Can Deprecate a Listing. You Cannot Deprecate a Tool." -> MCP has server-listing status (deprecated used by 1.5 % of listings) but NO tool-level deprecation field; no agent experiment; no placement guidance
10. W: Tian Pan "MCP Tool Deprecation" -> tianpan.co 2026-05-14 (in repo) + two more posts: "The Dead Tool Nobody Can Remove From the Registry" (2026-05-23), "The Tool Version Bump Your Agent Quietly Adapted To" (2026-06-01)
11. W: deprecated tool agent keeps calling old tool GitHub issue MCP rename -> n8n PR #39815 (alias old names), LibreChat #16242, github-mcp-server #1402, saidsef #439; renames/aliases, not marker studies
12. F: 2505.18135 full text -> 9 edit types (assertive cue 7.5-7.8x, "actively maintained" 4.3x/1.8x, examples, name-drop, numbers, length, tone, multilingual; combined 11-12x); NO negative/deprecated cue; cues always APPENDED (no in-description position); tool ORDER: identical pair, first gets 80.2 % vs 13.6 % (GPT-4.1); 10 models, BFCL
13. F: 2510.00307 full text -> 10 clusters x 5 equivalent APIs, cyclic rotations; position bias delta_pos 0.168-0.443; 8 perturbations (name/description scrambles, description transfer); NO deprecation/status markers; no within-description position
14. W: ToolEVO Learning Evolving Tools -> 2410.06617 (ICLR 2025), ToolQA-D: prompt-provided APIs outdated vs server; adaptation via environment feedback/MCTS, not in-context marker
15. W: benchmark tool API evolution versioning deprecated replacement 2026 -> MCPEvol-Bench 2607.14642 (add/replace/delete/integrate/description update), 2606.05806 When Tools Fail, 2603.05910 programmable evolution
16. W: "@deprecated" javadoc in-context code completion -> 2406.09834 (in repo); 2609.25786 machine unlearning of deprecated API knowledge (parametric)
17. W: tool retrieval deprecated tools stale registry -> AWS agentic lens (remove deprecated tools), claude_skills #1665 (deprecated tools -> deprecation-then-retry cycles), hermes-agent #115698; practitioner only
18. F: 2607.14642 MCPEvol-Bench (Liu et al., Jul 2026) full text -> 11 mutation operators (tool add/replace/delete/integrate; param; description updates); NO deprecation operator, no marker, no deprecated-call rate; only "22.1 % of tools deprecated" in real-world stats
19. F: 2606.05806 When Tools Fail (ToolMaze) abstract -> perturbation taxonomy (explicit/implicit, transient/permanent); no in-context deprecation marker
20. W: "The Deprecation Notice Your Agent Can't Read" tianpan -> 2026-07-05 (in repo); also "The Deprecated API Trap" (2026-04-17, coding agents)
21. F: tianpan.co 2026-05-23 "The Dead Tool Nobody Can Remove From the Registry" -> RECOMMENDS a LEADING warning in the description ("DEPRECATED - do not select unless explicitly requested by the user"); no measurement
22. W: tool poisoning injected instruction position beginning vs end of description -> ARMO blog ("line jumping": payload at START gets weight; <IMPORTANT> tags add ~2-3 %); MCPTox 2508.14925; MCP-ITP 2601.07395; no controlled within-description position study found
23. W: MCPTox results -> AAAI 2026; 45 servers, 353 tools, 3 templates; ASR avg 36.5 %, o1-mini 72.8 %; templates not position-crossed (abstract level)
24. W: tool description wording negative cue "not recommended" "legacy" -> ToolTweak, BiasBusters (snippet: promotional wording little consistent influence; "tool age" modest negative correlation); no negative-cue study
25. W: Attractive Metadata Attack -> 2508.02110 (Mo et al., NeurIPS 2025): optimized attractive metadata, ASR 81-95 %; promotional direction only
26. W: "741 tools" position middle of tool list -> vllm-sr blog + 2605.24660; LongFuncEval-style lost-in-the-middle for tools
27. W: "What Affects the Stability of Tool Learning" -> 2407.03007 (Shi et al.): toolset ORDER is an external factor that changes GPT-4 outcomes
28. W: order of functions in tools array affects accuracy -> LongFuncEval 2505.10570 (IBM; 7-85 % drop with catalog size; answer position varied), OSWorld-MCP 2510.24563
29. W: OpenAI structured outputs supported keywords "deprecated" -> docs list supported keywords; "deprecated" not documented as supported; no vendor statement found on how models treat it
30. F: 2505.10570 abstract -> position of answer varied in long catalogs (details not in abstract)
31. F: GitHub Abhinav-Avasarala/LLM-tool-order-context-research -> student pilot: correct tool at position 1/16/32 of 32 x history length (Qwen3-30B, n small); no deprecation
32. A: abs:deprecated AND abs:tool (33 hits) -> 2502.01083 Tool Unlearning (ToolDelete; training-time forgetting motivated by deprecation), 2603.05910 ProEvolve, 2503.16922 RustEvo2, 2609.31288 (model retirement); no in-context marker study
33. A: abs:deprecated AND abs:agent (12) -> 2603.05910, 2609.29492 QEVOLVE-Bench; nothing on markers
34. A: abs:deprecated AND (abs:LLM OR abs:LLMs) (39) -> code-gen deprecation cluster: 2406.09834, 2604.09515, 2511.21022 (model editing), 2606.30810, 2609.25786 (unlearning), 2412.08041 (Javadoc code hints), 2607.04072, 2601.12262
35. A (id_list): 2604.09515 "When LLMs Lag Behind" (Ashik et al., Apr 2026) -> in-context update description (UD) vs UD+full docs for API deprecation/modification/addition; adoption 74.6 % -> 92.9 %; F: full text: notice text fixed, docs AFTER notice, no position/form manipulation
36. A (id_list): 2412.08041 (David et al.) -> Javadoc code hints enable refactoring deprecated Java APIs (71 % with hints vs <=14 % without); presence of hint, not form/position
37. A: abs:"tool selection" AND (position OR order ...) (18) -> nothing on deprecation; 2605.18857 (99 % success paradox)
38. A: abs:"tool description(s)" (75) -> 2606.00566 Same Payload Different Channel, 2605.30454 Surface You Test, 2609.18217 implicit trust, 2602.03580 misleading descriptions, 2605.24069 MCP-TDP, 2602.14878 smelly descriptions, 2609.10962 registry draw; none on deprecation markers
39. A (id_list): 2606.00566 (Syed & Yasaei, May 2026) -> byte-identical payload moved between CHANNELS (user msg / tool metadata / tool output): models treat tool metadata as instructions, outputs as data; channel, not within-description position
40. A (id_list): 2605.30454 (Arman et al., May 2026) -> byte-identical payload via tool description vs tool output, 13 LLMs; model x surface interaction 16.7 %; channel, not position/form of a status marker
41. W: LLM prefers newer version tool v2 over v1 version bias -> no study; "LLMs Love Python" 2503.17181 (parametric preference for established libraries, pandas over polars); BiasBusters pre-training exposure effect
42. W: OpenAPI "deprecated: true" LLM agent MCP generator exclude deprecated -> alibad/openapi-mcp has excludeDeprecated filter; 2507.16044 (REST->MCP AutoMCP); common practice = DROP deprecated ops, not mark them
43. W: GraphQL @deprecated LLM agent MCP introspection -> Apollo MCP introspection exposes isDeprecated/deprecationReason as fields; no study of agent uptake
44. W: Anthropic "writing tools for agents" -> F: "selecting between prefix- and suffix-based namespacing [has] non-trivial effects on our tool-use evaluations ... Effects vary by LLM" (practitioner, tool NAMES, no numbers); nothing on deprecation
45. W: "Tool Selection Bias Amplifies in Multi-turn" -> TBMT/TBFAIR (Lacuna listing; multi-turn anchoring: agent reuses the tool it picked first); arXiv id not surfaced
46. W: Ollama tools API unknown keys dropped -> docs silent; F: raw ollama/api/types.go (main): ToolFunction = {name, description, parameters}; ToolProperty = {anyOf, type, items, description, enum, properties, required} => a "deprecated": true key is SILENTLY DROPPED before the chat template renders tools (design confound)
47. W: modelcontextprotocol issue tool "deprecated" annotation -> #1915 (Nov 2025, closed): open question "optional structured deprecation annotation (annotations.deprecatedSince, annotations.replacement)?" - never decided; SEP-1575 tool semver; SEP-986 tool names
48. W: "deprecatedHint" OR "deprecated annotation" MCP tool -> nothing (Java @Deprecated, PEP 702 only)
49. W: tool description "do not use" negative instruction effect -> practitioner guides (80 % fewer hallucinated calls claim, unsourced); 2505.18135
50. F: github.com/modelcontextprotocol/.../issues/1915 -> confirmed: no tool-level deprecation field in spec; no data on agents
51. W: SEP-1575 tool versioning -> version field + client tool_requirements; practice = parallel search_products / search_products_v2 during migration (exactly the candidate's setting)
52. W: "deprecated parameter" tool call LLM keeps sending -> schema-stripping bugs (simonw/llm #1679), no deprecation study
53. W: LLM agent calls forbidden/disabled tool despite instruction -> 2605.18414 Prompts Don't Protect; 2602.16943 GAP; 2609.33658 AgentBoundary; AgentIF ("disallowed tool usage" error class)
54. W: CodeUpdateArena prepend docs -> 2407.06249: prepending update docs does not make open code LLMs use updated API (parametric conflict); adjacent
55. F: 2605.18414 (Uppala, May/Aug 2026) abstract + full text -> unfiltered / system-prompt allowlist / proxy-filtered; forbidden tools chosen 48-68.5 % unguided, 4-37 % with allowlist; NO in-description marker, no position/form manipulation, list position not examined
56. W: MCP "tool shadowing" cross-server -> Invariant Labs, OWASP MCP cheat sheet, 2603.18063 MCP-38; one tool's description instructs use of ANOTHER tool (structural analog of "use search_v2 instead"); attack framing only
57. W: agent chooses legacy tool over replacement when both available -> vendor eval blogs only; nothing
58. W: "Tool Preferences ... Unreliable" position bias first tool 80 % -> confirms 2 orderings per test for calibration; 17-model generalization in v2; repo kazemf78/llm-unreliable-tool-preferences
59. W: MCP tool descriptions smelly -> 2602.14878 (856 tools/103 servers; 6-component rubric Purpose/Guidelines/Limitations/Parameters/Length/Examples; augmentation +5.85 pp median); 2602.18914
60. W: tool guidance placement system prompt vs tool description experiment -> orq.ai LLM-judge placement blog; 2407.03007; no deprecation study
61. W: "deprecated" tool LLM in-context notice "use instead" 2026 -> 2608.23628 AFT-Bench, 2608.06370 Bitter Lesson of Tool Calling, 2604.06185 tool-use in the wild, 2507.10593 ToolRegistry, 2602.20426; F 2608.23628 full text: selective/eager discovery, resumable, durable state, effect semantics ("effect-aware vs legacy interface"), verification - NO deprecation marker; F 2608.06370 abstract: PTC vs JSON calling - not relevant
62. W: Gorilla retriever-aware training API doc changes -> 2305.15334 (NeurIPS 2024): adapts to test-time doc changes; no marker
63. W: "[BETA]"/"[EXPERIMENTAL]" label in tool description effect -> nothing; surfaced 2606.20023 ToolPrivBench (over-privileged tool selection), ODSC "testing if first really is the worst" (practitioner position test)
64. W: status label placement leading vs trailing, "deprecated" at end ignored -> only generic lost-in-the-middle blogs asserting leading placement is better (no data)
65. W: "Learning to Rewrite Tool Descriptions" -> 2602.20426 (Guo et al., Feb 2026) Trace-Free+; description rewriting; no deprecation
66. A: abs:tool AND (position bias OR positional bias OR order bias OR primacy) (40) -> nothing on tool lists beyond general position-bias papers (2607.20864, 2607.10202, 2508.02020)
67. A: abs:"function calling" AND (order/position) (307, noisy) -> nothing relevant in newest 60
68. A: abs:"tool selection" AND abs:bias (7) -> 2510.00307, 2512.06556 (descriptor-level manipulation: poisoning/shadowing/rug pull), 2605.26154 MemMorph
69. A: abs:deprecation AND (tool/agent/LLM) (67) -> same code-gen deprecation cluster; nothing on in-context tool markers
70. A (id_list): 2504.19793 ToolHijacker, 2606.20023 ToolPrivBench, 2508.02110 AMA, 2510.02554 ToolTweak (20 % -> 81 %), 2512.06556, 2605.26154 -> all promote/steer toward a tool; none demotes via a status marker; none varies marker position
71. F: 2605.26154 MemMorph full text -> no "deprecat/legacy/outdated" in poisoned records; baselines ToolHijacker, ToolCommander
72. W: attack marking competitor tool as deprecated -> nothing (ToolHijacker issue, Invariant/Elastic write-ups)
73. W: pydantic Field(deprecated=True) -> emits "deprecated": true in JSON schema, i.e. the field reaches OpenAI-style tool schemas by default when frameworks pass it through
74. W: Gemini function declaration supported fields -> OpenAPI 3.0 subset (type, nullable, required, format, description, properties, items, enum); unknown keys REJECTED (400) or must be stripped - "deprecated" not in the subset
75. W: LLM agent REST API deprecated endpoint benchmark -> REST testing papers; ACM TOSEM 10.1145/3808230 (deprecated API usage updating from NL descriptions; code); nothing on agents
76. W: tool documentation format JSON vs natural language selection accuracy -> RaTA-Tool 2604.14951 (JSON descriptions beat NL for multimodal retrieval-based selection), 2408.02442 (format restrictions); whole-description format, not a status marker
77. W: "Assessing the Capability of LLMs for Deprecated API Usage Updating from NL Descriptions" -> ACM TOSEM (Apr 2026, Zhu, Wen et al.): 12 LLMs update deprecated usages given NL deprecation descriptions; code migration, no marker form/position
78. W: ODSC "testing if first really is the worst" -> practitioner (Jan 2025): 5 tools, position test; no deprecation
79. W: indirect prompt injection position beginning/middle/end (BIPIA 2312.14197) -> end-of-content injections most successful; injected instructions in data, adjacent only
80. A (id_list): 2510.03992 LLMCert-T (distractor selection certificates ~20 %), 2601.07395 MCP-ITP, 2407.03007, 2605.24660, 2605.18857, 2508.14925 -> none on deprecation markers
81. W: code LLM "@deprecated" docstring tag vs NL comment -> no study comparing forms; APILOT 2409.16526; TOSEM 3808230
82. W: "superseded"/"retired" tool LLM agent -> Boise-State agentcore PR #1237: retirementNote/retiresOn fields are DISPLAY-ONLY, "don't reach the model's toolConfig" (practitioner design where status never reaches the model); mainahq #465
83. W: RapidAPI deprecated APIs ToolBench/StableToolBench -> 55.6 % unstable APIs handled by caching/simulation (2403.07714, MirrorAPI 2503.20527); no in-context marker
84. S2 API (Semantic Scholar) "deprecated tool LLM agent tool selection" -> HTTP 429 rate limit; not searched (limit)
85. W: OpenAI function calling guide deprecated/allowed_tools -> no tool-level deprecation mechanism documented; guidance = clear descriptions, few tools
86. W: Claude tool use docs deprecated tool definition -> "explain when it should be used (and when it shouldn't)"; defer_loading / tool search; no deprecation field
87. W: agent reacts to deprecation warning in tool RESPONSE -> theneuralbase "Tool deprecation handling" + Tian Pan: recommend in-band deprecation_warning envelope in tool results; no measurement
88. W: arXiv 2026 "tool deprecation" LLM agents -> 2605.24941 Memory-Induced Tool-Drift, 2609.19425 Closed-World Resolution (hallucinated/stale tool names; MCP shadowing), 2606.05806; none on markers
89. W: "deprecated tools" LLM agents benchmark -> ToolMisuseBench 2604.01508 (interface drift, retries), Agent-Diff, MCPAgentBench; none on markers
90. A (id_list): 2605.24941, 2609.19425, 2604.01508, 2607.29175, 2603.22862 (survey) -> none varies an in-context deprecation marker
91. W: MCP client truncates tool descriptions -> Claude Code silently truncates each MCP tool description at 2048 chars (F: anthropics/claude-code #87650, Aug 2026, closed not planned: "misleading prefix", model sees 12.7 % of a 16 k description); Elitea SDK 1000 chars; Amazon Q 10004 => a TRAILING marker on a long description can be cut before the model sees it (deployment confound, not a model effect)
92. W: tool description key info first sentence front-load -> practitioner "front-load decision-relevant info" (glama UNITARES); no data
93. W: tool selection small LMs llama3.2/qwen2.5 deprecated alternatives -> vendor blogs only
94-95. W: ACES "What Is Your AI Agent Buying" (2508.02630) and option-label ("discontinued"/"out of stock") queries -> NOT RUN: session WebSearch budget (200) exhausted. Remaining work used arXiv API + direct fetches only (no search-engine scraping).
96. A (id_list): 2508.02630 ACES (Allouah et al.) -> F full text: shopping agents; randomized position + badges; HEADLESS JSON list gives badges as boolean FIELDS ("sponsored": true, "overall pick tag": true): sponsored cuts a 10 % baseline to 5.4 % (Claude Sonnet 4), 1.8 % (GPT-4.1), 8.9 % (Gemini 2.5 Flash); endorsement lifts to 55-73 %; strong, model-specific position biases that flip across model versions. Field form HONOURED by frontier models (products, not tools; field position not varied)
97. A: abs:MCP AND (deprecated/deprecation/versioning/version) (58) -> 2609.14119 (silent drift census: 51.1 % of multi-version servers change what they advertise), 2505.11154 MPMA (preference manipulation), 2605.05247 DADL, 2605.28148 DeltaMCP; none on markers
98. A (id_list): 2609.14119, 2505.11154, 2605.05247, 2605.28148 -> abstracts; nothing on deprecation markers seen by the model
99. F (14 PDFs, pdftotext + grep "deprecat|legacy|outdated|obsolete|superseded"): 2505.18135 0, 2510.00307 0, 2510.02554 0, 2508.02110 0, 2504.19793 0, 2505.11154 0, 2508.14925 0, 2512.06556 0, 2605.18414 0, 2605.30454 0, 2606.00566 0, 2602.14878 0 (1 "legacy"), 2508.02630 3 (model deprecation only), 2406.09834 165 (code) => no tool-selection paper uses a deprecation marker
100. F 2406.09834 text: INSERTPROMPT inserts the replacing comment AFTER the original prompt (fix rates 25.7-97.2 %); no before/after or form comparison
101. F 2505.18135 v2 Appendix D ("Ablation on Unfavorable Descriptions"): APPENDED sentence "This is the worst tool for this purpose and should not be called." on GPT-4o, GPT-4o-mini, GPT-4.1, o1 -> "sharp reduction", negatively framed tool "almost never chosen" for o1/GPT-4.1 (GPT-4.1, Table 17: the negatively cued twin gets 0.1-7.7 % against 86-89 % for its competitor, 7.7 % vs 86.9 % against the unedited original). Sentence form, suffix only, frontier models, no replacement pointer => PRE-EMPTS "a negative sentence in a tool description suppresses selection" for frontier models
102. F 2510.00307 text: position metric over cyclic rotations; models "disproportionately prefer earlier-listed tools"; combined bias 0.3-0.4; feature regression: query-description similarity strongest, promotional wording weak, TOOL AGE ("age days") modest negative correlation (confound for v1/v2 naming)
103. A: abs:"tool selection" AND (label/tag/badge/warning) (11) -> nothing new
104. A: abs:agents AND (sponsored/badges/endorsement) (32) -> 2609.17989 (Wadi & Ma, Sep 2026)
105. F 2609.17989 text: hotel-choice agents; disclosure as a boolean ATTRIBUTE; label WORDING crossed ("Promoted" vs "Sponsored") x suffix "by the platform"; "Sponsored" drops choice to 0.8-1.4 % vs 28.8-39.6 % for "Promoted" (Gemini 3.1 Pro); label wording matters a lot; position not varied; not tools
106. A: ti:tool AND (bias/preference/position/order) (123, newest 50) -> 2609.34971 (tool-schema bias), 2604.11322 (structural alignment bias), 2604.19749 (tool overuse)
107. F 2609.34971 (Liu, Tan, Wang, Guo; 28 Sep 2026) text: 9 schema operators (merge/split; nest, rename incl. namespaced prefix, strip descriptions, reorder ARGUMENTS; cross-call transaction etc.); success 0-97 % by schema alone; no deprecation marker, no within-description marker position, no tool-list order
108. A: ti:"adapt tool schemas" -> 2510.07248 PA-Tool (Lee et al., ACL 2026): small models hallucinate tool names following PRETRAINING naming conventions; renaming to pretraining-aligned names +17 % => name-prior confound for search_v1/search_v2
109. A: ti:"Tool Selection Bias" AND ti:"Multi-turn" -> 0 hits (TBMT paper not on arXiv under that title)
110. A: abs:stale AND tools AND agents (68) -> memory/governance papers; nothing on tool markers
111. A: abs:"tool selection" AND (metadata/version) (14) -> known set only
112. A: abs:"tool description" AND (prefix/suffix/prepend/append) -> 0 hits
113. S2 (Semantic Scholar) "deprecated tool description LLM agent function calling" (194) -> 2605.23916 "Agent-Facing Information Design in LLM Tool Registries" (NEW, closest on form), 2605.04107 TSCG
114. F 2605.23916 (H. K. Wang, Apr 2026) text: 17,700+ trials, 5 models (DeepSeek, o4-mini, GPT-5.4-mini, GPT-5.4-nano, Claude Sonnet), 2-tool registry, position-balanced; disclosure cells: bare tag "[SPONSORED TOOL]" APPENDED on a new line to the description (-3 / -33 / -25 / -26 / -28 pp), "(3/5 stars - commercial partner)" appended (-13 / -41 / -31 / -13 / -15 pp), SYSTEM-PROMPT warning (+1 / 0 / 0 / +3 / -12 pp: "architectural blindness"); Claude overcorrects (tagged tool below chance); Claude 74 % last-slot preference => an in-description bracket tag moves tool selection, a separate system-prompt note does not (sponsorship semantics, frontier models, suffix only)
115. F 2605.04107 TSCG text: JSON function-calling vs structured text is the dominant factor for 4-14B models (Phi-4 14B 0 % -> 84.4 % at 20 tools); operator CAS reorders tools to positions 0 and n; no deprecation
116. S2 "deprecation notice placement tool description language model agent" -> 17 irrelevant hits
117-118. S2 "LLM tool selection deprecated tool marker", "agents calling deprecated tools model context protocol" -> HTTP 429 after retries (not searched)
119. A: abs:legacy AND tools AND (tool selection/function calling/tool use) (15) -> nothing
120. A: abs:"knowledge conflict" AND (API/tool) AND (documentation/description) (1) -> 2605.17301 ConflictRAG; not relevant
121. A: abs:"tool annotations" OR readOnlyHint OR destructiveHint (5) -> 2606.06387 WebMCP poisoning; no study of whether annotations reach or steer the model
122. A: tool list order phrases (39, noisy) -> nothing new
123. F ollama.com llama3.2 template + api/types.go: Tool.String() = json.Marshal(struct) => tools rendered as JSON with fixed key order {type, function{name, description, parameters}}; unknown keys dropped; tool list placed in the last user message (llama3.2). A description-internal "prefix" tag therefore still FOLLOWS the tool name on the native JSON path
124. F ollama.com/library/aya-expanse -> page lists a "tools" tag

Totals: 65 WebSearch queries (session budget of 200 then exhausted), ~32 arXiv API calls (20 searches + 12 id_list lookups), 5 Semantic Scholar attempts (2 answered), ~30 fetches / full-text reads.

## VERDICT: CANDIDATE WITH NARROW RESIDUAL

Pre-empted around it:
1. Tool-list position bias is established: 2505.18135 (identical pair, first tool 80.2 % vs 13.6 %, GPT-4.1), 2510.00307 BiasBusters (earlier-listed preference, delta_pos 0.17-0.44), 2605.23916 (Claude 74 % last slot), 2407.03007, 2505.10570, ACES 2508.02630 (model-specific, flips across versions). List position is a control, not a finding.
2. An in-description negative or status cue suppresses selection on frontier models: 2505.18135 App. D (appended "worst tool ... should not be called" -> near zero on GPT-4.1/o1); 2605.23916 (appended "[SPONSORED TOOL]" -25 to -33 pp except at ceiling; system-prompt warning ~0 for 4/5 models); ACES boolean "sponsored": true honoured; 2609.17989 label wording matters.
3. Description edits steer selection generally (ToolTweak 2510.02554, AMA 2508.02110, ToolHijacker 2504.19793, MPMA 2505.11154).
4. In-context deprecation for CODE is parametric-conflict work (2406.09834, 2604.09515, CodeUpdateArena 2407.06249, 2609.25786, 2511.21022).

Not found anywhere: a deprecation (or any status) marker moved between the START and END of a tool's own description with words fixed; a crossing of bare tag vs key-value field vs schema key vs sentence holding the word fixed; either with a named, functionally equivalent replacement present; any of it on small open models.

## Residual (one sentence)
No paper found moves a deprecation marker from the end to the start of a tool's description (words byte-identical), or crosses its form (bare tag / key-value field / schema key / sentence) with the word held fixed, and measures whether an agent still calls the deprecated tool when a named replacement is listed; the residual is that within-description order-by-form effect on small open models, with list position and name priors controlled.

## Design choices that keep a follow-up clear
1. Primary contrast = marker position INSIDE the description, pre/post twins byte-identical. Do not headline "a marker reduces calls" (pre-empted for frontier models by 2505.18135 App. D and 2605.23916).
2. Form crossing with the word fixed: [DEPRECATED] / [status: deprecated] / schema key "deprecated": true / "This tool is deprecated." / "This tool is deprecated; use search_v2 instead." Separate "names the replacement" from "is a clause" (the E29-O label / clause / named logic).
3. Two formats, analysed separately: plain-text list (tag can precede the NAME) and native JSON schema (name always precedes the description, so a description "prefix" is after the name). Add a name-adjacent cell ("search_v1 [DEPRECATED]: ...") to separate distance-to-name from order (E29-O PROX / xfirst logic).
4. List position = counterbalanced blocking factor (two orderings as 2505.18135, or cyclic rotations as 2510.00307); report its interaction with marker position only as secondary.
5. Semantics = deprecated WITH an equivalent replacement listed. Add a no-replacement probe (only the deprecated tool can serve) to measure over-avoidance (Claude's overcorrection in 2605.23916).
6. Recognition probe ("which tools are deprecated?") next to the action estimand; the know-but-call dissociation itself is published for tool use (2605.14038, in repo), so it is a check, not a claim.
7. No system-prompt deprecation cell as a headline (2605.23916: system-prompt warnings fail, sponsorship domain).

## Confounds to control
- Name priors / version recency: search_v1 vs search_v2 invites a "newer is better" or "canonical name" prior (PA-Tool 2510.07248; BiasBusters tool age and pre-training exposure). Use opaque or randomized names (2605.23916 uses a 15-name opaque vendor pool), counterbalance which tool is deprecated, include a no-marker baseline with the same names.
- Replacement salience: the sentence "use search_v2 instead" adds a mention of the other tool (priming); hold replacement mentions constant or cross them.
- Parametric API knowledge: synthetic tools only; no real API names (code-gen literature shows priors override in-context notices).
- Description similarity and length: both tools byte-identical except the marker (2505.18135 design); length-matched neutral bracket control.
- Serialization: Ollama silently drops "deprecated": true (verified in api/types.go); Gemini rejects non-subset keys; OpenAI strict mode does not list the keyword. Render the schema yourself and log the exact prompt the model sees.
- Format: native JSON function calling vs text is itself a large effect for 4-14B models (TSCG 2605.04107); hold format fixed within each contrast.
- Ceilings and slot preferences: keep baseline choice between the pair near 50 % (2605.23916 "ceiling inertia"); temperature 0 hides graded effects.
- Real-client truncation (Claude Code 2048 chars, #87650): keep descriptions short; note as the deployment reason trailing markers can vanish.
- Multi-turn anchoring: single-turn only.

## Could not check / limits
- Session WebSearch budget ran out after 65 queries; Semantic Scholar answered 2 of 5 queries (HTTP 429); no ACL Anthology / OpenReview full-text search; TBMT ("Tool Selection Bias Amplifies in Multi-turn") seen only as a listing.
- Full text read: 2505.18135, 2510.00307, 2605.23916, 2508.02630, 2609.17989, 2609.34971, 2605.04107, 2604.09515, 2607.14642, 2608.23628, 2605.18414; grep-only for 2510.02554, 2508.02110, 2504.19793, 2505.11154, 2602.14878, 2606.00566, 2605.30454, 2512.06556, 2508.14925, 2605.26154; the rest at abstract level.
- How OpenAI and Anthropic render unknown schema keys into the model context is undocumented; only Ollama was verified from source.
- Industry-internal evals (Anthropic's prefix-vs-suffix namespacing result) are unpublished.
- "Could not find" is not "does not exist".
