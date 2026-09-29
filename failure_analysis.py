"""failure_analysis.py: break the system on purpose, and save what happens.

Week 4 of the brief: "break things on purpose". Each case deliberately
violates one assumption the system depends on, then records how the system
behaved. Evidence goes to transcripts/failures/, the summary table to
results/failures/summary.csv. The frozen experiment (transcripts/exp and the
CSVs in results/) is never touched.

    python failure_analysis.py              # every case (6 need Ollama, ~4 min)
    python failure_analysis.py --offline    # only the cases that need no model
    python failure_analysis.py --case window_zero

Each case states what it EXPECTS before it runs, then checks the observed
behaviour against it. `as_designed` is True when the system did what it was
built to do, False when it did not, and "finding" for cases that probe a
weakness rather than a guard.
"""
import argparse
import csv
import json
import os
import time
from dataclasses import replace

import requests

import experiment
from budget import Budget
from context import make_policy
from engine import DialogueEngine, view_for
from evaluate import evaluate, source_coverage
from finalise import MAX_ATTEMPTS, finalise
from judge import judge
from llm_client import ChatResponse, MockClient, OllamaClient
from scenario import AGENT_A, AGENT_B, INCIDENT

OUT = "transcripts/failures"
RESULTS = "results/failures"
HOST = "http://localhost:11434"

#: A plan that satisfies all seven rules. Used where a case needs a valid plan.
GOOD_PLAN = ('{"actions": ["ISOLATE_NODE", "RUN_BACKUP", "FAILOVER_API", '
             '"RESTART_DB", "RESTORE_TRAFFIC"], "ready": true}')
PROSE_PLAN = ("Sure! First isolate the node, then back it up, fail the API over, "
              "restart the database and bring traffic back.")


# ------------------------------------------------------------------- helpers
def save_json(name, record):
    os.makedirs(OUT, exist_ok=True)
    path = f"{OUT}/{name}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    return path


def fresh_budget():
    """The same finalisation budget run_incident uses: one attempt + one retry."""
    return Budget(max_turns=MAX_ATTEMPTS, max_tokens=100_000, max_seconds=300)


def run_dialogue(name, client, window=None, dialogue_budget=None, agents=None,
                 turns=10, broke=""):
    """Seeded dialogue -> final plan -> deterministic evaluation -> saved.

    The same steps as run_incident.main, minus the judge (not needed to show
    any failure here), with the knobs a failure case needs exposed.
    """
    agents = agents or [AGENT_A, AGENT_B]
    policy = make_policy(window)
    budget = dialogue_budget or Budget(max_turns=turns, max_tokens=100_000,
                                       max_seconds=600)
    engine = DialogueEngine(agents, client, budget, manage_context=policy)
    engine.transcript = INCIDENT.seed_entries()
    seeded = len(engine.transcript)
    engine.run()
    dialogue_elapsed = round(budget.elapsed, 3)   # before finalisation adds time

    result = finalise(agents[0], engine.transcript, client, fresh_budget(),
                      INCIDENT, manage_context=policy)
    final_context = policy.select(view_for(agents[0], engine.transcript))
    generated = engine.transcript[seeded:]
    path = engine.save(f"{OUT}/{name}.json", meta={
        "case": name,
        "broke": broke,
        "dialogue_stop_reason": budget.stop_reason,
        "dialogue_elapsed_seconds": dialogue_elapsed,
        "generated_turns": len(generated),
        "prompt_tokens_per_turn": [e.prompt_tokens for e in generated],
        "context": policy.as_dict(),
        "source_coverage": source_coverage(final_context, INCIDENT),
        "finalisation": result.as_dict(),
    })
    return {"budget": budget, "elapsed": dialogue_elapsed, "generated": generated,
            "result": result, "ev": result.evaluation, "path": path}


def plan_summary(ev):
    if not ev.parsed:
        return f"plan not parsed ({ev.parse_error})"
    return (f"recall {ev.constraint_recall:.3f}, violated {ev.violated or 'none'}, "
            f"success {ev.success}")


class SmallContextClient(OllamaClient):
    """OllamaClient that also tells Ollama how big its context window is.

    The frozen client sends only `temperature`; this one adds `num_ctx`, so a
    prompt larger than the window can be provoked on purpose.
    """

    def __init__(self, num_ctx, host=HOST):
        super().__init__(host=host)
        self.num_ctx = num_ctx

    def chat(self, model, messages, temperature=0.7):
        t0 = time.monotonic()
        resp = requests.post(f"{self.host}/api/chat", json={
            "model": model, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_ctx": self.num_ctx},
        }, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        return ChatResponse(
            text=data["message"]["content"].strip(),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            seconds=time.monotonic() - t0,
        )


# ------------------------------------------------------- offline (no model)
def case_runaway_loop():
    """A goal that never arrives. Only the Budget can end the loop."""
    client = MockClient()
    budget = Budget(max_turns=50, max_tokens=10**9, max_seconds=60)
    engine = DialogueEngine([AGENT_A, AGENT_B], client, budget,
                            goal_reached=lambda transcript: False)
    engine.run()
    path = engine.save(f"{OUT}/runaway_loop.json", meta={"case": "runaway_loop"})
    ok = budget.stop_reason == "max_turns" and len(engine.transcript) == 50
    return ok, (f"stopped by {budget.stop_reason} after {len(engine.transcript)} "
                f"turns; {client._i} model calls"), path


def case_plan_retry_recovers():
    """First plan reply is prose; the one corrective retry fixes it."""
    client = MockClient(replies=[PROSE_PLAN, GOOD_PLAN])
    result = finalise(AGENT_A, INCIDENT.seed_entries(), client, fresh_budget(), INCIDENT)
    path = save_json("plan_retry_recovers", result.as_dict())
    ok = (result.stop_reason == "accepted" and result.retries == 1
          and result.attempt_errors[0] is not None and result.evaluation.success)
    return ok, (f"attempt 1 rejected ({result.attempt_errors[0]}), attempt 2 "
                f"{result.stop_reason}; {plan_summary(result.evaluation)}"), path


def case_plan_retry_gives_up():
    """Both plan replies are prose. Recorded as a parse failure, never guessed."""
    client = MockClient(replies=[PROSE_PLAN, "The plan is as I described above."])
    result = finalise(AGENT_A, INCIDENT.seed_entries(), client, fresh_budget(), INCIDENT)
    path = save_json("plan_retry_gives_up", result.as_dict())
    ev = result.evaluation
    ok = (result.stop_reason == "parse_failed" and client._i == MAX_ATTEMPTS
          and not ev.parsed and not ev.success)
    return ok, (f"{client._i} calls, stop_reason {result.stop_reason}, "
                f"{plan_summary(ev)}"), path


def case_plan_no_budget():
    """The finalisation budget is already spent: no call is made at all."""
    client = MockClient(replies=[GOOD_PLAN])
    spent = Budget(max_turns=0, max_tokens=100_000, max_seconds=300)
    result = finalise(AGENT_A, INCIDENT.seed_entries(), client, spent, INCIDENT)
    path = save_json("plan_no_budget", result.as_dict())
    ok = (client._i == 0 and result.stop_reason == "budget_exhausted"
          and not result.evaluation.parsed)
    return ok, (f"{client._i} calls, stop_reason {result.stop_reason}, "
                f"{plan_summary(result.evaluation)}"), path


def case_judge_garbage():
    """The judge answers in prose, then with plausible but invalid JSON."""
    client = MockClient(replies=[
        "I'd give this plan a solid 4 out of 5!",
        '{"score": 7, "success": "yes", "reason": "great plan"}',
    ])
    verdict = judge(client, INCIDENT.seed_entries(), GOOD_PLAN, fresh_budget())
    primary = evaluate(GOOD_PLAN, INCIDENT)
    path = save_json("judge_garbage", {"judge": verdict.as_dict(),
                                       "primary_evaluation": primary.as_dict()})
    ok = verdict.score is None and verdict.stop_reason == "parse_failed" and primary.success
    return ok, (f"judge errors {verdict.attempt_errors}, score {verdict.score}; "
                f"deterministic verdict unaffected: success {primary.success}"), path


def case_ollama_down():
    """No model server. The run must fail loudly and write no result."""
    client = OllamaClient(host="http://localhost:9")   # nothing listens here
    engine = DialogueEngine([AGENT_A, AGENT_B], client,
                            Budget(max_turns=2, max_tokens=100_000, max_seconds=60))
    engine.transcript = INCIDENT.seed_entries()
    try:
        engine.run()
    except RuntimeError as exc:
        message = str(exc).splitlines()[0]
        path = save_json("ollama_down", {"raised": "RuntimeError", "message": str(exc),
                                         "turns_generated": len(engine.transcript) - 6})
        return True, f"RuntimeError: {message} (no result row written)", path
    return False, "no error raised", None


def case_guard_config_diff():
    """Two conditions differ in a second setting. The experiment must refuse."""
    configs = [experiment.condition_config(w) for w in experiment.WINDOWS]
    configs[1] = {**configs[1], "agent_b_temperature": 0.7}
    try:
        experiment.assert_one_variable(configs)
    except AssertionError as exc:
        path = save_json("guard_config_diff", {"refused": str(exc)})
        return True, f"refused: {exc}", path
    return False, "experiment would have started", None


def case_guard_inert():
    """Windows bigger than the dialogue: every condition sees the same thing."""
    try:
        experiment.assert_not_inert([20, 30, 40], len(INCIDENT.seed_dialogue) + 10)
    except AssertionError as exc:
        path = save_json("guard_inert", {"refused": str(exc)})
        return True, "refused: conditions are INERT at 16 messages", path
    return False, "experiment would have started", None


# ------------------------------------------------------- real model (Ollama)
def token_cap(name, window):
    """max_tokens=2500. The Budget counts prompt + completion tokens per call."""
    budget = Budget(max_turns=10, max_tokens=2500, max_seconds=600)
    r = run_dialogue(name, OllamaClient(host=HOST), window=window,
                     dialogue_budget=budget, broke="max_tokens=2500")
    ok = r["budget"].stop_reason == "max_tokens"
    return ok, (f"stopped by {r['budget'].stop_reason} after {len(r['generated'])} "
                f"of 10 turns ({r['budget'].tokens} tokens); a plan was still "
                f"requested on its own budget: {plan_summary(r['ev'])}"), r["path"]


def case_token_cap_full():
    return token_cap("token_cap_full", None)


def case_token_cap_recency4():
    return token_cap("token_cap_recency4", 4)


def case_wall_clock_cap():
    """max_seconds=3. The Budget is checked BETWEEN calls, not during one."""
    budget = Budget(max_turns=10, max_tokens=100_000, max_seconds=3)
    r = run_dialogue("wall_clock_cap", OllamaClient(host=HOST),
                     dialogue_budget=budget, broke="max_seconds=3")
    ok = r["budget"].stop_reason == "max_seconds"
    return ok, (f"stopped by {r['budget'].stop_reason} after {len(r['generated'])} "
                f"turns at {r['elapsed']}s: the cap overran by "
                f"{r['elapsed'] - 3:.1f}s because a call in flight is never "
                f"interrupted"), r["path"]


def case_window_zero():
    """recency-0: every call sees only the system prompt. No memory at all."""
    r = run_dialogue("window_zero", OllamaClient(host=HOST), window=0,
                     broke="window=0")
    return "finding", (f"{len(r['generated'])} turns with no history; "
                       f"{plan_summary(r['ev'])}; actions {r['ev'].actions}"), r["path"]


def case_context_overflow():
    """Full history, but Ollama is told the window is only 512 tokens."""
    r = run_dialogue("context_overflow", SmallContextClient(num_ctx=512),
                     broke="num_ctx=512 with full history")
    seen = [e.prompt_tokens for e in r["generated"]]
    plan_seen = r["result"].attempts[0].prompt_tokens
    return "finding", (f"prompt tokens Ollama reports per turn {seen}, final plan "
                       f"{plan_seen}: capped near 512 with no error. The engine "
                       f"believes it sent full history; {plan_summary(r['ev'])}"), r["path"]


def case_rules_in_system_prompt():
    """Design rule 1 broken: the seed rules are copied into both system prompts."""
    rules = "\n".join(f"- {text}" for _, text in INCIDENT.seed_dialogue[1:])
    extra = f"\n\nConstraints already established for this incident:\n{rules}"
    agents = [replace(AGENT_A, system_prompt=AGENT_A.system_prompt + extra),
              replace(AGENT_B, system_prompt=AGENT_B.system_prompt + extra)]
    r = run_dialogue("rules_in_system_prompt", OllamaClient(host=HOST), window=4,
                     agents=agents, broke="rules in system prompt, window=4")
    return "finding", (f"window 4 but every rule always visible: "
                       f"{plan_summary(r['ev'])}; actions {r['ev'].actions}"), r["path"]


CASES = [
    # name, needs_model, what was broken, what should happen
    ("runaway_loop", False, "goal never reached, 50-turn cap",
     "Budget stops the loop at max_turns"),
    ("plan_retry_recovers", False, "first plan reply is prose",
     "one corrective retry, then accepted"),
    ("plan_retry_gives_up", False, "both plan replies are prose",
     "exactly 2 calls, recorded as parse failure, success False"),
    ("plan_no_budget", False, "finalisation budget already spent",
     "no model call, recorded as budget_exhausted"),
    ("judge_garbage", False, "judge returns prose, then out-of-range JSON",
     "judge verdict empty; deterministic verdict unaffected"),
    ("ollama_down", False, "model server unreachable",
     "clear RuntimeError, no result row"),
    ("guard_config_diff", False, "conditions differ in two settings",
     "experiment refuses to start"),
    ("guard_inert", False, "windows larger than the dialogue",
     "experiment refuses to start"),
    ("token_cap_full", True, "max_tokens=2500, full history",
     "stops early on max_tokens; plan still requested"),
    ("token_cap_recency4", True, "max_tokens=2500, window 4",
     "stops on max_tokens, but later than full history"),
    ("wall_clock_cap", True, "max_seconds=3",
     "stops on max_seconds"),
    ("window_zero", True, "window=0: no history at all",
     "(probe) how much does the plan depend on context?"),
    ("context_overflow", True, "num_ctx=512 with full history",
     "(probe) what does Ollama do with a prompt that does not fit?"),
    ("rules_in_system_prompt", True, "rules moved into system prompts",
     "(probe) do the rules hold when they can never be forgotten?"),
]


def main(offline, only):
    os.makedirs(RESULTS, exist_ok=True)
    path = f"{RESULTS}/summary.csv"
    rows = {}
    if os.path.exists(path):       # keep earlier rows when re-running one case
        with open(path, newline="", encoding="utf-8") as fh:
            rows = {r["case"]: r for r in csv.DictReader(fh)}
    for name, needs_model, broke, expected in CASES:
        if (offline and needs_model) or (only and name != only):
            continue
        t0 = time.monotonic()
        as_designed, observed, evidence = globals()[f"case_{name}"]()
        rows[name] = {"case": name, "needs_model": needs_model, "broke": broke,
                      "expected": expected, "observed": observed,
                      "as_designed": as_designed, "evidence": evidence or "",
                      "seconds": round(time.monotonic() - t0, 1)}
        print(f"[{'OK' if as_designed is True else as_designed}] {name}: {observed}")
    ordered = [rows[n] for n, *_ in CASES if n in rows]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ordered[0].keys()))
        w.writeheader()
        w.writerows(ordered)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true", help="skip cases that need Ollama")
    p.add_argument("--case", default=None, help="run one case by name")
    a = p.parse_args()
    main(offline=a.offline, only=a.case)
