"""xray_build.py: build the Zombie Constraint X-ray from the repository's own
result files. Every rate is recomputed from the per-unit CSVs; every plan is
the raw `output` field of the matching JSON. No model calls.

    python xray_build.py            writes docs/xray/zombie_xray.html (static)
    from xray_build import build_data, render_page   (used by xray_server.py)
"""
import csv
import glob
import json
import math
import os
from collections import defaultdict

from lineage_bench import DOMAINS
from lineage_e16 import all_dialogues, corpus_hash
from lineage_e29 import ARMS, DESIGNS, all_e29_dialogues, context_block
from lineage_e29 import corpus_hash as e29_hash

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "docs", "xray", "index_template.html")
STATIC = os.path.join(HERE, "docs", "xray", "zombie_xray.html")

MODELS = ["gemma4:e4b", "llama3.2:3b", "qwen2.5:3b-instruct", "qwen2.5:7b-instruct",
          "aya-expanse:8b", "qwen2.5:14b-instruct"]
SIZES = {"gemma4:e4b": "~4B", "llama3.2:3b": "3B", "qwen2.5:3b-instruct": "3B",
         "qwen2.5:7b-instruct": "7B", "aya-expanse:8b": "8B", "qwen2.5:14b-instruct": "14B"}
E29_MODELS = ["llama3.2:3b", "qwen2.5:7b-instruct"]


def slug(s):
    return s.replace(".", "").replace(":", "-")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def _rows(pattern):
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, pattern))):
        rows += list(csv.DictReader(open(f, encoding="utf-8")))
    return rows


def _json(pattern):
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, pattern))):
        out += json.load(open(f, encoding="utf-8"))
    return out


def e18_ladder():
    """E17/E18 pin4 cells: per-unit inclusion and per-dialogue plans, six models."""
    units = defaultdict(dict)
    outputs = defaultdict(dict)
    for m in MODELS:
        rows = _rows(f"results/e17_{slug(m)}_v6_pin4_o*.csv")
        assert len(rows) == 384, (m, len(rows))
        for r in rows:
            units[(r["instance"], int(r["rotation"]), r["constraint"])][m] = r
        for d in _json(f"results/e17_{slug(m)}_v6_pin4_o*.json"):
            outputs[(d["instance"], d["rotation"])][m] = d["output"]
    agg = {}
    for m in MODELS:
        by = defaultdict(lambda: [0, 0])
        plans = []
        for per in units.values():
            r = per[m]
            by[r["status"]][1] += 1
            if r["included"] == "True":
                by[r["status"]][0] += 1
            plans.append(int(r["n_actions"]))
        agg[m] = {"size": SIZES[m], "mean_plan": round(sum(plans) / len(plans), 2)}
        for st, (k, n) in by.items():
            agg[m][st] = {"rate": round(k / n, 3), "k": k, "n": n, "ci": wilson(k, n)}
    dias = []
    for d in all_dialogues():
        inst, rot = d["instance"], d["rotation"]
        us = []
        for u in d["units"]:
            per = units[(inst.id, rot, u["constraint"])]
            us.append({"constraint": u["constraint"], "action": u["action"], "status": u["status"],
                       "included": {m: per[m]["included"] == "True" for m in MODELS}})
        dias.append({"instance": inst.id, "domain": inst.domain, "graph": inst.graph, "rotation": rot,
                     "verbs": dict(DOMAINS[inst.domain]["actions"]),
                     "turns": [{"speaker": s, "text": t, "tag": tag[0], "cid": tag[1]} for s, t, tag in d["dialogue"]],
                     "units": us, "plans": {m: outputs[(inst.id, rot)][m] for m in MODELS}})

    def split_score(dd):
        s = 0
        for u in dd["units"]:
            if u["status"] == "rejected":
                k = sum(u["included"].values())
                s = max(s, min(k, 6 - k))
        return s
    show = sorted([x for x in dias if any(u["status"] == "rejected" for u in x["units"])],
                  key=split_score, reverse=True)
    return agg, dias, [(x["instance"], x["rotation"]) for x in show[:6]]


def e29_summaries():
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "results", "e29_*_summary.json"))):
        e = json.load(open(path, encoding="utf-8"))
        v = e["verdict"]
        e["verdict_short"] = v.split(":")[0].split(" (")[0].lower()
        e["note"] = (f"{e['model']}, read by the rule declared before the first call: {v}. "
                     f"Under write-time delete the restatement moved relapse from "
                     f"{e['p']['delete|neutral']:.2f} to {e['p']['delete|restated']:.2f}; under full context "
                     f"the same line moved it by {e['delta']['full']:+.2f}.")
        out.append(e)
    if out:
        out[-1]["note"] += (" Stores are semantic ideals built from the scorer's tags, not the output of a "
                            "real extractor; paired bootstrap over dialogues, B = 2000; the read rule uses "
                            "only the within-design difference, so levels across designs are shown, not compared.")
        b = os.path.join(HERE, "results", "e29b_llama32-3b_summary.json")
        if os.path.exists(b):
            eb = json.load(open(b, encoding="utf-8"))
            out[-1]["note"] += (f" A follow-up (E29-B) ran the Mem0 paper's own extraction prompt for real on "
                                f"{eb['n']} of these dialogues with llama3.2:3b: it stored the proposed step at its "
                                f"proposal line in {eb['manip_prop']:.2f} of them, so that stage reads uninformative "
                                f"by its declared rule; descriptively, the rejected step mostly never entered the "
                                f"store at all, and a later restatement entered it as a fresh fact.")
    return out


def e29_dialogues():
    """The 96 E29 dialogues: turns per arm, the context block per design, and
    every recorded decider output, keyed by model."""
    recorded = defaultdict(dict)
    for m in E29_MODELS:
        for d in _json(f"results/e29_{slug(m)}_o*.json"):
            recorded[(d["instance"], d["rotation"], d["arm"], d["design"])][m] = d["output"]
    out = []
    for d in all_e29_dialogues():
        inst, rot = d["instance"], d["rotation"]
        rej = next(u for u in d["units"] if u["status"] == "rejected")
        verbs = dict(DOMAINS[inst.domain]["actions"])
        rec = {"instance": inst.id, "domain": inst.domain, "rotation": rot,
               "rejected_action": rej["action"], "phrase": verbs[rej["action"]],
               "vocab": list(inst.actions),
               "units": [{"constraint": u["constraint"], "action": u["action"], "status": u["status"]} for u in d["units"]],
               "arms": {}, "blocks": {}, "recorded": {}}
        for arm in ARMS:
            dia = d["arms"][arm]
            rec["arms"][arm] = [{"speaker": s, "text": t, "tag": tag[0], "cid": tag[1]} for s, t, tag in dia]
            rec["blocks"][arm] = {X: context_block(X, inst, dia) for X in DESIGNS}
            rec["recorded"][arm] = {X: recorded.get((inst.id, rot, arm, X), {}) for X in DESIGNS}
        out.append(rec)
    return out


def e29b_snapshots():
    out = {}
    for d in _json("results/e29b_llama32-3b_o*.json"):
        out[f"{d['instance']}|{d['rotation']}|{d['arm']}"] = {
            "lines": d["lines"], "snapshots": d["snapshots"], "events": d["events"],
            "final_store": d["final_store"], "decider_output": d["decider_output"], "phrase": d["phrase"]}
    return out


def build_data(live=False, live_models=None):
    agg, dias, showcase = e18_ladder()
    return {"corpus_hash": corpus_hash(), "e29_hash": e29_hash(), "models": MODELS, "agg": agg,
            "dialogues": dias, "showcase": showcase, "e29": e29_summaries(),
            "e29_dialogues": e29_dialogues(), "e29_models": E29_MODELS, "e29b": e29b_snapshots(),
            "live": {"models": live_models or []} if live else None}


def render_page(data):
    tpl = open(TEMPLATE, encoding="utf-8").read()
    blob = json.dumps(data).replace("</", "<\\/")
    body = tpl.replace("__DATA__", blob)
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "</head>\n<body>\n" + body + "\n</body>\n</html>\n")


if __name__ == "__main__":
    data = build_data(live=False)
    html = render_page(data)
    os.makedirs(os.path.dirname(STATIC), exist_ok=True)
    open(STATIC, "w", encoding="utf-8").write(html)
    print(f"wrote {STATIC} ({len(html):,} bytes); corpus {data['corpus_hash']}, e29 {data['e29_hash']}, "
          f"{len(data['e29_dialogues'])} E29 dialogues, {len(data['e29b'])} E29-B snapshot records")
