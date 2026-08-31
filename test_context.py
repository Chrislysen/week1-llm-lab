"""Self-check for the context-selection policies.

Run:  python test_context.py
"""
from context import (FullHistory, OracleBudget, RandomBudget, RecencyBudget,
                     RecencyWindow, make_policy, preflight,
                     query_for_finalisation, query_for_turn, words)

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

assert [(c["available"], c["kept"], c["dropped"]) for c in p.calls] == [
    (14, 4, 10), (6, 4, 2), (2, 2, 0),
], p.calls
# Every call also records the budget unit, so spend is auditable per call.
assert [c["words_kept"] for c in p.calls] == [4, 4, 2], p.calls
assert [c["words_available"] for c in p.calls] == [14, 6, 2], p.calls

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

# -- Word-budgeted policies (the research extension) ---------------------

def sized(specs):
    """A rendered view whose dialogue messages have the given word counts."""
    return [SYS] + [
        {"role": "user", "content": " ".join(f"w{i}_{k}" for k in range(n))}
        for i, n in enumerate(specs)
    ]


SIZES = [10, 20, 30, 40, 50, 60]          # 210 words total, 6 messages
POOL = sized(SIZES)

# Recency: newest first, skipping anything that would overflow, chronological
# on the way out. At W=100 over sizes [10,20,30,40,50,60]:
#   w5(60) fits -> 60;  w4(50) would make 110 -> SKIPPED;  w3(40) -> 100 exactly.
# The skip is the documented rule: stopping at the first non-fit would leave
# this arm at 60/100 and break budget parity with the other arms.
out = RecencyBudget(100)(list(POOL))
assert out[0] == SYS
kept = [m["content"].split()[0].split("_")[0] for m in out[1:]]
assert kept == ["w3", "w5"], kept

picked = RecencyBudget(100).select(POOL)[1:]
assert sum(words(m["content"]) for m in picked) == 100, "should fill the budget"
# Chronological order is restored regardless of pick order.
idx = [POOL.index(m) for m in picked]
assert idx == sorted(idx), "selection must be restored to chronological order"

# Whole messages only -- nothing is ever truncated or rewritten.
for m in picked:
    assert m in POOL, "a budgeted policy must not modify message content"

# POOL[1..6] have 10, 20, 30, 40, 50, 60 words. Put the "planted" messages at
# the two OLDEST positions -- the ones recency reaches last -- so the oracle and
# recency genuinely diverge.
SOURCES = [POOL[1]["content"], POOL[2]["content"]]      # 10 + 20 = 30 words

# The budget is never exceeded, at any W, for any policy.
for W in range(0, 260, 10):
    for pol in (RecencyBudget(W), RandomBudget(W, seed=1),
                OracleBudget(W, SOURCES)):
        sel = pol.select(POOL)
        assert sel[0] == SYS, f"{pol.label} dropped the system prompt"
        spend = sum(words(m["content"]) for m in sel[1:])
        assert spend <= W, f"{pol.label} overspent: {spend} > {W}"
        assert all(m in POOL for m in sel[1:]), f"{pol.label} injected content"
        i = [POOL.index(m) for m in sel[1:]]
        assert i == sorted(i), f"{pol.label} broke chronological order"

# W = 0 keeps nothing but the system prompt.
assert RecencyBudget(0).select(POOL) == [SYS]

# Oracle takes the constraint-bearing messages FIRST. At W=30 the two sources
# (10 + 20) exactly fill the budget and nothing else fits.
sel = OracleBudget(30, SOURCES).select(POOL)
assert [m["content"] for m in sel[1:]] == SOURCES, sel

# Recency at the SAME budget gets neither of them: it spends 30 on the newest
# message that fits. This is the whole point of the pilot in miniature.
rec = RecencyBudget(30).select(POOL)
assert not any(m["content"] in SOURCES for m in rec[1:]), rec

# With more room the oracle keeps both sources and spends the rest on recency.
sel = OracleBudget(90, SOURCES).select(POOL)
got = [m["content"] for m in sel[1:]]
assert all(s in got for s in SOURCES), "oracle must not drop a source message"
assert len(got) > len(SOURCES), "oracle should spend leftover budget"
assert sum(words(m["content"]) for m in sel[1:]) <= 90

# Oracle may SELECT using hidden knowledge but must never INJECT. Its output is
# always a subset of its input -- the property that makes it a legitimate
# upper bound rather than a cheat.
for W in (0, 45, 90, 150, 250):
    sel = OracleBudget(W, SOURCES).select(POOL)
    assert all(m in POOL for m in sel), "oracle injected content not in the dialogue"

# Random is seeded and reproducible; different seeds can differ.
a = RandomBudget(100, seed=7).select(POOL)
b = RandomBudget(100, seed=7).select(POOL)
assert a == b, "random must be reproducible from its seed"
seeds = {tuple(m["content"] for m in RandomBudget(100, seed=s).select(POOL))
         for s in range(12)}
assert len(seeds) > 1, "random should vary across seeds"

assert RecencyBudget(250).config() == {"max_words": 250}
assert RandomBudget(250, seed=3).config()["seed"] == 3
assert OracleBudget(250, SOURCES).config()["n_source_texts"] == 2
assert make_policy(RecencyBudget(250)).label == "recency-250"

print("budgeted policies:   OK")

# -- The frozen query definition -----------------------------------------

view = [SYS,
        {"role": "assistant", "content": "I will isolate the node."},
        {"role": "user", "content": "Back up before you restart."}]

assert query_for_turn(view) == "Back up before you restart."
assert query_for_turn([SYS]) == ""

q = query_for_finalisation(view, "Write the final plan as JSON.")
assert q.startswith("Write the final plan as JSON.")
assert "Back up before you restart." in q
assert query_for_finalisation([SYS], "INSTR") == "INSTR"

# The query is built only from what the agent can already see. No constraint
# ids, no evaluator state, no hidden key.
for leak in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "constraint", "oracle"):
    assert leak not in q, f"query leaked {leak!r}"

print("frozen query:        OK")

# -- Preflight regression: identical content fingerprints identically ----
#
# pilot.py originally fed preflight a stand-in transcript whose messages were
# ALL the same 40-word string. Any selection of six of them was byte-identical,
# so preflight reported inert==True for arms that are plainly not inert. The
# behaviour below is correct -- preflight compares selected CONTENT -- so the
# defect was in the caller's fixture. Pinned here so it cannot come back.

same = [SYS] + [{"role": "user", "content": "w " * 20} for _ in range(12)]
budgeted = [RecencyBudget(60), RandomBudget(60, seed=1),
            OracleBudget(60, ["w " * 20])]
assert preflight(same, budgeted)["inert"] is True, (
    "identical message content SHOULD fingerprint identically -- this is the "
    "caller's fixture bug, not a preflight bug")

distinct = [SYS] + [
    {"role": "user", "content": " ".join(f"m{i}w{k}" for k in range(20))}
    for i in range(12)
]
report = preflight(distinct, [RecencyBudget(60), RandomBudget(60, seed=1),
                              OracleBudget(60, [distinct[1]["content"]])])
assert report["inert"] is False, report
assert report["distinct_contexts"] == 3, report

print("preflight fixture:   OK")
print("\nAll checks passed.")
