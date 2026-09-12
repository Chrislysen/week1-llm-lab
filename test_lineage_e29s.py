"""Zero-model-call checks for the E29-S 2x2."""
from lineage_bench import DOMAINS
from lineage_e29 import all_e29_dialogues, store_addonly
from lineage_e29e import store_e
from lineage_e29s import DESIGNS_S, context_block_s, store_s

DS = all_e29_dialogues()


def _rej(d):
    return next(u for u in d["units"] if u["status"] == "rejected")


def _verb(d, u):
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_three_cells_are_byte_identical_to_e29e():
    """addonly, addonly_meta and addonly_flag must be the same stores E29-E
    measured, so the new cell is the only thing that changed."""
    for d in DS:
        for arm in ("restated", "neutral"):
            for X in ("addonly", "addonly_meta", "addonly_flag"):
                a, _ = store_s(X, d["instance"], d["arms"][arm])
                b, _ = store_e(X, d["instance"], d["arms"][arm])
                assert a == b, (X, d["instance"].id, arm)
    a, _ = store_s("addonly", DS[0]["instance"], DS[0]["arms"]["neutral"])
    b, _ = store_addonly(DS[0]["instance"], DS[0]["arms"]["neutral"])
    assert a == b


def test_merged_is_the_same_text_with_one_bullet_fewer():
    """The whole manipulation: one "\\n- " becomes " ". No word changes."""
    for d in DS:
        for arm in ("restated", "neutral"):
            a, _ = store_s("addonly", d["instance"], d["arms"][arm])
            m, _ = store_s("addonly_merged", d["instance"], d["arms"][arm])
            assert len(m) == len(a) - 1, (d["instance"].id, arm)
            assert " ".join(a).split() == " ".join(m).split(), (d["instance"].id, arm)
            # and the join happened on the proposal of the rejected step
            u = _rej(d)
            verb = _verb(d, u)
            joined = [x for x in m if x.count(verb) == 2 and "rejected the proposal" in x]
            assert len(joined) == 1, (d["instance"].id, arm, m)


def test_merged_keeps_every_other_line_untouched():
    for d in DS:
        a, _ = store_s("addonly", d["instance"], d["arms"]["neutral"])
        m, _ = store_s("addonly_merged", d["instance"], d["arms"]["neutral"])
        merged = next(x for x in m if "rejected the proposal" in x)
        rest_m = [x for x in m if x != merged]
        rest_a = [x for x in a if "rejected the proposal" not in x
                  and not merged.startswith(x)]
        assert rest_m == rest_a, (d["instance"].id, rest_m, rest_a)


def test_the_rejection_survives_in_every_cell():
    """All four stores contain the rejection; only its structure differs."""
    for d in DS:
        u = _rej(d)
        verb = _verb(d, u)
        for X in DESIGNS_S:
            lines, _ = store_s(X, d["instance"], d["arms"]["neutral"])
            text = " ".join(lines)
            assert verb in text
            assert ("rejected" in text) or ("WITHDRAWN" in text) or ("[withdrawn]" in text), X


def test_headers_match_e29():
    d = DS[0]
    for X in DESIGNS_S:
        assert context_block_s(X, d["instance"], d["arms"]["restated"]).startswith(
            "MEMORY NOTES FROM THE DISCUSSION\n")
