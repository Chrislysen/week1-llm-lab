"""Self-check for the finalisation step (final plan + bounded retry).

Run:  python test_finalise.py

Same plain-assert style as the other two suites.
"""
import json
import os
import tempfile

from budget import Budget
from engine import DialogueEngine, Entry
from finalise import MAX_ATTEMPTS, finalise
from llm_client import ChatResponse
from scenario import AGENT_A, AGENT_B, INCIDENT

S = INCIDENT

GOOD_PLAN = json.dumps({
    "actions": ["ISOLATE_NODE", "RUN_BACKUP", "FAILOVER_API",
                "RESTART_DB", "RESTORE_TRAFFIC"],
    "ready": True,
})


class ScriptedClient:
    """Returns queued replies in order and records every call it received.

    Exists so a test can control exactly what the 'model' says. `calls` is what
    proves no model call happened without being logged.
    """

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []

    def chat(self, model, messages, temperature=0.7):
        self.calls.append(messages)
        text = self._replies.pop(0) if self._replies else "(script exhausted)"
        return ChatResponse(
            text=text,
            prompt_tokens=sum(len(m["content"].split()) for m in messages),
            completion_tokens=max(1, len(text.split())),
            seconds=0.01,
        )


def fresh_budget(max_turns=MAX_ATTEMPTS):
    return Budget(max_turns=max_turns, max_tokens=100_000, max_seconds=300)


TRANSCRIPT = S.seed_entries()

# -- Valid first-attempt JSON --------------------------------------------

client = ScriptedClient([GOOD_PLAN])
r = finalise(AGENT_A, TRANSCRIPT, client, fresh_budget(), S)

assert r.stop_reason == "accepted", r.stop_reason
assert len(r.attempts) == 1
assert r.retries == 0
assert r.attempt_errors == [None]
assert r.evaluation.parsed and r.evaluation.success
assert r.evaluation.violations == 0
assert r.plan_text == GOOD_PLAN
# No invisible calls: one attempt logged, one call made.
assert len(client.calls) == len(r.attempts) == 1
# The agent saw the dialogue plus the instruction, and its own seeded turns
# came back as "assistant".
first_call = client.calls[0]
assert first_call[0]["role"] == "system"
assert first_call[-1]["role"] == "user"
assert any(m["role"] == "assistant" for m in first_call)

print("valid first attempt:   OK")

# -- Malformed first attempt, valid retry --------------------------------

client = ScriptedClient(["Sure, I'd restart the database first.", GOOD_PLAN])
r = finalise(AGENT_A, TRANSCRIPT, client, fresh_budget(), S)

assert r.stop_reason == "accepted", r.stop_reason
assert len(r.attempts) == 2
assert r.retries == 1
# The malformed attempt is preserved, with its reason.
assert r.attempts[0].content == "Sure, I'd restart the database first."
assert r.attempt_errors[0] == "no JSON object found"
assert r.attempt_errors[1] is None
assert r.evaluation.success
assert len(client.calls) == 2
# The retry showed the model its own bad output and the error.
retry_call = client.calls[1]
assert retry_call[-2]["role"] == "assistant"
assert retry_call[-2]["content"] == "Sure, I'd restart the database first."
assert "no JSON object found" in retry_call[-1]["content"]
# Every attempt carries measured cost.
assert all(e.prompt_tokens > 0 and e.completion_tokens > 0 for e in r.attempts)

print("retry after malformed: OK")

# -- Malformed both times ------------------------------------------------

client = ScriptedClient(["no json here", '{"actions": ["RUN_BACKUP"]'])
r = finalise(AGENT_A, TRANSCRIPT, client, fresh_budget(), S)

assert r.stop_reason == "parse_failed", r.stop_reason
assert len(r.attempts) == MAX_ATTEMPTS == 2
assert r.retries == 1
assert all(err is not None for err in r.attempt_errors)
assert not r.evaluation.parsed
assert not r.evaluation.success
assert r.evaluation.violations == 0, "an unparsed plan has no constraint verdict"
assert r.plan_text is None
# Bounded: it stopped at MAX_ATTEMPTS and did not keep going.
assert len(client.calls) == 2

# A schema-valid-JSON-but-wrong-shape reply also fails, and is retried.
client = ScriptedClient(['{"actions": ["RUN_BACKUP"]}', '{"steps": []}'])
r = finalise(AGENT_A, TRANSCRIPT, client, fresh_budget(), S)
assert r.stop_reason == "parse_failed"
assert r.attempt_errors[0] == "missing or non-boolean key: ready"

print("malformed both times:  OK")

# -- Budget exhausted ----------------------------------------------------

# One turn of budget: the first attempt runs, then the budget stops the retry.
client = ScriptedClient(["not json", GOOD_PLAN])
r = finalise(AGENT_A, TRANSCRIPT, client, fresh_budget(max_turns=1), S)

assert r.stop_reason == "budget_exhausted", r.stop_reason
assert len(r.attempts) == 1, "the retry must not have been made"
assert len(client.calls) == 1, "no model call after the budget was spent"
assert not r.evaluation.success

# No budget at all: no model call is made whatsoever.
client = ScriptedClient([GOOD_PLAN])
r = finalise(AGENT_A, TRANSCRIPT, client, fresh_budget(max_turns=0), S)
assert r.stop_reason == "budget_exhausted"
assert r.attempts == []
assert client.calls == [], "a spent budget must produce zero model calls"
assert r.evaluation is not None and not r.evaluation.parsed

print("budget exhausted:      OK")

# -- Evaluation survives save / load -------------------------------------

client = ScriptedClient(["nope", GOOD_PLAN])
budget = fresh_budget()
r = finalise(AGENT_A, TRANSCRIPT, client, budget, S)

engine = DialogueEngine([AGENT_A, AGENT_B], client, Budget(max_turns=0))
engine.transcript = list(TRANSCRIPT)

with tempfile.TemporaryDirectory() as tmp:
    path = engine.save(
        os.path.join(tmp, "run.json"),
        meta={"scenario": S.id, "finalisation": r.as_dict()},
    )
    with open(path) as f:
        loaded = json.load(f)

fin = loaded["meta"]["finalisation"]
ev = fin["evaluation"]

assert fin["stop_reason"] == "accepted"
assert fin["retries"] == 1
assert fin["totals"]["attempts"] == 2
assert ev["parsed"] is True
assert ev["success"] is True
assert ev["violated"] == []
assert ev["satisfied"] == r.evaluation.satisfied
assert ev["constraint_recall"] == round(r.evaluation.constraint_recall, 4)
assert ev["actions"] == r.evaluation.actions

# The malformed first attempt survived the round trip, with its reason.
assert len(fin["attempts"]) == 2
assert fin["attempts"][0]["content"] == "nope"
assert fin["attempts"][0]["parse_error"] == "no JSON object found"
assert fin["attempts"][1]["parse_error"] is None
# Costs survived too, so the run's real spend is reconstructable from disk.
assert fin["totals"]["prompt_tokens"] > 0
assert fin["totals"]["completion_tokens"] > 0
assert len(loaded["messages"]) == len(TRANSCRIPT)

print("save / load:           OK")
print("\nAll checks passed.")
