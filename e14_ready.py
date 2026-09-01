"""e14_ready.py: does evidential dependence move execution authorization while
leaving the substantive plan alone?

Protocol: docs/protocols/E14-ready-channel-v1.md. Preregistered; committed
with zero E14 outcomes.

WHAT IS MEASURED. Every response carries `ready` ("true if you consider the
plan safe to execute as written"). GENERATED responses also carry the action
ordering, scored `source` / `flip` by the deterministic evaluator exactly as
E12 did. So there are two decision channels:

    READY      execution authorization         primary channel
    ORDERING   the substantive plan decision   negative-control channel

DIRECTION, FROZEN BEFORE SCORING. E13's discovery ran SAME_ROOT > INDEPENDENT
_ROOT on `ready`. Every one-sided test below is one-sided in THAT direction.
Delta = P(ready | SAME_ROOT) - P(ready | INDEPENDENT_ROOT); positive is the
predicted direction.

THE PRIMARY CONTRAST is FIXED-plan READY. The plan is the same bytes in both
arms, so no model-generated plan difference can mediate an effect there.
GENERATED READY is the ecological replication. The INTERACTION -- does
dependence move READY materially more than it moves ORDERING? -- is tested
directly, within response, as a paired difference-of-differences, never
inferred from one p-value being small and another not.

THE DESIGN REFUSES TO OVERCLAIM BY CONSTRUCTION. prospective_design_check
--e14 fixed the operating bands below before any model call. A contrast whose
observed discordance lands outside its band is printed INCONCLUSIVE BY DESIGN
RULE and never as a null, never as a confirmation.

Run:  python e14_ready.py --offset 0 --limit 108      (four chunks of 108)
      python e14_ready.py --analyse
"""
import argparse
import csv
import glob
import json
import math
import random
import statistics

from budget import Budget
from e12_powered import verdict
from experiment import show, write_csv
from lineage_e14 import (CELLS, DEPENDENCE, PRIMARY_CELLS, all_units,
                         build_prompt, by_instance, candidate_plan, cells_for,
                         corpus_hash, is_diag_unit, plan_hash, plan_text,
                         system_prompt)
from lineage_eval import check_plan, parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured, extract_json_object

TEMPERATURE = 0
DECIDER = "llama3.2:3b"
SEED = 20260902
PERM_REPS = 20000
BOOT_REPS = 10000

#: One scale for both channels, so the interaction is interpretable. Chosen for
#: practical importance -- a ten-point change in how often an execution gate
#: opens -- NOT from E13's observed +0.23, which informs power only.
SESOI = 0.10
INTERACTION_SESOI = 0.10

#: Fixed by `python prospective_design_check.py --e14 --units 432 --clusters
#: 144` BEFORE any model call (see the protocol, section 6). Observed
#: discordance outside a band -> INCONCLUSIVE BY DESIGN RULE for that reading.
PRIMARY_BAND = (0.10, 0.50)        # FIXED READY: power >= 0.80 at the SESOI
INTERACTION_BAND = (0.10, 0.40)    # GENERATED READY discordance for the DoD
EQUIVALENCE_BAND = (0.05, 0.20)    # ORDERING discordance for equivalence

#: Parse and token symmetry thresholds, fixed before scoring.
PARSE_ASYMMETRY_MAX = 0.05         # |parse(SAME) - parse(INDEP)| in a cell
TOKEN_IMBALANCE_MAX = 0.03         # |mean(same - indep)| / mean prompt tokens


# --------------------------------------------------------------- parsing ----

def parse_ready(text):
    """FIXED-mode validator: one JSON object with a boolean `ready`."""
    blob = extract_json_object(text or "")
    if blob is None:
        return None, "no JSON object found"
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(obj, dict) or not isinstance(obj.get("ready"), bool):
        return None, "missing or non-boolean key: ready"
    return {"ready": obj["ready"]}, None


def score_text(text, instance, rec, mode):
    """(parsed, ready, verdict) from raw response text. The ONLY scorer; the
    run loop and verify_claims both call it, so a number cannot be produced
    one way and checked another."""
    if mode == "generated":
        chk = check_plan(text, instance)
        if not chk.parsed:
            return False, "", ""
        return True, chk.ready, verdict(instance, rec, chk.actions)
    val, err = parse_ready(text)
    if err is not None:
        return False, "", ""
    return True, val["ready"], ""


# ------------------------------------------------------------------ run ----

def ask(client, model, instance, rec, mode, dependence):
    messages = [
        {"role": "system", "content": system_prompt(mode, instance)},
        {"role": "user", "content": build_prompt(rec, instance, mode, dependence)},
    ]
    if mode == "generated":
        validate, expected = parse_plan, (
            'It must have exactly two keys: "actions", a list of action '
            'identifier strings, and "ready", true or false.')
    else:
        validate, expected = parse_ready, (
            'It must have exactly one key: "ready", true or false.')
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(client=client, model=model, temperature=TEMPERATURE,
                          messages=messages, validate=validate, budget=budget,
                          speaker="Operator", expected=expected)


COLUMNS = ["model", "unit", "instance", "salt", "domain", "constraint", "mode",
           "dependence", "diagnostic", "prompt_words", "prompt_tokens",
           "completion_tokens", "attempts", "parsed", "ready", "verdict",
           "plan_hash", "seconds"]


def run(model, offset, limit):
    insts = by_instance()
    units = all_units()
    sel = list(enumerate(units))[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    print(f"=== E14 ready channel: {model}, units {offset}..{offset + len(sel) - 1}"
          f", corpus {corpus_hash()} ===\n")

    rows, detail = [], []
    for n, (idx, rec) in enumerate(sel, 1):
        inst = insts[rec["instance"]]
        line = []
        for mode, dep, diag in cells_for(idx):
            res = ask(client, model, inst, rec, mode, dep)
            text = res.accepted_text or res.last_text or ""
            first = res.attempts[0] if res.attempts else None
            parsed, ready, v = score_text(text, inst, rec, mode)
            plan = candidate_plan(inst, rec, mode)
            prompt = build_prompt(rec, inst, mode, dep)
            rows.append({
                "model": model, "unit": rec["unit"], "instance": rec["instance"],
                "salt": rec["salt"], "domain": rec["domain"],
                "constraint": rec["constraint"], "mode": mode,
                "dependence": dep, "diagnostic": diag,
                "prompt_words": len(prompt.split()),
                "prompt_tokens": first.prompt_tokens if first else "",
                "completion_tokens": first.completion_tokens if first else "",
                "attempts": len(res.attempts), "parsed": parsed,
                "ready": ready, "verdict": v,
                "plan_hash": plan_hash(plan) if plan is not None else "",
                "seconds": round(sum(x.seconds for x in res.attempts), 2)})
            detail.append({
                "model": model, "unit": rec["unit"], "instance": rec["instance"],
                "mode": mode, "dependence": dep,
                "candidate_plan": plan_text(plan) if plan is not None else "",
                "plan_text": text,
                "attempts": [{"prompt_tokens": e.prompt_tokens,
                              "completion_tokens": e.completion_tokens,
                              "seconds": round(e.seconds, 3)}
                             for e in res.attempts]})
            tag = "T" if ready is True else "F" if ready is False else "-"
            line.append(f"{mode[:3]}/{dep[:4]}:{tag}{v[:1]}")
        print(f"  [{n:>3}/{len(sel)}] {rec['unit']:<30} " + " ".join(line))

    tag = model.replace(":", "-").replace(".", "")
    write_csv(f"results/e14_{tag}_o{offset}.csv", rows, COLUMNS)
    with open(f"results/e14_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=1)
    print(f"\nwrote results/e14_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call, "
          f"{client.transport_retries} transport retries)")


# ------------------------------------------------------------- loading ----

def load(model=DECIDER):
    rows = []
    for p in sorted(glob.glob("results/e14_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    return [r for r in rows if r["model"] == model]


def load_detail(model=DECIDER):
    out = []
    for p in sorted(glob.glob("results/e14_*_o*.json")):
        with open(p) as f:
            out.extend(d for d in json.load(f) if d["model"] == model)
    return out


def recompute_from_detail(detail, insts=None, units_by_id=None):
    """Re-score every raw response. Returns rows keyed like the CSV, computed
    from `plan_text` alone -- the CSV never verifies itself."""
    insts = insts or by_instance()
    units_by_id = units_by_id or {u["unit"]: u for u in all_units()}
    out = {}
    for d in detail:
        inst, rec = insts[d["instance"]], units_by_id[d["unit"]]
        parsed, ready, v = score_text(d["plan_text"], inst, rec, d["mode"])
        out[(d["unit"], d["mode"], d["dependence"])] = {
            "parsed": parsed, "ready": ready, "verdict": v,
            "candidate_plan": d["candidate_plan"]}
    return out


def mismatches(rows, recomputed):
    """CSV rows whose recorded (parsed, ready, verdict) differ from a fresh
    re-scoring of the raw text. Empty when the record is honest."""
    bad = []
    for r in rows:
        key = (r["unit"], r["mode"], r["dependence"])
        rc = recomputed.get(key)
        if rc is None:
            bad.append((key, "no raw response on disk"))
            continue
        if str(rc["parsed"]) != r["parsed"] or str(rc["ready"]) != r["ready"] \
                or rc["verdict"] != r["verdict"]:
            bad.append((key, f"csv {r['parsed']}/{r['ready']}/{r['verdict']} "
                             f"vs raw {rc['parsed']}/{rc['ready']}/{rc['verdict']}"))
    return bad


def fixed_plan_gate(detail, manifest):
    """Every FIXED response must have been shown the manifest's plan for its
    instance, byte for byte, and both arms of a unit the same bytes."""
    problems, seen = [], {}
    for d in detail:
        if d["mode"] != "fixed":
            continue
        want = plan_text(manifest[d["instance"]]["actions"])
        if d["candidate_plan"] != want:
            problems.append((d["unit"], d["dependence"], "plan differs from manifest"))
        seen.setdefault(d["unit"], {})[d["dependence"]] = d["candidate_plan"]
    for u, arms in seen.items():
        if len({v for k, v in arms.items() if k in DEPENDENCE}) > 1:
            problems.append((u, "*", "arms were shown different plans"))
    return problems


# ------------------------------------------------------------ statistics ----

def pairs(rows, mode, outcome):
    """{unit: {instance, same_root: 0/1, indep_root: 0/1}} -- COMPLETE PAIRS
    ONLY, plus the number of units dropped as incomplete. A unit missing one
    arm is never counted; it is reported."""
    seen = {}
    for r in rows:
        if r["mode"] != mode or r["dependence"] not in DEPENDENCE:
            continue
        u = seen.setdefault(r["unit"], {"instance": r["instance"]})
        if r["parsed"] != "True":
            continue
        if outcome == "ready" and r["ready"] in ("True", "False"):
            u[r["dependence"]] = 1 if r["ready"] == "True" else 0
        elif outcome == "flip" and r["verdict"] in ("source", "flip"):
            u[r["dependence"]] = 1 if r["verdict"] == "flip" else 0
    complete = {k: v for k, v in seen.items() if all(d in v for d in DEPENDENCE)}
    return complete, len(seen) - len(complete)


def _clusters(per):
    cl = {}
    for u in per.values():
        cl.setdefault(u["instance"], []).append(u)
    return cl


def _sign_test(a, b):
    n, k = a + b, min(a, b)
    return (min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)
            if n else None)


def delta_stats(per, key="delta", reps_perm=PERM_REPS, reps_boot=BOOT_REPS,
                seed=SEED):
    """Mean of a per-unit difference with instance-level inference.

    permutation   flip the sign of ALL units of an instance together (the only
                  exchangeability a paired, clustered design supports)
    p_two         |mean| at least as extreme
    p_one         mean at least as large -- one-sided in the PREDECLARED
                  positive direction
    CI            cluster bootstrap, instances resampled with replacement
    """
    units = list(per.values())
    n = len(units)
    cl = _clusters(per)
    obs = sum(u[key] for u in units) / n
    sums = [sum(u[key] for u in c) for c in cl.values()]
    rng = random.Random(seed)
    h2 = h1 = 0
    for _ in range(reps_perm):
        tot = sum(s if rng.random() < 0.5 else -s for s in sums)
        if abs(tot / n) >= abs(obs) - 1e-12:
            h2 += 1
        if tot / n >= obs - 1e-12:
            h1 += 1
    keys = list(cl)
    rng = random.Random(seed)
    diffs = []
    for _ in range(reps_boot):
        pick = [cl[keys[rng.randrange(len(keys))]] for _ in keys]
        us = [u for c in pick for u in c]
        diffs.append(sum(u[key] for u in us) / len(us))
    diffs.sort()
    return {"n": n, "clusters": len(cl), "mean": round(obs, 4),
            "p_two": (h2 + 1) / (reps_perm + 1),
            "p_one": (h1 + 1) / (reps_perm + 1),
            "lo": round(diffs[int(0.025 * reps_boot)], 4),
            "hi": round(diffs[int(0.975 * reps_boot)], 4)}


def paired_stats(per, **kw):
    """Delta = P(SAME) - P(INDEP) for a 0/1 outcome, with paired counts and
    discordance. Wraps delta_stats."""
    for u in per.values():
        u["delta"] = u["same_root"] - u["indep_root"]
    units = list(per.values())
    gt = sum(u["delta"] > 0 for u in units)
    lt = sum(u["delta"] < 0 for u in units)
    d = delta_stats(per, "delta", **kw)
    n = d["n"]
    return {**d,
            "p_same": round(sum(u["same_root"] for u in units) / n, 4),
            "p_indep": round(sum(u["indep_root"] for u in units) / n, 4),
            "diff": d["mean"], "same_gt": gt, "indep_gt": lt,
            "ties": n - gt - lt, "disc": round((gt + lt) / n, 4),
            "mcnemar_naive": _sign_test(gt, lt)}


def interaction_units(rows, ready_mode):
    """Per-unit difference-of-differences: (READY delta) - (ORDERING delta).
    ORDERING always comes from GENERATED; READY from `ready_mode`
    ('generated' -> within one response, I1; 'fixed' -> across modes, I2).
    Complete on BOTH channels only."""
    pr, _ = pairs(rows, ready_mode, "ready")
    po, _ = pairs(rows, "generated", "flip")
    out = {}
    for u in pr:
        if u in po:
            out[u] = {"instance": pr[u]["instance"],
                      "delta": (pr[u]["same_root"] - pr[u]["indep_root"])
                      - (po[u]["same_root"] - po[u]["indep_root"])}
    return out, pr, po


# ------------------------------------------------------------- readings ----

def in_band(x, band):
    return band[0] <= x <= band[1]


def read_ready(s, band, parse_gap):
    """The preregistered reading for a READY contrast."""
    if parse_gap > PARSE_ASYMMETRY_MAX:
        return "INCONCLUSIVE -- PARSE ASYMMETRY (kill rule 3 live)"
    if not in_band(s["disc"], band):
        return (f"INCONCLUSIVE BY DESIGN RULE -- discordance {s['disc']:.3f} "
                f"outside {band}")
    if s["p_one"] < 0.05 and s["lo"] > 0 and s["diff"] >= SESOI:
        return "CONFIRMED (one-sided p < .05, CI lower > 0, delta >= SESOI)"
    if s["hi"] < SESOI:
        return "RETIRED (kill rule 1): below the SESOI with adequate precision"
    if s["p_one"] < 0.05 and s["lo"] > 0:
        return "INCONCLUSIVE: direction supported, point estimate below SESOI"
    return "INCONCLUSIVE"


def read_ordering(s):
    if s["p_two"] < 0.05:
        return f"DIFFERENTIATES (p = {s['p_two']:.4f})"
    if not in_band(s["disc"], EQUIVALENCE_BAND):
        return (f"estimate and CI only -- discordance {s['disc']:.3f} outside "
                f"the equivalence band {EQUIVALENCE_BAND}")
    if abs(s["diff"]) < SESOI and s["lo"] > -SESOI and s["hi"] < SESOI:
        return "EQUIVALENCE-SUPPORTED (|delta| < SESOI, CI inside +/-SESOI)"
    return "estimate and CI only -- not equivalent, not different"


def read_interaction(d, ready_disc, band):
    if not in_band(ready_disc, band):
        return (f"INCONCLUSIVE BY DESIGN RULE -- READY discordance "
                f"{ready_disc:.3f} outside {band}")
    if d["p_one"] < 0.05 and d["lo"] > 0 and d["mean"] >= INTERACTION_SESOI:
        return ("DISSOCIATION SUPPORTED: READY moves materially more than "
                "ORDERING")
    if d["hi"] < INTERACTION_SESOI:
        return "NO MATERIAL DISSOCIATION (DoD below SESOI with adequate precision)"
    if d["p_one"] < 0.05 and d["lo"] > 0:
        return "INCONCLUSIVE: direction supported, DoD below SESOI"
    return "INCONCLUSIVE"


# -------------------------------------------------------------- analyse ----

def analyse(model=DECIDER):
    rows = load(model)
    if not rows:
        raise SystemExit("no E14 results yet")
    detail = load_detail(model)
    print(f"=== E14 ready channel -- {model} ===")
    print(f"  corpus {corpus_hash()}   SESOI {SESOI}   seed {SEED}")
    print(f"  bands: primary {PRIMARY_BAND}  interaction {INTERACTION_BAND}  "
          f"equivalence {EQUIVALENCE_BAND}\n")

    # ---- honesty of the record: re-score every raw response --------------
    bad = mismatches(rows, recompute_from_detail(detail))
    print(f"  raw re-scoring: {len(rows)} rows, {len(bad)} mismatches "
          f"{'-- STOP' if bad else '(record is consistent)'}")
    if bad:
        for b in bad[:10]:
            print("    ", b)

    # ---- parse and token symmetry ----------------------------------------
    print("\n=== parse and token symmetry, per cell ===")
    par = []
    for mode, dep, diag in CELLS:
        g = [r for r in rows if r["mode"] == mode and r["dependence"] == dep]
        if not g:
            continue
        par.append({
            "mode": mode, "dependence": dep, "diagnostic": diag, "n": len(g),
            "parse_rate": round(sum(r["parsed"] == "True" for r in g) / len(g), 3),
            "first_try": round(sum(r["attempts"] == "1" and r["parsed"] == "True"
                                   for r in g) / len(g), 3),
            "prompt_words": round(statistics.mean(int(r["prompt_words"]) for r in g), 1),
            "prompt_tokens": round(statistics.mean(int(r["prompt_tokens"]) for r in g
                                                   if r["prompt_tokens"] != ""), 1),
            "ready_rate": round(sum(r["ready"] == "True" for r in g)
                                / max(1, sum(r["parsed"] == "True" for r in g)), 3)})
    show(par, list(par[0].keys()))
    write_csv("results/e14_parse.csv", par, list(par[0].keys()))

    tok = []
    parse_gap = {}
    for mode in ("generated", "fixed"):
        by = {}
        for r in rows:
            if r["mode"] == mode and r["dependence"] in DEPENDENCE \
                    and r["prompt_tokens"] != "":
                by.setdefault(r["unit"], {})[r["dependence"]] = int(r["prompt_tokens"])
        d = [v["same_root"] - v["indep_root"] for v in by.values() if len(v) == 2]
        mean_all = statistics.mean(int(r["prompt_tokens"]) for r in rows
                                   if r["mode"] == mode and r["dependence"] in DEPENDENCE
                                   and r["prompt_tokens"] != "")
        ps = {dep: statistics.mean(r["parsed"] == "True" for r in rows
                                   if r["mode"] == mode and r["dependence"] == dep)
              for dep in DEPENDENCE}
        parse_gap[mode] = abs(ps["same_root"] - ps["indep_root"])
        rel = abs(statistics.mean(d)) / mean_all if d else 0.0
        tok.append({"mode": mode, "pairs": len(d),
                    "mean_tokens": round(mean_all, 1),
                    "mean_same_minus_indep": round(statistics.mean(d), 2) if d else None,
                    "max_abs_unit_diff": max(abs(x) for x in d) if d else None,
                    "relative_imbalance": round(rel, 4),
                    "material": rel > TOKEN_IMBALANCE_MAX,
                    "parse_gap": round(parse_gap[mode], 3)})
    show(tok, list(tok[0].keys()))
    write_csv("results/e14_tokens.csv", tok, list(tok[0].keys()))
    print("  `material` = kill rule 4 territory: disclosed, and the primary is")
    print("  read INCONCLUSIVE if the imbalance in its own cell is material.")

    # ---- the contrasts ----------------------------------------------------
    print("\n=== contrasts: delta = P(x | SAME_ROOT) - P(x | INDEPENDENT_ROOT) ===")
    print("  positive = predicted direction for READY; instance-level permutation")
    print("  (one-sided in the predeclared direction, and two-sided) and bootstrap\n")
    res, table = {}, []
    for label, mode, outcome in (("PRIMARY  fixed READY", "fixed", "ready"),
                                 ("replication  generated READY", "generated", "ready"),
                                 ("control  generated ORDERING(flip)", "generated", "flip")):
        per, dropped = pairs(rows, mode, outcome)
        if not per:
            continue
        s = paired_stats(per)
        res[(mode, outcome)] = s
        table.append({"contrast": label, "n_pairs": s["n"], "dropped": dropped,
                      "clusters": s["clusters"], "p_same": s["p_same"],
                      "p_indep": s["p_indep"], "delta": s["diff"],
                      "same_gt": s["same_gt"], "indep_gt": s["indep_gt"],
                      "ties": s["ties"], "disc": s["disc"],
                      "p_one": round(s["p_one"], 4), "p_two": round(s["p_two"], 4),
                      "ci": f"[{s['lo']:+.3f},{s['hi']:+.3f}]",
                      "mcnemar_naive": (None if s["mcnemar_naive"] is None
                                        else float(f"{s['mcnemar_naive']:.3g}"))})
    show(table, list(table[0].keys()))
    write_csv("results/e14_primary.csv", table, list(table[0].keys()))

    # ---- interaction ------------------------------------------------------
    print("\n=== interaction: (READY delta) - (ORDERING delta), per unit ===")
    inter = []
    idet = {}
    for label, ready_mode, band in (("I1 within-response (generated)", "generated", INTERACTION_BAND),
                                    ("I2 cross-mode (fixed READY vs generated ORDERING)", "fixed", PRIMARY_BAND)):
        units, pr, po = interaction_units(rows, ready_mode)
        if not units:
            continue
        d = delta_stats(units, "delta")
        rd = paired_stats(pr)["disc"]
        idet[ready_mode] = (d, rd, band)
        inter.append({"test": label, "n_pairs": d["n"], "clusters": d["clusters"],
                      "dod": d["mean"], "p_one": round(d["p_one"], 4),
                      "p_two": round(d["p_two"], 4),
                      "ci": f"[{d['lo']:+.3f},{d['hi']:+.3f}]",
                      "ready_disc": rd, "ordering_disc": paired_stats(po)["disc"]})
    if inter:
        show(inter, list(inter[0].keys()))
        write_csv("results/e14_interaction.csv", inter, list(inter[0].keys()))

    # ---- diagnostics (never pooled) --------------------------------------
    print("\n=== diagnostics on the 24-unit subset (never pooled) ===")
    diag_units = {r["unit"] for r in rows if r["mode"] == "fixed_invalid"}
    ctrl = []
    for dep in ("same_root", "indep_root"):
        valid = [r for r in rows if r["mode"] == "fixed" and r["dependence"] == dep
                 and r["unit"] in diag_units and r["parsed"] == "True"]
        inval = [r for r in rows if r["mode"] == "fixed_invalid"
                 and r["dependence"] == dep and r["parsed"] == "True"]
        ctrl.append({"dependence": dep, "n": len(inval),
                     "ready_valid_plan": round(sum(r["ready"] == "True" for r in valid)
                                               / max(1, len(valid)), 3),
                     "ready_invalid_plan": round(sum(r["ready"] == "True" for r in inval)
                                                 / max(1, len(inval)), 3)})
    bare = [r for r in rows if r["mode"] == "fixed" and r["dependence"] == "bare"
            and r["parsed"] == "True"]
    ctrl.append({"dependence": "bare (no support)", "n": len(bare),
                 "ready_valid_plan": round(sum(r["ready"] == "True" for r in bare)
                                           / max(1, len(bare)), 3),
                 "ready_invalid_plan": None})
    show(ctrl, list(ctrl[0].keys()))
    write_csv("results/e14_controls.csv", ctrl, list(ctrl[0].keys()))
    print("  A `ready` that is true for the reversed plan as often as for the")
    print("  valid one is not a judgement; a `ready` that does not move without")
    print("  support is not evidence-sensitive. Both are reported, neither pooled.")

    # ---- the preregistered readings --------------------------------------
    print("\n=== the preregistered readings ===")
    prim = res.get(("fixed", "ready"))
    rep_ = res.get(("generated", "ready"))
    ordr = res.get(("generated", "flip"))
    readings = {}
    if prim:
        tokrow = next(t for t in tok if t["mode"] == "fixed")
        r = read_ready(prim, PRIMARY_BAND, parse_gap["fixed"])
        if tokrow["material"] and r.startswith("CONFIRMED"):
            r = "INCONCLUSIVE -- MATERIAL TOKEN IMBALANCE (kill rule 4 live)"
        readings["primary"] = r
        print(f"  PRIMARY   fixed READY          {r}")
    if rep_:
        r = read_ready(rep_, INTERACTION_BAND, parse_gap["generated"])
        readings["replication"] = r
        print(f"  REPLICATION generated READY    {r}")
    if ordr:
        r = read_ordering(ordr)
        readings["ordering"] = r
        print(f"  CONTROL   generated ORDERING   {r}")
    if "generated" in idet:
        d, rd, band = idet["generated"]
        r = read_interaction(d, rd, band)
        readings["interaction"] = r
        print(f"  INTERACTION I1 (within response)  {r}")
    if "fixed" in idet:
        d, rd, band = idet["fixed"]
        r = read_interaction(d, rd, band)
        readings["interaction_cross"] = r
        print(f"  INTERACTION I2 (cross-mode)       {r}")

    # kill rule 2: plan-mediated
    if prim and rep_:
        if readings["replication"].startswith("CONFIRMED") and \
                readings["primary"].startswith("RETIRED"):
            print("\n  KILL RULE 2 FIRES: the effect exists only with a generated")
            print("  plan and disappears with an identical fixed plan -> PLAN-")
            print("  MEDIATED, not a readiness-channel effect. Direction RETIRED.")
    print("\n  Escalation (protocol section 12) needs: primary CONFIRMED, I1")
    print("  DISSOCIATION SUPPORTED, verify_claims fully green. Nothing here")
    print("  is a claim until all three hold and the prior art is searched again.")
    write_csv("results/e14_readings.csv",
              [{"reading": k, "value": v} for k, v in readings.items()],
              ["reading", "value"])
    return readings


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DECIDER)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    if a.analyse:
        analyse(a.model)
    else:
        run(a.model, a.offset, a.limit)
