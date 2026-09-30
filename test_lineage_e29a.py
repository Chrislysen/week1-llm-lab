"""Zero-model-call checks for E29-A: only the rendering of the rejection may change."""
import glob
import json

from lineage_e29 import DOMAINS, all_e29_dialogues
from lineage_e29a import CELLS, context_block_a, store_a
from lineage_e29s import context_block_s, store_s
from lineage_e29t import context_block_t

DS = all_e29_dialogues()
ARMS = ("restated", "neutral")
REASON = "it is not needed for this case"


def phrase(d):
    u = next(u for u in d["units"] if u["status"] == "rejected")
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_anchors_are_earlier_blocks_byte_for_byte():
    for d in DS:
        for arm in ARMS:
            a = d["arms"][arm]
            assert context_block_a("sentence", d["instance"], a) == context_block_s("addonly", d["instance"], a)
            assert context_block_a("status_long", d["instance"], a) == context_block_s("addonly_meta", d["instance"], a)
            assert context_block_a("tag_prefix", d["instance"], a) == context_block_s("addonly_flag", d["instance"], a)
            assert context_block_a("paren_suffix", d["instance"], a) == context_block_t("withdrawn_suffix", d["instance"], a)


def test_anchors_match_the_prompts_actually_sent():
    """Against recorded prompts, not against the functions E29-A reuses."""
    from e29a_at_issue import build_user
    for m in ("llama32-3b", "qwen25-14b-instruct", "aya-expanse-8b"):
        sent = {}
        for f in sorted(glob.glob(f"results/e29s_{m}_r*.json")):
            for r in json.load(open(f, encoding="utf-8")):
                sent[(r["instance"], str(r["rotation"]), r["design"], r["arm"])] = r["prompt"]
        for d in DS:
            for cell, design in (("sentence", "addonly"), ("tag_prefix", "addonly_flag"), ("status_long", "addonly_meta")):
                key = (d["instance"].id, str(d["rotation"]), design, "neutral")
                assert sent[key] == build_user(cell, d["instance"], d["arms"]["neutral"]), (m, key)
    for m in ("llama32-3b", "qwen25-14b-instruct"):
        sent = {(r["instance"], str(r["rotation"]), r["design"]): r["prompt"]
                for r in json.load(open(f"results/e29t_{m}_r0.json", encoding="utf-8")) if r["arm"] == "neutral"}
        for d in DS:
            assert sent[(d["instance"].id, str(d["rotation"]), "withdrawn_suffix")] == \
                build_user("paren_suffix", d["instance"], d["arms"]["neutral"]), m


def test_only_the_proposal_and_rejection_change():
    """Every cell keeps the rest of the add-only stream, in order, untouched."""
    for d in DS:
        for arm in ARMS:
            base = store_s("addonly", d["instance"], d["arms"][arm])[0]
            r = next(k for k, x in enumerate(base) if " rejected the proposal to " in x)
            rest = base[: r - 1] + base[r + 1:]
            for c in CELLS[1:]:
                s = store_a(c, d["instance"], d["arms"][arm])
                k = len(s) - len(rest)
                assert k in (1, 2), (c, k)
                assert s[: r - 1] == rest[: r - 1] and s[r - 1 + k:] == rest[r - 1:], c


def test_every_cell_names_the_step_and_records_the_rejection_once():
    for d in DS:
        x = phrase(d)
        for c in CELLS:
            s = store_a(c, d["instance"], d["arms"]["neutral"])
            marks = [it for it in s if ("rejected" in it or "withdrawn" in it.lower())]
            assert len(marks) == 1, (c, marks)
            assert x in " ".join(s), c
            assert (REASON in " ".join(s)) == (c in ("sentence", "status_long")), c


def test_status_short_is_verb_less_and_status_long_is_not():
    for d in DS:
        x = phrase(d)
        short = store_a("status_short", d["instance"], d["arms"]["neutral"])
        long = store_a("status_long", d["instance"], d["arms"]["neutral"])
        assert f"status({x}) = WITHDRAWN." in short
        assert f"status({x}) = WITHDRAWN; {REASON}." in long


def test_the_medial_pair_differs_only_in_the_clause_link():
    """Same words for A, B and X, the rejection in the same place, X last in both."""
    for d in DS:
        arc = [i for i in store_a("arc_medial", d["instance"], d["arms"]["neutral"]) if "'s proposal" in i][0]
        main = [i for i in store_a("main_medial", d["instance"], d["arms"]["neutral"]) if "'s proposal" in i][0]
        assert arc.replace(", which was rejected by ", " was rejected by ").replace(", was to ", "; it was to ") == main
        assert arc.endswith(f"was to {phrase(d)}.") and main.endswith(f"was to {phrase(d)}.")


def test_cells_are_distinct():
    d = DS[0]
    blocks = {c: context_block_a(c, d["instance"], d["arms"]["neutral"]) for c in CELLS}
    assert len(set(blocks.values())) == len(CELLS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
