"""Zero-model-call extraction of real E17/E18 pin4 data for the memory X-ray demo."""
import csv, glob, json, math, collections, sys
sys.path.insert(0, '.')
from lineage_e16 import all_dialogues, corpus_hash
from lineage_bench import DOMAINS

MODELS = ["gemma4:e4b", "llama3.2:3b", "qwen2.5:3b-instruct", "qwen2.5:7b-instruct", "aya-expanse:8b", "qwen2.5:14b-instruct"]
SIZES = {"gemma4:e4b": "~4B", "llama3.2:3b": "3B", "qwen2.5:3b-instruct": "3B", "qwen2.5:7b-instruct": "7B", "aya-expanse:8b": "8B", "qwen2.5:14b-instruct": "14B"}
def slug(s): return s.replace(".", "").replace(":", "-")

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (round(c-h, 3), round(c+h, 3))

units = collections.defaultdict(dict)   # (inst, rot, constraint) -> model -> row
outputs = collections.defaultdict(dict) # (inst, rot) -> model -> output
for m in MODELS:
    rows = []
    for f in sorted(glob.glob(f"results/e17_{slug(m)}_v6_pin4_o*.csv")):
        rows += list(csv.DictReader(open(f)))
    assert len(rows) == 384, (m, len(rows))
    for r in rows:
        units[(r["instance"], int(r["rotation"]), r["constraint"])][m] = r
    for f in sorted(glob.glob(f"results/e17_{slug(m)}_v6_pin4_o*.json")):
        for d in json.load(open(f)):
            outputs[(d["instance"], d["rotation"])][m] = d["output"]
    assert len({k for k in outputs if m in outputs[k]}) == 144, m

# aggregate rates
agg = {}
for m in MODELS:
    by = collections.defaultdict(lambda: [0, 0])
    plans = []
    for k, per in units.items():
        r = per[m]; by[r["status"]][1] += 1
        if r["included"] == "True": by[r["status"]][0] += 1
        plans.append(int(r["n_actions"]))
    agg[m] = {"size": SIZES[m], "mean_plan": round(sum(plans)/len(plans), 2)}
    for st, (k, n) in by.items():
        agg[m][st] = {"rate": round(k/n, 3), "k": k, "n": n, "ci": wilson(k, n)}

# per-dialogue records with turns + each model's plan
dias = []
for d in all_dialogues():
    inst, rot = d["instance"], d["rotation"]
    turns = [{"speaker": s, "text": t, "tag": tag[0], "cid": tag[1]} for s, t, tag in d["dialogue"]]
    us = []
    for u in d["units"]:
        per = units[(inst.id, rot, u["constraint"])]
        us.append({"constraint": u["constraint"], "action": u["action"], "status": u["status"],
                   "included": {m: per[m]["included"] == "True" for m in MODELS}})
    plans = {m: outputs[(inst.id, rot)][m] for m in MODELS}
    dias.append({"instance": inst.id, "domain": inst.domain, "graph": inst.graph, "rotation": rot,
                 "vocab": sorted({a for a, _ in DOMAINS[inst.domain]["actions"]}),
                 "verbs": dict(DOMAINS[inst.domain]["actions"]),
                 "turns": turns, "units": us, "plans": plans})

# showcase: dialogues with a rejected unit where models split
def split_score(dd):
    s = 0
    for u in dd["units"]:
        if u["status"] == "rejected":
            k = sum(u["included"].values()); s = max(s, min(k, 6-k))
    return s
show = sorted([d for d in dias if any(u["status"]=="rejected" for u in d["units"])], key=split_score, reverse=True)
print("corpus hash", corpus_hash())
for m in MODELS:
    a = agg[m]; print(f"{m:22} rejected {a['rejected']['rate']:.3f} {a['rejected']['ci']}  never {a['never']['rate']:.3f}  accepted {a['accepted']['rate']:.3f}  proposed {a['proposed']['rate']:.3f}  |plan| {a['mean_plan']}")
print("top splits:", [(d["instance"], d["rotation"], split_score(d)) for d in show[:8]])
out = {"corpus_hash": corpus_hash(), "models": MODELS, "agg": agg, "dialogues": dias,
       "showcase": [(d["instance"], d["rotation"]) for d in show[:6]]}
json.dump(out, open("C:/Users/chris/AppData/Local/Temp/claude/C--Users-chris-week1-llm-lab/69e40ecd-f587-4c11-ac76-e565a3ca3e06/scratchpad/xray_data.json", "w"))
print("bytes", len(json.dumps(out)))
