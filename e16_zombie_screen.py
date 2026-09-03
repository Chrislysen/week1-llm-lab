"""e16_zombie_screen.py: does a rejected constraint stay in the plan?

EXPLORATORY SCREEN. Declared in docs/protocols/E16-zombie-screen.md before
any call; no claim can follow from it.

WHAT IT REUSES, UNCHANGED. E10's decider system prompt, E13's plan validator
and parse/retry machinery, the frozen plan instruction, temperature 0, and the
context policies from context.py exactly as the base engine applies them at
finalisation. The corpus is lineage_e16.py (hash checked at start).

Stage 1:  --policy full           the whole dialogue is in context
Stage 2:  --policy dense:35 ...   the policy's selection is in context; what
                                  it kept is recorded per unit, so the read is
                                  conditional on realised exposure.

Run:  python e16_zombie_screen.py --model qwen2.5:3b-instruct --policy full
"""
import argparse
import json
import statistics

from budget import Budget
from context import (BM25Budget, DenseBudget, FusionBudget, RandomBudget,
                     RecencyBudget, query_for_finalisation)
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from experiment import show, write_csv
from lineage_bench import plan_instruction
from lineage_e16 import all_dialogues, corpus_hash, message_list, render
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

CORPUS_HASH = "70f136a47f5779c8"
COLUMNS = ["model", "policy", "instance", "rotation", "slot", "constraint",
           "action", "status", "proposal_in_context", "reply_in_context",
           "exposure", "parsed", "included", "n_actions", "ready", "attempts",
           "prompt_tokens"]

_POLICIES = {
    "recency": RecencyBudget,
    "random": lambda w: RandomBudget(w, seed=0),
    "bm25": BM25Budget,
    "dense": DenseBudget,
    "fusion": FusionBudget,
}


def make_policy(spec):
    if spec == "full":
        return None
    name, w = spec.split(":")
    return _POLICIES[name](int(w))


def slug(s):
    return s.replace(".", "").replace(":", "-")


def context_for(policy, inst, dia):
    """(system, rendered discussion, kept dialogue positions)."""
    system = SYSTEM.format(setting=inst.setting)
    if policy is None:
        return system, render(dia), set(range(len(dia)))
    msgs = message_list(system, dia)
    query = query_for_finalisation(msgs, plan_instruction(inst))
    policy.select(msgs, query=query)
    kept = sorted(set(policy._last["selected_ids"]) | {len(dia) - 1})
    return system, render([dia[i] for i in kept]), set(kept)


def exposure_of(status, prop_in, reply_in):
    if status == "never":
        return "n/a"
    if status == "proposed":
        return "proposal" if prop_in else "absent"
    return {(True, True): "both", (True, False): "proposal_only",
            (False, True): "reply_only", (False, False): "neither"}[(prop_in, reply_in)]


def run(model, policy_spec, offset, limit):
    assert corpus_hash() == CORPUS_HASH, "E16 corpus disturbed"
    policy = make_policy(policy_spec)
    ds = all_dialogues()[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    print(f"=== E16 zombie screen: {model}, policy {policy_spec}, "
          f"{len(ds)} dialogues, corpus {CORPUS_HASH} ===\n")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst, dia = d["instance"], d["dialogue"]
        system, body, kept = context_for(policy, inst, dia)
        user = f"DISCUSSION\n----------\n{body}\n\n{plan_instruction(inst)}"
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": user}]
        budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
        res = ask_structured(client=client, model=model, temperature=TEMPERATURE,
                             messages=messages, validate=validate, budget=budget,
                             speaker="Operator", expected=expected)
        text = res.accepted_text or res.last_text or ""
        plan, _err = parse_plan(text)
        actions = plan["actions"] if plan else []
        pos = {}
        for k, (_, _, tag) in enumerate(dia):
            pos.setdefault(tag[1], {})[tag[0]] = k
        for u in d["units"]:
            p = pos.get(u["constraint"], {})
            prop_in = p.get("proposal") in kept if "proposal" in p else False
            reply_in = p.get("reply") in kept if "reply" in p else False
            rows.append({
                "model": model, "policy": policy_spec, "instance": u["instance"],
                "rotation": u["rotation"], "slot": u["slot"],
                "constraint": u["constraint"], "action": u["action"],
                "status": u["status"], "proposal_in_context": prop_in,
                "reply_in_context": reply_in,
                "exposure": exposure_of(u["status"], prop_in, reply_in),
                "parsed": plan is not None,
                "included": (u["action"] in actions) if plan else None,
                "n_actions": len(actions) if plan else None,
                "ready": plan["ready"] if plan else None,
                "attempts": len(res.attempts),
                "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None,
            })
        detail.append({"instance": inst.id, "rotation": d["rotation"],
                       "kept": sorted(kept), "prompt": user, "output": text,
                       "attempts": [a.content for a in res.attempts]})
        flag = "" if plan else "  PARSE-FAIL"
        print(f"  [{i:3}/{len(ds)}] {inst.id:22} r{d['rotation']} "
              f"actions={len(actions)}{flag}")
    stem = f"results/e16_{slug(model)}_{slug(policy_spec)}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    print(f"\n  transport retries: {client.transport_retries}")
    print(f"  wrote {stem}.csv / .json\n")
    summary = []
    for st in ("accepted", "proposed", "rejected", "never"):
        rs = [r for r in rows if r["status"] == st and r["parsed"]]
        summary.append({"status": st, "n": len(rs),
                        "included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None})
    show(summary, ["status", "n", "included"])
    parsed = sum(r["parsed"] for r in rows) / len(rows)
    print(f"\n  parse rate {parsed:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--policy", default="full")
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.model, a.policy, a.offset, a.limit)
