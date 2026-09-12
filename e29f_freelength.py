"""e29f_freelength.py: E29-F runner -- the E29 designs with the plan length
UNPINNED, the one adversarial objection the record could not answer.

DECLARED in docs/protocols/E29F-free-length.md before any decider call.
Everything is E29's except the plan instruction, which is E17's `free` mode
instead of `pin4`: the decider chooses how many steps the plan has.

    python e29f_freelength.py --hash
    python e29f_freelength.py --model llama3.2:3b --dry-run
    python e29f_freelength.py --model llama3.2:3b --offset 0 --limit 24
"""
import argparse
import hashlib
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e17_menu_law import plan_instruction
from e29_memory_semantics import COLUMNS, E29_HASH, slug
from experiment import show, write_csv
from lineage_e16 import corpus_hash as e16_hash
from lineage_e29 import ARMS, E16_HASH, all_e29_dialogues, context_block, corpus_hash
from lineage_e29e import context_block_e
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

#: full and delete carry the main E29 contrast; addonly and addonly_flag carry
#: the E29-E own-record contrast. Four designs, the argument's load-bearing set.
DESIGNS_F = ("full", "delete", "addonly", "addonly_flag")
LENGTH = "free"
E29F_HASH = "42de19f5bb6fd6df"


def block(design, instance, dialogue):
    if design in ("full", "delete", "addonly", "wiki"):
        return context_block(design, instance, dialogue)
    return context_block_e(design, instance, dialogue)


def blocks_hash():
    h = hashlib.sha256()
    for d in all_e29_dialogues():
        for arm in ARMS:
            for X in DESIGNS_F:
                h.update(f"{d['instance'].id}|{d['rotation']}|{arm}|{X}|{LENGTH}|".encode())
                h.update(build_user(X, d["instance"], d["arms"][arm]).encode())
    return h.hexdigest()[:16]


def build_user(design, instance, dialogue):
    return (block(design, instance, dialogue) + "\n\n"
            + plan_instruction(tuple(instance.actions), LENGTH))


def run(model, offset, limit, dry_run):
    assert e16_hash() == E16_HASH and corpus_hash() == E29_HASH, "E29 corpus disturbed"
    assert blocks_hash() == E29F_HASH, f"E29-F blocks disturbed: {blocks_hash()}"
    ds = all_e29_dialogues()[offset:None if limit is None else offset + limit]
    print(f"=== E29-F free-length: {model}, {len(ds)} dialogues x {len(ARMS)} arms x "
          f"{len(DESIGNS_F)} designs = {len(ds) * len(ARMS) * len(DESIGNS_F)} calls"
          f"{' (DRY RUN, no calls)' if dry_run else ''} ===\n")
    client = None if dry_run else RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst = d["instance"]
        system = SYSTEM.format(setting=inst.setting)
        for arm in ARMS:
            dia = d["arms"][arm]
            for design in DESIGNS_F:
                user = build_user(design, inst, dia)
                if dry_run:
                    text, attempts, ptok, ctok, secs, plan = "", 0, None, None, None, None
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
                detail.append({"instance": inst.id, "rotation": d["rotation"], "arm": arm,
                               "design": design, "prompt": user, "output": text})
                if not dry_run:
                    print(f"  [{i:2}/{len(ds)}] {inst.id:20} r{d['rotation']} {arm:8} {design:13} "
                          f"n={len(actions)}{'' if plan else '  PARSE-FAIL'}  {secs}s")
    if dry_run:
        d0 = detail[0]
        print(d0["prompt"].rsplit("\n\n", 2)[-2] + "\n\n" + d0["prompt"].rsplit("\n\n", 1)[-1])
        print(f"\n... {len(detail)} prompts assembled, none sent.")
        return
    stem = f"results/e29f_{slug(model)}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    print(f"\n  wrote {stem}.csv / .json")
    ok = [r for r in rows if r["parsed"]]
    summary = []
    for design in DESIGNS_F:
        for arm in ARMS:
            rs = [r for r in ok if r["design"] == design and r["arm"] == arm and r["status"] == "rejected"]
            nev = [r["included"] for r in ok if r["design"] == design and r["arm"] == arm and r["status"] == "never"]
            summary.append({"design": design, "arm": arm, "n": len(rs),
                            "rejected_included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None,
                            "never_included": round(statistics.mean(nev), 3) if nev else None,
                            "mean_plan": round(statistics.mean(
                                r["n_actions"] for r in ok
                                if r["design"] == design and r["arm"] == arm), 2)})
    show(summary, ["design", "arm", "n", "rejected_included", "never_included", "mean_plan"])
    print(f"\n  parse {len(ok)/len(rows):.3f}   mean |plan| {statistics.mean(r['n_actions'] for r in ok):.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hash", action="store_true")
    a = ap.parse_args()
    if a.hash:
        print(blocks_hash())
    else:
        assert a.model, "--model is required"
        run(a.model, a.offset, a.limit, a.dry_run)
