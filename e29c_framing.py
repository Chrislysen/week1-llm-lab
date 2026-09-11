"""e29c_framing.py: E29-C runner -- four arms under the `full` design.

DECLARED in docs/protocols/E29C-framing.md before any decider call. Everything
else is E29's: E10 SYSTEM, E17 `pin4` plan instruction, temperature 0, the
RetryingOllamaClient, the same row format. Corpus: lineage_e29c.py.

    python e29c_framing.py --model llama3.2:3b --dry-run
    python e29c_framing.py --model llama3.2:3b --offset 0 --limit 48
    python e29c_framing.py --model llama3.2:3b --offset 48
"""
import argparse
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e29_memory_semantics import COLUMNS, E29_HASH, build_user, slug
from experiment import show, write_csv
from lineage_e16 import corpus_hash as e16_hash
from lineage_e29 import E16_HASH, corpus_hash as e29_hash
from lineage_e29c import ARMS_C, all_e29c_dialogues, corpus_hash
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

#: Pinned at declaration. The runner refuses to start if the corpus moved.
E29C_HASH = "979143b67049adf2"
DESIGN = "full"


def run(model, offset, limit, dry_run):
    assert e16_hash() == E16_HASH, "E16 corpus disturbed"
    assert e29_hash() == E29_HASH, "E29 corpus disturbed"
    assert corpus_hash() == E29C_HASH, f"E29-C corpus disturbed: {corpus_hash()}"
    ds = all_e29c_dialogues()[offset:None if limit is None else offset + limit]
    print(f"=== E29-C framing: {model}, {len(ds)} dialogues x {len(ARMS_C)} arms "
          f"under `{DESIGN}` = {len(ds) * len(ARMS_C)} calls"
          f"{' (DRY RUN, no calls)' if dry_run else ''} ===\n")
    client = None if dry_run else RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst = d["instance"]
        system = SYSTEM.format(setting=inst.setting)
        for arm in ARMS_C:
            dia = d["arms"][arm]
            user = build_user(DESIGN, inst, dia)
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
                    "model": model, "design": DESIGN, "arm": arm,
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
                           "arm": arm, "design": DESIGN, "prompt": user, "output": text})
            if not dry_run:
                print(f"  [{i:2}/{len(ds)}] {inst.id:20} r{d['rotation']} {arm:14} "
                      f"n={len(actions)}{'' if plan else '  PARSE-FAIL'}  {secs}s")
    if dry_run:
        for x in detail[:4]:
            line = [l for l in x["prompt"].splitlines() if "earlier in this discussion" in l]
            print(f"  {x['arm']:14} {line}")
        print(f"\n... {len(detail)} prompts assembled, none sent.")
        return
    stem = f"results/e29c_{slug(model)}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    print(f"\n  wrote {stem}.csv / .json")
    ok = [r for r in rows if r["parsed"]]
    summary = []
    for arm in ARMS_C:
        rs = [r for r in ok if r["arm"] == arm and r["status"] == "rejected"]
        summary.append({"arm": arm, "n": len(rs),
                        "rejected_included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None})
    show(summary, ["arm", "n", "rejected_included"])
    print(f"\n  parse {len(ok)/len(rows):.3f}   mean |plan| "
          f"{statistics.mean(r['n_actions'] for r in ok):.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(a.model, a.offset, a.limit, a.dry_run)
