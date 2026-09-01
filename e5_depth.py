"""e5_depth.py: does a distortion get adopted more when it sits further from its source?

Four conditions per instance, ground truth identical in all of them:

    d1        S + C1                 corruption one hop from the source
    d2        S + L1 + C2            one faithful restatement in between
    d3        S + L1 + L2 + C3       two faithful restatements in between
    control   S + L1 + L2 + L3       no corruption, same message count as d3

The control separates depth from context length: d3 shows four messages, so
without it a d1-to-d3 difference could just be more text.

Primary measure: `follows_corruption` -- does the plan order the two actions the
way the DISTORTION says, or the way the SOURCE says? Reported as a three-way
split (source / corruption / neither) so an ambiguous plan is never silently
counted as either.

Run:  python e5_depth.py --model llama3.2:3b
"""
import argparse
import json
import statistics

from budget import Budget
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_depth import MAX_DEPTH, build_chain, follows_corruption
from lineage_eval import check_plan, parse_plan
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

TEMPERATURE = 0
CONDITIONS = [("d1", 1, True), ("d2", 2, True), ("d3", 3, True),
              ("control", 3, False), ("d1_padded", 1, True)]

SYSTEM = (
    "You are an operations engineer. You have just read a short discussion "
    "about {setting}. Produce the plan they agreed on, following everything "
    "that was established in the discussion."
)


def render(messages):
    return "\n".join(f"{m.speaker}: {m.text}" for m in messages)


def messages_for(chain, name, depth, corrupt):
    """`d1_padded` holds message count and corruption position at the d3 values
    while replacing the faithful links with irrelevant filler."""
    if name == "d1_padded":
        return chain.padded(MAX_DEPTH - 1)
    return chain.exposure(depth, corrupt)


def ask(client, model, instance, chain, name, depth, corrupt):
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


def main(model, offset, limit):
    client = OllamaClient()
    instances = all_instances()[offset:None if limit is None else offset + limit]
    tag = model.replace(":", "-").replace(".", "")
    print(f"=== E5 relay depth: {model}, {len(instances)} instances "
          f"x {len(CONDITIONS)} conditions ===\n")

    rows, detail = [], []
    for k, inst in enumerate(instances, 1):
        chain = build_chain(inst)
        for name, depth, corrupt in CONDITIONS:
            res = ask(client, model, inst, chain, name, depth, corrupt)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            verdict = (follows_corruption(inst, chain, chk.actions)
                       if chk.parsed else None)
            rows.append({
                "model": model, "instance": inst.id, "domain": inst.domain,
                "graph": inst.graph, "condition": name, "depth": depth,
                "corrupt": corrupt, "constraint": chain.constraint_id,
                "n_messages": len(messages_for(chain, name, depth, corrupt)),
                "parsed": chk.parsed,
                "verdict": verdict or "",
                "follows_source": verdict == "source",
                "follows_corruption": verdict == "corruption",
                "neither": verdict == "neither",
                "constraint_recall": chk.constraint_recall,
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
            })
            detail.append({"model": model, "instance": inst.id,
                           "condition": name, "plan_text": text})
        print(f"  [{k:>2}/{len(instances)}] {inst.id:<20} " + "  ".join(
            f"{c[0]}:{rows[-len(CONDITIONS) + i]['verdict'][:4] or '----'}"
            for i, c in enumerate(CONDITIONS)))

    write_csv(f"results/e5_depth_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e5_depth_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)

    print("\n=== adoption of the distortion by depth ===")
    out = []
    for name, depth, corrupt in CONDITIONS:
        g = [r for r in rows if r["condition"] == name and r["parsed"]]
        if not g:
            continue
        n = len(g)
        src = sum(r["follows_source"] for r in g)
        cor = sum(r["follows_corruption"] for r in g)
        out.append({
            "condition": name, "depth": depth, "corrupt": corrupt,
            "n": n, "msgs": g[0]["n_messages"],
            "follows_source": src, "follows_corruption": cor,
            "neither": sum(r["neither"] for r in g),
            "adoption": round(cor / (src + cor), 4) if src + cor else None,
            "recall": round(statistics.mean(
                r["constraint_recall"] for r in g
                if r["constraint_recall"] is not None), 4),
        })
    show(out, list(out[0].keys()))
    print("\n  `adoption` = corruption / (source + corruption), so an ambiguous")
    print("  plan is excluded from the ratio rather than counted as either.")
    print(f"\nwrote results/e5_depth_{tag}_o{offset}.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama3.2:3b")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    a = p.parse_args()
    main(a.model, a.offset, a.limit)
