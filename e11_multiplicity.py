"""e11_multiplicity.py: is E10's null a fact about the model, or about k=2?

Protocol: docs/protocols/E11-multiplicity-v1.md. Preregistered; committed with
zero E11 results present.

THIS IS AN ATTACK ON E10'S OWN CONCLUSION. E10 found same_root and indep_root
identical at exactly k=2 and concluded the model assigns zero weight to
evidential dependence. The serious competing explanation is that two agreeing
messages already saturate resistance, so nothing measured at k=2 could have
moved. E11 varies k and reads the curves.

H7 IS CHECKED FIRST AND IT CAN RETRACT E10. If `same_k1 ~ same_k2 ~ same_k3`
with no step anywhere, resistance is saturated across the whole tested range,
E10's null is UNINFORMATIVE, and the claim "the model assigns zero weight to
evidential dependence" must be withdrawn and replaced with "the E10 design could
not have detected such an effect". That outcome is written down first on purpose.

Run:  python e11_multiplicity.py --limit 12
      python e11_multiplicity.py --analyse
"""
import argparse
import csv
import glob
import json
import statistics

from budget import Budget
from e10_independence import (DECIDER, SESOI, SYSTEM, bootstrap_ci, holm,
                              mcnemar)
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_e11 import (ARMS, K_VALUES, N_ARMS, all_e11, corpus_hash,
                         exposure, kind_and_k, n_roots, render)
from lineage_eval import check_plan, obeys, parse_plan
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

TEMPERATURE = 0


def verdict(instance, rec, actions):
    """`source` / `flip` / `neither`. No arm here supersedes, so ground truth is
    always the original ordering and `flip` is always adoption of a falsehood."""
    from lineage_bench import Constraint
    orig = {x.id: x for x in instance.constraints}[rec["constraint"]]
    flipped = Constraint(id=orig.id, kind="before", a=orig.b, b=orig.a)
    s, f = obeys(orig, actions), obeys(flipped, actions)
    if s and not f:
        return "source"
    if f and not s:
        return "flip"
    return "neither"


def ask(client, model, instance, rec, arm):
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            "DISCUSSION\n----------\n"
            f"{render(exposure(rec, arm))}\n\n{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(
        client=client, model=model, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def run(model, offset, limit):
    insts, recs = all_instances(), all_e11()
    pairs = list(zip(insts, recs))[offset:None if limit is None else offset + limit]
    client = OllamaClient()
    print(f"=== E11 multiplicity: {model}, {len(pairs)} instances x {N_ARMS} "
          f"arms, corpus {corpus_hash()} ===\n")

    rows, detail = [], []
    for i, (inst, rec) in enumerate(pairs, 1):
        for arm in ARMS:
            kind, k = kind_and_k(arm)
            res = ask(client, model, inst, rec, arm)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            v = verdict(inst, rec, chk.actions) if chk.parsed else ""
            rows.append({
                "model": model, "instance": inst.id, "domain": inst.domain,
                "arm": arm, "kind": kind, "k": k,
                "roots": n_roots(rec, arm),
                "n_messages": len(exposure(rec, arm)),
                "parsed": chk.parsed, "verdict": v,
                "seconds": round(sum(x.seconds for x in res.attempts), 2),
            })
            detail.append({"model": model, "instance": inst.id, "arm": arm,
                           "plan_text": text})
        print(f"  [{i:>2}/{len(pairs)}] {inst.id:<20} " + " ".join(
            f"{a}:{rows[-N_ARMS + j]['verdict'][:4] or '----'}"
            for j, a in enumerate(ARMS)))

    tag = model.replace(":", "-").replace(".", "")
    write_csv(f"results/e11_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e11_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e11_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call)")


def load(model=None):
    rows = []
    for p in sorted(glob.glob("results/e11_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
    return [r for r in rows if model is None or r["model"] == model]


def analyse(model=DECIDER):
    rows = load(model)
    if not rows:
        raise SystemExit("no E11 results yet")
    per = {}
    for r in rows:
        if r["parsed"]:
            per.setdefault(r["instance"], {})[r["arm"]] = r["verdict"]

    print(f"=== E11 multiplicity -- {model} ===")
    print(f"  corpus {corpus_hash()}   n = {len(per)} instances\n")

    rate, table = {}, []
    for arm in ARMS:
        g = [r for r in rows if r["arm"] == arm and r["parsed"]]
        s = sum(r["verdict"] == "source" for r in g)
        f = sum(r["verdict"] == "flip" for r in g)
        rate[arm] = round(f / (s + f), 4) if s + f else None
        table.append({"arm": arm, "kind": g[0]["kind"], "k": g[0]["k"],
                      "roots": g[0]["roots"], "n": len(g),
                      "source": s, "flip": f,
                      "neither": sum(r["verdict"] == "neither" for r in g),
                      "flip_rate": rate[arm]})
    cols = list(table[0].keys())
    show(table, cols)
    write_csv("results/e11_summary.csv", table, cols)

    print("\n  flip rate = adopted the unsupported contradiction (lower is more")
    print("  resistant). Curves by k:")
    print(f"      {'k':<4}{'filler':>10}{'same':>10}{'indep':>10}")
    print(f"      {'0':<4}{rate['bare']:>10}{rate['bare']:>10}{rate['bare']:>10}")
    for k in K_VALUES:
        print(f"      {k:<4}{rate[f'filler_k{k}']:>10}"
              f"{rate[f'same_k{k}']:>10}{rate[f'indep_k{k}']:>10}")

    # ---- H7 FIRST. It can retract E10. --------------------------------
    print("\n=== H7 -- CHECKED FIRST. Does the manipulation move at all? ===")
    steps, moved = [], False
    for a, b in (("bare", "same_k1"), ("same_k1", "same_k2"),
                 ("same_k2", "same_k3")):
        p, n01, n10 = mcnemar(per, a, b)
        steps.append({"step": f"{a} -> {b}", "from": rate[a], "to": rate[b],
                      "discordant": f"{n10}-{n01}",
                      "p": None if p is None else float(f"{p:.4g}")})
        if p is not None and p < 0.05:
            moved = True
    show(steps, ["step", "from", "to", "discordant", "p"])
    write_csv("results/e11_dose.csv", steps, ["step", "from", "to",
                                              "discordant", "p"])
    if not moved:
        print("\n  H7 FLAT. No step in the same-root dose curve is significant.")
        print("  SATURATION CANNOT BE RULED OUT, so E10's null is UNINFORMATIVE.")
        print("  PREREGISTERED CONSEQUENCE: retract 'the model assigns zero")
        print("  weight to evidential dependence' and replace it with 'the E10")
        print("  design could not have detected such an effect'. Everything")
        print("  below is reported but must not be read as evidence about")
        print("  evidential reasoning.")
    else:
        print("\n  H7 HOLDS: adding correlated support keeps moving the")
        print("  decision, so the design has room. A null in H6 is therefore")
        print("  informative rather than saturated.")

    # ---- H6, the primary family --------------------------------------
    print("\n=== H6 -- PRIMARY. same vs indep at each k (Holm over 3) ===")
    raw, fam = [], []
    for k in K_VALUES:
        a, b = f"same_k{k}", f"indep_k{k}"
        p, n01, n10 = mcnemar(per, a, b)
        lo, hi = bootstrap_ci(per, a, b)
        raw.append(p)
        fam.append({"k": k, "roots_same": 1, "roots_indep": k + 1,
                    "same": rate[a], "indep": rate[b],
                    "diff": round(rate[b] - rate[a], 4),
                    "discordant": f"{n10}-{n01}",
                    "ci": None if lo is None else f"[{lo:+.3f},{hi:+.3f}]",
                    "p_raw": None if p is None else float(f"{p:.4g}")})
    for row, adj in zip(fam, holm(raw)):
        row["p_holm"] = None if adj is None else round(adj, 4)
    fcols = ["k", "roots_same", "roots_indep", "same", "indep", "diff",
             "discordant", "ci", "p_raw", "p_holm"]
    show(fam, fcols)
    write_csv("results/e11_h6.csv", fam, fcols)

    sig = [r for r in fam if r["p_holm"] is not None and r["p_holm"] < 0.05]
    print()
    if sig:
        ks = ", ".join(f"k={r['k']}" for r in sig)
        print(f"  H6 SIGNIFICANT at {ks}. E10's null was k-SPECIFIC. Narrow the")
        print("  E10 conclusion to k=2 and reopen the lineage question only at")
        print("  the k where the effect appears, pending replication.")
    elif moved:
        print("  H6 NULL AT EVERY k, WITH A WORKING DOSE-RESPONSE. The")
        print("  manipulation demonstrably moves the decision; evidential")
        print("  independence still does nothing. E10's conclusion is confirmed")
        print("  and extended across k = 1, 2, 3.")
        big = [r for r in fam if abs(r["diff"]) >= SESOI]
        if big:
            print(f"  CAUTION: |diff| >= SESOI ({SESOI}) at "
                  f"{', '.join('k=' + str(r['k']) for r in big)} despite p >= .05")
            print("  -- underpowered there, not equivalent. Do not call it zero.")
    else:
        print("  H6 null, but H7 was flat, so this says nothing. See above.")

    # ---- effective evidence count -------------------------------------
    if moved:
        print("\n=== effective evidence count ===")
        print("  If k correlated restatements sit on the same curve as k")
        print("  independent sources, the dependence discount is zero.")
        for k in K_VALUES:
            s, d = rate[f"same_k{k}"], rate[f"indep_k{k}"]
            print(f"    k={k}: same-root(1 root) {s}   indep({k + 1} roots) {d}"
                  f"   gap {d - s:+.4f}")

    # ---- H8, dilution -------------------------------------------------
    print("\n=== H8 -- dilution has its own dose-response ===")
    d8 = []
    for k in K_VALUES:
        p, n01, n10 = mcnemar(per, f"filler_k{k}", f"same_k{k}")
        d8.append({"k": k, "filler": rate[f"filler_k{k}"],
                   "same": rate[f"same_k{k}"], "discordant": f"{n10}-{n01}",
                   "p": None if p is None else float(f"{p:.4g}")})
    show(d8, ["k", "filler", "same", "discordant", "p"])
    print("  filler vs same at matched k and matched length isolates SEMANTIC")
    print("  corroboration from the effect of simply adding messages.")


def cross():
    """Phase 6: the principal contrasts across model families.

    THE PRINCIPAL CONTRAST IS NOW H8, NOT H6. E10's independence result was
    retracted as underpowered (docs/protocols/E10-H3-RETRACTION.md), so the
    finding worth replicating is the one that is actually well-powered: does
    paraphrastic corroboration beat length-matched filler, dose-dependently?

    H6 is still reported per model, but it carries the same power problem
    everywhere and no equivalence claim may be made from it.
    """
    rows = load()
    models = sorted({r["model"] for r in rows})
    print("=== E11 across model families ===")
    print(f"  corpus {corpus_hash()}   n = 36 instances per model\n")

    fam = {"llama3.2:3b": "Llama (Meta)", "aya-expanse:8b": "Aya (Cohere)",
           "qwen2.5:7b-instruct": "Qwen (Alibaba)",
           "qwen2.5:3b-instruct": "Qwen (Alibaba)",
           "qwen2.5:14b-instruct": "Qwen (Alibaba)"}

    out = []
    for m in models:
        per = {}
        for r in rows:
            if r["model"] == m and r["parsed"]:
                per.setdefault(r["instance"], {})[r["arm"]] = r["verdict"]

        def rate(a):
            g = [v[a] for v in per.values() if a in v]
            s = sum(x == "source" for x in g)
            f = sum(x == "flip" for x in g)
            return round(f / (s + f), 4) if s + f else None

        row = {"model": m, "family": fam.get(m, "?"),
               "bare": rate("bare")}
        for k in K_VALUES:
            row[f"same_k{k}"] = rate(f"same_k{k}")
        # H8 at k=3, the strongest corroboration contrast
        p8, n01, n10 = mcnemar(per, "filler_k3", "same_k3")
        row["H8_k3"] = None if p8 is None else float(f"{p8:.3g}")
        row["H8_disc"] = f"{n10}-{n01}"
        # H7: does the dose curve move at all for this model?
        p7, _, _ = mcnemar(per, "bare", "same_k3")
        row["H7"] = None if p7 is None else float(f"{p7:.3g}")
        # H6 at k=3
        p6, m01, m10 = mcnemar(per, "same_k3", "indep_k3")
        row["H6_k3"] = None if p6 is None else float(f"{p6:.3g}")
        row["H6_disc"] = f"{m10}-{m01}"
        out.append(row)

    cols = (["model", "family", "bare"] + [f"same_k{k}" for k in K_VALUES]
            + ["H7", "H8_k3", "H8_disc", "H6_k3", "H6_disc"])
    show(out, cols)
    write_csv("results/e11_cross_model.csv", out, cols)

    fams = {r["family"] for r in out}
    h8ok = sum(1 for r in out if r["H8_k3"] is not None and r["H8_k3"] < 0.05)
    print(f"\n  H8 (corroboration beats matched-length filler) significant in "
          f"{h8ok}/{len(out)} deciders across {len(fams)} families.")
    print("  H7 is the dose-response; H6 is the independence contrast, which")
    print("  remains underpowered in every model and supports NO equivalence")
    print("  claim -- see docs/protocols/E10-H3-RETRACTION.md.")
    if len(fams) < 3:
        print(f"\n  ONLY {len(fams)} DISTINCT FAMILIES. qwen2.5 at several scales")
        print("  is ONE family, not three. Per the campaign kill rule, an effect")
        print("  surviving fewer than 3 families is a model-specific behavioural")
        print("  finding and must be reported as such.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--cross", action="store_true")
    p.add_argument("--model", default=DECIDER)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    if a.cross:
        cross()
    elif a.analyse:
        analyse(a.model)
    else:
        run(a.model, a.offset, a.limit)
