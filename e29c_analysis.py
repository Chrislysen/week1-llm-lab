"""e29c_analysis.py: read E29-C by the rule declared in
docs/protocols/E29C-framing.md. Zero model calls.

    Delta_ftr   = P(rejected step included | restated) - P(... | neutral)
    Delta_plain = P(... | plain) - P(... | plain_neutral)
    Diff        = Delta_ftr - Delta_plain
Paired bootstrap over dialogues, seed 0, B = 2000, percentile 95% intervals.

Run:  python e29c_analysis.py --model llama3.2:3b
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29c import ARMS_C

B = 2000


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model):
    rows = []
    for f in sorted(glob.glob(f"results/e29c_{slug(model)}_o*.csv")):
        rows += list(csv.DictReader(open(f, encoding="utf-8")))
    for r in rows:
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["parsed"] = r["parsed"] == "True"
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    return rows


def cells(rows):
    out = defaultdict(dict)
    for r in rows:
        if r["status"] == "rejected":
            out[(r["instance"], r["rotation"])][r["arm"]] = r["included"]
    return out


def stats(dias, keys):
    p = {}
    for arm in ARMS_C:
        vals = [dias[k][arm] for k in keys if dias[k].get(arm) is not None]
        p[arm] = statistics.mean(vals) if vals else float("nan")
    d_ftr = p["restated"] - p["neutral"]
    d_plain = p["plain"] - p["plain_neutral"]
    return p, d_ftr, d_plain, d_ftr - d_plain


def excludes_zero(lo, hi):
    return lo > 0 or hi < 0


def main(model):
    rows = load(model)
    if not rows:
        print("no E29-C rows for", model); return
    dias = cells(rows)
    complete = [k for k, v in dias.items() if all(v.get(a) is not None for a in ARMS_C)]
    print(f"=== E29-C read: {model} — {len(dias)} dialogues seen, {len(complete)} complete on all 4 arms ===\n")

    void = []
    print("  validity per arm (parse rate, mean |plan|):")
    for arm in ARMS_C:
        rs = [r for r in rows if r["arm"] == arm]
        parse = statistics.mean(r["parsed"] for r in rs)
        lens = [r["n_actions"] for r in rs if r["parsed"]]
        mp = statistics.mean(lens) if lens else float("nan")
        flag = "" if parse >= 0.95 and 3.9 <= mp <= 4.1 else "   VOID"
        if flag: void.append(arm)
        print(f"    {arm:14} parse {parse:.3f}   |plan| {mp:.2f}{flag}")

    p, d_ftr, d_plain, diff = stats(dias, complete)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        _, a, b, c = stats(dias, sample)
        boots["ftr"].append(a); boots["plain"].append(b); boots["diff"].append(c)

    def ci(key):
        v = sorted(boots[key]); return v[int(0.025 * B)], v[int(0.975 * B) - 1]

    print(f"\n  rejected-step inclusion under full context, n = {len(complete)} dialogues per arm:")
    for arm in ARMS_C:
        print(f"    {arm:14} {p[arm]:.3f}")
    c_ftr, c_plain, c_diff = ci("ftr"), ci("plain"), ci("diff")
    print(f"\n    Delta_ftr   (restated - neutral)       {d_ftr:+.3f}  [{c_ftr[0]:+.3f}, {c_ftr[1]:+.3f}]")
    print(f"    Delta_plain (plain - plain_neutral)    {d_plain:+.3f}  [{c_plain[0]:+.3f}, {c_plain[1]:+.3f}]")
    print(f"    Diff        (Delta_ftr - Delta_plain)  {diff:+.3f}  [{c_diff[0]:+.3f}, {c_diff[1]:+.3f}]")

    print("\n  controls (inclusion of never-mentioned / accepted steps):")
    for arm in ARMS_C:
        rs = [r for r in rows if r["arm"] == arm and r["parsed"]]
        nev = [r["included"] for r in rs if r["status"] == "never"]
        acc = [r["included"] for r in rs if r["status"] == "accepted"]
        print(f"    {arm:14} never {statistics.mean(nev):.3f} (n={len(nev)})   accepted {statistics.mean(acc):.3f} (n={len(acc)})")

    # declared read rule
    if void:
        verdict = "VOID (validity failed on " + ", ".join(void) + ")"
    elif not (excludes_zero(*c_ftr) and d_ftr < 0):
        verdict = "NO-REPLICATION (the E29 negative Delta_full did not replicate; the framing question is moot)"
    elif not excludes_zero(*c_plain) and excludes_zero(*c_diff):
        verdict = "FRAMING (the plain mention does not move enactment; the for-the-record line does)"
    elif excludes_zero(*c_plain) and d_plain < 0 and not excludes_zero(*c_diff):
        verdict = "ANY-MENTION (both late mentions lower enactment by amounts not distinguishable)"
    else:
        verdict = "UNRESOLVED"
    print(f"\n  VERDICT: {verdict}")
    out = {"model": model, "n_complete": len(complete), "p": p,
           "delta_ftr": d_ftr, "delta_plain": d_plain, "diff": diff,
           "ci_ftr": c_ftr, "ci_plain": c_plain, "ci_diff": c_diff,
           "void": void, "verdict": verdict}
    with open(f"results/e29c_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29c_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    main(ap.parse_args().model)
