"""e29s_analysis.py: read E29-S by the rule declared in
docs/protocols/E29S-structure.md. Zero model calls.

The 2x2 over the neutral arm, where every store contains the rejection:

                     own item          same item
    proposition      addonly           addonly_merged
    attribute        addonly_meta      addonly_flag

    S_merge     = P(addonly_merged) - P(addonly)        separation | proposition
    S_flag      = P(addonly_flag)   - P(addonly_meta)   separation | attribute
    S_form_own  = P(addonly_meta)   - P(addonly)        form | own item
    S_form_same = P(addonly_flag)   - P(addonly_merged) form | same item

Paired bootstrap over dialogues, seed 0, B = 2000.

Run:  python e29s_analysis.py --model llama3.2:3b
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29s import DESIGNS_S

B = 2000
SESOI = 0.15
MIN_EFFECT = 0.05
CONTRASTS = {
    "S_merge": ("addonly_merged", "addonly", "separation, proposition form held"),
    "S_flag": ("addonly_flag", "addonly_meta", "separation, attribute form held"),
    "S_form_own": ("addonly_meta", "addonly", "form, own item held"),
    "S_form_same": ("addonly_flag", "addonly_merged", "form, same item held"),
}


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model):
    seen = {}
    for f in sorted(glob.glob(f"results/e29s_{slug(model)}_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
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
    for X in DESIGNS_S:
        for arm in ("restated", "neutral"):
            v = [dias[k][X][arm] for k in keys if dias[k][X].get(arm) is not None]
            p[(X, arm)] = statistics.mean(v) if v else float("nan")
    delta = {X: p[(X, "restated")] - p[(X, "neutral")] for X in DESIGNS_S}
    g = {name: p[(a, "neutral")] - p[(b, "neutral")] for name, (a, b, _) in CONTRASTS.items()}
    return p, delta, g


def excl0(lo, hi):
    return lo > 0 or hi < 0


def main(model):
    rows = load(model)
    if not rows:
        print("no E29-S rows for", model); return
    dias = cells(rows)
    complete = [k for k, v in dias.items()
                if all(v[X].get(a) is not None for X in DESIGNS_S for a in ("restated", "neutral"))]
    print(f"=== E29-S read: {model}, {len(dias)} dialogues seen, {len(complete)} complete ===\n")
    void = []
    for X in DESIGNS_S:
        for arm in ("restated", "neutral"):
            rs = [r for r in rows if r["design"] == X and r["arm"] == arm]
            parse = statistics.mean(r["parsed"] for r in rs)
            lens = [r["n_actions"] for r in rs if r["parsed"]]
            mp = statistics.mean(lens) if lens else float("nan")
            bad = parse < 0.95 or not (3.9 <= mp <= 4.1)
            if bad: void.append((X, arm))
            print(f"    {X:16} {arm:9} parse {parse:.3f}   |plan| {mp:.2f}{'   VOID' if bad else ''}")

    p, delta, g = stats(dias, complete)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        _, dl, gg = stats(dias, sample)
        for X in DESIGNS_S:
            boots[("delta", X)].append(dl[X])
        for k, v in gg.items():
            boots[("g", k)].append(v)

    def ci(key):
        v = sorted(boots[key]); return v[int(0.025 * B)], v[int(0.975 * B) - 1]

    print(f"\n  the 2x2, neutral arm (n = {len(complete)}), rejected-step inclusion:")
    print(f"    {'':16} {'own item':>12} {'same item':>12}")
    print(f"    {'proposition':16} {p[('addonly','neutral')]:12.3f} {p[('addonly_merged','neutral')]:12.3f}")
    print(f"    {'attribute':16} {p[('addonly_meta','neutral')]:12.3f} {p[('addonly_flag','neutral')]:12.3f}")

    print("\n  contrasts:")
    for name, (a, b, what) in CONTRASTS.items():
        lo, hi = ci(("g", name))
        print(f"    {name:12} {what:34} {g[name]:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    print("\n  restatement effect within each design:")
    for X in DESIGNS_S:
        lo, hi = ci(("delta", X))
        print(f"    {X:16} restated {p[(X,'restated')]:.3f}  neutral {p[(X,'neutral')]:.3f}  "
              f"Delta {delta[X]:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    sep = [ci(("g", k)) for k in ("S_merge", "S_flag")]
    frm = [ci(("g", k)) for k in ("S_form_own", "S_form_same")]
    sep_big = all(g[k] >= SESOI and excl0(*c) for k, c in zip(("S_merge", "S_flag"), sep))
    frm_big = all(g[k] >= SESOI and excl0(*c) for k, c in zip(("S_form_own", "S_form_same"), frm))
    sep_any = any(g[k] >= SESOI and excl0(*c) for k, c in zip(("S_merge", "S_flag"), sep))
    frm_any = any(g[k] >= SESOI and excl0(*c) for k, c in zip(("S_form_own", "S_form_same"), frm))
    if void:
        verdict = "VOID (" + ", ".join(f"{a}/{b}" for a, b in void) + ")"
    elif sep_big and not frm_any:
        verdict = "SEPARATION (item separation drives it; the wording does not)"
    elif frm_big and not sep_any:
        verdict = "FORM (propositional form drives it; the bullet boundary does not)"
    elif sep_any and frm_any:
        verdict = "INTERACTION (both matter; neither alone explains the cell pattern)"
    elif not sep_any and not frm_any:
        verdict = "NULL (no contrast reaches the threshold)"
    else:
        verdict = "PARTIAL"
    print(f"\n  VERDICT: {verdict}")
    out = {"model": model, "n_complete": len(complete),
           "p": {f"{X}|{a}": v for (X, a), v in p.items()}, "delta": delta, "g": g,
           "ci_delta": {X: ci(("delta", X)) for X in DESIGNS_S},
           "ci_g": {k: ci(("g", k)) for k in CONTRASTS},
           "void": void, "verdict": verdict}
    with open(f"results/e29s_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29s_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    main(ap.parse_args().model)
