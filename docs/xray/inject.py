"""Inline the X-ray data (and E29 summary, if present) into the template."""
import json, os, sys

S = os.path.dirname(os.path.abspath(__file__))
REPO = r"C:\Users\chris\week1-llm-lab"
tpl = open(os.path.join(S, "xray_template.html"), encoding="utf-8").read()
data = json.load(open(os.path.join(S, "xray_data.json"), encoding="utf-8"))

import glob
summaries = []
for summary_path in sorted(glob.glob(os.path.join(REPO, "results", "e29_*_summary.json"))):
    e = json.load(open(summary_path, encoding="utf-8"))
    v = e["verdict"]
    e["verdict_short"] = v.split(":")[0].split(" (")[0].lower()
    e["note"] = (f"{e['model']}, read by the rule declared before the first call: {v}. "
                 f"Under write-time delete the restatement moved relapse from "
                 f"{e['p']['delete|neutral']:.2f} to {e['p']['delete|restated']:.2f}; under full context the same line "
                 f"moved it by {e['delta']['full']:+.2f}.")
    summaries.append(e)
    print("E29 summary attached:", e["model"], v)
if summaries:
    summaries[-1]["note"] += (" Stores are semantic ideals built from the scorer's tags, not the output of a real "
                              "extractor; paired bootstrap over dialogues, B = 2000; the read rule uses only the "
                              "within-design difference, so levels across designs are shown, not compared.")
    b = os.path.join(REPO, "results", "e29b_llama32-3b_summary.json")
    if os.path.exists(b):
        eb = json.load(open(b, encoding="utf-8"))
        summaries[-1]["note"] += (f" A follow-up (E29-B) ran the Mem0 paper's own extraction prompt for real on {eb['n']} of these "
                                  f"dialogues with llama3.2:3b: it stored the proposed step at its proposal line in "
                                  f"{eb['manip_prop']:.2f} of them, so that stage reads uninformative by its declared rule; "
                                  f"descriptively, the rejected step mostly never entered the store at all, and a later "
                                  f"restatement entered it as a fresh fact.")
    data["e29"] = summaries
else:
    print("no E29 summary yet")

blob = json.dumps(data).replace("</", "<\\/")
html = tpl.replace("__DATA__", blob)
out = os.path.join(S, "zombie_xray.html")
open(out, "w", encoding="utf-8").write(html)
print("written", len(html), "bytes ->", out)
