"""e29_analysis.py: read E29 by the rule declared in
docs/protocols/E29-memory-semantics.md. Zero model calls.

    Delta_X  = P(rejected step included | restated, X) - P(... | neutral, X)
    DiD_X    = Delta_X - Delta_full
Paired bootstrap over dialogues (the unit of independence), seed 0, B = 2000,
percentile 95% intervals.

Run:  python e29_analysis.py --model llama3.2:3b
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29 import ARMS, DESIGNS

B = 2000
SESOI = 0.15
MIN_EFFECT = 0.05


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model, prefix="e29"):
    """Untagged chunk files first, then tagged re-runs (e.g. `_fix_o*`), so a
    re-run row replaces the original for the same (dialogue, design, arm, unit)."""
    rows = []
    files = sorted(glob.glob(f"results/{prefix}_{slug(model)}_o*.csv"))
    fixes = sorted(glob.glob(f"results/{prefix}_{slug(model)}_*_o*.csv"))
    for f in files + fixes:
        rows += list(csv.DictReader(open(f, encoding="utf-8")))
    seen = {}
    for r in rows:
        seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    if fixes:
        print(f"  ({len(fixes)} tagged re-run file(s) override the originals)")
    for r in rows:
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["parsed"] = r["parsed"] == "True"
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    return rows


def cells(rows):
    """dialogue -> design -> arm -> included(rejected unit)."""
    out = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        if r["status"] != "rejected":
            continue
        out[(r["instance"], r["rotation"])][r["design"]][r["arm"]] = r["included"]
    return out


def deltas(dias, keys):
    p = {}
    for X in DESIGNS:
        for arm in ARMS:
            vals = [dias[k][X][arm] for k in keys if dias[k][X].get(arm) is not None]
            p[(X, arm)] = statistics.mean(vals) if vals else float("nan")
    delta = {X: p[(X, "restated")] - p[(X, "neutral")] for X in DESIGNS}
    did = {X: delta[X] - delta["full"] for X in DESIGNS}
    return p, delta, did


def main(model, corpus="e16"):
    prefix = {"e16": "e29", "new": "e29n"}[corpus]
    rows = load(model, prefix)
    if not rows:
        print(f"no {prefix} rows for", model); return
    dias = cells(rows)
    complete = [k for k, v in dias.items()
                if all(v[X].get(arm) is not None for X in DESIGNS for arm in ARMS)]
    print(f"=== E29 read [{corpus}]: {model} — {len(dias)} dialogues seen, {len(complete)} complete on all 8 cells ===\n")

    # validity per cell
    void = []
    print("  validity per cell (parse rate, mean |plan|):")
    for X in DESIGNS:
        for arm in ARMS:
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm]
            parse = statistics.mean(r["parsed"] for r in rs)
            lens = [r["n_actions"] for r in rs if r["parsed"]]
            mp = statistics.mean(lens) if lens else float("nan")
            flag = "" if parse >= 0.95 and 3.9 <= mp <= 4.1 else "   VOID"
            if flag: void.append((X, arm))
            print(f"    {X:8} {arm:9} parse {parse:.3f}   |plan| {mp:.2f}{flag}")

    p, delta, did = deltas(dias, complete)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        _, dl, dd = deltas(dias, sample)
        for X in DESIGNS:
            boots[("delta", X)].append(dl[X]); boots[("did", X)].append(dd[X])

    def ci(key):
        v = sorted(boots[key]); return v[int(0.025 * B)], v[int(0.975 * B) - 1]

    print(f"\n  rejected-step inclusion, n = {len(complete)} dialogues per cell:")
    print(f"    {'design':8} {'restated':>9} {'neutral':>9} {'Delta':>8} {'95% CI':>18} {'DiD vs full':>12} {'95% CI':>18}")
    verdict_rows = {}
    for X in DESIGNS:
        lo, hi = ci(("delta", X)); dlo, dhi = ci(("did", X))
        verdict_rows[X] = (did[X], dlo, dhi)
        print(f"    {X:8} {p[(X,'restated')]:9.3f} {p[(X,'neutral')]:9.3f} {delta[X]:+8.3f} "
              f"[{lo:+.3f}, {hi:+.3f}]   {did[X]:+12.3f} [{dlo:+.3f}, {dhi:+.3f}]")

    # controls: never / accepted per cell
    print("\n  controls (inclusion of never-mentioned / accepted steps):")
    for X in DESIGNS:
        for arm in ARMS:
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm and r["parsed"]]
            nev = [r["included"] for r in rs if r["status"] == "never"]
            acc = [r["included"] for r in rs if r["status"] == "accepted"]
            print(f"    {X:8} {arm:9} never {statistics.mean(nev):.3f} (n={len(nev)})   "
                  f"accepted {statistics.mean(acc):.3f} (n={len(acc)})")

    # declared read rule
    others = [X for X in DESIGNS if X != "full" and (X, "restated") not in void and (X, "neutral") not in void]
    dep = [X for X in others if abs(verdict_rows[X][0]) >= SESOI and (verdict_rows[X][1] > 0 or verdict_rows[X][2] < 0)]
    null = all(abs(verdict_rows[X][0]) < MIN_EFFECT and -SESOI <= verdict_rows[X][1] and verdict_rows[X][2] <= SESOI for X in others)
    if ("full", "restated") in void or ("full", "neutral") in void or not others:
        verdict = "VOID (validity failed on a load-bearing cell)"
    elif dep:
        verdict = "DESIGN-DEPENDENT: " + ", ".join(f"{X} DiD {verdict_rows[X][0]:+.3f}" for X in dep)
    elif null:
        verdict = "NULL (every DiD inside the SESOI band)"
    else:
        verdict = "PARTIAL"
    print(f"\n  restatement effect under full context: Delta_full = {delta['full']:+.3f}")
    print(f"  VERDICT: {verdict}")
    out = {"model": model, "n_complete": len(complete), "p": {f"{X}|{a}": v for (X, a), v in p.items()},
           "delta": delta, "did": did,
           "ci_delta": {X: ci(("delta", X)) for X in DESIGNS}, "ci_did": {X: ci(("did", X)) for X in DESIGNS},
           "void": void, "verdict": verdict}
    out["corpus"] = corpus
    with open(f"results/{prefix}_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/{prefix}_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", default="e16", choices=("e16", "new"))
    a = ap.parse_args()
    main(a.model, a.corpus)
