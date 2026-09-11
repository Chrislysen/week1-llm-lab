"""e29_memory_semantics.py: does a partner's restatement of a rejected step
raise enactment, and by an amount that depends on the memory design?

DECLARED in docs/protocols/E29-memory-semantics.md before any call.

WHAT IT REUSES, UNCHANGED. E10's decider system prompt, E13's validator and
parse/retry machinery, E17's frozen `pin4` plan instruction at |vocab| = 6,
temperature 0, the RetryingOllamaClient. The corpus is lineage_e29.py (both
hashes asserted at start).

One process block runs every cell of a dialogue back to back in a fixed
order -- designs (full, delete, addonly, wiki) inside arms (restated, neutral)
-- so the eight cells of a dialogue share a process and a position window.

Run:  python e29_memory_semantics.py --model llama3.2:3b --offset 0 --limit 20
      python e29_memory_semantics.py --model llama3.2:3b --dry-run
"""
import argparse
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e17_menu_law import plan_instruction
from experiment import show, write_csv
from lineage_e16 import corpus_hash as e16_hash
from lineage_bench import NEW_DOMAINS
from lineage_e29 import ARMS, DESIGNS, E16_HASH, all_e29_dialogues, context_block, corpus_hash
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

E29_HASH = "187a426616f26598"
#: E29-N, the second corpus (docs/protocols/E29N-second-corpus.md), pinned at declaration.
E29N_HASH = "7d33038c6c1a9912"
CORPORA = {"e16": (None, "e29"), "new": (NEW_DOMAINS, "e29n")}
COLUMNS = ["model", "design", "arm", "instance", "rotation", "slot", "constraint",
           "action", "status", "parsed", "included", "n_actions", "ready",
           "attempts", "prompt_tokens", "completion_tokens", "seconds"]


def slug(s):
    return s.replace(".", "").replace(":", "-")


def build_user(design, instance, dialogue):
    return (context_block(design, instance, dialogue) + "\n\n"
            + plan_instruction(tuple(instance.actions), "pin4"))


def run(model, offset, limit, designs, arms, dry_run, corpus="e16"):
    domains, stem_prefix = CORPORA[corpus]
    assert e16_hash() == E16_HASH, "E16 corpus disturbed"
    assert corpus_hash() == E29_HASH, "E29 corpus disturbed"
    if corpus == "new":
        assert corpus_hash(domains) == E29N_HASH, f"E29-N corpus disturbed: {corpus_hash(domains)}"
    ds = all_e29_dialogues(domains)[offset:None if limit is None else offset + limit]
    print(f"=== E29 memory semantics [{corpus}]: {model}, {len(ds)} dialogues x "
          f"{len(arms)} arms x {len(designs)} designs = {len(ds)*len(arms)*len(designs)} calls"
          f"{' (DRY RUN, no calls)' if dry_run else ''} ===\n")
    client = None if dry_run else RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst = d["instance"]
        system = SYSTEM.format(setting=inst.setting)
        for arm in arms:
            dia = d["arms"][arm]
            for design in designs:
                user = build_user(design, inst, dia)
                if dry_run:
                    text, attempts, ptok, ctok, secs = "", 0, None, None, None
                    plan = None
                else:
                    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
                    res = ask_structured(client=client, model=model, temperature=TEMPERATURE,
                                         messages=[{"role": "system", "content": system},
                                                   {"role": "user", "content": user}],
                                         validate=validate, budget=budget,
                                         speaker="Operator", expected=expected)
                    text = res.accepted_text or res.last_text or ""
                    plan, _err = parse_plan(text)
                    attempts = len(res.attempts)
                    ptok = res.attempts[0].prompt_tokens if res.attempts else None
                    ctok = sum(a.completion_tokens or 0 for a in res.attempts)
                    secs = round(sum(a.seconds or 0 for a in res.attempts), 3)
                actions = plan["actions"] if plan else []
                for u in d["units"]:
                    rows.append({
                        "model": model, "design": design, "arm": arm,
                        "instance": u["instance"], "rotation": u["rotation"],
                        "slot": u["slot"], "constraint": u["constraint"],
                        "action": u["action"], "status": u["status"],
                        "parsed": plan is not None,
                        "included": (u["action"] in actions) if plan else None,
                        "n_actions": len(actions) if plan else None,
                        "ready": plan["ready"] if plan else None,
                        "attempts": attempts, "prompt_tokens": ptok,
                        "completion_tokens": ctok, "seconds": secs,
                    })
                detail.append({"instance": inst.id, "rotation": d["rotation"],
                               "arm": arm, "design": design,
                               "prompt": user, "output": text})
                if not dry_run:
                    print(f"  [{i:2}/{len(ds)}] {inst.id:20} r{d['rotation']} {arm:8} {design:7} "
                          f"n={len(actions)}{'' if plan else '  PARSE-FAIL'}  {secs}s")
    if dry_run:
        d0 = detail[0]
        print(d0["prompt"]); print(f"\n... {len(detail)} prompts assembled, none sent.")
        return
    stem = f"results/{stem_prefix}_{slug(model)}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    print(f"\n  wrote {stem}.csv / .json")
    ok = [r for r in rows if r["parsed"]]
    summary = []
    for design in designs:
        for arm in arms:
            rs = [r for r in ok if r["design"] == design and r["arm"] == arm and r["status"] == "rejected"]
            summary.append({"design": design, "arm": arm, "n": len(rs),
                            "rejected_included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None})
    show(summary, ["design", "arm", "n", "rejected_included"])
    print(f"\n  parse {len(ok)/len(rows):.3f}   mean |plan| "
          f"{statistics.mean(r['n_actions'] for r in ok):.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--designs", default=",".join(DESIGNS))
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--corpus", default="e16", choices=sorted(CORPORA))
    a = ap.parse_args()
    designs = tuple(x for x in a.designs.split(",") if x)
    arms = tuple(x for x in a.arms.split(",") if x)
    assert set(designs) <= set(DESIGNS) and set(arms) <= set(ARMS)
    run(a.model, a.offset, a.limit, designs, arms, a.dry_run, a.corpus)
