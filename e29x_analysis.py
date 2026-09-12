"""e29x_analysis.py: read E29-X by the rule declared in
docs/protocols/E29X-reviewer-controls.md. Zero model calls.

For each decider, from the same-session run:
    Delta_X   = P(rejected step in plan | restated, X) - P(... | neutral, X), X in full / full_explicit / tombstone
    DiD_X     = Delta_X - Delta_full
and, against that decider's E29 summary (same dialogues, earlier session):
    R1  level gap: |P(neutral, full_explicit) - P(neutral, addonly)| vs |P(neutral, full) - P(neutral, addonly)|
    T1  Delta_tombstone relative to E29's Delta_addonly and Delta_delete
Paired bootstrap over dialogues, seed 0, B = 2000.

Run:  python e29x_analysis.py --model llama3.2:3b
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

B = 2000
SESOI = 0.15
DESIGNS = ("full", "full_explicit", "tombstone")


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model):
    rows = []
    for f in sorted(glob.glob(f"results/e29x_{slug(model)}_o*.csv")):
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
    for X in DESIGNS:
        for arm in ("restated", "neutral"):
            vals = [dias[k][X][arm] for k in keys if dias[k][X].get(arm) is not None]
            p[(X, arm)] = statistics.mean(vals) if vals else float("nan")
    delta = {X: p[(X, "restated")] - p[(X, "neutral")] for X in DESIGNS}
    did = {X: delta[X] - delta["full"] for X in DESIGNS}
    return p, delta, did


def excl0(lo, hi):
    return lo > 0 or hi < 0


def main(model):
    rows = load(model)
    if not rows:
        print("no E29-X rows for", model); return
    dias = cells(rows)
    complete = [k for k, v in dias.items() if all(v[X].get(a) is not None for X in DESIGNS for a in ("restated", "neutral"))]
    print(f"=== E29-X read: {model} — {len(dias)} dialogues seen, {len(complete)} complete on all 6 cells ===\n")
    void = []
    for X in DESIGNS:
        for arm in ("restated", "neutral"):
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm]
            parse = statistics.mean(r["parsed"] for r in rs)
            lens = [r["n_actions"] for r in rs if r["parsed"]]
            mp = statistics.mean(lens) if lens else float("nan")
            flag = "" if parse >= 0.95 and 3.9 <= mp <= 4.1 else "   VOID"
            if flag: void.append((X, arm))
            print(f"    {X:14} {arm:9} parse {parse:.3f}   |plan| {mp:.2f}{flag}")

    p, delta, did = stats(dias, complete)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        ps, dl, dd = stats(dias, sample)
        for X in DESIGNS:
            boots[("delta", X)].append(dl[X]); boots[("did", X)].append(dd[X])
            boots[("neutral", X)].append(ps[(X, "neutral")])

    def ci(key):
        v = sorted(boots[key]); return v[int(0.025 * B)], v[int(0.975 * B) - 1]

    print(f"\n  rejected-step inclusion, n = {len(complete)}:")
    print(f"    {'design':14} {'restated':>9} {'neutral':>9} {'Delta':>8} {'95% CI':>18} {'DiD vs full':>12} {'95% CI':>18}")
    for X in DESIGNS:
        lo, hi = ci(("delta", X)); dlo, dhi = ci(("did", X))
        print(f"    {X:14} {p[(X,'restated')]:9.3f} {p[(X,'neutral')]:9.3f} {delta[X]:+8.3f} [{lo:+.3f}, {hi:+.3f}]   "
              f"{did[X]:+12.3f} [{dlo:+.3f}, {dhi:+.3f}]")

    # E29 reference for this decider
    ref_path = f"results/e29_{slug(model)}_summary.json"
    try:
        ref = json.load(open(ref_path, encoding="utf-8"))
    except FileNotFoundError:
        ref = None
    out = {"model": model, "n_complete": len(complete),
           "p": {f"{X}|{a}": v for (X, a), v in p.items()}, "delta": delta, "did": did,
           "ci_delta": {X: ci(("delta", X)) for X in DESIGNS}, "ci_did": {X: ci(("did", X)) for X in DESIGNS},
           "void": void}
    if ref:
        e29 = ref["p"]; e29d = ref["delta"]
        gap_full = abs(p[("full", "neutral")] - e29["addonly|neutral"])
        gap_expl = abs(p[("full_explicit", "neutral")] - e29["addonly|neutral"])
        print(f"\n  R1 level gap to E29 add-only (neutral arm, add-only {e29['addonly|neutral']:.3f}):"
              f"  full {p[('full','neutral')]:.3f} -> gap {gap_full:.3f};  full_explicit {p[('full_explicit','neutral')]:.3f} -> gap {gap_expl:.3f}")
        lo_n, hi_n = ci(("neutral", "full_explicit"))
        r1 = "RENDERING" if gap_expl < gap_full and (hi_n < e29["full|neutral"]) else "DESIGN"
        print(f"     full_explicit neutral 95% CI [{lo_n:.3f}, {hi_n:.3f}] vs E29 full neutral {e29['full|neutral']:.3f}  ->  {r1}")
        print(f"\n  T1 tombstone against E29 add-only Delta {e29d['addonly']:+.3f} and delete Delta {e29d['delete']:+.3f}:"
              f"  Delta_tombstone {delta['tombstone']:+.3f}, DiD {did['tombstone']:+.3f}")
        dlo, dhi = ci(("did", "tombstone"))
        if abs(did["tombstone"]) >= SESOI and excl0(dlo, dhi):
            t1 = "FLAG NOT HONOURED (behaves like delete)"
        elif abs(did["tombstone"]) < 0.05 and -SESOI <= dlo and dhi <= SESOI:
            t1 = "FLAG HONOURED (behaves like add-only)"
        else:
            t1 = "BETWEEN"
        print(f"     -> {t1}")
        out.update({"e29_ref": {"addonly_neutral": e29["addonly|neutral"], "full_neutral": e29["full|neutral"],
                                "delta_addonly": e29d["addonly"], "delta_delete": e29d["delete"]},
                    "r1": {"gap_full": gap_full, "gap_explicit": gap_expl, "verdict": r1},
                    "t1": {"verdict": t1}})
    with open(f"results/e29x_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"\n  wrote results/e29x_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    main(ap.parse_args().model)
