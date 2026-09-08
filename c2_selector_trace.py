"""c2_selector_trace.py: does a stale restatement defeat supersession? NO.

ZERO model calls, zero embedding inference. Run: python c2_selector_trace.py

This script IS the evidence that retired C2 (docs/NEXT-RESEARCH-SCREEN.md).

Exercises the REAL selector (context.RecencyBudget, context.BM25Budget) on an
authored history containing a proposal, its authoritative retraction, and a later
restatement of the obsolete proposal that explicitly does NOT authorise a new
decision.

Three conditions at the SAME position, to separate the mechanisms:
  ECHO     stale restatement of the obsolete proposal
  NEUTRAL  equal-word-count message, no relation to the proposal
  ABSENT   no message at that position at all

ECHO vs NEUTRAL  -> semantic/content effect, position and length held fixed.
NEUTRAL vs ABSENT-> ordinary displacement from adding any text.
"""
from context import BM25Budget, RecencyBudget, query_for_turn, words

SYS = {"role": "system", "content": "You are the Operations Lead."}

PROPOSAL = "I would add SNAPSHOT_STORE to the recovery plan for this incident."
RETRACT = ("Retracting that: SNAPSHOT_STORE is revoked by the change board and "
           "must not appear in the plan.")
# Restates the obsolete proposal. Explicitly NOT a new authorisation.
ECHO = ("Earlier in this thread SNAPSHOT_STORE was put forward for the recovery "
        "plan; noting it only as history, not as a new decision.")
FILL = ["The status page still shows a partial outage for the region.",
        "Customer reports are arriving through the support queue.",
        "The on-call engineer has acknowledged the incident page."]
CURRENT = "Given all of the above, what should the plan contain?"


def neutral_matching(target):
    """Neutral filler padded to the same word count as `target`."""
    base = ("Unrelated note: the cafeteria badge reader was replaced this morning "
            "and facilities logged the work order for the building manager.")
    w = words(base)
    need = words(target)
    toks = base.split()
    while w < need:
        toks.append("additionally")
        w += 1
    return " ".join(toks[:len(toks)]) if w == need else " ".join(toks[:need])


def history(variant, echo_role="assistant"):
    """[system, proposal, fill, retraction, fill, fill, <variant>, current]."""
    msgs = [SYS,
            {"role": "assistant", "content": PROPOSAL},
            {"role": "user", "content": FILL[0]},
            {"role": "user", "content": RETRACT},
            {"role": "assistant", "content": FILL[1]},
            {"role": "user", "content": FILL[2]}]
    if variant == "echo":
        msgs.append({"role": echo_role, "content": ECHO})
    elif variant == "neutral":
        msgs.append({"role": echo_role, "content": neutral_matching(ECHO)})
    msgs.append({"role": "user", "content": CURRENT})
    return msgs


def contains(sel, needle):
    return any(needle in m["content"] for m in sel)


def report(policy, label, variant, echo_role="assistant"):
    msgs = history(variant, echo_role)
    sel = policy.select(msgs)
    last = getattr(policy, "_last", {})
    kept_prop = contains(sel, "I would add SNAPSHOT_STORE")
    kept_retr = contains(sel, "is revoked by the change board")
    kept_echo = contains(sel, "put forward for the recovery")
    print(f"  {label:14} {variant:8} role={echo_role:9} "
          f"prop={'Y' if kept_prop else '.'} retr={'Y' if kept_retr else '.'} "
          f"echo={'Y' if kept_echo else '.'}  "
          f"sel={last.get('n_selected')}/{last.get('n_candidates')} "
          f"w_hist={last.get('words_history')} ids={last.get('selected_ids')}")
    return kept_prop, kept_retr, kept_echo


print("=== word counts ===")
print(f"  proposal {words(PROPOSAL)}  retraction {words(RETRACT)}  "
      f"echo {words(ECHO)}  neutral {words(neutral_matching(ECHO))}  "
      f"current {words(CURRENT)}")
print(f"  derived query: {query_for_turn(history('echo'))!r}\n")

for W in (20, 30, 40, 50, 60):
    print(f"=== budget W={W} words ===")
    for variant in ("echo", "neutral", "absent"):
        report(RecencyBudget(W), "recency", variant)
    for variant in ("echo", "neutral", "absent"):
        report(BM25Budget(W), "bm25", variant)
    print()

print("=== source attribution, content and position held fixed (W=40) ===")
for role in ("assistant", "user"):
    report(RecencyBudget(40), "recency", "echo", role)
    report(BM25Budget(40), "bm25", "echo", role)
