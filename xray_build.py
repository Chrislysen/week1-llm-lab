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

from lineage_bench import BENCH_DOMAINS, DOMAINS
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
E29_MODELS = ["llama3.2:3b", "qwen2.5:7b-instruct", "qwen2.5:14b-instruct", "gemma4:e4b"]


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


def e29c_note():
    """E29-C: the follow-up on the negative full-context restatement effect."""
    parts = []
    for slug_, name in (("llama32-3b", "llama3.2:3b"), ("qwen25-7b-instruct", "qwen2.5:7b-instruct")):
        b = os.path.join(HERE, "results", f"e29c_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        v = e["verdict"].split(" ")[0]
        parts.append(f"{name}: for-the-record {e['delta_ftr']:+.3f} [{e['ci_ftr'][0]:+.3f}, {e['ci_ftr'][1]:+.3f}], "
                     f"plain mention {e['delta_plain']:+.3f} [{e['ci_plain'][0]:+.3f}, {e['ci_plain'][1]:+.3f}], "
                     f"difference {e['diff']:+.3f} [{e['ci_diff'][0]:+.3f}, {e['ci_diff'][1]:+.3f}] — {v}")
    if not parts:
        return ""
    return ("A second follow-up, E29-C, asked why the restatement lowers enactment under full raw context. "
            "It re-ran the two E29 lines beside a plain late mention with no authorship claim "
            "(\"Just to note it, X came up earlier in this discussion\"), 96 dialogues, four arms, both deciders. "
            + " · ".join(parts) + ". On the course model the protection is the \"for the record, I did raise it\" register, "
            "which sends the decider back to the rejection; a plain mention does nothing. "
            "The stores never saw that register; they saw a fact.")


def e29d_note():
    """E29-D: the real write path with an operational extractor."""
    b = os.path.join(HERE, "results", "e29d_qwen25-7b-instruct_llama32-3b_summary.json")
    if not os.path.exists(b):
        return ""
    e = json.load(open(b, encoding="utf-8"))
    ref = e.get("e29_ref") or {}
    dl = ref.get("delete", {}).get("delta"); ad = ref.get("addonly", {}).get("delta")
    return (f"E29-D then ran the Mem0 write path for real with an extractor that stores operational facts "
            f"(qwen2.5:7b-instruct for extraction and Mem0's own update router, verbatim), on {e['n']} of these dialogues, "
            f"decider llama3.2:3b. The store held the proposed step in {e['w0']:.2f} of dialogues; the router deleted it on "
            f"rejection in {e['w1']:.2f}; the restatement raised enactment on the real store by {e['delta_real']:+.3f} "
            f"[{e['ci'][0]:+.3f}, {e['ci'][1]:+.3f}], between the oracle add-only ({ad:+.3f}) and delete ({dl:+.3f}) designs "
            f"on the same dialogues — {e['verdict']}.")


def e29n_note():
    """E29-N: the same experiment on a second corpus."""
    parts = []
    for slug_, name in (("llama32-3b", "llama3.2:3b"), ("qwen25-7b-instruct", "qwen2.5:7b-instruct"), ("qwen25-14b-instruct", "qwen2.5:14b-instruct")):
        b = os.path.join(HERE, "results", f"e29n_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        parts.append(f"{name}: delete DiD {e['did']['delete']:+.3f} [{e['ci_did']['delete'][0]:+.3f}, {e['ci_did']['delete'][1]:+.3f}], "
                     f"add-only {e['did']['addonly']:+.3f}, wiki {e['did']['wiki']:+.3f}, full-context Δ {e['delta']['full']:+.3f} — "
                     f"{e['verdict'].split(':')[0].lower()}")
    if not parts:
        return ""
    return ("E29-N repeated the experiment unchanged on a second corpus: six new domains (grid, airline, newsroom, water, "
            "checkout, telecom) and a second sentence bank, generated by the same rules, 96 dialogues, 768 calls per decider. "
            + " · ".join(parts) + ". The level of enactment moved a lot with the new wording (under full context the rejected step "
            "came back about 0.7 of the time against 0.3 before); the ordering across designs did not.")


def e29x_note():
    """E29-X: the two reviewer controls (rendering, tombstone)."""
    parts = []
    for slug_, name in (("llama32-3b", "llama3.2:3b"), ("qwen25-7b-instruct", "qwen2.5:7b-instruct"), ("qwen25-14b-instruct", "qwen2.5:14b-instruct")):
        b = os.path.join(HERE, "results", f"e29x_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        r1 = e.get("r1", {}).get("verdict", "?"); t1 = e.get("t1", {}).get("verdict", "?")
        parts.append(f"{name}: explicit-referent transcript neutral level {e['p']['full_explicit|neutral']:.3f} vs plain {e['p']['full|neutral']:.3f} "
                     f"({r1.lower()}); tombstone {e['p']['tombstone|restated']:.3f} / {e['p']['tombstone|neutral']:.3f}, "
                     f"DiD {e['did']['tombstone']:+.3f} [{e['ci_did']['tombstone'][0]:+.3f}, {e['ci_did']['tombstone'][1]:+.3f}] ({t1.lower()})")
    if not parts:
        return ""
    return ("E29-X ran two controls an outside adversarial review asked for: a transcript whose accept and reject replies name their "
            "referent as explicitly as the store does, to test whether the level gap between full context and add-only was rendering; "
            "and a tombstone design that keeps the rejected proposal flagged [withdrawn] instead of deleting it. "
            + " · ".join(parts) + ".")


DECIDERS = (("llama32-3b", "llama3.2:3b", "3B"), ("qwen25-7b-instruct", "qwen2.5:7b-instruct", "7B"),
            ("qwen25-14b-instruct", "qwen2.5:14b-instruct", "14B"), ("gemma4-e4b", "gemma4:e4b", "~4B"))


def figure_data():
    """Every E29-family summary, flattened for the design-by-decider figure:
    one row per (corpus, decider, design) with levels, Delta and DiD intervals."""
    rows = []
    for corpus, prefix in (("first corpus", "e29"), ("second corpus", "e29n")):
        for slug_, name, size in DECIDERS:
            b = os.path.join(HERE, "results", f"{prefix}_{slug_}_summary.json")
            if not os.path.exists(b):
                continue
            e = json.load(open(b, encoding="utf-8"))
            for X in ("full", "delete", "addonly", "wiki"):
                rows.append({"corpus": corpus, "decider": name, "size": size, "design": X,
                             "restated": e["p"][f"{X}|restated"], "neutral": e["p"][f"{X}|neutral"],
                             "delta": e["delta"][X], "ci_delta": e["ci_delta"][X],
                             "did": e["did"][X], "ci_did": e["ci_did"][X], "n": e["n_complete"],
                             "verdict": e["verdict"].split(":")[0]})
    for slug_, name, size in DECIDERS:
        b = os.path.join(HERE, "results", f"e29x_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        for X in ("full_explicit", "tombstone"):
            rows.append({"corpus": "first corpus (controls)", "decider": name, "size": size, "design": X,
                         "restated": e["p"][f"{X}|restated"], "neutral": e["p"][f"{X}|neutral"],
                         "delta": e["delta"][X], "ci_delta": e["ci_delta"][X],
                         "did": e["did"][X], "ci_did": e["ci_did"][X], "n": e["n_complete"], "verdict": ""})
    for slug_, name, size in DECIDERS:
        b = os.path.join(HERE, "results", f"e29e_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        for X in ("addonly_meta", "addonly_flag"):
            rows.append({"corpus": "first corpus (encoding)", "decider": name, "size": size, "design": X,
                         "restated": e["p"][f"{X}|restated"], "neutral": e["p"][f"{X}|neutral"],
                         "delta": e["delta"][X], "ci_delta": e["ci_delta"][X],
                         "did": e["did"][X], "ci_did": e["ci_did"][X], "n": e["n_complete"], "verdict": ""})
    return rows


def e29e_note():
    """E29-E: the encoding isolation."""
    parts = []
    for slug_, name in (("llama32-3b", "llama3.2:3b"), ("qwen25-7b-instruct", "qwen2.5:7b-instruct"), ("qwen25-14b-instruct", "qwen2.5:14b-instruct")):
        b = os.path.join(HERE, "results", f"e29e_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        parts.append(f"{name}: own line as a sentence {e['p']['addonly|neutral']:.3f}, own line as status(X) = WITHDRAWN "
                     f"{e['p']['addonly_meta|neutral']:.3f}, as a [withdrawn] prefix {e['p']['addonly_flag|neutral']:.3f} "
                     f"(own-line effect {e['g']['fm']:+.3f} [{e['ci_g']['fm'][0]:+.3f}, {e['ci_g']['fm'][1]:+.3f}])")
    if not parts:
        return ""
    return ("E29-E then removed a confound the tombstone control had left behind, holding the store fixed and changing only how "
            "the rejection is written. Re-wording it from a sentence to a key-value assertion in the same position does nothing; "
            "collapsing it from its own line onto the proposal it negates does. Neutral arm, 96 dialogues: "
            + " · ".join(parts) + ". A retraction has to be its own record. Carried as an attribute of the record it "
            "negates — which is how every shipped soft-delete design encodes it — it is largely ignored.")


def e29s_note():
    """E29-S: the 2x2 that isolates the mechanism."""
    parts = []
    for slug_, name in (("llama32-3b", "llama3.2:3b"), ("qwen25-14b-instruct", "qwen2.5:14b-instruct")):
        b = os.path.join(HERE, "results", f"e29s_{slug_}_summary.json")
        if not os.path.exists(b):
            continue
        e = json.load(open(b, encoding="utf-8"))
        p_ = e["p"]
        parts.append(f"{name}: own item {p_['addonly|neutral']:.3f} as a sentence and {p_['addonly_meta|neutral']:.3f} as status(X) = WITHDRAWN; "
                     f"merged into the proposal {p_['addonly_merged|neutral']:.3f} as a sentence but {p_['addonly_flag|neutral']:.3f} as a [withdrawn] prefix")
    if not parts:
        return ""
    return ("E29-S then split the two things that collapse confounded, with a 2x2 whose merged-sentence cell is byte-identical "
            "text to the protective cell (one newline and bullet become a space). Neither merging a sentence nor re-wording "
            "within its own item changes anything; only doing both does. Neutral arm, 96 dialogues: " + " · ".join(parts)
            + ". A retraction is ignored when it is a verb-less attribute of the record it retracts, which is how every shipped "
            "soft-delete design encodes revocation.")


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
    for dom in BENCH_DOMAINS:
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
            "e29_caveat": E29_CAVEAT, "e29b_note": e29b_note(), "e29c_note": e29c_note(), "e29d_note": e29d_note(), "e29n_note": e29n_note(), "e29x_note": e29x_note(), "e29e_note": e29e_note(), "e29s_note": e29s_note(), "figure": figure_data(),
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


CITY_TEMPLATE = os.path.join(HERE, "docs", "xray", "city_template.html")


def render_city_page(data):
    """The full-screen player (served at /city)."""
    tpl = open(CITY_TEMPLATE, encoding="utf-8").read()
    blob = json.dumps(page_data(data)).replace("</", "<\\/")
    body = tpl.replace("__DATA__", blob)
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "</head>\n<body>\n" + body + "\n</body>\n</html>\n")


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
