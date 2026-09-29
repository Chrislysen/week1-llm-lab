"""e29r_analysis.py: read E29-R by the rule declared in docs/protocols/E29R-formats.md.
Zero model calls.

For each decider and each list format, the E29-S 2x2 over the neutral arm:

                     own item          same item
    proposition      addonly           addonly_merged
    attribute        addonly_meta      addonly_flag

and E29-S's four contrasts, with E29-S's bootstrap (paired over dialogues,
seed 0, B = 2000). The markdown column is read from E29-S's own summary.

A contrast REACHES when it is >= 0.15 and its interval excludes zero.
CONJUNCTION (the E29-S pattern) holds for a format when S_flag and S_form_same
both reach and neither S_merge nor S_form_own does.

    GENERAL            CONJUNCTION in all three new formats
    FORMAT-DEPENDENT   CONJUNCTION in one or two
    MARKDOWN-SPECIFIC  CONJUNCTION in none

Run:  python e29r_analysis.py --model llama3.2:3b
      python e29r_analysis.py --all
"""
import argparse
import csv
import glob
import json
import random
import statistics
from collections import defaultdict

from lineage_e29r import DESIGNS_S, RUN_FORMATS

B = 2000
SESOI = 0.15
CONTRASTS = {
    "S_merge": ("addonly_merged", "addonly", "separation, proposition held"),
    "S_flag": ("addonly_flag", "addonly_meta", "separation, attribute held"),
    "S_form_own": ("addonly_meta", "addonly", "form, own item held"),
    "S_form_same": ("addonly_flag", "addonly_merged", "form, same item held"),
}
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct")


def slug(s):
    return s.replace(".", "").replace(":", "-")


def load(model):
    seen = {}
    for f in sorted(glob.glob(f"results/e29r_{slug(model)}_*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["format"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    for r in rows:
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["parsed"] = r["parsed"] == "True"
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    return rows


def reaches(g, lo, hi):
    return g >= SESOI and (lo > 0 or hi < 0)


def read_format(rows, fmt):
    """The E29-S read for one format: cells, contrasts, CIs, controls, pattern."""
    rs = [r for r in rows if r["format"] == fmt]
    rej = defaultdict(dict)
    for r in rs:
        if r["status"] == "rejected":
            rej[(r["instance"], r["rotation"])][(r["design"], r["arm"])] = r["included"]
    keys = [k for k, v in rej.items()
            if all(v.get((X, a)) is not None for X in DESIGNS_S for a in ("restated", "neutral"))]
    void = []
    for X in DESIGNS_S:
        for a in ("restated", "neutral"):
            c = [r for r in rs if r["design"] == X and r["arm"] == a]
            parse = statistics.mean(r["parsed"] for r in c) if c else 0.0
            lens = [r["n_actions"] for r in c if r["parsed"]]
            mp = statistics.mean(lens) if lens else float("nan")
            if parse < 0.95 or not (3.9 <= mp <= 4.1):
                void.append((X, a, round(parse, 3), round(mp, 2)))

    def cell(ks, X, a):
        v = [rej[k][(X, a)] for k in ks]
        return statistics.mean(v) if v else float("nan")

    def contrasts(ks):
        return {n: cell(ks, a, "neutral") - cell(ks, b, "neutral") for n, (a, b, _) in CONTRASTS.items()}

    p = {f"{X}|{a}": cell(keys, X, a) for X in DESIGNS_S for a in ("restated", "neutral")}
    g = contrasts(keys)
    rng = random.Random(0)
    boots = defaultdict(list)
    for _ in range(B):
        sample = [keys[rng.randrange(len(keys))] for _ in keys]
        for n, v in contrasts(sample).items():
            boots[n].append(v)
    ci = {n: (sorted(v)[int(0.025 * B)], sorted(v)[int(0.975 * B) - 1]) for n, v in boots.items()}
    # control (P2): never-mentioned and accepted inclusion across the four designs, neutral arm
    ctrl = {}
    for st in ("never", "accepted"):
        vals = []
        for X in DESIGNS_S:
            v = [r["included"] for r in rs if r["design"] == X and r["arm"] == "neutral" and r["status"] == st and r["parsed"]]
            vals.append(statistics.mean(v) if v else float("nan"))
        ctrl[st] = (min(vals), max(vals))
    conj = (reaches(g["S_flag"], *ci["S_flag"]) and reaches(g["S_form_same"], *ci["S_form_same"])
            and not reaches(g["S_merge"], *ci["S_merge"]) and not reaches(g["S_form_own"], *ci["S_form_own"]))
    return {"format": fmt, "n": len(keys), "p": p, "g": g, "ci": ci, "void": void,
            "control_range": ctrl, "conjunction": conj and not void}


def markdown_from_e29s(model):
    """E29-S's own read, as the markdown column."""
    try:
        s = json.load(open(f"results/e29s_{slug(model)}_summary.json", encoding="utf-8"))
    except FileNotFoundError:
        return None
    g, ci = s["g"], s["ci_g"]
    conj = (reaches(g["S_flag"], *ci["S_flag"]) and reaches(g["S_form_same"], *ci["S_form_same"])
            and not reaches(g["S_merge"], *ci["S_merge"]) and not reaches(g["S_form_own"], *ci["S_form_own"]))
    return {"format": "markdown (E29-S)", "n": s["n_complete"], "p": s["p"], "g": g,
            "ci": {k: tuple(v) for k, v in ci.items()}, "void": s["void"], "conjunction": conj and not s["void"]}


def main(model):
    rows = load(model)
    if not rows:
        print("no E29-R rows for", model)
        return None
    reads = [read_format(rows, f) for f in RUN_FORMATS]
    md = markdown_from_e29s(model)
    print(f"=== E29-R read: {model} ===")
    for r in ([md] if md else []) + reads:
        print(f"\n  {r['format']}  (n = {r['n']}){'   VOID ' + str(r['void']) if r['void'] else ''}")
        p = r["p"]
        print(f"    {'':12} {'own item':>9} {'same item':>10}")
        print(f"    {'proposition':12} {p['addonly|neutral']:9.3f} {p['addonly_merged|neutral']:10.3f}")
        print(f"    {'attribute':12} {p['addonly_meta|neutral']:9.3f} {p['addonly_flag|neutral']:10.3f}")
        for n in CONTRASTS:
            lo, hi = r["ci"][n]
            print(f"    {n:12} {r['g'][n]:+.3f} [{lo:+.3f}, {hi:+.3f}]{'  reaches' if reaches(r['g'][n], lo, hi) else ''}")
        if "control_range" in r:
            print(f"    control (neutral): never {r['control_range']['never'][0]:.3f}-{r['control_range']['never'][1]:.3f}, "
                  f"accepted {r['control_range']['accepted'][0]:.3f}-{r['control_range']['accepted'][1]:.3f}")
        print(f"    CONJUNCTION: {'yes' if r['conjunction'] else 'no'}")
    k = sum(r["conjunction"] for r in reads)
    complete = all(r["n"] == 96 for r in reads)
    verdict = ("GENERAL" if k == len(reads) else "MARKDOWN-SPECIFIC" if k == 0 else "FORMAT-DEPENDENT")
    if not complete:
        verdict = "INCOMPLETE (" + ", ".join(f"{r['format']} n={r['n']}" for r in reads) + ") -- provisional: " + verdict
    print(f"\n  VERDICT ({model}): {verdict}   [conjunction in {k} of {len(reads)} new formats]")
    out = {"model": model, "verdict": verdict, "conjunction_formats": k, "complete": complete,
           "reads": reads, "markdown": md}
    with open(f"results/e29r_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"  wrote results/e29r_{slug(model)}_summary.json")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    for m in (DECIDERS if a.all or not a.model else (a.model,)):
        main(m)
