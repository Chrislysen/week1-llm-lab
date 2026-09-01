"""e4_merge.py: cross-model x authority-rule table for E4.

Merges every E4 slice and reports the 2x2 that matters: does capacity change the
behaviour, and is the standing authority rule read at all?

The reflex baselines are model-independent and computed without any model call,
so every model result can be read against the same fixed ceiling and floor.

Run:  python e4_merge.py
"""
import csv
import glob
import statistics

from experiment import show, write_csv
from lineage_bench import all_instances
from lineage_eval import baseline_scores


def load():
    rows = []
    for path in sorted(glob.glob("results/e4_*_o*.csv")):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                for k in ("parsed", "success", "applicable", "correct_both",
                          "source_reflex", "latest_reflex", "neither",
                          "resisted", "exercised"):
                    r[k] = r[k] == "True"
                r["authority_rule"] = r["authority_rule"] == "True"
                r["constraint_recall"] = float(r["constraint_recall"])
                r["seconds"] = float(r["seconds"])
                rows.append(r)
    return rows


def main():
    rows = load()
    # A model x rule cell may have been run in slices; dedupe on instance.
    seen, uniq = set(), []
    for r in rows:
        k = (r["model"], r["authority_rule"], r["instance"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    rows = uniq
    print(f"=== E4: {len(rows)} runs, "
          f"{len({(r['model'], r['authority_rule']) for r in rows})} cells ===\n")

    bl = [baseline_scores(i) for i in all_instances()]
    print("=== fixed reference points (no model involved) ===")
    for k in ("source_truster", "latest_truster"):
        print(f"  {k:<16} mean recall "
              f"{statistics.mean(b[k]['constraint_recall'] for b in bl):.4f}   "
              f"success {sum(b[k]['success'] for b in bl)}/36")
    print(f"  {'speaker policy':<16} mean recall 1.0000   success 36/36   "
          f"<- the correct policy\n")

    out = []
    for model in dict.fromkeys(r["model"] for r in rows):
        for rule in (True, False):
            g = [r for r in rows if r["model"] == model
                 and r["authority_rule"] == rule and r["applicable"]]
            if not g:
                continue
            n = len(g)
            out.append({
                "model": model,
                "authority_rule": rule,
                "n": n,
                "parse_rate": round(sum(r["parsed"] for r in g) / n, 4),
                "correct_both": f"{sum(r['correct_both'] for r in g)}/{n}",
                "latest_reflex": f"{sum(r['latest_reflex'] for r in g)}/{n}",
                "source_reflex": f"{sum(r['source_reflex'] for r in g)}/{n}",
                "neither": f"{sum(r['neither'] for r in g)}/{n}",
                "exercised": round(sum(r["exercised"] for r in g) / n, 4),
                "resisted": round(sum(r["resisted"] for r in g) / n, 4),
                "mean_recall": round(
                    statistics.mean(r["constraint_recall"] for r in g), 4),
                "success": f"{sum(r['success'] for r in g)}/{n}",
                "mean_s": round(statistics.mean(r["seconds"] for r in g), 1),
            })
    show(out, list(out[0].keys()))
    write_csv("results/e4_summary.csv", out, list(out[0].keys()))

    print("\n=== authority-rule ablation: does removing the rule change anything? ===")
    for model in dict.fromkeys(r["model"] for r in rows):
        cells = {c["authority_rule"]: c for c in out if c["model"] == model}
        if True in cells and False in cells:
            a, b = cells[True], cells[False]
            print(f"  {model}")
            for f in ("correct_both", "latest_reflex", "exercised", "resisted"):
                print(f"      {f:<15} with rule {str(a[f]):<8} "
                      f"without {str(b[f]):<8}")
    print("\n  A model that READS the standing rule should get worse without it.")
    print("  Identical performance means the rule was never used, and the")
    print("  latest reflex is an ABSENCE of authority reasoning rather than a")
    print("  misapplication of it.")

    print("\nwrote results/e4_summary.csv")


if __name__ == "__main__":
    main()
