"""e7_modeb.py: E5 again, on relays a model wrote. The external validity check.

PREDECLARED. This file is committed BEFORE the decision run, with the corpus
frozen and hashed and the analysis fixed, so the git history shows the
hypotheses were written down before the numbers existed. Nothing below is
tuned after seeing a result; if the result contradicts the prediction, the
prediction stands as written and the contradiction is the finding.

WHAT IS HELD FIXED FROM E5. The decider (llama3.2:3b), the temperature (0), the
system prompt, the plan instruction, the five conditions, the exposure schedule,
the scoring function, and the base instances with their ground truth. Verified
mechanically by test_lineage_modeb.test_exposure_schedule_is_identical_to_mode_a.

WHAT CHANGES. The relay text only. E5's relays came from four fixed templates;
E7's are written by qwen2.5:7b-instruct and certified by qwen2.5:14b-instruct.
One variable moves. That is the experiment.

MODE A REFERENCE (corrected corpus 9dd2cea1, n = 36):

    d1 0.7778   d2 0.6111   d3 0.4167   control 0.0000   d1_padded 0.8000
    d1 vs d3          p = 0.0010     monotone gradient with depth
    d1 vs d1_padded   p = 1.0000     length alone does nothing

PREDICTIONS, in the order they will be checked:

  P1  adoption(d1) > adoption(d3).  The direction is the whole claim. If it
      reverses or vanishes, E5's gradient is a property of four sentence
      templates, not of relay depth.
  P2  adoption(d1_padded) is close to adoption(d1), not to adoption(d3).
      Length still does nothing; corroboration is what moves adoption.
  P3  adoption(control) is at or near 0. With no contradiction present the
      plan follows the source. This is the sanity floor -- if it fails, the
      Mode B corpus is broken and P1/P2 are uninterpretable, so it is checked
      FIRST at analysis time regardless of the order above.

FALSIFICATION, stated so it cannot be renegotiated later:

    If adoption(d1) <= adoption(d3) in Mode B, then E5's depth effect does not
    survive natural relay text, and docs/ must report the Mode A finding as
    SCRIPTING-DEPENDENT. Not "weaker in Mode B", not "directionally consistent".
    Reported as an artefact, which is what sec.8 of the benchmark design
    committed to doing.

A RIVAL EXPLANATION MODE B RULES OUT FOR FREE. Source bias (Dai et al., KDD
2024) says a model favours ITS OWN generations. The decider here wrote none of
the text it reads -- a different model wrote every relay -- so whatever survives
is not self-preference.

A LIMIT MODE B DOES NOT RULE OUT. The relays are model-written but the exposure
is still curated: a real dialogue decides for itself how many times to restate a
claim. Mode B makes the TEXT natural, not the CONVERSATION. Saying so is not a
hedge; it is the difference between this and a claim about real deployments.

Run:  python e7_modeb.py --limit 12          # chunked, like every other run
      python e7_modeb.py --analyse           # after all chunks land
"""
import argparse
import csv
import glob
import json
import math
import statistics

from budget import Budget
from e5_depth import CONDITIONS, SYSTEM, messages_for, render
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_depth import follows_corruption
from lineage_eval import check_plan, parse_plan
from lineage_modeb import certified, fixture_hash, modeb_chain
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

TEMPERATURE = 0
DECIDER = "llama3.2:3b"          # E5's model, deliberately unchanged

#: Mode A on the corrected corpus. Held here as the comparison target so the
#: analysis cannot quietly drift toward whatever Mode B produced.
MODE_A = {"d1": 0.7778, "d2": 0.6111, "d3": 0.4167, "control": 0.0,
          "d1_padded": 0.8000}


def ask(client, model, instance, chain, name, depth, corrupt):
    """Byte-identical to E5's prompt construction, by import rather than copy."""
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            "DISCUSSION\n----------\n"
            f"{render(messages_for(chain, name, depth, corrupt))}\n\n"
            f"{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(
        client=client, model=model, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def mcnemar(per, a, b):
    """Exact paired test, same as E5. Returns None when no pair discordant."""
    n01 = sum(1 for x in per.values()
              if x.get(a) == "corruption" and x.get(b) == "source")
    n10 = sum(1 for x in per.values()
              if x.get(a) == "source" and x.get(b) == "corruption")
    n = n01 + n10
    if n == 0:
        return None, n01, n10
    k = min(n01, n10)
    p = min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)
    return p, n01, n10


def analyse():
    rows = []
    for p in sorted(glob.glob("results/e7_modeb_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    if not rows:
        raise SystemExit("no E7 results yet")
    for r in rows:
        r["parsed"] = r["parsed"] == "True"

    print(f"=== E7 Mode B: {DECIDER} deciding on model-written relays ===")
    print(f"  corpus {fixture_hash()}   n = "
          f"{len({r['instance'] for r in rows})} instances\n")

    out, adopt = [], {}
    for name, depth, corrupt in CONDITIONS:
        g = [r for r in rows if r["condition"] == name and r["parsed"]]
        if not g:
            continue
        src = sum(r["verdict"] == "source" for r in g)
        cor = sum(r["verdict"] == "corruption" for r in g)
        a = round(cor / (src + cor), 4) if src + cor else None
        adopt[name] = a
        out.append({"condition": name, "n": len(g),
                    "follows_source": src, "follows_corruption": cor,
                    "neither": sum(r["verdict"] == "neither" for r in g),
                    "adoption_B": a, "adoption_A": MODE_A.get(name),
                    "delta": (round(a - MODE_A[name], 4)
                              if a is not None and name in MODE_A else None)})
    show(out, list(out[0].keys()))
    write_csv("results/e7_modeb_summary.csv", out, list(out[0].keys()))

    per = {}
    for r in rows:
        if r["parsed"]:
            per.setdefault(r["instance"], {})[r["condition"]] = r["verdict"]

    print("\n=== paired McNemar, the same five comparisons as E5 ===")
    stats = []
    for a, b in (("d1", "d2"), ("d2", "d3"), ("d1", "d3"),
                 ("d1", "d1_padded"), ("d1_padded", "d3")):
        p, n01, n10 = mcnemar(per, a, b)
        # Formatted, not rounded. round(9.537e-07, 4) is 0.0, and printing a
        # p-value as "0.0" states something no finite test can support.
        stats.append({"pair": f"{a} vs {b}", "discordant": f"{n10}-{n01}",
                      "p": None if p is None else
                           f"{p:.4f}" if p >= 1e-4 else f"{p:.3e}"})
    show(stats, ["pair", "discordant", "p"])
    write_csv("results/e7_modeb_mcnemar.csv", stats, ["pair", "discordant", "p"])

    print("\n=== the predeclared checks ===")
    ctrl = adopt.get("control")
    print(f"  P3  control at or near 0                     "
          f"{ctrl}  -> {'HOLDS' if ctrl is not None and ctrl <= 0.05 else 'FAILS'}")
    if ctrl is None or ctrl > 0.05:
        print("      The floor failed. P1 and P2 are NOT interpretable; the")
        print("      corpus is the suspect, not the hypothesis.")
        return
    d1, d3, dp = adopt.get("d1"), adopt.get("d3"), adopt.get("d1_padded")
    p1 = d1 is not None and d3 is not None and d1 > d3
    print(f"  P1  adoption(d1) > adoption(d3)              "
          f"{d1} > {d3}  -> {'HOLDS' if p1 else 'FAILS'}")
    if dp is not None and d1 is not None and d3 is not None:
        near_d1 = abs(dp - d1) < abs(dp - d3)
        print(f"  P2  d1_padded tracks d1, not d3             "
              f"{dp}  -> {'HOLDS' if near_d1 else 'FAILS'}")

    print()
    if p1:
        print("  The direction survives model-written relays. E5's gradient is")
        print("  not an artefact of four sentence templates.")
    else:
        print("  FALSIFIED AS PREDECLARED. adoption(d1) <= adoption(d3) on")
        print("  natural relay text, so E5's depth effect is SCRIPTING-")
        print("  DEPENDENT and docs/ must report it as such.")
    print("\n  Magnitudes are NOT compared across modes as though the two")
    print("  corpora were interchangeable -- different text, different task")
    print("  difficulty. The direction and the length control are what")
    print("  transfer, and they are what was predeclared.")

    exploratory(adopt, per)


def revision_framing():
    """How often each mode's corruption is phrased as a REVISION, not a relay.

    Measured because the two modes produced different SHAPES, and a difference
    in how the contradiction is worded is the first thing that could cause that.
    Constant across conditions within a mode -- the same corruption text appears
    at every depth -- so it cannot touch P1/P2/P3, which are within-mode.
    """
    from lineage_bench import all_instances
    from lineage_depth import build_chain
    from lineage_modeb import modeb_chain
    cues = ("actually", "changed", "update", "revis", "correct", "instead",
            "procedure is", "new order", "swap")
    out = {}
    for mode, fn in (("A", build_chain), ("B", modeb_chain)):
        out[mode] = sum(any(c in fn(i).corrupted[0].text.lower() for c in cues)
                        for i in all_instances())
    return out


def exploratory(adopt, per):
    """EXPLORATORY. Everything here was looked at AFTER the numbers existed.

    Kept separate from the predeclared block on purpose. These are hypotheses
    generated by this run, not results of it, and nothing below may be reported
    as a finding without a fresh predeclared test on data it has not seen.
    """
    print("\n=== EXPLORATORY -- generated after seeing the result ===")
    print("  Not predeclared. Hypotheses, not findings.\n")

    print("  1. THE SHAPE DIFFERS BETWEEN MODES, though the direction does not.")
    print(f"       mode A   0.7778 -> 0.6111 -> 0.4167    gradient")
    print(f"       mode B   {adopt.get('d1')} -> {adopt.get('d2')} -> "
          f"{adopt.get('d3')}    step at the first link")
    print("     In Mode B one corroborating restatement does essentially all the")
    print("     work and a second adds nothing (d2 vs d3 p = 1.0000). In Mode A")
    print("     the decline was spread across both steps.")
    print("     NOTE: this project retracted a 'step function' reading of Mode A")
    print("     TWICE. That history is a reason for more caution here, not less.")
    print("     A step in Mode B does not retroactively vindicate it in Mode A --")
    print("     the Mode A data still shows a gradient and still says so.\n")

    rf = revision_framing()
    print("  2. A CANDIDATE EXPLANATION, MEASURED RATHER THAN ASSERTED.")
    print(f"     Corruptions phrased as a REVISION rather than a plain relay:")
    print(f"       mode A  {rf['A']}/36        mode B  {rf['B']}/36")
    print("     Mode A draws its corruption from the shared T_REVISION pool, so")
    print("     it often arrives as an update ('The procedure is now...'). Mode")
    print("     B's generator was asked for a normal chat message and mostly")
    print("     wrote a flat assertion. An update from a colleague is a stronger")
    print("     reason to change a plan than a bare contradiction, which would")
    print("     make Mode A's corruption harder to shrug off at every depth.")
    print("     This is consistent with the magnitudes. It is not tested here,")
    print("     and consistency is not evidence.\n")

    print("  3. WHAT WOULD TEST IT: hold the relay text fixed and vary ONLY the")
    print("     corruption's framing, revision vs plain. That is a new")
    print("     experiment with its own predeclaration, not a re-reading of")
    print("     this one.")


def main(offset, limit):
    chains = certified()
    if not chains:
        raise SystemExit("no certified Mode B corpus; run: python lineage_modeb.py")
    instances = [i for i in all_instances() if i.id in chains]
    instances = instances[offset:None if limit is None else offset + limit]
    client = OllamaClient()
    print(f"=== E7 Mode B: {DECIDER}, {len(instances)} instances "
          f"x {len(CONDITIONS)} conditions, corpus {fixture_hash()} ===\n")

    rows, detail = [], []
    for k, inst in enumerate(instances, 1):
        chain = modeb_chain(inst, chains)
        for name, depth, corrupt in CONDITIONS:
            res = ask(client, DECIDER, inst, chain, name, depth, corrupt)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            verdict = (follows_corruption(inst, chain, chk.actions)
                       if chk.parsed else None)
            rows.append({
                "model": DECIDER, "instance": inst.id, "domain": inst.domain,
                "graph": inst.graph, "condition": name, "depth": depth,
                "corrupt": corrupt, "constraint": chain.constraint_id,
                "n_messages": len(messages_for(chain, name, depth, corrupt)),
                "parsed": chk.parsed, "verdict": verdict or "",
                "constraint_recall": chk.constraint_recall,
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
            })
            detail.append({"model": DECIDER, "instance": inst.id,
                           "condition": name, "plan_text": text})
        print(f"  [{k:>2}/{len(instances)}] {inst.id:<20} " + "  ".join(
            f"{c[0]}:{rows[-len(CONDITIONS) + i]['verdict'][:4] or '----'}"
            for i, c in enumerate(CONDITIONS)))

    tag = DECIDER.replace(":", "-").replace(".", "")
    write_csv(f"results/e7_modeb_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e7_modeb_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e7_modeb_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    analyse() if a.analyse else main(a.offset, a.limit)
