"""paper_fig_position.py: the E29-A figure -- the same revocation before and after the record.
Drawn from the committed summaries. Zero model calls.

One panel per model family. Each row joins the marker placed before the proposal text (left
colour) to the same marker placed after it (right colour). Field-style markers, which E29-T
placed after the record, are shown as single points: they fail even there.

    python paper_fig_position.py   -> docs/paper/fig7-position.svg and .png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = [("llama32-3b", "llama3.2:3b (Meta)"), ("qwen25-14b-instruct", "qwen2.5:14b (Alibaba)"),
          ("aya-expanse-8b", "aya-expanse:8b (Cohere)")]
PAIRS = [("[withdrawn]", "tag_prefix", "tag_suffix"), ("(withdrawn)", "paren_prefix", "paren_suffix")]
FIELDS = [("[is_active: false]", "is_active_false"), ("[invalid_at: …]", "invalid_at")]
BEFORE, AFTER, FIELD, SENT = "#C8461B", "#3A5F9E", "#7A5C99", "#0E7C6B"


def load(name):
    p = os.path.join(HERE, "results", name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def main():
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 3.9), sharey=True)
    labels = [p[0] for p in PAIRS] + [f[0] + " after, a field" for f in FIELDS]
    ys = list(range(len(labels)))[::-1]
    for ax, (slug, name) in zip(axes, MODELS):
        a = load(f"e29a_{slug}_summary.json")["p"]
        t = load(f"e29t_{slug}_summary.json")
        for y, (lab, pre, post) in zip(ys, PAIRS):
            ax.plot([a[post], a[pre]], [y, y], color="#B8C2CC", lw=2.2, zorder=1)
            ax.scatter([a[pre]], [y], s=70, color=BEFORE, zorder=3, label="marker before the proposal" if y == ys[0] else None)
            ax.scatter([a[post]], [y], s=70, color=AFTER, zorder=3, label="marker after the proposal" if y == ys[0] else None)
            ax.annotate(f"{a[pre]:.0%}", (a[pre], y), textcoords="offset points", xytext=(0, 8), ha="center",
                        fontsize=8, color=BEFORE)
            ax.annotate(f"{a[post]:.0%}", (a[post], y), textcoords="offset points", xytext=(0, 8), ha="center",
                        fontsize=8, color=AFTER)
        for y, (lab, key) in zip(ys[len(PAIRS):], FIELDS):
            if t:
                v = t["p"][key]
                ax.scatter([v], [y], s=70, marker="D", color=FIELD, zorder=3,
                           label="field after the proposal (E29-T)" if key == FIELDS[0][1] else None)
                ax.annotate(f"{v:.0%}", (v, y), textcoords="offset points", xytext=(0, 8), ha="center",
                            fontsize=8, color=FIELD)
            else:
                ax.text(0.02, y, "not run on this model", fontsize=8, color="#888", va="center")
        ax.axvline(a["sentence"], color=SENT, ls="--", lw=1.1)
        ax.text(a["sentence"], len(labels) - 0.45, " written as a sentence", fontsize=7.5, color=SENT, va="bottom")
        ax.set_xlim(0, 1.0)
        ax.set_ylim(-0.6, len(labels) - 0.1)
        ax.set_title(name, fontsize=10)
        ax.set_xlabel("share of plans that still include the rejected step")
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
        ax.grid(axis="x", alpha=0.25)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels(labels, fontsize=9)
    handles, labs = [], []
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in labs:
                handles.append(h)
                labs.append(l)
    fig.legend(handles, labs, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Where the revocation sits decides it: the same marker before and after the record "
                 "(E29-A, 96 dialogues per point)", fontsize=10.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    out = os.path.join(HERE, "docs", "paper", "fig7-position")
    fig.savefig(out + ".svg")
    fig.savefig(out + ".png", dpi=170)
    print("wrote", out + ".svg / .png")


if __name__ == "__main__":
    main()
