"""e29e_analysis.py: read E29-E by the rule declared in
docs/protocols/E29E-encoding.md. Zero model calls.

The estimands are LEVEL differences in the neutral arm, where the only thing
that differs between designs is how the rejection is written:

    G_meta = P(included | neutral, addonly_meta) - P(... | neutral, addonly)
    G_flag = P(included | neutral, addonly_flag) - P(... | neutral, addonly)
    G_fm   = P(included | neutral, addonly_flag) - P(... | neutral, addonly_meta)

plus, for continuity with E29, the within-design restatement effect Delta_X
and its DiD against the same-session addonly reference. Paired bootstrap over
dialogues, seed 0, B = 2000, percentile 95% intervals.

Run:  python e29e_analysis.py --model llama3.2:3b
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29e import DESIGNS_E

B = 2000
SESOI = 0.15
MIN_EFFECT = 0.05


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model):
    rows = []
    for f in sorted(glob.glob(f"results/e29e_{slug(model)}_o*.csv")):
        rows += list(csv.DictReader(open(f, encoding="utf-8")))
    for r in rows:
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["parsed"] = r["parsed"] == "True"
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    return rows


def cells(rows):
    out = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        if r["status"] == "rejected":
            out[(r["instance"], r["rotation"])][r["design"]][r["arm"]] = r["included"]
    return out


def stats(dias, keys):
    p = {}
    for X in DESIGNS_E:
        for arm in ("restated", "neutral"):
            vals = [dias[k][X][arm] for k in keys if dias[k][X].get(arm) is not None]
            p[(X, arm)] = statistics.mean(vals) if vals else float("nan")
    delta = {X: p[(X, "restated")] - p[(X, "neutral")] for X in DESIGNS_E}
    did = {X: delta[X] - delta["addonly"] for X in DESIGNS_E}
    g = {"meta": p[("addonly_meta", "neutral")] - p[("addonly", "neutral")],
         "flag": p[("addonly_flag", "neutral")] - p[("addonly", "neutral")],
         "fm": p[("addonly_flag", "neutral")] - p[("addonly_meta", "neutral")]}
    return p, delta, did, g


def excl0(lo, hi):
    return lo > 0 or hi < 0


def main(model):
    rows = load(model)
    if not rows:
        print("no E29-E rows for", model); return
    dias = cells(rows)
    complete = [k for k, v in dias.items()
                if all(v[X].get(a) is not None for X in DESIGNS_E for a in ("restated", "neutral"))]
    print(f"=== E29-E read: {model} — {len(dias)} dialogues seen, {len(complete)} complete on all 6 cells ===\n")
    void = []
    for X in DESIGNS_E:
        for arm in ("restated", "neutral"):
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm]
            parse = statistics.mean(r["parsed"] for r in rs)
            lens = [r["n_actions"] for r in rs if r["parsed"]]
            mp = statistics.mean(lens) if lens else float("nan")
            flag = "" if parse >= 0.95 and 3.9 <= mp <= 4.1 else "   VOID"
            if flag: void.append((X, arm))
            print(f"    {X:14} {arm:9} parse {parse:.3f}   |plan| {mp:.2f}{flag}")

    p, delta, did, g = stats(dias, complete)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        _, dl, dd, gg = stats(dias, sample)
        for X in DESIGNS_E:
            boots[("delta", X)].append(dl[X]); boots[("did", X)].append(dd[X])
        for k, v in gg.items():
            boots[("g", k)].append(v)

    def ci(key):
        v = sorted(boots[key]); return v[int(0.025 * B)], v[int(0.975 * B) - 1]

    print(f"\n  rejected-step inclusion, n = {len(complete)}:")
    print(f"    {'design':14} {'restated':>9} {'neutral':>9} {'Delta':>8} {'95% CI':>18} {'DiD':>8} {'95% CI':>18}")
    for X in DESIGNS_E:
        lo, hi = ci(("delta", X)); dlo, dhi = ci(("did", X))
        print(f"    {X:14} {p[(X,'restated')]:9.3f} {p[(X,'neutral')]:9.3f} {delta[X]:+8.3f} [{lo:+.3f}, {hi:+.3f}] "
              f"{did[X]:+8.3f} [{dlo:+.3f}, {dhi:+.3f}]")

    print("\n  encoding contrasts, NEUTRAL arm (the rejection is present in all three):")
    labels = {"meta": "G_meta  metadata vs prose, same line count and position",
              "flag":  "G_flag  flag on the proposal vs prose line",
              "fm":    "G_fm    flag vs metadata (the extra line alone)"}
    for k in ("meta", "flag", "fm"):
        lo, hi = ci(("g", k))
        print(f"    {labels[k]:58} {g[k]:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    print("\n  controls (never-mentioned / accepted):")
    for X in DESIGNS_E:
        for arm in ("restated", "neutral"):
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm and r["parsed"]]
            nev = [r["included"] for r in rs if r["status"] == "never"]
            acc = [r["included"] for r in rs if r["status"] == "accepted"]
            print(f"    {X:14} {arm:9} never {statistics.mean(nev):.3f}   accepted {statistics.mean(acc):.3f}")

    gm_lo, gm_hi = ci(("g", "meta")); gf_lo, gf_hi = ci(("g", "flag"))
    if void:
        verdict = "VOID (" + ", ".join(f"{a}/{b}" for a, b in void) + ")"
    elif g["meta"] >= SESOI and excl0(gm_lo, gm_hi):
        verdict = "ENCODING (wording alone moves it, at constant line count)"
    elif abs(g["meta"]) < MIN_EFFECT and -SESOI <= gm_lo and gm_hi <= SESOI and g["flag"] >= SESOI and excl0(gf_lo, gf_hi):
        verdict = "LENGTH (only dropping the line moves it)"
    elif (abs(g["meta"]) < MIN_EFFECT and abs(g["flag"]) < MIN_EFFECT
          and -SESOI <= gm_lo and gm_hi <= SESOI and -SESOI <= gf_lo and gf_hi <= SESOI):
        verdict = "NULL (neither re-encoding moves it; the E29-X gap was elsewhere)"
    else:
        verdict = "PARTIAL"
    print(f"\n  VERDICT: {verdict}")
    out = {"model": model, "n_complete": len(complete),
           "p": {f"{X}|{a}": v for (X, a), v in p.items()}, "delta": delta, "did": did, "g": g,
           "ci_delta": {X: ci(("delta", X)) for X in DESIGNS_E},
           "ci_did": {X: ci(("did", X)) for X in DESIGNS_E},
           "ci_g": {k: ci(("g", k)) for k in ("meta", "flag", "fm")},
           "void": void, "verdict": verdict}
    with open(f"results/e29e_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29e_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    main(ap.parse_args().model)
