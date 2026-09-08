"""Deterministic mechanism tests for agentcom_bundle. Zero model calls.

Ports the supplied laboratory's fixtures (AGENTCOM-BUNDLE spec, Phase A) into
this repo's pytest suite, and adds the checks that laboratory could not make
because it had no repo interface: rendered-vs-additive budget accounting, and
that the opt-in adapter is a genuine pass-through.

Every utility below is an AUTHORED mathematical function in abstract units.
These tests check mechanism only. They are not agent results, not evidence that
any model behaves this way, and not a novelty claim.
"""
import pytest

from agentcom_bundle import (MAX_CANDIDATES, Candidate,
                             CoefficientProvenance, QuadraticUtility,
                             SnapshotPolicy, additive_estimate,
                             anchored_expansion, conditional_greedy,
                             exact_select, max_residual, render_bundle,
                             select_bundle, serialised_cost)

IDS = ("A", "B", "C")


def unit_cost(_ids):
    return lambda s: len(s)


def expand_and_select(ids, budget, utility):
    est = anchored_expansion(ids, utility)
    cost = unit_cost(ids)
    return (conditional_greedy(ids, budget, utility, cost),
            select_bundle(ids, budget, est, cost),
            exact_select(ids, budget, utility, cost),
            max_residual(ids, utility, est))


# --- the supplied laboratory's cases --------------------------------------


def test_positive_pair_defeats_singleton_greedy():
    u = lambda s: 0.8 * ({"A", "B"} <= set(s)) + 0.2 * ("C" in s)
    greedy, bundle, oracle, resid = expand_and_select(IDS, 2, u)
    assert sorted(greedy) == ["C"]                  # each singleton looks weak
    assert sorted(bundle) == ["A", "B"]
    assert sorted(oracle) == ["A", "B"]
    assert resid == pytest.approx(0.0)


def test_recipient_context_changes_the_best_bundle():
    """Same offered messages; only what the recipient already knows differs."""
    has_a = lambda s: 0.8 * ("B" in s) + 0.2 * ("C" in s)
    has_b = lambda s: 0.8 * ("A" in s) + 0.2 * ("C" in s)
    assert sorted(expand_and_select(IDS, 2, has_a)[1]) == ["B", "C"]
    assert sorted(expand_and_select(IDS, 2, has_b)[1]) == ["A", "C"]


def test_no_invented_benefit_when_interactions_absent():
    u = lambda s: sum({"A": 0.5, "B": 0.3, "C": 0.2}[i] for i in s)
    greedy, bundle, oracle, resid = expand_and_select(IDS, 2, u)
    assert sorted(bundle) == ["A", "B"] == sorted(greedy) == sorted(oracle)
    assert resid == pytest.approx(0.0)


def test_negative_interaction_is_handled_by_recomputed_greedy_too():
    u = (lambda s: 0.4 * ("A" in s) + 0.4 * ("B" in s) + 0.2 * ("C" in s)
         - 0.7 * ({"A", "B"} <= set(s)))
    greedy, bundle, _, _ = expand_and_select(IDS, 2, u)
    assert sorted(greedy) == ["A", "C"]
    assert sorted(bundle) == ["A", "C"]


def test_ANCHORED_degree_two_misses_a_third_order_requirement():
    """The declared limitation, kept so it cannot be quietly dropped.

    SCOPE, made explicit (addendum, 2026-09-08): this tests the ANCHORED
    estimator -- `anchored_expansion`, which reads only the empty set, singletons
    and pairs. It is NOT a verdict on the degree-2 class. On this same authored
    table a uniform least-squares degree-2 projection selects A+B+C with zero
    regret; see `test_agentcom_analysis.py`. Assertions below are unchanged.
    """
    ids = ("A", "B", "C", "D")
    u = lambda s: 0.8 * ({"A", "B", "C"} <= set(s)) + 0.2 * ("D" in s)
    greedy, bundle, oracle, resid = expand_and_select(ids, 3, u)
    assert sorted(bundle) == ["D"]                  # pair model fails here
    assert sorted(oracle) == ["A", "B", "C"]        # unrestricted search does not
    assert resid > 0.5                              # higher-order residual is large


def test_optimal_sets_need_not_be_nested_in_budget():
    u = lambda s: 0.3 * ("A" in s) + 0.7 * ({"B", "C"} <= set(s))
    assert sorted(expand_and_select(IDS, 1, u)[1]) == ["A"]
    assert sorted(expand_and_select(IDS, 2, u)[1]) == ["B", "C"]


# --- guards ---------------------------------------------------------------


def test_selector_rejects_a_callable_which_restricts_but_does_not_isolate():
    """The type guard RESTRICTS the interface; it does not prove isolation.

    Rejecting a callable cannot tell whether the supplied coefficients were
    themselves fitted on evaluation outcomes. That is a pipeline property, so it
    is recorded as CoefficientProvenance data and audited -- not inferred here.
    """
    with pytest.raises(TypeError):
        select_bundle(IDS, 2, lambda s: 1.0, unit_cost(IDS))
    leaky = CoefficientProvenance(source="fitted", training_scope="dev+eval",
                                  saw_evaluation_outcomes=True)
    clean = CoefficientProvenance(source="authored", training_scope="none",
                                  saw_evaluation_outcomes=False)
    # Both pass the type guard; only provenance distinguishes them.
    assert leaky.saw_evaluation_outcomes and not clean.saw_evaluation_outcomes


def test_budget_is_respected_including_zero_and_negative_utility():
    est = QuadraticUtility(0.0, {"A": 1.0, "B": 0.5, "C": -0.1}, {("B", "C"): 0.8})
    costs = {"A": 3, "B": 2, "C": 1}
    cost_of = lambda s: sum(costs[i] for i in s)
    assert select_bundle(IDS, 3, est, cost_of) == frozenset(["B", "C"])
    assert select_bundle(IDS, 0, est, cost_of) == frozenset()
    for b in range(7):
        chosen = select_bundle(IDS, b, est, cost_of)
        assert cost_of(chosen) <= b
    only_bad = QuadraticUtility(0.0, {"A": -1.0}, {})
    assert select_bundle(("A",), 1, only_bad, lambda s: len(s)) == frozenset()


def test_candidate_cap_and_input_validation():
    ids = tuple(f"m{i}" for i in range(MAX_CANDIDATES + 1))
    with pytest.raises(ValueError):
        exact_select(ids, 1, lambda s: 0.0, lambda s: len(s))
    with pytest.raises(ValueError):
        exact_select(IDS, -1, lambda s: 0.0, lambda s: len(s))
    with pytest.raises(ValueError):
        exact_select(IDS, True, lambda s: 0.0, lambda s: len(s))


# --- budget accounting the abstract laboratory could not check ------------


CANDS = (Candidate("A", "the wire format is a bare integer"),
         Candidate("B", "the consumer reads it as milliseconds"),
         Candidate("C", "unrelated note about the build cache"))


def test_rendered_cost_exceeds_the_additive_estimate():
    """Separators and header are real budget; the additive figure misses them."""
    subset = frozenset({"A", "B"})
    assert serialised_cost(CANDS, subset) > additive_estimate(CANDS, subset)
    assert serialised_cost(CANDS, frozenset()) == 0
    assert additive_estimate(CANDS, frozenset()) == 0


def test_selection_charged_on_the_rendered_bundle():
    est = QuadraticUtility(0.0, {"A": 0.1, "B": 0.1, "C": 0.0},
                           {("A", "B"): 1.0})
    ids = tuple(c.cid for c in CANDS)
    tight = serialised_cost(CANDS, frozenset({"A", "B"})) - 1
    assert select_bundle(ids, tight, est, lambda s: serialised_cost(CANDS, s)) \
        != frozenset({"A", "B"})
    ok = serialised_cost(CANDS, frozenset({"A", "B"}))
    assert select_bundle(ids, ok, est, lambda s: serialised_cost(CANDS, s)) \
        == frozenset({"A", "B"})


# --- the adapter is opt-in and, by default, inert -------------------------


def test_snapshot_policy_is_a_pass_through_by_default():
    msgs = [{"role": "system", "content": "sys"},
            {"role": "user", "content": "hello there"}]
    p = SnapshotPolicy(candidates=CANDS)
    out = p(list(msgs))
    assert out == msgs                       # unchanged content and order
    assert len(p.snapshots) == 1
    assert p.snapshots[0]["subset"] == []
    assert p.snapshots[0]["budget_unit"] == "rendered_words"
    assert p.calls and p.calls[0]["dropped"] == 0


def test_snapshot_policy_delivers_and_enforces_budget_when_asked():
    msgs = [{"role": "system", "content": "sys"},
            {"role": "user", "content": "what now"}]
    p = SnapshotPolicy(candidates=CANDS, budget=100,
                       deliver=lambda m, c: {"A", "B"})
    out = p(list(msgs))
    assert len(out) == len(msgs) + 1
    assert "wire format" in render_bundle(CANDS, {"A", "B"})
    assert out[-1] == msgs[-1]               # current message stays last
    tight = SnapshotPolicy(candidates=CANDS, budget=1,
                           deliver=lambda m, c: {"A", "B"})
    with pytest.raises(ValueError):
        tight(list(msgs))
