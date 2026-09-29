"""paper_fig_idioms.py: Figure 5 for the draft -- E29-T, the revocation idioms
shipped systems use, from the committed summaries and per-call CSVs. Zero
model calls.

    python paper_fig_idioms.py   -> docs/paper/fig5-idioms.svg and .png
"""
import csv
import json
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lineage_e29t import IDIOMS

HERE = os.path.dirname(os.path.abspath(__file__))
DECIDERS = [("llama32-3b", "llama3.2:3b"), ("qwen25-14b-instruct", "qwen2.5:14b-instruct")]
LABEL = {"sentence": "- B rejected the proposal to X; ...   (control)",
         "withdrawn_prefix": "- [withdrawn] A proposed to X.",
         "withdrawn_suffix": "- A proposed to X. (withdrawn)",
         "status_revoked": "- A proposed to X. [status: revoked]",
         "is_active_false": "- A proposed to X. [is_active: false]",
         "invalid_at": "- A proposed to X. [invalid_at: 2026-09-12 10:04]",
         "strikethrough": "- ~~A proposed to X.~~   (strikethrough)"}
COL = {"FAILS": "#C8461B", "UNCLEAR": "#9AA8B5", "HONOURED": "#0E7C6B", "control": "#3A5F9E"}


def proposed_range(slug):
    """Inclusion of a step that was proposed and never decided, per idiom cell."""
    rows = list(csv.DictReader(open(os.path.join(HERE, "results", f"e29t_{slug}_r0.csv"), encoding="utf-8")))
    v = [statistics.mean(r["included"] == "True" for r in rows
                         if r["design"] == i and r["status"] == "proposed" and r["parsed"] == "True") for i in IDIOMS]
    return min(v), max(v)


def main():
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), sharey=True)
    ys = list(range(len(IDIOMS)))[::-1]
    for ax, (slug, name) in zip(axes, DECIDERS):
        s = json.load(open(os.path.join(HERE, "results", f"e29t_{slug}_summary.json"), encoding="utf-8"))
        lo, hi = proposed_range(slug)
        ax.axvspan(lo, hi, color="#E3E8ED", lw=0, zorder=0)
        for y, i in zip(ys, IDIOMS):
            p = s["p"][i]
            cls = "control" if i == "sentence" else s["class"][i]
            ax.barh(y, p, color=COL[cls], height=0.62, zorder=2)
            ax.text(p + 0.012, y, f"{p:.3f}" + ("" if cls == "control" else f"  {cls.lower()}"),
                    va="center", fontsize=8, color="#16212B")
        ax.set_xlim(0, 1.18)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_title(f"{name}   ({s['fails']} of 5 fail: {s['verdict']})", fontsize=10)
        ax.grid(axis="x", color="#E3E8ED", lw=0.8, zorder=0)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_xlabel("P(the rejected step is in the plan)", fontsize=8.5)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([LABEL[i] for i in IDIOMS], fontsize=8.5, family="monospace")
    fig.suptitle("The same rejection, written seven ways: the in-place fields leave the rejected step in the plan",
                 fontsize=11, y=0.98)
    fig.text(0.5, 0.01, "E29-T, neutral arm, n = 96 dialogues per bar; only the marked item changes. Shaded band: a step "
             "that was proposed and never decided (no rejection at all). Classes by the declared rule.",
             ha="center", fontsize=8, color="#5B6B7A")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    out = os.path.join(HERE, "docs", "paper", "fig5-idioms")
    fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=200)
    print("wrote", out + ".svg / .png")


if __name__ == "__main__":
    main()
