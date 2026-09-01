"""lineage_recompute.py: re-derive the supersession metrics from saved plans.

The first `supersession_respected` was vacuous -- superseded constraints are
excluded from `effective_constraints`, so they could never appear in `violated`
and the rate was always 1.0 when eligible. An empty plan scored 1.0.

Every number it produced in results/e2_matrix_*.csv for that column is void.
This script recomputes the corrected metrics from the SAVED PLAN TEXT in
results/e2_matrix_detail.json, so no model call is repeated and the correction
is auditable against the same artifacts.

Run:  python lineage_recompute.py
"""
import json
import statistics

from experiment import show, write_csv
from lineage_bench import expose, generate_instance
from lineage_eval import (check_plan, presence, supersession_collateral,
                          supersession_respected)

DETAIL = "results/e2_matrix_detail.json"


def main():
    with open(DETAIL) as f:
        detail = json.load(f)

    rows = []
    for rec in detail:
        if rec["condition"] != "supersession":
            continue
        domain, graph = rec["instance"].split("-")
        inst = generate_instance(domain, graph)
        pres = presence(inst, expose(inst, "supersession"))
        chk = check_plan(rec["plan_text"], inst)
        sr = supersession_respected(inst, pres, chk)
        col = supersession_collateral(inst, pres, chk)
        ann = {c.id: c for c in inst.constraints}[inst.announced_supersession]
        rows.append({
            "instance": rec["instance"],
            "domain": inst.domain,
            "graph": inst.graph,
            "announced": inst.announced_supersession,
            "announced_kind": ann.kind,
            "lifted_closure": len(inst.superseded),
            "parsed": chk.parsed,
            "constraint_recall": chk.constraint_recall,
            "exercised": sr["exercised"],
            "ambiguous": sr["ambiguous"],
            "collateral_violations": col["violations"],
            "collateral_ids": "|".join(col["violated"]),
        })

    write_csv("results/e2_supersession_corrected.csv", rows, list(rows[0].keys()))

    n = len(rows)
    ex = sum(r["exercised"] for r in rows)
    am = sum(r["ambiguous"] for r in rows)
    print(f"=== corrected supersession metrics, n={n} instances ===")
    print("    recomputed from saved plan text; no model calls\n")
    print(f"  exercised (plan demonstrably free of the lifted rule)  "
          f"{ex}/{n} = {ex / n:.4f}")
    print(f"  ambiguous (plan satisfies the lifted rule anyway)      {am}/{n}")
    print("    ambiguous is UNMEASURED, not wrong -- still-bound and")
    print("    coincidentally-compatible are indistinguishable from the plan.\n")
    print(f"  mean collateral violations                            "
          f"{statistics.mean(r['collateral_violations'] for r in rows):.2f}")
    print(f"  instances with >=1 collateral violation                "
          f"{sum(r['collateral_violations'] > 0 for r in rows)}/{n}")
    print("    collateral = constraints that were NOT lifted, violated in a")
    print("    context containing an override. This is over-application damage.\n")

    by_kind = []
    for kind in ("required", "before"):
        g = [r for r in rows if r["announced_kind"] == kind]
        if not g:
            continue
        by_kind.append({
            "announced_kind": kind, "n": len(g),
            "exercised": sum(r["exercised"] for r in g),
            "exercised_rate": round(sum(r["exercised"] for r in g) / len(g), 4),
            "mean_collateral": round(
                statistics.mean(r["collateral_violations"] for r in g), 2),
            "mean_recall": round(
                statistics.mean(r["constraint_recall"] for r in g), 4),
        })
    show(by_kind, list(by_kind[0].keys()))

    print("\n=== by domain ===")
    by_dom = []
    for d in sorted({r["domain"] for r in rows}):
        g = [r for r in rows if r["domain"] == d]
        by_dom.append({
            "domain": d, "n": len(g),
            "exercised": sum(r["exercised"] for r in g),
            "mean_collateral": round(
                statistics.mean(r["collateral_violations"] for r in g), 2),
            "mean_recall": round(
                statistics.mean(r["constraint_recall"] for r in g), 4),
        })
    show(by_dom, list(by_dom[0].keys()))

    print("\nwrote results/e2_supersession_corrected.csv")
    print("The supersession columns in results/e2_matrix_*.csv are VOID; use this file.")


if __name__ == "__main__":
    main()
