"""e29d_analysis.py: read E29-D by the rule declared in
docs/protocols/E29D-real-ops-extractor.md. Zero model calls.

    W0  manipulation check: store mentions the step after its proposal line (>= 0.5 or UNINFORMATIVE)
    W1  rejection removed the step from the store, given it was there
    W2  final store mentions the rejected step, per arm
    D   Delta_real = P(rejected step included | restated) - P(... | neutral), paired bootstrap
Reference: E29's oracle `delete` and `addonly` Deltas on the SAME dialogues and decider.

Run:  python e29d_analysis.py --extractor qwen2.5:7b-instruct --decider llama3.2:3b
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

B = 2000
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


def e29_reference(decider, keys):
    """E29 oracle Deltas for `delete` and `addonly` restricted to `keys`."""
    rows = load(f"results/e29_{slug(decider)}_o*.csv")
    cells = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        if r["status"] == "rejected" and r["parsed"] == "True":
            cells[(r["instance"], r["rotation"])][r["design"]][r["arm"]] = _b(r["included"])
    out = {}
    for X in ("delete", "addonly", "full"):
        ks = [k for k in keys if cells[k][X].get("restated") is not None and cells[k][X].get("neutral") is not None]
        if not ks:
            out[X] = None; continue
        pr = statistics.mean(cells[k][X]["restated"] for k in ks)
        pn = statistics.mean(cells[k][X]["neutral"] for k in ks)
        out[X] = {"n": len(ks), "restated": pr, "neutral": pn, "delta": pr - pn}
    return out


def main(extractor, decider):
    rows = load(f"results/e29d_{slug(extractor)}_{slug(decider)}_o*.csv")
    if not rows:
        print("no E29-D rows for", extractor, decider); return
    rej = [r for r in rows if r["status"] == "rejected"]
    dias = defaultdict(dict)
    for r in rej:
        dias[(r["instance"], r["rotation"])][r["arm"]] = r
    complete = [k for k, v in dias.items() if "restated" in v and "neutral" in v]
    print(f"=== E29-D read: {extractor} -> {decider} — {len(dias)} dialogues, {len(complete)} complete on both arms ===\n")

    void = False
    for arm in ("restated", "neutral"):
        rs = [r for r in rows if r["arm"] == arm]
        parse = statistics.mean(r["parsed"] == "True" for r in rs)
        lens = [int(r["n_actions"]) for r in rs if r["parsed"] == "True"]
        mp = statistics.mean(lens) if lens else float("nan")
        ok = parse >= 0.95 and 3.9 <= mp <= 4.1
        void = void or not ok
        print(f"  {arm:9} decider parse {parse:.3f}   |plan| {mp:.2f}{'' if ok else '   VOID'}")

    one = [dias[k]["restated"] for k in complete]
    w0 = statistics.mean(_b(r["after_proposal_mentions"]) is True for r in one)
    reply_gone = [(_b(r["after_reply_mentions"]) is False) for r in one if _b(r["after_proposal_mentions"]) is True]
    w1 = statistics.mean(reply_gone) if reply_gone else float("nan")
    bad_x = statistics.mean(int(r["malformed_extract"]) for r in one)
    bad_u = statistics.mean(int(r["malformed_update"]) for r in one)
    print(f"\n  W0 manipulation check: store mentions the step after its proposal line in {w0:.3f} of dialogues "
          f"({'PASS' if w0 >= MANIP_MIN else 'FAIL, stage UNINFORMATIVE'})")
    print(f"  W1 rejection removed the step from the store, given it was there: {w1:.3f}  (n={len(reply_gone)})")
    print(f"  malformed outputs per dialogue: extractor {bad_x:.2f}, router {bad_u:.2f}")
    w2 = {}
    for arm in ("restated", "neutral"):
        rs = [dias[k][arm] for k in complete]
        w2[arm] = statistics.mean(_b(r["store_mentions_action"]) is True for r in rs)
        d = statistics.mean(int(r["n_delete"]) for r in rs)
        a = statistics.mean(int(r["n_add"]) for r in rs)
        u = statistics.mean(int(r["n_update"]) for r in rs)
        sz = statistics.mean(int(r["store_size"]) for r in rs)
        print(f"  W2 {arm:9} final store mentions the rejected step: {w2[arm]:.3f}   "
              f"ADD/UPDATE/DELETE per dialogue {a:.2f}/{u:.2f}/{d:.2f}   store size {sz:.1f}")

    def p_arm(keys, arm):
        vals = [_b(dias[k][arm]["included"]) for k in keys if _b(dias[k][arm]["included"]) is not None]
        return statistics.mean(vals) if vals else float("nan")

    pr, pn = p_arm(complete, "restated"), p_arm(complete, "neutral")
    d0 = pr - pn
    rng = random.Random(0)
    boots = []
    for _ in range(B):
        sample = [complete[rng.randrange(len(complete))] for _ in complete]
        boots.append(p_arm(sample, "restated") - p_arm(sample, "neutral"))
    boots.sort()
    lo, hi = boots[int(0.025 * B)], boots[int(0.975 * B) - 1]
    print(f"\n  D  rejected-step inclusion on the real store, n = {len(complete)}: "
          f"restated {pr:.3f}  neutral {pn:.3f}  Delta_real {d0:+.3f}  [{lo:+.3f}, {hi:+.3f}]")
    ref = e29_reference(decider, complete)
    for X in ("delete", "addonly", "full"):
        if ref[X]:
            print(f"     E29 oracle {X:8} on the same {ref[X]['n']} dialogues: restated {ref[X]['restated']:.3f}  "
                  f"neutral {ref[X]['neutral']:.3f}  Delta {ref[X]['delta']:+.3f}")

    if w0 < MANIP_MIN:
        verdict = "UNINFORMATIVE (manipulation check failed)"
    elif void:
        verdict = "VOID (decider validity failed)"
    elif d0 >= 0.15 and lo > 0:
        verdict = "REAL-STORE EFFECT"
    elif abs(d0) < 0.05 and -0.15 <= lo and hi <= 0.15:
        verdict = "NULL"
    else:
        verdict = "PARTIAL"
    print(f"\n  VERDICT: {verdict}")
    out = {"extractor": extractor, "decider": decider, "n": len(complete), "w0": w0, "w1": w1,
           "w2": w2, "malformed_extract": bad_x, "malformed_update": bad_u,
           "p_restated": pr, "p_neutral": pn, "delta_real": d0, "ci": [lo, hi],
           "e29_ref": ref, "verdict": verdict}
    with open(f"results/e29d_{slug(extractor)}_{slug(decider)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29d_{slug(extractor)}_{slug(decider)}_summary.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", required=True)
    ap.add_argument("--decider", required=True)
    a = ap.parse_args()
    main(a.extractor, a.decider)
