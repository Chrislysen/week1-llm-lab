"""pilot.py: the viability gate for the retrieval extension.

One question: IS THERE ANY HEADROOM?

Not "does BM25 beat recency". If an ORACLE -- handed exactly the messages that
carry planted constraints, competing under the same word budget -- cannot beat
recency, then no retriever can, and building BM25/dense/fusion would be work
spent on an effect that is not there.

    3 arms (recency / random / oracle) x 3 repeats = 9 runs at W = 250 words.

Decision rules, fixed here BEFORE the runs (see docs/research-design.md S8):

  oracle <= recency          -> STOP selector development. Report "no
                                task-level retrieval headroom demonstrated on
                                this scenario at this budget". NOT "H2 confirmed"
                                -- a 3x3 pilot with no noise floor cannot
                                confirm a hypothesis.
  oracle > recency ~= random -> the metric is insensitive to WHICH messages are
                                kept. Stop and diagnose the scenario.
  oracle > recency > random  -> headroom exists. Proceed to build the selectors.

Run:  python pilot.py --mock
      python pilot.py
"""
import argparse
import contextlib
import io
import json
import os
import statistics

import run_incident
from context import OracleBudget, RandomBudget, RecencyBudget, preflight
from experiment import COLUMNS, TURNS, row_from_transcript, show, write_csv
from scenario import CONSTRAINTS, INCIDENT

W = 250
REPEATS = 3
OUT_DIR = "transcripts/pilot"
RESULTS_DIR = "results"

#: The oracle's hidden knowledge: the exact seed messages that carry planted
#: constraints. Used ONLY to choose among messages already in the dialogue.
SOURCE_TEXTS = [
    INCIDENT.seed_dialogue[t][1]
    for t in sorted({c.stated_at_turn for c in CONSTRAINTS})
]

PILOT_COLUMNS = COLUMNS + [
    "retrieval_recall", "exec_acc_given_retrieval", "n_retrieved_constraints",
    "words_kept_mean", "words_available_mean",
]


def arms(repeat):
    """The three pilot arms. Random is seeded per repeat, so runs are reproducible."""
    return [
        ("recency", RecencyBudget(W)),
        ("random", RandomBudget(W, seed=repeat)),
        ("oracle", OracleBudget(W, SOURCE_TEXTS)),
    ]


def enrich(row, path):
    """Add the retrieved-vs-used split, re-read from the saved transcript."""
    with open(path) as f:
        m = json.load(f)["meta"]

    cov = m["source_coverage"]
    satisfied = set(m["finalisation"]["evaluation"]["satisfied"])
    retrieved = cov["constraints_with_source_present"]

    row["retrieval_recall"] = cov["coverage"]
    row["n_retrieved_constraints"] = len(retrieved)
    # Undefined, not zero, when nothing was retrieved. Reported with its n.
    row["exec_acc_given_retrieval"] = (
        round(len([c for c in retrieved if c in satisfied]) / len(retrieved), 4)
        if retrieved else None
    )

    calls = m["context"]["calls"]
    row["words_kept_mean"] = round(statistics.mean(c["words_kept"] for c in calls), 1)
    row["words_available_mean"] = round(
        statistics.mean(c["words_available"] for c in calls), 1)
    return row


def execute(arm, policy, repeat, mock):
    out = f"{OUT_DIR}/{arm}_r{repeat}.json"
    log = f"{OUT_DIR}/{arm}_r{repeat}.log"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_incident.main(mock=mock, turns=TURNS, out=out, window=policy,
                          host="http://localhost:11434")
    os.makedirs(os.path.dirname(log) or ".", exist_ok=True)
    with open(log, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    return out


def gate(summary):
    """Apply the pre-registered decision rules. Returns (verdict, explanation)."""
    by = {s["condition"]: s["mean_constraint_recall"] for s in summary}
    rec, ran, ora = by["recency"], by["random"], by["oracle"]
    if ora <= rec:
        return "STOP", (
            f"oracle ({ora}) <= recency ({rec}). No task-level retrieval headroom "
            "demonstrated on this scenario at this budget. This is NOT a confirmed "
            "hypothesis -- a 3x3 pilot with no noise floor cannot confirm one. "
            "Do not build BM25, dense or fusion."
        )
    if ora <= ran:
        return "DIAGNOSE", (
            f"oracle ({ora}) > recency ({rec}) but <= random ({ran}). The metric is "
            "not sensitive to WHICH messages are kept. Diagnose the scenario before "
            "building any selector."
        )
    return "PROCEED", (
        f"oracle ({ora}) > recency ({rec}) and > random ({ran}). Headroom exists at "
        "this budget; selector development is justified."
    )


def main(mock):
    print("=== pilot preflight ===")
    expected = len(INCIDENT.seed_dialogue) + TURNS
    # Each stand-in must have DISTINCT content. An earlier version used the same
    # 40-word string for every message, so any six of them fingerprinted
    # identically and preflight reported inert==True on arms that are plainly
    # not inert. A preflight that misreports is worse than no preflight.
    # The first len(SOURCE_TEXTS) carry the real source texts so the oracle's
    # priority is actually exercised.
    fake = [{"role": "system", "content": "s"}]
    for i in range(expected):
        fake.append({
            "role": "user",
            "content": SOURCE_TEXTS[i] if i < len(SOURCE_TEXTS)
            else " ".join(f"m{i}w{k}" for k in range(40)),
        })
    report = preflight(fake, [p for _, p in arms(1)])
    print(f"  W = {W} words of retrieved dialogue history "
          f"(system prompt, query and final instruction are OUTSIDE the budget)")
    print(f"  source messages known to the oracle: {len(SOURCE_TEXTS)}")
    print(f"  distinct contexts: {report['distinct_contexts']}, "
          f"identical_pairs: {report['identical_pairs']}, inert: {report['inert']}")
    print(f"  plan: 3 arms x {REPEATS} repeats = {3 * REPEATS} runs, "
          f"{TURNS} dialogue turns each\n")

    rows = []
    for repeat in range(1, REPEATS + 1):
        for arm, policy in arms(repeat):
            path = execute(arm, policy, repeat, mock)
            row = row_from_transcript(path, arm, W, repeat)
            rows.append(enrich(row, path))
            print(f"  {arm:<8} r{repeat}  recall {row['constraint_recall']:<6} "
                  f"retr {row['retrieval_recall']:<4} "
                  f"exec {str(row['exec_acc_given_retrieval']):<6} "
                  f"words {row['words_kept_mean']:<6} "
                  f"tok {row['prompt_tokens']:<6} {row['seconds']}s")

    rows.sort(key=lambda r: (r["condition"], r["repeat"]))
    print(f"\n=== per-run ({len(rows)} runs) ===")
    show(rows, PILOT_COLUMNS)
    print("\nwrote", write_csv(f"{RESULTS_DIR}/pilot_runs.csv", rows, PILOT_COLUMNS))

    summary = []
    for cond in ("recency", "random", "oracle"):
        g = [r for r in rows if r["condition"] == cond]
        exec_vals = [r["exec_acc_given_retrieval"] for r in g
                     if r["exec_acc_given_retrieval"] is not None]
        summary.append({
            "condition": cond,
            "n": len(g),
            "mean_constraint_recall": round(
                statistics.mean(r["constraint_recall"] for r in g), 4),
            "success_rate": round(sum(r["deterministic_success"] for r in g) / len(g), 4),
            "mean_retrieval_recall": round(
                statistics.mean(r["retrieval_recall"] for r in g), 4),
            "mean_exec_acc": round(statistics.mean(exec_vals), 4) if exec_vals else None,
            "n_exec_defined": len(exec_vals),
            "mean_words_kept": round(statistics.mean(r["words_kept_mean"] for r in g), 1),
            "mean_prompt_tokens": round(statistics.mean(r["prompt_tokens"] for r in g), 1),
            "mean_seconds": round(statistics.mean(r["seconds"] for r in g), 2),
        })

    print("\n=== per-arm summary ===")
    show(summary, list(summary[0].keys()))
    print("\nwrote", write_csv(f"{RESULTS_DIR}/pilot_summary.csv", summary,
                               list(summary[0].keys())))

    verdict, why = gate(summary)
    print(f"\n=== GATE: {verdict} ===\n  {why}")

    # Budget parity audit. Equal capacity is the design's core claim; realised
    # spend is the only thing that can falsify it.
    tok = [s["mean_prompt_tokens"] for s in summary]
    print(f"\n  budget parity: mean prompt tokens {tok}, "
          f"spread {round(max(tok) - min(tok), 1)} "
          f"({round(100 * (max(tok) - min(tok)) / statistics.mean(tok), 1)}% of mean)")
    return verdict


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true")
    main(mock=p.parse_args().mock)
