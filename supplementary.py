"""supplementary.py: the frozen experiment again, with independent repeats.

At temperature 0 the frozen repeats were copies (see docs/COMP-ANALYSIS.md).
This reruns the same pipeline with both agents at temperature 0.7, 5 repeats
per condition, plus recency-0 as a floor control. The declaration, with the
predictions, is docs/SUPPLEMENTARY-T07.md and was committed before any run.

The ONLY change is the agents' temperature. The runs go through the unchanged
run_incident.main; the two agents it uses are swapped for copies at 0.7.
The judge stays at temperature 0, as in the frozen runs.

    python supplementary.py --condition recency-4   # one condition, resumable
    python supplementary.py --all                   # every condition (~13 min)
    python supplementary.py --summarise             # tables + prediction checks

Resumable: a run whose transcript already exists is skipped, never redone.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import statistics
from dataclasses import replace

import experiment
import run_incident
from scenario import AGENT_A, AGENT_B, INCIDENT

TEMPERATURE = 0.7
REPEATS = 5
CONDITIONS = {"recency-0": 0, "recency-4": 4, "recency-8": 8,
              "recency-12": 12, "full": None}
OUT_DIR = "transcripts/supp_t07"
RESULTS_DIR = "results/supp_t07"
CIDS = [c.id for c in INCIDENT.constraints]

# The one manipulation: run_incident.main reads these two names at call time.
run_incident.AGENT_A = replace(AGENT_A, temperature=TEMPERATURE)
run_incident.AGENT_B = replace(AGENT_B, temperature=TEMPERATURE)


def execute(condition, repeat):
    """One run, exactly as experiment.execute does it, into its own folder."""
    out = f"{OUT_DIR}/{condition}_r{repeat}.json"
    if os.path.exists(out):
        return out, False
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_incident.main(mock=False, turns=experiment.TURNS, out=out,
                          window=CONDITIONS[condition], host="http://localhost:11434")
    with open(out.replace(".json", ".log"), "w", encoding="utf-8") as fh:
        fh.write(buf.getvalue())
    return out, True


def run(conditions):
    os.makedirs(OUT_DIR, exist_ok=True)
    for condition in conditions:
        for r in range(1, REPEATS + 1):
            path, fresh = execute(condition, r)
            row = experiment.row_from_transcript(path, condition, CONDITIONS[condition], r)
            print(f"  {condition:<11} r{r}  {'ran ' if fresh else 'kept'}  "
                  f"recall {row['constraint_recall']:<6} violated {row['violated'] or '-':<12} "
                  f"judge {row['judge_score']}  {row['seconds']}s")


def load(condition, repeat):
    path = f"{OUT_DIR}/{condition}_r{repeat}.json"
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    # The saved agents must show the manipulation actually happened.
    assert all(a["temperature"] == TEMPERATURE for a in data["agents"]), path
    return path, data


def summarise():
    rows, per_cond = [], []
    for condition in CONDITIONS:
        g = []
        for r in range(1, REPEATS + 1):
            path, data = load(condition, r)
            row = experiment.row_from_transcript(path, condition, CONDITIONS[condition], r)
            ev = data["meta"]["finalisation"]["evaluation"]
            row["dialogue_hash"] = hashlib.sha1("\n".join(
                m["content"] for m in data["messages"][6:]).encode()).hexdigest()[:8]
            row["ready"] = ev["ready"]
            row["actions"] = " > ".join(ev["actions"])
            g.append(row)
        rows += g
        recall = [x["constraint_recall"] for x in g]
        per_cond.append({
            "condition": condition,
            "n": len(g),
            "distinct_dialogues": len({x["dialogue_hash"] for x in g}),
            "mean_recall": round(statistics.mean(recall), 4),
            "sd_recall": round(statistics.stdev(recall), 4),
            "min_recall": min(recall),
            "max_recall": max(recall),
            "success": f"{sum(x['deterministic_success'] for x in g)}/{len(g)}",
            "parsed": f"{sum(x['parse_success'] for x in g)}/{len(g)}",
            **{c: f"{sum(c in x['violated'].split('|') for x in g)}/{len(g)}" for c in CIDS},
            "plans_with_invented_actions": f"{sum(x['unknown_actions'] > 0 for x in g)}/{len(g)}",
            "ready_true": f"{sum(x['ready'] for x in g)}/{len(g)}",
            "judge_scores": " ".join(str(x["judge_score"]) for x in g),
            "mean_prompt_tokens": round(statistics.mean(x["prompt_tokens"] for x in g)),
        })

    cols = experiment.COLUMNS + ["dialogue_hash", "ready", "actions"]
    experiment.write_csv(f"{RESULTS_DIR}/runs.csv", rows, cols)
    experiment.write_csv(f"{RESULTS_DIR}/summary.csv", per_cond, list(per_cond[0].keys()))

    by = {s["condition"]: s for s in per_cond}
    count = lambda cond, cid: sum(cid in x["violated"].split("|")
                                  for x in rows if x["condition"] == cond)
    early = lambda cond: sum(("C1" in x["violated"].split("|") or "C2" in x["violated"].split("|"))
                             for x in rows if x["condition"] == cond)
    checks = [
        ("P1", "at least 4 of 5 dialogues distinct in every condition",
         all(s["distinct_dialogues"] >= 4 for s in per_cond),
         ", ".join(f"{s['condition']} {s['distinct_dialogues']}" for s in per_cond)),
        ("P2", "C5 broken in at least 3 of 5 full-history runs",
         count("full", "C5") >= 3, f"full C5 {count('full', 'C5')}/5"),
        ("P3", "C1 or C2 broken in more recency-4 runs than full",
         early("recency-4") > early("full"),
         f"recency-4 {early('recency-4')}/5 vs full {early('full')}/5"),
        ("P4", "recency-0 mean recall below full",
         by["recency-0"]["mean_recall"] < by["full"]["mean_recall"],
         f"recency-0 {by['recency-0']['mean_recall']} vs full {by['full']['mean_recall']}"),
    ]
    experiment.write_csv(f"{RESULTS_DIR}/predictions.csv",
                         [{"id": i, "prediction": p, "holds": h, "observed": o}
                          for i, p, h, o in checks], ["id", "prediction", "holds", "observed"])

    figure(rows, f"{RESULTS_DIR}/fig_recall_t0_vs_t07.png")

    print("=== per-condition summary ===")
    experiment.show(per_cond, list(per_cond[0].keys()))
    print("\n=== declared predictions ===")
    for i, p, h, o in checks:
        print(f"  {i} {'HOLDS ' if h else 'FAILS '} {p}  ({o})")
    print(f"\nwrote {RESULTS_DIR}/")


def figure(rows, path):
    """Recall of every run: frozen (temperature 0) beside supplementary (0.7)."""
    import csv
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frozen = []
    for name in ("runs.csv", "ceiling.csv"):
        with open(f"results/{name}", newline="") as fh:
            frozen += [(r["condition"], float(r["constraint_recall"]))
                       for r in csv.DictReader(fh)]
    supp = [(r["condition"], r["constraint_recall"]) for r in rows]

    ink, ink2, muted, grid, surface = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
    series = [("frozen, temperature 0 (3 runs; mostly identical copies)", frozen, "#2a78d6", -0.17),
              ("supplementary, temperature 0.7 (5 independent runs)", supp, "#eb6834", 0.17)]
    plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
                         "font.size": 9, "text.color": ink, "axes.labelcolor": ink2,
                         "xtick.color": muted, "ytick.color": muted, "axes.edgecolor": "#c3c2b7"})
    fig, ax = plt.subplots(figsize=(7.2, 4.0), facecolor=surface)
    ax.set_facecolor(surface)
    conds = list(CONDITIONS)
    for label, data, color, dx in series:
        for i, cond in enumerate(conds):
            vals = [v for c, v in data if c == cond]
            if not vals:
                continue
            # Stack repeated values sideways so identical runs stay countable.
            seen = {}
            for v in vals:
                k = seen.get(v, 0)
                seen[v] = k + 1
                ax.scatter(i + dx + (k - 1) * 0.045, v, s=34, color=color,
                           edgecolors=surface, linewidths=1.2, zorder=3)
            m = statistics.mean(vals)
            ax.plot([i + dx - 0.11, i + dx + 0.11], [m, m], color=color, linewidth=2.5, zorder=4)
        ax.scatter([], [], s=34, color=color, label=label)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels(["recency-0\n(no context)", "recency-4", "recency-8", "recency-12",
                        "full history"])
    ax.set_ylabel("constraint recall (bar = mean)")
    ax.set_ylim(-0.04, 1.06)
    ax.grid(axis="y", color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    ax.set_title("Recall per run: the frozen ordering does not survive independent repeats",
                 loc="left", fontsize=11, fontweight="bold", color=ink)
    fig.text(0.01, 0.01, "recall 0.0 = plan never parsed (recency-4 r2). Frozen runs had "
             "no recency-0 condition.", fontsize=7.5, color=ink2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=200, facecolor=surface)
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--condition", choices=list(CONDITIONS))
    p.add_argument("--all", action="store_true")
    p.add_argument("--summarise", action="store_true")
    a = p.parse_args()
    if a.condition or a.all:
        run([a.condition] if a.condition else list(CONDITIONS))
    if a.summarise:
        summarise()
