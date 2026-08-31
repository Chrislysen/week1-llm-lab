"""e1_landscape.py: E1 -- the post-amendment scored retrieval landscape.

    5 scored conditions x 3 repeats = 15 runs
    + oracle x 3, run SEPARATELY as a diagnostic, never pooled with the five.

Runs against the frozen protocol at tag `selector-protocol-v1`: current-message
separation, W = 250 history words, alpha = 0.40, frozen query definitions,
message-level retrieval unit. Nothing is tuned from the results.

Random seeds are predeclared in results/e1_seeds.json, committed before the
first model call, and echoed into every run artifact.

E1 is a MECHANISM AND VIABILITY experiment on ONE scenario. It is not
generalization evidence and is not significance-tested, by instruction.

Run:  python e1_landscape.py --mock
      python e1_landscape.py
"""
import argparse
import contextlib
import io
import json
import os
import statistics

import run_incident
from context import (BM25Budget, DenseBudget, FusionBudget, OracleBudget,
                     RandomBudget, RecencyBudget)
from experiment import TURNS, row_from_transcript, show, write_csv
from scenario import CONSTRAINTS, INCIDENT

W = 250
REPEATS = 3
OUT_DIR = "transcripts/e1"
RESULTS_DIR = "results"
SEED_FILE = "results/e1_seeds.json"

SOURCE_TURNS = sorted({c.stated_at_turn for c in CONSTRAINTS})
SOURCE_TEXTS = [INCIDENT.seed_dialogue[t][1] for t in SOURCE_TURNS]
SEEDED = len(INCIDENT.seed_dialogue)

SEEDS = {int(k): v for k, v in
         json.load(open(SEED_FILE))["random_seeds"].items()}

#: The five scored conditions. Oracle is deliberately NOT here.
SCORED = ["recency", "random", "bm25", "dense", "fusion"]

COLUMNS = [
    "condition", "repeat", "seed",
    "constraint_recall", "deterministic_success",
    "retrieval_recall", "violated", "violations",
    "sel_source", "sel_seed_other", "sel_generated", "selected_ids",
    "unknown_actions", "parse_success", "retries",
    "judge_score", "judge_success",
    "history_words", "current_words",
    "prompt_tokens", "completion_tokens", "seconds",
]


def policy_for(condition, repeat):
    if condition == "recency":
        return RecencyBudget(W), None
    if condition == "random":
        return RandomBudget(W, seed=SEEDS[repeat]), SEEDS[repeat]
    if condition == "bm25":
        return BM25Budget(W), None
    if condition == "dense":
        return DenseBudget(W), None
    if condition == "fusion":
        return FusionBudget(W), None
    if condition == "oracle":
        return OracleBudget(W, SOURCE_TEXTS), None
    raise ValueError(condition)


def execute(condition, repeat, mock):
    policy, seed = policy_for(condition, repeat)
    out = f"{OUT_DIR}/{condition}_r{repeat}.json"
    log = f"{OUT_DIR}/{condition}_r{repeat}.log"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_incident.main(mock=mock, turns=TURNS, out=out, window=policy,
                          host="http://localhost:11434")
    os.makedirs(os.path.dirname(log) or ".", exist_ok=True)
    with open(log, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())

    # Echo the seed and the protocol into the artifact itself, so a run is
    # self-describing without needing this script.
    with open(out) as f:
        data = json.load(f)
    data["meta"]["e1"] = {
        "condition": condition, "repeat": repeat, "seed": seed,
        "history_budget_words": W, "protocol_tag": "selector-protocol-v1",
    }
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    return out, seed


def compose(selected_ids):
    """Split a selection into source / other-seed / generated messages.

    Candidate positions map straight onto dialogue positions, because the pool
    is the dialogue minus its last message.
    """
    src = sum(i in SOURCE_TURNS for i in selected_ids)
    seed_other = sum(i < SEEDED and i not in SOURCE_TURNS for i in selected_ids)
    return src, seed_other, len(selected_ids) - src - seed_other


def build_row(path, condition, repeat, seed):
    base = row_from_transcript(path, condition, W, repeat)
    with open(path) as f:
        m = json.load(f)["meta"]

    # The LAST context call is the finalisation selection -- the one that
    # produced the plan being scored.
    final_call = m["context"]["calls"][-1]
    ids = final_call.get("selected_ids", [])
    src, seed_other, gen = compose(ids)

    cov = m["source_coverage"]
    return {
        "condition": condition,
        "repeat": repeat,
        "seed": seed if seed is not None else "",
        "constraint_recall": base["constraint_recall"],
        "deterministic_success": base["deterministic_success"],
        "retrieval_recall": cov["coverage"],
        "violated": base["violated"],
        "violations": base["violations"],
        "sel_source": src,
        "sel_seed_other": seed_other,
        "sel_generated": gen,
        "selected_ids": "|".join(map(str, ids)),
        "unknown_actions": base["unknown_actions"],
        "parse_success": base["parse_success"],
        "retries": base["retries"],
        "judge_score": base["judge_score"],
        "judge_success": base["judge_success"],
        "history_words": final_call.get("words_history"),
        "current_words": final_call.get("words_current"),
        "prompt_tokens": base["prompt_tokens"],
        "completion_tokens": base["completion_tokens"],
        "seconds": base["seconds"],
    }


def summarise(rows):
    out = []
    for cond in dict.fromkeys(r["condition"] for r in rows):
        g = [r for r in rows if r["condition"] == cond]
        judged = [r["judge_score"] for r in g if r["judge_score"] is not None]
        out.append({
            "condition": cond,
            "n": len(g),
            "mean_constraint_recall": round(
                statistics.mean(r["constraint_recall"] for r in g), 4),
            "success_rate": round(
                sum(r["deterministic_success"] for r in g) / len(g), 4),
            "mean_retrieval_recall": round(
                statistics.mean(r["retrieval_recall"] for r in g), 4),
            "mean_sel_source": round(statistics.mean(r["sel_source"] for r in g), 2),
            "mean_sel_generated": round(
                statistics.mean(r["sel_generated"] for r in g), 2),
            "parse_rate": round(sum(r["parse_success"] for r in g) / len(g), 4),
            "mean_unknown_actions": round(
                statistics.mean(r["unknown_actions"] for r in g), 2),
            "mean_judge": round(statistics.mean(judged), 2) if judged else None,
            "mean_history_words": round(
                statistics.mean(r["history_words"] for r in g), 1),
            "mean_prompt_tokens": round(
                statistics.mean(r["prompt_tokens"] for r in g), 1),
            "mean_seconds": round(statistics.mean(r["seconds"] for r in g), 2),
        })
    return out


def run_block(conditions, mock, label):
    rows = []
    for cond in conditions:
        for repeat in range(1, REPEATS + 1):
            path, seed = execute(cond, repeat, mock)
            row = build_row(path, cond, repeat, seed)
            rows.append(row)
            print(f"  {cond:<8} r{repeat}"
                  f"{f' seed={seed}' if seed else '        '}"
                  f"  recall {row['constraint_recall']:<6} "
                  f"retr {row['retrieval_recall']:<4} "
                  f"src/gen {row['sel_source']}/{row['sel_generated']}  "
                  f"succ {str(row['deterministic_success']):<5} "
                  f"judge {row['judge_score']}  {row['seconds']}s")
    return rows


def main(mock):
    print("=== E1: post-amendment scored retrieval landscape ===")
    print(f"  protocol tag        selector-protocol-v1 (frozen)")
    print(f"  history budget      W = {W} words, current-message separation ON")
    print(f"  predeclared seeds   {SEEDS}  (from {SEED_FILE})")
    print(f"  scored conditions   {SCORED} x {REPEATS}")
    print(f"  diagnostic          oracle x {REPEATS}, reported separately\n")

    print(f"--- scored ({len(SCORED) * REPEATS} runs) ---")
    rows = run_block(SCORED, mock, "scored")

    print(f"\n--- oracle diagnostic ({REPEATS} runs, NOT pooled) ---")
    orows = run_block(["oracle"], mock, "diagnostic")

    print(f"\n=== E1 per-run ({len(rows)} scored runs) ===")
    show(rows, COLUMNS)
    write_csv(f"{RESULTS_DIR}/e1_runs.csv", rows, COLUMNS)

    print("\n=== E1 per-condition summary (scored) ===")
    summary = summarise(rows)
    show(summary, list(summary[0].keys()))
    write_csv(f"{RESULTS_DIR}/e1_summary.csv", summary, list(summary[0].keys()))

    print("\n=== oracle diagnostic (separate, not an E1 condition) ===")
    show(orows, COLUMNS)
    osum = summarise(orows)
    show(osum, list(osum[0].keys()))
    write_csv(f"{RESULTS_DIR}/e1_oracle.csv", orows, COLUMNS)
    write_csv(f"{RESULTS_DIR}/e1_oracle_summary.csv", osum, list(osum[0].keys()))

    tok = [s["mean_prompt_tokens"] for s in summary]
    hist = [s["mean_history_words"] for s in summary]
    print(f"\n=== budget parity (scored arms) ===")
    print(f"  history words      {min(hist)} - {max(hist)}  "
          f"(spread {round(max(hist) - min(hist), 1)})")
    print(f"  prompt tokens      {min(tok)} - {max(tok)}  "
          f"(spread {round(max(tok) - min(tok), 1)}, "
          f"{round(100 * (max(tok) - min(tok)) / statistics.mean(tok), 1)}% of mean)")

    print("\nwrote results/e1_runs.csv, e1_summary.csv, e1_oracle.csv, "
          "e1_oracle_summary.csv")
    print("\nE1 is a mechanism/viability experiment on ONE scenario. Not "
          "significance-tested, not generalization evidence, and no selector "
          "may be tuned from it.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true")
    main(mock=p.parse_args().mock)
