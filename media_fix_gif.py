"""media_fix_gif.py: the animated explainer of the E29-M fix for the README.
Every number is read from results/e29m_*_summary.json. Zero model calls.

    python media_fix_gif.py   -> docs/media/fix.gif
"""
import json
import os
import shutil
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BG, FG, DIM = "#0d1117", "#e6edf3", "#7d8590"
TAG, FIX, BAR = "#f0883e", "#3fb950", "#58a6ff"
MODELS = [("llama32-3b", "llama3.2:3b"), ("qwen25-14b-instruct", "qwen2.5:14b")]
REC = "Operations Lead proposed to cycle the settlement engine."
SENT = "The proposal to cycle the settlement engine was withdrawn."
FPS = 10


def rates():
    out = {}
    for slug, name in MODELS:
        s = json.load(open(os.path.join(HERE, "results", f"e29m_{slug}_summary.json"), encoding="utf-8"))
        out[name] = (s["p"]["is_active_false"], s["p"]["annotate_is_active"], s["p"]["sentence"])
    return out


def frame(path, stage, t, R):
    """stage 0: the tag only; stage 1: the sentence appears and the bars fall."""
    fig = plt.figure(figsize=(9.6, 5.4), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 96); ax.set_ylim(0, 54); ax.axis("off")
    title = ("A revoked record, marked the way many memory systems mark it" if stage == 0
             else "Now append one plain sentence, and keep the field")
    ax.text(4, 49, title, color=FG, fontsize=15, weight="bold", va="center")
    ax.text(4, 43.5, "MEMORY SHOWN TO THE MODEL", color=DIM, fontsize=9, family="monospace")
    ax.text(4, 39.5, "- Safety Auditor asked for a backup before any restart.", color=DIM, fontsize=10.5, family="monospace")
    ax.text(4, 35.5, f"- {REC}", color=FG, fontsize=10.5, family="monospace")
    ax.text(4 + 0.875 * (len(REC) + 3), 35.5, "[is_active: false]", color=TAG, fontsize=10.5, family="monospace",
            weight="bold")
    if stage == 1:
        a = min(1.0, t / 0.6)
        ax.text(4, 31.5, f"- {SENT}", color=FIX, fontsize=10.5, family="monospace", weight="bold", alpha=a)
    ax.text(4, 25, "HOW OFTEN THE REJECTED STEP ENDS UP IN THE PLAN (96 dialogues)", color=DIM, fontsize=9,
            family="monospace")
    for i, (name, (tag, fixed, sent)) in enumerate(R.items()):
        y = 19 - i * 7.5
        if stage == 0:
            v = tag * min(1.0, t / 0.8)
        else:
            k = min(1.0, max(0.0, (t - 0.6) / 1.2))
            v = tag + (fixed - tag) * (k * k * (3 - 2 * k))
        ax.text(4, y, name, color=FG, fontsize=11, va="center")
        ax.add_patch(plt.Rectangle((22, y - 1.6), 60, 3.2, color="#21262d", lw=0))
        ax.add_patch(plt.Rectangle((22, y - 1.6), 60 * v, 3.2, color=TAG if stage == 0 else BAR, lw=0))
        ax.plot([22 + 60 * sent] * 2, [y - 2.2, y + 2.2], color=FIX, lw=2)
        ax.text(83.5, y, f"{v * 100:.0f} %", color=FG, fontsize=12, weight="bold", va="center")
    ax.text(4, 3.5, "Green tick: the same rejection written as its own sentence. The memory lines illustrate the setup; "
            "the rates are E29-M's recorded plans (pre-registered).", color=DIM, fontsize=8.2)
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


def main():
    R = rates()
    tmp = tempfile.mkdtemp()
    n = 0
    for stage, seconds in ((0, 4.0), (1, 5.0)):
        for i in range(int(seconds * FPS)):
            frame(os.path.join(tmp, f"f{n:04d}.png"), stage, i / FPS, R)
            n += 1
    out = os.path.join(HERE, "docs", "media", "fix.gif")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS),
                    "-i", os.path.join(tmp, "f%04d.png"), "-vf",
                    "split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none",
                    "-loop", "0", out], check=True)
    shutil.rmtree(tmp)
    print("wrote", out, f"({n} frames, {os.path.getsize(out) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
