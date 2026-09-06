"""e24c_hard.py: the reorder test with an exclusion set that is not at ceiling.

E24-B's diagnosis: 6 of 8 exclusion constraints sat at 1.000 because models never
spontaneously used the forbidden tokens, pinning the exclusion side near 1.0 and
compressing the differences a reorder test needs. More items could not fix that.

THE FIX. Forbid words the task ACTIVELY ELICITS, so satisfaction sits mid-range
where verbosity can move it. Each task gets its own forbidden terms.

Declared in docs/protocols/E24-constraint-length.md before any generation.
"""
import argparse
import re

from e24_constraint_length import CONSTRAINTS as BASE
from experiment import write_csv
from robust_client import RetryingOllamaClient

#: task -> words the task naturally elicits, forbidden one at a time
TASKS_HARD = {
    "Explain how a bicycle gear system works.": ["gear", "wheel", "chain", "pedal"],
    "Describe what happens during a thunderstorm.": ["storm", "lightning", "cloud", "rain"],
    "Explain why bread dough rises.": ["yeast", "dough", "gas", "bread"],
    "Describe how a public library is organised.": ["book", "library", "shelf", "borrow"],
    "Explain what tides are and what causes them.": ["moon", "tide", "water", "gravity"],
    "Describe how a bridge carries load.": ["bridge", "load", "weight", "support"],
}
INCLUSION = [c for c in BASE if c[1] == "inclusion"]

COLUMNS = ["model", "task", "constraint", "kind", "n_words", "satisfied"]


def combos():
    out = []
    for task, words in TASKS_HARD.items():
        for w in words:
            out.append((task, f"exc_hard_{w}", "exclusion",
                        f'Never use the word "{w}".',
                        (lambda ww: lambda t: not re.search(rf"\b{ww}\w*\b", t, re.I))(w)))
        for cid, kind, instr, verify in INCLUSION:
            out.append((task, cid, kind, instr, verify))
    return out


def run(model, offset, limit):
    client = RetryingOllamaClient()
    cs = combos()[offset:None if limit is None else offset + limit]
    print(f"=== E24-C {model} | {len(cs)} generations ===\n")
    rows = []
    for i, (task, cid, kind, instr, verify) in enumerate(cs, 1):
        msg = [{"role": "user",
                "content": f"{task}\n\n{instr}\nReply with the answer only."}]
        text = client.chat(model=model, messages=msg, temperature=0).text or ""
        rows.append({"model": model, "task": task[:28], "constraint": cid,
                     "kind": kind, "n_words": len(text.split()),
                     "satisfied": bool(verify(text))})
        if i % 24 == 0 or i == len(cs):
            print(f"  [{i:3}/{len(cs)}]")
    stem = ("results/e24c_" + model.replace(".", "").replace(":", "-")
            + f"_o{offset}")
    write_csv(stem + ".csv", rows, COLUMNS)
    print(f"\n  wrote {stem}.csv")
    for k in ("inclusion", "exclusion"):
        rs = [r for r in rows if r["kind"] == k]
        if rs:
            print(f"  {k:10} n={len(rs):3} words {sum(r['n_words'] for r in rs)/len(rs):6.1f}"
                  f"  satisfied {sum(r['satisfied'] for r in rs)/len(rs):.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.model, a.offset, a.limit)
