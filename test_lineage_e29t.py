"""Zero-model-call checks for E29-T: only the revocation idiom may change."""
from lineage_e29 import all_e29_dialogues
from lineage_e29s import context_block_s, store_s
from lineage_e29t import IDIOMS, REAL_WORLD, context_block_t, store_t

DS = all_e29_dialogues()
ARMS = ("restated", "neutral")


def test_sentence_and_anchor_are_e29s_blocks_byte_for_byte():
    for d in DS:
        for arm in ARMS:
            assert context_block_t("sentence", d["instance"], d["arms"][arm]) == \
                context_block_s("addonly", d["instance"], d["arms"][arm])
            assert context_block_t("withdrawn_prefix", d["instance"], d["arms"][arm]) == \
                context_block_s("addonly_flag", d["instance"], d["arms"][arm])


def test_every_idiom_differs_from_the_tag_on_exactly_one_item():
    """Same stream as E29-S's flag store; only the marked proposal differs."""
    for d in DS:
        for arm in ARMS:
            flag = store_s("addonly_flag", d["instance"], d["arms"][arm])[0]
            for idiom in REAL_WORLD:
                t = store_t(idiom, d["instance"], d["arms"][arm])
                assert len(t) == len(flag)
                diffs = [(a, b) for a, b in zip(flag, t) if a != b]
                assert len(diffs) == 1, (idiom, d["instance"].id, arm, diffs)
                old, new = diffs[0]
                bare = old[len("[withdrawn] "):]
                assert bare in new and "rejected" not in new, (idiom, new)


def test_no_idiom_carries_a_rejection_sentence():
    """Every idiom cell must record the rejection ONLY as the idiom."""
    for d in DS:
        for idiom in IDIOMS[1:]:
            t = store_t(idiom, d["instance"], d["arms"]["neutral"])
            assert not any("rejected the proposal" in x for x in t), idiom


def test_idioms_are_distinct():
    d = DS[0]
    blocks = {i: context_block_t(i, d["instance"], d["arms"]["neutral"]) for i in IDIOMS}
    assert len(set(blocks.values())) == len(IDIOMS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
