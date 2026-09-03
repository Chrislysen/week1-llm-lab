"""test_lineage_e16.py: gates the E16 zombie screen must clear before any call."""
from collections import Counter

from lineage_bench import DOMAINS, all_instances
from lineage_e10 import corpus_hash as e10_hash
from lineage_e11 import corpus_hash as e11_hash
from lineage_e12 import corpus_hash as e12_hash
from lineage_e16 import (N_ROTATIONS, STATUSES, T_ACCEPT, T_REJECT, T_PROPOSE,
                         all_dialogues, corpus_hash, render, required_slots)

DS = all_dialogues()
BY_INST = {i.id: i for i in all_instances()}


def test_frozen_corpora_undisturbed():
    assert e10_hash() == "00947dde8eb0520b", "E10 corpus disturbed"
    assert e11_hash() == "5c28ada4c4b899dc", "E11 corpus disturbed"
    assert e12_hash() == "ecf1f4884fa49270", "E12 corpus disturbed"


def test_counts_and_balance():
    assert len(DS) == 36 * N_ROTATIONS
    units = [u for d in DS for u in d["units"]]
    assert len(units) == 384, len(units)
    per = Counter(u["status"] for u in units)
    assert all(per[s] == 96 for s in STATUSES), per


def test_every_constraint_sees_every_status_once():
    seen = {}
    for d in DS:
        for u in d["units"]:
            seen.setdefault((u["instance"], u["constraint"]), []).append(u["status"])
    assert len(seen) == 96
    for key, sts in seen.items():
        assert sorted(sts) == sorted(STATUSES), (key, sts)


def test_replies_carry_no_action_words():
    """A reply must refer to the proposal by adjacency only (module docstring)."""
    phrases = {p.lower() for dom in DOMAINS.values() for _, p in dom["actions"]}
    idents = {a.lower() for dom in DOMAINS.values() for a, _ in dom["actions"]}
    for t in T_ACCEPT + T_REJECT:
        low = t.lower()
        assert "{a}" not in t
        assert not any(p in low for p in phrases), t
        assert not any(i in low for i in idents), t
    # And every proposal template does carry the action.
    assert all("{a}" in t for t in T_PROPOSE)


def test_reply_immediately_follows_its_proposal():
    for d in DS:
        dia = d["dialogue"]
        for u in d["units"]:
            idx = [i for i, (_, _, tag) in enumerate(dia) if tag[1] == u["constraint"]]
            if u["status"] == "never":
                assert idx == [], u
            elif u["status"] == "proposed":
                assert len(idx) == 1 and dia[idx[0]][2][0] == "proposal", u
            else:
                assert len(idx) == 2 and idx[1] == idx[0] + 1, u
                assert dia[idx[0]][2][0] == "proposal" and dia[idx[1]][2][0] == "reply"
                assert dia[idx[0]][0] != dia[idx[1]][0], "reply must come from the other speaker"


def test_last_message_is_noise():
    for d in DS:
        assert d["dialogue"][-1][2] == ("noise", None), d["instance"].id


def test_same_proposal_wording_under_every_status():
    """Status differences must not be template differences."""
    for inst in all_instances():
        for c in required_slots(inst):
            texts = set()
            for d in DS:
                if d["instance"].id != inst.id:
                    continue
                for s, t, tag in d["dialogue"]:
                    if tag == ("proposal", c.id):
                        texts.add(t)
            assert len(texts) == 1, (inst.id, c.id, texts)


def test_no_status_or_lineage_marker_in_text():
    for d in DS:
        low = render(d["dialogue"]).lower()
        # Domain noise legitimately says "status page"; the markers that would
        # leak the design are the status labels and constraint ids.
        for w in ("accepted", "rejected", "proposed", "k1", "k2", "k3", "k4", "k5", "k6", "k7"):
            assert w not in low.replace(",", " ").replace(".", " ").split(), (d["instance"].id, w)


def test_deterministic_hash():
    assert corpus_hash() == "70f136a47f5779c8", corpus_hash()
    assert corpus_hash() == corpus_hash()
