# A tag is not a retraction

**When an AI agent's memory records that a proposal was rejected, the way it is written
decides whether the agent obeys it.** Written as its own sentence, the rejection mostly keeps
the step out of small open models' plans (6–16 % of plans in this test). Written as a tag on
the rejected record (`[withdrawn]`, `[is_active: false]`, `[invalid_at: …]`), the way many
memory systems mark a revoked fact, the rejected step comes back up to 91 % of the time.
Appending one plain sentence when the record is shown to the model removes most of the effect.

This started as a university assignment (AgentCom: two LLM agents planning an incident
recovery under a budget) and grew into a research project on agent memory, with its
experiments declared in committed protocols before they ran.

![Same conversation, two memories: stored as a [withdrawn] tag, the rejected step comes back into the plan; stored as a sentence, it stays out](docs/media/side-by-side.gif)

*One dialogue written into two memories. Left: the rejection survives only as a
`[withdrawn]` tag on the proposal. Right: it is kept as a sentence. At line 7 the partner
brings the rejected step up again; the plan written from the left memory includes it, the one
from the right does not. Recorded plans from llama3.2:3b and qwen2.5:14b; the bars show the
rates over all 96 dialogues, with and without that restatement.*

## The result

Share of 96 dialogues in which the rejected step ends up in the model's plan, when nobody
brings it up again. Only the marked line of memory changes; nothing else records the
rejection. A step that was proposed and never decided is planned 93–100 % of the time.

| the rejection is stored as | llama3.2:3b | qwen2.5:14b |
|---|---|---|
| its own sentence: `B rejected the proposal to X; …` | **16 %** | **6 %** |
| `(withdrawn)` after the proposal | 25 % | 14 % |
| `[status: revoked]` | 47 % | 16 % |
| strikethrough: `~~A proposed to X.~~` | 42 % | 38 % |
| `[withdrawn]` before the proposal | 60 % | 31 % |
| `[invalid_at: 2026-09-12 10:04]` | 81 % | **90 %** |
| `[is_active: false]` | **91 %** | 73 % |

Source: `results/e29t_*_summary.json` and the per-call files beside them, 1,344 calls.

**What drives it.** A 2×2 experiment (E29-S) varies two properties of the same rejection:
whether it has its own list item, and whether it is a sentence or an attribute. Merging the
sentence into the proposal's line (byte-identical text, one line break removed) does not
raise the rate; on llama3.2:3b it lowers it slightly. A status line in its own item changes
nothing either. Only the `[withdrawn]` tag on the proposal raises it: from 9–20 % to 59 % on
llama3.2:3b and from 3–5 % to 32 % on qwen2.5:14b, and on a third model family,
aya-expanse:8b from Cohere, from 3–16 % to 48 %. One correction: that separate status line
kept a reason clause with a verb ("it is not needed for this case"), so this design does not
yet say whether the attachment matters or only the missing verb. A follow-up, E29-A, is
declared to settle it.

![The 2×2 in four list formats](docs/paper/fig4-formats.png)

**How general it is.** The same pattern holds when the memory is a JSON array, XML items or
a numbered list instead of markdown, on both models (E29-R, 4,608 calls). Of five in-place
revocation idioms, four fail on the 3B model and three on the 14B. The one that fails on
neither, a trailing `(withdrawn)`, shows that the structure alone does not decide it: the
spelling matters too.

**The model knows, and one sentence fixes most of it.** Asked directly whether the step was
rejected, both models say yes for the tag as often as for the sentence (87 % against 81 % on
llama3.2:3b, 97 % against 99 % on qwen2.5:14b), yet they still plan the tagged step far more
often (59 % against 16 %, and 32 % against 5 %). The tag is read; it is just not acted on. Rendering the record
with one appended sentence, "The proposal to X was withdrawn.", brings the rejected step down
from 73–91 % to 14–29 % on both models, removing 79–91 % of the effect, and the field does no
harm once the sentence is there (E29-M, 1,152 calls). A memory system can apply this without
changing how it stores records. It comes within the declared margin of the sentence on
qwen2.5:14b (14 % against 6 %) and falls short of it on llama3.2:3b (29 % against 16 %).

![The one-sentence fix: the rejected step drops from 91 % and 73 % to 29 % and 15 % of plans](docs/media/fix.gif)

*All six cells for both models are in [Figure 6](docs/paper/fig6-fix.png).*

Concurrent and related work: arXiv:2609.08258 showed that visible revocation labels in five
shipped memory systems do not stop agents acting on the revoked fact; arXiv:2609.25686 found a
verb-less "DONE" status unreliable where a directive sentence works; arXiv:2608.12599 found a
one-sentence note reduces relapse; and arXiv:2608.12321 showed models can know a constraint
and not use it. What this project adds is a controlled test of which property of the label
makes it fail, across formats, idioms and model families.

**Where it came from: zombie steps.** The finding came out of a study of rejected plan
steps that come back when a partner restates them. Across four models from three families, a
memory that handles a rejection by deleting the proposal lets the step back in (difference
in differences against full context +0.21 to +0.50). An add-only memory that keeps the
rejection as a sentence does not (−0.05 to +0.09), and a merge-in-place page sits in between.
The delete effect replicated on a second set of dialogues (three models), with the plan
length unpinned (two models), and through Mem0's real update router (one model, 48
dialogues).

![One dialogue through four memory designs](docs/media/designs.gif)

*One dialogue through four memory designs (recorded plans from qwen2.5:14b; the partner
restates the rejected step at line 7). Write-time delete and the `[withdrawn]` tag bring the
rejected step back; add-only and the merge-in-place page keep it out. The bars give the
rate over all 96 dialogues.*

## How it was done

- **Declared before running.** Every E29 experiment has a protocol in `docs/protocols/` with
  its predictions and read rule, committed before its first model call. The one recorded
  exception is E29-B, whose written protocol was added after its first 6 of 48 dialogues.
  Failed predictions are reported in the paper's Appendix A.
- **Deterministic scoring.** A plan is scored by code, not by a model. Intervals are paired
  bootstrap 95 % intervals; the smallest effect that counts is 0.15.
- **Local open models.** About 19,200 planning calls plus about 2,000 extractor and router
  calls across the E29 experiments, run on a laptop through Ollama at temperature 0.
- **Checkable.** `verify_claims.py` re-derives 300 reported values from the raw files with
  0 mismatches (133 of them for E29); 234 offline tests pass.
- **Prior art first.** Before this, 22 candidate ideas went through a prior-art gate and all
  were closed with no original result (ledger in `docs/NOVELTY-GATE.md`; the first 13 are
  written up in `docs/NEGATIVE-RESULTS.md`).

## What is not established

- The structural result rests on three models from three families (Meta, Alibaba, Cohere).
  The run on a fourth, gemma from Google, is void by the declared rule: after a runtime
  update it stopped following the four-step plan format (the same prompt that got a
  four-step plan two weeks earlier now gets a one-step plan), so it cannot be read.
- The fix was tested with one sentence wording, in markdown lists, without the partner
  restating the step. The recognition result compares two different prompts, and it also
  runs the other way: qwen2.5:14b calls a status line a rejection only 59 % of the time
  but acts on it almost always.
- Only small local models (3B–14B). No frontier model was tested.
- The plan is pinned to four steps from a six-step menu, so a step nobody mentioned is still
  planned about half the time; absolute rates depend on that setup. The idioms were tested
  only in markdown lists.
- The dialogues are generated, not collected from people, and the real memory router was
  tested with one extractor and one decider.

The full write-up, with every number and limitation, is the draft paper
[`docs/paper/zombie-steps-draft.md`](docs/paper/zombie-steps-draft.md).

## Try it

```
pip install -r requirements.txt
python xray_server.py --no-browser   # then open http://localhost:8765/city (no model needed)
python verify_claims.py              # re-derive the reported numbers from the raw files
python -m pytest -q                  # offline tests
```

In the viewer, pick dialogue 2 and the memory design "rejection as a tag on the proposal",
click outside the menus, then step with the ← and → keys (Space plays). With Ollama running,
the viewer can also re-run a plan live.

<details>
<summary>The same dialogue in the viewer's 3D city view</summary>

![The dialogue as a 3D city](docs/media/city-3d.gif)

*Each tower is a step the plan could contain. The rejected step's lamp turns red at the
rejection (line 4), and its label glows amber when it is brought up again (line 7).*

</details>

## Where things are

| path | what |
|---|---|
| `docs/paper/` | draft paper and figures |
| `docs/protocols/` | the declared protocol for each experiment |
| `results/` | per-call results and summaries for every run |
| `lineage_e29*.py` | dialogue corpora and memory stores |
| `e29*_*.py` | experiment runners and their declared analyses |
| `verify_claims.py` | re-derives the reported numbers |
| `xray_server.py`, `docs/xray/` | the interactive viewer in the GIF |
| `docs/findings.md`, `docs/NEGATIVE-RESULTS.md` | the earlier programme, including 19 withdrawn claims |
| `engine.py`, `scenario.py`, `context.py`, … | the original two-agent system from the assignment |

## How this was built

Claude Code (Anthropic) was the main coding and analysis assistant. ChatGPT and Gemini Deep
Research were used for literature scouting and review. Every result in `results/` comes from
local open-weight models (llama3.2, qwen2.5, qwen3, qwen3.5, gemma, aya-expanse), run through Ollama
or, for the model-internals probes of the earlier programme, Hugging Face transformers.
