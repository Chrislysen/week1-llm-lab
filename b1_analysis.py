"""b1_analysis.py: score B1 outcomes and locate behaviour. No model calls.

Outcome scoring is the declared programmatic check. The INTERMEDIATE scoring
below is a post-hoc extraction heuristic (identifier scan, first occurrence) and
is labelled EXPLORATORY wherever it is used.
"""
import json
import statistics as st
from collections import defaultdict

import lineage_bench as lb
import lineage_eval as le

SALT = "agentcom-b1"
COMBOS = [("payments", "chain"), ("robotics", "fork"), ("pharmacy", "join"),
          ("satellite", "diamond"), ("brewery", "twochain"), ("rail", "star"),
          ("payments", "diamond"), ("robotics", "twochain")]
ARMS = ("solo", "independent", "communicating")
INST = {f"{d}-{g}~{SALT}": lb.generate_instance(d, g, salt=SALT) for d, g in COMBOS}


def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def extract_order(text, actions):
    """EXPLORATORY: identifiers in order of first appearance."""
    hits = []
    for a in actions:
        i = text.find(a)
        if i >= 0:
            hits.append((i, a))
    return [a for _, a in sorted(hits)]


def score_actions(actions, inst):
    sat = [c.id for c in inst.constraints if le.obeys(c, actions)]
    vio = [c.id for c in inst.constraints if not le.obeys(c, actions)]
    return len(vio), (len(sat) / len(inst.constraints))


out = load("results/b1_outcomes.jsonl")
calls = load("results/b1_calls.jsonl")

print("=== B1 outcomes | 8 fresh instances x 3 arms x 5 calls = 120 calls ===\n")
print(f"{'instance':34} " + "  ".join(f"{a[:5]:>13}" for a in ARMS))
by = {(r["instance"], r["arm"]): r for r in out}
for iid in INST:
    row = []
    for a in ARMS:
        r = by.get((iid, a))
        row.append(f"{'OK ' if r['success'] else '   '}v={len(r['violated'])} "
                   f"r={r['constraint_recall']:.2f}" if r else " " * 13)
    print(f"{iid:34} " + "  ".join(f"{c:>13}" for c in row))

print("\n=== per-arm summary ===")
print(f"{'arm':16}{'success':>9}{'mean viol':>11}{'mean recall':>13}"
      f"{'prompt tok':>12}{'compl tok':>11}{'total tok':>11}{'seconds':>9}")
tok = defaultdict(lambda: [0, 0, 0.0])
for c in calls:
    t = tok[c["arm"]]
    t[0] += c["prompt_tokens"]; t[1] += c["completion_tokens"]; t[2] += c["seconds"]
for a in ARMS:
    rs = [r for r in out if r["arm"] == a]
    s = sum(r["success"] for r in rs)
    p, comp, sec = tok[a]
    print(f"{a:16}{s}/{len(rs):>7}{st.mean(len(r['violated']) for r in rs):>11.2f}"
          f"{st.mean(r['constraint_recall'] for r in rs):>13.3f}"
          f"{p:>12}{comp:>11}{p+comp:>11}{sec:>9.0f}")

print("\n=== position control (arm order was counterbalanced) ===")
for pos in (1, 2, 3):
    rs = [r for r in out if r["arm_position_in_process"] == pos]
    print(f"  position {pos}: success {sum(r['success'] for r in rs)}/{len(rs)}"
          f"  mean viol {st.mean(len(r['violated']) for r in rs):.2f}")

print("\n=== behaviour: plan shape ===")
for a in ARMS:
    rs = [r for r in out if r["arm"] == a]
    dup = sum(len(r["actions"]) != len(set(r["actions"])) for r in rs)
    short = sum(len(set(r["actions"])) < 6 for r in rs)
    print(f"  {a:16} duplicate-action plans {dup}/8   plans missing actions {short}/8")

print("\n=== EXPLORATORY: did a better intermediate get lost at aggregation? ===")
print("    (identifier-scan heuristic on the two refined drafts; post-hoc)")
lost = []
for r in out:
    inst = INST[r["instance"]]
    agg_v = len(r["violated"])
    best = None
    for j, t in enumerate(r["final_texts"]):
        o = extract_order(t, inst.actions)
        if len(o) < 2:
            continue
        v, rec = score_actions(o, inst)
        if best is None or v < best[0]:
            best = (v, j, o, rec)
    if best and best[0] < agg_v:
        lost.append((r["instance"], r["arm"], best[0], agg_v, best[2]))
        print(f"  {r['instance']:34} {r['arm']:14} intermediate v={best[0]} "
              f"-> aggregate v={agg_v}")
if not lost:
    print("  none found")
print(f"\n  cases where aggregation scored WORSE than its best refined draft: "
      f"{len(lost)}/{len(out)}")
