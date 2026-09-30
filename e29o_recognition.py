"""e29o_recognition.py: E29-O's two probes -- what does the decider say about the marked step?

DECLARED in docs/protocols/E29O-order.md before any decider call. Same system prompt and
E29-O context blocks (neutral arm, both corpora), one direct question instead of the plan
instruction, temperature 0, 8 tokens.

Probe K (E29-K's question, parsing and control target, unchanged):
    Question: has the step "{phrase}" been rejected or withdrawn in this discussion?
    Answer with exactly one word: yes or no.
    on withdrawn_pre, withdrawn_post, later_pre, named_pre, label_pre, clause_pre, field_post.
    Descriptive: is each marker understood as a rejection?

Probe E (end state), option order alternating by dialogue:
    Question: at the end of this discussion, was the step "{phrase}" still proposed, or had it
    been withdrawn?  Answer with exactly one word: proposed or withdrawn.
    on withdrawn_pre, withdrawn_post, later_pre, later_post. The control is a step that was not
    withdrawn: the undecided proposal if the dialogue has one, else the accepted one.
    It carries T1's condition, and tests NARR's premise that a leading marker leaves the step
    "still proposed" at the end.

    python e29o_recognition.py --hash
    python e29o_recognition.py --all            # all deciders, resumable
    python e29o_recognition.py --analyse
"""
import argparse
import csv
import hashlib
import json
import os
import re
import statistics
from collections import defaultdict

from e10_independence import SYSTEM
from e29_memory_semantics import slug
from e29k_recognition import QUESTION, parse_answer, phrase_of
from e29o_order import DECIDERS, HOST, runtime
from lineage_bench import DOMAINS
from lineage_e29o import context_block_o, dialogues
from robust_client import RetryingOllamaClient

PROBE_K = ("withdrawn_pre", "withdrawn_post", "later_pre", "named_pre", "label_pre", "clause_pre", "field_post")
PROBE_E = ("withdrawn_pre", "withdrawn_post", "later_pre", "later_post")
TARGETS = ("rejected", "control")
QE = ('Question: at the end of this discussion, was the step "{phrase}" still proposed, or had it been withdrawn?\n'
      'Answer with exactly one word: proposed or withdrawn.',
      'Question: at the end of this discussion, had the step "{phrase}" been withdrawn, or was it still proposed?\n'
      'Answer with exactly one word: withdrawn or proposed.')
E29OR_HASH = "1ab20d15e0e747be"
N_DIALOGUES = 192
FIELDS = ["model", "probe", "design", "target", "instance", "rotation", "phrase", "answer", "parsed", "hit",
          "seconds", "digest", "ollama"]


def phrase_e(d, target):
    """Probe E's step: the rejected one, or one that was not withdrawn (undecided, else accepted)."""
    order = ("rejected",) if target == "rejected" else ("proposed", "accepted")
    u = next(u for st in order for u in d["units"] if u["status"] == st)
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def parse_e(text):
    m = re.match(r"\W*(proposed|withdrawn)\b", (text or "").strip().lower())
    return m.group(1) if m else None


def jobs():
    """(probe, dialogue index, dialogue, cell, target, user message), in run order."""
    for n, d in enumerate(dialogues()):
        block = {c: context_block_o(c, d["instance"], d["arms"]["neutral"]) for c in set(PROBE_K) | set(PROBE_E)}
        for c in PROBE_K:
            for t in TARGETS:
                yield "K", n, d, c, t, block[c] + "\n\n" + QUESTION.format(phrase=phrase_of(d, t))
        for c in PROBE_E:
            for t in TARGETS:
                yield "E", n, d, c, t, block[c] + "\n\n" + QE[n % 2].format(phrase=phrase_e(d, t))


def blocks_hash():
    h = hashlib.sha256()
    for probe, n, d, c, t, user in jobs():
        h.update(f"{probe}|{d['instance'].id}|{d['rotation']}|{c}|{t}|".encode())
        h.update(SYSTEM.format(setting=d["instance"].setting).encode())
        h.update(user.encode())
    return h.hexdigest()[:16]


def run(model):
    assert blocks_hash() == E29OR_HASH, f"E29-O recognition prompts disturbed: {blocks_hash()}"
    dig, ver = runtime(model)
    print(f"=== E29-O recognition: {model} (digest {dig}, Ollama {ver}) ===", flush=True)
    path = f"results/e29o_recognition_{slug(model)}.csv"
    done = set()
    if os.path.exists(path):
        done = {(r["probe"], r["instance"], r["rotation"], r["design"], r["target"])
                for r in csv.DictReader(open(path, encoding="utf-8"))}
    client = RetryingOllamaClient(host=HOST)
    new = not os.path.exists(path)
    last = None
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for probe, n, d, c, t, user in jobs():
            if (probe, d["instance"].id, str(d["rotation"]), c, t) in done:
                continue
            reply = client.chat(model, [{"role": "system", "content": SYSTEM.format(setting=d["instance"].setting)},
                                        {"role": "user", "content": user}], temperature=0, num_predict=8)
            ans = parse_answer(reply.text) if probe == "K" else parse_e(reply.text)
            w.writerow({"model": model, "probe": probe, "design": c, "target": t, "instance": d["instance"].id,
                        "rotation": d["rotation"], "phrase": phrase_of(d, t) if probe == "K" else phrase_e(d, t),
                        "answer": (reply.text or "")[:40], "parsed": ans is not None,
                        "hit": ans == ("yes" if probe == "K" else "withdrawn"),
                        "seconds": round(reply.seconds or 0, 3), "digest": dig, "ollama": ver})
            if n != last:
                fh.flush()
                if n % 48 == 0:
                    print(f"  [{n}/{N_DIALOGUES}]", flush=True)
                last = n
    print(f"  wrote {path}", flush=True)


def _rates(rows, probe, cells):
    cell = defaultdict(dict)
    for r in rows:
        if r["probe"] == probe:
            cell[(r["instance"], r["rotation"])][(r["design"], r["target"])] = (r["parsed"] == "True", r["hit"] == "True")
    keys = [k for k, v in cell.items() if len(v) == len(cells) * len(TARGETS)]
    hit = {(c, t): statistics.mean(cell[k][(c, t)][1] for k in keys) for c in cells for t in TARGETS} if keys else {}
    parse = min(statistics.mean(cell[k][(c, t)][0] for k in keys) for c in cells for t in TARGETS) if keys else 0.0
    return keys, hit, parse


def analyse(model):
    """Probe validity and T1's end-state condition, by the declared rule."""
    path = f"results/e29o_recognition_{slug(model)}.csv"
    if not os.path.exists(path):
        print("no E29-O recognition rows for", model)
        return None
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    out = {"model": model}
    for probe, cells in (("K", PROBE_K), ("E", PROBE_E)):
        keys, hit, parse = _rates(rows, probe, cells)
        if len(keys) < N_DIALOGUES:
            out[probe] = {"n": len(keys), "status": "INCOMPLETE"}
            continue
        ctrl = max(hit[(c, "control")] for c in cells)
        j = {c: hit[(c, "rejected")] - hit[(c, "control")] for c in cells}
        valid = parse >= 0.95 and ctrl <= 0.35 and j["withdrawn_post"] >= 0.40
        out[probe] = {"n": len(keys), "status": "VALID" if valid else "VOID", "min_parse": parse,
                      "max_control": ctrl, "hit": {f"{c}|{t}": v for (c, t), v in hit.items()}, "J": j}
    e = out["E"]
    if e["status"] == "VALID":
        w = {c: e["hit"][f"{c}|rejected"] for c in PROBE_E}
        e["condition"] = ("MET" if (w["later_pre"] >= 0.80 and w["later_pre"] >= w["later_post"] - 0.15)
                          else "NOT MET")
        e["narr_premise"] = ("REFUTED" if w["withdrawn_pre"] >= 0.80
                             else "SUPPORTED" if w["withdrawn_pre"] <= w["withdrawn_post"] - 0.15 else "UNCLEAR")
    else:
        e["condition"] = e["status"]
        e["narr_premise"] = "NOT READ"
    print(f"=== E29-O recognition read: {model} ===")
    for probe, cells in (("K", PROBE_K), ("E", PROBE_E)):
        o = out[probe]
        print(f"  probe {probe}: {o['status']} (n = {o['n']})")
        if "hit" in o:
            for c in cells:
                print(f"    {c:15} rejected {o['hit'][f'{c}|rejected']:.3f}   control {o['hit'][f'{c}|control']:.3f}"
                      f"   J {o['J'][c]:+.3f}")
            print(f"    min parse {o['min_parse']:.3f}   max control {o['max_control']:.3f}")
    print(f"  T1 END-STATE CONDITION ({model}): {e['condition']}   NARR premise: {e['narr_premise']}")
    with open(f"results/e29o_recognition_{slug(model)}_summary.json", "w", encoding="utf-8") as f:
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
        print("E29-O RECOGNITION ALL DONE", flush=True)
