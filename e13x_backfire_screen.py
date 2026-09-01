"""e13x_backfire_screen.py: does the normative-principle backfire generalise?

EXPLORATORY SCREEN. Declared in docs/protocols/E13X-backfire-screen.md before
any call; no claim can follow from it.

WHAT IT REUSES, UNCHANGED. E13's frozen prompts (lineage_e13.build_prompt on
the frozen E12 units), E13's validators and scorer, temperature 0. Only three
of E13's five arms are run -- `default`, `identify`, `normative` -- because the
question is whether the PRINCIPLE (normative minus identify) raises adoption
of the unsupported contradiction in deciders other than llama3.2:3b.
Output goes to results/e13x_*.csv/json, never to E13's files.

Run:  python e13x_backfire_screen.py --model aya-expanse:8b --offset 0 --limit 36
"""
import argparse
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import (TEMPERATURE, make_validator, recognition_correct,
                             schema_hint)
from e12_powered import verdict
from lineage_bench import all_instances, plan_instruction
from lineage_e12 import all_units
from lineage_e13 import DEPENDENCE, DIAGNOSTIC, build_prompt, corpus_hash
from lineage_eval import check_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

ARMS = ["default", "identify", "normative"]


def cells():
    return [(a, d) for a in ARMS for d in DEPENDENCE]


def run(model, offset, limit):
    by_id = {i.id: i for i in all_instances()}
    units = all_units()[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    print(f"=== E13-X backfire screen: {model}, {len(units)} units x "
          f"{len(cells())} cells, prompts {corpus_hash(plan_instruction)} ===\n")
    rows, detail = [], []
    for i, rec in enumerate(units, 1):
        inst = by_id[rec["instance"]]
        pi = plan_instruction(inst)
        for arm, dep in cells():
            prompt = build_prompt(rec, dep, arm, pi)
            messages = [{"role": "system",
                         "content": SYSTEM.format(setting=inst.setting)},
                        {"role": "user", "content": prompt}]
            budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000,
                            max_seconds=600)
            res = ask_structured(
                client=client, model=model, temperature=TEMPERATURE,
                messages=messages, validate=make_validator(arm),
                budget=budget, speaker="Operator", expected=schema_hint(arm))
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            v = verdict(inst, rec, chk.actions) if chk.parsed else ""
            recog = (res.value or {}).get("recog") if res.value else None
            p_ok, s_ok = recognition_correct(arm, dep, recog)
            first = res.attempts[0] if res.attempts else None
            rows.append({
                "model": model, "unit": rec["unit"],
                "instance": rec["instance"], "domain": rec["domain"],
                "intervention": arm, "dependence": dep,
                "diagnostic": arm in DIAGNOSTIC,
                "prompt_words": len(prompt.split()),
                "prompt_tokens": first.prompt_tokens if first else "",
                "attempts": len(res.attempts),
                "parsed": chk.parsed, "verdict": v,
                "ready": chk.ready if chk.parsed else "",
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
    from experiment import write_csv
    write_csv(f"results/e13x_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e13x_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)
    print(f"\nwrote results/e13x_{tag}_o{offset}.csv  "
          f"(mean {statistics.mean(r['seconds'] for r in rows):.1f}s/call, "
          f"{client.transport_retries} transport retries)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    a = p.parse_args()
    run(a.model, a.offset, a.limit)
