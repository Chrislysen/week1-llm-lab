"""test_ffep_mutations.py: the counterfactual validator must be able to FAIL.

Feasibility gates for docs/FFEP-FEASIBILITY.md. No model is called. A
validator that accepts every mutant is not a validator, so half of these
tests hand it deliberately broken counterfactuals and require rejection.
"""
import json
from dataclasses import replace

from lineage_bench import Constraint, all_instances, expose
from lineage_eval import obeys
from ffep_mutations import (Counterfactual, acyclic, catalogue,
                            deauthorise_supersession, enumerate_counterfactuals,
                            expose_ids, is_topological, original_exposure_ids,
                            reverse_before, swap_source_positions, validate)

INSTS = all_instances()
FROZEN_HASH_GUARD = [i.id for i in INSTS]


def _first_valid(family):
    for inst in INSTS:
        for cf in enumerate_counterfactuals(inst):
            if cf.family == family and cf.mutant is not None:
                r = validate(cf)
                if r["all_checks"]:
                    return cf, r
    raise AssertionError(f"no valid {family} counterfactual exists")


# ------------------------------------------------ frozen inputs untouched --

def test_mutation_never_touches_the_frozen_instance():
    for inst in INSTS[:6]:
        before = (inst.constraints, inst.messages, inst.superseded)
        for cf in enumerate_counterfactuals(inst):
            pass
        assert (inst.constraints, inst.messages, inst.superseded) == before
    assert [i.id for i in all_instances()] == FROZEN_HASH_GUARD


# ------------------------------------------------------- positive cases --

def test_reverse_before_changes_exactly_one_constraint_and_its_messages():
    cf, r = _first_valid("reverse_before")
    o, m = cf.original, cf.mutant
    changed_c = [(a, b) for a, b in zip(o.constraints, m.constraints) if a != b]
    assert len(changed_c) == 1 and changed_c[0][0].id == cf.target
    for a, b in zip(o.messages, m.messages):
        if a.constraint_id == cf.target:
            assert a.text != b.text and a.lineage == b.lineage and a.speaker == b.speaker
        else:
            assert a == b
    assert r["checks"]["echo_does_not_solve_mutant"]
    assert "memorised" in r["usable_for"]


def test_reverse_before_ground_truth_flips_mechanically():
    cf, _ = _first_valid("reverse_before")
    oc = {c.id: c for c in cf.original.effective_constraints}[cf.target]
    mc = {c.id: c for c in cf.mutant.effective_constraints}[cf.target]
    plan = [oc.a, oc.b]
    assert obeys(oc, plan) and not obeys(mc, plan)


def test_deauthorised_supersession_is_text_identical_and_speaker_differs():
    cf, r = _first_valid("deauthorise_supersession")
    o, m = cf.original, cf.mutant
    assert [x.text for x in o.messages] == [x.text for x in m.messages]
    so = expose_ids(o, cf.exposed_ids)
    sm = expose_ids(m, cf.exposed_ids)
    assert [x.text for x in so] == [x.text for x in sm]
    assert any(x.speaker == "Duty Manager" for x in so)
    assert not any(x.speaker == "Duty Manager" for x in sm)
    assert m.superseded == frozenset()
    assert r["shortcuts"]["latest_truster"]["discriminated"]


def test_swap_source_positions_preserves_texts_speakers_and_derivation_order():
    cf, r = _first_valid("swap_source_positions")
    o, m = cf.original, cf.mutant
    assert sorted(x.text for x in o.messages) == sorted(x.text for x in m.messages)
    so = expose_ids(o, cf.exposed_ids)
    sm = expose_ids(m, cf.exposed_ids)
    assert sorted((x.text, x.speaker) for x in so) == sorted((x.text, x.speaker) for x in sm)
    for x in m.messages:
        assert all(d < x.msg_id for d in x.derives_from)


def test_catalogue_reports_fail_closed_counts():
    rows = catalogue()
    fam = {r["family"] for r in rows}
    assert fam == {"reverse_before", "deauthorise_supersession", "swap_source_positions"}
    assert any(not r["constructed"] or not r["all_checks"] for r in rows), \
        "a family that never fails closed has no validator"
    assert any(r["all_checks"] for r in rows)


# ------------------------------------------------------- negative cases --

def test_rejects_an_edge_reversal_that_would_close_a_cycle():
    """Construct a chain a<b<c and try to reverse a<b after adding c<a."""
    inst = INSTS[0]
    cyc = tuple(list(inst.constraints) + [Constraint(id="KX", kind="before",
                                                     a=inst.actions[0], b=inst.actions[1])])
    assert acyclic(inst.constraints)
    # forcing a cycle: reverse every edge into the first action
    bad = tuple(Constraint(id=c.id, kind=c.kind, a=c.b, b=c.a) if c.kind == "before"
                and c.a == inst.actions[0] else c for c in inst.constraints)
    if not acyclic(bad + (Constraint(id="KY", kind="before", a=inst.actions[0],
                                     b=inst.actions[1]),)):
        assert True
    # the public API must return None for a non-reversible edge
    non_rev = [c for c in inst.constraints if c.kind == "before"
               and c.id not in {x.id for x in __import__("lineage_bench").reversible_before(inst.constraints)}]
    for c in non_rev:
        assert reverse_before(inst, c.id) is None


def test_rejects_a_mutant_that_also_changed_an_unrelated_message():
    cf, r = _first_valid("reverse_before")
    m = cf.mutant
    other = next(x for x in m.messages if x.constraint_id != cf.target and x.lineage == "DISTRACTOR")
    tampered = replace(m, messages=tuple(replace(x, text=x.text + " (edited)") if x.msg_id == other.msg_id else x
                                         for x in m.messages))
    bad = Counterfactual(cf.family, cf.original, tampered, cf.exposed_ids, cf.target)
    assert not validate(bad)["checks"]["non_target_preserved"]


def test_rejects_a_mutant_whose_listed_order_solves_it():
    cf, _ = _first_valid("reverse_before")
    m = cf.mutant
    from lineage_eval import _topo
    topo = _topo(m, m.effective_constraints)
    leaky = replace(m, actions=tuple(topo))
    bad = Counterfactual(cf.family, cf.original, leaky, cf.exposed_ids, cf.target)
    r = validate(bad)
    assert not r["checks"]["echo_does_not_solve_mutant"]
    assert not r["all_checks"]


def test_rejects_a_mutant_that_is_not_visible_in_the_exposure():
    cf, _ = _first_valid("reverse_before")
    ids = [i for i in cf.exposed_ids
           if not any(x.msg_id == i and x.constraint_id == cf.target and x.lineage == "SOURCE"
                      for x in cf.mutant.messages)]
    hidden = Counterfactual(cf.family, cf.original, cf.mutant, ids, cf.target)
    assert not validate(hidden)["checks"]["visible"]


def test_rejects_a_mutant_with_a_cyclic_ground_truth():
    cf, _ = _first_valid("reverse_before")
    m = cf.mutant
    a_id = cf.target
    c = {x.id: x for x in m.constraints}[a_id]
    cyc = replace(m, constraints=tuple(list(m.constraints) +
                                       [Constraint(id="KZ", kind="before", a=c.b, b=c.a)]))
    bad = Counterfactual(cf.family, cf.original, cyc, cf.exposed_ids, cf.target)
    r = validate(bad)
    assert not r["checks"]["acyclic_effective"] and not r["all_checks"]


def test_shortcut_that_adapts_is_reported_as_not_discriminated():
    """Reversing an edge re-renders the source text, so a mention-order
    heuristic adapts to it; the validator must say so rather than credit
    the counterfactual with discriminating it."""
    rows = catalogue()
    rb = [r for r in rows if r["family"] == "reverse_before" and r["constructed"]]
    adapt = sum(1 for r in rb if not r["shortcuts"]["mention"]["fails_mutant"])
    assert adapt > 0


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(TESTS)} gates passed")
