"""Gates for E17. All must pass before any call.

The load-bearing gates are:
  * test_free_v6_is_the_frozen_instruction_verbatim -- the |vocab|=6 free cell
    must reproduce lineage_bench.plan_instruction exactly, so it is comparable
    to E16 stage 1 and to the E16 menu diagnostic's base arm;
  * test_pin4_adds_exactly_one_line -- the pinned condition must differ from
    free by ONE sentence and nothing else, or the length manipulation is
    confounded with a wording change.
"""
import lineage_bench
from lineage_e16 import all_dialogues, corpus_hash, render

from e16_menu_diagnostic import EXTRA_ACTIONS
from e17_menu_law import (CORPUS_HASH, EXTRA_ACTIONS_2, LENGTHS, PIN_N,
                          VOCAB_SIZES, plan_instruction, vocabulary)

INSTANCES = lineage_bench.all_instances()


def test_corpus_hash_unchanged():
    assert corpus_hash() == CORPUS_HASH


def test_twelve_new_distractors_per_domain():
    settings = {i.setting for i in INSTANCES}
    assert set(EXTRA_ACTIONS_2) == settings
    for setting, extras in EXTRA_ACTIONS_2.items():
        assert len(extras) == 12, setting
        assert len(set(extras)) == 12, setting


def test_all_distractors_globally_distinct_and_new():
    original = set()
    for i in INSTANCES:
        original |= set(i.actions)
    tier1 = [a for e in EXTRA_ACTIONS.values() for a in e]
    tier2 = [a for e in EXTRA_ACTIONS_2.values() for a in e]
    allx = tier1 + tier2
    assert len(allx) == len(set(allx)), "duplicate distractor across tiers"
    assert not (set(allx) & original), "distractor collides with a real action"


def test_no_distractor_appears_in_any_dialogue():
    allx = {a for e in EXTRA_ACTIONS_2.values() for a in e}
    for d in all_dialogues():
        text = render(d["dialogue"]).lower()
        for a in allx:
            assert a not in text, (a, d["instance"].id)
            assert a.lower() not in text, (a, d["instance"].id)
            assert a.lower().replace("_", " ") not in text, (a, d["instance"].id)


def test_vocabulary_sizes_and_nesting():
    for i in INSTANCES:
        v6, v12, v24 = (vocabulary(i, n) for n in VOCAB_SIZES)
        assert (len(v6), len(v12), len(v24)) == (6, 12, 24)
        assert len(set(v24)) == 24
        assert set(v6) <= set(v12) <= set(v24)


def test_every_unit_action_in_every_vocabulary():
    for d in all_dialogues():
        for n in VOCAB_SIZES:
            vocab = set(vocabulary(d["instance"], n))
            for u in d["units"]:
                assert u["action"] in vocab, (n, u["action"])


def test_free_v6_is_the_frozen_instruction_verbatim():
    for i in INSTANCES:
        assert plan_instruction(vocabulary(i, 6), "free") == \
            lineage_bench.plan_instruction(i)


def test_pin4_adds_exactly_one_line():
    for i in INSTANCES:
        for n in VOCAB_SIZES:
            free = plan_instruction(vocabulary(i, n), "free")
            pin = plan_instruction(vocabulary(i, n), "pin4")
            assert pin.startswith(free), n
            added = pin[len(free):]
            assert added.count("\n") == 1, repr(added)
            assert str(PIN_N) in added


def test_pin4_is_achievable_at_every_vocabulary_size():
    """PIN_N must not exceed the smallest menu, or the arm is impossible."""
    assert PIN_N <= min(VOCAB_SIZES)


def test_every_arm_lists_all_its_identifiers():
    for i in INSTANCES:
        for n in VOCAB_SIZES:
            for L in LENGTHS:
                text = plan_instruction(vocabulary(i, n), L)
                for a in vocabulary(i, n):
                    assert a in text
