"""e16_analysis.py: reader for the E16 zombie screen. Fixed before any call.

Per (model, policy): include rate per status; paired contrasts per constraint
(each constraint is seen once under every status) with INSTANCE-level
sign-flip permutation and instance-level bootstrap; parse rate; and, for a
budgeted policy, include rate conditional on realised exposure.

Run:  python e16_analysis.py --model qwen2.5:3b-instruct --policy full
"""
import argparse
import csv
import glob
import random
import statistics

from experiment import show

SEED = 20260903
PERM_REPS = 20_000
BOOT_REPS = 2_000
CONTRASTS = [("never", "rejected"), ("proposed", "rejected"),
             ("rejected", "accepted"), ("never", "proposed"), ("never", "accepted")]


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model, policy):
    rows = []
    for p in sorted(glob.glob(f"results/e16_{slug(model)}_{slug(policy)}_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    return rows


def by_constraint(rows):
    """{instance: [{status: included_bool_or_None, ...} per constraint]}."""
    units = {}
    for r in rows:
        key = (r["instance"], r["constraint"])
        inc = None if r["parsed"] != "True" else (r["included"] == "True")
        units.setdefault(key, {})[r["status"]] = inc
    clusters = {}
    for (inst, _), u in units.items():
        clusters.setdefault(inst, []).append(u)
    return clusters


def paired_contrast(clusters, a, b, reps=PERM_REPS, seed=SEED):
    """Mean of (b - a) over constraints that have both; cluster inference."""
    per = {}
    for inst, units in clusters.items():
        ds = [int(u[b]) - int(u[a]) for u in units
              if u.get(a) is not None and u.get(b) is not None]
        if ds:
            per[inst] = ds
    flat = [d for ds in per.values() for d in ds]
    n = len(flat)
    if n == 0:
        return None
    obs = sum(flat) / n
    rng = random.Random(seed)
    hits = 0
    for _ in range(reps):
        tot = 0
        for ds in per.values():
            tot += (-1 if rng.random() < 0.5 else 1) * sum(ds)
        if abs(tot / n) >= abs(obs) - 1e-12:
            hits += 1
    p = (hits + 1) / (reps + 1)
    keys = list(per)
    boots = []
    for _ in range(BOOT_REPS):
        pick = [per[keys[rng.randrange(len(keys))]] for _ in keys]
        f = [d for ds in pick for d in ds]
        boots.append(sum(f) / len(f))
    boots.sort()
    ci = (boots[int(0.025 * BOOT_REPS)], boots[int(0.975 * BOOT_REPS)])
    return {"diff": obs, "p": p, "ci": ci, "pos": sum(d > 0 for d in flat),
            "neg": sum(d < 0 for d in flat), "n": n}


def analyse(model, policy):
    rows = load(model, policy)
    if not rows:
        print(f"no rows for {model} / {policy}")
        return
    print(f"=== E16 zombie screen: {model}, policy {policy}, {len(rows)} unit rows ===\n")
    parsed = [r for r in rows if r["parsed"] == "True"]
    print(f"  parse rate {len(parsed) / len(rows):.3f}   "
          f"mean actions per plan {statistics.mean(int(r['n_actions']) for r in parsed):.2f}   "
          f"ready=true {statistics.mean(r['ready'] == 'True' for r in parsed):.3f}\n")
    table = []
    for st in ("accepted", "proposed", "rejected", "never"):
        rs = [r for r in parsed if r["status"] == st]
        table.append({"status": st, "n": len(rs),
                      "included": round(statistics.mean(r["included"] == "True" for r in rs), 3)})
    show(table, ["status", "n", "included"])
    clusters = by_constraint(rows)
    print()
    out = []
    for a, b in CONTRASTS:
        c = paired_contrast(clusters, a, b)
        if c:
            out.append({"contrast": f"{b} - {a}", "n": c["n"],
                        "diff": f"{c['diff']:+.4f}", "pos/neg": f"{c['pos']}/{c['neg']}",
                        "cluster p": f"{c['p']:.4f}",
                        "95% CI": f"[{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}]"})
    show(out, ["contrast", "n", "diff", "pos/neg", "cluster p", "95% CI"])
    if policy != "full":
        print("\n  conditional on realised exposure:")
        exp = []
        for st in ("accepted", "proposed", "rejected"):
            for e in sorted({r["exposure"] for r in parsed if r["status"] == st}):
                rs = [r for r in parsed if r["status"] == st and r["exposure"] == e]
                exp.append({"status": st, "exposure": e, "n": len(rs),
                            "included": round(statistics.mean(r["included"] == "True" for r in rs), 3)})
        show(exp, ["status", "exposure", "n", "included"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--policy", default="full")
    a = ap.parse_args()
    analyse(a.model, a.policy)
