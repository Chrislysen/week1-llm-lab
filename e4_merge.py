"""e4_merge.py: revision-following as a function of the STATED rule.

Four system-prompt variants, one unchanged ground truth. In every variant the
only legitimate revision is the Duty Manager's; only the sentence the model is
shown changes.

    none      no sentence about revision authority at all -- the floor
    prohibit  "the agreed procedure is final; no revision applies"
    permit    "any participant may revise; the most recent version applies"
    restrict  "only the Duty Manager may revise" -- the TRUE rule

`exercised` (how often the model follows a revision) is the primary measure and
is interpretable in all four. `correct_both` is only interpretable under `none`
and `restrict`, where the prompt does not contradict ground truth; under
`prohibit` and `permit` the prompt asserts something false, so correctness is
recorded but not compared.

Run:  python e4_merge.py
"""
import csv
import glob
import statistics

from experiment import show, write_csv
from lineage_bench import all_instances
from lineage_eval import baseline_scores

VARIANTS = ("none", "prohibit", "permit", "restrict")
BOOLS = ("parsed", "success", "applicable", "correct_both", "source_reflex",
         "latest_reflex", "neither", "resisted", "exercised")


def load():
    rows, seen = [], set()
    for path in sorted(glob.glob("results/e4_*_o*.csv")):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                for k in BOOLS:
                    r[k] = r[k] == "True"
                # Files written before the four-variant change carry only the
                # boolean; map it onto the variant name it corresponds to.
                if not r.get("rule_variant"):
                    r["rule_variant"] = ("restrict"
                                         if r.get("authority_rule") == "True"
                                         else "none")
                # Empty when the plan did not parse: recall is None,
                # not 0.0. Kept as a row so parse failures stay visible
                # in the denominator instead of vanishing.
                r["constraint_recall"] = (
                    float(r["constraint_recall"])
                    if r["constraint_recall"] else None)
                r["seconds"] = float(r["seconds"])
                k = (r["model"], r["rule_variant"], r["instance"])
                if k in seen:
                    continue
                seen.add(k)
                rows.append(r)
    return rows


def main():
    rows = load()
    models = sorted({r["model"] for r in rows})
    print(f"=== E4: {len(rows)} runs, "
          f"{len({(r['model'], r['rule_variant']) for r in rows})} cells, "
          f"{len(models)} models ===\n")

    bl = [baseline_scores(i) for i in all_instances()]
    print("=== fixed reference points, no model involved ===")
    for k in ("source_truster", "latest_truster"):
        print(f"  {k:<16} recall "
              f"{statistics.mean(b[k]['constraint_recall'] for b in bl):.4f}   "
              f"success {sum(b[k]['success'] for b in bl)}/36")
    print(f"  {'speaker policy':<16} recall 1.0000   success 36/36  <- correct\n")

    out = []
    for m in models:
        for v in VARIANTS:
            g = [r for r in rows if r["model"] == m
                 and r["rule_variant"] == v and r["applicable"]]
            if not g:
                continue
            n = len(g)
            out.append({
                "model": m, "rule": v, "n": n,
                "parse": round(sum(r["parsed"] for r in g) / n, 3),
                "correct": f"{sum(r['correct_both'] for r in g)}/{n}",
                "latest": f"{sum(r['latest_reflex'] for r in g)}/{n}",
                "source": f"{sum(r['source_reflex'] for r in g)}/{n}",
                "neither": f"{sum(r['neither'] for r in g)}/{n}",
                "exercised": round(sum(r["exercised"] for r in g) / n, 4),
                "resisted": round(sum(r["resisted"] for r in g) / n, 4),
                "recall": round(statistics.mean(
                    r["constraint_recall"] for r in g
                    if r["constraint_recall"] is not None), 4),
                "unparsed": sum(not r["parsed"] for r in g),
            })
    show(out, list(out[0].keys()))
    write_csv("results/e4_summary.csv", out, list(out[0].keys()))

    cells = {(c["model"], c["rule"]): c for c in out}
    full = [m for m in models if all((m, v) in cells for v in VARIANTS)]

    print("\n=== revision-following rate by STATED rule (ground truth unchanged) ===")
    print(f"  {'model':<22}" + "".join(f"{v:>11}" for v in VARIANTS))
    for m in full:
        print(f"  {m:<22}" + "".join(
            f"{cells[(m, v)]['exercised']:>11.3f}" for v in VARIANTS))

    print("\n=== contrasts ===")
    deltas = {"prohibit-none": [], "permit-none": [],
              "restrict-none": [], "restrict-permit": []}
    for m in full:
        e = {v: cells[(m, v)]["exercised"] for v in VARIANTS}
        deltas["prohibit-none"].append(e["prohibit"] - e["none"])
        deltas["permit-none"].append(e["permit"] - e["none"])
        deltas["restrict-none"].append(e["restrict"] - e["none"])
        deltas["restrict-permit"].append(e["restrict"] - e["permit"])
        print(f"  {m:<22} " + "  ".join(
            f"{k} {v[-1]:+.3f}" for k, v in deltas.items()))

    print(f"\n  across {len(full)} models:")
    for k, v in deltas.items():
        same = all(x > 0 for x in v) or all(x < 0 for x in v)
        print(f"    {k:<18} mean {statistics.mean(v):+.4f}   "
              f"range {min(v):+.3f}..{max(v):+.3f}   "
              f"{'SAME DIRECTION in all ' + str(len(v)) if same else 'mixed'}")
    # The headline contrast, over EVERY model that has both arms -- not only
    # those with all four variants.
    print("\n=== restrict - none, across every model with both arms ===")
    print("    Does naming an authority that RESTRICTS revision increase how")
    print("    often revisions are followed? Ground truth is identical.\n")
    pairs = []
    for m in models:
        if (m, "none") in cells and (m, "restrict") in cells:
            a, b = cells[(m, "none")], cells[(m, "restrict")]
            pairs.append((m, a["exercised"], b["exercised"],
                          b["exercised"] - a["exercised"],
                          a["resisted"], b["resisted"]))
    print(f"  {'model':<22}{'none':>8}{'restrict':>10}{'delta':>9}"
          f"{'resist n':>10}{'resist r':>10}")
    for m, a, b, d, ra, rb in pairs:
        print(f"  {m:<22}{a:>8.3f}{b:>10.3f}{d:>+9.3f}{ra:>10.3f}{rb:>10.3f}")

    pos = sum(x[3] > 0 for x in pairs)
    nm = len(pairs)
    print(f"\n  {pos}/{nm} models positive; mean delta "
          f"{statistics.mean(x[3] for x in pairs):+.4f}")
    if pos == nm:
        pv = 0.5 ** nm
        print(f"  Sign test, unanimous at n={nm}: one-sided p = {pv:.4f}"
              + ("  <- below 0.05" if pv < 0.05 else "  <- NOT significant"))
    else:
        print("  Not unanimous; a sign test gives nothing at this n.")

    rdelta = [x[5] - x[4] for x in pairs]
    print(f"  Resistance to an UNAUTHORISED revision over the same comparison: "
          f"mean {statistics.mean(rdelta):+.4f}")
    print("  That is the point: the rule raises compliance with EVERY revision")
    print("  rather than selectively with the one it authorises.")

    print("\n  Caveats that stay attached to this number: the models are not")
    print("  independent draws (three share the qwen2.5 family), a sign test")
    print("  ignores effect size, and each cell is n=36 with no within-model")
    print("  repeats, so cell noise is unestimated.")

    print("\nwrote results/e4_summary.csv")


if __name__ == "__main__":
    main()
