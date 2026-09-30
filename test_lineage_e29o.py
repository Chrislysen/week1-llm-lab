"""Zero-model-call checks for E29-O: only the marker's form and position, and the record's place, change."""
from lineage_bench import DOMAINS
from lineage_e29a import store_a
from lineage_e29o import CELLS, NEUTRAL, TOP, context_block_o, corpora_ok, dialogues, store_o
from lineage_e29s import store_s

DS = dialogues()
MARKS = ("rejected", "withdrawn")
PAIRS = ("withdrawn", "later", "named", "label", "clause", "xfirst", "field")


def phrase(d):
    u = next(u for u in d["units"] if u["status"] == "rejected")
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def proposer_and_rejector(d, x):
    base = store_s("addonly", d["instance"], d["arms"]["neutral"])[0]
    a = next(it for it in base if it.endswith(f"proposed to {x}.")).split(" proposed to ")[0]
    b = next(it for it in base if f"rejected the proposal to {x}" in it).split(" rejected the proposal to ")[0]
    return a, b


def target_index(s, x):
    """The record's item: it proposes X, or (X first) names X and its proposer."""
    xc = f"{x[0].upper()}{x[1:]} (proposed by"
    return next(k for k, it in enumerate(s) if f"proposed to {x}" in it or xc in it)


def test_two_corpora_192_dialogues_disjoint_ids():
    assert corpora_ok()
    assert len(DS) == 192
    assert len({(d["instance"].id, d["rotation"]) for d in DS}) == 192
    assert len({d["instance"].id for d in DS[:96]} & {d["instance"].id for d in DS[96:]}) == 0


def test_the_record_follows_the_neutral_item_and_is_never_first():
    for d in DS:
        x = phrase(d)
        for c in CELLS:
            s = store_o(c, d["instance"], d["arms"]["neutral"])
            i = target_index(s, x)
            assert s.count(NEUTRAL) == 1, c
            if c in TOP:
                assert i == 0, c
            else:
                assert i >= 1 and s[i - 1] == NEUTRAL, c


def test_the_neutral_item_is_in_no_stream():
    for d in DS:
        assert NEUTRAL not in store_s("addonly", d["instance"], d["arms"]["neutral"])[0]


def test_the_top_block_moves_only_the_record():
    for d in DS:
        x = phrase(d)
        for top, main in TOP.items():
            t = store_o(top, d["instance"], d["arms"]["neutral"])
            m = store_o(main, d["instance"], d["arms"]["neutral"])
            rec_m = [it for it in m if x in it]
            assert t[: len(rec_m)] == rec_m, top
            assert [it for it in t if it not in rec_m] == [it for it in m if it not in rec_m], top


def test_only_the_record_changes_and_the_rest_keeps_its_order():
    for d in DS:
        base = store_s("addonly", d["instance"], d["arms"]["neutral"])[0]
        x = phrase(d)
        r = next(k for k, it in enumerate(base) if f"rejected the proposal to {x}" in it)
        rest = base[: r - 1] + base[r + 1:]
        for c in CELLS:
            if c in TOP:
                continue
            s = store_o(c, d["instance"], d["arms"]["neutral"])
            k = len(s) - len(rest) - 1          # items standing for the record
            assert k in (1, 2), (c, k)
            assert s[: r - 1] == rest[: r - 1] and s[r - 1 + 1 + k:] == rest[r - 1:], c


def test_the_rejection_is_recorded_once_and_open_records_none():
    for d in DS:
        x = phrase(d)
        for c in CELLS:
            s = store_o(c, d["instance"], d["arms"]["neutral"])
            marks = [it for it in s if any(m in it.lower() for m in MARKS)]
            assert len(marks) == (0 if c == "open" else 1), (c, marks)
            assert x.lower() in " ".join(s).lower(), c


def test_pre_and_post_twins_hold_the_same_words_and_differ_only_in_the_record():
    for d in DS:
        x = phrase(d)
        for kind in PAIRS:
            pre = store_o(f"{kind}_pre", d["instance"], d["arms"]["neutral"])
            post = store_o(f"{kind}_post", d["instance"], d["arms"]["neutral"])
            i = target_index(pre, x)
            assert pre[:i] == post[:i] and pre[i + 1:] == post[i + 1:]
            assert sorted(pre[i].split()) == sorted(post[i].split()), kind
            assert pre[i].startswith("[") and post[i].endswith("]"), kind


def test_the_markers_are_as_declared():
    for d in DS:
        x = phrase(d)
        a, b = proposer_and_rejector(d, x)
        p = f"{a} proposed to {x}."
        xc = f"{x[0].upper()}{x[1:]} (proposed by {a})."
        want = {"withdrawn_pre": f"[withdrawn] {p}", "withdrawn_post": f"{p} [withdrawn]",
                "later_pre": f"[subsequently withdrawn] {p}", "later_post": f"{p} [subsequently withdrawn]",
                "formally_pre": f"[formally withdrawn] {p}",
                "named_pre": f"[{b} rejected the proposal to {x}] {p}", "named_post": f"{p} [{b} rejected the proposal to {x}]",
                "label_pre": f"[withdrawn: {x}] {p}", "label_post": f"{p} [withdrawn: {x}]",
                "clause_pre": f"[{b} rejected the proposal] {p}", "clause_post": f"{p} [{b} rejected the proposal]",
                "xfirst_pre": f"[withdrawn] {xc}", "xfirst_post": f"{xc} [withdrawn]",
                "field_pre": f"[status: withdrawn] {p}", "field_post": f"{p} [status: withdrawn]",
                "first_pre": f"[withdrawn] {p}", "first_post": f"{p} [withdrawn]", "open": p}
        for c, line in want.items():
            s = store_o(c, d["instance"], d["arms"]["neutral"])
            assert s[target_index(s, x)] == line, (c, s[target_index(s, x)], line)


def test_the_length_control_matches_the_temporal_cue_in_words():
    for d in DS[:5]:
        x = phrase(d)
        f = store_o("formally_pre", d["instance"], d["arms"]["neutral"])
        l = store_o("later_pre", d["instance"], d["arms"]["neutral"])
        i = target_index(f, x)
        assert len(f[i].split()) == len(l[i].split())


def test_e29a_cells_are_these_cells_without_the_neutral_item():
    for d in DS[:96]:
        for c, a in (("withdrawn_pre", "tag_prefix"), ("withdrawn_post", "tag_suffix"),
                     ("sentence_short", "sentence_short")):
            s = store_o(c, d["instance"], d["arms"]["neutral"])
            assert [it for it in s if it != NEUTRAL] == store_a(a, d["instance"], d["arms"]["neutral"]), c


def test_cells_are_distinct():
    for d in (DS[0], DS[100]):
        blocks = {c: context_block_o(c, d["instance"], d["arms"]["neutral"]) for c in CELLS}
        assert len(set(blocks.values())) == len(CELLS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
