"""Self-check for the LLM judge and for source coverage.

Run:  python test_judge.py
"""
import json

from budget import Budget
from engine import view_for
from evaluate import source_coverage
from judge import JUDGE_NAME, judge, judge_messages, parse_judgement
from llm_client import ChatResponse
from scenario import AGENT_A, INCIDENT
from structured import MAX_ATTEMPTS

S = INCIDENT
TRANSCRIPT = S.seed_entries()
PLAN = '{"actions": ["ISOLATE_NODE", "RUN_BACKUP"], "ready": true}'

GOOD = json.dumps({"score": 4, "success": True, "reason": "Plan follows the agreed order."})


class ScriptedClient:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = []

    def chat(self, model, messages, temperature=0.7):
        self.calls.append((model, messages))
        text = self._replies.pop(0) if self._replies else "(script exhausted)"
        return ChatResponse(
            text=text,
            prompt_tokens=sum(len(m["content"].split()) for m in messages),
            completion_tokens=max(1, len(text.split())),
            seconds=0.01,
        )


def budget(max_turns=MAX_ATTEMPTS):
    return Budget(max_turns=max_turns, max_tokens=100_000, max_seconds=300)


# -- Valid output --------------------------------------------------------

client = ScriptedClient([GOOD])
j = judge(client, TRANSCRIPT, PLAN, budget())

assert j.stop_reason == "accepted", j.stop_reason
assert j.score == 4 and j.success is True
assert j.reason == "Plan follows the agreed order."
assert j.retries == 0
assert len(j.attempts) == len(client.calls) == 1, "no invisible calls"
assert j.attempts[0].speaker == JUDGE_NAME
assert j.attempts[0].prompt_tokens > 0 and j.attempts[0].completion_tokens > 0
assert j.attempts[0].seconds > 0

# Wrapped in prose or a fence still reads.
for wrapper in (f"Here you go:\n```json\n{GOOD}\n```", f"Verdict: {GOOD} Done."):
    assert judge(ScriptedClient([wrapper]), TRANSCRIPT, PLAN, budget()).score == 4

# The judge is blind: nothing in its prompt names the experimental condition.
# Note the terms are specific. Bare "policy" would false-positive, because the
# incident itself says "our policy is that we take a backup" -- that is scenario
# content, not a leaked condition label.
prompt = "\n".join(m["content"] for m in judge_messages(TRANSCRIPT, PLAN))
for leak in ("recency", "max_messages", "context policy", "full history",
             "manage_context", "truncat", "window"):
    assert leak not in prompt.lower(), f"judge prompt leaked {leak!r}"

print("valid judgement:       OK")

# -- Malformed then valid ------------------------------------------------

client = ScriptedClient(["I think it was pretty good overall.", GOOD])
j = judge(client, TRANSCRIPT, PLAN, budget())

assert j.stop_reason == "accepted"
assert j.retries == 1 and len(j.attempts) == 2
assert j.attempt_errors[0] == "no JSON object found"
assert j.attempt_errors[1] is None
assert j.score == 4
# The malformed attempt is preserved with its cost.
assert j.attempts[0].content == "I think it was pretty good overall."
assert all(e.prompt_tokens > 0 for e in j.attempts)
# The retry showed the judge its own output and the error.
_, retry = client.calls[1]
assert retry[-2]["role"] == "assistant"
assert "no JSON object found" in retry[-1]["content"]

print("retry after malformed: OK")

# -- Malformed both times ------------------------------------------------

client = ScriptedClient(["no json", '{"score": 4, "success": true'])
j = judge(client, TRANSCRIPT, PLAN, budget())

assert j.stop_reason == "parse_failed", j.stop_reason
assert len(j.attempts) == MAX_ATTEMPTS == 2
assert j.score is None and j.success is None and j.reason is None
assert all(e is not None for e in j.attempt_errors)
assert len(client.calls) == 2, "bounded: must not keep retrying"

print("malformed both times:  OK")

# -- Schema validation ---------------------------------------------------

for bad, why in [
    ("", "empty"),
    ("nothing here", "no JSON"),
    ('{"success": true, "reason": "x"}', "missing score"),
    ('{"score": "4", "success": true, "reason": "x"}', "score is a string"),
    ('{"score": true, "success": true, "reason": "x"}', "score is a bool"),
    ('{"score": 0, "success": true, "reason": "x"}', "score below range"),
    ('{"score": 6, "success": true, "reason": "x"}', "score above range"),
    ('{"score": 4, "reason": "x"}', "missing success"),
    ('{"score": 4, "success": "yes", "reason": "x"}', "success not a bool"),
    ('{"score": 4, "success": true}', "missing reason"),
    ('{"score": 4, "success": true, "reason": "   "}', "blank reason"),
    ('[1, 2, 3]', "not an object"),
]:
    value, error = parse_judgement(bad)
    assert value is None and error, f"should have been rejected ({why}): {bad!r}"

# Boundary scores are accepted.
for n in (1, 5):
    value, error = parse_judgement(json.dumps({"score": n, "success": False, "reason": "x"}))
    assert error is None and value["score"] == n

print("schema validation:     OK")

# -- Budget exhaustion ---------------------------------------------------

client = ScriptedClient(["not json", GOOD])
j = judge(client, TRANSCRIPT, PLAN, budget(max_turns=1))
assert j.stop_reason == "budget_exhausted", j.stop_reason
assert len(j.attempts) == 1 and len(client.calls) == 1
assert j.score is None

client = ScriptedClient([GOOD])
j = judge(client, TRANSCRIPT, PLAN, budget(max_turns=0))
assert j.stop_reason == "budget_exhausted"
assert j.attempts == [] and client.calls == [], "a spent budget must make zero calls"
assert j.score is None
assert j.as_dict()["totals"]["prompt_tokens"] == 0

print("budget exhausted:      OK")

# -- Source coverage -----------------------------------------------------

# Full context: every planted source message is present.
full = view_for(AGENT_A, TRANSCRIPT)
cov = source_coverage(full, S)
assert cov["source_messages_present"] == cov["source_messages_total"] == 5, cov
assert cov["coverage"] == 1.0
assert sorted(cov["constraints_with_source_present"]) == [c.id for c in S.constraints]

# Only the system prompt: nothing planted survives.
cov = source_coverage(full[:1], S)
assert cov["source_messages_present"] == 0
assert cov["coverage"] == 0.0
assert cov["constraints_with_source_present"] == []

# A window keeping the last two seed messages covers exactly their constraints.
cov = source_coverage(full[:1] + full[-2:], S)
assert cov["present_turns"] == [4, 5], cov["present_turns"]
assert cov["constraints_with_source_present"] == ["C5", "C6", "C7"], cov

# Coverage is about the ORIGINAL message, not the information. A paraphrase
# does not count, by design -- that is what makes 0/5 coverage with 7/7
# constraint recall a meaningful, reportable outcome rather than a bug.
paraphrase = [full[0], {"role": "user",
                        "content": "back up before you restart the database"}]
cov = source_coverage(paraphrase, S)
assert cov["source_messages_present"] == 0, "a paraphrase must not count as coverage"

print("source coverage:       OK")
print("\nAll checks passed.")
