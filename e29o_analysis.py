"""e29o_analysis.py: read E29-O by the rule declared in docs/protocols/E29O-order.md.
Zero model calls.

Per decider, neutral arm, inclusion of the rejected proposal's step P(cell) (in `open` the same
step, undecided), complete-case over the twenty cells, paired bootstrap over the 192 dialogues
(seed 0, B = 2000, percentile 95 %).

Cell classes against the reference REF = whichever of sentence_short and withdrawn_post has
the lower P: FAILS if G >= 0.15 with an interval excluding 0, HONOURED if G's upper bound < 0.15,
UNCLEAR otherwise.

Gate O, POS = P(withdrawn_pre) - P(withdrawn_post): ORDER (POS >= 0.15, lower bound > 0),
NO ORDER EFFECT (interval inside (-0.15, 0.15)), REVERSED (POS <= -0.15, upper bound < 0),
UNCLEAR. The accounts are read only under ORDER.

Tests, scaled by each decider's own order effect: D = d - POS/2, bootstrapped jointly.
    T1 temporal cue   RESCUE = P(withdrawn_pre) - P(later_pre); LEN = P(withdrawn_pre) - P(formally_pre).
                      RESCUED: RESCUE's D > 0 and LEN's D < 0.   LENGTH: both D > 0.
                      NOT RESCUED: RESCUE's D < 0, counted only if probe E's end-state
                      condition is MET (else UNINTERPRETABLE).   Otherwise UNCLEAR.
    T3 per marker     m in (label, clause, named), d = P(m_pre) - P(m_post). If m_post FAILS: UNINFORMATIVE;
                      if m_post is UNCLEAR: UNCLEAR. Else BOUND (D > 0), FREE (D < 0, not reversed),
                      REVERSED (d <= -0.15, upper bound < 0), UNCLEAR.
    T4 X first        PX = P(xfirst_pre) - P(xfirst_post): DIRECTION (lower bound > 0),
                      PROXIMITY (upper bound < 0), UNCLEAR.
    T5 field form     FF = P(field_post) - P(withdrawn_post), W = P(open) - P(withdrawn_post),
                      D = FF - W/2: FAILS (D > 0), WORKS (D < 0), UNCLEAR.
    T0 NARR premise   probe E: REFUTED / SUPPORTED / UNCLEAR (e29o_recognition.py).
"D > 0" means the interval of D lies above 0, and "D < 0" below it.

An account is refuted when an interpretable outcome of any test lies outside its predicted
set (PREDICTIONS). The verdict is the one account left; NONE FITS if none is; UNRESOLVED if
more than one is.

    python e29o_analysis.py --all
"""
import argparse
import csv
import glob
import json
import os
import random
import statistics
from collections import defaultdict

from lineage_e29o import CELLS

B, SESOI, N = 2000, 0.15, 192
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct", "aya-expanse:8b")
PAIRS = {"POS": ("withdrawn_pre", "withdrawn_post"), "RESCUE": ("withdrawn_pre", "later_pre"),
         "LEN": ("withdrawn_pre", "formally_pre"), "PL": ("label_pre", "label_post"),
         "PC": ("clause_pre", "clause_post"), "PN": ("named_pre", "named_post"),
         "PX": ("xfirst_pre", "xfirst_post"), "FF": ("field_post", "withdrawn_post"),
         "W": ("open", "withdrawn_post"), "POSL": ("later_pre", "later_post"), "PF": ("field_pre", "field_post"),
         "OPN": ("open", "withdrawn_pre"), "FPP": ("first_pre", "withdrawn_pre"),
         "FPQ": ("first_post", "withdrawn_post"), "FPS": ("first_sentence", "sentence_short")}
SCALED = ("RESCUE", "LEN", "PL", "PC", "PN")
TESTS = ("T1", "label", "clause", "named", "T4", "T5", "T0")
INTERPRETABLE = {"T1": {"RESCUED", "NOT RESCUED", "LENGTH"},
                 "label": {"FREE", "BOUND", "REVERSED", "UNINFORMATIVE"},
                 "clause": {"FREE", "BOUND", "REVERSED", "UNINFORMATIVE"},
                 "named": {"FREE", "BOUND", "REVERSED", "UNINFORMATIVE"},
                 "T4": {"DIRECTION", "PROXIMITY"}, "T5": {"FAILS", "WORKS"}, "T0": {"REFUTED", "SUPPORTED"}}
ANY = None
PREDICTIONS = {   # account: allowed outcomes per test (ANY = no prediction)
    "NARR":   {"T1": {"RESCUED"}, "label": {"BOUND"}, "clause": {"BOUND"}, "named": ANY,
               "T4": {"DIRECTION"}, "T5": {"WORKS"}, "T0": {"SUPPORTED"}},
    "REC":    {"T1": {"NOT RESCUED"}, "label": {"BOUND"}, "clause": {"BOUND"}, "named": {"BOUND"},
               "T4": {"DIRECTION"}, "T5": {"WORKS"}, "T0": ANY},
    "BIND":   {"T1": {"NOT RESCUED"}, "label": {"FREE"}, "clause": {"BOUND"}, "named": {"FREE"},
               "T4": {"DIRECTION"}, "T5": {"WORKS"}, "T0": ANY},
    "CLAUSE": {"T1": {"NOT RESCUED"}, "label": {"BOUND"}, "clause": {"FREE"}, "named": {"FREE"},
               "T4": {"DIRECTION"}, "T5": {"WORKS"}, "T0": ANY},
    "PROX":   {"T1": {"NOT RESCUED"}, "label": {"FREE"}, "clause": {"BOUND"}, "named": {"FREE"},
               "T4": {"PROXIMITY"}, "T5": {"WORKS"}, "T0": ANY},
    "META":   {"T1": {"NOT RESCUED"}, "label": {"UNINFORMATIVE"}, "clause": {"FREE"}, "named": {"FREE"},
               "T4": {"DIRECTION"}, "T5": {"FAILS"}, "T0": ANY},
}


def slug(s):
    return s.replace(".", "").replace(":", "-")


def ci(v):
    v = sorted(v)
    return v[int(0.025 * B)], v[int(0.975 * B) - 1]


def run_files(model):
    fs = glob.glob(f"results/e29o_{slug(model)}_r*.csv")
    return sorted(fs, key=lambda f: int(f.rsplit("_r", 1)[1].split(".")[0]))


def old_rule(s):
    """The draft's recognition condition, kept to show which verdicts depend on the amendment:
    probe K on withdrawn_pre and later_pre, parse >= 0.95, control yes <= 0.20 in both, and
    later_pre recognised no worse than 0.15 below withdrawn_pre."""
    k = s.get("K", {})
    if "hit" not in k:
        return k.get("status", "NOT RUN")
    h = k["hit"]
    if k["min_parse"] < 0.95 or max(h["withdrawn_pre|control"], h["later_pre|control"]) > 0.20:
        return "VOID"
    return "MET" if h["later_pre|rejected"] >= h["withdrawn_pre|rejected"] - 0.15 else "NOT MET"


def recognition(model):
    p = f"results/e29o_recognition_{slug(model)}_summary.json"
    if not os.path.exists(p):
        return {"condition": "NOT RUN", "narr_premise": "NOT READ", "old_rule": "NOT RUN"}
    s = json.load(open(p, encoding="utf-8"))
    e = s.get("E", {})
    return {"condition": e.get("condition", e.get("status", "NOT RUN")),
            "narr_premise": e.get("narr_premise", "NOT READ"), "old_rule": old_rule(s)}


def refuted(account, outcomes):
    pred = PREDICTIONS[account]
    return [t for t in TESTS if outcomes[t] in INTERPRETABLE[t] and pred[t] is not ANY and outcomes[t] not in pred[t]]


def verdict(outcomes):
    alive = [a for a in PREDICTIONS if not refuted(a, outcomes)]
    return alive[0] if len(alive) == 1 else "NONE FITS" if not alive else "UNRESOLVED: " + ", ".join(alive)


def outcomes_of(c, cls, rec_condition, narr_premise):
    """The seven test outcomes from contrasts `c` (each with d, ci and, if scaled, D, Dci) and cell classes."""
    def above(k):
        return c[k]["Dci"][0] > 0

    def below(k):
        return c[k]["Dci"][1] < 0

    if above("RESCUE"):
        t1 = "LENGTH" if above("LEN") else "RESCUED" if below("LEN") else "UNCLEAR"
    elif below("RESCUE"):
        t1 = "NOT RESCUED" if rec_condition == "MET" else "UNINTERPRETABLE"
    else:
        t1 = "UNCLEAR"
    out = {"T1": t1}
    for m, k in (("label", "PL"), ("clause", "PC"), ("named", "PN")):
        post = cls[f"{m}_post"]["class"]
        d, (lo, hi) = c[k]["d"], c[k]["ci"]
        if post == "FAILS":
            out[m] = "UNINFORMATIVE"
        elif post == "UNCLEAR":
            out[m] = "UNCLEAR"
        elif d <= -SESOI and hi < 0:
            out[m] = "REVERSED"
        elif above(k):
            out[m] = "BOUND"
        elif below(k):
            out[m] = "FREE"
        else:
            out[m] = "UNCLEAR"
    lo, hi = c["PX"]["ci"]
    out["T4"] = "DIRECTION" if lo > 0 else "PROXIMITY" if hi < 0 else "UNCLEAR"
    out["T5"] = "FAILS" if c["FF"]["Dci"][0] > 0 else "WORKS" if c["FF"]["Dci"][1] < 0 else "UNCLEAR"
    out["T0"] = narr_premise
    return out


def main(model):
    seen = {}
    for f in run_files(model):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            seen[(r["instance"], r["rotation"], r["design"], r["arm"], r["slot"])] = r
    rows = list(seen.values())
    if not rows:
        print("no E29-O rows for", model)
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
    ref = min(("sentence_short", "withdrawn_post"), key=lambda c: P[c])
    rng = random.Random(0)
    bootG, bootD, bootS = defaultdict(list), defaultdict(list), defaultdict(list)
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        ps = {c: p(s, c) for c in CELLS}
        for c in CELLS:
            bootG[c].append(ps[c] - ps[ref])
        dd = {name: ps[a] - ps[b] for name, (a, b) in PAIRS.items()}
        for name, v in dd.items():
            bootD[name].append(v)
        for name in SCALED:
            bootS[name].append(dd[name] - dd["POS"] / 2)
        bootS["FF"].append(dd["FF"] - dd["W"] / 2)
        bootD["FPI"].append(dd["FPP"] - dd["FPQ"])
    cls = {}
    for c in CELLS:
        g = P[c] - P[ref]
        lo, hi = ci(bootG[c])
        cls[c] = {"G": g, "ci": [lo, hi],
                  "class": "FAILS" if (g >= SESOI and lo > 0) else "HONOURED" if hi < SESOI else "UNCLEAR"}
    con = {}
    for name, (a, b) in PAIRS.items():
        d = P[a] - P[b]
        con[name] = {"d": d, "ci": list(ci(bootD[name]))}
        if name in bootS:
            half = (P["open"] - P["withdrawn_post"]) if name == "FF" else (P["withdrawn_pre"] - P["withdrawn_post"])
            con[name]["D"] = d - half / 2
            con[name]["Dci"] = list(ci(bootS[name]))
    con["FPI"] = {"d": con["FPP"]["d"] - con["FPQ"]["d"], "ci": list(ci(bootD["FPI"]))}
    lo, hi = con["POS"]["ci"]
    pos = con["POS"]["d"]
    gate = ("ORDER" if pos >= SESOI and lo > 0 else "NO ORDER EFFECT" if (-SESOI < lo and hi < SESOI)
            else "REVERSED" if pos <= -SESOI and hi < 0 else "UNCLEAR")
    rec = recognition(model)
    status = "VOID" if void else ("INCOMPLETE" if len(attempted) < N else "FINAL")
    if gate == "ORDER":
        outs = outcomes_of(con, cls, rec["condition"], rec["narr_premise"])
        verd = verdict(outs)
        outs_old = dict(outs)
        if outs["T1"] in ("NOT RESCUED", "UNINTERPRETABLE"):
            outs_old["T1"] = "NOT RESCUED" if rec["old_rule"] == "MET" else "UNINTERPRETABLE"
        verd_old = verdict(outs_old)
        ref_by = {a: refuted(a, outs) for a in PREDICTIONS}
    else:
        outs, verd, verd_old, ref_by = {t: "-" for t in TESTS}, "NOT READ", "NOT READ", {}
    print(f"=== E29-O read: {model}  (n = {len(keys)} complete of {len(attempted)} attempted; {status}) ===")
    print(f"  reference for HONOURED: {ref} ({P[ref]:.3f})")
    for c in CELLS:
        g = cls[c]
        print(f"  {c:15} {P[c]:.3f}   G {g['G']:+.3f} [{g['ci'][0]:+.3f}, {g['ci'][1]:+.3f}]  {g['class']:9}"
              f"  (never-mentioned {ctrl['never'][c]:.3f})")
    for name, v in con.items():
        a, b = PAIRS.get(name, ("(first_pre-withdrawn_pre)", "(first_post-withdrawn_post)"))
        extra = f"   D {v['D']:+.3f} [{v['Dci'][0]:+.3f}, {v['Dci'][1]:+.3f}]" if "D" in v else ""
        print(f"  {name:6} {a} - {b}: {v['d']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}]{extra}")
    print("  control inclusion across cells: " + "; ".join(
        f"{st} {min(v.values()):.3f}-{max(v.values()):.3f}" for st, v in ctrl.items())
        + (f"   P2 MISS: {p2_miss}" if p2_miss else "   P2 holds"))
    print(f"  GATE O ({model}): {gate}")
    print("  outcomes: " + "   ".join(f"{t} {outs[t]}" for t in TESTS)
          + f"   (end-state condition {rec['condition']}; draft rule {rec['old_rule']})")
    for a, why in ref_by.items():
        print(f"    {a:6} {'refuted by ' + ', '.join(why) if why else 'not refuted'}")
    print(f"  ACCOUNT ({model}): {verd}"
          + ("" if verd_old == verd else f"   (under the draft's recognition rule: {verd_old})"))
    print(f"  STATUS ({model}): {status}" + (f" {void}" if void else ""))
    out = {"model": model, "n": len(keys), "attempted": len(attempted), "status": status, "void": void,
           "p": P, "reference": ref, "cells": cls, "contrasts": con, "gate": gate, "outcomes": outs,
           "refuted_by": ref_by, "account": verd, "account_draft_rule": verd_old, "recognition": rec,
           "control": ctrl, "p2_miss": p2_miss}
    with open(f"results/e29o_{slug(model)}_summary.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


def programme(outs):
    """Over deciders whose read is FINAL; needs at least two."""
    ok = [o for o in outs if o and o["status"] == "FINAL"]
    if len(ok) < 2:
        return {"order": "NO PROGRAMME READING (fewer than two final deciders)", "account": "-", "first": "-",
                "n": len(ok)}
    gates = [o["gate"] for o in ok]
    if gates.count("ORDER") >= 2 and not any(g in ("NO ORDER EFFECT", "REVERSED") for g in gates):
        order = "THE ORDER EFFECT SURVIVES LIST-POSITION CONTROL"
    elif gates.count("NO ORDER EFFECT") >= 2 and "ORDER" not in gates:
        order = "THE ORDER EFFECT DOES NOT SURVIVE LIST-POSITION CONTROL"
    else:
        order = "MIXED: " + ", ".join(f"{o['model']} {o['gate']}" for o in ok)
    read = [o for o in ok if o["gate"] == "ORDER"]
    acc = "MIXED: " + ", ".join(f"{o['model']} {o['account']}" for o in ok)
    for a in PREDICTIONS:
        if sum(o["account"] == a for o in read) >= 2 and not any(o["refuted_by"].get(a) for o in read):
            acc = f"{a} SUPPORTED"
    fp = [o["contrasts"]["FPI"] for o in ok]
    pos_eff = sum(c["d"] >= SESOI and c["ci"][0] > 0 for c in fp)
    neg_eff = sum(c["d"] <= -SESOI and c["ci"][1] < 0 for c in fp)
    first = ("THE LEADING MARKER FAILS MOST WHEN THE RECORD IS FIRST IN THE LIST" if pos_eff >= 2 and not neg_eff
             else "MIXED OR UNCLEAR: " + ", ".join(f"{o['model']} FPI {o['contrasts']['FPI']['d']:+.3f}" for o in ok))
    return {"order": order, "account": acc, "first": first, "n": len(ok)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all:
        outs = [main(m) for m in DECIDERS]
        prog = programme(outs)
        print("=== E29-O programme reading ===")
        for k in ("order", "account", "first"):
            print(f"  {k.upper()}: {prog[k]}")
        with open("results/e29o_programme.json", "w", encoding="utf-8") as fh:
            json.dump(prog, fh, indent=1)
    else:
        main(a.model or DECIDERS[0])
