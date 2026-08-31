"""experiment.py: the compulsory experiment. Three conditions, three repeats.

    recency window = 4 | 8 | 12,  three real runs each,  nine scored runs.

The independent variable is `max_messages` and nothing else. That is asserted
before any model is called, by diffing the three fully-expanded configurations
against each other -- if anything but `max_messages` differs, the run refuses to
start. The guard is self-tested: it is handed a deliberately corrupted pair and
must reject it.

Full history is run separately as a DIAGNOSTIC CEILING. It is not a fourth
condition and is not pooled into the comparison.

Every number in results/runs.csv is re-read from the saved transcript on disk,
not carried over from memory. The transcripts are the evidence; the table is
derived from them.

Run:  python experiment.py            # 9 scored runs
      python experiment.py --ceiling  # 3 extra full-history diagnostic runs
      python experiment.py --mock     # plumbing only, no model
"""
import argparse
import contextlib
import csv
import io
import json
import os
import statistics

import run_incident
from context import RecencyWindow, preflight
from finalise import MAX_ATTEMPTS
from judge import DEFAULT_JUDGE_MODEL
from scenario import AGENT_A, AGENT_B, INCIDENT

WINDOWS = [4, 8, 12]
REPEATS = 3
TURNS = 10

DIALOGUE_MAX_TOKENS = 100_000
DIALOGUE_MAX_SECONDS = 600

OUT_DIR = "transcripts/exp"
RESULTS_DIR = "results"

COLUMNS = [
    "condition", "window", "repeat",
    "parse_success", "retries",
    "constraint_recall", "violations", "violated", "deterministic_success",
    "source_coverage", "source_present", "source_total",
    "unknown_actions",
    "judge_score", "judge_success", "judge_stop_reason",
    "prompt_tokens", "completion_tokens", "seconds",
]


def condition_config(window):
    """Every setting a run depends on, fully expanded, for one condition."""
    return {
        "scenario": INCIDENT.id,
        "constraints": len(INCIDENT.constraints),
        "seed_messages": len(INCIDENT.seed_dialogue),
        "agent_a_name": AGENT_A.name,
        "agent_a_model": AGENT_A.model,
        "agent_a_temperature": AGENT_A.temperature,
        "agent_a_system_prompt": AGENT_A.system_prompt,
        "agent_b_name": AGENT_B.name,
        "agent_b_model": AGENT_B.model,
        "agent_b_temperature": AGENT_B.temperature,
        "agent_b_system_prompt": AGENT_B.system_prompt,
        "dialogue_max_turns": TURNS,
        "dialogue_max_tokens": DIALOGUE_MAX_TOKENS,
        "dialogue_max_seconds": DIALOGUE_MAX_SECONDS,
        "finalisation_max_attempts": MAX_ATTEMPTS,
        "judge_model": DEFAULT_JUDGE_MODEL,
        "judge_max_attempts": MAX_ATTEMPTS,
        "policy": "recency",
        # THE ONE INDEPENDENT VARIABLE
        "max_messages": window,
    }


def differing_keys(configs, ignore="max_messages"):
    """Keys whose value is not identical across every config."""
    keys = set().union(*(c.keys() for c in configs))
    return sorted(
        k for k in keys
        if k != ignore and len({json.dumps(c.get(k), sort_keys=True) for c in configs}) > 1
    )


def assert_one_variable(configs):
    """Refuse to run unless the conditions differ in max_messages alone."""
    # Self-test: the guard must reject a config that differs elsewhere.
    corrupted = [dict(configs[0]), dict(configs[0])]
    corrupted[1]["agent_a_temperature"] = 0.99
    if differing_keys(corrupted) != ["agent_a_temperature"]:
        raise AssertionError("the config-diff guard does not detect a real difference")

    bad = differing_keys(configs)
    if bad:
        raise AssertionError(f"conditions differ in more than max_messages: {bad}")
    windows = [c["max_messages"] for c in configs]
    if len(set(windows)) != len(windows):
        raise AssertionError(f"conditions are not distinct: {windows}")
    return True


def assert_not_inert(windows, dialogue_messages):
    """Refuse to run if every window would select the identical context."""
    fake = [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": f"m{i}"} for i in range(dialogue_messages)
    ]
    report = preflight(fake, [RecencyWindow(n) for n in windows])
    if report["inert"]:
        raise AssertionError(f"conditions are INERT at this length: {report}")
    return report


def row_from_transcript(path, condition, window, repeat):
    """Re-read one saved run from disk and flatten it into a results row."""
    with open(path) as f:
        data = json.load(f)
    m = data["meta"]
    ev = m["finalisation"]["evaluation"]
    cov = m["source_coverage"]
    j = m["judge"]
    total = m["realised"]["experiment_total"]
    return {
        "condition": condition,
        "window": window,
        "repeat": repeat,
        "parse_success": ev["parsed"],
        "retries": m["finalisation"]["retries"],
        "constraint_recall": ev["constraint_recall"],
        "violations": ev["violations"],
        "violated": "|".join(ev["violated"]),
        "deterministic_success": ev["success"],
        "source_coverage": cov["coverage"],
        "source_present": cov["source_messages_present"],
        "source_total": cov["source_messages_total"],
        "unknown_actions": len(ev["unknown_actions"]),
        "judge_score": j["score"],
        "judge_success": j["success"],
        "judge_stop_reason": j["stop_reason"],
        "prompt_tokens": total["prompt_tokens"],
        "completion_tokens": total["completion_tokens"],
        "seconds": total["seconds"],
    }


def summarise(rows):
    """Simple per-condition summaries. Means and rates only, by instruction."""
    out = []
    for condition in dict.fromkeys(r["condition"] for r in rows):
        g = [r for r in rows if r["condition"] == condition]
        judged = [r["judge_score"] for r in g if r["judge_score"] is not None]
        out.append({
            "condition": condition,
            "n": len(g),
            "mean_constraint_recall": round(
                statistics.mean(r["constraint_recall"] for r in g), 4),
            "deterministic_success_rate": round(
                sum(r["deterministic_success"] for r in g) / len(g), 4),
            "parse_rate": round(sum(r["parse_success"] for r in g) / len(g), 4),
            "mean_source_coverage": round(
                statistics.mean(r["source_coverage"] for r in g), 4),
            "mean_prompt_tokens": round(
                statistics.mean(r["prompt_tokens"] for r in g), 1),
            "mean_seconds": round(statistics.mean(r["seconds"] for r in g), 2),
            "mean_judge_score": round(statistics.mean(judged), 3) if judged else None,
            "n_judged": len(judged),
        })
    return out


def write_csv(path, rows, columns):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    return path


def show(rows, columns):
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in columns}
    print("  " + "  ".join(c.ljust(widths[c]) for c in columns))
    for r in rows:
        print("  " + "  ".join(str(r[c]).ljust(widths[c]) for c in columns))


def execute(window, repeat, mock, condition):
    """One run. Verbose output goes to a log beside the transcript."""
    out = f"{OUT_DIR}/{condition}_r{repeat}.json"
    log = f"{OUT_DIR}/{condition}_r{repeat}.log"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_incident.main(mock=mock, turns=TURNS, out=out, window=window,
                          host="http://localhost:11434")
    os.makedirs(os.path.dirname(log) or ".", exist_ok=True)
    with open(log, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    return out


def main(mock, ceiling_repeats):
    configs = [condition_config(w) for w in WINDOWS]

    print("=== preflight ===")
    assert_one_variable(configs)
    print(f"  config diff: conditions differ in max_messages alone "
          f"({[c['max_messages'] for c in configs]}) -- guard self-tested")

    expected_messages = len(INCIDENT.seed_dialogue) + TURNS
    report = assert_not_inert(WINDOWS, expected_messages)
    print(f"  inertness:   {report['distinct_contexts']} distinct contexts at "
          f"{expected_messages} messages, kept={report['kept']}, "
          f"identical_pairs={report['identical_pairs']}")
    print(f"  plan:        {len(WINDOWS)} conditions x {REPEATS} repeats = "
          f"{len(WINDOWS) * REPEATS} scored runs, {TURNS} dialogue turns each\n")

    rows = []
    for window in WINDOWS:
        condition = f"recency-{window}"
        for repeat in range(1, REPEATS + 1):
            path = execute(window, repeat, mock, condition)
            row = row_from_transcript(path, condition, window, repeat)
            rows.append(row)
            print(f"  {condition:<12} r{repeat}  recall {row['constraint_recall']:<6} "
                  f"success {str(row['deterministic_success']):<5} "
                  f"cov {row['source_coverage']:<4} "
                  f"judge {row['judge_score']}  {row['seconds']}s")

    print(f"\n=== per-run results ({len(rows)} scored runs) ===")
    show(rows, COLUMNS)
    print("\nwrote", write_csv(f"{RESULTS_DIR}/runs.csv", rows, COLUMNS))

    summary = summarise(rows)
    print("\n=== per-condition summary ===")
    show(summary, list(summary[0].keys()))
    print("\nwrote", write_csv(f"{RESULTS_DIR}/summary.csv", summary,
                               list(summary[0].keys())))

    if ceiling_repeats:
        print(f"\n=== full-history diagnostic ceiling ({ceiling_repeats} runs) ===")
        crows = []
        for repeat in range(1, ceiling_repeats + 1):
            path = execute(None, repeat, mock, "full")
            crows.append(row_from_transcript(path, "full", "full", repeat))
            print(f"  full         r{repeat}  recall {crows[-1]['constraint_recall']:<6} "
                  f"success {str(crows[-1]['deterministic_success']):<5} "
                  f"cov {crows[-1]['source_coverage']:<4} "
                  f"judge {crows[-1]['judge_score']}  {crows[-1]['seconds']}s")
        show(crows, COLUMNS)
        print("\nwrote", write_csv(f"{RESULTS_DIR}/ceiling.csv", crows, COLUMNS))
        cs = summarise(crows)
        show(cs, list(cs[0].keys()))
        write_csv(f"{RESULTS_DIR}/ceiling_summary.csv", cs, list(cs[0].keys()))
        print("\nThe ceiling is a diagnostic, NOT a fourth condition. It is not "
              "pooled with the three scored conditions above.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true")
    p.add_argument("--ceiling", type=int, nargs="?", const=3, default=0,
                   help="also run N full-history diagnostic runs (default 3)")
    args = p.parse_args()
    main(mock=args.mock, ceiling_repeats=args.ceiling)
