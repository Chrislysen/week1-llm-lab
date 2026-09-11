"""Zero-model-call checks that the E29-C corpus is what the declaration says."""
from lineage_bench import DOMAINS
from lineage_e29 import NEUTRAL_BY_WORDS, all_e29_dialogues
from lineage_e29c import ARMS_C, T_PLAIN, all_e29c_dialogues, corpus_hash

DS = all_e29c_dialogues()
E29 = {(d["instance"].id, d["rotation"]): d for d in all_e29_dialogues()}


def _rej(d):
    return next(u for u in d["units"] if u["status"] == "rejected")


def _verb(d, u):
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_same_96_dialogues_and_four_arms():
    assert len(DS) == 96
    assert {(d["instance"].id, d["rotation"]) for d in DS} == set(E29)
    for d in DS:
        assert set(d["arms"]) == set(ARMS_C)


def test_e29_arms_are_byte_identical():
    for d in DS:
        e = E29[(d["instance"].id, d["rotation"])]
        assert d["arms"]["restated"] == e["arms"]["restated"]
        assert d["arms"]["neutral"] == e["arms"]["neutral"]


def test_every_pair_of_arms_differs_in_exactly_the_inserted_line():
    for d in DS:
        ref = d["arms"]["neutral"]
        for arm in ARMS_C:
            a = d["arms"][arm]
            assert len(a) == len(ref)
            diffs = [i for i, (x, y) in enumerate(zip(a, ref)) if x != y]
            assert len(diffs) <= 1, (d["instance"].id, d["rotation"], arm, diffs)
            if diffs:
                i = diffs[0]
                assert a[i][0] == ref[i][0]                          # same speaker
                assert len(a[i][1].split()) == len(ref[i][1].split())  # same word count
                assert i >= len(a) - 2
            assert a[-1][2][0] == "noise"


def test_plain_lines_have_the_declared_text_and_tags():
    for d in DS:
        u = _rej(d)
        plain, pn = d["arms"]["plain"], d["arms"]["plain_neutral"]
        i = next(i for i, (_, _, tag) in enumerate(plain) if tag == ("restate", u["constraint"]))
        assert plain[i][1] == T_PLAIN.format(a=_verb(d, u))
        k = len(_verb(d, u).split())
        assert pn[i][1] == T_PLAIN.format(a=NEUTRAL_BY_WORDS[k])
        assert pn[i][2] == ("neutral", None)
        # spoken by the original proposer, like E29's line
        p = next(j for j, (_, _, tag) in enumerate(plain) if tag == ("proposal", u["constraint"]))
        assert plain[p][0] == plain[i][0] == pn[i][0]


def test_all_four_lines_share_the_word_count():
    for d in DS:
        n = None
        for arm in ARMS_C:
            a = d["arms"][arm]
            line = next(t for _, t, tag in a if tag[0] in ("restate", "neutral"))
            n = len(line.split()) if n is None else n
            assert len(line.split()) == n


def test_corpus_hash_is_stable():
    assert corpus_hash() == corpus_hash()
    assert len(corpus_hash()) == 16
