"""e10_independence.py: does evidential DEPENDENCE matter, once everything else is matched?

Protocol: docs/protocols/E10-lineage-independence-v1.md. Preregistered; this
file is committed with ZERO E10 results present, and git ancestry is the proof.

THE LOAD-BEARING TEST IS H3: `indep_root` vs `same_root`. Both arms show a
source and two support messages, identical in count, speakers, order, position,
sentence skeletons and length to the word, with a byte-identical contradiction.
They differ in one thing -- whether the support traces to ONE evidential root or
THREE.

If H3 is null, the honest conclusion is that this is generic
repetition/corroboration, which is thoroughly pre-empted, and the lineage
direction is retired. That outcome is written into the kill rules and is not
negotiable after the fact.

MEASURE. Every arm is scored on the same binary: does the plan order the two
actions the way the SOURCE says, or the way the LAST message says? Reported as a
three-way split so an ambiguous plan is never silently counted as either.

    contradiction arms   `flip` = adopted an UNSUPPORTED contradiction   (bad)
    supersession arms    `flip` = accepted a LEGITIMATE revision          (good)

Same computation, opposite valence. Both are printed with their valence stated,
because a single "adoption" column that means opposite things in different rows
is how a reader gets misled.

Run:  python e10_independence.py --model llama3.2:3b --limit 12
      python e10_independence.py --analyse
      python e10_independence.py --manipulation-check
"""
import argparse
import csv
import glob
import json
import math
import random
import statistics

from budget import Budget
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_e10 import (ARMS, BASES, N_ARMS, SUPERSESSION_ARMS, all_e10,
                         corpus_hash, exposure, ground_truth, render)
from lineage_eval import check_plan, obeys, parse_plan
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured, extract_json_object

TEMPERATURE = 0
DECIDER = "llama3.2:3b"

SYSTEM = (
    "You are an operations engineer. You have just read a short discussion "
    "about {setting}. Produce the plan they agreed on, following everything "
    "that was established in the discussion."
)

#: Smallest effect of interest for H3, fixed in the protocol BEFORE scoring.
#: Below this, and with a CI that excludes larger effects, H3 is reported as an
#: equivalence-supported null rather than as "not significant".
SESOI = 0.10

#: The secondary family, Holm-corrected. H3 is primary and stands alone.
SECONDARY = [("H1", "bare", "filler"),
             ("H2", "filler", "same_root"),
             ("H4a", "same_root", "same_root_nospk"),
             ("H4b", "indep_root", "indep_root_nospk"),
             ("H5", "same_root", "same_root_super"),
             ("H5b", "bare_super", "same_root_super")]


def verdict(instance, e10, arm, actions):
    """`source` / `flip` / `neither`, against this arm's own ground truth.

    `flip` means the plan follows the LAST message rather than the source's
    original ordering. In contradiction arms that is adoption of a falsehood; in
    supersession arms it is compliance with a legitimate revision.
    """
    from lineage_bench import Constraint
    orig = {x.id: x for x in instance.constraints}[e10.constraint_id]
    flipped = Constraint(id=orig.id, kind="before", a=orig.b, b=orig.a)
    s, f = obeys(orig, actions), obeys(flipped, actions)
    if s and not f:
        return "source"
    if f and not s:
        return "flip"
    return "neither"


def ask(client, model, instance, e10, arm):
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            "DISCUSSION\n----------\n"
            f"{render(exposure(e10, arm))}\n\n{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(
        client=client, model=model, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def mcnemar(per, a, b, key="flip"):
    """Exact paired binomial. Returns (p, n_a_only, n_b_only)."""
    n01 = sum(1 for x in per.values()
              if x.get(a) == key and x.get(b) not in (None, key))
    n10 = sum(1 for x in per.values()
              if x.get(b) == key and x.get(a) not in (None, key))
    n = n01 + n10
    if n == 0:
        return None, n01, n10
    k = min(n01, n10)
    return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n,
               1.0), n01, n10


def bootstrap_ci(per, a, b, key="flip", reps=10000, seed=20260901):
    """Percentile CI for the paired difference, resampling INSTANCES.

    The instance is the sampling unit, so the bootstrap resamples instances --
    not messages, not model calls. Seed is fixed and declared.
    """
    ids = [i for i, x in per.items() if a in x and b in x]
    if not ids:
        return None, None
    rng = random.Random(seed)
    diffs = []
    for _ in range(reps):
        pick = [ids[rng.randrange(len(ids))] for _ in ids]
        fa = sum(per[i][a] == key for i in pick) / len(pick)
        fb = sum(per[i][b] == key for i in pick) / len(pick)
        diffs.append(fb - fa)
    diffs.sort()
    return diffs[int(0.025 * reps)], diffs[int(0.975 * reps)]


def holm(pvals):
    """Holm-Bonferroni. Returns adjusted p in the original order."""
    idx = sorted(range(len(pvals)), key=lambda i: (pvals[i] is None, pvals[i]))
    m = sum(1 for p in pvals if p is not None)
    out, running = [None] * len(pvals), 0.0
    rank = 0
    for i in idx:
        if pvals[i] is None:
            continue
        adj = min(1.0, (m - rank) * pvals[i])
        running = max(running, adj)          # enforce monotonicity
        out[i] = running
        rank += 1
    return out


def run(model, offset, limit):
    insts = all_instances()
    e10s = all_e10()
    pairs = list(zip(insts, e10s))[offset:None if limit is None else offset + limit]
    client = OllamaClient()
    print(f"=== E10 lineage independence: {model}, {len(pairs)} instances x "
          f"{N_ARMS} arms, corpus {corpus_hash()} ===\n")

    rows, detail = [], []
    for k, (inst, e) in enumerate(pairs, 1):
        for arm, *_ in ARMS:
            res = ask(client, model, inst, e, arm)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            v = verdict(inst, e, arm, chk.actions) if chk.parsed else ""
            rows.append({
                "model": model, "instance": inst.id, "domain": inst.domain,
                "arm": arm, "supersession": arm in SUPERSESSION_ARMS,
                "constraint": e.constraint_id,
                "n_messages": len(exposure(e, arm)),
                "n_roots": (1 if arm.startswith("same_root")
                            else 3 if arm.startswith("indep_root") else 0),
                "parsed": chk.parsed, "verdict": v,
                "constraint_recall": chk.constraint_recall,
                "seconds": round(sum(x.seconds for x in res.attempts), 2),
            })
            detail.append({"model": model, "instance": inst.id, "arm": arm,
                           "plan_text": text})
        print(f"  [{k:>2}/{len(pairs)}] {inst.id:<20} " + " ".join(
            f"{a[0][:9]}:{rows[-N_ARMS + i]['verdict'][:4] or '----'}"
            for i, a in enumerate(ARMS)))

    tag = model.replace(":", "-").replace(".", "")
    write_csv(f"results/e10_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e10_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e10_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call)")


def load(model=None):
    rows = []
    for p in sorted(glob.glob("results/e10_*_o*.csv")):
        if "manip" in p:
            continue
        rows.extend(csv.DictReader(open(p, newline="")))
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
    return [r for r in rows if model is None or r["model"] == model]


def analyse(model=DECIDER):
    rows = load(model)
    if not rows:
        raise SystemExit("no E10 results yet")
    per = {}
    for r in rows:
        if r["parsed"]:
            per.setdefault(r["instance"], {})[r["arm"]] = r["verdict"]

    print(f"=== E10 lineage independence -- {model} ===")
    print(f"  corpus {corpus_hash()}   n = {len(per)} instances\n")

    table, rate = [], {}
    for arm, *_ in ARMS:
        g = [r for r in rows if r["arm"] == arm and r["parsed"]]
        s = sum(r["verdict"] == "source" for r in g)
        f = sum(r["verdict"] == "flip" for r in g)
        rate[arm] = round(f / (s + f), 4) if s + f else None
        table.append({
            "arm": arm, "roots": g[0]["n_roots"] if g else "",
            "msgs": g[0]["n_messages"] if g else "", "n": len(g),
            "source": s, "flip": f,
            "neither": sum(r["verdict"] == "neither" for r in g),
            "flip_rate": rate[arm],
            "valence": "accepted valid update" if arm in SUPERSESSION_ARMS
                       else "adopted false claim"})
    cols = list(table[0].keys())
    show(table, cols)
    write_csv("results/e10_summary.csv", table, cols)
    print("  `flip` = plan follows the LAST message, not the source's ordering.")
    print("  In contradiction arms that is BAD; in supersession arms it is GOOD.")

    # ---- H3, the primary test, alone and uncorrected -------------------
    print("\n=== H3 -- PRIMARY. Does evidential dependence matter? ===")
    p3, n_same, n_ind = mcnemar(per, "same_root", "indep_root")
    lo, hi = bootstrap_ci(per, "same_root", "indep_root")
    d = (rate["indep_root"] - rate["same_root"]
         if None not in (rate["indep_root"], rate["same_root"]) else None)
    print(f"  same_root  (1 root)  flip rate {rate['same_root']}")
    print(f"  indep_root (3 roots) flip rate {rate['indep_root']}")
    print(f"  paired difference {d:+.4f}   discordant {n_ind}-{n_same}   "
          f"p = {'n/a' if p3 is None else f'{p3:.4g}'}")
    if lo is not None:
        print(f"  95% bootstrap CI over instances: [{lo:+.4f}, {hi:+.4f}]")

    print()
    if p3 is not None and p3 < 0.05:
        print("  H3 SURVIVES. Evidential dependence changes the decision with")
        print("  count, wording, speakers, order, position and length matched.")
        print("  Next per protocol: replicate across >=3 model families.")
    elif (d is not None and abs(d) < SESOI and lo is not None
          and lo > -SESOI and hi < SESOI):
        print(f"  H3 IS AN EQUIVALENCE-SUPPORTED NULL. |diff| < {SESOI} and the")
        print(f"  95% CI [{lo:+.4f}, {hi:+.4f}] excludes effects larger than")
        print(f"  {SESOI} in BOTH directions. This is not 'p > .05'; it is")
        print("  positive evidence that the model does not distinguish one")
        print("  evidential root from three.")
        print("\n  KILL RULE FIRES: the effect is generic repetition /")
        print("  corroboration, which is thoroughly pre-empted. RETIRE the")
        print("  lineage novelty direction and write the narrow result memo.")
    else:
        print("  H3 IS NOT SUPPORTED AND NOT EQUIVALENCE-SUPPORTED. The study")
        print("  is underpowered for the effect size observed. Do NOT read this")
        print("  as 'no difference' -- report it as inconclusive at n = 36.")

    # ---- secondary family, Holm-corrected ------------------------------
    print("\n=== secondary family (Holm-corrected over 6 tests) ===")
    raw, sec = [], []
    for name, a, b in SECONDARY:
        p, n01, n10 = mcnemar(per, a, b)
        raw.append(p)
        sec.append({"hyp": name, "contrast": f"{a} vs {b}",
                    "flip_a": rate[a], "flip_b": rate[b],
                    "discordant": f"{n10}-{n01}", "p_raw": p})
    for row, adj in zip(sec, holm(raw)):
        row["p_holm"] = None if adj is None else round(adj, 4)
        row["p_raw"] = None if row["p_raw"] is None else float(f"{row['p_raw']:.4g}")
    scols = ["hyp", "contrast", "flip_a", "flip_b", "discordant", "p_raw", "p_holm"]
    show(sec, scols)
    write_csv("results/e10_hypotheses.csv", sec, scols)

    print("\n  H4 is the speaker check. If the C/D contrast is unchanged with")
    print("  speaker labels stripped, the mechanism is evidence multiplicity,")
    print("  NOT social or multi-agent source weighting, and must not be")
    print("  described as either.")
    print("  H5b is the clean hysteresis test (identical source and identical")
    print("  supersession tail; differs only by the two support messages).")
    print("  H5 confounds authority framing with tail length -- see the")
    print("  protocol; it is descriptive only.")

    # ---- hysteresis reading --------------------------------------------
    b0, b1 = rate.get("bare_super"), rate.get("same_root_super")
    b2 = rate.get("indep_root_super")
    if None not in (b0, b1):
        print("\n=== hysteresis ===")
        print(f"  valid update accepted with NO prior support   {b0}")
        print(f"  ... after 2 same-root support messages        {b1}")
        print(f"  ... after 2 independent-root support messages {b2}")
        if b1 < b0:
            print("  Prior support REDUCES acceptance of a legitimate update.")
            print("  That is evidence inertia, not authority reasoning, and it")
            print("  is a finding in its own right regardless of H3.")
        else:
            print("  Prior support does not impair valid updating here.")


def manipulation_check(model, limit):
    """PREREGISTERED, NON-DECISION. Can the model even see the manipulation?

    H3 failing is ambiguous between "cannot perceive basis identity" and
    "perceives it but does not weight it evidentially". This resolves that, and
    never contributes to any decision metric.
    """
    insts, e10s = all_instances(), all_e10()
    pairs = list(zip(insts, e10s))[:limit]
    client = OllamaClient()
    print(f"=== manipulation check: {model} (NON-DECISION) ===\n")
    rows = []
    for inst, e in pairs:
        for arm, expected in (("same_root", 1), ("indep_root", 3)):
            msgs = [
                {"role": "system", "content":
                    "You read a short operations discussion and report what it "
                    "cites. Reply with a JSON object and nothing else."},
                {"role": "user", "content":
                    f"DISCUSSION\n----------\n{render(exposure(e, arm))}\n\n"
                    'How many DISTINCT named documents or records are cited in '
                    'the discussion above? Reply with exactly: {"count": <n>}'},
            ]
            reply = client.chat(model, msgs, TEMPERATURE)
            blob = extract_json_object(reply.text or "")
            got = None
            if blob:
                try:
                    got = json.loads(blob).get("count")
                except json.JSONDecodeError:
                    pass
            rows.append({"instance": inst.id, "arm": arm, "expected": expected,
                         "reported": got, "correct": got == expected})
        print(f"  {inst.id:<20} same:{rows[-2]['reported']} "
              f"indep:{rows[-1]['reported']}")
    write_csv("results/e10_manip_check.csv", rows, list(rows[0].keys()))
    acc = statistics.mean(r["correct"] for r in rows)
    print(f"\n  accuracy {acc:.0%} over {len(rows)} probes")
    print("  If this is high and H3 still fails, the model PERCEIVES evidential")
    print("  dependence and declines to weight it -- the interesting negative.")
    print("  If it is low, the manipulation was not perceptible and H3 says")
    print("  nothing about evidential reasoning.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DECIDER)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    p.add_argument("--manipulation-check", action="store_true")
    a = p.parse_args()
    if a.analyse:
        analyse(a.model)
    elif a.manipulation_check:
        manipulation_check(a.model, a.limit or 12)
    else:
        run(a.model, a.offset, a.limit)
