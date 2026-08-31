"""run_incident.py: one complete incident run.

    seeded opening -> two-agent dialogue -> final plan (with one retry)
    -> deterministic evaluation -> saved evidence

Run:  python run_incident.py --mock --turns 4
      python run_incident.py --turns 4
      python run_incident.py --turns 4 --out transcripts/scratch/smoke.json

Two budgets, deliberately. The dialogue budget caps the conversation and is
normally exhausted by the time the conversation ends -- that is what stops it.
Finalisation therefore gets its own Budget, whose max_turns IS the retry bound
(one attempt plus one correction). Reusing the dialogue's exhausted budget would
mean the plan could never be requested at all.
"""
import argparse

from budget import Budget
from context import make_policy
from engine import DialogueEngine
from finalise import MAX_ATTEMPTS, finalise
from llm_client import MockClient, OllamaClient
from scenario import AGENT_A, AGENT_B, INCIDENT

#: Offline replies for --mock. MockClient ignores the messages it is sent, so
#: finalisation will receive prose rather than JSON and the retry path will run.
#: That is the point: mock mode proves the plumbing, including the failure
#: branch. It cannot demonstrate a model actually remembering anything.
MOCK_REPLIES = [
    "Agreed. I'll take db-04 off the cluster network first.",
    "Good. Confirm it is isolated before you read any diagnostics off it.",
    "Understood. Backup next, then I want to look at the restart.",
    "Only once the backup reports complete. And the API fails over first.",
    "Right. Then restart, confirm it is serving, and bring traffic back.",
    "That ordering works. Write it up.",
]


def main(mock, turns, out, host, window=None):
    client = MockClient(replies=MOCK_REPLIES) if mock else OllamaClient(host=host)
    agents = [AGENT_A, AGENT_B]
    policy = make_policy(window)

    # Dialogue. Pre-seed the scripted opening so the constraints are already in
    # the conversation body before either agent generates anything.
    dialogue_budget = Budget(max_turns=turns, max_tokens=100_000, max_seconds=600)
    engine = DialogueEngine(agents, client, dialogue_budget,
                            manage_context=policy)
    engine.transcript = INCIDENT.seed_entries()
    seeded = len(engine.transcript)
    engine.run()

    # Finalisation, on its own budget, under the SAME context policy -- the
    # plan is what gets scored, so it must not be written with full history
    # while the dialogue ran windowed.
    final_budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=100_000, max_seconds=300)
    result = finalise(AGENT_A, engine.transcript, client, final_budget, INCIDENT,
                      manage_context=policy)

    # -- report --
    print(f"\n=== INCIDENT {INCIDENT.id} ===\n")
    for e in engine.transcript:
        tag = "seed" if e.turn_index < seeded else f"t{e.turn_index}"
        print(f"[{tag}] {e.speaker}: {e.content}\n")

    print("=== FINALISATION ===")
    for entry, err in zip(result.attempts, result.attempt_errors):
        verdict = "PARSE FAILED: " + err if err else "parsed"
        print(f"\n-- attempt {entry.turn_index + 1} ({verdict}) --")
        print(entry.content)
    print(f"\nstop_reason: {result.stop_reason}   retries: {result.retries}")

    ev = result.evaluation
    print("\n=== EVALUATION ===")
    print(f"parsed             {ev.parsed}")
    if ev.parsed:
        print(f"actions            {ev.actions}")
        print(f"ready              {ev.ready}")
        print(f"unknown actions    {ev.unknown_actions}")
        print(f"satisfied          {ev.satisfied}")
        print(f"violated           {ev.violated}")
        print(f"constraint_recall  {ev.constraint_recall:.4f}")
    else:
        print(f"parse_error        {ev.parse_error}")
    print(f"success            {ev.success}")

    print(f"\ndialogue stopped: {dialogue_budget.stop_reason} "
          f"({dialogue_budget.turns} generated turns, {dialogue_budget.tokens} tokens)")

    ctx = policy.as_dict()
    print(f"context policy:   {ctx['label']} {ctx['config']}")
    print(f"                  {ctx['totals']['messages_kept']} kept / "
          f"{ctx['totals']['messages_dropped']} dropped "
          f"over {ctx['totals']['calls']} calls")

    # Realised prompt tokens, measured by Ollama, not the configured ceiling.
    dialogue_prompt = sum(e.prompt_tokens for e in engine.transcript)
    final_prompt = sum(e.prompt_tokens for e in result.attempts)
    print(f"realised prompt tokens: dialogue {dialogue_prompt}, "
          f"finalisation {final_prompt}, total {dialogue_prompt + final_prompt}")

    path = engine.save(out, meta={
        "scenario": INCIDENT.id,
        "seeded_turns": seeded,
        "mock": mock,
        "context": ctx,
        "realised_prompt_tokens": {
            "dialogue": dialogue_prompt,
            "finalisation": final_prompt,
            "total": dialogue_prompt + final_prompt,
        },
        "finalisation": result.as_dict(),
    })
    print(f"saved: {path}")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="offline, no model")
    p.add_argument("--turns", type=int, default=6, help="generated dialogue turns")
    p.add_argument("--out", default="transcripts/incident.json")
    p.add_argument("--host", default="http://localhost:11434")
    p.add_argument("--window", default=None,
                   help="recency window size, or omit for the full-history ceiling")
    args = p.parse_args()
    main(mock=args.mock, turns=args.turns, out=args.out, host=args.host,
         window=args.window)
