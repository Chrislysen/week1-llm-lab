"""lineage_matrix.py: the full exposure matrix. 36 instances x 6 conditions.

Exposure is CONTROLLED directly -- no selectors are involved -- so a decision
failure here cannot be a retrieval failure in disguise. That separation is the
whole reason the benchmark exists.

216 model calls. Decision authority inversion is measured ONLY in the `both`
and `both_recovery` conditions, because it is only defined where the
authoritative source and a conflicting derived representation were both
actually in front of the model.

Run:  python lineage_matrix.py
"""
import json
import statistics

from budget import Budget
from experiment import show, write_csv
from lineage_bench import (AUTHORITY_RULE, EXPOSURES, all_instances, expose,
                           plan_instruction, render_dialogue)
from lineage_eval import check_plan, parse_plan, score
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

MODEL = "llama3.2:3b"
TEMPERATURE = 0
CONDITIONS = list(EXPOSURES)

SYSTEM = (
    "You are an operations engineer. You have just read a short discussion "
    "about {setting}. Produce the plan they agreed on, following everything "
    "that was established in the discussion.\n\n" + AUTHORITY_RULE
)


def ask(client, instance, condition):
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            "DISCUSSION\n----------\n"
            f"{render_dialogue(expose(instance, condition))}\n\n"
            f"{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=100_000, max_seconds=300)
    return ask_structured(
        client=client, model=MODEL, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def main(offset=0, limit=None, out_tag=""):
    """Chunkable: long single runs kept getting killed, so the matrix is run
    in slices and merged. Each slice writes its own artifacts."""
    client = OllamaClient()
    instances = all_instances()[offset:None if limit is None else offset + limit]
    rows, detail = [], []

    total = len(instances) * len(CONDITIONS)
    print(f"=== exposure matrix: {len(instances)} instances x "
          f"{len(CONDITIONS)} conditions = {total} calls ===")
    print(f"    model {MODEL}, temp {TEMPERATURE}, exposure controlled, no selectors\n")

    done = 0
    for inst in instances:
        for cond in CONDITIONS:
            res = ask(client, inst, cond)
            text = res.accepted_text or res.last_text or ""
            sc = score(inst, expose(inst, cond), text)
            chk = check_plan(text, inst)
            dai = sc["decision_authority_inversion"]
            rows.append({
                "instance": inst.id, "domain": inst.domain, "graph": inst.graph,
                "condition": cond,
                "parsed": chk.parsed, "retries": res.retries,
                "constraint_recall": chk.constraint_recall,
                "violations": len(chk.violated),
                "violated": "|".join(chk.violated),
                "success": chk.success,
                "n_actions": len(chk.actions),
                "unknown_actions": len(chk.unknown_actions),
                "dai_eligible": dai["eligible"],
                "dai_follows_source": dai["follows_source"],
                "dai_follows_corruption": dai["follows_corruption"],
                "dai_follows_neither": dai["follows_neither"],
                "dai_rate": dai["rate"],
                "corr_eligible": sc["corruption_susceptibility"]["eligible"],
                "corr_adopted": sc["corruption_susceptibility"]["adopted"],
                "corr_rate": sc["corruption_susceptibility"]["rate"],
                "sup_eligible": sc["supersession_respected"]["eligible"],
                "sup_rate": sc["supersession_respected"]["rate"],
                "rec_eligible": sc["recovery"]["eligible"],
                "rec_rate": sc["recovery"]["rate"],
                "util_source": sc["utilization"]["direct_source"],
                "util_source_n": sc["utilization"]["direct_source_n"],
                "util_faithful": sc["utilization"]["faithful_relay"],
                "util_faithful_n": sc["utilization"]["faithful_relay_n"],
                "prompt_tokens": sum(e.prompt_tokens for e in res.attempts),
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
            })
            detail.append({"instance": inst.id, "condition": cond,
                           "plan_text": text, "score": sc})
            done += 1
        print(f"  [{done:>3}/{total}] {inst.id}")

    write_csv(f"results/e2_matrix_runs{out_tag}.csv", rows, list(rows[0].keys()))
    with open(f"results/e2_matrix_detail{out_tag}.json", "w") as f:
        json.dump(detail, f, indent=2)
    if out_tag:
        print(f"slice written: offset={offset} n={len(instances)} rows={len(rows)}")
        return

    def agg(g, num, den):
        n = sum(r[num] for r in g)
        d = sum(r[den] for r in g)
        return (round(n / d, 4) if d else None), n, d

    print("\n=== per condition, over 36 instances ===")
    summary = []
    for cond in CONDITIONS:
        g = [r for r in rows if r["condition"] == cond]
        parsed = [r for r in g if r["parsed"]]
        dai_rate, dai_c, dai_t = agg(
            g, "dai_follows_corruption", "dai_eligible")
        # The inversion ratio uses source+corruption only, excluding "neither".
        sc_den = sum(r["dai_follows_source"] + r["dai_follows_corruption"] for r in g)
        summary.append({
            "condition": cond,
            "n": len(g),
            "parse_rate": round(len(parsed) / len(g), 4),
            "mean_recall": round(statistics.mean(
                r["constraint_recall"] for r in parsed), 4) if parsed else None,
            "success_rate": round(sum(r["success"] for r in g) / len(g), 4),
            "dai_eligible": dai_t,
            "dai_follows_source": sum(r["dai_follows_source"] for r in g),
            "dai_follows_corruption": dai_c,
            "dai_follows_neither": sum(r["dai_follows_neither"] for r in g),
            "dai_rate": round(dai_c / sc_den, 4) if sc_den else None,
            "corr_rate": agg(g, "corr_adopted", "corr_eligible")[0],
            "corr_n": agg(g, "corr_adopted", "corr_eligible")[2],
            "sup_eligible": sum(r["sup_eligible"] for r in g),
            "rec_eligible": sum(r["rec_eligible"] for r in g),
            "mean_actions": round(statistics.mean(
                r["n_actions"] for r in parsed), 2) if parsed else None,
        })
    show(summary, list(summary[0].keys()))
    write_csv("results/e2_matrix_summary.csv", summary, list(summary[0].keys()))

    print("\n=== decision authority inversion, by domain (condition=both) ===")
    both = [r for r in rows if r["condition"] == "both"]
    grid = []
    for d in sorted({r["domain"] for r in both}):
        g = [r for r in both if r["domain"] == d]
        src = sum(r["dai_follows_source"] for r in g)
        cor = sum(r["dai_follows_corruption"] for r in g)
        nei = sum(r["dai_follows_neither"] for r in g)
        grid.append({"domain": d, "follows_source": src,
                     "follows_corruption": cor, "follows_neither": nei,
                     "inversion_rate": round(cor / (src + cor), 4) if src + cor else None})
    show(grid, list(grid[0].keys()))

    print("\n=== corruption_only vs both: does the source rescue the decision? ===")
    for cond in ("corruption_only", "both", "both_recovery"):
        g = [r for r in rows if r["condition"] == cond]
        a = sum(r["corr_adopted"] for r in g)
        e = sum(r["corr_eligible"] for r in g)
        rec_n = sum(r["rec_eligible"] for r in g)
        rec_ok = sum((r["rec_rate"] or 0) * r["rec_eligible"] for r in g)
        line = (f"  {cond:<16} corruption adopted {a}/{e}"
                f"  ({round(a / e, 4) if e else 'n/a'})")
        if rec_n:
            line += f"   recovery {round(rec_ok):.0f}/{rec_n}"
        print(line)

    print("\nwrote results/e2_matrix_runs.csv, e2_matrix_summary.csv, "
          "e2_matrix_detail.json")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--tag", default="")
    a = p.parse_args()
    main(offset=a.offset, limit=a.limit, out_tag=a.tag)
