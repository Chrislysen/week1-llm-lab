"""e25_ifeval.py: does the type-by-length confound appear on IFEval's REAL items?

Declared in docs/protocols/E25-ifeval.md before any generation. E24/E24-C
established the mechanism on 16 hand-written constraints; the standing objection
was that those are not a real benchmark's items. This uses IFEval's actual 541
prompts and its actual instruction types.

CLASSIFICATION, from IFEval's own instruction ids and kwargs:

  INCLUSION  (satisfied more easily by a LONGER response)
    keywords:existence                  include these keywords
    keywords:frequency        (>=)      keyword at least N times
    length_constraints:number_words (>=) at least N words
  EXCLUSION  (satisfied less easily by a LONGER response)
    keywords:forbidden_words            do not use these words
    punctuation:no_comma                no commas anywhere
    length_constraints:number_words (<)  fewer than N words

Everything else (formatting, casing, language, structure) is length-neutral or
ambiguous and is EXCLUDED from the analysis rather than guessed at.

Scoring is IFEval's instruction-level convention: each target instruction in a
prompt is verified independently, so a prompt carrying several instructions
contributes one observation per target instruction.
"""
import argparse
import json
import re
import statistics

from datasets import load_dataset

from experiment import write_csv
from robust_client import RetryingOllamaClient

INCLUSION = {"keywords:existence", "keywords:frequency",
             "length_constraints:number_words"}
EXCLUSION = {"keywords:forbidden_words", "punctuation:no_comma"}
#: Runaway guard. Small models loop forever on some IFEval prompts (e.g. the
#: all-caps song-lyric item, key 1132, which consumed 515s before being killed).
#: 1500 tokens is ~1100 words -- far above any legitimate IFEval response, whose
#: longest length constraint is "at least 500 words". Responses hitting the cap
#: are counted and reported.
RUNAWAY_CAP = 1500

COLUMNS = ["model", "key", "instruction_id", "kind", "n_words", "satisfied"]


def classify(iid, kw):
    """(kind, verifier) or None if length-neutral / not analysed."""
    if iid == "keywords:existence":
        ks = kw.get("keywords") or []
        return "inclusion", lambda t: all(
            re.search(rf"\b{re.escape(k)}", t, re.I) for k in ks)
    if iid == "keywords:frequency":
        k, n, rel = kw.get("keyword"), kw.get("frequency"), kw.get("relation")
        if not k or n is None:
            return None
        cnt = lambda t: len(re.findall(rf"\b{re.escape(k)}", t, re.I))
        if rel == "at least":
            return "inclusion", lambda t: cnt(t) >= n
        return "exclusion", lambda t: cnt(t) < n
    if iid == "length_constraints:number_words":
        n, rel = kw.get("num_words"), kw.get("relation")
        if n is None:
            return None
        if rel == "at least":
            return "inclusion", lambda t: len(t.split()) >= n
        return "exclusion", lambda t: len(t.split()) < n
    if iid == "keywords:forbidden_words":
        fs = kw.get("forbidden_words") or []
        return "exclusion", lambda t: not any(
            re.search(rf"\b{re.escape(f)}", t, re.I) for f in fs)
    if iid == "punctuation:no_comma":
        return "exclusion", lambda t: "," not in t
    return None


def targets():
    """[(key, prompt, [(iid, kind, verifier), ...]), ...] for analysed prompts."""
    ds = load_dataset("google/IFEval", split="train")
    out = []
    for r in ds:
        items = []
        for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
            if iid in INCLUSION or iid in EXCLUSION:
                c = classify(iid, {k: v for k, v in kw.items() if v is not None})
                if c:
                    items.append((iid, c[0], c[1]))
        if items:
            out.append((r["key"], r["prompt"], items))
    return out


def run(model, offset, limit):
    ts = targets()
    ts = ts[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    print(f"=== E25 {model} | {len(ts)} IFEval prompts ===\n")
    rows = []
    for i, (key, prompt, items) in enumerate(ts, 1):
        text = client.chat(model=model,
                           messages=[{"role": "user", "content": prompt}],
                           temperature=0, num_predict=RUNAWAY_CAP).text or ""
        nw = len(text.split())
        for iid, kind, verify in items:
            rows.append({"model": model, "key": key, "instruction_id": iid,
                         "kind": kind, "n_words": nw,
                         "satisfied": bool(verify(text))})
        if i % 40 == 0 or i == len(ts):
            print(f"  [{i:3}/{len(ts)}]")
    stem = ("results/e25_" + model.replace(".", "").replace(":", "-")
            + f"_o{offset}")
    write_csv(stem + ".csv", rows, COLUMNS)
    print(f"\n  wrote {stem}.csv")
    for k in ("inclusion", "exclusion"):
        rs = [r for r in rows if r["kind"] == k]
        if rs:
            print(f"  {k:10} n={len(rs):4}  satisfied {sum(r['satisfied'] for r in rs)/len(rs):.3f}")
    ok = {(r["key"], r["n_words"]) for r in rows}
    print(f"  mean response words {statistics.mean(w for _, w in ok):.1f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.model, a.offset, a.limit)
