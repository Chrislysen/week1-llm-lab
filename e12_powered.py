"""e12_powered.py: the independence question, at adequate power, with clustering handled.

Protocol: docs/protocols/E12-powered-independence-v1.md. Preregistered; committed
with zero E12 results.

WHAT THIS DISCRIMINATES, in one sentence: whether the model applies a real but
small discount to correlated evidence, or none at all -- a question E10 could not
answer because at n = 36 its power at the preregistered SESOI was 0.14.

THE CLUSTERING IS THE WHOLE STATISTICAL POINT. 108 units live inside 36
instances. Units in one instance share a domain, an action vocabulary and a
setting; they are not independent draws. Treating them as 108 independent
observations would manufacture precision and would be a worse error than the one
E12 exists to fix. So:

    interval   cluster bootstrap -- resample the 36 INSTANCES with replacement,
               carrying all of each instance's units
    test       cluster permutation -- flip the same/indep labels for ALL units
               of an instance together, which is the only exchangeability the
               design actually supports
    naive test reported ALONGSIDE, purely to show how much the clustering
               matters. It is never the headline.

PREREGISTERED DECISION RULE, carried over from E10 unchanged:
  SESOI = 0.10.
  - cluster-permutation p < 0.05                  -> effect exists
  - |diff| < 0.10 AND cluster-bootstrap 95% CI inside +/-0.10
                                                  -> EQUIVALENCE-SUPPORTED NULL
  - otherwise                                     -> still inconclusive; say so

Only the second outcome licenses "the model does not discount correlated
evidence". E10 claimed it without earning it; E12 either earns it or does not.

Run:  python e12_powered.py --limit 36
      python e12_powered.py --analyse
"""
import argparse
import csv
import glob
import json
import math
import random
import statistics

from budget import Budget
from e10_independence import SESOI, SYSTEM
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_e12 import ARMS, N_ARMS, all_units, corpus_hash, exposure, render
from lineage_eval import check_plan, obeys, parse_plan
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

TEMPERATURE = 0
DECIDER = "llama3.2:3b"
BOOT_REPS = 10000
PERM_REPS = 20000
SEED = 20260901


def verdict(instance, rec, actions):
    from lineage_bench import Constraint
    orig = {x.id: x for x in instance.constraints}[rec["constraint"]]
    flipped = Constraint(id=orig.id, kind="before", a=orig.b, b=orig.a)
    s, f = obeys(orig, actions), obeys(flipped, actions)
    if s and not f:
        return "source"
    if f and not s:
        return "flip"
    return "neither"


def ask(client, model, instance, rec, arm):
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            "DISCUSSION\n----------\n"
            f"{render(exposure(rec, arm))}\n\n{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(
        client=client, model=model, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def run(model, offset, limit):
    by_id = {i.id: i for i in all_instances()}
    units = all_units()[offset:None if limit is None else offset + limit]
    client = OllamaClient()
    print(f"=== E12 powered independence: {model}, {len(units)} units x "
          f"{N_ARMS} arms, corpus {corpus_hash()} ===\n")

    rows, detail = [], []
    for i, rec in enumerate(units, 1):
        inst = by_id[rec["instance"]]
        for arm in ARMS:
            res = ask(client, model, inst, rec, arm)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            v = verdict(inst, rec, chk.actions) if chk.parsed else ""
            rows.append({
                "model": model, "unit": rec["unit"], "instance": rec["instance"],
                "domain": rec["domain"], "constraint": rec["constraint"],
                "arm": arm, "parsed": chk.parsed, "verdict": v,
                "seconds": round(sum(x.seconds for x in res.attempts), 2)})
            detail.append({"model": model, "unit": rec["unit"],
                           "instance": rec["instance"], "arm": arm,
                           "plan_text": text})
        print(f"  [{i:>3}/{len(units)}] {rec['unit']:<24} " + " ".join(
            f"{a[:6]}:{rows[-N_ARMS + j]['verdict'][:4] or '----'}"
            for j, a in enumerate(ARMS)))

    tag = model.replace(":", "-").replace(".", "")
    write_csv(f"results/e12_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e12_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e12_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call)")


def load(model=DECIDER):
    rows = []
    for p in sorted(glob.glob("results/e12_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    return [r for r in rows
            if r["model"] == model and r["parsed"] == "True"]


def cluster_bootstrap(clusters, a, b, reps=BOOT_REPS, seed=SEED):
    """Resample INSTANCES with replacement, carrying all their units."""
    keys = list(clusters)
    rng = random.Random(seed)
    diffs = []
    for _ in range(reps):
        pick = [clusters[keys[rng.randrange(len(keys))]] for _ in keys]
        units = [u for c in pick for u in c]
        fa = sum(u.get(a) == "flip" for u in units) / len(units)
        fb = sum(u.get(b) == "flip" for u in units) / len(units)
        diffs.append(fb - fa)
    diffs.sort()
    return diffs[int(0.025 * reps)], diffs[int(0.975 * reps)]


def cluster_permutation(clusters, a, b, reps=PERM_REPS, seed=SEED):
    """Swap the two arm labels for ALL units of an instance together.

    Instance-level exchangeability is the only kind this design supports. A
    unit-level permutation would assume the three propositions inside an
    instance are independent, which is the assumption being avoided.
    """
    units = [u for c in clusters.values() for u in c]
    obs = (sum(u.get(b) == "flip" for u in units)
           - sum(u.get(a) == "flip" for u in units)) / len(units)
    rng = random.Random(seed)
    hits = 0
    for _ in range(reps):
        tot = 0
        for c in clusters.values():
            swap = rng.random() < 0.5
            x, y = (b, a) if swap else (a, b)
            tot += sum((u.get(y) == "flip") - (u.get(x) == "flip") for u in c)
        if abs(tot / len(units)) >= abs(obs) - 1e-12:
            hits += 1
    return (hits + 1) / (reps + 1), obs


def naive_mcnemar(units, a, b):
    n01 = sum(1 for u in units
              if u.get(a) == "flip" and u.get(b) not in (None, "flip"))
    n10 = sum(1 for u in units
              if u.get(b) == "flip" and u.get(a) not in (None, "flip"))
    n = n01 + n10
    if n == 0:
        return None, n01, n10
    k = min(n01, n10)
    return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n,
               1.0), n01, n10


def analyse(model=DECIDER):
    rows = load(model)
    if not rows:
        raise SystemExit("no E12 results yet")
    per_unit = {}
    for r in rows:
        per_unit.setdefault(r["unit"], {})["instance"] = r["instance"]
        per_unit[r["unit"]][r["arm"]] = r["verdict"]

    clusters = {}
    for u, d in per_unit.items():
        clusters.setdefault(d["instance"], []).append(d)
    units = list(per_unit.values())

    print(f"=== E12 powered independence -- {model} ===")
    print(f"  corpus {corpus_hash()}")
    print(f"  {len(units)} units in {len(clusters)} instance clusters\n")

    rate, table = {}, []
    for arm in ARMS:
        s = sum(u.get(arm) == "source" for u in units)
        f = sum(u.get(arm) == "flip" for u in units)
        rate[arm] = round(f / (s + f), 4) if s + f else None
        table.append({"arm": arm, "n": s + f, "source": s, "flip": f,
                      "neither": sum(u.get(arm) == "neither" for u in units),
                      "flip_rate": rate[arm]})
    show(table, list(table[0].keys()))
    write_csv("results/e12_summary.csv", table, list(table[0].keys()))

    print("\n=== PRIMARY: same_root vs indep_root, clustered ===")
    p_perm, obs = cluster_permutation(clusters, "same_root", "indep_root")
    lo, hi = cluster_bootstrap(clusters, "same_root", "indep_root")
    p_naive, n01, n10 = naive_mcnemar(units, "same_root", "indep_root")
    print(f"  same_root  {rate['same_root']}    indep_root {rate['indep_root']}")
    print(f"  observed difference          {obs:+.4f}")
    print(f"  cluster permutation p        {p_perm:.4f}   ({PERM_REPS} reps, "
          f"instance-level label swaps)")
    print(f"  cluster bootstrap 95% CI     [{lo:+.4f}, {hi:+.4f}]")
    print(f"  naive unit-level McNemar     p = "
          f"{'n/a' if p_naive is None else f'{p_naive:.4f}'}  "
          f"discordant {n10}-{n01}")
    print("  The naive line is shown to expose how much clustering matters.")
    print("  It is NOT the headline and must not be quoted as one.")

    print("\n=== the preregistered decision rule ===")
    if p_perm < 0.05:
        print(f"  EFFECT EXISTS. p = {p_perm:.4f} < 0.05. The model does")
        print("  distinguish correlated from independent support. E10's null")
        print("  was a power failure, exactly as the retraction suspected.")
    elif abs(obs) < SESOI and lo > -SESOI and hi < SESOI:
        print(f"  EQUIVALENCE-SUPPORTED NULL. |{obs:+.4f}| < {SESOI} and the")
        print(f"  cluster-bootstrap CI [{lo:+.4f}, {hi:+.4f}] lies entirely")
        print(f"  inside +/-{SESOI}.")
        print("  THIS is the claim E10 made without earning it, and E12 earns")
        print("  it: the model applies no practically meaningful discount to")
        print("  correlated evidence. Bounded, clustered, and preregistered.")
    else:
        print(f"  STILL INCONCLUSIVE. p = {p_perm:.4f}, CI [{lo:+.4f}, {hi:+.4f}]")
        print(f"  against a SESOI of {SESOI}. Not an effect, and not")
        print("  equivalence either. Report as inconclusive and do NOT upgrade.")

    print("\n=== anchors (corroboration should be large and obvious) ===")
    for a, b in (("bare", "filler"), ("filler", "same_root")):
        pp, ob = cluster_permutation(clusters, a, b)
        l2, h2 = cluster_bootstrap(clusters, a, b)
        print(f"  {a:<10} {rate[a]}  ->  {b:<10} {rate[b]}   diff {ob:+.4f}   "
              f"cluster p {pp:.4f}   CI [{l2:+.3f},{h2:+.3f}]")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DECIDER)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    analyse(a.model) if a.analyse else run(a.model, a.offset, a.limit)
