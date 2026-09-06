"""Gates for the E16 menu diagnostic. Run before any call is made.

The load-bearing gate is test_base_arm_is_the_frozen_instruction_verbatim:
the diagnostic compares a new `wide` arm against the ALREADY-RUN E16 stage-1
data. That comparison is only valid if the two prompts differ in the
identifier list and in nothing else.
"""
import lineage_bench
from lineage_e16 import all_dialogues, corpus_hash, render, required_slots

from e16_menu_diagnostic import (CORPUS_HASH, EXTRA_ACTIONS,
                                 menu_plan_instruction, vocabulary)

INSTANCES = lineage_bench.all_instances()


def test_corpus_hash_unchanged():
    assert corpus_hash() == CORPUS_HASH


def test_six_domains_six_extras_each():
    settings = {i.setting for i in INSTANCES}
    assert set(EXTRA_ACTIONS) == settings
    for setting, extras in EXTRA_ACTIONS.items():
        assert len(extras) == 6, setting
        assert len(set(extras)) == 6, setting


def test_extras_are_globally_distinct_and_new():
    original = set()
    for i in INSTANCES:
        original |= set(i.actions)
    allextra = [a for extras in EXTRA_ACTIONS.values() for a in extras]
    assert len(allextra) == len(set(allextra)), "duplicate distractor"
    assert not (set(allextra) & original), "distractor collides with a real action"


def test_no_distractor_appears_in_any_dialogue():
    """A distractor must never be mentioned; that is the whole point."""
    allextra = {a for extras in EXTRA_ACTIONS.values() for a in extras}
    for d in all_dialogues():
        text = render(d["dialogue"]).lower()
        for a in allextra:
            # neither the identifier nor its prose form may occur
            assert a not in text, (a, d["instance"].id)
            assert a.lower() not in text, (a, d["instance"].id)
            assert a.lower().replace("_", " ") not in text, (a, d["instance"].id)


def test_vocabulary_sizes_per_arm():
    for i in INSTANCES:
        assert len(vocabulary(i, "base")) == 6
        assert len(vocabulary(i, "wide")) == 12
        assert len(set(vocabulary(i, "wide"))) == 12
        assert len(vocabulary(i, "narrow")) in (2, 3)


def test_narrow_arm_keeps_every_unit_action():
    for d in all_dialogues():
        narrow = set(vocabulary(d["instance"], "narrow"))
        for u in d["units"]:
            assert u["action"] in narrow


def test_every_arm_contains_every_unit_action():
    for d in all_dialogues():
        for arm in ("narrow", "base", "wide"):
            vocab = set(vocabulary(d["instance"], arm))
            for u in d["units"]:
                assert u["action"] in vocab, (arm, u["action"])


def test_narrow_is_a_subset_of_base_is_a_subset_of_wide():
    for i in INSTANCES:
        n, b, w = (set(vocabulary(i, a)) for a in ("narrow", "base", "wide"))
        assert n <= b <= w


def test_base_arm_is_the_frozen_instruction_verbatim():
    """The only permitted difference between arms is the identifier list."""
    for i in INSTANCES:
        assert menu_plan_instruction(i, vocabulary(i, "base")) == \
            lineage_bench.plan_instruction(i)


def test_wide_instruction_lists_all_twelve():
    for i in INSTANCES:
        text = menu_plan_instruction(i, vocabulary(i, "wide"))
        for a in vocabulary(i, "wide"):
            assert a in text
        assert text.count("identifiers:") == 1


def test_required_slots_match_unit_actions():
    for d in all_dialogues():
        slots = {c.a for c in required_slots(d["instance"])}
        assert {u["action"] for u in d["units"]} <= slots
