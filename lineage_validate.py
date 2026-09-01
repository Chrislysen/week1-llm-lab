"""lineage_validate.py: the small real-model validation gate for E2.

SIX instances (one per surface domain, each on a different constraint graph) x
THREE exposure conditions = 18 model calls. This is a gate, not an experiment.
It asks three yes/no questions about the instrument:

  clean solvability        source_only  -- can the model solve an instance at
                           all when the authoritative sources are present and
                           nothing contradicts them? If not, the benchmark is
                           too hard and any later signal is noise.

  corruption sensitivity   corruption_only -- when only a distorted derivative
                           is present, does the model adopt the distortion? If
                           it never does, the instrument cannot detect decision
                           authority inversion and the corruption is inert.

  legitimate supersession  supersession -- when an override is present, is the
                           model free of the lifted rule? A benchmark where
                           "always trust the earliest source" wins teaches
                           nothing.

Selectors are NOT involved. Exposure is controlled directly, so nothing here
depends on retrieval. Do not run all selectors over all 36 instances yet.

Run:  python lineage_validate.py
"""
import json
import statistics

from budget import Budget
from experiment import show, write_csv
from lineage_bench import (expose, generate_instance, plan_instruction,
                           render_dialogue)
from lineage_eval import check_plan, parse_plan, presence, score
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

MODEL = "llama3.2:3b"
TEMPERATURE = 0

#: One per domain, each on a different graph, so the gate spans both axes.
GATE = [
    ("payments", "chain"),
    ("robotics", "fork"),
    ("pharmacy", "join"),
    ("satellite", "diamond"),
    ("brewery", "twochain"),
    ("rail", "star"),
]

CONDITIONS = ["source_only", "corruption_only", "supersession"]

SYSTEM = (
    "You are an operations engineer. You have just read a short discussion "
    "between two colleagues about {setting}. Produce the plan they agreed on, "
    "following everything that was established in the discussion."
)


def ask(client, instance, condition):
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            f"DISCUSSION\n----------\n"
            f"{render_dialogue(expose(instance, condition))}\n\n"
            f"{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=100_000, max_seconds=300)
    return ask_structured(
        client=client, model=MODEL, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.',
    )


def main():
    client = OllamaClient()
    rows, records = [], []

    print("=== E2 validation gate: 6 instances x 3 conditions = 18 model calls ===")
    print(f"    model {MODEL}, temperature {TEMPERATURE}, exposure controlled "
          f"directly (no selectors)\n")

    for domain, graph in GATE:
        inst = generate_instance(domain, graph)
        cid = next(iter(inst.superseded))
        for condition in CONDITIONS:
            res = ask(client, inst, condition)
            text = res.accepted_text or res.last_text or ""
            sc = score(inst, expose(inst, condition), text)
            chk = check_plan(text, inst)

            row = {
                "instance": inst.id,
                "graph": graph,
                "condition": condition,
                "n_constraints": len(inst.constraints),
                "parsed": chk.parsed,
                "retries": res.retries,
                "constraint_recall": chk.constraint_recall,
                "violated": "|".join(chk.violated),
                "success": chk.success,
                "unknown_actions": len(chk.unknown_actions),
                "n_actions": len(chk.actions),
                "corruption_eligible": sc["corruption_susceptibility"]["eligible"],
                "corruption_adopted": sc["corruption_susceptibility"]["adopted"],
                "corruption_rate": sc["corruption_susceptibility"]["rate"],
                "supersession_eligible": sc["supersession_respected"]["eligible"],
                "supersession_rate": sc["supersession_respected"]["rate"],
                "direct_source_util": sc["utilization"]["direct_source"],
                "direct_source_n": sc["utilization"]["direct_source_n"],
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
                "prompt_tokens": sum(e.prompt_tokens for e in res.attempts),
            }
            rows.append(row)
            records.append({"row": row, "score": sc, "plan_text": text,
                            "superseded_constraint": cid})
            print(f"  {inst.id:<20} {condition:<16} "
                  f"recall {str(chk.constraint_recall):<6} "
                  f"viol {row['violated'] or '-':<8} "
                  f"corr {row['corruption_adopted']}/{row['corruption_eligible']} "
                  f"sup {str(row['supersession_rate']):<5} "
                  f"{row['seconds']}s")

    print("\n=== raw per-instance results ===")
    show(rows, list(rows[0].keys()))
    write_csv("results/e2_validation_runs.csv", rows, list(rows[0].keys()))
    with open("results/e2_validation_detail.json", "w") as f:
        json.dump(records, f, indent=2)

    print("\n=== gate readings (raw, no claims) ===")
    for cond in CONDITIONS:
        g = [r for r in rows if r["condition"] == cond]
        parsed = [r for r in g if r["parsed"]]
        recalls = [r["constraint_recall"] for r in parsed]
        line = (f"  {cond:<16} parsed {len(parsed)}/{len(g)}  "
                f"mean recall {statistics.mean(recalls):.4f}  "
                f"success {sum(r['success'] for r in g)}/{len(g)}")
        if cond == "corruption_only":
            elig = sum(r["corruption_eligible"] for r in g)
            adopt = sum(r["corruption_adopted"] for r in g)
            line += f"  corruption adopted {adopt}/{elig}"
        if cond == "supersession":
            rates = [r["supersession_rate"] for r in g
                     if r["supersession_rate"] is not None]
            line += (f"  supersession respected "
                     f"{sum(rates):.0f}/{len(rates)}" if rates else "  n/a")
        print(line)

    print("\nRaw readings only. No gate verdict is asserted here -- the three "
          "questions above are for review.")
    print("wrote results/e2_validation_runs.csv and e2_validation_detail.json")


if __name__ == "__main__":
    main()
