"""e29o_order.py: E29-O runner -- which way does a revocation marker attach?

DECLARED in docs/protocols/E29O-order.md before any decider call. Everything is
E29-A's (system prompt, plan instruction, pinned plan, temperature, validator,
512-token runaway guard, markdown list, neutral arm, deciders, digests, Ollama
version); only the rendering and list position of the rejected proposal vary
(lineage_e29o.CELLS).

    python e29o_order.py --hash
    python e29o_order.py --model llama3.2:3b
    python e29o_order.py --all                 # all deciders, resumable
"""
import argparse
import csv as _csv
import glob as _glob
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e17_menu_law import plan_instruction
from e29_memory_semantics import COLUMNS, E29_HASH, slug
from e29s_structure import NUM_PREDICT_CAP, CappedClient
from experiment import write_csv
from lineage_e16 import corpus_hash as e16_hash
from lineage_e29 import E16_HASH, corpus_hash
from lineage_e29o import CELLS as IDIOMS, context_block_o, corpora_ok, dialogues
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

LENGTH = "pin4"
ARMS_T = ("neutral",)
DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct", "aya-expanse:8b")
E29O_HASH = "cebbddd2378f205f"
LOG = "results/e29o_run.log"
DIGESTS = {"llama3.2:3b": "a80c4f17acd5", "qwen2.5:14b-instruct": "7cdf5a0187d5", "aya-expanse:8b": "65f986688a01"}
OLLAMA_VERSION = "0.34.4"
# 127.0.0.1, not localhost: on this machine "localhost" tries IPv6 first and adds 2.04 s to
# every request. Same server, same payload; transport only.
HOST = "http://127.0.0.1:11434"


def runtime(model):
    """Refuse to run on a model digest or Ollama version other than the declared ones."""
    tags = json.load(urllib.request.urlopen(HOST + "/api/tags", timeout=5))
    dig = next(m["digest"] for m in tags["models"] if m["name"] in (model, model + ":latest"))
    ver = json.load(urllib.request.urlopen(HOST + "/api/version", timeout=5))["version"]
    assert dig.startswith(DIGESTS[model]) and ver == OLLAMA_VERSION, (model, dig[:12], ver)
    return dig[:12], ver


def build_user(idiom, instance, dialogue):
    return context_block_o(idiom, instance, dialogue) + "\n\n" + plan_instruction(tuple(instance.actions), LENGTH)


def blocks_hash():
    """Every system and user message the runner will send."""
    h = hashlib.sha256()
    for d in dialogues():
        h.update(SYSTEM.format(setting=d["instance"].setting).encode())
        for arm in ARMS_T:
            for i in IDIOMS:
                h.update(f"{d['instance'].id}|{d['rotation']}|{arm}|{i}|{LENGTH}|".encode())
                h.update(build_user(i, d["instance"], d["arms"][arm]).encode())
    return h.hexdigest()[:16]


def run_files(model):
    """This decider's run files in run order (r2 before r10)."""
    fs = _glob.glob(f"results/e29o_{slug(model)}_r*.csv")
    return sorted(fs, key=lambda f: int(f.rsplit("_r", 1)[1].split(".")[0]))


def done_pairs(model):
    have = {}
    for fn in run_files(model):
        for r in _csv.DictReader(open(fn, encoding="utf-8")):
            if r["parsed"] == "True":
                have.setdefault((r["instance"], r["rotation"]), set()).add((r["design"], r["arm"]))
    need = {(i, a) for i in IDIOMS for a in ARMS_T}
    return {k for k, v in have.items() if need <= v}


def next_stem(model):
    i = 0
    while os.path.exists(f"results/e29o_{slug(model)}_r{i}.csv"):
        i += 1
    return f"results/e29o_{slug(model)}_r{i}"


def run(model, resume=True, limit=None):
    assert e16_hash() == E16_HASH and corpus_hash() == E29_HASH and corpora_ok(), "E29 corpora disturbed"
    assert blocks_hash() == E29O_HASH, f"E29-O blocks disturbed: {blocks_hash()}"
    ds = dialogues()
    if resume:
        done = done_pairs(model)
        ds = [d for d in ds if (d["instance"].id, str(d["rotation"])) not in done]
    ds = ds[:limit] if limit else ds
    per = len(ARMS_T) * len(IDIOMS)
    print(f"=== E29-O order: {model}, {len(ds)} dialogues x {per} prompts = {len(ds) * per} calls ===", flush=True)
    if not ds:
        print("  nothing to do", flush=True)
        return
    dig, ver = runtime(model)
    print(f"  runtime: {model} digest {dig}, Ollama {ver}", flush=True)
    client = CappedClient(RetryingOllamaClient(host=HOST), NUM_PREDICT_CAP)
    validate, expected = make_validator("default"), schema_hint("default")
    rows, detail, stem = [], [], next_stem(model)
    for n, d in enumerate(ds, 1):
        inst = d["instance"]
        system = SYSTEM.format(setting=inst.setting)
        for arm in ARMS_T:
            for idiom in IDIOMS:
                user = build_user(idiom, inst, d["arms"][arm])
                budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
                res = ask_structured(client=client, model=model, temperature=TEMPERATURE,
                                     messages=[{"role": "system", "content": system},
                                               {"role": "user", "content": user}],
                                     validate=validate, budget=budget, speaker="Operator", expected=expected)
                text = res.accepted_text or res.last_text or ""
                plan, _err = parse_plan(text)
                actions = plan["actions"] if plan else []
                secs = round(sum(a.seconds or 0 for a in res.attempts), 3)
                for u in d["units"]:
                    rows.append({"model": model, "design": idiom, "arm": arm,
                                 "instance": u["instance"], "rotation": u["rotation"], "slot": u["slot"],
                                 "constraint": u["constraint"], "action": u["action"], "status": u["status"],
                                 "parsed": plan is not None,
                                 "included": (u["action"] in actions) if plan else None,
                                 "n_actions": len(actions) if plan else None,
                                 "ready": plan["ready"] if plan else None,
                                 "attempts": len(res.attempts),
                                 "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None,
                                 "completion_tokens": sum(a.completion_tokens or 0 for a in res.attempts),
                                 "seconds": secs})
                detail.append({"instance": inst.id, "rotation": d["rotation"], "arm": arm,
                               "design": idiom, "prompt": user, "output": text, "digest": dig, "ollama": ver})
        write_csv(stem + ".csv", rows, COLUMNS)
        with open(stem + ".json", "w", encoding="utf-8") as f:
            json.dump(detail, f, indent=1)
        print(f"  [{n:2}/{len(ds)}] {inst.id:22} r{d['rotation']}  {per} calls", flush=True)
    print(f"  wrote {stem}.csv / .json", flush=True)


def pid_alive(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
    return str(pid) in out


def run_all(after=None):
    if after:
        print(f"waiting for process {after} to exit ...", flush=True)
        while pid_alive(after):
            time.sleep(30)
    for m in DECIDERS:
        run(m)
    print("E29-O ALL DONE", flush=True)


def detach(after=None):
    flags = 0x00000008 | 0x00000200 | 0x01000000
    log = open(LOG, "a", encoding="utf-8")
    cmd = [sys.executable, "-u", os.path.abspath(__file__), "--all"] + (["--after", str(after)] if after else [])
    p = subprocess.Popen(cmd, cwd=os.getcwd(), stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
    print(f"E29-O detached: pid {p.pid}, log {LOG}" + (f", starts after pid {after} exits" if after else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--detach", action="store_true")
    ap.add_argument("--after", type=int)
    a = ap.parse_args()
    if a.hash:
        print(blocks_hash())
    elif a.detach:
        detach(a.after)
    elif a.all:
        run_all(a.after)
    else:
        run(a.model, limit=a.limit)
