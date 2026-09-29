"""e29r_formats.py: E29-R runner -- the E29-S 2x2 in JSON, XML and numbered lists.

DECLARED in docs/protocols/E29R-formats.md before any decider call. Everything
is E29-S's (system prompt, plan instruction, pinned plan, temperature,
validator, the 512-token runaway guard); only the list container varies.

    python e29r_formats.py --hash
    python e29r_formats.py --model llama3.2:3b --resume [--limit N]
    python e29r_formats.py --all            # both deciders, resumable, in order
    python e29r_formats.py --detach         # --all in a detached process, log in results/

Results are checkpointed after EVERY dialogue into results/e29r_<model>_r*.csv
and `--resume` skips dialogues already complete in any result file.
"""
import argparse
import csv as _csv
import glob as _glob
import hashlib
import json
import os
import statistics
import subprocess
import sys

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e17_menu_law import plan_instruction
from e29_memory_semantics import COLUMNS, E29_HASH, slug
from e29s_structure import NUM_PREDICT_CAP, CappedClient
from experiment import show, write_csv
from lineage_e16 import corpus_hash as e16_hash
from lineage_e29 import ARMS, E16_HASH, all_e29_dialogues, corpus_hash
from lineage_e29r import DESIGNS_S, RUN_FORMATS, context_block_r
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

LENGTH = "pin4"
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct")       # E29-S's two, the extremes of its range
COLUMNS_R = COLUMNS + ["format"]
E29R_HASH = "8a9412801fc2bae1"
LOG = "results/e29r_run.log"


def build_user(fmt, design, instance, dialogue):
    return (context_block_r(fmt, design, instance, dialogue) + "\n\n"
            + plan_instruction(tuple(instance.actions), LENGTH))


def blocks_hash():
    h = hashlib.sha256()
    for d in all_e29_dialogues():
        for arm in ARMS:
            for fmt in RUN_FORMATS:
                for X in DESIGNS_S:
                    h.update(f"{d['instance'].id}|{d['rotation']}|{arm}|{fmt}|{X}|{LENGTH}|".encode())
                    h.update(build_user(fmt, X, d["instance"], d["arms"][arm]).encode())
    return h.hexdigest()[:16]


def done_pairs(model):
    """(instance, rotation) already complete on every format, design and arm."""
    have = {}
    for fn in sorted(_glob.glob(f"results/e29r_{slug(model)}_*.csv")):
        for r in _csv.DictReader(open(fn, encoding="utf-8")):
            if r["parsed"] == "True":
                have.setdefault((r["instance"], r["rotation"]), set()).add((r["format"], r["design"], r["arm"]))
    need = {(f, X, a) for f in RUN_FORMATS for X in DESIGNS_S for a in ARMS}
    return {k for k, v in have.items() if need <= v}


def next_stem(model):
    i = 0
    while os.path.exists(f"results/e29r_{slug(model)}_r{i}.csv"):
        i += 1
    return f"results/e29r_{slug(model)}_r{i}"


def run(model, offset=0, limit=None, dry_run=False, resume=False):
    assert e16_hash() == E16_HASH and corpus_hash() == E29_HASH, "E29 corpus disturbed"
    assert blocks_hash() == E29R_HASH, f"E29-R blocks disturbed: {blocks_hash()}"
    ds = all_e29_dialogues()
    if resume:                     # drop finished dialogues BEFORE slicing
        done = done_pairs(model)
        before = len(ds)
        ds = [d for d in ds if (d["instance"].id, str(d["rotation"])) not in done]
        print(f"  resume: {before - len(ds)} of {before} already complete, {len(ds)} left", flush=True)
    ds = ds[offset:None if limit is None else offset + limit]
    per = len(ARMS) * len(RUN_FORMATS) * len(DESIGNS_S)
    print(f"=== E29-R formats: {model}, {len(ds)} dialogues x {per} prompts = {len(ds) * per} calls"
          f"{' (DRY RUN, no calls)' if dry_run else ''} ===\n", flush=True)
    if not ds:
        print("  nothing to do", flush=True)
        return
    client = None if dry_run else CappedClient(RetryingOllamaClient(), NUM_PREDICT_CAP)
    validate, expected = make_validator("default"), schema_hint("default")
    rows, detail = [], []
    stem = None if dry_run else next_stem(model)
    for i, d in enumerate(ds, 1):
        inst = d["instance"]
        system = SYSTEM.format(setting=inst.setting)
        for arm in ARMS:
            dia = d["arms"][arm]
            for fmt in RUN_FORMATS:
                for design in DESIGNS_S:
                    user = build_user(fmt, design, inst, dia)
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
                            "model": model, "design": design, "arm": arm, "format": fmt,
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
                                   "format": fmt, "design": design, "prompt": user, "output": text})
        if not dry_run:                       # checkpoint after every dialogue
            write_csv(stem + ".csv", rows, COLUMNS_R)
            with open(stem + ".json", "w", encoding="utf-8") as f:
                json.dump(detail, f, indent=1)
            ok_d = [r for r in rows if r["instance"] == inst.id and str(r["rotation"]) == str(d["rotation"])]
            fails = sum(1 for r in ok_d if not r["parsed"]) // max(1, len(d["units"]))
            print(f"  [{i:2}/{len(ds)}] {inst.id:22} r{d['rotation']}  {per} calls"
                  f"{'' if not fails else f'  {fails} PARSE-FAIL'}", flush=True)
    if dry_run:
        print(detail[0]["prompt"])
        print(f"\n... {len(detail)} prompts assembled, none sent.")
        return
    print(f"\n  wrote {stem}.csv / .json", flush=True)
    ok = [r for r in rows if r["parsed"]]
    summary = []
    for fmt in RUN_FORMATS:
        for design in DESIGNS_S:
            rs = [r for r in ok if r["format"] == fmt and r["design"] == design and r["arm"] == "neutral" and r["status"] == "rejected"]
            summary.append({"format": fmt, "design": design, "n": len(rs),
                            "rejected_incl_neutral": round(statistics.mean(r["included"] for r in rs), 3) if rs else None})
    show(summary, ["format", "design", "n", "rejected_incl_neutral"])
    print(f"\n  parse {len(ok)/len(rows):.3f}", flush=True)


def run_all():
    for m in DECIDERS:
        run(m, resume=True)
    print("E29-R ALL DONE", flush=True)


def detach():
    flags = 0x00000008 | 0x00000200 | 0x01000000        # DETACHED | NEW_GROUP | BREAKAWAY
    os.makedirs("results", exist_ok=True)
    log = open(LOG, "a", encoding="utf-8")
    p = subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--all"], cwd=os.getcwd(),
                         stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
    print(f"E29-R detached: pid {p.pid}, log {LOG}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--detach", action="store_true")
    a = ap.parse_args()
    if a.hash:
        print(blocks_hash())
    elif a.detach:
        detach()
    elif a.all:
        run_all()
    else:
        assert a.model, "--model is required"
        run(a.model, a.offset, a.limit, a.dry_run, a.resume)
