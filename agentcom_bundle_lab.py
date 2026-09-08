#!/usr/bin/env python3
"""A deterministic mechanism check for a proposed AgentCom research direction.

No LLM, network, learned model, repository integration, or empirical agent result.
Utilities below are authored mathematical functions, and costs are abstract units.
The selector accepts coefficients; learning reliable coefficients is unsolved here.

Run: python agentcom_bundle_lab.py

PROVENANCE: supplied verbatim with the AgentCom bundle specification
(2026-09-08) and committed unchanged as the Phase A reference artifact. Its
fixtures are ported into `test_agentcom_bundle.py` against this repo's
`agentcom_bundle` module; keeping the original here makes that port auditable.
Not imported by any repo module. Not collected by pytest.
"""

from dataclasses import dataclass
from itertools import combinations
import json
import math
from typing import Callable, FrozenSet, Mapping


Coalition = FrozenSet[str]
Utility = Callable[[Coalition], float]


def subsets(ids: tuple[str, ...]):
    for size in range(len(ids) + 1):
        for group in combinations(ids, size):
            yield frozenset(group)


@dataclass(frozen=True)
class QuadraticUtility:
    base: float
    unary: Mapping[str, float]
    pairs: Mapping[tuple[str, str], float]

    def __call__(self, selected: Coalition) -> float:
        return (
            self.base
            + sum(self.unary[i] for i in selected)
            + sum(v for (i, j), v in self.pairs.items() if i in selected and j in selected)
        )


def quadratic_from_oracle(ids: tuple[str, ...], utility: Utility) -> QuadraticUtility:
    """Known degree-2 anchored set-function expansion; this is NOT a learner.

    Calls the supplied mathematical utility on empty, singleton, and pair sets.
    Equality with the full utility requires zero higher-order residuals.
    """
    base = utility(frozenset())
    unary = {i: utility(frozenset([i])) - base for i in ids}
    pairs = {
        (i, j): utility(frozenset([i, j])) - base - unary[i] - unary[j]
        for i, j in combinations(sorted(ids), 2)
    }
    return QuadraticUtility(base, unary, pairs)


def validate_inputs(costs: Mapping[str, int], budget: int):
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    if len(costs) > 16:
        raise ValueError("exact prototype is deliberately limited to 16 candidates")
    if any(not isinstance(i, str) or not i for i in costs):
        raise ValueError("candidate IDs must be nonempty strings")
    if any(isinstance(c, bool) or not isinstance(c, int) or c <= 0 for c in costs.values()):
        raise ValueError("each candidate must have positive integer cost")


def exact_select(costs: Mapping[str, int], budget: int, utility: Utility) -> Coalition:
    """Maximise supplied utility under a hard budget, including the empty set.

    Exact enumeration is suitable only for the small mechanism laboratory.
    Ties prefer lower cost, then lexicographically earlier IDs.
    """
    validate_inputs(costs, budget)
    best = frozenset()
    best_key = None
    for selected in subsets(tuple(sorted(costs))):
        cost = sum(costs[i] for i in selected)
        if cost > budget:
            continue
        score = float(utility(selected))
        if not math.isfinite(score):
            raise ValueError("utility must be finite")
        key = (-score, cost, tuple(sorted(selected)))
        if best_key is None or key < best_key:
            best, best_key = selected, key
    return best


def select_bundle(costs: Mapping[str, int], budget: int, estimate: QuadraticUtility):
    """Deployment-shaped interface: no oracle or task answer is accepted here."""
    if set(estimate.unary) != set(costs):
        raise ValueError("unary coefficients must match all candidate IDs")
    for key in estimate.pairs:
        if len(key) != 2 or key[0] >= key[1] or any(i not in costs for i in key):
            raise ValueError("pairs must contain two distinct, sorted, known IDs")
    values = [estimate.base, *estimate.unary.values(), *estimate.pairs.values()]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("coefficients must be finite")
    return exact_select(costs, budget, estimate)


def conditional_greedy(costs: Mapping[str, int], budget: int, utility: Utility):
    """Strong singleton comparator: recompute exact marginal utility after each add.

    It stops when no affordable individual addition has positive marginal value.
    This is not an implementation of RepoShapley, C3, or a general set policy.
    """
    validate_inputs(costs, budget)
    selected = frozenset()
    while True:
        remaining = budget - sum(costs[i] for i in selected)
        current = utility(selected)
        offers = [
            ((utility(selected | {i}) - current) / costs[i], i)
            for i in sorted(costs) if i not in selected and costs[i] <= remaining
        ]
        if not offers:
            return selected
        gain, chosen = sorted(offers, key=lambda p: (-p[0], p[1]))[0]
        if gain <= 1e-12:
            return selected
        selected = selected | {chosen}


@dataclass(frozen=True)
class Fixture:
    name: str
    ids: tuple[str, ...]
    budget: int
    utility: Utility
    meaning: str


def fixtures():
    return [
        Fixture("pair_needed", ("A", "B", "C"), 2,
                lambda s: 0.8 * ({"A", "B"} <= s) + 0.2 * ("C" in s),
                "A and B jointly solve one subtask; C independently solves another."),
        Fixture("recipient_already_has_A", ("A", "B", "C"), 2,
                lambda s: 0.8 * ("B" in s) + 0.2 * ("C" in s),
                "Same offered messages; the recipient now already has A's information."),
        Fixture("recipient_already_has_B", ("A", "B", "C"), 2,
                lambda s: 0.8 * ("A" in s) + 0.2 * ("C" in s),
                "Same offered messages; the recipient instead already has B's information."),
        Fixture("independent_benefits", ("A", "B", "C"), 2,
                lambda s: sum({"A": 0.5, "B": 0.3, "C": 0.2}[i] for i in s),
                "No pair interactions: the bundle model should add no benefit."),
        Fixture("negative_interaction", ("A", "B", "C"), 2,
                lambda s: 0.4 * ("A" in s) + 0.4 * ("B" in s)
                          + 0.2 * ("C" in s) - 0.7 * ({"A", "B"} <= s),
                "A and B each help alone but interfere together."),
        Fixture("third_order_failure", ("A", "B", "C", "D"), 3,
                lambda s: 0.8 * ({"A", "B", "C"} <= s) + 0.2 * ("D" in s),
                "The required triple has no singleton or pair benefit; degree 2 misses it."),
        Fixture("budget_one", ("A", "B", "C"), 1,
                lambda s: 0.3 * ("A" in s) + 0.7 * ({"B", "C"} <= s),
                "Best set at budget 1 is A."),
        Fixture("budget_two", ("A", "B", "C"), 2,
                lambda s: 0.3 * ("A" in s) + 0.7 * ({"B", "C"} <= s),
                "Best set at budget 2 is BC: it need not extend the smaller-budget set."),
    ]


def run_lab():
    rows = []
    for fixture in fixtures():
        costs = {i: 1 for i in fixture.ids}
        estimate = quadratic_from_oracle(fixture.ids, fixture.utility)
        greedy = conditional_greedy(costs, fixture.budget, fixture.utility)
        bundle = select_bundle(costs, fixture.budget, estimate)
        oracle = exact_select(costs, fixture.budget, fixture.utility)
        residual = max(abs(fixture.utility(s) - estimate(s)) for s in subsets(fixture.ids))
        rows.append({
            "fixture": fixture.name,
            "meaning": fixture.meaning,
            "budget_abstract_units": fixture.budget,
            "greedy_set": sorted(greedy),
            "greedy_true_authored_utility": round(fixture.utility(greedy), 6),
            "bundle_set": sorted(bundle),
            "bundle_true_authored_utility": round(fixture.utility(bundle), 6),
            "full_set_oracle": sorted(oracle),
            "oracle_true_authored_utility": round(fixture.utility(oracle), 6),
            "max_degree_two_residual_all_subsets": round(residual, 6),
        })

    by_name = {row["fixture"]: row for row in rows}
    assert by_name["pair_needed"]["bundle_set"] == ["A", "B"]
    assert by_name["pair_needed"]["greedy_set"] == ["C"]
    assert by_name["recipient_already_has_A"]["bundle_set"] == ["B", "C"]
    assert by_name["recipient_already_has_B"]["bundle_set"] == ["A", "C"]
    assert by_name["independent_benefits"]["bundle_set"] == ["A", "B"]
    assert by_name["third_order_failure"]["bundle_set"] == ["D"]
    assert by_name["third_order_failure"]["full_set_oracle"] == ["A", "B", "C"]
    assert by_name["budget_one"]["bundle_set"] == ["A"]
    assert by_name["budget_two"]["bundle_set"] == ["B", "C"]

    # Separate budget and signed-coefficient checks with non-unit costs.
    costs = {"A": 3, "B": 2, "C": 1}
    estimate = QuadraticUtility(0, {"A": 1.0, "B": 0.5, "C": -0.1}, {("B", "C"): 0.8})
    assert select_bundle(costs, 3, estimate) == frozenset(["B", "C"])
    assert select_bundle(costs, 0, estimate) == frozenset()
    negative = QuadraticUtility(0, {"A": -1.0}, {})
    assert select_bundle({"A": 1}, 1, negative) == frozenset()
    for budget in range(7):
        chosen = select_bundle(costs, budget, estimate)
        assert sum(costs[i] for i in chosen) <= budget

    return {
        "status": "DETERMINISTIC MECHANISM CHECK ONLY",
        "model_calls": 0,
        "learned_coefficients": False,
        "cost_unit": "abstract units, not measured model tokens",
        "warning": "Authored utilities encode the examples by construction. These are not agent results or novel theorems.",
        "checks": "Fixture behavior, negative utility, zero budget, and non-unit hard budgets passed.",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run_lab(), indent=2, sort_keys=True))
