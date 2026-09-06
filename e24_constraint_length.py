"""e24_constraint_length.py: do inclusion and exclusion constraints move in
OPPOSITE directions with response length?

Declared in docs/protocols/E24-constraint-length.md before any generation.
Gated NARROW (T-2) -- the general principle that aggregation composition affects
rankings is published; the mechanism and the demonstration are not. NOT a
novelty claim.

THE MECHANISM, which is arithmetic before it is empirical:

    INCLUSION constraints ("mention X at least 3 times", "at least N words")
        get MONOTONICALLY EASIER as the response lengthens.
    EXCLUSION constraints ("never use the word Y", "at most N words")
        get MONOTONICALLY HARDER as the response lengthens.

IFEval's Keywords family contains both -- `include keywords` and
`keyword frequency` beside `forbidden words` -- scored into one aggregate. If
the two types respond oppositely to length, then a model's aggregate score
depends on the benchmark's inclusion:exclusion RATIO, which is an authoring
choice, and two benchmarks with the same constraints in different proportions
can rank the same models differently.

DESIGN. Response length is pinned by instruction (the technique E17 validated at
~100% compliance), and constraint satisfaction is checked programmatically.
Every constraint is verifiable with a short function, as in IFEval.
"""
import argparse
import csv
import itertools
import json
import re

from experiment import write_csv
from robust_client import RetryingOllamaClient

LENGTHS = {"short": 40, "medium": 120, "long": 300}

#: six neutral base tasks, no overlap with the E16 corpus
TASKS = [
    "Explain how a bicycle gear system works.",
    "Describe what happens during a thunderstorm.",
    "Explain why bread dough rises.",
    "Describe how a public library is organised.",
    "Explain what tides are and what causes them.",
    "Describe how a bridge carries load.",
]

#: (id, kind, instruction_text, verifier)
#: kind is "inclusion" (easier when longer) or "exclusion" (harder when longer)
CONSTRAINTS = [
    ("inc_kw3_system", "inclusion", 'Use the word "system" at least 3 times.',
     lambda t: len(re.findall(r"\bsystems?\b", t, re.I)) >= 3),
    ("inc_kw3_energy", "inclusion", 'Use the word "energy" at least 3 times.',
     lambda t: len(re.findall(r"\benergy\b", t, re.I)) >= 3),
    ("inc_kw2_because", "inclusion", 'Use the word "because" at least 2 times.',
     lambda t: len(re.findall(r"\bbecause\b", t, re.I)) >= 2),
    ("inc_kw2_example", "inclusion", 'Use the word "example" at least 2 times.',
     lambda t: len(re.findall(r"\bexamples?\b", t, re.I)) >= 2),
    ("inc_all3", "inclusion",
     'Include all three of these words: "pressure", "balance", "result".',
     lambda t: all(re.search(rf"\b{w}\w*\b", t, re.I)
                   for w in ("pressure", "balance", "result"))),
    ("inc_num2", "inclusion", "Include at least 2 numbers written as digits.",
     lambda t: len(re.findall(r"\d", t)) >= 2),
    ("inc_comma8", "inclusion", "Use at least 8 commas.",
     lambda t: t.count(",") >= 8),
    ("inc_sent5", "inclusion", "Write at least 5 sentences.",
     lambda t: len([s for s in re.split(r"[.!?]+", t) if s.strip()]) >= 5),
    ("exc_kw_very", "exclusion", 'Never use the word "very".',
     lambda t: not re.search(r"\bvery\b", t, re.I)),
    ("exc_kw_the", "exclusion", 'Never use the word "important".',
     lambda t: not re.search(r"\bimportant\b", t, re.I)),
    ("exc_kw_you", "exclusion", 'Never use the word "you".',
     lambda t: not re.search(r"\byou\b", t, re.I)),
    ("exc_kw_can", "exclusion", 'Never use the word "can".',
     lambda t: not re.search(r"\bcan\b", t, re.I)),
    ("exc_letter_z", "exclusion", 'Never use the letter "z".',
     lambda t: "z" not in t.lower()),
    ("exc_no_digits", "exclusion", "Do not use any digits.",
     lambda t: not re.search(r"\d", t)),
    ("exc_no_semicolon", "exclusion", "Do not use any semicolons or colons.",
     lambda t: ";" not in t and ":" not in t),
    ("exc_no_question", "exclusion", "Do not use any question marks.",
     lambda t: "?" not in t),
]

COLUMNS = ["model", "length", "target_words", "task", "constraint", "kind",
           "n_words", "satisfied"]


def build_prompt(task, instruction, target):
    return (f"{task}\n\n{instruction}\n"
            f"Write approximately {target} words. Reply with the answer only.")


def run(model, offset, limit):
    client = RetryingOllamaClient()
    combos = [(ln, t, c) for ln in LENGTHS for t in TASKS for c in CONSTRAINTS]
    combos = combos[offset:None if limit is None else offset + limit]
    print(f"=== E24 {model} | {len(combos)} generations ===\n")
    rows = []
    for i, (ln, task, (cid, kind, instr, verify)) in enumerate(combos, 1):
        target = LENGTHS[ln]
        msgs = [{"role": "user", "content": build_prompt(task, instr, target)}]
        text = client.chat(model=model, messages=msgs, temperature=0).text or ""
        rows.append({"model": model, "length": ln, "target_words": target,
                     "task": task[:28], "constraint": cid, "kind": kind,
                     "n_words": len(text.split()),
                     "satisfied": bool(verify(text))})
        if i % 48 == 0 or i == len(combos):
            print(f"  [{i:4}/{len(combos)}]")
    stem = f"results/e24_{model.replace('.','').replace(':','-')}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    print(f"\n  wrote {stem}.csv")
    for ln in LENGTHS:
        for kind in ("inclusion", "exclusion"):
            rs = [r for r in rows if r["length"] == ln and r["kind"] == kind]
            if rs:
                w = sum(r["n_words"] for r in rs) / len(rs)
                s = sum(r["satisfied"] for r in rs) / len(rs)
                print(f"  {ln:7} {kind:10} words {w:6.1f}  satisfied {s:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.model, a.offset, a.limit)
