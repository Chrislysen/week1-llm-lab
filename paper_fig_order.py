"""paper_fig_order.py: the E29-O figure -- the same revocation before and after the record.
Drawn from the committed summaries. Zero model calls.

One panel per decider. Each row is a pre/post pair: the dot on the left is the marker before
the record, the dot on the right after it, joined by a line, with the undecided-step ceiling
(`open`) and the sentence reference drawn as vertical guides.

    python paper_fig_order.py   -> docs/paper/fig8-order.svg and .png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DECIDERS = [("llama32-3b", "llama3.2:3b"), ("qwen25-14b-instruct", "qwen2.5:14b"), ("aya-expanse-8b", "aya-expanse:8b")]
ROWS = [("withdrawn", "[withdrawn]"), ("later", "[subsequently withdrawn]"), ("label", "[withdrawn: X]"),
        ("clause", "[B rejected the proposal]"), ("named", "[B rejected the proposal to X]"),
        ("xfirst", "[withdrawn], step name first"), ("field", "[status: withdrawn]"),
        ("first", "[withdrawn], record first in list")]
PRE, POST = "#C8461B", "#3A5F9E"


def cells(kind):
    if kind == "first":
        return "first_pre", "first_post"
    return f"{kind}_pre", f"{kind}_post"


def main():
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6), sharey=True)
    ys = list(range(len(ROWS)))[::-1]
    for ax, (slug, name) in zip(axes, DECIDERS):
        p = os.path.join(HERE, "results", f"e29o_{slug}_summary.json")
        if not os.path.exists(p):
            ax.set_title(f"{name}: not run")
            ax.axis("off")
            continue
        s = json.load(open(p, encoding="utf-8"))
        P = s["p"]
        for y, (kind, label) in zip(ys, ROWS):
            a, b = cells(kind)
            ax.plot([P[a], P[b]], [y, y], color="#9AA8B5", lw=1.5, zorder=1)
            ax.scatter([P[a]], [y], color=PRE, s=46, zorder=2, label="marker before the record" if y == ys[0] else None)
            ax.scatter([P[b]], [y], color=POST, s=46, zorder=2, label="marker after the record" if y == ys[0] else None)
        ax.axvline(P["open"], color="#555", ls=":", lw=1)
        ax.axvline(P["sentence_short"], color="#0E7C6B", ls="--", lw=1)
        ax.text(P["open"], len(ROWS) - 0.4, " no rejection", fontsize=7.5, color="#555", va="bottom")
        ax.text(P["sentence_short"], len(ROWS) - 0.4, " sentence", fontsize=7.5, color="#0E7C6B", va="bottom", ha="right")
        ax.set_xlim(0, 1.02)
        ax.set_title(f"{name}  (n = {s['n']}; {s['gate'].lower()}; account: {s['account']})", fontsize=9)
        ax.set_xlabel("rejected step planned")
        ax.grid(axis="x", alpha=0.25)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([label for _, label in ROWS], fontsize=8.5)
    axes[0].legend(loc="lower right", fontsize=7.5, frameon=False)
    fig.suptitle("E29-O: the same revocation before and after the record", fontsize=11)
    fig.tight_layout()
    out = os.path.join(HERE, "docs", "paper", "fig8-order")
    fig.savefig(out + ".svg")
    fig.savefig(out + ".png", dpi=160)
    print("wrote", out + ".svg / .png")


if __name__ == "__main__":
    main()
