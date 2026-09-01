"""screen_analysis.py: read the two declared EXPLORATORY screens.

E12-X  (docs/protocols/E12X-qwen14b-ready-screen.md): the READY channel on a
       second decider with dynamic range, over the frozen E12 corpus.
E13-X  (docs/protocols/E13X-backfire-screen.md): the normative-principle
       backfire on three further deciders, over E13's frozen prompts.

Everything here is exploratory. Instance-level inference throughout, using
e14_ready.delta_stats (sign-flip permutation over instances, instance
bootstrap). Nothing printed is a claim.

Run:  python screen_analysis.py --e12x qwen2.5:14b-instruct
      python screen_analysis.py --e13x aya-expanse:8b
"""
import argparse
import collections
import csv
import glob
import io
import json

from e14_ready import delta_stats
from experiment import show
from lineage_eval import parse_plan


def _pairs_stats(per, label):
    units = list(per.values())
    n = len(units)
    gt = sum(u["delta"] > 0 for u in units)
    lt = sum(u["delta"] < 0 for u in units)
    d = delta_stats(per, "delta")
    return {"contrast": label, "n": n, "clusters": d["clusters"],
            "delta": d["mean"], "pos": gt, "neg": lt, "ties": n - gt - lt,
            "p_two": round(d["p_two"], 4), "ci": f"[{d['lo']:+.3f},{d['hi']:+.3f}]"}


# ------------------------------------------------------------------ E12-X --

def e12x(model):
    tag = model.replace(":", "-").replace(".", "")
    rows, det = [], {}
    for p in sorted(glob.glob(f"results/e12_{tag}_o*.csv")):
        rows += list(csv.DictReader(open(p, newline="")))
    for p in sorted(glob.glob(f"results/e12_{tag}_o*.json")):
        for r in json.load(io.open(p, encoding="utf-8")):
            det[(r["unit"], r["arm"])] = r["plan_text"]
    if not rows:
        raise SystemExit(f"no E12-X rows for {model}")
    print(f"=== E12-X exploratory screen -- {model}: {len(rows)} rows ===")
    by = collections.defaultdict(dict)
    for r in rows:
        pl, _ = parse_plan(det.get((r["unit"], r["arm"]), ""))
        by[r["unit"]].setdefault("instance", r["instance"])
        by[r["unit"]][r["arm"]] = {
            "parsed": r["parsed"] == "True",
            "flip": (1 if r["verdict"] == "flip" else 0) if r["verdict"] in ("source", "flip") else None,
            "ready": (1 if pl["ready"] else 0) if pl is not None else None}
    arms = ["bare", "filler", "same_root", "indep_root"]
    tab = []
    for a in arms:
        vals = [u[a] for u in by.values() if a in u]
        tab.append({"arm": a, "n": len(vals),
                    "parsed": sum(v["parsed"] for v in vals),
                    "ready": sum(1 for v in vals if v["ready"] == 1),
                    "ready_rate": round(sum(1 for v in vals if v["ready"] == 1)
                                        / max(1, sum(1 for v in vals if v["ready"] is not None)), 3),
                    "flip_rate": round(sum(1 for v in vals if v["flip"] == 1)
                                       / max(1, sum(1 for v in vals if v["flip"] is not None)), 3)})
    show(tab, list(tab[0].keys()))
    out = []
    for outcome in ("ready", "flip"):
        for a, b in (("same_root", "indep_root"), ("filler", "same_root"), ("bare", "filler")):
            per = {}
            for uid, u in by.items():
                if a in u and b in u and u[a][outcome] is not None and u[b][outcome] is not None:
                    per[uid] = {"instance": u["instance"], "delta": u[a][outcome] - u[b][outcome]}
            if per:
                out.append(_pairs_stats(per, f"{outcome}: {a} - {b}"))
    print()
    show(out, list(out[0].keys()))
    print("\n  positive on 'ready: same_root - indep_root' = llama's direction.")
    print("  Exploratory; 108 units / 36 clusters; no claim.")


# ------------------------------------------------------------------ E13-X --

def e13x(model):
    tag = model.replace(":", "-").replace(".", "")
    rows = []
    for p in sorted(glob.glob(f"results/e13x_{tag}_o*.csv")):
        rows += list(csv.DictReader(open(p, newline="")))
    if not rows:
        raise SystemExit(f"no E13-X rows for {model}")
    print(f"=== E13-X exploratory screen -- {model}: {len(rows)} rows ===")
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(r["intervention"], r["dependence"])].append(r)
    tab = []
    for (arm, dep), g in sorted(cells.items()):
        ok = [r for r in g if r["verdict"] in ("source", "flip")]
        tab.append({"intervention": arm, "dependence": dep, "n": len(g),
                    "parse_rate": round(sum(r["parsed"] == "True" for r in g) / len(g), 3),
                    "flip_rate": round(sum(r["verdict"] == "flip" for r in ok) / max(1, len(ok)), 3),
                    "ready_rate": round(sum(r["ready"] == "True" for r in g)
                                        / max(1, sum(r["parsed"] == "True" for r in g)), 3)})
    show(tab, list(tab[0].keys()))
    by = collections.defaultdict(dict)
    for r in rows:
        if r["verdict"] in ("source", "flip"):
            by[(r["unit"], r["dependence"])][r["intervention"]] = 1 if r["verdict"] == "flip" else 0
    out = []
    for a, b in (("normative", "default"), ("identify", "default"), ("normative", "identify")):
        per = {}
        for (uid, dep), u in by.items():
            if a in u and b in u:
                per[(uid, dep)] = {"instance": uid.split(":")[0], "delta": u[a] - u[b]}
        if per:
            out.append(_pairs_stats(per, f"flip: {a} - {b} (pooled over dependence)"))
    print()
    show(out, list(out[0].keys()))
    print("\n  llama3.2:3b (E13, re-derived): normative - default +0.1019 (29 vs 7,")
    print("  p 0.0064); identify - default +0.0139; positive = the backfire.")
    print("  Exploratory; no claim.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--e12x")
    p.add_argument("--e13x")
    a = p.parse_args()
    if a.e12x:
        e12x(a.e12x)
    if a.e13x:
        e13x(a.e13x)
