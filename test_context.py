"""Self-check for the context-selection policies.

Run:  python test_context.py
"""
from context import FullHistory, RecencyWindow, make_policy, preflight

SYS = {"role": "system", "content": "You are the Operations Lead."}


def transcript(n):
    """A rendered message list: system prompt + n alternating dialogue turns."""
    return [SYS] + [
        {"role": "assistant" if i % 2 == 0 else "user", "content": f"m{i}"}
        for i in range(n)
    ]


MSGS = transcript(14)

# -- The system prompt is never dropped ----------------------------------

for policy in (FullHistory(), RecencyWindow(0), RecencyWindow(1), RecencyWindow(99)):
    out = policy(list(MSGS))
    assert out[0] == SYS, f"{policy.label} dropped or moved the system prompt"

# A list that does not start with a system message is a programming error,
# not something to silently paper over.
for policy in (FullHistory(), RecencyWindow(4)):
    try:
        policy([{"role": "user", "content": "hi"}])
    except ValueError:
        pass
    else:
        raise AssertionError(f"{policy.label} accepted a list with no system prompt")

print("system prompt kept:  OK")

# -- Recency keeps the most recent N, in order ---------------------------

out = RecencyWindow(4)(list(MSGS))
assert [m["content"] for m in out] == ["You are the Operations Lead.",
                                       "m10", "m11", "m12", "m13"], out
assert len(out) == 5

out = RecencyWindow(8)(list(MSGS))
assert [m["content"] for m in out[1:]] == [f"m{i}" for i in range(6, 14)]

out = RecencyWindow(12)(list(MSGS))
assert [m["content"] for m in out[1:]] == [f"m{i}" for i in range(2, 14)]

# Roles are preserved exactly as rendered; the policy never rewrites them.
assert all(m["role"] in ("assistant", "user") for m in out[1:])

# N larger than the transcript keeps everything.
assert RecencyWindow(99)(list(MSGS)) == MSGS

# N = 0 keeps nothing. This is the one that bites: rest[-0:] is the WHOLE
# list in Python, so a naive slice would silently keep everything.
out = RecencyWindow(0)(list(MSGS))
assert out == [SYS], f"max_messages=0 must keep only the system prompt, got {out}"

try:
    RecencyWindow(-1)
except ValueError:
    pass
else:
    raise AssertionError("negative window should be rejected")

# Full history is the identity.
assert FullHistory()(list(MSGS)) == MSGS

print("recency window:      OK")

# -- Policies record what they did ---------------------------------------

p = RecencyWindow(4)
p(list(transcript(14)))
p(list(transcript(6)))
p(list(transcript(2)))

assert p.calls == [
    {"available": 14, "kept": 4, "dropped": 10},
    {"available": 6, "kept": 4, "dropped": 2},
    {"available": 2, "kept": 2, "dropped": 0},
], p.calls

d = p.as_dict()
assert d["policy"] == "recency"
assert d["label"] == "recency-4"
assert d["config"] == {"max_messages": 4}
assert d["totals"] == {
    "calls": 3, "messages_available": 22, "messages_kept": 10, "messages_dropped": 12,
}

assert make_policy(8).config() == {"max_messages": 8}
assert make_policy(None).name == "full"
assert make_policy("full").name == "full"

print("policy records:      OK")

# -- Preflight: are the three configured windows actually distinct? ------

WINDOWS = [4, 8, 12]


def windows():
    return [RecencyWindow(n) for n in WINDOWS]


# Long transcript: all three windows must see different things.
report = preflight(transcript(14), windows())
assert report["inert"] is False
assert report["distinct_contexts"] == 3
assert report["identical_pairs"] == [], report["identical_pairs"]
assert report["kept"] == {"recency-4": 4, "recency-8": 8, "recency-12": 12}

# Short transcript: every window keeps everything, so the comparison is inert
# and the preflight must say so rather than let the run proceed.
report = preflight(transcript(3), windows())
assert report["inert"] is True
assert report["distinct_contexts"] == 1
assert len(report["identical_pairs"]) == 3

# Partially inert: 8 and 12 collapse together at 8 messages, 4 still differs.
report = preflight(transcript(8), windows())
assert report["inert"] is False
assert report["identical_pairs"] == [("recency-8", "recency-12")]
assert report["distinct_contexts"] == 2

# The boundary: 13 messages is the shortest transcript on which all three
# windows differ AND the widest still drops something.
report = preflight(transcript(13), windows())
assert report["distinct_contexts"] == 3
assert report["kept"]["recency-12"] == 12 < 13

# Preflight must not pollute a policy's own call log.
ps = windows()
preflight(transcript(14), ps)
assert all(p.calls == [] for p in ps), "preflight recorded a call"

print("preflight:           OK")
print("\nAll checks passed.")
