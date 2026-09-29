"""comp_analysis.py: descriptive analysis of the frozen compulsory runs.

Read-only. Zero model calls. Reads the 12 transcripts in transcripts/exp/ and
first checks each one is byte-identical to the copy frozen at tag
compulsory-baseline-v1, so nothing here can be computed from edited evidence.
Writes tables and figures to results/comp_analysis/. Every number in
docs/COMP-ANALYSIS.md comes from this script.

    python comp_analysis.py

What it answers, in order:

  A. Are the three repeats per condition independent?        (trajectories)
  B. Which rules broke, in which runs?                       (constraint matrix)
  C. Was the rule's source message in context when it broke? (visibility)
  D. What did the dialogue actually talk about?              (concept mentions)
  E. What did the final plans contain?                       (plans)
  F. What did each condition cost?                           (cost)
  G. What did the judge say, and did it discriminate?        (judge)

The concept lexicon in D is a keyword heuristic. It says whether a word was
used, not whether a rule was stated correctly. It is reported as such.
"""
import csv
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys

from scenario import ACTIONS, INCIDENT

TAG = "compulsory-baseline-v1"
RUN_DIR = "transcripts/exp"
OUT = "results/comp_analysis"
CONDITIONS = ["recency-4", "recency-8", "recency-12", "full"]
WINDOW = {"recency-4": 4, "recency-8": 8, "recency-12": 12, "full": None}
SEEDED = len(INCIDENT.seed_dialogue)          # 6 scripted turns
CONSTRAINTS = INCIDENT.constraints
CIDS = [c.id for c in CONSTRAINTS]

#: One pattern per action concept. Heuristic: word use, not correct statement.
CONCEPTS = {
    "ISOLATE_NODE": r"isolat",
    "RUN_DIAGNOSTICS": r"diagnos",
    "RUN_BACKUP": r"back ?up|backed up",
    "FAILOVER_API": r"fail(?:ed|ing|s)? ?over",
    "RESTART_DB": r"restart",
    "RESTORE_TRAFFIC": r"traffic",
}


# --------------------------------------------------------------------- loading
def verify_frozen(path):
    """Refuse to analyse a transcript that differs from the tagged copy."""
    rel = path.replace("\\", "/")
    frozen = subprocess.run(["git", "show", f"{TAG}:{rel}"],
                            capture_output=True, check=True).stdout
    with open(path, "rb") as fh:
        local = fh.read()
    if local.replace(b"\r\n", b"\n") != frozen.replace(b"\r\n", b"\n"):
        sys.exit(f"REFUSING: {rel} differs from {TAG}")


def load_runs():
    runs = []
    for cond in CONDITIONS:
        for r in (1, 2, 3):
            path = f"{RUN_DIR}/{cond}_r{r}.json"
            verify_frozen(path)
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            runs.append({"label": f"{cond}_r{r}", "cond": cond, "repeat": r, "d": d})
    return runs


def generated(run):
    """The model-written dialogue turns (everything after the seed)."""
    return run["d"]["messages"][SEEDED:]


def digest(texts):
    return hashlib.sha1("\n\x00".join(texts).encode()).hexdigest()[:8]


def visible_turns(cond, total=16):
    """Turn indices the Operations Lead could see when writing the final plan."""
    w = WINDOW[cond]
    return list(range(total)) if w is None else list(range(max(0, total - w), total))


# ------------------------------------------------------------------- analyses
def trajectories(runs):
    """A. Distinct dialogues per condition, and where each run leaves full history."""
    ref = {m["turn_index"]: m["content"] for m in generated(runs[-3])}  # full_r1
    rows = []
    for run in runs:
        gen = generated(run)
        plan = run["d"]["meta"]["finalisation"]["attempts"][-1]["content"]
        actions = run["d"]["meta"]["finalisation"]["evaluation"]["actions"]
        first_diff = next((m["turn_index"] for m in gen
                           if m["content"] != ref[m["turn_index"]]), None)
        rows.append({
            "run": run["label"],
            "condition": run["cond"],
            "dialogue_hash": digest([m["content"] for m in gen]),
            # Raw reply text: differs if only the code fence or spacing differs.
            "plan_text_hash": digest([plan]),
            "plan_actions_hash": digest(actions),
            "first_turn_differing_from_full_r1": first_diff,
        })
    summary = []
    for cond in CONDITIONS:
        g = [r for r in rows if r["condition"] == cond]
        summary.append({
            "condition": cond,
            "runs": len(g),
            "distinct_dialogues": len({r["dialogue_hash"] for r in g}),
            "distinct_plan_texts": len({r["plan_text_hash"] for r in g}),
            "distinct_action_lists": len({r["plan_actions_hash"] for r in g}),
        })
    return rows, summary


def distinct_runs(runs, traj):
    """One representative per (condition, dialogue, plan actions): the real sample."""
    seen, keep = set(), []
    for run, t in zip(runs, traj):
        key = (t["condition"], t["dialogue_hash"], t["plan_actions_hash"])
        if key not in seen:
            seen.add(key)
            keep.append(run)
    return keep


def pairwise_divergence(runs, cond):
    """First generated turn at which each pair of repeats differs."""
    g = [r for r in runs if r["cond"] == cond]
    out = []
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            a, b = generated(g[i]), generated(g[j])
            t = next((x["turn_index"] for x, y in zip(a, b)
                      if x["content"] != y["content"]), None)
            out.append({"pair": f"{g[i]['label']} vs {g[j]['label']}", "first_diff_turn": t})
    return out


def constraint_matrix(runs):
    """B + C. Per run and rule: violated? source message visible at finalisation?"""
    rows = []
    for run in runs:
        ev = run["d"]["meta"]["finalisation"]["evaluation"]
        vis = set(visible_turns(run["cond"]))
        row = {"run": run["label"], "condition": run["cond"]}
        for c in CONSTRAINTS:
            row[c.id] = int(c.id in ev["violated"])
            row[f"{c.id}_source_visible"] = int(c.stated_at_turn in vis)
        rows.append(row)
    by_cond = []
    for cond in CONDITIONS:
        g = [r for r in rows if r["condition"] == cond]
        by_cond.append({"condition": cond,
                        **{c: f"{sum(r[c] for r in g)}/{len(g)}" for c in CIDS}})
    # Cross-tab over all 12 runs x 7 rules: is breaking a rule tied to losing its source?
    cells = [(r[c], r[f"{c}_source_visible"]) for r in rows for c in CIDS]
    xtab = {
        "violated_source_visible": sum(1 for v, s in cells if v and s),
        "violated_source_gone": sum(1 for v, s in cells if v and not s),
        "kept_source_visible": sum(1 for v, s in cells if not v and s),
        "kept_source_gone": sum(1 for v, s in cells if not v and not s),
    }
    return rows, by_cond, xtab


def concept_mentions(runs):
    """D. Which action concepts each generated turn mentions (keyword heuristic)."""
    rows = []
    for run in runs:
        for m in generated(run):
            text = m["content"].lower()
            hits = {k: int(bool(re.search(p, text))) for k, p in CONCEPTS.items()}
            rows.append({"run": run["label"], "condition": run["cond"],
                         "turn": m["turn_index"], "speaker": m["speaker"],
                         **hits, "any": int(any(hits.values())), "content_lower": text})
    per_run = []
    for run in runs:
        g = [r for r in rows if r["run"] == run["label"]]
        vis = set(visible_turns(run["cond"]))
        seen = [r for r in g if r["turn"] in vis]
        per_run.append({
            "run": run["label"],
            "condition": run["cond"],
            "turns_with_no_action_concept": f"{sum(1 - r['any'] for r in g)}/{len(g)}",
            **{f"mentions_{k}": sum(r[k] for r in g) for k in CONCEPTS},
            # The invented "remove the node from the network" step (turns 6-7 in
            # the recency-8/12/full trajectories). No seed turn uses "remov".
            "node_removal_step_in_final_context": int(
                any(re.search(r"remov", r["content_lower"]) for r in seen)),
            "isolation_mentioned_in_final_context": int(
                any(r["ISOLATE_NODE"] for r in seen)
                or any(INCIDENT.seed_dialogue[t][1].lower().count("isolat")
                       for t in vis if t < SEEDED)),
        })
    return rows, per_run


def plans(runs):
    """E. Final plan contents."""
    rows = []
    for run in runs:
        fin = run["d"]["meta"]["finalisation"]
        ev = fin["evaluation"]
        acts = ev["actions"]
        pos = {a: (acts.index(a) if a in acts else None)
               for a in ("FAILOVER_API", "RESTART_DB")}
        rows.append({
            "run": run["label"],
            "condition": run["cond"],
            "actions": " > ".join(acts),
            "n_actions": len(acts),
            "invented_actions": "|".join(ev["unknown_actions"]),
            "missing_vocab_actions": "|".join(a for a in ACTIONS if a not in acts),
            "failover_after_restart": int(pos["FAILOVER_API"] is not None
                                          and pos["RESTART_DB"] is not None
                                          and pos["FAILOVER_API"] > pos["RESTART_DB"]),
            "ready": ev["ready"],
            "violated": "|".join(ev["violated"]),
            "constraint_recall": ev["constraint_recall"],
            "retries": fin["retries"],
            "first_attempt_error": fin["attempts"][0]["parse_error"],
            "accepted_reply_in_code_fence": int("```" in fin["attempts"][-1]["content"]),
        })
    return rows


def cost(runs):
    """F. Realised token and time cost, per condition."""
    per_call = []
    for run in runs:
        for m in generated(run):
            per_call.append({"run": run["label"], "condition": run["cond"],
                             "call": f"turn {m['turn_index']}",
                             "prompt_tokens": m["prompt_tokens"]})
        per_call.append({"run": run["label"], "condition": run["cond"],
                         "call": "final plan",
                         "prompt_tokens": run["d"]["meta"]["finalisation"]["attempts"][0]["prompt_tokens"]})
    rows = []
    full_mean = None
    for cond in reversed(CONDITIONS):
        g = [r for r in runs if r["cond"] == cond]
        real = [r["d"]["meta"]["realised"] for r in g]
        exp_tok = statistics.mean(x["experiment_total"]["prompt_tokens"] for x in real)
        if cond == "full":
            full_mean = exp_tok
        rows.append({
            "condition": cond,
            "mean_dialogue_prompt_tokens": round(statistics.mean(x["dialogue"]["prompt_tokens"] for x in real)),
            "mean_final_plan_prompt_tokens": round(statistics.mean(x["finalisation"]["prompt_tokens"] for x in real)),
            "mean_experiment_prompt_tokens": round(exp_tok),
            "share_of_full": round(exp_tok / full_mean, 3),
            "mean_completion_tokens": round(statistics.mean(x["experiment_total"]["completion_tokens"] for x in real)),
            "mean_seconds": round(statistics.mean(x["experiment_total"]["seconds"] for x in real), 1),
            "mean_constraint_recall": round(statistics.mean(
                r["d"]["meta"]["finalisation"]["evaluation"]["constraint_recall"] for r in g), 4),
        })
    return per_call, list(reversed(rows))


def judge(runs):
    """G. Judge verdicts beside the deterministic ones."""
    rows = []
    for run in runs:
        j = run["d"]["meta"]["judge"]
        ev = run["d"]["meta"]["finalisation"]["evaluation"]
        rows.append({
            "run": run["label"],
            "condition": run["cond"],
            "judge_score": j["score"],
            "judge_success": j["success"],
            "deterministic_success": ev["success"],
            "violated": "|".join(ev["violated"]),
            "reason_names_failover_order": int(bool(re.search(r"fail ?over", j["reason"].lower()))),
            "judge_reason": j["reason"],
        })
    return rows


# --------------------------------------------------------------------- output
def write_csv(name, rows):
    path = f"{OUT}/{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def md_table(rows, cols=None):
    cols = cols or list(rows[0].keys())
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join("" if r[c] is None else str(r[c]) for c in cols) + " |"
            for r in rows]
    return "\n".join(out)


# -------------------------------------------------------------------- figures
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
SERIES = {"recency-4": "#2a78d6", "recency-8": "#eb6834",
          "recency-12": "#1baf7a", "full": "#eda100"}
CRITICAL = "#d03b3b"


def _style(plt):
    plt.rcParams.update({
        "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": AXIS,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    })


def fig_constraints(plt, matrix_rows, path):
    """Violations per run and rule, with the rule's source visibility marked."""
    from matplotlib.patches import Rectangle
    n_r, n_c = len(matrix_rows), len(CIDS)
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    for i, row in enumerate(matrix_rows):
        for j, c in enumerate(CIDS):
            v, s = row[c], row[f"{c}_source_visible"]
            ax.add_patch(Rectangle((j + 0.04, i + 0.06), 0.92, 0.88,
                                   facecolor=CRITICAL if v else "#f0efec",
                                   edgecolor=INK2 if s else "none",
                                   linewidth=1.6 if s else 0))
            ax.text(j + 0.5, i + 0.5, "✕" if v else "✓",
                    ha="center", va="center", fontsize=10,
                    color="#ffffff" if v else MUTED, fontweight="bold" if v else "normal")
    for k in (3, 6, 9):
        ax.axhline(k, color=AXIS, linewidth=1)
    ax.set_xlim(0, n_c)
    ax.set_ylim(n_r, 0)
    ax.set_xticks([j + 0.5 for j in range(n_c)])
    ax.set_xticklabels([f"{c.id}\nturn {c.stated_at_turn}" for c in CONSTRAINTS])
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(n_r)])
    ax.set_yticklabels([r["run"] for r in matrix_rows])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.text(0.02, 0.975, "Which rules each final plan broke", fontsize=11,
             fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.035,
             "✕ red = rule violated    ✓ grey = rule kept    "
             "outlined = the message that stated the rule was still in the\n"
             "final-plan context. Column label gives the seeded turn that stated the rule.",
             fontsize=8, color=INK2, va="bottom")
    fig.subplots_adjust(left=0.2, right=0.98, top=0.86, bottom=0.12)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_prompt_tokens(plt, per_call, path):
    """Prompt tokens per model call: the window caps growth, full history does not."""
    calls = [f"turn {t}" for t in range(SEEDED, 16)] + ["final plan"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for cond in CONDITIONS:
        runs = sorted({r["run"] for r in per_call if r["condition"] == cond})
        series = [[next(r["prompt_tokens"] for r in per_call
                        if r["run"] == run and r["call"] == c) for c in calls] for run in runs]
        mean = [statistics.mean(col) for col in zip(*series)]
        ax.plot(range(len(calls)), mean, color=SERIES[cond], linewidth=2,
                marker="o", markersize=4, label=cond)
        ax.annotate(cond, (len(calls) - 1, mean[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=INK2)
    ax.set_xticks(range(len(calls)))
    ax.set_xticklabels([c.replace("turn ", "") for c in calls[:-1]] + ["plan"])
    ax.set_xlabel("model call (dialogue turn index, then the final-plan request)")
    ax.set_ylabel("prompt tokens")
    ax.set_ylim(0, None)
    ax.set_xlim(-0.3, len(calls) - 1 + 1.6)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)
    ax.set_title("Prompt size per model call (mean of 3 repeats)", loc="left",
                 fontsize=11, fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    runs = load_runs()

    traj, traj_sum = trajectories(runs)
    r4_pairs = pairwise_divergence(runs, "recency-4")
    matrix, matrix_by_cond, xtab = constraint_matrix(runs)
    distinct = distinct_runs(runs, traj)
    _, _, xtab_distinct = constraint_matrix(distinct)
    xtab_rows = [{"sample": f"all runs ({len(runs)})", **xtab},
                 {"sample": f"distinct trajectories ({len(distinct)}: "
                            + ", ".join(r["label"] for r in distinct) + ")",
                  **xtab_distinct}]
    mentions, mentions_per_run = concept_mentions(runs)
    plan_rows = plans(runs)
    per_call, cost_rows = cost(runs)
    judge_rows = judge(runs)

    for name, rows in [("trajectories", traj), ("trajectory_summary", traj_sum),
                       ("recency4_divergence", r4_pairs),
                       ("constraint_matrix", matrix), ("violations_by_condition", matrix_by_cond),
                       ("violation_vs_source_visible", xtab_rows),
                       ("concept_mentions_by_turn",
                        [{k: v for k, v in r.items() if k != "content_lower"} for r in mentions]),
                       ("concept_mentions_by_run", mentions_per_run),
                       ("plans", plan_rows), ("prompt_tokens_per_call", per_call),
                       ("cost_by_condition", cost_rows), ("judge", judge_rows)]:
        write_csv(name, rows)

    sections = [
        ("A. Trajectories: are the repeats independent?", md_table(traj_sum)),
        ("A2. First generated turn differing from full_r1", md_table(
            traj, ["run", "dialogue_hash", "plan_text_hash", "plan_actions_hash",
                   "first_turn_differing_from_full_r1"])),
        ("A3. recency-4 repeats: first differing turn", md_table(r4_pairs)),
        ("B. Violations by condition", md_table(matrix_by_cond)),
        ("C. Rule broken vs its source message in the final-plan context "
         "(cells = runs x 7 rules)", md_table(xtab_rows)),
        ("D. Concept mentions in the generated dialogue (keyword heuristic)",
         md_table(mentions_per_run)),
        ("E. Final plans", md_table(plan_rows)),
        ("F. Cost by condition", md_table(cost_rows)),
        ("G. Judge vs deterministic evaluator", md_table(judge_rows)),
    ]
    with open(f"{OUT}/tables.md", "w", encoding="utf-8") as fh:
        fh.write("# Compulsory analysis: generated tables\n\n"
                 f"Generated by `comp_analysis.py` from the transcripts frozen at `{TAG}`. "
                 "Do not edit by hand.\n")
        for title, body in sections:
            fh.write(f"\n## {title}\n\n{body}\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        _style(plt)
        fig_constraints(plt, matrix, f"{OUT}/fig_constraints.png")
        fig_prompt_tokens(plt, per_call, f"{OUT}/fig_prompt_tokens.png")
    except ImportError:
        print("matplotlib not installed; figures skipped")

    for title, body in sections:
        print(f"\n## {title}\n{body}")
    print(f"\nwrote {OUT}/")


if __name__ == "__main__":
    main()
