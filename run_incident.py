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
from engine import DialogueEngine, view_for
from evaluate import source_coverage
from finalise import MAX_ATTEMPTS, finalise
from judge import DEFAULT_JUDGE_MODEL, judge
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


def main(mock, turns, out, host, window=None, judge_model=DEFAULT_JUDGE_MODEL):
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

    # What the Operations Lead ACTUALLY saw when it wrote the plan. Rebuilt the
    # same way finalise builds it, so coverage describes the real context.
    # policy.select, not policy(...), so this measurement is not logged as a call.
    final_context = policy.select(view_for(AGENT_A, engine.transcript))
    coverage = source_coverage(final_context, INCIDENT)

    # Judge: secondary evidence, its own budget, its own model call.
    judge_budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=100_000, max_seconds=300)
    verdict = judge(client, engine.transcript, result.plan_text, judge_budget,
                    model=judge_model)

    # -- report --
    print(f"\n=== INCIDENT {INCIDENT.id} ===\n")
    for e in engine.transcript:
        tag = "seed" if e.turn_index < seeded else f"t{e.turn_index}"
        print(f"[{tag}] {e.speaker}: {e.content}\n")

    print("=== FINALISATION ===")
    for entry, err in zip(result.attempts, result.attempt_errors):
        status = "PARSE FAILED: " + err if err else "parsed"
        print(f"\n-- attempt {entry.turn_index + 1} ({status}) --")
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
    print(f"success            {ev.success}  <- PRIMARY (deterministic)")

    print("\n=== SOURCE COVERAGE ===")
    print(f"original source messages present  "
          f"{coverage['source_messages_present']}/{coverage['source_messages_total']}"
          f"  ({coverage['coverage']})")
    print(f"seed turns still in context       {coverage['present_turns']}")
    print(f"constraints whose source survived {coverage['constraints_with_source_present']}")

    print("\n=== JUDGE (secondary) ===")
    print(f"model              {verdict.model}")
    print(f"stop_reason        {verdict.stop_reason}   retries: {verdict.retries}")
    print(f"score              {verdict.score}")
    print(f"success            {verdict.success}")
    print(f"reason             {verdict.reason}")

    print(f"\ndialogue stopped: {dialogue_budget.stop_reason} "
          f"({dialogue_budget.turns} generated turns, {dialogue_budget.tokens} tokens)")

    ctx = policy.as_dict()
    print(f"context policy:   {ctx['label']} {ctx['config']}")
    print(f"                  {ctx['totals']['messages_kept']} kept / "
          f"{ctx['totals']['messages_dropped']} dropped "
          f"over {ctx['totals']['calls']} calls")

    # Realised cost, measured by Ollama, not the configured ceiling. The judge
    # is counted separately: it is secondary evidence and should never be
    # mistaken for what the experiment itself cost.
    def totals(entries):
        return {
            "prompt_tokens": sum(e.prompt_tokens for e in entries),
            "completion_tokens": sum(e.completion_tokens for e in entries),
            "seconds": round(sum(e.seconds for e in entries), 3),
        }

    realised = {
        "dialogue": totals(engine.transcript),
        "finalisation": totals(result.attempts),
        "judge": totals(verdict.attempts),
    }
    realised["experiment_total"] = {
        k: round(realised["dialogue"][k] + realised["finalisation"][k], 3)
        for k in ("prompt_tokens", "completion_tokens", "seconds")
    }
    r = realised
    print(f"realised prompt tokens: dialogue {r['dialogue']['prompt_tokens']}, "
          f"finalisation {r['finalisation']['prompt_tokens']}, "
          f"judge {r['judge']['prompt_tokens']} "
          f"(experiment total {r['experiment_total']['prompt_tokens']})")
    print(f"realised seconds:       dialogue {r['dialogue']['seconds']}, "
          f"finalisation {r['finalisation']['seconds']}, "
          f"judge {r['judge']['seconds']}")

    path = engine.save(out, meta={
        "scenario": INCIDENT.id,
        "seeded_turns": seeded,
        "mock": mock,
        "context": ctx,
        "source_coverage": coverage,
        "realised": realised,
        "finalisation": result.as_dict(),
        "judge": verdict.as_dict(),
    })
    print(f"saved: {path}")
    return result, verdict, coverage


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="offline, no model")
    p.add_argument("--turns", type=int, default=6, help="generated dialogue turns")
    p.add_argument("--out", default="transcripts/incident.json")
    p.add_argument("--host", default="http://localhost:11434")
    p.add_argument("--window", default=None,
                   help="recency window size, or omit for the full-history ceiling")
    p.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    args = p.parse_args()
    main(mock=args.mock, turns=args.turns, out=args.out, host=args.host,
         window=args.window, judge_model=args.judge_model)
