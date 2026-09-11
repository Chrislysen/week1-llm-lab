"""e29b_analysis.py: read E29-B by the rule declared in
docs/protocols/E29-memory-semantics.md (E29-B section). Zero model calls.

Run:  python e29b_analysis.py --model llama3.2:3b
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
MIN_EFFECT = 0.05
MANIP_MIN = 0.5


def slug(s):
    return s.replace(".", "").replace(":", "-")


def _b(v):
    return {"True": True, "False": False}.get(v)


def load(pattern):
    rows = []
    for f in sorted(glob.glob(pattern)):
        rows += list(csv.DictReader(open(f, encoding="utf-8")))
    return rows


def main(model):
    rows = load(f"results/e29b_{slug(model)}_o*.csv")
    if not rows:
        print("no E29-B rows for", model); return
    rej = [r for r in rows if r["status"] == "rejected"]
    dias = defaultdict(dict)
    for r in rej:
        dias[(r["instance"], r["rotation"])][r["arm"]] = r
    complete = [k for k, v in dias.items() if "restated" in v and "neutral" in v]
    print(f"=== E29-B read: {model} — {len(dias)} dialogues, {len(complete)} complete on both arms ===\n")

    # validity
    for arm in ("restated", "neutral"):
        rs = [r for r in rows if r["arm"] == arm]
        parse = statistics.mean(r["parsed"] == "True" for r in rs)
        lens = [int(r["n_actions"]) for r in rs if r["parsed"] == "True"]
        mp = statistics.mean(lens) if lens else float("nan")
        print(f"  {arm:9} decider parse {parse:.3f}   |plan| {mp:.2f}{'' if parse >= 0.95 and 3.9 <= mp <= 4.1 else '   VOID'}")

    # write-path descriptives (per dialogue; prefix values identical across arms)
    one = [dias[k]["restated"] for k in complete]
    prop = statistics.mean(_b(r["after_proposal_mentions"]) is True for r in one)
    reply_gone = [(_b(r["after_reply_mentions"]) is False) for r in one if _b(r["after_proposal_mentions"]) is True]
    w1 = statistics.mean(reply_gone) if reply_gone else float("nan")
    print(f"\n  manipulation check: store mentions the step after its proposal line in {prop:.3f} of dialogues "
          f"({'PASS' if prop >= MANIP_MIN else 'FAIL, stage UNINFORMATIVE'})")
    print(f"  W1  rejection removed the step from the store (given it was there): {w1:.3f}  (n={len(reply_gone)})")
    for arm in ("restated", "neutral"):
        rs = [dias[k][arm] for k in complete]
        m = statistics.mean(_b(r["store_mentions_action"]) is True for r in rs)
        d = statistics.mean(int(r["n_delete"]) for r in rs)
        bad = statistics.mean(int(r["malformed_extract"]) + int(r["malformed_update"]) for r in rs)
        calls = statistics.mean(int(r["write_calls"]) for r in rs)
        print(f"  W2  {arm:9} final store mentions the rejected step: {m:.3f}   DELETEs/dialogue {d:.2f}   "
              f"malformed/dialogue {bad:.2f}   write calls/dialogue {calls:.1f}")

    # decider effect, paired bootstrap
    def delta(keys):
        r_ = [_b(dias[k]["restated"]["included"]) for k in keys]
        n_ = [_b(dias[k]["neutral"]["included"]) for k in keys]
        r_ = [x for x in r_ if x is not None]; n_ = [x for x in n_ if x is not None]
        return statistics.mean(r_) - statistics.mean(n_), statistics.mean(r_), statistics.mean(n_)
    d0, pr, pn = delta(complete)
    rng = random.Random(0)
    bs = sorted(delta([complete[rng.randrange(len(complete))] for _ in complete])[0] for _ in range(B))
    lo, hi = bs[int(0.025 * B)], bs[int(0.975 * B) - 1]
    print(f"\n  rejected-step inclusion on the REAL store: restated {pr:.3f}  neutral {pn:.3f}  "
          f"Delta_real {d0:+.3f} [{lo:+.3f}, {hi:+.3f}]  (n={len(complete)})")

    # the same dialogues under E29's oracle delete and full arms
    e29 = load(f"results/e29_{slug(model)}_o*.csv")
    keys = set(complete)
    ref = {}
    for X in ("delete", "full"):
        cell = {arm: [_b(r["included"]) for r in e29 if r["status"] == "rejected" and r["design"] == X
                      and r["arm"] == arm and (r["instance"], r["rotation"]) in keys] for arm in ("restated", "neutral")}
        if all(cell.values()):
            ref[X] = statistics.mean(cell["restated"]) - statistics.mean(cell["neutral"])
            print(f"  same {len(cell['restated'])} dialogues, E29 {X:6} oracle: Delta {ref[X]:+.3f}")

    if prop < MANIP_MIN:
        verdict = "UNINFORMATIVE (manipulation check failed)"
    elif d0 >= SESOI and lo > 0:
        verdict = "REAL-STORE EFFECT"
    elif abs(d0) < MIN_EFFECT and -SESOI <= lo and hi <= SESOI:
        verdict = "NULL"
    else:
        verdict = "PARTIAL"
    print(f"\n  VERDICT: {verdict}")
    out = {"model": model, "n": len(complete), "manip_prop": prop, "w1_delete_given_present": w1,
           "p_restated": pr, "p_neutral": pn, "delta_real": d0, "ci": [lo, hi], "e29_ref": ref, "verdict": verdict}
    with open(f"results/e29b_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29b_{slug(model)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    main(ap.parse_args().model)
