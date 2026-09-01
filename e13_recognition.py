"""e13_recognition.py: does routing recognised dependence into reasoning change the decision?

Protocol: docs/protocols/E13-recognition-utilization-v1.md. Preregistered;
committed with zero E13 outcomes.

E12 established that the model prices k reports from ONE evidential root exactly
as it prices k INDEPENDENT roots, while a frozen probe shows it can report the
difference. E13 asks whether making it state the structure -- or handing it the
structure, or the normative rule -- makes the recognition govern the decision.

TWO STATES ARE KEPT FOR EVERY DECISION, which is the whole point:

    RECOGNITION STATE   what the model said the evidence structure was
    ACTION STATE        what the deterministic evaluator says the plan did

The headline is not aggregate accuracy. It is whether correct reportable
recognition actually governs behaviour, within the same response.

THE DESIGN REFUSES TO OVERCLAIM BY CONSTRUCTION. prospective_design_check says
this design (108 units, 36 clusters, SESOI 0.10) is powered only for observed
discordance in [0.08, 0.12]. Any contrast landing outside that band is printed
as INCONCLUSIVE by rule -- never as a null. That contingency is fixed here,
before scoring, because E10 reported a null from a design that could not have
produced one.

Run:  python e13_recognition.py --limit 36
      python e13_recognition.py --analyse
"""
import argparse
import csv
import glob
import json
import statistics

from budget import Budget
from e10_independence import SESOI, SYSTEM, holm
from e12_powered import cluster_bootstrap, cluster_permutation, verdict
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_e12 import all_units
from lineage_e13 import (DEPENDENCE, DIAGNOSTIC, INTERVENTIONS,
                         RECOGNITION_ARMS, build_prompt, cells, corpus_hash,
                         expected_recognition, schema_hint)
from lineage_eval import check_plan, parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured, extract_json_object

TEMPERATURE = 0
DECIDER = "llama3.2:3b"

#: Fixed by prospective_design_check BEFORE any model call. Outside this band
#: the design cannot support a null, so it does not print one.
POWERED_DISCORDANCE = (0.08, 0.12)


def make_validator(intervention):
    """Accepts the plan, and the recognition keys when the arm requests them.

    Recognition is parsed but NEVER gates acceptance beyond presence: a wrong
    answer is data, not a parse failure. Only a missing or malformed field is
    a failure, or the arm's recognition state would be silently selected for
    correctness.
    """
    from lineage_e13 import RECOG_KEYS
    keys = RECOG_KEYS.get(intervention)

    def validate(text):
        value, err = parse_plan(text)
        if err is not None:
            return None, err
        if not keys:
            return {"plan": value, "recog": None}, None
        blob = extract_json_object(text or "")
        try:
            obj = json.loads(blob) if blob else {}
        except json.JSONDecodeError:
            return None, "recognition fields could not be parsed"
        missing = [k for k in keys if k not in obj]
        if missing:
            return None, f"missing required key(s): {', '.join(missing)}"
        return {"plan": value, "recog": {k: obj[k] for k in keys}}, None

    return validate


def recognition_correct(intervention, dependence, recog):
    """Preregistered. PRIMARY = the boolean. SECONDARY = the count, scored two
    ways because the count question is genuinely ambiguous.

    THE AMBIGUITY, found in a 2-unit smoke test BEFORE preregistration. Asked
    how many distinct underlying records the support rests on, the model
    answered 4 for an independent-root item whose support rests on 3. That is
    not obviously wrong: the contradiction message is also a report, and a
    reader may or may not count it. The instruction says "the support", which
    excludes it, but the reading is defensible.

    So the count is scored STRICT (exactly k+1) and LENIENT (k+1 or k+2,
    allowing the contradiction to be counted), both declared here before any
    scored run. The BOOLEAN carries the primary measure precisely because it
    has no such ambiguity: same underlying source or not.
    """
    if intervention not in RECOGNITION_ARMS or not recog:
        return None, None
    want = expected_recognition(dependence)
    got_bool = recog.get("same_underlying_source")
    got_n = recog.get("independent_source_count")
    primary = (isinstance(got_bool, bool)
               and got_bool == want["same_underlying_source"])
    n = want["independent_source_count"]
    try:
        got = int(got_n)
        secondary = "strict" if got == n else ("lenient" if got == n + 1
                                               else "wrong")
    except (TypeError, ValueError):
        secondary = "wrong"
    return primary, secondary


def run(model, offset, limit):
    by_id = {i.id: i for i in all_instances()}
    units = all_units()[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    print(f"=== E13 recognition->utilization: {model}, {len(units)} units x "
          f"{len(cells())} cells, prompts {corpus_hash(plan_instruction)} ===\n")

    rows, detail = [], []
    for i, rec in enumerate(units, 1):
        inst = by_id[rec["instance"]]
        pi = plan_instruction(inst)
        for arm, dep in cells():
            prompt = build_prompt(rec, dep, arm, pi)
            messages = [
                {"role": "system",
                 "content": SYSTEM.format(setting=inst.setting)},
                {"role": "user", "content": prompt}]
            budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000,
                            max_seconds=600)
            res = ask_structured(
                client=client, model=model, temperature=TEMPERATURE,
                messages=messages, validate=make_validator(arm),
                budget=budget, speaker="Operator",
                expected=schema_hint(arm))
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            v = verdict(inst, rec, chk.actions) if chk.parsed else ""
            recog = (res.value or {}).get("recog") if res.value else None
            p_ok, s_ok = recognition_correct(arm, dep, recog)
            rows.append({
                "model": model, "unit": rec["unit"],
                "instance": rec["instance"], "domain": rec["domain"],
                "intervention": arm, "dependence": dep,
                "diagnostic": arm in DIAGNOSTIC,
                "prompt_words": len(prompt.split()),
                "parsed": chk.parsed, "verdict": v,
                "recog_bool": (recog or {}).get("same_underlying_source", ""),
                "recog_count": (recog or {}).get("independent_source_count", ""),
                "recog_primary_ok": "" if p_ok is None else p_ok,
                "recog_count_score": "" if s_ok is None else s_ok,
                "seconds": round(sum(x.seconds for x in res.attempts), 2)})
            detail.append({"model": model, "unit": rec["unit"],
                           "instance": rec["instance"], "intervention": arm,
                           "dependence": dep, "plan_text": text})
        print(f"  [{i:>3}/{len(units)}] {rec['unit']:<24} " + " ".join(
            f"{a[:4]}/{d[:4]}:{rows[-len(cells()) + j]['verdict'][:4] or '----'}"
            for j, (a, d) in enumerate(cells())))

    tag = model.replace(":", "-").replace(".", "")
    write_csv(f"results/e13_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e13_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e13_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call, "
          f"{client.transport_retries} transport retries)")


def load(model=DECIDER):
    rows = []
    for p in sorted(glob.glob("results/e13_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    return [r for r in rows if r["model"] == model]


def _by_unit(rows, arm):
    """{unit: {dependence: verdict}} for one intervention, COMPLETE PAIRS ONLY.

    THE COMPLETENESS FILTER IS NOT COSMETIC. Without it, a unit whose SAME arm
    parsed and whose INDEP arm did not still enters the flip-rate denominator,
    and `u.get("indep_root")` returns None, which counts as "did not flip". A
    differential parse failure between the two dependence arms would then read
    as a behavioural difference -- manufacturing exactly the effect E13 is
    testing for, in exactly the arms that impose the heaviest output burden.

    Dropped units are counted and reported, never silently discarded.
    """
    seen = {}
    for r in rows:
        if r["intervention"] != arm:
            continue
        seen.setdefault(r["unit"], {"instance": r["instance"]})
        if r["parsed"] == "True" and r["verdict"] in ("source", "flip"):
            seen[r["unit"]][r["dependence"]] = r["verdict"]
    complete = {u: d for u, d in seen.items()
                if all(k in d for k in DEPENDENCE)}
    return complete, len(seen) - len(complete)


def discordance(per):
    """Fraction of units whose two dependence arms disagree."""
    n = d = 0
    for u in per.values():
        a, b = u.get("same_root"), u.get("indep_root")
        if a in ("source", "flip") and b in ("source", "flip"):
            n += 1
            d += a != b
    return (d / n if n else 0.0), n


def differentiation(per):
    """flip(SAME) - flip(INDEP). POSITIVE is the NORMATIVE direction: one root
    is weaker evidence, so it should protect LESS and flip MORE."""
    clusters = {}
    for u in per.values():
        clusters.setdefault(u["instance"], []).append(u)
    p, _ = cluster_permutation(clusters, "indep_root", "same_root")
    lo, hi = cluster_bootstrap(clusters, "indep_root", "same_root")
    units = [u for c in clusters.values() for u in c]
    same = sum(u.get("same_root") == "flip" for u in units) / len(units)
    ind = sum(u.get("indep_root") == "flip" for u in units) / len(units)
    return {"flip_same": round(same, 4), "flip_indep": round(ind, 4),
            "diff": round(same - ind, 4), "p": p, "lo": lo, "hi": hi,
            "clusters": clusters}


def analyse(model=DECIDER):
    rows = load(model)
    if not rows:
        raise SystemExit("no E13 results yet")
    print(f"=== E13 recognition -> utilization -- {model} ===")
    print(f"  prompts {corpus_hash(plan_instruction)}   "
          f"SESOI {SESOI}   powered discordance band {POWERED_DISCORDANCE}\n")

    # ---- parse rates first: an intervention that cannot be parsed is not an
    # intervention, and a differential parse rate is itself a confound.
    pr = []
    for arm, _, _ in INTERVENTIONS:
        for dep in DEPENDENCE:
            g = [r for r in rows if r["intervention"] == arm
                 and r["dependence"] == dep]
            pr.append({"intervention": arm, "dependence": dep, "n": len(g),
                       "parse_rate": round(
                           sum(r["parsed"] == "True" for r in g) / len(g), 3)
                       if g else None,
                       "prompt_words": g[0]["prompt_words"] if g else None})
    show(pr, ["intervention", "dependence", "n", "parse_rate", "prompt_words"])
    write_csv("results/e13_parse.csv", pr,
              ["intervention", "dependence", "n", "parse_rate", "prompt_words"])

    # ---- RQ1 recognition, measured independently of action ----------------
    print("\n=== RQ1 -- recognition accuracy (independent of the action) ===")
    rq1 = []
    for arm in sorted(RECOGNITION_ARMS):
        for dep in DEPENDENCE:
            g = [r for r in rows if r["intervention"] == arm
                 and r["dependence"] == dep and r["recog_primary_ok"] != ""]
            if not g:
                continue
            rq1.append({
                "intervention": arm, "dependence": dep, "n": len(g),
                "bool_correct": round(
                    sum(r["recog_primary_ok"] == "True" for r in g) / len(g), 3),
                "count_strict": round(
                    sum(r["recog_count_score"] == "strict" for r in g) / len(g), 3),
                "count_lenient": round(
                    sum(r["recog_count_score"] in ("strict", "lenient")
                        for r in g) / len(g), 3)})
    if rq1:
        show(rq1, list(rq1[0].keys()))
        write_csv("results/e13_recognition.csv", rq1, list(rq1[0].keys()))
    print("  If recognition is weak the problem is PERCEPTUAL, not utilization,")
    print("  and the whole direction narrows -- falsification rule 2.")

    # The count, analysed PAIRED -- the same shape as E12's frozen probe, which
    # reported 27 vs 0, p = 1.5e-08. The boolean is the predeclared PRIMARY and
    # stays primary; this is the predeclared SECONDARY, and reporting both is
    # what lets a disagreement between them be seen rather than chosen between.
    print("\n=== RQ1b -- does the reported COUNT discriminate, paired by unit? ===")
    import math as _m
    disc_tab = []
    for arm in sorted(RECOGNITION_ARMS):
        per = {}
        for r in rows:
            if r["intervention"] == arm and r["recog_count"] != "":
                try:
                    per.setdefault(r["unit"], {})[r["dependence"]] = int(
                        r["recog_count"])
                except ValueError:
                    pass
        hi = sum(1 for v in per.values()
                 if len(v) == 2 and v["indep_root"] > v["same_root"])
        lo = sum(1 for v in per.values()
                 if len(v) == 2 and v["indep_root"] < v["same_root"])
        n, k = hi + lo, min(hi, lo)
        p = (min(2 * sum(_m.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)
             if n else None)
        disc_tab.append({"intervention": arm, "indep_gt_same": hi,
                         "indep_lt_same": lo,
                         "sign_p": None if p is None else float(f"{p:.4g}")})
    show(disc_tab, ["intervention", "indep_gt_same", "indep_lt_same", "sign_p"])
    write_csv("results/e13_count_discrimination.csv", disc_tab,
              ["intervention", "indep_gt_same", "indep_lt_same", "sign_p"])
    print("  E12's frozen probe, for comparison: 27 vs 0, p = 1.5e-08.")
    print("  A boolean that says 'same' regardless while the COUNT tracks the")
    print("  manipulation is a RESPONSE BIAS in the boolean, not an absence of")
    print("  recognition -- and the two measures must be reported together.")

    # ---- RQ2-RQ4: behavioural differentiation per intervention ------------
    print("\n=== behavioural differentiation: flip(SAME) - flip(INDEP) ===")
    print("  positive = NORMATIVE direction (one root should protect LESS)\n")
    res, raw = {}, []
    table = []
    for arm, _, diag in INTERVENTIONS:
        per, dropped = _by_unit(rows, arm)
        if not per:
            continue
        d = differentiation(per)
        disc, n_pairs = discordance(per)
        powered = POWERED_DISCORDANCE[0] <= disc <= POWERED_DISCORDANCE[1]
        res[arm] = {**d, "disc": disc, "powered": powered, "n": n_pairs}
        if not diag:
            raw.append(d["p"])
        table.append({
            "intervention": arm, "diagnostic": diag, "n_pairs": n_pairs,
            "dropped_incomplete": dropped,
            "flip_same": d["flip_same"], "flip_indep": d["flip_indep"],
            "diff": d["diff"], "p": round(d["p"], 4),
            "ci": f"[{d['lo']:+.3f},{d['hi']:+.3f}]",
            "discordance": round(disc, 3),
            "in_powered_band": powered})
    show(table, list(table[0].keys()))
    write_csv("results/e13_differentiation.csv", table, list(table[0].keys()))

    print("\n=== the preregistered readings ===")
    for arm, _, diag in INTERVENTIONS:
        r = res.get(arm)
        if not r:
            continue
        tag = " (DIAGNOSTIC, never pooled)" if diag else ""
        if r["p"] < 0.05:
            msg = f"DIFFERENTIATES (p = {r['p']:.4f}, diff {r['diff']:+.4f})"
        elif not r["powered"]:
            msg = (f"INCONCLUSIVE BY RULE -- discordance {r['disc']:.3f} is "
                   f"outside the powered band {POWERED_DISCORDANCE}")
        elif abs(r["diff"]) < SESOI and r["lo"] > -SESOI and r["hi"] < SESOI:
            msg = (f"EQUIVALENCE-SUPPORTED NULL (diff {r['diff']:+.4f}, "
                   f"CI [{r['lo']:+.3f},{r['hi']:+.3f}] inside +/-{SESOI})")
        else:
            msg = f"inconclusive (p = {r['p']:.4f}, CI wider than the SESOI)"
        print(f"  {arm:<10}{tag}\n      {msg}")

    # ---- secondary family: did the intervention CHANGE the differentiation?
    print("\n=== secondary: intervention vs DEFAULT (Holm over the family) ===")
    base = res.get("default")
    sec, praw = [], []
    if base:
        for arm, _, diag in INTERVENTIONS:
            if arm == "default" or arm not in res:
                continue
            r = res[arm]
            did = r["diff"] - base["diff"]
            sec.append({"intervention": arm, "diagnostic": diag,
                        "diff": r["diff"], "default_diff": base["diff"],
                        "did": round(did, 4)})
            praw.append(r["p"])
        for row, adj in zip(sec, holm(praw)):
            row["own_p_holm"] = None if adj is None else round(adj, 4)
        show(sec, list(sec[0].keys()))
        write_csv("results/e13_secondary.csv", sec, list(sec[0].keys()))
    print("  `did` is the difference-in-differences against DEFAULT. SHAM is")
    print("  the control: if SHAM moves `did` as much as IDENTIFY, the cause is")
    print("  the structured-output burden, not dependence reasoning.")

    # ---- the coupling measure, which is the actual mechanism question -----
    print("\n=== within-unit coupling: does correct recognition govern action? ===")
    cpl = []
    for arm in sorted(RECOGNITION_ARMS):
        by_unit = {}
        for r in rows:
            if r["intervention"] != arm or r["parsed"] != "True":
                continue
            by_unit.setdefault(r["unit"], {})[r["dependence"]] = r
        both_ok = notok = 0
        sens_ok = sens_not = 0
        for u, d in by_unit.items():
            if set(d) != set(DEPENDENCE):
                continue
            ok = all(d[x]["recog_primary_ok"] == "True" for x in DEPENDENCE)
            # independence-sensitive = flipped on SAME, held source on INDEP
            sens = (d["same_root"]["verdict"] == "flip"
                    and d["indep_root"]["verdict"] == "source")
            if ok:
                both_ok += 1
                sens_ok += sens
            else:
                notok += 1
                sens_not += sens
        cpl.append({
            "intervention": arm,
            "n_recognized_both": both_ok,
            "P(sensitive|recognized)": round(sens_ok / both_ok, 3) if both_ok else None,
            "n_misrecognized": notok,
            "P(sensitive|misrecognized)": round(sens_not / notok, 3) if notok else None})
    if cpl:
        show(cpl, list(cpl[0].keys()))
        write_csv("results/e13_coupling.csv", cpl, list(cpl[0].keys()))
    print("  If these two columns are equal, the model's own reported structure")
    print("  is NOT connected to what it does -- falsification rule 6, and the")
    print("  strongest form of the dissociation.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DECIDER)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    analyse(a.model) if a.analyse else run(a.model, a.offset, a.limit)
