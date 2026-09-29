"""e29t_analysis.py: read E29-T by the rule declared in docs/protocols/E29T-idioms.md.
Zero model calls.

Per decider, neutral arm, for each idiom i:  G_i = P(i) - P(sentence), with a
paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %).

    FAILS      G_i >= 0.15 and its interval excludes 0   (ignored like E29-S's tag)
    HONOURED   the interval's upper bound < 0.15          (read like the sentence)
    UNCLEAR    otherwise

Verdict per decider, over the five real-world idioms (the anchor excluded):
ALL-FAIL (5), MOST-FAIL (3-4), FEW-FAIL (1-2), NONE-FAIL (0).

    python e29t_analysis.py --all
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29t import IDIOMS, REAL_WORLD

B, SESOI = 2000, 0.15
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct")
E29S_ANCHOR = {"llama3.2:3b": (0.156, 0.594), "qwen2.5:14b-instruct": (0.052, 0.323)}   # sentence, tag


def slug(s):
    return s.replace(".", "").replace(":", "-")


def main(model):
    seen = {}
    for f in sorted(glob.glob(f"results/e29t_{slug(model)}_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    if not rows:
        print("no E29-T rows for", model)
        return None
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    rej = defaultdict(dict)
    for r in rows:
        if r["status"] == "rejected" and r["arm"] == "neutral":
            rej[(r["instance"], r["rotation"])][r["design"]] = r["included"]
    keys = [k for k, v in rej.items() if all(v.get(i) is not None for i in IDIOMS)]
    void = []
    for i in IDIOMS:
        c = [r for r in rows if r["design"] == i]
        parse = statistics.mean(r["parsed"] for r in c)
        lens = [r["n_actions"] for r in c if r["parsed"]]
        mp = statistics.mean(lens) if lens else float("nan")
        if parse < 0.95 or not (3.9 <= mp <= 4.1):
            void.append((i, round(parse, 3), round(mp, 2)))

    def p(ks, i):
        return statistics.mean(rej[k][i] for k in ks)

    P = {i: p(keys, i) for i in IDIOMS}
    G = {i: P[i] - P["sentence"] for i in IDIOMS[1:]}
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        base = p(s, "sentence")
        for i in IDIOMS[1:]:
            boots[i].append(p(s, i) - base)
    ci = {i: (sorted(v)[int(0.025 * B)], sorted(v)[int(0.975 * B) - 1]) for i, v in boots.items()}
    cls = {}
    for i in IDIOMS[1:]:
        lo, hi = ci[i]
        cls[i] = "FAILS" if (G[i] >= SESOI and (lo > 0 or hi < 0)) else "HONOURED" if hi < SESOI else "UNCLEAR"
    ctrl = {}
    for st in ("never", "accepted"):
        v = [statistics.mean(r["included"] for r in rows if r["design"] == i and r["status"] == st and r["parsed"]) for i in IDIOMS]
        ctrl[st] = (round(min(v), 3), round(max(v), 3))
    k = sum(cls[i] == "FAILS" for i in REAL_WORLD)
    verdict = "ALL-FAIL" if k == 5 else "MOST-FAIL" if k >= 3 else "FEW-FAIL" if k >= 1 else "NONE-FAIL"
    if void:
        verdict = "VOID " + str(void)
    if len(keys) < 96:
        verdict = f"INCOMPLETE (n={len(keys)}) -- provisional: " + verdict
    anchor = E29S_ANCHOR.get(model)
    print(f"=== E29-T read: {model}  (n = {len(keys)}) ===")
    print(f"  {'sentence':18} {P['sentence']:.3f}   (E29-S {anchor[0] if anchor else '-'})")
    for i in IDIOMS[1:]:
        lo, hi = ci[i]
        extra = f"   (E29-S {anchor[1]})" if (i == "withdrawn_prefix" and anchor) else ""
        print(f"  {i:18} {P[i]:.3f}   G {G[i]:+.3f} [{lo:+.3f}, {hi:+.3f}]  {cls[i]}{extra}")
    print(f"  control: never {ctrl['never'][0]}-{ctrl['never'][1]}, accepted {ctrl['accepted'][0]}-{ctrl['accepted'][1]}")
    print(f"  VERDICT ({model}): {verdict}   [{k} of 5 real-world idioms fail]")
    out = {"model": model, "n": len(keys), "p": P, "g": G, "ci": ci, "class": cls, "control": ctrl,
           "void": void, "verdict": verdict, "fails": k}
    with open(f"results/e29t_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    for m in (DECIDERS if a.all or not a.model else (a.model,)):
        main(m)
