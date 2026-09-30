"""Zero-model-call checks for E29-M: the fix changes only how the revoked record is rendered."""
from lineage_e29 import DOMAINS, all_e29_dialogues
from lineage_e29m import CELLS, FLAGS, context_block_m, store_m
from lineage_e29t import store_t

DS = all_e29_dialogues()
ARMS = ("restated", "neutral")


def rejected_phrase(d):
    u = next(u for u in d["units"] if u["status"] == "rejected")
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_control_and_anchors_are_the_prompts_e29t_sent():
    """Checked against E29-T's recorded prompts, not against the function E29-M reuses."""
    import json
    from e29m_fix import build_user
    for m in ("llama32-3b", "qwen25-14b-instruct"):
        sent = {(r["instance"], str(r["rotation"]), r["design"]): r["prompt"]
                for r in json.load(open(f"results/e29t_{m}_r0.json", encoding="utf-8")) if r["arm"] == "neutral"}
        for d in DS:
            for c in ("sentence", "is_active_false", "invalid_at"):
                assert sent[(d["instance"].id, str(d["rotation"]), c)] == build_user(c, d["instance"], d["arms"]["neutral"])


def test_rewrite_is_the_control_with_one_item_reworded_in_place():
    """Every reply in this corpus directly follows its proposal, so G is a one-item wording contrast."""
    for d in DS:
        for arm in ARMS:
            ctrl = store_t("sentence", d["instance"], d["arms"][arm])
            fix = store_m("rewrite", d["instance"], d["arms"][arm])
            assert len(fix) == len(ctrl)
            diffs = [k for k, (a, b) in enumerate(zip(ctrl, fix)) if a != b]
            assert len(diffs) == 1 and "rejected the proposal" in ctrl[diffs[0]]
            assert fix[diffs[0]] == f"The proposal to {rejected_phrase(d)} was withdrawn."


def test_rewrite_is_the_same_store_whichever_field_it_came_from():
    from lineage_e29m import rewrite_revocations
    for d in DS:
        for arm in ARMS:
            a = rewrite_revocations(store_t("is_active_false", d["instance"], d["arms"][arm]), FLAGS["is_active_false"])
            b = rewrite_revocations(store_t("invalid_at", d["instance"], d["arms"][arm]), FLAGS["invalid_at"])
            assert a == b == store_m("rewrite", d["instance"], d["arms"][arm])


def test_rewrite_removes_the_field_and_adds_exactly_one_sentence_after_the_record():
    for d in DS:
        for arm in ARMS:
            tag = store_t("is_active_false", d["instance"], d["arms"][arm])
            fix = store_m("rewrite", d["instance"], d["arms"][arm])
            assert len(fix) == len(tag) + 1
            i = next(k for k, x in enumerate(tag) if x.endswith(FLAGS["is_active_false"]))
            assert fix[:i] == tag[:i] and fix[i + 2:] == tag[i + 1:]
            assert fix[i] == tag[i][: -len(FLAGS["is_active_false"])]
            assert fix[i + 1] == f"The proposal to {rejected_phrase(d)} was withdrawn."
            assert not any("[is_active" in x or "[invalid_at" in x for x in fix)


def test_annotate_keeps_the_field_and_adds_the_same_sentence():
    for d in DS:
        for arm in ARMS:
            for cell, idiom in (("annotate_is_active", "is_active_false"), ("annotate_invalid_at", "invalid_at")):
                tag = store_t(idiom, d["instance"], d["arms"][arm])
                ann = store_m(cell, d["instance"], d["arms"][arm])
                i = next(k for k, x in enumerate(tag) if x.endswith(FLAGS[idiom]))
                assert ann[: i + 1] == tag[: i + 1] and ann[i + 2:] == tag[i + 1:]
                assert ann[i + 1] == f"The proposal to {rejected_phrase(d)} was withdrawn."


def test_no_fixed_cell_carries_the_original_rejection_sentence():
    """The fix's sentence is the only verbal record of the rejection."""
    for d in DS:
        for cell in CELLS[1:]:
            s = store_m(cell, d["instance"], d["arms"]["neutral"])
            assert not any("rejected the proposal" in x for x in s), cell


def test_cells_are_distinct():
    d = DS[0]
    blocks = {c: context_block_m(c, d["instance"], d["arms"]["neutral"]) for c in CELLS}
    assert len(set(blocks.values())) == len(CELLS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
