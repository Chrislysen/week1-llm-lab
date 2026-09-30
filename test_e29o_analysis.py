"""Zero-model-call checks that E29-O's declared read returns each account on data built to show it,
and refuses rival worlds (length, a failed probe, no order effect)."""
import copy
import csv
import json
import os
import random
import tempfile

import e29o_analysis as A
from lineage_e29o import CELLS, dialogues

COLS = ["model", "design", "arm", "instance", "rotation", "slot", "constraint", "action", "status", "parsed",
        "included", "n_actions", "ready", "attempts", "prompt_tokens", "completion_tokens", "seconds"]
LO, HI = 0.05, 0.70
BASE = {c: LO for c in CELLS} | {"open": 0.95, "withdrawn_pre": HI, "formally_pre": HI, "later_pre": HI,
                                  "field_pre": HI, "first_pre": 0.95, "xfirst_pre": HI}
WORLDS = {   # rejected-step inclusion per cell; unlisted cells are LO
    "NARR": BASE | {"later_pre": LO, "label_pre": HI, "clause_pre": HI, "named_pre": HI},
    "REC": BASE | {"label_pre": HI, "clause_pre": HI, "named_pre": HI},
    "BIND": BASE | {"clause_pre": HI},
    "CLAUSE": BASE | {"label_pre": HI},
    "PROX": BASE | {"clause_pre": HI, "xfirst_pre": LO, "xfirst_post": HI},
    "META": BASE | {"label_pre": HI, "label_post": HI, "field_post": HI},
    "LENGTH": BASE | {"later_pre": LO, "formally_pre": LO, "clause_pre": HI},
    "NO ORDER": BASE | {"withdrawn_pre": LO},
}
PREMISE = {"NARR": "SUPPORTED"}


def build(world, model, condition="MET"):
    rng = random.Random(7)
    rows = []
    for d in dialogues():
        for c in CELLS:
            for u in d["units"]:
                p = WORLDS[world][c] if u["status"] == "rejected" else {"never": 0.5}.get(u["status"], 0.95)
                rows.append({"model": model, "design": c, "arm": "neutral", "instance": u["instance"],
                             "rotation": u["rotation"], "slot": u["slot"], "constraint": u["constraint"],
                             "action": u["action"], "status": u["status"], "parsed": True,
                             "included": rng.random() < p, "n_actions": 4, "ready": True, "attempts": 1,
                             "prompt_tokens": 0, "completion_tokens": 0, "seconds": 0})
    os.makedirs("results", exist_ok=True)
    with open(f"results/e29o_{A.slug(model)}_r0.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    k_hit = {"withdrawn_pre|rejected": 0.9, "withdrawn_pre|control": 0.05,
             "later_pre|rejected": 0.9, "later_pre|control": 0.05}
    with open(f"results/e29o_recognition_{A.slug(model)}_summary.json", "w", encoding="utf-8") as fh:
        json.dump({"K": {"status": "VALID", "min_parse": 1.0, "hit": k_hit},
                   "E": {"status": "VALID", "condition": condition,
                         "narr_premise": PREMISE.get(world, "UNCLEAR")}}, fh)


def read(world, condition="MET", model="llama3.2:3b"):
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            build(world, model, condition)
            return A.main(model)
        finally:
            os.chdir(here)


def test_each_account_world_returns_that_account_and_only_that_one():
    for world in ("NARR", "REC", "BIND", "CLAUSE", "PROX", "META"):
        out = read(world)
        assert out["gate"] == "ORDER", world
        assert out["account"] == world, (world, out["outcomes"], out["refuted_by"])


def test_a_length_effect_fits_no_account():
    out = read("LENGTH")
    assert out["outcomes"]["T1"] == "LENGTH" and out["account"] == "NONE FITS", out["outcomes"]


def test_no_order_effect_reads_no_account():
    out = read("NO ORDER")
    assert out["gate"] == "NO ORDER EFFECT" and out["account"] == "NOT READ"


def test_not_rescued_needs_the_end_state_condition():
    out = read("REC", condition="NOT MET")
    assert out["outcomes"]["T1"] == "UNINTERPRETABLE"
    assert out["account"].startswith("UNRESOLVED") and "NARR" in out["account"] and "REC" in out["account"]


def test_the_premise_probe_refutes_narr():
    o = {"T1": "RESCUED", "label": "BOUND", "clause": "BOUND", "named": "BOUND", "T4": "DIRECTION",
         "T5": "WORKS", "T0": "REFUTED"}
    assert "T0" in A.refuted("NARR", o) and A.verdict(o) == "NONE FITS"
    assert A.verdict(o | {"T0": "UNCLEAR"}) == "NARR"


def test_reversed_and_uninformative_outcomes_refute_the_accounts_they_contradict():
    o = {"T1": "NOT RESCUED", "label": "FREE", "clause": "BOUND", "named": "REVERSED", "T4": "DIRECTION",
         "T5": "WORKS", "T0": "UNCLEAR"}
    assert A.verdict(o) == "NONE FITS"
    assert A.verdict(o | {"named": "UNCLEAR"}) == "BIND"
    assert A.verdict(o | {"label": "UNINFORMATIVE", "clause": "FREE", "named": "FREE", "T5": "FAILS"}) == "META"


def test_scaled_classes_follow_the_order_effect_not_a_fixed_threshold():
    """d = 0.12 with POS = 0.16 is more than half the order effect: BOUND, although d < 0.15."""
    c = {k: {"d": 0.0, "ci": [-0.05, 0.05], "D": -0.08, "Dci": [-0.12, -0.03]} for k in A.PAIRS}
    c["PN"] = {"d": 0.12, "ci": [0.06, 0.18], "D": 0.04, "Dci": [0.01, 0.07]}
    c["PX"] = {"d": 0.1, "ci": [0.02, 0.18]}
    cls = {f"{m}_post": {"class": "HONOURED"} for m in ("label", "clause", "named")}
    o = A.outcomes_of(c, cls, "MET", "UNCLEAR")
    assert o["named"] == "BOUND" and o["label"] == "FREE" and o["T4"] == "DIRECTION"


def test_programme_needs_two_agreeing_deciders_and_no_refutation():
    b1, b2 = read("BIND", model="llama3.2:3b"), read("BIND", model="aya-expanse:8b")
    assert A.programme([b1, b2])["account"] == "BIND SUPPORTED"
    n = read("CLAUSE", model="qwen2.5:14b-instruct")
    assert A.programme([b1, b2, n])["account"].startswith("MIXED")        # BIND refuted on the 14B
    assert A.programme([b1])["order"].startswith("NO PROGRAMME READING")
    nb = copy.deepcopy(n)
    nb["gate"] = "NO ORDER EFFECT"
    assert A.programme([b1, b2, nb])["order"].startswith("MIXED")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
