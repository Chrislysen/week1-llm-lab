"""Plan-selection fixture checks. Zero model calls.

Validates the FIXTURE LOGIC only. Says nothing about whether any receiver can
exploit the structure -- that is what a separately declared and allocated
qualification arm would test.
"""
import json
from collections import Counter
from itertools import permutations

import pytest

from plansel_fixtures import (LABELS, build_fixture, consistent_options, family,
                              render_prompt, score_option)


@pytest.fixture(scope="module")
def fam():
    return family(8)


def test_information_structure_is_4_2_2_1(fam):
    """Neither -> 4, either alone -> 2, both -> exactly 1."""
    for fx in fam:
        assert len(consistent_options(fx, ())) == 4
        assert len(consistent_options(fx, ("F1",))) == 2
        assert len(consistent_options(fx, ("F2",))) == 2
        both = consistent_options(fx, ("F1", "F2"))
        assert len(both) == 1 and both[0].label == fx.correct_label


def test_holding_the_first_fact_leaves_only_the_second_message_needed(fam):
    """The recipient-context contrast the direction rests on."""
    for fx in fam:
        assert len(consistent_options(fx, ("F1",))) == 2      # still ambiguous
        assert len(consistent_options(fx, ("F1", "F2"))) == 1  # F2 resolves it


def test_holds_across_all_four_fact_assignments():
    for i in range(4):
        fx = build_fixture(i, domain="payments")
        assert len(consistent_options(fx, ())) == 4
        assert len(consistent_options(fx, ("F1", "F2"))) == 1


def test_holds_across_all_24_display_orders(fam):
    fx = fam[0]
    unique = consistent_options(fx, ("F1", "F2"))[0].label
    for perm in permutations(fx.options):
        g = fx.__class__(**{**fx.__dict__, "options": perm})
        assert len(consistent_options(g, ())) == 4
        assert len(consistent_options(g, ("F1",))) == 2
        both = consistent_options(g, ("F1", "F2"))
        assert len(both) == 1 and both[0].label == unique


def test_answer_identity_and_position_are_balanced_and_separable(fam):
    assert dict(Counter(f.correct_label for f in fam)) == {L: 2 for L in LABELS}
    assert dict(Counter(f.correct_position for f in fam)) == {1: 2, 2: 2, 3: 2, 4: 2}
    # separable: label and position are not the same variable
    assert any(LABELS.index(f.correct_label) + 1 != f.correct_position for f in fam)


def test_scorer_accepts_only_the_consistent_option(fam):
    for fx in fam:
        good = score_option(json.dumps({"option": fx.correct_label, "ready": True}), fx)
        assert good["parsed"] and good["success"] and good["violated"] == []
        for o in fx.options:
            if o.label == fx.correct_label:
                continue
            bad = score_option(json.dumps({"option": o.label, "ready": True}), fx)
            assert bad["parsed"] and not bad["success"] and bad["violated"]


def test_scorer_rejects_malformed_and_preserves_readiness(fam):
    fx = fam[0]
    assert not score_option("no json", fx)["parsed"]
    assert not score_option(json.dumps({"option": "P9", "ready": True}), fx)["parsed"]
    assert not score_option(json.dumps({"option": fx.correct_label}), fx)["parsed"]
    refused = score_option(json.dumps({"option": fx.correct_label, "ready": False}), fx)
    assert refused["parsed"] and refused["violated"] == [] and not refused["success"]


def test_prompt_supplies_no_answer_and_delivers_only_the_subset(fam):
    fx = fam[0]
    facts = {cid: t for cid, t in fx.candidates}
    empty = render_prompt(fx, "knows_neither", frozenset())
    assert facts["A"] not in empty and facts["B"] not in empty
    assert all(o.label in empty for o in fx.options)      # options always shown
    assert "correct" not in empty.lower()
    one = render_prompt(fx, "knows_neither", frozenset({"A"}))
    assert facts["A"] in one and facts["B"] not in one


# --- quartet construction (PSQ) -------------------------------------------


def test_quartet_holds_everything_fixed_except_fact_orientation():
    from plansel_fixtures import quartets
    for q in quartets(8):
        assert len({tuple(o.label for o in f.options) for f in q}) == 1
        assert len({tuple(o.sequence for o in f.options) for f in q}) == 1
        assert len({f.actions for f in q}) == 1
        assert len({(f.candidates[2], f.candidates[3]) for f in q}) == 1
        # the fact messages DO change, consistently with the constraints
        assert len({(f.candidates[0], f.candidates[1]) for f in q}) == 4
        assert len({f.constraints for f in q}) == 4


def test_each_quartet_has_four_different_correct_options_and_positions():
    from plansel_fixtures import LABELS, quartets
    for q in quartets(8):
        assert sorted(f.correct_label for f in q) == sorted(LABELS)
        assert sorted(f.correct_position for f in q) == [1, 2, 3, 4]


def test_no_answer_is_revealed_by_ids_or_prompts():
    from plansel_fixtures import CIDS, quartets, render_prompt
    for q in quartets(8):
        for f in q:
            assert f.correct_label not in f.fid
            p = render_prompt(f, "knows_neither", frozenset(CIDS))
            lines = [l.strip() for l in p.split("\n") if l.strip().startswith("P")]
            assert len(lines) == 4
            assert len({len(l.split(":")[0]) for l in lines}) == 1
            assert "correct" not in p.lower()


def test_all_32_cases_score_correctly():
    import json as _json
    from plansel_fixtures import quartets, score_option
    for q in quartets(8):
        for f in q:
            good = score_option(_json.dumps({"option": f.correct_label,
                                             "ready": True}), f)
            assert good["success"] and good["violated"] == []
            for o in f.options:
                if o.label != f.correct_label:
                    bad = score_option(_json.dumps({"option": o.label,
                                                    "ready": True}), f)
                    assert not bad["success"] and bad["violated"]
