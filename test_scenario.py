"""Self-check for the incident scenario and the deterministic evaluator.

Run:  python test_scenario.py

Same style as test_engine.py: plain asserts, no test framework, prints what
passed. Several of these are falsification tests -- they plant a real defect and
require the checker to go red. A checker that cannot fail is not a checker.
"""
import json

from evaluate import evaluate, parse_plan
from scenario import ACTIONS, AGENT_A, AGENT_B, INCIDENT

S = INCIDENT


def plan_json(actions, ready=True):
    return json.dumps({"actions": list(actions), "ready": ready})


GOOD = [
    "ISOLATE_NODE",
    "RUN_DIAGNOSTICS",
    "RUN_BACKUP",
    "FAILOVER_API",
    "RESTART_DB",
    "RESTORE_TRAFFIC",
]

# -- Scenario integrity --------------------------------------------------

# Turn parity: the engine picks the speaker with len(transcript) % len(agents),
# so an even-length seed leaves the Operations Lead to speak next.
assert len(S.seed_dialogue) % 2 == 0, "seed length must be even"
assert S.seed_dialogue[0][0] == AGENT_A.name, "Operations Lead should open"

entries = S.seed_entries()
assert len(entries) == len(S.seed_dialogue)
assert [e.turn_index for e in entries] == list(range(len(entries)))

# Every constraint must actually be traceable to the sentence that conveys it.
# This is what stops the hidden key and the visible dialogue drifting apart.
for c in S.constraints:
    speaker, text = S.seed_dialogue[c.stated_at_turn]
    assert c.natural and c.natural in text, (
        f"{c.id}: natural text {c.natural!r} not found in seed turn "
        f"{c.stated_at_turn}"
    )
    assert c.a in ACTIONS, f"{c.id}: unknown action {c.a}"
    if c.kind == "before":
        assert c.b in ACTIONS, f"{c.id}: unknown action {c.b}"

# DESIGN RULE 1: constraints live in the dialogue, never in a system prompt.
# Anything in a system prompt survives every context policy by construction, so
# a constraint placed there could never be forgotten and the later context
# experiment would measure nothing.
for agent in (AGENT_A, AGENT_B):
    for c in S.constraints:
        assert c.natural not in agent.system_prompt, (
            f"{c.id} leaked into {agent.name}'s system prompt"
        )
    for action in ACTIONS:
        assert action not in agent.system_prompt, (
            f"action vocabulary leaked into {agent.name}'s system prompt"
        )

assert AGENT_A.system_prompt != AGENT_B.system_prompt, "personas must differ"

print("scenario integrity:  OK")

# -- Known-good plan passes ----------------------------------------------

ev = evaluate(plan_json(GOOD), S)
assert ev.parsed, ev.parse_error
assert ev.violated == [], f"expected no violations, got {ev.violated}"
assert ev.violations == 0
assert ev.constraint_recall == 1.0
assert ev.unknown_actions == []
assert ev.success

# The minimum plan that satisfies everything: diagnostics are optional.
minimal = ["ISOLATE_NODE", "RUN_BACKUP", "FAILOVER_API", "RESTART_DB", "RESTORE_TRAFFIC"]
assert evaluate(plan_json(minimal), S).success

print("known-good plan:     OK")

# -- Known-bad ordering fails --------------------------------------------

# Backup after the restart violates C4 and nothing else.
bad_order = [
    "ISOLATE_NODE",
    "RUN_DIAGNOSTICS",
    "FAILOVER_API",
    "RESTART_DB",
    "RUN_BACKUP",
    "RESTORE_TRAFFIC",
]
ev = evaluate(plan_json(bad_order), S)
assert ev.parsed
assert ev.violated == ["C4"], ev.violated
assert ev.violations == 1
assert not ev.success

# Diagnostics before isolating the node violates C2.
ev = evaluate(plan_json(["RUN_DIAGNOSTICS"] + GOOD[:1] + GOOD[2:]), S)
assert "C2" in ev.violated, ev.violated

# Traffic restored before the database is back violates C6.
ev = evaluate(
    plan_json(["ISOLATE_NODE", "RUN_BACKUP", "FAILOVER_API", "RESTORE_TRAFFIC", "RESTART_DB"]),
    S,
)
assert "C6" in ev.violated, ev.violated

print("bad ordering:        OK")

# -- Missing required action fails ---------------------------------------

# Dropping the backup breaks C3 (required) and C4 (its ordering rule, which is
# no longer vacuous because RESTART_DB is still present).
no_backup = ["ISOLATE_NODE", "RUN_DIAGNOSTICS", "FAILOVER_API", "RESTART_DB", "RESTORE_TRAFFIC"]
ev = evaluate(plan_json(no_backup), S)
assert sorted(ev.violated) == ["C3", "C4"], ev.violated
assert not ev.success

# The lazy plan C7 exists to stop: propose almost nothing, and every ordering
# rule is vacuously satisfied.
ev = evaluate(plan_json(["ISOLATE_NODE", "RUN_BACKUP"]), S)
assert "C7" in ev.violated, ev.violated
assert not ev.success

# An empty plan must fail, not score vacuously perfectly.
ev = evaluate(plan_json([]), S)
assert not ev.success and ev.violations >= 3, ev.as_dict()

print("missing required:    OK")

# -- Malformed JSON is caught --------------------------------------------

for bad, why in [
    ("", "empty output"),
    ("I'll restart the database first.", "prose with no JSON"),
    ('{"actions": ["RUN_BACKUP"], "ready": true', "unbalanced brace"),
    ('{"actions": ["RUN_BACKUP"] "ready": true}', "missing comma"),
    ('{"ready": true}', "missing actions"),
    ('{"actions": "RUN_BACKUP", "ready": true}', "actions not a list"),
    ('{"actions": [1, 2], "ready": true}', "actions not strings"),
    ('{"actions": ["RUN_BACKUP"]}', "missing ready"),
    ('{"actions": ["RUN_BACKUP"], "ready": "yes"}', "ready not a boolean"),
    ('["RUN_BACKUP"]', "top level not an object"),
]:
    ev = evaluate(bad, S)
    assert not ev.parsed, f"should have failed to parse ({why}): {bad!r}"
    assert ev.parse_error, why
    assert not ev.success
    assert ev.violations == 0, "an unparsed plan has no constraint verdict"

print("malformed JSON:      OK")

# -- Parsing is forgiving about wrapping, strict about content -----------

wrapped = f"Here is the plan:\n```json\n{plan_json(GOOD)}\n```\nLet me know."
ev = evaluate(wrapped, S)
assert ev.parsed and ev.success, "fenced JSON should still parse"

prose = f"Sure. {plan_json(GOOD)} That respects everything we agreed."
assert evaluate(prose, S).success, "JSON embedded in prose should still parse"

# A brace inside a string must not confuse the scanner.
plan, err = parse_plan('{"actions": [], "ready": false, "note": "a } brace"}')
assert plan is not None and err is None, err

print("wrapped JSON:        OK")

# -- Invented actions are a diagnostic, not a task failure ----------------

# Task success is: parsed AND ready AND zero constraint violations.
# An invented action name is recorded, but does not by itself fail the task.
ev = evaluate(plan_json(GOOD + ["REBOOT_EVERYTHING"]), S)
assert ev.parsed
assert ev.unknown_actions == ["REBOOT_EVERYTHING"], ev.unknown_actions
assert ev.violated == []
assert ev.constraint_recall == 1.0
assert ev.success, "invented actions are a diagnostic, not a task failure"

# Several invented names, still a success, all of them recorded.
noisy = ["NOTIFY_OPS"] + GOOD + ["MONITOR_CLUSTER", "TEST_API"]
ev = evaluate(plan_json(noisy), S)
assert ev.success
assert ev.unknown_actions == ["NOTIFY_OPS", "MONITOR_CLUSTER", "TEST_API"]

# But a constraint violation still fails, whether or not names were invented.
bad_with_noise = ["NOTIFY_OPS", "ISOLATE_NODE", "RESTART_DB", "RUN_BACKUP",
                  "FAILOVER_API", "RESTORE_TRAFFIC"]
ev = evaluate(plan_json(bad_with_noise), S)
assert ev.parsed
assert ev.unknown_actions == ["NOTIFY_OPS"]
assert ev.violated, "a real ordering violation must still fail"
assert not ev.success

# And malformed output fails regardless.
ev = evaluate("no json at all", S)
assert not ev.parsed and not ev.success

# `ready: false` is the agent declining to sign off. Not a success.
ev = evaluate(plan_json(GOOD, ready=False), S)
assert ev.parsed and ev.violations == 0
assert not ev.success, "a plan not declared ready is not a success"

print("unknown actions:     OK")
print("\nAll checks passed.")
