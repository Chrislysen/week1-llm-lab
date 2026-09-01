"""ffep_inventory.py: what does "167 VERIFIED" actually contain?

Feasibility audit for docs/FFEP-FEASIBILITY.md. No model calls. Reads the
saved output of verify_claims.py and every raw artifact under results/, and
writes docs/ffep_inventory.json plus a table on stdout, separating

    verifier assertions        one [ OK ] line each, classified by what they check
    scientific claims          the numbers a document reports (statistical rows)
    experiment runs            (experiment, model) pairs with raw output on disk
    raw model responses        one plan_text each
    task instances             frozen formal instances
    propositions               (instance, constraint) units
    conditions                 arms / exposure conditions / cells
    repeated runs              same prompt sent more than once
    clusters                   the sampling unit the statistics actually use
    successful trajectories    responses whose verdict is the "pass" the
                               experiment scored -- and separately, plans that
                               pass the full deterministic evaluator (zero
                               violations AND ready)
    independent sampling units what a confirmatory FFEP run could count

Run:  python verify_claims.py > /tmp/verify_full.txt ; python ffep_inventory.py /tmp/verify_full.txt
"""
import collections
import glob
import io
import json
import os
import re
import sys

from lineage_bench import all_instances
from lineage_eval import check_plan, parse_plan

CATS = [
    ("structure", re.compile(r"hash|fixture|count|identical|byte|regenerat|prompt|corpus|manifest|row count|cells present|arms? |parse rate|units? x|clusters|calls per model|responses on disk|artifacts", re.I)),
    ("control", re.compile(r"echo|empty|null|truster|control|baseline|ceiling|gate|leak", re.I)),
    ("statistic", re.compile(r"\bp\b|p <|p >|CI|bootstrap|permutation|McNemar|sign|diff|rate|adoption|flip|discordan|equivalen|SESOI|holm|delta|READY|ready|recogni|count|inversion|recall|success|sensitiv|degrade|discriminat", re.I)),
]


def classify(desc):
    for name, rx in CATS:
        if rx.search(desc):
            return name
    return "other"


def verifier_assertions(path):
    ok, skip = [], []
    for line in io.open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*\[ OK \] (.*?)\s{2}= ", line)
        if m:
            ok.append(m.group(1).strip())
            continue
        m = re.match(r"\s*\[SKIP\] (.*)", line)
        if m:
            skip.append(m.group(1).strip())
    return ok, skip


def raw_responses():
    """Every plan_text on disk, keyed by experiment file family."""
    rows = []
    for p in sorted(glob.glob("results/*.json")):
        base = os.path.basename(p)
        exp = re.match(r"(e\d+x?|ceiling)", base)
        exp = exp.group(1) if exp else base.split("_")[0]
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        recs = d if isinstance(d, list) else list(d.values())
        for r in recs:
            if not isinstance(r, dict) or "plan_text" not in r:
                continue
            rows.append({"exp": exp, "file": base, "model": r.get("model", "?"),
                         "instance": r.get("instance", "?"), "unit": r.get("unit"),
                         "cond": r.get("arm") or r.get("intervention") or r.get("condition") or "?",
                         "dep": r.get("dependence"), "plan_text": r["plan_text"]})
    return rows


def main(verify_path):
    ok, skip = verifier_assertions(verify_path)
    by_cat = collections.Counter(classify(d) for d in ok)
    by_section = collections.Counter()
    for d in ok:
        m = re.match(r"(E\d+X?|E1\b|Mode|corpus|control|E6|E2|E3|E4|E5|E7|E8|E9)", d)
        by_section[m.group(1) if m else "other"] += 1

    rows = raw_responses()
    insts = {i.id: i for i in all_instances()}
    runs = collections.Counter((r["exp"], r["model"]) for r in rows)
    per_exp = collections.defaultdict(lambda: {"responses": 0, "models": set(), "conds": set(), "instances": set(), "units": set()})
    dup = collections.Counter((r["exp"], r["model"], r["instance"], r["unit"], r["cond"], r["dep"]) for r in rows)
    repeated = sum(1 for k, v in dup.items() if v > 1)
    full_pass = collections.Counter()
    parsed = collections.Counter()
    for r in rows:
        e = per_exp[r["exp"]]
        e["responses"] += 1
        e["models"].add(r["model"]); e["conds"].add(r["cond"]); e["instances"].add(r["instance"])
        if r["unit"]:
            e["units"].add(r["unit"])
        inst = insts.get(r["instance"].split("~")[0]) if isinstance(r["instance"], str) else None
        if inst is not None:
            chk = check_plan(r["plan_text"], inst)
            parsed[r["exp"]] += chk.parsed
            full_pass[r["exp"]] += bool(chk.parsed and not chk.violated and chk.ready)

    # E12/E13 scored verdicts from CSVs (the experiment's own "pass" = holds the source)
    verdicts = collections.defaultdict(collections.Counter)
    for p in sorted(glob.glob("results/e1[0-3]_*_o*.csv")) + sorted(glob.glob("results/e13x_*_o*.csv")) + sorted(glob.glob("results/e12_*_o*.csv")):
        import csv
        exp = re.match(r"(e\d+x?)", os.path.basename(p)).group(1)
        for r in csv.DictReader(open(p, newline="")):
            verdicts[(exp, r["model"])][r.get("verdict", "")] += 1

    inv = {
        "verifier": {"ok": len(ok), "skip": len(skip), "by_category": dict(by_cat), "by_section": dict(by_section),
                     "note": "one [ OK ] line = one recomputation matching a pinned value; not a trajectory"},
        "task_instances_frozen": len(insts),
        "clusters_frozen": len(insts),
        "propositions_e12_units": 108,
        "domains": 6, "graphs": 6,
        "experiment_runs": [{"exp": e, "model": m, "responses": n} for (e, m), n in sorted(runs.items())],
        "raw_responses_total": len(rows),
        "repeated_identical_cells": repeated,
        "per_experiment": {e: {"responses": v["responses"], "models": sorted(v["models"]), "conditions": len(v["conds"]),
                               "instances": len(v["instances"]), "units": len(v["units"]),
                               "parsed": parsed.get(e), "full_evaluator_pass_zero_violations_and_ready": full_pass.get(e)}
                           for e, v in sorted(per_exp.items())},
        "scored_verdicts": {f"{e}/{m}": dict(c) for (e, m), c in sorted(verdicts.items())},
    }
    os.makedirs("docs", exist_ok=True)
    with open("docs/ffep_inventory.json", "w") as f:
        json.dump(inv, f, indent=1, sort_keys=True)

    print(f"verifier: {len(ok)} OK, {len(skip)} SKIP; by category {dict(by_cat)}")
    print(f"          by section {dict(by_section)}")
    print(f"raw responses on disk: {len(rows)} across {len(runs)} (experiment, model) runs; "
          f"repeated identical cells: {repeated}")
    print(f"frozen instances {len(insts)} (6 domains x 6 graphs), E12 propositions 108, clusters = instances")
    print("\n  exp     responses  models  conds  inst  units  parsed  full-pass(zero viol & ready)")
    for e, v in sorted(inv["per_experiment"].items()):
        print(f"  {e:<7} {v['responses']:>8}  {len(v['models']):>5}  {v['conditions']:>5}  {v['instances']:>4}  "
              f"{v['units']:>5}  {str(v['parsed']):>6}  {str(v['full_evaluator_pass_zero_violations_and_ready']):>6}")
    print("\n  scored verdicts (experiment's own pass = 'source'):")
    for k, c in sorted(inv["scored_verdicts"].items()):
        print(f"  {k:<28} {dict(c)}")
    print("\nwrote docs/ffep_inventory.json")


if __name__ == "__main__":
    main(sys.argv[1])
