"""paper_fig.py: Figure 1 for the draft, from the same summaries the report
reads. Zero model calls.

    python paper_fig.py      -> docs/paper/fig1-delta-by-design.svg and .png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from xray_build import figure_data

HERE = os.path.dirname(os.path.abspath(__file__))
COL = {"full": "#7D8A97", "delete": "#C8461B", "addonly": "#3A5F9E", "wiki": "#0E7C6B",
       "full_explicit": "#9AA8B5", "tombstone": "#B8781E"}
NAME = {"full": "full raw context", "delete": "write-time delete", "addonly": "add-only",
        "wiki": "merge-in-place page", "full_explicit": "explicit-referent transcript (control)",
        "tombstone": "tombstone, flagged withdrawn (control)"}
ORDER = ["full", "delete", "addonly", "wiki", "full_explicit", "tombstone"]
DECIDERS = ["llama3.2:3b", "qwen2.5:7b-instruct", "qwen2.5:14b-instruct", "gemma4:e4b"]
GROUPS = ["first corpus", "second corpus", "first corpus (controls)"]


def main():
    rows = figure_data()
    lines = []
    for g in GROUPS:
        present = [m for m in DECIDERS if any(r["corpus"] == g and r["decider"] == m for r in rows)]
        if not present:
            continue
        lines.append(("group", g, None))
        for m in present:
            rs = sorted([r for r in rows if r["corpus"] == g and r["decider"] == m], key=lambda r: ORDER.index(r["design"]))
            lines.append(("row", m, rs))
    sub, gap, grp = 1.0, 0.8, 1.6
    height = sum(grp if k == "group" else len(rs) * sub + gap for k, _, rs in lines)
    fig, ax = plt.subplots(figsize=(8.6, 0.24 * height + 1.2))
    y = 0.0
    yticks, ylabels = [], []
    ax.axvspan(-0.15, 0.15, color="#CFD6DD", alpha=0.35, lw=0)
    ax.axvline(0, color="#16212B", lw=1.1)
    seen = set()
    for kind, label, rs in lines:
        if kind == "group":
            ax.text(-0.36, -(y + 0.9), label.upper(), fontsize=8.5, fontweight="bold", va="center", ha="left", color="#16212B")
            y += grp
            continue
        cy0 = y + len(rs) * sub / 2
        yticks.append(-cy0); ylabels.append(f"{label}  ({rs[0]['size']})")
        for i, r in enumerate(rs):
            cy = -(y + i * sub + sub / 2)
            lo, hi = r["ci_delta"]
            ax.plot([lo, hi], [cy, cy], color=COL[r["design"]], lw=2.0, solid_capstyle="round", zorder=2)
            ax.plot([r["delta"]], [cy], marker="o", ms=5.5, color=COL[r["design"]],
                    mfc="white" if r["design"] == "full_explicit" else COL[r["design"]], mec=COL[r["design"]], zorder=3,
                    label=NAME[r["design"]] if r["design"] not in seen else None)
            seen.add(r["design"])
            ax.text(hi + 0.012, cy, f"{r['delta']:+.2f}", fontsize=7.2, va="center", color="#5B6B7A")
        y += len(rs) * sub + gap
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=8.5)
    ax.set_xlim(-0.36, 0.68); ax.set_ylim(-(y + 0.2), 0.4)
    ax.set_xlabel("Δ = P(rejected step in plan | restated) − P(… | neutral), 95% paired-bootstrap interval", fontsize=8.5)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0); ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="x", color="#E3E8ED", lw=0.8, zorder=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), fontsize=7.5, frameon=False, ncol=3)
    fig.tight_layout()
    out = os.path.join(HERE, "docs", "paper", "fig1-delta-by-design")
    fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=200)
    print("wrote", out + ".svg / .png", f"({len(rows)} marks)")


if __name__ == "__main__":
    main()
