"""e17_analysis.py: reader for E17. Applies the declared read rule mechanically.

The rule is fixed in docs/protocols/E17-menu-law.md and reproduced here. There
is deliberately no branch for "interesting but not covered by the rule": a
result outside the thresholds is AMBIGUOUS and is printed as AMBIGUOUS.

The `free` cells at |vocab| 6 and 12 are NOT re-run -- they are E16 stage 1 and
the E16 menu diagnostic's wide arm, whose prompts are byte-identical to this
study's free/6 and free/12 (enforced by test_e17_menu_law.py and
test_e16_menu_diagnostic.py).

Run:  python e17_analysis.py --model qwen2.5:3b-instruct
"""
import argparse
import csv
import math
import os
import random
import statistics

from experiment import show

SEED = 20260906
BOOT_REPS = 2_000
STATUSES = ("accepted", "proposed", "rejected", "never")

#: declared read rule
PIN_N = 4
PIN_PLAN_TOLERANCE = 0.15          # (b) pin4 |plan| within +/-15% of 4.0
ESTABLISH_FALL = 2.5               # (c) never falls >= 2.5x from |vocab| 6 to 24
REFUTE_FALL = 1.5                  # < 1.5x with |plan| fixed => menu account dead
VOID_PARSE = 0.95


def slug(s):
    return s.replace(".", "").replace(":", "-")


def path_for(model, vocab, length):
    """free/6 and free/12 come from the earlier studies, by design."""
    m = slug(model)
    if length == "free" and vocab == 6:
        return f"results/e16_{m}_full_o0.csv", 6
    if length == "free" and vocab == 12:
        return f"results/e16menu_{m}_wide_o0.csv", 12
    return f"results/e17_{m}_v{vocab}_{length}_o0.csv", vocab


def load(model, vocab, length):
    path, v = path_for(model, vocab, length)
    if not os.path.exists(path):
        return None
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        rows.append({"instance": r["instance"], "rotation": r["rotation"],
                     "status": r["status"], "parsed": r["parsed"] == "True",
                     "included": r["included"] == "True",
                     "n_actions": int(r["n_actions"]) if r["n_actions"] else None,
                     "vocab": v})
    return rows


def boot_ci(rows, status, reps=BOOT_REPS, seed=SEED):
    by = {}
    for r in rows:
        if r["status"] == status and r["parsed"]:
            by.setdefault(r["instance"], []).append(r["included"])
    insts = list(by)
    if not insts:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        draw = [v for _ in insts for v in by[rng.choice(insts)]]
        means.append(statistics.mean(draw))
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps)]


def cell(model, vocab, length):
    rows = load(model, vocab, length)
    if rows is None:
        return None
    ok = [r for r in rows if r["parsed"]]
    dia = {(r["instance"], r["rotation"]): r["n_actions"] for r in ok}
    plans = list(dia.values())
    d = {"vocab": vocab, "length": length, "n": len(rows),
         "parse": len(ok) / len(rows), "plan": statistics.mean(plans),
         "exact4": sum(p == PIN_N for p in plans) / len(plans)}
    d["chance"] = d["plan"] / vocab
    for st in STATUSES:
        rs = [r for r in ok if r["status"] == st]
        d[st] = sum(r["included"] for r in rs) / len(rs) if rs else None
    d["never_ci"] = boot_ci(rows, "never")
    return d


def verdict(model, cells):
    print(f"\n=== READ RULE (declared 2026-09-06), {model} ===\n")
    need = [(6, "pin4"), (24, "pin4")]
    if any(cells.get(k) is None for k in need):
        print("  pin4 endpoints missing; no verdict")
        return
    pins = [cells[(v, "pin4")] for v in (6, 12, 24) if cells.get((v, "pin4"))]
    frees = [cells[(v, "free")] for v in (6, 12, 24) if cells.get((v, "free"))]

    if any(c["parse"] < VOID_PARSE for c in cells.values() if c):
        print("  a cell is VOID on parse rate")
        return

    lo, hi = PIN_N * (1 - PIN_PLAN_TOLERANCE), PIN_N * (1 + PIN_PLAN_TOLERANCE)
    b = all(lo <= c["plan"] <= hi for c in pins)
    plans_str = ", ".join(f"{c['plan']:.2f}" for c in pins)
    print(f"  (b) pin4 |plan| within [{lo:.2f}, {hi:.2f}] in every cell: "
          f"{'YES' if b else 'NO'}  ({plans_str})")
    if not b:
        print("\n  VERDICT: VOID -- the model did not obey the length instruction.")
        return

    if len(frees) >= 3:
        pl = [c["plan"] for c in frees]
        a = pl[0] < pl[1] < pl[2]
        print(f"  (a) free |plan| rises monotonically 6<12<24: "
              f"{'YES' if a else 'NO'}  ({', '.join(f'{p:.2f}' for p in pl)})")
    else:
        a = None
        print("  (a) free arm incomplete -- not evaluated")

    n6, n24 = cells[(6, "pin4")]["never"], cells[(24, "pin4")]["never"]
    fall = n6 / n24
    print(f"  (c) pin4 never falls 6->24 by >= {ESTABLISH_FALL}x: "
          f"{n6:.3f} -> {n24:.3f} = {fall:.2f}x  "
          f"{'YES' if fall >= ESTABLISH_FALL else 'NO'}")
    print(f"      (chance falls {cells[(6,'pin4')]['chance'] / cells[(24,'pin4')]['chance']:.2f}x)")

    if fall >= ESTABLISH_FALL and b and (a or a is None):
        v = "ELASTICITY ESTABLISHED"
    elif fall < REFUTE_FALL:
        v = "MENU ACCOUNT REFUTED -- the line dies here"
    else:
        v = "AMBIGUOUS -- recorded as ambiguous, per the declared rule"
    print(f"\n  VERDICT: {v}")

    print("\n  post-hoc, NOT declared: never / chance by cell, and the implied exponent")
    for c in pins:
        print(f"    pin4 |v|={c['vocab']:2}  chance {c['chance']:.3f}  "
              f"never {c['never']:.3f}  ratio {c['never']/c['chance']:.2f}")
    e = math.log(fall) / math.log(cells[(6, 'pin4')]['chance'] / cells[(24, 'pin4')]['chance'])
    print(f"    never ~ chance^{e:.2f}   (1.00 = H_menu, 0.00 = H_base)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    a = ap.parse_args()
    cells = {}
    table = []
    for length in ("free", "pin4"):
        for vocab in (6, 12, 24):
            c = cell(a.model, vocab, length)
            cells[(vocab, length)] = c
            if c:
                table.append({
                    "length": length, "|vocab|": vocab, "parse": round(c["parse"], 3),
                    "|plan|": round(c["plan"], 2), "exact4": round(c["exact4"], 3),
                    "chance": round(c["chance"], 3),
                    "accepted": round(c["accepted"], 3),
                    "rejected": round(c["rejected"], 3),
                    "never": round(c["never"], 3),
                    "never 95% CI": f"[{c['never_ci'][0]:.3f}, {c['never_ci'][1]:.3f}]",
                })
    print(f"\n=== E17 menu law: {a.model} ===\n")
    show(table, ["length", "|vocab|", "parse", "|plan|", "exact4", "chance",
                 "accepted", "rejected", "never", "never 95% CI"])
    verdict(a.model, cells)
