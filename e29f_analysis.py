"""e29f_analysis.py: read E29-F by the rule declared in
docs/protocols/E29F-free-length.md. Zero model calls.

With the plan length unpinned, raw inclusion rises for everything, so the
headline quantities are reported both raw and net of the same cell's
never-mentioned rate:

    Delta_X      = P(rejected in plan | restated, X) - P(... | neutral, X)
    DiD_X        = Delta_X - Delta_full
    Excess_X,arm = P(rejected | arm, X) - P(never-mentioned | arm, X)
    G_flag       = P(rejected | neutral, addonly_flag) - P(... | neutral, addonly)

Paired bootstrap over dialogues, seed 0, B = 2000.

Run:  python e29f_analysis.py --model llama3.2:3b
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
DESIGNS = ("full", "delete", "addonly", "addonly_flag")


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model):
    rows = []
    seen = {}
    for f in sorted(glob.glob(f"results/e29f_{slug(model)}_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    for r in rows:
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["parsed"] = r["parsed"] == "True"
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    return rows


def cells(rows, status):
    """dialogue -> design -> arm -> mean inclusion over that status's units."""
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in rows:
        if r["status"] == status and r["included"] is not None:
            acc[(r["instance"], r["rotation"])][r["design"]][r["arm"]].append(r["included"])
    out = defaultdict(lambda: defaultdict(dict))
    for k, byd in acc.items():
        for X, bya in byd.items():
            for a, v in bya.items():
                out[k][X][a] = statistics.mean(v)
    return out


def stats(rej, nev, keys, nkeys=None):
    """`keys` are dialogues complete on the rejected unit; `nkeys` those
    complete on a never-mentioned unit. Only about half the dialogues carry a
    never-mentioned slot, so tying the two together would halve the n on the
    headline quantities for no reason."""
    nkeys = keys if nkeys is None else nkeys
    p, pn = {}, {}
    for X in DESIGNS:
        for arm in ("restated", "neutral"):
            vr = [rej[k][X][arm] for k in keys if rej[k][X].get(arm) is not None]
            vn = [nev[k][X][arm] for k in nkeys if nev[k][X].get(arm) is not None]
            p[(X, arm)] = statistics.mean(vr) if vr else float("nan")
            pn[(X, arm)] = statistics.mean(vn) if vn else float("nan")
    delta = {X: p[(X, "restated")] - p[(X, "neutral")] for X in DESIGNS}
    did = {X: delta[X] - delta["full"] for X in DESIGNS}
    excess = {(X, a): p[(X, a)] - pn[(X, a)] for X in DESIGNS for a in ("restated", "neutral")}
    gflag = p[("addonly_flag", "neutral")] - p[("addonly", "neutral")]
    return p, pn, delta, did, excess, gflag


def excl0(lo, hi):
    return lo > 0 or hi < 0


def main(model):
    rows = load(model)
    if not rows:
        print("no E29-F rows for", model); return
    rej, nev = cells(rows, "rejected"), cells(rows, "never")
    _need = [(X, a) for X in DESIGNS for a in ("restated", "neutral")]
    complete = [k for k in rej if all(rej[k][X].get(a) is not None for X, a in _need)]
    ncomplete = [k for k in nev if all(nev[k][X].get(a) is not None for X, a in _need)]
    print(f"=== E29-F read: {model} — {len(rej)} dialogues seen, {len(complete)} complete ===\n")
    print(f"  dialogues carrying a never-mentioned unit: {len(ncomplete)}")
    void = []
    print("  validity and plan length (length is an OUTCOME here, not a gate):")
    for X in DESIGNS:
        for arm in ("restated", "neutral"):
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm]
            parse = statistics.mean(r["parsed"] for r in rs)
            lens = [r["n_actions"] for r in rs if r["parsed"]]
            mp = statistics.mean(lens) if lens else float("nan")
            nv = statistics.mean([r["included"] for r in rs if r["status"] == "never" and r["included"] is not None])
            bad = parse < 0.95 or nv >= 0.95
            if bad: void.append((X, arm))
            print(f"    {X:14} {arm:9} parse {parse:.3f}   |plan| {mp:.2f}   never {nv:.3f}"
                  f"{'   VOID' if bad else ''}")

    p, pn, delta, did, excess, gflag = stats(rej, nev, complete, ncomplete)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        nsample = [ncomplete[rng.randrange(len(ncomplete))] for _ in ncomplete]
        _, _, dl, dd, ex, gf = stats(rej, nev, sample, nsample)
        for X in DESIGNS:
            boots[("delta", X)].append(dl[X]); boots[("did", X)].append(dd[X])
            for a in ("restated", "neutral"):
                boots[("excess", X, a)].append(ex[(X, a)])
        boots[("gflag",)].append(gf)

    def ci(key):
        v = sorted(boots[key]); return v[int(0.025 * B)], v[int(0.975 * B) - 1]

    print(f"\n  rejected-step inclusion, n = {len(complete)}:")
    print(f"    {'design':14} {'restated':>9} {'neutral':>9} {'Delta':>8} {'95% CI':>18} {'DiD':>8} {'95% CI':>18}")
    for X in DESIGNS:
        lo, hi = ci(("delta", X)); dlo, dhi = ci(("did", X))
        print(f"    {X:14} {p[(X,'restated')]:9.3f} {p[(X,'neutral')]:9.3f} {delta[X]:+8.3f} [{lo:+.3f}, {hi:+.3f}] "
              f"{did[X]:+8.3f} [{dlo:+.3f}, {dhi:+.3f}]")

    print("\n  excess over the same cell's never-mentioned rate:")
    for X in DESIGNS:
        for a in ("restated", "neutral"):
            lo, hi = ci(("excess", X, a))
            print(f"    {X:14} {a:9} never {pn[(X,a)]:.3f}   excess {excess[(X,a)]:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    glo, ghi = ci(("gflag",))
    print(f"\n  G_flag (own-record vs prefix, neutral arm): {gflag:+.3f} [{glo:+.3f}, {ghi:+.3f}]")

    dlo, dhi = ci(("did", "delete"))
    f2 = did["delete"] >= SESOI and excl0(dlo, dhi)
    f3 = gflag > 0 and excl0(glo, ghi)
    reversed_ = (did["delete"] <= -SESOI and excl0(dlo, dhi)) or (gflag < 0 and excl0(glo, ghi))
    if void:
        verdict = "VOID (" + ", ".join(f"{a}/{b}" for a, b in void) + ")"
    elif reversed_:
        verdict = "REVERSED (an effect flips sign with the plan unpinned)"
    elif f2 and f3:
        verdict = "SURVIVES (design dependence and the own-record effect both hold unpinned)"
    elif f2 or f3:
        verdict = "PARTIAL (" + ("design dependence" if f2 else "own-record effect") + " holds, the other does not)"
    else:
        verdict = "CEILING-DEPENDENT (neither effect survives unpinning)"
    print(f"\n  VERDICT: {verdict}")
    out = {"model": model, "n_complete": len(complete), "n_never": len(ncomplete),
           "p": {f"{X}|{a}": v for (X, a), v in p.items()},
           "never": {f"{X}|{a}": v for (X, a), v in pn.items()},
           "delta": delta, "did": did,
           "excess": {f"{X}|{a}": v for (X, a), v in excess.items()},
           "ci_delta": {X: ci(("delta", X)) for X in DESIGNS},
           "ci_did": {X: ci(("did", X)) for X in DESIGNS},
           "gflag": gflag, "ci_gflag": [glo, ghi],
           "mean_plan": statistics.mean(r["n_actions"] for r in rows if r["parsed"]),
           "void": void, "verdict": verdict}
    with open(f"results/e29f_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29f_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    main(ap.parse_args().model)
