# AgentCom starter code

This is the code skeleton you build on across the four weeks. Some files are
complete (you just use them), others have TODOs you fill in.

Read the "Cost & Safety" section in the course handbook before your first lab.

## Getting started

```
pip install -r requirements.txt
```

You also need [Ollama](https://ollama.com) installed with a small model pulled:

```
ollama pull llama3.2:3b
```

Don't have Ollama yet or working offline? Everything runs in **mock mode** --
add `--mock` to any command and it uses canned replies instead of a real model.
You can build and debug your entire loop this way.

## First thing to try

```
python run.py --mock     # should print a reply instantly
python run.py            # uses the real model (needs Ollama running)
```

If the second one errors, check that Ollama is running (`ollama serve`) and
that you pulled the model with the exact tag (`llama3.2:3b`, not `llama3.2`).

## What's in here

- `budget.py` -- complete. The Budget class that caps every loop. Don't change it.
- `llm_client.py` -- complete. OllamaClient + MockClient, same interface.
- `agents.py` -- complete. A small Agent dataclass (name, prompt, model, temperature).
- `ping_pong.py` -- Week 1 starting point. Two agents debating. Edit the personas.
- `engine.py` -- has TODOs. You implement `view_for` and `run` in Week 2, add
  `manage_context` in Week 3.
- `run.py` -- complete. Smoke test + config-driven runner.
- `test_engine.py` -- self-check for Week 2. Run it after implementing engine.py.
- `configs/debate.yaml` -- example config. Copy it and tweak for experiments.

## Week by week

**Week 1**: Run `python ping_pong.py --mock`, then swap in your own personas
and scenario. Write the design doc.

**Week 2**: Fill in the two TODOs in `engine.py`, then run a full dialogue with
`python run.py --config configs/debate.yaml --mock`.

**Week 3**: Add context management, write a judge function, run experiments by
copying the config and changing one parameter at a time.
The config's optional `context:` block chooses the policy (`full`, `recency`,
`recency_words`, `bm25`, `fusion`); `configs/debate_window4.yaml`,
`debate_window8.yaml` and `debate_bm25.yaml` are `debate.yaml` with that one
block changed.
The plan's diagnostic arms for the selector experiment (`full` ceiling,
`last`-message floor, `sabotage` selector) run with
`python e1_landscape.py --sanity`; outcome in
`docs/protocols/E1S-selector-sanity-arms.md`.

**Week 4**: Break things on purpose, collect your numbers from the saved
transcripts in `transcripts/`, write the report.

## One rule

No `while` loop that calls a model exists without a Budget controlling it.
If you're unsure about something, start with `Budget(max_turns=2)` in mock mode.
Two turns can't hurt.

## The Zombie Constraint X-ray

Everything the research branch measured, on one page, rebuilt from the result
files every time it starts:

```
python xray_server.py        # builds from results/, opens http://localhost:8765/
python xray_server.py --daemon   # same, detached from the shell; logs in results/
python xray_build.py         # writes the static page to docs/xray/zombie_xray.html
```

The page shows real dialogues and the six models' actual plans, the relapse
ladder with intervals recomputed from the CSVs, the four memory designs, and
the E29 rows. With Ollama running, the live panel lets you pick a dialogue, an
arm and a memory design, see the exact block the decider was given, and press
**Run live** to send it to the local model now and compare with the record.
Press **Play** in *Watch it happen* and a dialogue plays line by line while a
small 3D city shows the memory store: six buildings for the six steps, the two
agents as lights, roof lamps for what each design has stored, the decider's
ripple while tokens stream, and the plan drawn as a path. Live runs are demo
calls; nothing is written to `results/`.
