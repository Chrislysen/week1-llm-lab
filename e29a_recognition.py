"""e29a_recognition.py: E29-A's recognition condition -- is the aside understood as a rejection?

DECLARED in docs/protocols/E29A-at-issue.md before any decider call. E29-K's question,
answer parsing and control target, unchanged, asked on E29-A's headline pair
(arc_medial, main_medial) in the neutral arm. An AT-ISSUE GATES read counts as
at-issue gating only if the aside is recognised as a rejection within 0.15 of its
main-clause twin; otherwise the aside may simply not have been understood.

    python e29a_recognition.py --hash
    python e29a_recognition.py --all            # all deciders, resumable
    python e29a_recognition.py --analyse
"""
import argparse
import csv
import hashlib
import json
import os
import statistics
from collections import defaultdict

from e10_independence import SYSTEM
from e29_memory_semantics import slug
from e29a_at_issue import DECIDERS, runtime
from e29k_recognition import FIELDS, QUESTION, TARGETS, parse_answer, phrase_of
from lineage_e29 import all_e29_dialogues
from lineage_e29a import context_block_a
from robust_client import RetryingOllamaClient

PAIR = ("arc_medial", "main_medial")
E29AR_HASH = "20cdf27899b304d1"
WITHIN = 0.15


def build_user(cell, d, target):
    return context_block_a(cell, d["instance"], d["arms"]["neutral"]) + "\n\n" + QUESTION.format(phrase=phrase_of(d, target))


def blocks_hash():
    h = hashlib.sha256()
    for d in all_e29_dialogues():
        for c in PAIR:
            for t in TARGETS:
                h.update(f"{d['instance'].id}|{d['rotation']}|{c}|{t}|".encode())
                h.update(build_user(c, d, t).encode())
    return h.hexdigest()[:16]


def run(model):
    assert blocks_hash() == E29AR_HASH, f"E29-A recognition prompts disturbed: {blocks_hash()}"
    dig, ver = runtime(model)
    print(f"=== E29-A recognition: {model} (digest {dig}, Ollama {ver}) ===", flush=True)
    path = f"results/e29a_recognition_{slug(model)}.csv"
    done = set()
    if os.path.exists(path):
        done = {(r["instance"], r["rotation"], r["design"], r["target"]) for r in csv.DictReader(open(path, encoding="utf-8"))}
    client = RetryingOllamaClient()
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for n, d in enumerate(all_e29_dialogues(), 1):
            system = SYSTEM.format(setting=d["instance"].setting)
            for c in PAIR:
                for t in TARGETS:
                    if (d["instance"].id, str(d["rotation"]), c, t) in done:
                        continue
                    reply = client.chat(model, [{"role": "system", "content": system},
                                                {"role": "user", "content": build_user(c, d, t)}],
                                        temperature=0, num_predict=8)
                    ans = parse_answer(reply.text)
                    w.writerow({"model": model, "design": c, "target": t, "instance": d["instance"].id,
                                "rotation": d["rotation"], "phrase": phrase_of(d, t), "answer": (reply.text or "")[:40],
                                "parsed": ans is not None, "yes": ans == "yes", "seconds": round(reply.seconds or 0, 3)})
            fh.flush()
            if n % 24 == 0:
                print(f"  [{n}/96]", flush=True)
    print(f"  wrote {path}", flush=True)


def analyse(model):
    path = f"results/e29a_recognition_{slug(model)}.csv"
    if not os.path.exists(path):
        print("no E29-A recognition rows for", model)
        return None
    cell = defaultdict(dict)
    for r in csv.DictReader(open(path, encoding="utf-8")):
        cell[(r["instance"], r["rotation"])][(r["design"], r["target"])] = (r["parsed"] == "True", r["yes"] == "True")
    keys = [k for k, v in cell.items() if len(v) == len(PAIR) * len(TARGETS)]
    R = {c: statistics.mean(cell[k][(c, "rejected")][1] for k in keys) for c in PAIR}
    C = {c: statistics.mean(cell[k][(c, "control")][1] for k in keys) for c in PAIR}
    parse = min(statistics.mean(cell[k][(c, t)][0] for k in keys) for c in PAIR for t in TARGETS)
    void = parse < 0.95 or max(C.values()) > 0.20
    met = (not void) and abs(R["arc_medial"] - R["main_medial"]) <= WITHIN
    verdict = "VOID" if void else ("CONDITION MET" if met else "CONDITION NOT MET")
    print(f"=== E29-A recognition read: {model} (n = {len(keys)}) ===")
    for c in PAIR:
        print(f"  {c:12} says 'rejected' {R[c]:.3f}   control 'yes' {C[c]:.3f}")
    print(f"  |difference| {abs(R['arc_medial'] - R['main_medial']):.3f} (condition: <= {WITHIN})   min parse {parse:.3f}")
    print(f"  VERDICT ({model}): {verdict}")
    out = {"model": model, "n": len(keys), "recognised": R, "yes_to_control": C, "min_parse": parse, "verdict": verdict}
    with open(f"results/e29a_recognition_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return out


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
        print("E29-A RECOGNITION ALL DONE", flush=True)
