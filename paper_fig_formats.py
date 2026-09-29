"""paper_fig_formats.py: Figure 4 for the draft -- E29-S's 2x2 in four list
formats, from the committed summaries. Zero model calls.

    python paper_fig_formats.py   -> docs/paper/fig4-formats.svg and .png

Markdown is E29-S's own data (results/e29s_*_summary.json); JSON, XML and the
numbered list are E29-R (results/e29r_*_summary.json).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DECIDERS = [("llama3.2:3b", "llama32-3b", "llama3.2:3b (3B)"),
            ("qwen2.5:14b-instruct", "qwen25-14b-instruct", "qwen2.5:14b-instruct (14B)")]
FORMATS = [("markdown", "markdown list"), ("json", "JSON array"), ("xml", "XML items"), ("numbered", "numbered list")]
CELLS = [["addonly", "addonly_merged"], ["addonly_meta", "addonly_flag"]]   # rows: proposition, attribute
VMAX = 0.65


def panels(slug):
    s = json.load(open(os.path.join(HERE, "results", f"e29s_{slug}_summary.json"), encoding="utf-8"))
    out = {"markdown": s["p"]}
    r = json.load(open(os.path.join(HERE, "results", f"e29r_{slug}_summary.json"), encoding="utf-8"))
    for read in r["reads"]:
        out[read["format"]] = read["p"]
    return out


def main():
    fig, axes = plt.subplots(len(DECIDERS), len(FORMATS), figsize=(11.2, 6.1))
    cmap = plt.get_cmap("Oranges")
    for i, (_, slug, label) in enumerate(DECIDERS):
        ps = panels(slug)
        for j, (fmt, title) in enumerate(FORMATS):
            ax = axes[i][j]
            p = ps[fmt]
            grid = [[p[f"{X}|neutral"] for X in row] for row in CELLS]
            ax.imshow(grid, cmap=cmap, vmin=0, vmax=VMAX)
            for a in range(2):
                for b in range(2):
                    v = grid[a][b]
                    tag = (a, b) == (1, 1)
                    ax.text(b, a, f"{v:.3f}", ha="center", va="center", fontsize=11.5,
                            fontweight="bold" if tag else "normal",
                            color="white" if v > 0.42 else "#16212B")
            ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
            ax.set_xticklabels(["own item", "same item\nas the proposal"] if i == len(DECIDERS) - 1 else ["", ""],
                               fontsize=8.5)
            ax.set_yticklabels(["proposition\n(has a verb)", "attribute\n(no verb)"] if j == 0 else ["", ""], fontsize=8.5)
            ax.tick_params(length=0)
            for sp in ax.spines.values():
                sp.set_visible(False)
            if i == 0:
                ax.set_title(title + ("  (E29-S)" if fmt == "markdown" else "  (E29-R)"), fontsize=10, pad=8)
        axes[i][0].annotate(label, xy=(-0.62, 0.5), xycoords="axes fraction", rotation=90,
                            ha="center", va="center", fontsize=10, fontweight="bold", color="#16212B")
    fig.suptitle("The tag cell stands out in every list format: a revocation is ignored when it is "
                 "subordinate and verb-less", fontsize=11.5, y=0.99)
    fig.text(0.5, 0.012, "rejected-step inclusion, neutral arm, n = 96 dialogues per cell. Bottom right of each panel: "
             "the rejection as a verb-less tag on the proposal's item, [withdrawn] A proposed to X.",
             ha="center", fontsize=8.5, color="#5B6B7A")
    fig.tight_layout(rect=(0.03, 0.035, 1, 0.965))
    out = os.path.join(HERE, "docs", "paper", "fig4-formats")
    fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=200)
    print("wrote", out + ".svg / .png")


if __name__ == "__main__":
    main()
