"""paper_fig_fix.py: the E29-M figure -- one appended sentence against the tag.
Drawn from the committed summaries and per-call CSVs. Zero model calls.

    python paper_fig_fix.py   -> docs/paper/fig6-fix.svg and .png
"""
import csv
import json
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lineage_e29m import CELLS

HERE = os.path.dirname(os.path.abspath(__file__))
DECIDERS = [("llama32-3b", "llama3.2:3b"), ("qwen25-14b-instruct", "qwen2.5:14b-instruct")]
LABEL = {"sentence": "- B rejected the proposal to X; ...   (control)",
         "is_active_false": "- A proposed to X. [is_active: false]",
         "invalid_at": "- A proposed to X. [invalid_at: ...]",
         "rewrite": "fix: field removed + \"The proposal to X was withdrawn.\"",
         "annotate_is_active": "fix: [is_active: false] kept + that sentence",
         "annotate_invalid_at": "fix: [invalid_at: ...] kept + that sentence"}
COL = {"control": "#3A5F9E", "anchor": "#C8461B", "FIXED": "#0E7C6B", "PARTIAL": "#6BAF9F", "NOT FIXED": "#9AA8B5",
       "UNTESTABLE": "#9AA8B5"}


def proposed_range(slug):
    rows = list(csv.DictReader(open(os.path.join(HERE, "results", f"e29m_{slug}_r0.csv"), encoding="utf-8")))
    v = [statistics.mean(r["included"] == "True" for r in rows
                         if r["design"] == c and r["status"] == "proposed" and r["parsed"] == "True") for c in CELLS]
    return min(v), max(v)


def main():
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.3), sharey=True)
    ys = list(range(len(CELLS)))[::-1]
    for ax, (slug, name) in zip(axes, DECIDERS):
        s = json.load(open(os.path.join(HERE, "results", f"e29m_{slug}_summary.json"), encoding="utf-8"))
        lo, hi = proposed_range(slug)
        ax.axvspan(lo, hi, color="#E3E8ED", lw=0, zorder=0)
        for y, c in zip(ys, CELLS):
            p = s["p"][c]
            if c == "sentence":
                cls, tag = "control", ""
            elif c in ("is_active_false", "invalid_at"):
                cls, tag = "anchor", ""
            else:
                key = next(k for k in s["fixes"] if k.startswith(c + " vs"))
                cls = s["fixes"][key]["class"]
                tag = "  " + cls.lower()
            ax.barh(y, p, color=COL[cls], height=0.62, zorder=2)
            ax.text(p + 0.012, y, f"{p:.3f}{tag}", va="center", fontsize=8, color="#16212B")
        ax.set_xlim(0, 1.18)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_title(f"{name}   (rewrite: {s['verdict']})", fontsize=10)
        ax.grid(axis="x", color="#E3E8ED", lw=0.8, zorder=0)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_xlabel("P(the rejected step is in the plan)", fontsize=8.5)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([LABEL[c] for c in CELLS], fontsize=8.5, family="monospace")
    fig.suptitle("The fix: one appended sentence brings the rejected step most of the way back out of the plan",
                 fontsize=11, y=0.98)
    fig.text(0.5, 0.01, "E29-M, neutral arm, n = 96 dialogues per bar. Shaded band: a step that was proposed and "
             "never decided. Classes by the declared rule (FIXED / PARTIAL against the sentence control).",
             ha="center", fontsize=8, color="#5B6B7A")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    out = os.path.join(HERE, "docs", "paper", "fig6-fix")
    fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=200)
    print("wrote", out + ".svg / .png")


if __name__ == "__main__":
    main()
