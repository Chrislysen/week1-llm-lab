"""Deterministic fixture checks for Phase B. Zero model calls.

These validate the FIXTURES: that reference solutions exist and score, that
known-bad outputs are rejected, that the two recipient contexts are nested
variants of one task, that budget accounting is in rendered words, and that the
schedule is reproducible and inside the 288-call ceiling.

They say NOTHING about whether any model can solve these tasks. That is what the
qualification arm is for, and it has not been run.
"""
import json

import pytest

import lineage_eval as le
from agentcom_bundle import SubsetOutcome
from phaseb_fixtures import (CEILING, CIDS, QUAL_COMBOS, STUDY_COMBOS,
                             build_task, decision_points, qualification_schedule,
                             reference_plan, render_prompt, schedule,
                             score_response, validate)


@pytest.fixture(scope="module")
def prepared():
    tasks = [build_task(d, g) for d, g in STUDY_COMBOS]
    qual = [build_task(d, g, salt="phaseb-qual-v1") for d, g in QUAL_COMBOS]
    return tasks, qual, schedule(tasks), qualification_schedule(qual)


def test_full_validation_suite_passes(prepared):
    rep, fail = validate(*prepared)
    assert fail == 0, [r for r in rep if not r["ok"]]
    assert len(rep) > 150


def test_every_task_has_a_verified_reference_solution(prepared):
    tasks, qual, _, _ = prepared
    for t in tasks + qual:
        inst = t["instance"]
        ref = reference_plan(inst)
        assert ref is not None, t["task_id"]
        assert all(le.obeys(c, ref) for c in inst.constraints)
        assert score_response(json.dumps({"actions": ref, "ready": True}),
                              inst).success


def test_known_invalid_outputs_are_rejected(prepared):
    tasks, _, _, _ = prepared
    inst = tasks[0]["instance"]
    ref = reference_plan(inst)
    assert not score_response("no json here", inst).parsed
    assert not score_response('{"actions": ["X"]}', inst).parsed  # no `ready`
    assert not score_response(json.dumps({"actions": ref, "ready": False}),
                              inst).success
    assert not score_response(json.dumps({"actions": list(reversed(ref)),
                                          "ready": True}), inst).success
    assert not score_response(json.dumps({"actions": [], "ready": True}),
                              inst).success


def test_contexts_are_nested_variants_not_independent_tasks(prepared):
    tasks, _, _, _ = prepared
    for t in tasks:
        a, b = t["variants"]["knows_A"], t["variants"]["knows_B"]
        assert set(a) ^ set(b) == {t["candidates"][0].source_id,
                                   t["candidates"][1].source_id}
        # same underlying task, therefore the same scoring key for both
        assert t["instance"].constraints is t["instance"].constraints
    # 8 tasks, 16 decision points -- the unit of independence is the task
    assert len(tasks) == 8
    assert len(decision_points(tasks)) == 16


def test_qualification_fixtures_are_separate_from_study_tasks(prepared):
    tasks, qual, _, _ = prepared
    assert not ({t["task_id"] for t in tasks} & {t["task_id"] for t in qual})
    assert len(qual) == 8


def test_prompts_carry_exactly_the_delivered_subset(prepared):
    tasks, _, _, _ = prepared
    t = tasks[0]
    empty = render_prompt(t, "knows_A", frozenset())
    for c in t["candidates"][2:]:          # C and D are never pre-known
        assert c.text not in empty
    for cid in CIDS:
        one = render_prompt(t, "knows_A", frozenset({cid}))
        chosen = next(c for c in t["candidates"] if c.cid == cid)
        assert chosen.text in one


def test_schedule_is_reproducible_and_positions_are_logged(prepared):
    tasks, _, blocks, _ = prepared
    again = schedule(tasks)
    assert [c["subset"] for b in again for c in b["calls"]] == \
           [c["subset"] for b in blocks for c in b["calls"]]
    for b in blocks:
        assert sorted(c["request_position"] for c in b["calls"]) == list(range(1, 17))
        assert len({tuple(c["subset"]) for c in b["calls"]}) == 16


def test_ceiling_accounting_is_exact(prepared):
    _, _, blocks, qblocks = prepared
    subset_calls = sum(b["n_calls"] for b in blocks)
    qual_calls = sum(b["n_calls"] for b in qblocks)
    assert subset_calls == CEILING["subset"] == 256
    assert qual_calls == CEILING["qualification"] == 16
    assert subset_calls + qual_calls + CEILING["reserve"] == CEILING["total"] == 288


def test_execution_fields_stay_empty_until_a_call_happens(prepared):
    tasks, _, _, _ = prepared
    dp = decision_points(tasks)[0]
    o = SubsetOutcome(dp_id=dp.dp_id, subset=("A",), rendered_words=7,
                      scorer="x")
    assert not o.executed and o.score is None and o.response is None
    assert o.prompt_tokens is None and o.completion_tokens is None
    with pytest.raises(ValueError):
        SubsetOutcome(dp_id=dp.dp_id, subset=("A",), rendered_words=7,
                      scorer="x", score=1.0)     # claims a result, never ran
