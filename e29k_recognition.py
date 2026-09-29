"""e29k_recognition.py: E29-K -- does the decider KNOW the tagged step was rejected?

DECLARED in docs/protocols/E29K-recognition.md before any decider call.

E29-S showed a rejection written as a verb-less tag on the proposal is enacted
far more than the same rejection as a sentence. That leaves two explanations:
the model does not read the tag as a rejection at all, or it reads it and the
planner ignores it anyway. E29-K asks the same decider, with the same system
prompt and the same four E29-S stores (neutral arm), one direct question
instead of the plan instruction:

    Question: has the step "{phrase}" been rejected or withdrawn in this discussion?
    Answer with exactly one word: yes or no.

once about the rejected step, and once about a step that was NOT rejected (a
yes-bias control, which should draw "no"): the accepted step if the dialogue
has one, else the proposed-only step, else the never-mentioned one.

    python e29k_recognition.py --hash
    python e29k_recognition.py --all            # both deciders, resumable
    python e29k_recognition.py --analyse
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import random
import re
import statistics
from collections import defaultdict

from e10_independence import SYSTEM
from e29_memory_semantics import slug
from lineage_bench import DOMAINS
from lineage_e29 import all_e29_dialogues
from lineage_e29s import DESIGNS_S, context_block_s
from robust_client import RetryingOllamaClient

DECIDERS = ("llama3.2:3b", "qwen2.5:14b-instruct")
QUESTION = ('Question: has the step "{phrase}" been rejected or withdrawn in this discussion?\n'
            'Answer with exactly one word: yes or no.')
TARGETS = ("rejected", "control")
E29K_HASH = "e9ef529280d358bb"
B, SESOI = 2000, 0.15
FIELDS = ["model", "design", "target", "instance", "rotation", "phrase", "answer", "parsed", "yes", "seconds"]


def phrase_of(d, target):
    order = ("rejected",) if target == "rejected" else ("accepted", "proposed", "never")
    u = next(u for st in order for u in d["units"] if u["status"] == st)
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def build_user(design, d, target):
    return (context_block_s(design, d["instance"], d["arms"]["neutral"]) + "\n\n"
            + QUESTION.format(phrase=phrase_of(d, target)))


def blocks_hash():
    h = hashlib.sha256()
    for d in all_e29_dialogues():
        for X in DESIGNS_S:
            for t in TARGETS:
                h.update(f"{d['instance'].id}|{d['rotation']}|{X}|{t}|".encode())
                h.update(build_user(X, d, t).encode())
    return h.hexdigest()[:16]


def parse_answer(text):
    m = re.match(r"\W*(yes|no)\b", (text or "").strip().lower())
    return m.group(1) if m else None


def run(model):
    assert blocks_hash() == E29K_HASH, f"E29-K prompts disturbed: {blocks_hash()}"
    path = f"results/e29k_{slug(model)}.csv"
    done = set()
    if os.path.exists(path):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            done.add((r["instance"], r["rotation"], r["design"], r["target"]))
    client = RetryingOllamaClient()
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        ds = all_e29_dialogues()
        print(f"=== E29-K recognition: {model}, {len(ds)} dialogues x {len(DESIGNS_S) * len(TARGETS)} questions ===", flush=True)
        for n, d in enumerate(ds, 1):
            system = SYSTEM.format(setting=d["instance"].setting)
            for X in DESIGNS_S:
                for t in TARGETS:
                    key = (d["instance"].id, str(d["rotation"]), X, t)
                    if key in done:
                        continue
                    reply = client.chat(model, [{"role": "system", "content": system},
                                                {"role": "user", "content": build_user(X, d, t)}],
                                        temperature=0, num_predict=8)
                    ans = parse_answer(reply.text)
                    w.writerow({"model": model, "design": X, "target": t, "instance": d["instance"].id,
                                "rotation": d["rotation"], "phrase": phrase_of(d, t), "answer": (reply.text or "")[:40],
                                "parsed": ans is not None, "yes": ans == "yes", "seconds": round(reply.seconds or 0, 3)})
            fh.flush()
            if n % 12 == 0:
                print(f"  [{n}/{len(ds)}]", flush=True)
    print(f"  wrote {path}", flush=True)


def analyse(model):
    rows = list(csv.DictReader(open(f"results/e29k_{slug(model)}.csv", encoding="utf-8")))
    cell = defaultdict(dict)
    for r in rows:
        cell[(r["instance"], r["rotation"])][(r["design"], r["target"])] = (r["parsed"] == "True", r["yes"] == "True")
    keys = [k for k, v in cell.items() if len(v) == len(DESIGNS_S) * len(TARGETS)]

    def rate(ks, X, t):
        v = [cell[k][(X, t)][1] for k in ks]
        return statistics.mean(v)

    parse = {(X, t): statistics.mean(cell[k][(X, t)][0] for k in keys) for X in DESIGNS_S for t in TARGETS}
    R = {X: rate(keys, X, "rejected") for X in DESIGNS_S}
    C = {X: rate(keys, X, "control") for X in DESIGNS_S}
    g = R["addonly"] - R["addonly_flag"]
    rng = random.Random(0)
    boot = []
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        boot.append(rate(s, "addonly", "rejected") - rate(s, "addonly_flag", "rejected"))
    boot.sort()
    lo, hi = boot[int(0.025 * B)], boot[int(0.975 * B) - 1]
    void = [f"{X}/{t} parse {v:.2f}" for (X, t), v in parse.items() if v < 0.95] + \
           [f"{X} yes-to-control {v:.2f}" for X, v in C.items() if v > 0.2]
    if void:
        verdict = "VOID (" + "; ".join(void) + ")"
    elif g >= SESOI and lo > 0:
        verdict = "NOT-READ (the tag is not recognised as a rejection)"
    elif hi < SESOI and R["addonly_flag"] >= 0.8:
        verdict = "READ-NOT-USED (recognised like the sentence, yet enacted in plans)"
    else:
        verdict = "UNCLEAR"
    print(f"=== E29-K read: {model} (n = {len(keys)}) ===")
    for X in DESIGNS_S:
        print(f"  {X:16} says 'rejected' for the rejected step {R[X]:.3f}   for a non-rejected step {C[X]:.3f}")
    print(f"  recognition gap sentence - tag: {g:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    print(f"  VERDICT ({model}): {verdict}")
    out = {"model": model, "n": len(keys), "recognised": R, "yes_to_control": C, "gap": g, "ci": [lo, hi],
           "parse": {f"{X}|{t}": v for (X, t), v in parse.items()}, "verdict": verdict}
    with open(f"results/e29k_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args()
    if a.hash:
        print(blocks_hash())
    elif a.analyse:
        for m in (DECIDERS if not a.model else (a.model,)):
            analyse(m)
    else:
        for m in (DECIDERS if a.all or not a.model else (a.model,)):
            run(m)
        print("E29-K ALL DONE", flush=True)
