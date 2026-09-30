"""e29a_analysis.py: read E29-A by the rule declared in docs/protocols/E29A-at-issue.md.
Zero model calls.

Per decider, neutral arm, rejected-step inclusion P(cell), complete-case over all
fifteen cells, paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %).
Cell classes against sentence_short: G = P(cell) - P(sentence_short); FAILS if G >= 0.15
with an interval excluding 0, HONOURED if G's upper bound < 0.15, UNCLEAR otherwise.

H1, attachment or the verb (E29-S's own claim): the class of status_short, a verb-less
status line in its own item.
    HONOURED -> ATTACHMENT MATTERS (a verb-less line is read when it has its own item)
    FAILS    -> THE VERB EXPLAINS IT (a verb-less line fails even in its own item)
    UNCLEAR  -> UNSETTLED
H2, at-issueness (sentence-medial pair): AM = P(arc_medial) - P(main_medial).
    UNTESTABLE          main_medial is not HONOURED
    AT-ISSUE GATES      AM >= 0.15 with an interval excluding 0
    REVERSED            AM <= -0.15 with an interval excluding 0
    NO AT-ISSUE EFFECT  AM's interval lies inside (-0.15, 0.15)
    UNCLEAR             otherwise
The cell classes describe; they do not change H1 or H2's class except through the
main_medial gate. Secondary contrasts are two-sided (EFFECT / NONE / UNCLEAR).

    python e29a_analysis.py --all
"""
import argparse
import csv
import glob
import json
import os
import random
import statistics
from collections import defaultdict

from lineage_e29a import CELLS

B, SESOI = 2000, 0.15
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct", "aya-expanse:8b")
PAIRS = {"AM": ("arc_medial", "main_medial"), "AT": ("appositive", "coordination"),
         "PAREN": ("parenthetical", "bare_second"), "VT": ("tag_prefix", "verbal_tag"),
         "POS": ("tag_prefix", "tag_suffix"), "POP": ("paren_prefix", "paren_suffix"),
         "BRP": ("tag_prefix", "paren_prefix"), "BRS": ("tag_suffix", "paren_suffix"),
         "RSN": ("sentence_short", "sentence"), "SRC": ("status_short", "status_long"),
         "PWV": ("paren_suffix", "parenthetical")}
ANCHORS = {"llama3.2:3b": {"sentence": 0.156, "tag_prefix": 0.594, "status_long": 0.198, "paren_suffix": 0.250},
           "qwen2.5:14b-instruct": {"sentence": 0.052, "tag_prefix": 0.323, "status_long": 0.031, "paren_suffix": 0.135},
           "aya-expanse:8b": {"sentence": 0.156, "tag_prefix": 0.479, "status_long": 0.031}}


def slug(s):
    return s.replace(".", "").replace(":", "-")


def ci(v):
    v = sorted(v)
    return v[int(0.025 * B)], v[int(0.975 * B) - 1]


def two_sided(d, lo, hi):
    if abs(d) >= SESOI and (lo > 0 or hi < 0):
        return "EFFECT"
    if -SESOI < lo and hi < SESOI:
        return "NONE"
    return "UNCLEAR"


def recognition(model):
    p = f"results/e29a_recognition_{slug(model)}_summary.json"
    return json.load(open(p, encoding="utf-8"))["verdict"] if os.path.exists(p) else "NOT RUN"


def main(model):
    seen = {}
    for f in sorted(glob.glob(f"results/e29a_{slug(model)}_r*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    if not rows:
        print("no E29-A rows for", model)
        return None
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    rej = defaultdict(dict)
    for r in rows:
        if r["status"] == "rejected" and r["arm"] == "neutral":
            rej[(r["instance"], r["rotation"])][r["design"]] = r["included"]
    attempted = {(r["instance"], r["rotation"]) for r in rows}
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
    p2_miss = [st for st in ("accepted", "proposed") if max(ctrl[st].values()) - min(ctrl[st].values()) > 0.10]

    def p(ks, c):
        return statistics.mean(rej[k][c] for k in ks)

    P = {c: p(keys, c) for c in CELLS}
    rng = random.Random(0)
    bootG, bootS, bootD = defaultdict(list), defaultdict(list), defaultdict(list)
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        ps = {c: p(s, c) for c in CELLS}
        for c in CELLS:
            bootG[c].append(ps[c] - ps["sentence_short"])
            bootS[c].append(ps[c] - ps["sentence"])
        for name, (a, b) in PAIRS.items():
            bootD[name].append(ps[a] - ps[b])
        bootD["POSxPOP"].append((ps["tag_prefix"] - ps["tag_suffix"]) - (ps["paren_prefix"] - ps["paren_suffix"]))
    cls = {}
    for c in CELLS:
        g = P[c] - P["sentence_short"]
        lo, hi = ci(bootG[c])
        slo, shi = ci(bootS[c])
        cls[c] = {"G": g, "ci": [lo, hi], "G_vs_sentence": P[c] - P["sentence"], "ci_vs_sentence": [slo, shi],
                  "class": "FAILS" if (g >= SESOI and lo > 0) else "HONOURED" if hi < SESOI else "UNCLEAR"}
    contrasts = {}
    for name, (a, b) in PAIRS.items():
        d = P[a] - P[b]
        lo, hi = ci(bootD[name])
        contrasts[name] = {"d": d, "ci": [lo, hi], "class": two_sided(d, lo, hi)}
    ix = (P["tag_prefix"] - P["tag_suffix"]) - (P["paren_prefix"] - P["paren_suffix"])
    lo, hi = ci(bootD["POSxPOP"])
    contrasts["POSxPOP"] = {"d": ix, "ci": [lo, hi], "class": two_sided(ix, lo, hi)}
    h1 = {"HONOURED": "ATTACHMENT MATTERS", "FAILS": "THE VERB EXPLAINS IT"}.get(cls["status_short"]["class"], "UNSETTLED")
    am = contrasts["AM"]
    if cls["main_medial"]["class"] != "HONOURED":
        h2 = "UNTESTABLE"
    elif am["d"] >= SESOI and am["ci"][0] > 0:
        h2 = "AT-ISSUE GATES"
    elif am["d"] <= -SESOI and am["ci"][1] < 0:
        h2 = "REVERSED"
    elif -SESOI < am["ci"][0] and am["ci"][1] < SESOI:
        h2 = "NO AT-ISSUE EFFECT"
    else:
        h2 = "UNCLEAR"
    anchors = ANCHORS.get(model, {})
    p1 = {c: (round(P[c], 3), anchors[c], abs(P[c] - anchors[c]) <= 0.10) for c in anchors}
    status = "VOID" if void else ("INCOMPLETE" if len(attempted) < 96 else "FINAL")
    print(f"=== E29-A read: {model}  (n = {len(keys)} complete of {len(attempted)} attempted; {status}) ===")
    for c in CELLS:
        extra = f"   (earlier {anchors[c]}{'' if p1[c][2] else ', P1 MISS'})" if c in anchors else ""
        g = cls[c]
        print(f"  {c:15} {P[c]:.3f}   G {g['G']:+.3f} [{g['ci'][0]:+.3f}, {g['ci'][1]:+.3f}]  {g['class']}{extra}")
    for name, (a, b) in PAIRS.items():
        c = contrasts[name]
        print(f"  {name:5} {a} - {b}: {c['d']:+.3f} [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}]  {c['class']}")
    c = contrasts["POSxPOP"]
    print(f"  POSxPOP (POS - POP, position by bracket): {c['d']:+.3f} [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}]  {c['class']}")
    print("  control inclusion across cells: " + "; ".join(
        f"{st} {min(v.values()):.3f}-{max(v.values()):.3f}" for st, v in ctrl.items())
        + (f"   P2 MISS: {p2_miss}" if p2_miss else "   P2 holds"))
    rec = recognition(model)
    print(f"  H1 ({model}): {h1}")
    print(f"  H2 ({model}): {h2}" + (f"   (recognition condition: {rec})" if h2 == "AT-ISSUE GATES" else ""))
    print(f"  STATUS ({model}): {status}" + (f" {void}" if void else ""))
    out = {"model": model, "n": len(keys), "attempted": len(attempted), "status": status, "void": void,
           "p": P, "cells": cls, "contrasts": contrasts, "h1": h1, "h2": h2, "recognition": rec,
           "p1": p1, "control": ctrl, "p2_miss": p2_miss}
    with open(f"results/e29a_{slug(model)}_summary.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


def programme(outs):
    """Over deciders whose read is FINAL (not VOID, not INCOMPLETE); needs at least two."""
    ok = [o for o in outs if o and o["status"] == "FINAL"]
    if len(ok) < 2:
        return {"h1": "NO PROGRAMME READING (fewer than two final deciders)", "h2": "NO PROGRAMME READING", "n": len(ok)}
    h1s = [o["h1"] for o in ok]
    if h1s.count("ATTACHMENT MATTERS") >= 2 and "THE VERB EXPLAINS IT" not in h1s:
        h1 = "ATTACHMENT MATTERS: the structural claim survives"
    elif h1s.count("THE VERB EXPLAINS IT") >= 2 and "ATTACHMENT MATTERS" not in h1s:
        h1 = "THE VERB EXPLAINS IT: E29-S's pattern is the missing verb; the conjunction claim is withdrawn"
    else:
        h1 = "MIXED: " + ", ".join(f"{o['model']} {o['h1']}" for o in ok)
    gates = [o for o in ok if o["h2"] == "AT-ISSUE GATES" and o["recognition"] == "CONDITION MET"]
    if len(gates) >= 2 and not any(o["h2"] == "REVERSED" for o in ok):
        h2 = "AT-ISSUE ACCOUNT SUPPORTED"
    elif sum(o["h2"] == "NO AT-ISSUE EFFECT" and all(o["cells"][c]["class"] == "HONOURED"
                                                     for c in ("arc_medial", "parenthetical", "verbal_tag"))
             for o in ok) >= 2:
        h2 = "VERB ACCOUNT SUPPORTED"
    elif sum(o["h2"] == "UNTESTABLE" for o in ok) >= 2:
        h2 = "AGAINST BOTH (the main-clause twin itself is not honoured)"
    else:
        h2 = "MIXED: " + ", ".join(f"{o['model']} {o['h2']}" for o in ok)
    return {"h1": h1, "h2": h2, "n": len(ok)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    outs = [main(m) for m in (DECIDERS if a.all or not a.model else (a.model,))]
    if a.all:
        prog = programme(outs)
        print(f"\n=== E29-A programme reading ({prog['n']} final deciders) ===\n  H1: {prog['h1']}\n  H2: {prog['h2']}")
        json.dump(prog, open("results/e29a_programme.json", "w", encoding="utf-8"), indent=1)
