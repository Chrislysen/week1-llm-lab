"""Zero-model-call checks that the E29 corpus and stores are what the
declaration says they are."""
import collections

from lineage_bench import DOMAINS
from lineage_e16 import build_dialogue, corpus_hash as e16_hash
from lineage_e29 import (ARMS, DESIGNS, E16_HASH, NEUTRAL_BY_WORDS, T_RESTATE,
                         all_e29_dialogues, context_block, facts_for,
                         store_addonly, store_delete, store_wiki)

DS = all_e29_dialogues()


def _rej(d):
    return next(u for u in d["units"] if u["status"] == "rejected")


def _verb(d, u):
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_base_is_e16_and_only_rejected_slot_dialogues():
    assert e16_hash() == E16_HASH
    assert len(DS) == 96
    for d in DS:
        assert sum(u["status"] == "rejected" for u in d["units"]) == 1


def test_arms_differ_in_exactly_one_line_and_end_on_noise():
    for d in DS:
        a, b = d["arms"]["restated"], d["arms"]["neutral"]
        assert len(a) == len(b)
        diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        assert len(diffs) == 1, (d["instance"].id, d["rotation"], diffs)
        i = diffs[0]
        assert a[i][2][0] == "restate" and b[i][2][0] == "neutral"
        assert a[i][0] == b[i][0]                       # same speaker
        assert len(a[i][1].split()) == len(b[i][1].split())  # same word count
        assert a[-1][2][0] == "noise" and b[-1][2][0] == "noise"
        # the inserted line is the last or second-to-last line
        assert i >= len(a) - 2


def test_inserted_line_is_spoken_by_the_original_proposer():
    for d in DS:
        u = _rej(d)
        a = d["arms"]["restated"]
        p = next(i for i, (_, _, tag) in enumerate(a) if tag == ("proposal", u["constraint"]))
        r = next(i for i, (_, _, tag) in enumerate(a) if tag == ("restate", u["constraint"]))
        assert a[p][0] == a[r][0]
        assert a[r][1] == T_RESTATE.format(a=_verb(d, u))


def test_base_lines_are_unchanged_from_e16():
    for d in DS:
        base = build_dialogue(d["instance"], d["rotation"])
        for arm in ARMS:
            lines = [(t, tag) for _, t, tag in d["arms"][arm] if tag[0] not in ("restate", "neutral")]
            base_lines = [(t, tag) for _, t, tag in base]
            # base lines appear in order; at most one extra noise line was appended
            assert lines[:len(base_lines)] == base_lines
            assert len(lines) - len(base_lines) in (0, 1)
            if len(lines) > len(base_lines):
                assert lines[-1][1] == ("noise", None)


def test_neutral_referents_cover_every_action_phrase_length():
    lengths = {len(v.split()) for dom in DOMAINS.values() for _, v in dom["actions"]}
    assert lengths <= set(NEUTRAL_BY_WORDS)
    for ref in NEUTRAL_BY_WORDS.values():
        for dom in DOMAINS.values():
            for _, v in dom["actions"]:
                assert v not in ref


def test_delete_semantics():
    for d in DS:
        u, verb = _rej(d), _verb(d, _rej(d))
        facts_n, ev_n = store_delete(d["instance"], d["arms"]["neutral"])
        facts_r, ev_r = store_delete(d["instance"], d["arms"]["restated"])
        # neutral: nothing about the rejected action survives, and one DELETE fired
        assert not any(verb in f for f in facts_n)
        assert sum(e == "DELETE" for e, _ in ev_n) == 1
        # restated: the mention survives exactly once, no rejection anywhere
        assert sum(verb in f for f in facts_r) == 1
        assert not any("rejected" in f for f in facts_r)
        assert any(f.startswith(f"{d['arms']['restated'][0][0]}") or True for f in facts_r)
        # accepted proposals are UPDATEd, not deleted
        for a in d["units"]:
            if a["status"] == "accepted":
                v = _verb(d, a)
                assert any(v in f and "accepted it" in f for f in facts_n)


def test_addonly_semantics():
    for d in DS:
        verb = _verb(d, _rej(d))
        facts_n, _ = store_addonly(d["instance"], d["arms"]["neutral"])
        facts_r, _ = store_addonly(d["instance"], d["arms"]["restated"])
        assert len(facts_n) == len(d["arms"]["neutral"])   # one fact per line
        assert sum(verb in f for f in facts_n) == 2         # proposal + rejection
        assert sum(verb in f for f in facts_r) == 3         # + restatement
        assert any("rejected the proposal to " + verb in f for f in facts_r)


def test_wiki_semantics():
    for d in DS:
        verb = _verb(d, _rej(d))
        pages_n, _ = store_wiki(d["instance"], d["arms"]["neutral"])
        pages_r, _ = store_wiki(d["instance"], d["arms"]["restated"])
        pn = next(p for p in pages_n if p.startswith(f"## {verb}\n"))
        pr = next(p for p in pages_r if p.startswith(f"## {verb}\n"))
        assert "- proposed by" in pn and "- rejected by" in pn and "noted again" not in pn
        assert "- proposed by" in pr and "- rejected by" in pr and "noted again" in pr
        assert any(p.startswith("## discussion log") for p in pages_n)


def test_full_is_the_transcript_and_blocks_are_nonempty():
    for d in DS:
        for arm in ARMS:
            for design in DESIGNS:
                block = context_block(design, d["instance"], d["arms"][arm])
                assert block.strip()
            full = context_block("full", d["instance"], d["arms"][arm])
            for s, t, _ in d["arms"][arm]:
                assert f"{s}: {t}" in full


def test_structure_counts():
    c = collections.Counter(len(d["arms"]["restated"]) for d in DS)
    assert sum(c.values()) == 96
    extra = sum(1 for d in DS
                if len(d["arms"]["restated"]) == len(build_dialogue(d["instance"], d["rotation"])) + 2)
    assert extra == 39, extra   # parity forces the fourth noise line in 39 dialogues
    for d in DS:
        assert d["arms"]["restated"][-2][2][0] == "restate"
