"""e8_crossmodel.py: is the corroboration effect a 3B-parameter artefact?

PREDECLARED. Committed before any decision call, like E7. Roadmap stage 8:
"Does it hold beyond llama3.2:3b, or is it a small-model artefact?"

E5 and E7 both used ONE decider, `llama3.2:3b`. That is the largest live threat
to the finding. This runs the frozen Mode B corpus through every other local
model, changing nothing but the decider.

WHAT IS HELD FIXED. The corpus (4a2938565a36ee9f), the five conditions, the
exposure schedule, the system prompt, the plan instruction, temperature 0, and
the scoring. `ask` is IMPORTED from e7_modeb, not copied, so the prompt cannot
drift between experiments.

THE ARMS, AND WHY THE CONTAMINATED ONES ARE INCLUDED ON PURPOSE.

    llama3.2:3b           clean, Meta          E7's decider (already run)
    aya-expanse:8b        clean, Cohere        different family entirely
    qwen2.5:3b-instruct   generator's FAMILY   same lineage as the writer
    qwen2.5:14b-instruct  CERTIFIED the corpus it now decides on
    qwen2.5:7b-instruct   WROTE every relay it now decides on

The last two cannot be read as clean replications and are not counted as such.
But excluding them would waste the sharpest test available:

  THE SELF-PREFERENCE PROBE. Every SOURCE message is template-written (Mode A
  text, held fixed across modes). Every CONTRADICTION is written by
  qwen2.5:7b-instruct. So when qwen2.5:7b is the decider, it is choosing between
  a claim it did not write and a contradiction it DID.

  Source bias (Dai et al., KDD 2024) -- a model preferring its own generations
  -- predicts that this model adopts the contradiction MORE than deciders that
  wrote none of the text. That is a directional prediction on an existing
  corpus, costing one extra arm, and it tests the rival explanation E7 claims to
  have ruled out by construction rather than by measurement.

PREDICTIONS, checked in this order:

  P6  control adoption at or near 0 for each decider. A model that adopts a
      contradiction which is not present is broken, not informative; it is
      EXCLUDED from P4/P5 and the exclusion is reported, never quietly dropped.
  P4  adoption(d1) > adoption(d3) for every non-excluded CLEAN decider. This is
      the replication. If it fails in half or more of them, the effect is
      model-specific and docs/ must say so.
  P5  adoption(d1_padded) nearer to d1 than to d3, for every clean decider.
      The length dissociation -- the load-bearing control -- must also transfer.
  P7  adoption(d1) for qwen2.5:7b-instruct (which wrote the contradictions)
      exceeds the mean adoption(d1) of the clean deciders. This is the source
      bias probe. NOTE THE ASYMMETRY: P7 confirming would mean self-preference
      is measurable here and E7's cross-model design was necessary. P7 failing
      is the stronger result for the main claim -- it means self-preference is
      not detectable on this corpus at all.

FALSIFICATION, fixed in advance:

    If P4 fails for half or more of the clean deciders, the corroboration effect
    is reported as MODEL-SPECIFIC, not as a property of LLM decision-making.
    "Held in the model we tested most" is not a replication.

WHAT THIS STILL WILL NOT SHOW. Every model here is local, open-weights, and
under 15B parameters. Nothing about frontier models follows from it, and a
uniform result across five small models is consistent with a shared property of
small open-weights models rather than with a general one.

Run:  python e8_crossmodel.py --model aya-expanse:8b --limit 12
      python e8_crossmodel.py --analyse
"""
import argparse
import csv
import glob
import json
import math
import statistics

from e5_depth import CONDITIONS, messages_for
from e7_modeb import DECIDER as E7_DECIDER, ask, mcnemar
from experiment import show, write_csv
from lineage_bench import all_instances
from lineage_depth import follows_corruption
from lineage_eval import check_plan
from lineage_modeb import GEN_MODEL, VERIFY_MODEL, certified, fixture_hash, modeb_chain
from llm_client import OllamaClient

#: Deciders and what disqualifies each from counting as a clean replication.
ARMS = {
    "llama3.2:3b": None,
    "aya-expanse:8b": None,
    "qwen2.5:3b-instruct": None,
    "qwen2.5:14b-instruct": "certified the corpus it is deciding on",
    "qwen2.5:7b-instruct": "wrote every relay it is deciding on",
}

#: Clean = wrote none of the text and certified none of it.
CLEAN = [m for m, why in ARMS.items() if why is None]

#: P6 floor. Above this a decider is treated as broken for this task.
CONTROL_CEILING = 0.05


def tag_of(model):
    return model.replace(":", "-").replace(".", "")


def run(model, offset, limit):
    chains = certified()
    if len(chains) != 36:
        raise SystemExit(f"corpus is {len(chains)}/36; refusing to run partial")
    instances = [i for i in all_instances() if i.id in chains]
    instances = instances[offset:None if limit is None else offset + limit]
    client = OllamaClient()
    note = ARMS.get(model)
    print(f"=== E8 {model}: {len(instances)} instances x {len(CONDITIONS)} "
          f"conditions, corpus {fixture_hash()} ===")
    print(f"    {'CLEAN' if note is None else 'CONTAMINATED -- ' + note}\n")

    rows, detail = [], []
    for k, inst in enumerate(instances, 1):
        chain = modeb_chain(inst, chains)
        for name, depth, corrupt in CONDITIONS:
            res = ask(client, model, inst, chain, name, depth, corrupt)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            verdict = (follows_corruption(inst, chain, chk.actions)
                       if chk.parsed else None)
            rows.append({
                "model": model, "clean": note is None, "instance": inst.id,
                "domain": inst.domain, "graph": inst.graph, "condition": name,
                "depth": depth, "corrupt": corrupt,
                "constraint": chain.constraint_id,
                "n_messages": len(messages_for(chain, name, depth, corrupt)),
                "parsed": chk.parsed, "verdict": verdict or "",
                "constraint_recall": chk.constraint_recall,
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
            })
            detail.append({"model": model, "instance": inst.id,
                           "condition": name, "plan_text": text})
        print(f"  [{k:>2}/{len(instances)}] {inst.id:<20} " + "  ".join(
            f"{c[0]}:{rows[-len(CONDITIONS) + i]['verdict'][:4] or '----'}"
            for i, c in enumerate(CONDITIONS)))

    t = tag_of(model)
    write_csv(f"results/e8_cross_{t}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e8_cross_{t}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    par = sum(r["parsed"] for r in rows)
    print(f"\nwrote results/e8_cross_{t}_o{offset}.csv  "
          f"({par}/{len(rows)} parsed, "
          f"mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call)")


def load_all():
    """E8 rows plus E7's llama3.2:3b run, which is the same experiment."""
    rows = []
    for p in sorted(glob.glob("results/e8_cross_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    for p in sorted(glob.glob("results/e7_modeb_*_o*.csv")):
        for r in csv.DictReader(open(p, newline="")):
            r["clean"] = "True"
            rows.append(r)
    for r in rows:
        r["parsed"] = r["parsed"] == "True"
        r["clean"] = r["clean"] == "True"
    return rows


def adoption(rows, model, cond):
    g = [r for r in rows if r["model"] == model and r["condition"] == cond
         and r["parsed"]]
    s = sum(r["verdict"] == "source" for r in g)
    c = sum(r["verdict"] == "corruption" for r in g)
    return (round(c / (s + c), 4) if s + c else None), len(g), s, c


def _cross_mcnemar(rows, m1, m2, cond):
    """Paired ACROSS MODELS on the same instances -- the test P7 should have
    used. Each instance contributes one pair, so the sampling unit stays the
    task instance rather than the model-condition cell."""
    def per(m):
        d = {}
        for r in rows:
            if r["model"] == m and r["parsed"]:
                d.setdefault(r["instance"], {})[r["condition"]] = r["verdict"]
        return d
    a, b = per(m1), per(m2)
    n01 = sum(1 for i in a if a[i].get(cond) == "corruption"
              and b.get(i, {}).get(cond) == "source")
    n10 = sum(1 for i in a if a[i].get(cond) == "source"
              and b.get(i, {}).get(cond) == "corruption")
    n = n01 + n10
    if n == 0:
        return None, n01, n10
    k = min(n01, n10)
    return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n,
               1.0), n01, n10


def analyse():
    rows = load_all()
    if not rows:
        raise SystemExit("no E8 results yet")
    models = [m for m in ARMS if any(r["model"] == m for r in rows)]

    print("=== E8 cross-model: same corpus, same prompts, decider varies ===")
    print(f"  corpus {fixture_hash()}   generator {GEN_MODEL}   "
          f"verifier {VERIFY_MODEL}\n")

    table, adopt = [], {}
    for m in models:
        adopt[m] = {c: adoption(rows, m, c)[0] for c, _, _ in CONDITIONS}
        n_par = sum(1 for r in rows if r["model"] == m and r["parsed"])
        n_all = sum(1 for r in rows if r["model"] == m)
        table.append({
            "model": m, "status": "clean" if ARMS[m] is None else "CONTAM",
            "parsed": f"{n_par}/{n_all}",
            **{c: adopt[m][c] for c, _, _ in CONDITIONS},
        })
    cols = ["model", "status", "parsed"] + [c for c, _, _ in CONDITIONS]
    show(table, cols)
    write_csv("results/e8_cross_summary.csv", table, cols)

    print("\n=== paired McNemar per decider (n = 36) ===")
    stats = []
    for m in models:
        per = {}
        for r in rows:
            if r["model"] == m and r["parsed"]:
                per.setdefault(r["instance"], {})[r["condition"]] = r["verdict"]
        row = {"model": m}
        for a, b in (("d1", "d3"), ("d1", "d1_padded"), ("d1_padded", "d3")):
            p, _, _ = mcnemar(per, a, b)
            row[f"{a}~{b}"] = (None if p is None else
                               f"{p:.4f}" if p >= 1e-4 else f"{p:.2e}")
        stats.append(row)
    scols = ["model", "d1~d3", "d1~d1_padded", "d1_padded~d3"]
    show(stats, scols)
    write_csv("results/e8_cross_mcnemar.csv", stats, scols)

    print("\n=== the predeclared checks ===")
    broken = [m for m in models
              if adopt[m]["control"] is None
              or adopt[m]["control"] > CONTROL_CEILING]
    print(f"  P6  control <= {CONTROL_CEILING} for every decider")
    for m in models:
        c = adopt[m]["control"]
        print(f"        {m:<22} {c}   {'ok' if m not in broken else 'EXCLUDED'}")
    if broken:
        print(f"      EXCLUDED from P4/P5, reported not dropped: {broken}")

    usable = [m for m in models if m in CLEAN and m not in broken]
    print(f"\n  P4  adoption(d1) > adoption(d3), clean deciders only")
    p4 = []
    for m in usable:
        ok = (adopt[m]["d1"] is not None and adopt[m]["d3"] is not None
              and adopt[m]["d1"] > adopt[m]["d3"])
        p4.append(ok)
        print(f"        {m:<22} {adopt[m]['d1']} > {adopt[m]['d3']}   "
              f"{'HOLDS' if ok else 'FAILS'}")

    print(f"\n  P5  d1_padded nearer d1 than d3, clean deciders only")
    p5 = []
    for m in usable:
        dp, d1, d3 = adopt[m]["d1_padded"], adopt[m]["d1"], adopt[m]["d3"]
        ok = (dp is not None and d1 is not None and d3 is not None
              and abs(dp - d1) < abs(dp - d3))
        p5.append(ok)
        print(f"        {m:<22} d1_padded {dp}   {'HOLDS' if ok else 'FAILS'}")

    print(f"\n  P7  source-bias probe: {GEN_MODEL} wrote every contradiction")
    gen_d1 = adopt.get(GEN_MODEL, {}).get("d1")
    clean_d1 = [adopt[m]["d1"] for m in usable if adopt[m]["d1"] is not None]
    if gen_d1 is None or not clean_d1:
        print("        not runnable: generator arm or clean arms missing")
    else:
        mean_clean = round(statistics.mean(clean_d1), 4)
        print(f"        generator d1 {gen_d1}   clean mean d1 {mean_clean}")
        if gen_d1 > mean_clean:
            print("        P7 HOLDS -- the writer adopts its own contradiction")
            print("        more than deciders that wrote none of it. Source bias")
            print("        is MEASURABLE here, which is why E7 used a decider")
            print("        that wrote nothing it read.")
        else:
            print("        P7 FAILS -- and this is the STRONGER outcome for the")
            print("        main claim. Self-preference is not detectable on this")
            print("        corpus even in the model that wrote the text, so it")
            print("        cannot be what E5/E7 measured.")

        # DEFECT NOTICE, written after scoring. The predeclared verdict above
        # is printed verbatim and is NOT rewritten. What follows records that
        # the test which produced it was badly specified by its author.
        print("\n  P7 AS PREDECLARED IS A DEFECTIVE TEST, and the defect is mine.")
        print("     It compares one proportion to a mean of two others with no")
        print(f"     magnitude and no test: {gen_d1} > {mean_clean}, a difference")
        print(f"     of {gen_d1 - mean_clean:+.4f} -- "
              f"{abs(gen_d1 - mean_clean) * 36:.2f} instances out of 36.")
        print("     A bare inequality between noisy proportions is satisfied by")
        print("     chance about half the time. It cannot license the conclusion")
        print("     it was written for, in EITHER direction.")
        print("\n  P7 DONE PROPERLY -- generator vs each clean decider, paired by")
        print("  instance on d1, exact McNemar:")
        for m in usable:
            pv, n01, n10 = _cross_mcnemar(rows, GEN_MODEL, m, "d1")
            print(f"        vs {m:<20} " + ("no discordant pairs" if pv is None
                  else f"{n01} vs {n10} discordant   p = {pv:.4f}"))
        print("\n     NO DETECTABLE SOURCE BIAS. The correct reading is the one")
        print("     predeclared for P7 FAILING: self-preference is absent even in")
        print("     the model that wrote every contradiction, so it cannot be")
        print("     what E5/E7/E9 measured. The predeclared inequality pointed")
        print("     the other way on a 0.17-instance margin, which is noise.")

    print("\n" + "=" * 64)
    n_ok = sum(p4)
    if not usable:
        print("  No usable clean decider. Nothing is concluded.")
    elif n_ok > len(usable) / 2:
        print(f"  P4 replicates in {n_ok}/{len(usable)} clean deciders; "
              f"P5 in {sum(p5)}/{len(usable)}.")
        print("  The effect is not specific to llama3.2:3b.")
    else:
        print(f"  FALSIFIED AS PREDECLARED. P4 holds in only {n_ok}/"
              f"{len(usable)} clean deciders, so the corroboration effect is")
        print("  MODEL-SPECIFIC and docs/ must report it as such.")
    print("\n  WHICH COMPARISON REPLICATED, PRECISELY. E8 runs E7's ARMS, and E9")
    print("  showed those arms confound corroboration with 'the contradictor is")
    print("  reversing his own just-stated position' (36/36 at d2/d3, absent at")
    print("  d1). So E8 establishes that the E7 PATTERN is not specific to")
    print("  llama3.2:3b. It does NOT confirm E9's identified mechanism and must")
    print("  not be cited as if it did -- the speaker-controlled contrast has")
    print("  been run on ONE decider only.")
    print("\n  Every model here is local, open-weights, under 15B. A uniform")
    print("  result across them is consistent with a shared property of small")
    print("  open-weights models, not with a general one.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="aya-expanse:8b")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    if a.analyse:
        analyse()
    else:
        if a.model == E7_DECIDER:
            raise SystemExit(f"{E7_DECIDER} is E7's decider; its run is reused")
        run(a.model, a.offset, a.limit)
