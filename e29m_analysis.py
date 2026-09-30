"""e29m_analysis.py: read E29-M by the rule declared in docs/protocols/E29M-fix.md.
Zero model calls.

Per decider, neutral arm, rejected-step inclusion P(cell), complete-case over all
six cells, paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %).

Fix rows (fix F read against anchor A): rewrite vs is_active_false, rewrite vs
invalid_at, annotate_is_active vs is_active_false, annotate_invalid_at vs invalid_at.
    UNTESTABLE  the anchor does not fail in this run (P(A) - P(sentence) < 0.15 or
                its interval includes 0)
    E = P(A) - P(F)            how far the fix lowers inclusion from the anchor
    G = P(F) - P(sentence)     how far the fix stays above the sentence control
    FIXED      E >= 0.15 with an interval excluding 0, and G's upper bound < 0.15
    PARTIAL    E >= 0.15 with an interval excluding 0, and G's upper bound >= 0.15
    NOT FIXED  otherwise
Headline per decider: the weaker of the two rewrite rows.
Secondary, the field's effect with the sentence present: D = P(annotate) - P(rewrite),
COMPETES (D >= 0.15, interval excluding 0) / INERT (upper bound < 0.15) / UNCLEAR.
P1 (anchors reproduce E29-T within 0.10) and P2 (accepted and undecided-proposal
inclusion within 0.10 across cells) are reported beside the verdict, not voiding.
VOID if any cell parses below 0.95 or its mean |plan| is outside [3.9, 4.1].

    python e29m_analysis.py --all
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29m import CELLS

B, SESOI = 2000, 0.15
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct")
ANCHORS = ("is_active_false", "invalid_at")
FIXES = (("rewrite", "is_active_false"), ("rewrite", "invalid_at"),
         ("annotate_is_active", "is_active_false"), ("annotate_invalid_at", "invalid_at"))
FIELD = ("annotate_is_active", "annotate_invalid_at")
RANK = {"UNTESTABLE": -1, "NOT FIXED": 0, "PARTIAL": 1, "FIXED": 2}
E29T = {"llama3.2:3b": {"sentence": 0.156, "is_active_false": 0.906, "invalid_at": 0.812},
        "qwen2.5:14b-instruct": {"sentence": 0.062, "is_active_false": 0.729, "invalid_at": 0.896}}


def slug(s):
    return s.replace(".", "").replace(":", "-")


def ci(v):
    v = sorted(v)
    return v[int(0.025 * B)], v[int(0.975 * B) - 1]


def excl0(lo, hi):
    return lo > 0 or hi < 0


def main(model):
    seen = {}
    for f in sorted(glob.glob(f"results/e29m_{slug(model)}_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    if not rows:
        print("no E29-M rows for", model)
        return None
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    rej = defaultdict(dict)
    for r in rows:
        if r["status"] == "rejected" and r["arm"] == "neutral":
            rej[(r["instance"], r["rotation"])][r["design"]] = r["included"]
    keys = [k for k, v in rej.items() if all(v.get(c) is not None for c in CELLS)]
    void = []
    for c in CELLS:
        cr = [r for r in rows if r["design"] == c]
        parse = statistics.mean(r["parsed"] for r in cr)
        lens = [r["n_actions"] for r in cr if r["parsed"]]
        mp = statistics.mean(lens) if lens else float("nan")
        if parse < 0.95 or not (3.9 <= mp <= 4.1):
            void.append((c, round(parse, 3), round(mp, 2)))
    ctrl = {st: {c: statistics.mean(r["included"] for r in rows
                                    if r["design"] == c and r["status"] == st and r["parsed"])
                 for c in CELLS} for st in ("accepted", "proposed", "never")}
    spec_miss = [st for st in ("accepted", "proposed") if max(ctrl[st].values()) - min(ctrl[st].values()) > 0.10]

    def p(ks, c):
        return statistics.mean(rej[k][c] for k in ks)

    P = {c: p(keys, c) for c in CELLS}
    rng = random.Random(0)
    bootA, bootE, bootG, bootD = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        ps = {c: p(s, c) for c in CELLS}
        for a in ANCHORS:
            bootA[a].append(ps[a] - ps["sentence"])
        for f, a in FIXES:
            bootE[(f, a)].append(ps[a] - ps[f])
            bootG[(f, a)].append(ps[f] - ps["sentence"])
        for f in FIELD:
            bootD[f].append(ps[f] - ps["rewrite"])
    e29t = E29T.get(model, {})
    p1 = {c: (round(P[c], 3), e29t[c], abs(P[c] - e29t[c]) <= 0.10) for c in e29t}
    out = {"model": model, "n": len(keys), "p": P, "void": void, "control": ctrl, "p2_miss": spec_miss,
           "p1": p1, "anchors": {}, "fixes": {}, "field": {}}
    print(f"=== E29-M read: {model}  (n = {len(keys)}) ===")
    for c in CELLS:
        extra = f"   (E29-T {e29t[c]}{'' if p1[c][2] else ', P1 MISS'})" if c in e29t else ""
        print(f"  {c:20} {P[c]:.3f}{extra}")
    fails = {}
    for a in ANCHORS:
        g = P[a] - P["sentence"]
        lo, hi = ci(bootA[a])
        fails[a] = g >= SESOI and excl0(lo, hi)
        out["anchors"][a] = {"G": g, "ci": [lo, hi], "fails": fails[a]}
    for f, a in FIXES:
        E, G = P[a] - P[f], P[f] - P["sentence"]
        (elo, ehi), (glo, ghi) = ci(bootE[(f, a)]), ci(bootG[(f, a)])
        if not fails[a]:
            cls = "UNTESTABLE"
        elif E >= SESOI and excl0(elo, ehi):
            cls = "FIXED" if ghi < SESOI else "PARTIAL"
        else:
            cls = "NOT FIXED"
        share = E / (P[a] - P["sentence"]) if P[a] != P["sentence"] else float("nan")
        out["fixes"][f"{f} vs {a}"] = {"E": E, "ci_E": [elo, ehi], "G": G, "ci_G": [glo, ghi],
                                       "class": cls, "share_removed": share}
        print(f"  {f:20} vs {a:16} E {E:+.3f} [{elo:+.3f}, {ehi:+.3f}]   "
              f"G {G:+.3f} [{glo:+.3f}, {ghi:+.3f}]   {cls}   (share removed {share:.2f})")
    for f in FIELD:
        D = P[f] - P["rewrite"]
        lo, hi = ci(bootD[f])
        cls = "COMPETES" if (D >= SESOI and excl0(lo, hi)) else "INERT" if hi < SESOI else "UNCLEAR"
        out["field"][f] = {"D": D, "ci": [lo, hi], "class": cls}
        print(f"  field effect, {f:20} D {D:+.3f} [{lo:+.3f}, {hi:+.3f}]   {cls}")
    print("  control inclusion across cells: " + "; ".join(
        f"{st} {min(v.values()):.3f}-{max(v.values()):.3f}" for st, v in ctrl.items())
        + (f"   P2 MISS: {spec_miss}" if spec_miss else "   P2 holds"))
    rw = [out["fixes"][f"rewrite vs {a}"]["class"] for a in ANCHORS]
    verdict = min(rw, key=RANK.get)
    if void:
        verdict = "VOID " + str(void)
    if len(keys) < 96:
        verdict = f"INCOMPLETE (n={len(keys)}) -- provisional: " + verdict
    out["verdict"] = verdict
    print(f"  VERDICT ({model}): rewrite {verdict}")
    with open(f"results/e29m_{slug(model)}_summary.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    for m in (DECIDERS if a.all or not a.model else (a.model,)):
        main(m)
