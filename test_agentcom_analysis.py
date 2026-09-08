"""Estimator diagnostics. Zero model calls; exact rational arithmetic.

Every table here is AUTHORED. These check mechanism, not agent behaviour, and
every fit is computed and evaluated on the same table -- in-sample and
EXPLORATORY by construction.
"""
from fractions import Fraction as F
from itertools import combinations

import pytest

from agentcom_analysis import (additive_can_encode_any_known_target,
                               anchored_fit, anchored_variance,
                               best_feasible, context_headroom, estimator_comparison,
                               evaluate, global_fit, global_fit_variance,
                               max_reconstruction_error)

IDS = ("A", "B", "C", "D")
N = 4
#: The same authored utility as the third-order fixture in the Phase A lab.
TRIPLE = {m: F(4, 5) * ((m & 0b0111) == 0b0111) + F(1, 5) * bool(m & 0b1000)
          for m in range(16)}
FEASIBLE_3 = tuple(m for m in range(16) if bin(m).count("1") <= 3)


def test_global_fit_matches_the_closed_form_and_normal_equations():
    q = global_fit(TRIPLE, N)
    idx = {c: i for i, c in enumerate(IDS)}
    assert q[0] == F(1, 10)
    for c in "ABC":
        assert q[1 << idx[c]] == F(-1, 5)
    assert q[1 << idx["D"]] == F(1, 5)
    for a, b in combinations("ABC", 2):
        assert q[(1 << idx[a]) | (1 << idx[b])] == F(2, 5)
    for c in "ABC":
        assert q[(1 << idx[c]) | (1 << idx["D"])] == F(0)
    # residual is uniform at 1/10: exact reconstruction is impossible here
    assert {abs(TRIPLE[m] - evaluate(q, m)) for m in range(16)} == {F(1, 10)}


def test_reconstruction_error_and_decision_regret_come_apart():
    """The correction the addendum requires: they are different quantities."""
    out = estimator_comparison(TRIPLE, IDS, FEASIBLE_3)
    assert out["optimal"] == ["A", "B", "C"]
    anchored, glob = out["rows"]
    assert anchored["estimator"] == "anchored_degree_2"
    assert anchored["selected"] == ["D"]
    assert anchored["decision_regret"] == F(3, 5)
    assert anchored["max_reconstruction_error"] == F(4, 5)
    assert glob["selected"] == ["A", "B", "C"]
    assert glob["decision_regret"] == 0
    assert glob["max_reconstruction_error"] == F(1, 10)
    # Worse reconstruction, better decision -- neither implies the other.
    assert glob["max_reconstruction_error"] < anchored["max_reconstruction_error"]
    assert glob["decision_regret"] < anchored["decision_regret"]
    assert all(r["in_sample"] for r in out["rows"])


def test_a_third_order_term_does_not_condemn_the_quadratic_CLASS():
    """A large ANCHORED residual is not grounds to discard degree-2 selection."""
    a = anchored_fit(TRIPLE, N)
    assert max_reconstruction_error(TRIPLE, a, N) == F(4, 5)      # anchored fails
    q = global_fit(TRIPLE, N)
    assert best_feasible(lambda m: evaluate(q, m), FEASIBLE_3) == 0b0111  # still decides right


def test_conditional_noise_variance_arithmetic():
    assert anchored_variance(3) == 7
    assert anchored_variance(4) == 31
    assert global_fit_variance(4) == F(11, 16)


def test_context_headroom_is_zero_when_the_optimum_is_shared():
    """Changing pair coefficients is not the same as useful recipient adaptation."""
    masks, feas = range(8), tuple(m for m in range(8) if bin(m).count("1") <= 2)
    same_opt = [{m: s * ((m & 0b011) == 0b011) + F(1, 10) * bool(m & 0b100)
                 for m in masks} for s in (F(3, 5), F(4, 5))]
    assert context_headroom(same_opt, feas) == 0
    moved_opt = [
        {m: F(4, 5) * ((m & 0b011) == 0b011) + F(1, 5) * bool(m & 0b100)
         for m in masks},
        {m: F(4, 5) * bool(m & 0b010) + F(1, 5) * bool(m & 0b100) for m in masks},
    ]
    assert context_headroom(moved_opt, feas) == F(1, 10)


def test_apparent_headroom_arises_from_pure_noise():
    """Exact null: identical contexts, 6 equally good actions, one Bernoulli obs.

    True adaptation gain is 0; the expected APPARENT gain is 301/4096 ~ 7.35%.
    One-decode maxima and in-table policy fits cannot establish held-out value.
    """
    analytic = (F(3, 4) ** 6 + F(1, 4) ** 6) / 2 - F(1, 2) ** 6
    assert analytic == F(301, 4096)
    from itertools import product
    rows = tuple(product((0, 1), repeat=6))
    total = F(0)
    for left in rows:
        for right in rows:
            total += (F(max(left) + max(right), 2)
                      - F(max(a + b for a, b in zip(left, right)), 2))
    assert total / len(rows) ** 2 == F(301, 4096)


def test_any_known_feasible_target_is_additively_encodable():
    """So interaction evidence must be about learnability, not expressibility."""
    for target in FEASIBLE_3:
        assert additive_can_encode_any_known_target(target, N, FEASIBLE_3)


def test_positive_success_scale_interaction_can_vanish_under_a_link():
    """Interaction claims depend on the response scale, so inspect the model."""
    from math import isclose, log
    p = {0: F(1, 5), 1: F(2, 5), 2: F(2, 5), 3: F(4, 5)}
    lp = {m: log(float(v)) for m, v in p.items()}
    assert p[3] - p[1] - p[2] + p[0] == F(1, 5)          # synergy on probability
    assert isclose(lp[3] - lp[1] - lp[2] + lp[0], 0, abs_tol=1e-12)   # none on log
    for budget in range(3):
        feas = tuple(m for m in range(4) if bin(m).count("1") <= budget)
        assert (best_feasible(lambda m: p[m], feas)
                == best_feasible(lambda m: lp[m], feas))


# --- check-level supervision: training only, and its trap -----------------


def test_scorer_already_exposes_check_level_labels_and_failure_kind():
    """No recovery from raw text is needed: PlanCheck is per-constraint."""
    import json

    import lineage_bench as lb
    import lineage_eval as le
    from agentcom_analysis import check_vector, failure_mode

    inst = lb.generate_instance("payments", "join", salt="phaseb-v1")
    cids = [c.id for c in inst.constraints]
    ref = ["PROBE_LATENCY", "CYCLE_ENGINE", "SNAPSHOT_STORE", "SHIFT_ROUTING",
           "REOPEN_GATEWAY", "DRAIN_NODE"]
    ok = le.check_plan(json.dumps({"actions": ref, "ready": True}), inst,
                       constraints=inst.constraints)
    assert failure_mode(ok) == "success"
    assert check_vector(ok, cids) == {c: True for c in cids}

    rev = le.check_plan(json.dumps({"actions": list(reversed(ref)), "ready": True}),
                        inst, constraints=inst.constraints)
    assert failure_mode(rev) == "violation"
    v = check_vector(rev, cids)
    assert any(v.values()) and not all(v.values())   # a genuine near-miss

    refused = le.check_plan(json.dumps({"actions": ref, "ready": False}), inst,
                            constraints=inst.constraints)
    assert failure_mode(refused) == "refusal"        # all checks pass, refused
    assert check_vector(refused, cids) == {c: True for c in cids}

    unparsed = le.check_plan("I refuse.", inst, constraints=inst.constraints)
    assert failure_mode(unparsed) == "unparsed"
    assert check_vector(unparsed, cids) is None      # absent, not all-false

    # "failure" collapses three distinguishable states.
    assert len({failure_mode(x) for x in (rev, refused, unparsed)}) == 3


def test_marginals_and_check_counts_both_fail_to_determine_all_pass():
    """Why a direct success objective is kept as the selection target."""
    from agentcom_analysis import all_pass_is_not_determined_by_marginals
    a = {(True, True): F(3, 4), (False, False): F(1, 4)}
    b = {(True, True): F(1, 2), (True, False): F(1, 4), (False, True): F(1, 4)}
    ra = all_pass_is_not_determined_by_marginals(a)
    rb = all_pass_is_not_determined_by_marginals(b)
    assert ra["marginals"] == rb["marginals"] == [F(3, 4), F(3, 4)]
    assert ra["expected_checks_passed"] == rb["expected_checks_passed"] == F(3, 2)
    assert ra["all_pass"] == F(3, 4) and rb["all_pass"] == F(1, 2)
    # identical marginals AND identical expected checks-passed, different objective
    assert ra["all_pass"] != rb["all_pass"]


def test_training_only_fields_are_named_and_absent_from_the_selection_path():
    import inspect

    from agentcom_analysis import TRAINING_ONLY_FIELDS
    from agentcom_bundle import select_bundle
    src = inspect.getsource(select_bundle)
    for field in TRAINING_ONLY_FIELDS:
        assert field not in src, f"selection path must not read {field}"


# --- questions a complete subset table can answer -------------------------


def test_multiplicity_and_non_monotonicity_are_measurable():
    from agentcom_analysis import (smaller_succeeds_when_full_pool_fails,
                                   working_bundle_multiplicity)
    n = 3
    feas = tuple(range(1 << n))
    # two distinct minimal winners -> "the" sufficient set is not well defined
    succ = {m: (m & 0b011) == 0b011 or (m & 0b101) == 0b101 for m in feas}
    out = working_bundle_multiplicity(succ, feas)
    assert out["n_minimal_successful"] == 2

    # full pool fails while a proper subset succeeds: the case a mining
    # procedure that discards full-pool failures would throw away
    succ2 = {m: bin(m).count("1") == 2 for m in feas}
    nm = smaller_succeeds_when_full_pool_fails(succ2, n)
    assert nm["applicable"] and nm["full_pool_succeeds"] is False
    assert len(nm["witnesses"]) == 3

    succ3 = {m: m == (1 << n) - 1 for m in feas}
    assert smaller_succeeds_when_full_pool_fails(succ3, n)["witnesses"] == []
