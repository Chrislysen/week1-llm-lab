"""e16_menu_analysis.py: reader for the E16 menu diagnostic.

FIXED BEFORE THE FIRST OUTCOME WAS READ. Applies the read rule declared in
docs/protocols/E16-menu-diagnostic.md and prints the verdict it implies. It
has no branch for "interesting but not covered by the rule".

The `base` arm is not re-run: it IS E16 stage 1, read from
results/e16_<model>_full_o0.csv, whose prompt is byte-identical to this
diagnostic's base arm (test_base_arm_is_the_frozen_instruction_verbatim).

Run:  python e16_menu_analysis.py --model qwen2.5:3b-instruct
"""
import argparse
import csv
import os
import random
import statistics

from experiment import show

SEED = 20260906
BOOT_REPS = 2_000
STATUSES = ("accepted", "proposed", "rejected", "never")

#: from the read rule, fixed before any call
SUPPORT_RATIO = 0.60
REFUTE_RATIO = 0.85
VOID_PARSE = 0.95
VOID_ACCEPTED = 0.80
UNINFORMATIVE_PLAN_GROWTH = 1.25


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model, arm):
    """Rows for one arm, normalised. `base` comes from the E16 stage-1 file."""
    if arm == "base":
        path = f"results/e16_{slug(model)}_full_o0.csv"
        vocab = 6
    else:
        path = f"results/e16menu_{slug(model)}_{arm}_o0.csv"
        vocab = None
    if not os.path.exists(path):
        return None
    rows = []
    for r in csv.DictReader(open(path, newline="")):
        rows.append({
            "instance": r["instance"], "constraint": r["constraint"],
            "status": r["status"], "parsed": r["parsed"] == "True",
            "included": r["included"] == "True",
            "n_actions": int(r["n_actions"]) if r["n_actions"] else None,
            "vocab_size": vocab if vocab else int(r["vocab_size"]),
            "n_extra": int(r["n_extra_included"]) if r.get("n_extra_included") else 0,
        })
    return rows


def rate(rows, status):
    rs = [r for r in rows if r["status"] == status and r["parsed"]]
    return (statistics.mean(r["included"] for r in rs), len(rs)) if rs else (None, 0)


def boot_ci(rows, status, reps=BOOT_REPS, seed=SEED):
    """Instance-clustered bootstrap CI for one status's include rate."""
    by_inst = {}
    for r in rows:
        if r["status"] == status and r["parsed"]:
            by_inst.setdefault(r["instance"], []).append(r["included"])
    insts = list(by_inst)
    if not insts:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        draw = [v for _ in insts for v in by_inst[rng.choice(insts)]]
        means.append(statistics.mean(draw))
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps)]


def describe(model, arm, rows):
    ok = [r for r in rows if r["parsed"]]
    parse = len(ok) / len(rows)
    plan = statistics.mean(r["n_actions"] for r in ok)
    vocab = statistics.mean(r["vocab_size"] for r in ok)
    extra = statistics.mean(r["n_extra"] for r in ok)
    print(f"\n=== {model}, arm {arm}, {len(rows)} unit rows ===\n")
    print(f"  parse rate {parse:.3f}   mean |plan| {plan:.2f}   "
          f"mean |vocab| {vocab:.2f}   menu chance {plan / vocab:.3f}   "
          f"distractors used {extra:.2f}")
    table = []
    for st in STATUSES:
        m, n = rate(rows, st)
        ci = boot_ci(rows, st)
        table.append({"status": st, "n": n,
                      "included": None if m is None else round(m, 3),
                      "95% CI": None if ci is None else
                      f"[{ci[0]:.3f}, {ci[1]:.3f}]"})
    show(table, ["status", "n", "included", "95% CI"])
    return {"parse": parse, "plan": plan, "vocab": vocab, "extra": extra,
            "never": rate(rows, "never")[0], "accepted": rate(rows, "accepted")[0]}


def verdict(model, base, wide):
    print(f"\n=== READ RULE (declared 2026-09-06), {model} ===\n")
    if wide is None:
        print("  wide arm absent; no verdict")
        return
    if wide["parse"] < VOID_PARSE or wide["accepted"] < VOID_ACCEPTED:
        print(f"  wide arm VOID: parse {wide['parse']:.3f} (need >= {VOID_PARSE}), "
              f"accepted {wide['accepted']:.3f} (need >= {VOID_ACCEPTED})")
        return
    growth = wide["plan"] / base["plan"]
    print(f"  base never {base['never']:.3f}   wide never {wide['never']:.3f}   "
          f"ratio {wide['never'] / base['never']:.3f}")
    print(f"  support if <= {SUPPORT_RATIO * base['never']:.3f}   "
          f"refute if >= {REFUTE_RATIO * base['never']:.3f}")
    print(f"  mean |plan| {base['plan']:.2f} -> {wide['plan']:.2f} "
          f"(x{growth:.2f}; uninformative if > {UNINFORMATIVE_PLAN_GROWTH})")
    if growth > UNINFORMATIVE_PLAN_GROWTH:
        print("\n  VERDICT: UNINFORMATIVE -- the plan scaled with the menu, "
              "so the 1/|vocab| arithmetic does not apply.")
        return
    if wide["never"] <= SUPPORT_RATIO * base["never"]:
        v = "H_menu SUPPORTED -- the never rate is a menu-selection rate."
    elif wide["never"] >= REFUTE_RATIO * base["never"]:
        v = "H_menu REFUTED, H_base supported -- the never rate is a content judgement."
    else:
        v = "AMBIGUOUS -- recorded as ambiguous, per the declared rule."
    print(f"\n  VERDICT: {v}")
    if wide["extra"] < 0.1:
        print("  CAVEAT: distractors were almost never chosen; the menu did not "
              "widen in the model's eyes and the test is weak.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    a = ap.parse_args()
    summaries = {}
    for arm in ("narrow", "base", "wide"):
        rows = load(a.model, arm)
        if rows is None:
            print(f"\n=== {a.model}, arm {arm}: not run ===")
            continue
        summaries[arm] = describe(a.model, arm, rows)
    if "base" in summaries:
        verdict(a.model, summaries["base"], summaries.get("wide"))
        if "narrow" in summaries:
            n, b = summaries["narrow"]["never"], summaries["base"]["never"]
            print(f"\n  secondary (direction only): narrow never {n:.3f} vs "
                  f"base {b:.3f} -- {'UP' if n > b else 'DOWN or FLAT'}, "
                  f"H_menu predicts UP")
