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


def _plan(text):
    """The recorded output as a plan object, or None if it does not parse."""
    if not isinstance(text, str):
        return None
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        return None
    try:
        o = json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return None
    return o if isinstance(o, dict) and isinstance(o.get("actions"), list) else None


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
                     "units": us, "plans": {m: _plan(outputs[(inst.id, rot)][m]) for m in MODELS}})

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
    return out


E29_CAVEAT = ("Stores are semantic ideals built from the scorer's tags, not the output of a real extractor. "
              "Paired bootstrap over dialogues, B = 2000. The read rule uses only the within-design difference, "
              "so levels across designs are shown, not compared.")


def e29b_note():
    b = os.path.join(HERE, "results", "e29b_llama32-3b_summary.json")
    if not os.path.exists(b):
        return ""
    eb = json.load(open(b, encoding="utf-8"))
    return (f"A follow-up, E29-B, ran the Mem0 paper's own extraction prompt for real on {eb['n']} of these "
            f"dialogues with llama3.2:3b. It stored the proposed step at its proposal line in {eb['manip_prop']:.2f} "
            f"of them, so that stage reads uninformative by its declared rule; descriptively, the rejected step "
            f"mostly never entered the store at all, and a later restatement entered it as a fresh fact.")


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
               "phrases": {a: verbs[a] for a in inst.actions},
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


def city_districts(dias):
    """One district per domain; tower heights are how often each step appeared in
    the recorded plans for that domain, over all dialogues and all six models."""
    out = []
    for dom in DOMAINS:
        actions = [a for a, _ in DOMAINS[dom]["actions"]]
        n, hits = 0, {a: 0 for a in actions}
        for d in dias:
            if d["domain"] != dom:
                continue
            for m in MODELS:
                p = d["plans"][m]
                if not p:
                    continue
                n += 1
                for a in p["actions"]:
                    if a in hits:
                        hits[a] += 1
        out.append({"domain": dom, "setting": DOMAINS[dom]["setting"], "actions": actions,
                    "verbs": dict(DOMAINS[dom]["actions"]),
                    "heights": {a: round(hits[a] / n, 3) if n else 0 for a in actions}, "plans": n})
    return out


def build_data(live=False, live_models=None):
    agg, dias, showcase = e18_ladder()
    return {"corpus_hash": corpus_hash(), "e29_hash": e29_hash(), "models": MODELS, "agg": agg,
            "dialogues": dias, "showcase": showcase, "e29": e29_summaries(), "city": city_districts(dias),
            "e29_caveat": E29_CAVEAT, "e29b_note": e29b_note(),
            "e29_dialogues": e29_dialogues(), "e29_models": E29_MODELS, "e29b": e29b_snapshots(),
            "live": {"models": live_models or []} if live else None}


INDEX_KEYS = ("instance", "domain", "rotation", "rejected_action", "phrase", "vocab", "phrases", "units")


def page_data(data):
    """What the page embeds: everything except the per-dialogue E29 blocks and
    recorded outputs, which the server serves on demand (/api/e29?i=)."""
    out = dict(data)
    out["e29_index"] = [{k: d[k] for k in INDEX_KEYS} for d in data.get("e29_dialogues", [])]
    out.pop("e29_dialogues", None)
    return out


def render_page(data):
    tpl = open(TEMPLATE, encoding="utf-8").read()
    blob = json.dumps(page_data(data)).replace("</", "<\\/")
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
