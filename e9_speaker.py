"""e9_speaker.py: is it corroboration, or a speaker caught reversing himself?

PREDECLARED, and it exists because an adversarial audit of E7 found a defect
that E7's own gates could not see.

THE PROBLEM. In every arm of E5 and E7, the contradiction at depth 2 and 3 is
spoken by THE SAME VOICE that just made the corroborating restatement -- 36/36,
verified. At depth 1 and in `d1_padded` there is no prior restatement at all.
So across the whole design:

    arm          corroboration present    contradictor reverses himself
    d1                   no                          no
    d1_padded            no                          no
    d2                   yes                         yes  (36/36)
    d3                   yes                         yes  (36/36)

Those two columns are identical. `d1_padded` vs `d3` -- the load-bearing
comparison, the one with p = 1.526e-05 -- moves BOTH factors at once. Nothing in
E5 or E7 can attribute the effect to either. The headline in docs/findings.md is
therefore NOT IDENTIFIED, and the gate that was supposed to prevent exactly this
(`test_corroborators_come_from_more_than_one_speaker`) slices the contradiction
out of the list before checking, so it compares only L1 against L2.

The rival account is ordinary and plausible: a colleague who states an ordering
and then, two messages later, asserts the opposite is a person contradicting
himself, and a reader may discount him for that alone -- no corroboration
required.

THE FIX IS A 2x2. Same corpus, same text, same instances, same everything. The
ONLY thing that varies is which name is attached to which message.

                        contradictor is a       contradictor previously
                        FRESH voice             asserted the opposite
    no corroboration    d1_fresh                d1_self
    corroboration       d3_fresh                d3_self

    d1_fresh   S(A), C(D)
    d1_self    S(A), C(A)
    d3_fresh   S(A), L1(B), L2(C), C(D)
    d3_self    S(A), L1(B), L2(C), C(C)

`d3_self` reproduces E7's `d3` structure; `d1_self` is the previously
non-existent cell that makes the design a factorial rather than a diagonal.

WHAT EACH OUTCOME MEANS, fixed before the run:

  A  d3_* well below d1_* at BOTH speaker levels
     -> corroboration is the mechanism. E7's headline survives, now identified.
  B  *_self well below *_fresh at BOTH corroboration levels, with little or no
     corroboration effect
     -> E5/E7 measured SELF-REVERSAL. The corroboration claim is retracted in
        full, not softened.
  C  both main effects present
     -> both operate; report the corroboration effect only at the size it has
        with the speaker factor held fixed, i.e. d3_fresh vs d1_fresh.
  D  neither
     -> the effect does not survive re-labelling speakers, which would mean it
        was never about message content at all.

PRIMARY TEST, chosen in advance so it cannot be picked afterwards:
    d1_fresh vs d3_fresh, paired McNemar. Both have a fresh contradictor, so
    self-reversal is absent from both and only corroboration differs. If this is
    null, outcome B or D holds no matter what the other cells do.

Speakers are the only manipulated variable. Message TEXT is byte-identical to
the frozen Mode B corpus 4a2938565a36ee9f, which is not modified.

Run:  python e9_speaker.py --model llama3.2:3b --limit 18
      python e9_speaker.py --analyse
"""
import argparse
import csv
import glob
import json
import math
import statistics
from dataclasses import replace

from budget import Budget
from e5_depth import SYSTEM, render
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_depth import MAX_DEPTH, follows_corruption
from lineage_eval import check_plan, parse_plan
from lineage_modeb import certified, fixture_hash, modeb_chain
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

TEMPERATURE = 0
DECIDER = "llama3.2:3b"

#: Four roles, so "fresh voice" is genuinely a name that has not spoken yet.
#: The base corpus ships two; the extra two are plausible members of the same
#: incident channel and are used for SPEAKER LABELS ONLY -- no text changes.
A, B, C, D = ("Operations Lead", "Safety Auditor", "Network Engineer",
              "Duty Manager")

#: (arm, corroborated, self_reversal)
ARMS = [("d1_fresh", False, False), ("d1_self", False, True),
        ("d3_fresh", True, False), ("d3_self", True, True)]


def exposure(chain, arm):
    """Messages for one cell. Text comes from the frozen corpus untouched."""
    src = replace(chain.source, speaker=A)
    corrupt = chain.corrupted[0]
    if arm.startswith("d1"):
        voice = A if arm.endswith("self") else D
        return [src, replace(corrupt, speaker=voice)]
    l1 = replace(chain.faithful[0], speaker=B)
    l2 = replace(chain.faithful[1], speaker=C)
    voice = C if arm.endswith("self") else D
    return [src, l1, l2, replace(corrupt, speaker=voice)]


def ask(client, model, instance, msgs):
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            f"DISCUSSION\n----------\n{render(msgs)}\n\n"
            f"{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(
        client=client, model=model, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def mcnemar(per, a, b):
    n01 = sum(1 for x in per.values()
              if x.get(a) == "corruption" and x.get(b) == "source")
    n10 = sum(1 for x in per.values()
              if x.get(a) == "source" and x.get(b) == "corruption")
    n = n01 + n10
    if n == 0:
        return None, n01, n10
    k = min(n01, n10)
    return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n,
               1.0), n01, n10


def run(model, offset, limit):
    chains = certified()
    if len(chains) != 36:
        raise SystemExit(f"corpus is {len(chains)}/36; refusing to run partial")
    instances = [i for i in all_instances() if i.id in chains]
    instances = instances[offset:None if limit is None else offset + limit]
    client = OllamaClient()
    print(f"=== E9 speaker 2x2: {model}, {len(instances)} instances x "
          f"{len(ARMS)} arms, corpus {fixture_hash()} ===\n")

    rows, detail = [], []
    for k, inst in enumerate(instances, 1):
        chain = modeb_chain(inst, chains)
        for arm, corrob, selfrev in ARMS:
            msgs = exposure(chain, arm)
            res = ask(client, model, inst, msgs)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            verdict = (follows_corruption(inst, chain, chk.actions)
                       if chk.parsed else None)
            rows.append({
                "model": model, "instance": inst.id, "domain": inst.domain,
                "arm": arm, "corroborated": corrob, "self_reversal": selfrev,
                "n_messages": len(msgs),
                "contradictor": msgs[-1].speaker,
                "spoke_before": any(m.speaker == msgs[-1].speaker
                                    for m in msgs[:-1]),
                "parsed": chk.parsed, "verdict": verdict or "",
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
            })
            detail.append({"model": model, "instance": inst.id, "arm": arm,
                           "plan_text": text})
        print(f"  [{k:>2}/{len(instances)}] {inst.id:<20} " + "  ".join(
            f"{a[0]}:{rows[-len(ARMS) + i]['verdict'][:4] or '----'}"
            for i, a in enumerate(ARMS)))

    t = model.replace(":", "-").replace(".", "")
    write_csv(f"results/e9_speaker_{t}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e9_speaker_{t}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e9_speaker_{t}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call)")


def analyse():
    rows = []
    for p in sorted(glob.glob("results/e9_speaker_*_o*.csv")):
        rows.extend(csv.DictReader(open(p, newline="")))
    if not rows:
        raise SystemExit("no E9 results yet")
    for r in rows:
        r["parsed"] = r["parsed"] == "True"

    print("=== E9: corroboration vs self-reversal, crossed ===")
    print(f"  {DECIDER}, corpus {fixture_hash()}, "
          f"n = {len({r['instance'] for r in rows})} instances")
    print("  Only speaker labels differ between arms. Text is identical.\n")

    adopt, table = {}, []
    for arm, corrob, selfrev in ARMS:
        g = [r for r in rows if r["arm"] == arm and r["parsed"]]
        s = sum(r["verdict"] == "source" for r in g)
        c = sum(r["verdict"] == "corruption" for r in g)
        adopt[arm] = round(c / (s + c), 4) if s + c else None
        table.append({"arm": arm, "corroborated": corrob,
                      "self_reversal": selfrev, "n": len(g),
                      "source": s, "corruption": c,
                      "neither": sum(r["verdict"] == "neither" for r in g),
                      "adoption": adopt[arm]})
    cols = list(table[0].keys())
    show(table, cols)
    write_csv("results/e9_speaker_summary.csv", table, cols)

    print("\n              contradictor FRESH   contradictor SELF-REVERSING")
    print(f"  no corrob.        {adopt['d1_fresh']:<18} {adopt['d1_self']}")
    print(f"  corroborated      {adopt['d3_fresh']:<18} {adopt['d3_self']}")

    per = {}
    for r in rows:
        if r["parsed"]:
            per.setdefault(r["instance"], {})[r["arm"]] = r["verdict"]

    print("\n=== paired McNemar ===")
    stats = []
    for a, b, what in (("d1_fresh", "d3_fresh", "PRIMARY: corroboration, "
                        "speaker held fresh"),
                       ("d1_self", "d3_self", "corroboration, speaker held "
                        "self-reversing"),
                       ("d1_fresh", "d1_self", "self-reversal, no corrob."),
                       ("d3_fresh", "d3_self", "self-reversal, corroborated")):
        p, n01, n10 = mcnemar(per, a, b)
        stats.append({"comparison": f"{a} vs {b}", "isolates": what,
                      "discordant": f"{n10}-{n01}",
                      "p": None if p is None else
                           f"{p:.4f}" if p >= 1e-4 else f"{p:.2e}"})
    scols = ["comparison", "isolates", "discordant", "p"]
    show(stats, scols)
    write_csv("results/e9_speaker_mcnemar.csv", stats, scols)

    corrob_effect = adopt["d1_fresh"] - adopt["d3_fresh"]
    speaker_effect = ((adopt["d1_fresh"] - adopt["d1_self"])
                      + (adopt["d3_fresh"] - adopt["d3_self"])) / 2
    p_primary = mcnemar(per, "d1_fresh", "d3_fresh")[0]

    print("\n=== the predeclared reading ===")
    print(f"  corroboration effect, speaker held FRESH : "
          f"{corrob_effect:+.4f}  (p = {p_primary:.3e})")
    print(f"  self-reversal effect, averaged over corrob.: {speaker_effect:+.4f}")
    big = 0.10
    if corrob_effect > big and p_primary is not None and p_primary < 0.05:
        if speaker_effect > big:
            print("\n  OUTCOME C: both factors operate. The corroboration claim")
            print("  survives but ONLY at the size it has here, with the")
            print("  speaker factor held fixed -- not at the E7 magnitude,")
            print("  which bundled the two together.")
        else:
            print("\n  OUTCOME A: corroboration is the mechanism. The E7")
            print("  headline is identified after all; the audit's confound is")
            print("  real in the design but not load-bearing in the data.")
    elif speaker_effect > big:
        print("\n  OUTCOME B: E5/E7 measured SELF-REVERSAL, not corroboration.")
        print("  The corroboration claim is RETRACTED IN FULL -- not softened,")
        print("  not 'partly confounded'. docs/findings.md must be rewritten.")
    else:
        print("\n  OUTCOME D: neither factor survives re-labelling speakers.")
        print("  The effect was never about message content. Retract.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DECIDER)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--analyse", action="store_true")
    a = p.parse_args()
    analyse() if a.analyse else run(a.model, a.offset, a.limit)
