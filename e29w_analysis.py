"""e29w_analysis.py: read E29-W by the rule declared in docs/protocols/E29W-knockout.md.
Zero model calls.

Rejected-step inclusion per condition (in base_open the same step, undecided), complete-case
over all ten conditions, paired bootstrap over dialogues (seed 0, B = 2000, percentile 95 %).
Directional classes for d = P(a) - P(b): BOUND if d >= 0.15 with an interval excluding 0; REVERSED
if d <= -0.15 with an interval excluding 0; FREE if the interval lies inside (-0.15, 0.15);
UNCLEAR otherwise.

Gate R (there is something to explain in this runtime):
    ORDER  = P(base_pre)  - P(base_post)   must be BOUND
    WORKS  = P(base_open) - P(base_post)   must be BOUND
Knockouts on the trailing marker, all layers:
    KR = P(kr_post) - P(base_post)   no later token may read the marker (positive control)
    KB = P(kb_post) - P(base_post)   the marker may not read its record
    KC = P(kc_post) - P(base_post)   the marker may not read N (control)
Reading:
    AT THE MARKER   KR BOUND, KB BOUND, KC FREE
    DOWNSTREAM      KR BOUND, KB FREE,  KC FREE
    NON-SPECIFIC    KR BOUND, KB BOUND, KC not FREE
    UNREADABLE      KR not BOUND (the knockout does not remove the marker's effect)
    UNCLEAR         otherwise
Exploratory, two-sided (EFFECT / NONE / UNCLEAR): EARLY = P(kb_early) - P(base_post),
LATE = P(kb_late) - P(base_post), FWD = P(kf_pre) - P(base_pre).

    python e29w_analysis.py
"""
import csv
import json
import random
import statistics
from collections import defaultdict

from e29w_knockout import CONDITIONS, STEM

B, SESOI = 2000, 0.15
BASE = ("base_open", "base_sentence", "base_pre", "base_post")


def ci(v):
    v = sorted(v)
    return v[int(0.025 * B)], v[int(0.975 * B) - 1]


def directional(d, lo, hi):
    if d >= SESOI and lo > 0:
        return "BOUND"
    if d <= -SESOI and hi < 0:
        return "REVERSED"
    if -SESOI < lo and hi < SESOI:
        return "FREE"
    return "UNCLEAR"


def two_sided(d, lo, hi):
    if abs(d) >= SESOI and (lo > 0 or hi < 0):
        return "EFFECT"
    if -SESOI < lo and hi < SESOI:
        return "NONE"
    return "UNCLEAR"


def reading(cls):
    kr, kb, kc = cls["KR"], cls["KB"], cls["KC"]
    if kr != "BOUND":
        return "UNREADABLE"
    if kb == "BOUND" and kc == "FREE":
        return "AT THE MARKER"
    if kb == "FREE" and kc == "FREE":
        return "DOWNSTREAM"
    if kb == "BOUND" and kc != "FREE":
        return "NON-SPECIFIC"
    return "UNCLEAR"


def main(path=STEM + ".csv"):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
        r["included"] = {"True": True, "False": False}.get(r["included"])
        r["n_actions"] = int(r["n_actions"]) if r["n_actions"] not in ("", "None") else None
    rej = defaultdict(dict)
    for r in rows:
        if r["status"] == "rejected":
            rej[(r["instance"], r["rotation"])][r["design"]] = r["included"]
    attempted = {(r["instance"], r["rotation"]) for r in rows}
    keys = [k for k, v in rej.items() if all(v.get(c) is not None for c in CONDITIONS)]
    void = {}
    for c in CONDITIONS:
        cr = [r for r in rows if r["design"] == c]
        parse = statistics.mean(r["parsed"] for r in cr)
        lens = [r["n_actions"] for r in cr if r["parsed"]]
        mp = statistics.mean(lens) if lens else float("nan")
        if parse < 0.95 or not (3.9 <= mp <= 4.1):
            void[c] = (round(parse, 3), round(mp, 2))

    def p(ks, c):
        return statistics.mean(rej[k][c] for k in ks)

    P = {c: p(keys, c) for c in CONDITIONS}
    defs = {"ORDER": ("base_pre", "base_post"), "WORKS": ("base_open", "base_post"),
            "KR": ("kr_post", "base_post"), "KB": ("kb_post", "base_post"), "KC": ("kc_post", "base_post")}
    expl = {"EARLY": ("kb_early", "base_post"), "LATE": ("kb_late", "base_post"), "FWD": ("kf_pre", "base_pre")}
    rng = random.Random(0)
    boot = defaultdict(list)
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        ps = {c: p(s, c) for c in CONDITIONS}
        for name, (a, b) in {**defs, **expl}.items():
            boot[name].append(ps[a] - ps[b])
        w = ps["base_open"] - ps["base_post"]
        boot["SHARE"].append((ps["kb_post"] - ps["base_post"]) / w if w else float("nan"))
    res, cls = {}, {}
    for name, (a, b) in defs.items():
        d = P[a] - P[b]
        lo, hi = ci(boot[name])
        cls[name] = directional(d, lo, hi) if not ({a, b} & set(void)) else "VOID"
        res[name] = {"d": d, "ci": [lo, hi], "class": cls[name]}
    for name, (a, b) in expl.items():
        d = P[a] - P[b]
        lo, hi = ci(boot[name])
        res[name] = {"d": d, "ci": [lo, hi], "class": two_sided(d, lo, hi) if not ({a, b} & set(void)) else "VOID"}
    w = P["base_open"] - P["base_post"]
    share = (P["kb_post"] - P["base_post"]) / w if w else float("nan")
    sl, sh = ci([x for x in boot["SHARE"] if x == x] or [float("nan")] * B)
    status = ("VOID" if set(void) & set(BASE) else "INCOMPLETE" if len(attempted) < 192 else "FINAL")
    gate = "MET" if (cls["ORDER"] == "BOUND" and cls["WORKS"] == "BOUND") else "NOT MET"
    read = reading(cls) if (status == "FINAL" and gate == "MET") else "NOT READ"
    print(f"=== E29-W read: Llama-3.2-3B-Instruct bf16 (n = {len(keys)} complete of {len(attempted)} attempted; {status}) ===")
    for c in CONDITIONS:
        print(f"  {c:14} {P[c]:.3f}" + (f"   VOID {void[c]}" if c in void else ""))
    for name, r in res.items():
        a, b = (defs.get(name) or expl.get(name))
        print(f"  {name:6} {a} - {b}: {r['d']:+.3f} [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]  {r['class']}")
    print(f"  share of the marker's effect removed by KB: {share:.2f} [{sl:.2f}, {sh:.2f}]")
    print(f"  GATE R: {gate}")
    print(f"  READING: {read}")
    out = {"n": len(keys), "attempted": len(attempted), "status": status, "void": void, "p": P,
           "contrasts": res, "share": [share, sl, sh], "gate": gate, "reading": read}
    with open(STEM.replace("_r0", "") + "_summary.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    return out


if __name__ == "__main__":
    main()
