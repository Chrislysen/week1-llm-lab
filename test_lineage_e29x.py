"""Zero-model-call checks for the E29-X reviewer controls."""
from lineage_bench import DOMAINS, NEW_DOMAINS
from lineage_e29 import all_e29_dialogues, context_block, store_delete
from lineage_e29x import (DESIGNS_X, EXPLICIT, context_block_x, explicit_dialogue,
                          store_tombstone)


def _verb(d, u):
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_explicit_rendering_changes_only_reply_referents():
    for doms in (None, NEW_DOMAINS):
        for d in all_e29_dialogues(doms):
            for arm in ("restated", "neutral"):
                dia = d["arms"][arm]
                ex = explicit_dialogue(d["instance"], dia)
                assert len(ex) == len(dia)
                for (s1, t1, g1), (s2, t2, g2) in zip(dia, ex):
                    assert s1 == s2 and g1 == g2
                    if g1[0] == "reply":
                        assert t1 in EXPLICIT and t2 != t1
                        assert "the proposal to " in t2
                    else:
                        assert t1 == t2


def test_explicit_reply_names_its_own_action_and_no_other():
    for d in all_e29_dialogues():
        verbs = {u["constraint"]: _verb(d, u) for u in d["units"]}
        dia = d["arms"]["neutral"]
        for (_, t, tag) in explicit_dialogue(d["instance"], dia):
            if tag[0] == "reply":
                own = verbs[tag[1]]
                assert own in t
                assert sum(v in t for v in set(verbs.values())) == 1, t


def test_tombstone_keeps_flagged_proposal_and_no_rejection_fact():
    for d in all_e29_dialogues():
        u = next(u for u in d["units"] if u["status"] == "rejected")
        verb = _verb(d, u)
        for arm in ("restated", "neutral"):
            facts, events = store_tombstone(d["instance"], d["arms"][arm])
            flagged = [f for f in facts if f.startswith("[withdrawn] ") and verb in f]
            assert len(flagged) == 1, (d["instance"].id, arm, facts)
            assert not any("rejected" in f for f in facts)
            assert sum(1 for e, _ in events if e == "FLAG") == 1
            mentions = [f for f in facts if verb in f]
            assert len(mentions) == (2 if arm == "restated" else 1)
            # the flagged line is the bare proposal fact, never an accepted one
            assert flagged[0] == f"[withdrawn] {flagged[0].split('] ', 1)[1]}" and "accepted" not in flagged[0]


def test_tombstone_differs_from_delete_only_by_the_flagged_line():
    for d in all_e29_dialogues():
        for arm in ("restated", "neutral"):
            t, _ = store_tombstone(d["instance"], d["arms"][arm])
            dl, _ = store_delete(d["instance"], d["arms"][arm])
            assert [f for f in t if not f.startswith("[withdrawn] ")] == dl


def test_headers_match_the_e29_designs():
    d = all_e29_dialogues()[0]
    dia = d["arms"]["restated"]
    assert context_block_x("full_explicit", d["instance"], dia).startswith("DISCUSSION\n----------\n")
    assert context_block_x("tombstone", d["instance"], dia).startswith("MEMORY NOTES FROM THE DISCUSSION\n")
    assert context_block("delete", d["instance"], dia).startswith("MEMORY NOTES FROM THE DISCUSSION\n")
    assert set(DESIGNS_X) == {"full_explicit", "tombstone"}
