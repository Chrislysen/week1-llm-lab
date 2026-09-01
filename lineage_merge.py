"""lineage_merge.py: merge the matrix slices and summarise.

The matrix is run in slices (long single runs kept being killed). This merges
them and RE-DERIVES every row from the saved plan text rather than concatenating
the slice CSVs, so the table comes from artifacts and not from bookkeeping.

Reported per condition AND per axis. The 36 instances are a 6x6 crossed design
-- 6 surface draws and 6 structures, not 36 independent samples -- so a bare
mean over 36 would overstate what is there.

Run:  python lineage_merge.py
"""
import glob
import json
import statistics

from experiment import show, write_csv
from lineage_bench import expose, generate_instance
from lineage_eval import baseline_scores, check_plan, presence, score

CHUNKS = sorted(glob.glob("results/e2_matrix_detail_c*.json"))


def main():
    detail = []
    for path in CHUNKS:
        with open(path) as f:
            detail.extend(json.load(f))
    print(f"=== merged {len(CHUNKS)} slices, {len(detail)} runs ===\n")

    rows = []
    for rec in detail:
        domain, graph = rec["instance"].split("-")
        inst = generate_instance(domain, graph)
        cond = rec["condition"]
        chk = check_plan(rec["plan_text"], inst)
        sc = score(inst, expose(inst, cond), rec["plan_text"])
        dai = sc["decision_authority_inversion"]
        rows.append({
            "instance": inst.id, "domain": domain, "graph": graph,
            "condition": cond,
            "parsed": chk.parsed,
            "constraint_recall": chk.constraint_recall,
            "violations": len(chk.violated),
            "violated": "|".join(chk.violated),
            "success": chk.success,
            "n_actions": len(chk.actions),
            "unknown_actions": len(chk.unknown_actions),
            "dai_eligible": dai["eligible"],
            "dai_src": dai["follows_source"],
            "dai_cor": dai["follows_corruption"],
            "dai_nei": dai["follows_neither"],
            "corr_eligible": sc["corruption_susceptibility"]["eligible"],
            "corr_adopted": sc["corruption_susceptibility"]["adopted"],
            "sup_eligible": sc["supersession_respected"]["eligible"],
            "sup_exercised": sc["supersession_respected"]["exercised"],
            "sup_collateral": sc["supersession_collateral"]["violations"] or 0,
            "rec_eligible": sc["recovery"]["eligible"],
            "rec_ok": round((sc["recovery"]["rate"] or 0)
                            * sc["recovery"]["eligible"]),
            "util_src": sc["utilization"]["direct_source"],
            "util_src_n": sc["utilization"]["direct_source_n"],
            "util_fai": sc["utilization"]["faithful_relay"],
            "util_fai_n": sc["utilization"]["faithful_relay_n"],
            "disc_applicable": sc["discrimination"].get("applicable", False),
            "disc_correct_both": sc["discrimination"].get("correct_both", False),
            "disc_source_reflex": sc["discrimination"].get("source_reflex", False),
            "disc_latest_reflex": sc["discrimination"].get("latest_reflex", False),
            "disc_neither": sc["discrimination"].get("neither", False),
            "disc_resisted": sc["discrimination"].get("resisted_corruption", False),
            "disc_exercised": sc["discrimination"].get("exercised_override", False),
        })

    write_csv("results/e2_matrix_runs.csv", rows, list(rows[0].keys()))
    with open("results/e2_matrix_detail.json", "w") as f:
        json.dump(detail, f, indent=2)

    conds = list(dict.fromkeys(r["condition"] for r in rows))

    print("=== per condition ===")
    summary = []
    for c in conds:
        g = [r for r in rows if r["condition"] == c]
        parsed = [r for r in g if r["parsed"]]
        src = sum(r["dai_src"] for r in g)
        cor = sum(r["dai_cor"] for r in g)
        nei = sum(r["dai_nei"] for r in g)
        ce = sum(r["corr_eligible"] for r in g)
        ca = sum(r["corr_adopted"] for r in g)
        fn = sum(r["util_fai_n"] for r in g)
        summary.append({
            "condition": c, "n": len(g),
            "parse_rate": round(len(parsed) / len(g), 4),
            "mean_recall": round(statistics.mean(
                r["constraint_recall"] for r in parsed), 4) if parsed else None,
            "sd_recall": round(statistics.stdev(
                r["constraint_recall"] for r in parsed), 4) if len(parsed) > 1 else None,
            "success": round(sum(r["success"] for r in g) / len(g), 4),
            "dai_src": src, "dai_cor": cor, "dai_nei": nei,
            "dai_rate": round(cor / (src + cor), 4) if src + cor else None,
            "corr_adopted": f"{ca}/{ce}" if ce else "-",
            "corr_rate": round(ca / ce, 4) if ce else None,
            "faithful_util_n": fn,
        })
    show(summary, list(summary[0].keys()))
    write_csv("results/e2_matrix_summary.csv", summary, list(summary[0].keys()))

    # Per-axis: 6 domains and 6 graphs are the independent draws, not 36.
    for axis in ("domain", "graph"):
        print(f"\n=== decision authority inversion by {axis} (condition=both) ===")
        both = [r for r in rows if r["condition"] == "both"]
        grid = []
        for v in sorted({r[axis] for r in both}):
            g = [r for r in both if r[axis] == v]
            s_, c_ = sum(r["dai_src"] for r in g), sum(r["dai_cor"] for r in g)
            grid.append({axis: v, "follows_source": s_, "follows_corruption": c_,
                         "rate": round(c_ / (s_ + c_), 4) if s_ + c_ else None})
        rates = [x["rate"] for x in grid if x["rate"] is not None]
        show(grid, list(grid[0].keys()))
        print(f"  across {axis}s: mean {statistics.mean(rates):.4f}  "
              f"sd {statistics.stdev(rates):.4f}  "
              f"range {min(rates):.4f}-{max(rates):.4f}")

    print("\n=== does the source rescue the decision? ===")
    for c in ("corruption_only", "both", "both_recovery"):
        g = [r for r in rows if r["condition"] == c]
        ce, ca = sum(r["corr_eligible"] for r in g), sum(r["corr_adopted"] for r in g)
        s_, c_ = sum(r["dai_src"] for r in g), sum(r["dai_cor"] for r in g)
        parts = [f"  {c:<16}"]
        if ce:
            parts.append(f"corruption adopted {ca}/{ce} = {ca / ce:.4f}")
        if s_ + c_:
            parts.append(f"DAI {c_}/{s_ + c_} = {c_ / (s_ + c_):.4f}")
        re_, ro = sum(r["rec_eligible"] for r in g), sum(r["rec_ok"] for r in g)
        if re_:
            parts.append(f"recovery {ro}/{re_} = {ro / re_:.4f}")
        print("   ".join(parts))

    print("\n=== supersession (corrected metric) ===")
    g = [r for r in rows if r["condition"] == "supersession"]
    e = sum(r["sup_eligible"] for r in g)
    x = sum(r["sup_exercised"] for r in g)
    print(f"  exercised {x}/{e} = {x / e:.4f}   "
          f"(ambiguous {e - x}/{e} -- unmeasured, not wrong)")
    print(f"  mean collateral violations {statistics.mean(r['sup_collateral'] for r in g):.2f}"
          f"   instances with >=1: {sum(r['sup_collateral'] > 0 for r in g)}/{len(g)}")

    print("\n=== faithful-relay utilization (the metric that could never fire) ===")
    for c in ("faithful_only", "source_and_faithful"):
        g = [r for r in rows if r["condition"] == c]
        if not g:
            continue
        n = sum(r["util_fai_n"] for r in g)
        vals = [r["util_fai"] for r in g if r["util_fai"] is not None]
        print(f"  {c:<20} n={n}  mean={statistics.mean(vals):.4f}" if vals
              else f"  {c:<20} n={n}  (undefined)")

    print("\nwrote results/e2_matrix_runs.csv, e2_matrix_summary.csv, "
          "e2_matrix_detail.json")


if __name__ == "__main__":
    main()
