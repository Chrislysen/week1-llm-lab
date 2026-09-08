"""agentcom_analysis.py: estimator diagnostics over COMPLETE subset tables.

ZERO MODEL CALLS. Exact rational arithmetic. Every table this module is tested
on is an AUTHORED mathematical example, not a model observation.

WHY THIS EXISTS
---------------
`agentcom_bundle.anchored_expansion` truncates the empty-set-anchored Mobius
expansion at degree 2. On a table with a genuine third-order term it can pick a
badly wrong bundle. That failure is real -- and it is a failure **of the anchored
estimator**, not of the degree-2 *class*. A uniform least-squares degree-2
projection of the same authored table selects the correct bundle while still
being unable to reconstruct the surface exactly.

Reconstruction error and decision regret are therefore DIFFERENT quantities and
are reported separately. A large anchored residual is not on its own grounds to
declare the quadratic class useless.

SCOPE, STATED ONCE
------------------
Any fit computed on a table and evaluated on that same table is **exploratory
and in-sample**. It establishes nothing about unseen tasks, and `global_fit`
needs the complete table, so it is a diagnostic and not a deployable learner.
"""
from fractions import Fraction
from itertools import combinations
from math import comb

__all__ = ["TRAINING_ONLY_FIELDS", "check_vector", "failure_mode",
           "all_pass_is_not_determined_by_marginals",
           "working_bundle_multiplicity", "smaller_succeeds_when_full_pool_fails",
           "index_map", "mask_of", "names_of", "anchored_fit", "global_fit",
           "evaluate", "max_reconstruction_error", "best_feasible",
           "estimator_comparison", "anchored_variance", "global_fit_variance",
           "context_headroom", "additive_can_encode_any_known_target"]


def index_map(ids):
    return {c: i for i, c in enumerate(sorted(ids))}


def mask_of(subset, idx):
    m = 0
    for c in subset:
        m |= 1 << idx[c]
    return m


def names_of(mask, ids):
    order = sorted(ids)
    return [order[i] for i in range(len(order)) if mask >> i & 1]


def _contained(term, mask):
    return (term & mask) == term


def _low_terms(n, degree=2):
    return tuple(t for t in range(1 << n) if bin(t).count("1") <= degree)


def evaluate(coeffs, mask):
    return sum((v for t, v in coeffs.items() if _contained(t, mask)),
               Fraction(0))


def anchored_fit(table, n):
    """Degree-2 truncation of the empty-set-anchored Mobius expansion.

    Uses only the empty set, singletons and pairs -- 11 of 16 cells at n=4.
    This is what `agentcom_bundle.anchored_expansion` computes.
    """
    out = {}
    for t in _low_terms(n):
        out[t] = sum(((-1) ** (bin(t).count("1") - bin(u).count("1")) * table[u]
                      for u in range(1 << n) if _contained(u, t)), Fraction(0))
    return out


def _character(term, mask):
    """Product of z_i = 2*x_i - 1 over i in `term`."""
    return (-1) ** bin(term & ~mask).count("1")


def global_fit(table, n):
    """Uniform least-squares degree-2 projection over the COMPLETE cube.

    Walsh characters are orthogonal on the balanced design, so the projection is
    a coefficient-wise truncation; the result is then converted back to the
    ordinary 0/1 monomial basis. The normal equations are verified exactly
    before returning, so a silent basis-conversion error cannot pass.

    Requires every one of the 2**n cells. Not a held-out learner.
    """
    terms = _low_terms(n)
    walsh = {t: sum((table[m] * _character(t, m) for m in range(1 << n)),
                    Fraction(0)) / (1 << n) for t in terms}
    coeffs = {t: Fraction(0) for t in terms}
    for t, w in walsh.items():
        for u in terms:
            if _contained(u, t):
                coeffs[u] += (w * 2 ** bin(u).count("1")
                              * (-1) ** (bin(t).count("1") - bin(u).count("1")))
    for t in terms:
        residual = sum((table[m] - evaluate(coeffs, m)
                        for m in range(1 << n) if _contained(t, m)), Fraction(0))
        if residual != 0:
            raise AssertionError(f"normal equation violated for term {t}")
    return coeffs


def max_reconstruction_error(table, coeffs, n):
    return max(abs(table[m] - evaluate(coeffs, m)) for m in range(1 << n))


def best_feasible(score, feasible):
    """Argmax over feasible masks; ties -> fewer members, then lower mask."""
    return min(feasible, key=lambda m: (-score(m), bin(m).count("1"), m))


def estimator_comparison(table, ids, feasible):
    """Anchored vs global degree-2 on ONE complete table.

    Reports reconstruction error and the bundle each estimator actually selects,
    because they can disagree: an estimator may reconstruct badly and still
    decide well, or vice versa.

    EXPLORATORY: fitted and evaluated on the same table.
    """
    n = len(ids)
    optimal = best_feasible(lambda m: table[m], feasible)
    rows = []
    for name, coeffs in (("anchored_degree_2", anchored_fit(table, n)),
                         ("global_least_squares_degree_2", global_fit(table, n))):
        chosen = best_feasible(lambda m: evaluate(coeffs, m), feasible)
        rows.append({
            "estimator": name,
            "selected": names_of(chosen, ids),
            "true_value_of_selected": table[chosen],
            "decision_regret": table[optimal] - table[chosen],
            "max_reconstruction_error": max_reconstruction_error(table, coeffs, n),
            "in_sample": True,
        })
    return {"optimal": names_of(optimal, ids),
            "true_optimal_value": table[optimal], "rows": rows}


# --- conditional noise arithmetic (assumptions stated, not assumed away) ---


def anchored_variance(k):
    """Var of the anchored prediction at a size-k set, in units of sigma^2.

    ASSUMES independent, equal-variance cell noise and a correct quadratic mean.
    Neither is established for a receiver. 7 at k=3, 31 at k=4.
    """
    return Fraction(((k - 1) * (k - 2) // 2) ** 2 + k * (k - 2) ** 2 + comb(k, 2))


def global_fit_variance(n):
    """Var of the global degree-2 fitted mean per cell, in units of sigma^2.

    Same assumptions as `anchored_variance`. 11/16 for n=4. The anchored form
    reads 11 of 16 cells; the global fit reads all 16, which Phase B collects
    anyway -- a reason to COMPARE procedures, not a measured improvement.
    """
    return Fraction(sum(comb(n, d) for d in range(3)), 1 << n)


# --- recipient-context value of information --------------------------------


def context_headroom(tables, feasible):
    """Gain a context-aware chooser could have over one shared choice.

    ZERO when the contexts share an optimal bundle, even if their pair
    coefficients differ -- changing interaction coefficients is NOT the same as
    valuable recipient adaptation. Feasible sets must MATCH across contexts, or
    a difference in affordability is mistaken for a difference in information.
    """
    k = len(tables)
    adaptive = sum((max(t[m] for m in feasible) for t in tables), Fraction(0)) / k
    shared = max(sum((t[m] for t in tables), Fraction(0)) / k for m in feasible)
    return adaptive - shared


def additive_can_encode_any_known_target(target, n, feasible):
    """An ALREADY-KNOWN feasible target is selectable by additive weights alone.

    +1 to members, -1 to non-members. This uses the answer, so it learns nothing
    and reconstructs nothing -- it is the reason evidence for explicit
    interactions must be about learnability and generalisation, never about the
    mere existence of an additive-vs-quadratic policy at one fixed cell.
    """
    w = {1 << i: Fraction(1 if target >> i & 1 else -1) for i in range(n)}
    return best_feasible(lambda m: evaluate(w, m), feasible) == target


# --- check-level supervision (TRAINING ONLY) ------------------------------

#: Fields that are TRAINING information only. The deployed selector chooses on
#: predicted overall task success under the rendered budget and never reads
#: these. Kept as a named list so the boundary is auditable rather than assumed.
TRAINING_ONLY_FIELDS = ("check_vector", "failure_mode", "constraint_recall")


def check_vector(plan_check, constraint_ids):
    """Per-check pass/fail from an existing `PlanCheck`. TRAINING ONLY.

    The scorer already exposes this: `satisfied` / `violated` are per-constraint,
    so no recovery from raw text is needed. An unparsed output has no check
    vector at all -- that is a distinct state, not a row of zeros, so it returns
    None rather than pretending every check failed.
    """
    if not plan_check.parsed:
        return None
    sat = set(plan_check.satisfied)
    return {cid: (cid in sat) for cid in constraint_ids}


def failure_mode(plan_check):
    """Which KIND of failure, not merely that one occurred. TRAINING ONLY.

    'failure' collapses four states this instrument can already separate:
      success   -- every check passes and the plan is offered as ready
      unparsed  -- no scoreable action was produced
      violation -- a scoreable plan that breaks at least one check
      refusal   -- every check passes but `ready` is false
    B1 measured the last two as very different behaviours (16/18 invalid plans
    were emitted silently as ready=true; 2/18 were self-flagged).
    """
    if not plan_check.parsed:
        return "unparsed"
    if plan_check.violated:
        return "violation"
    if not plan_check.ready:
        return "refusal"
    return "success"


def all_pass_is_not_determined_by_marginals(joint):
    """Diagnostic: two check distributions with equal marginals, unequal joint.

    `joint` maps outcome-tuples of booleans to probabilities. Returns the
    marginals, the all-pass probability and the expected number of checks passed.

    The authored pair in the tests has IDENTICAL marginals AND identical expected
    checks-passed, yet different all-pass rates -- so neither multiplying
    marginals nor rewarding more passed checks recovers the selection objective.
    Keep a direct success objective.
    """
    k = len(next(iter(joint)))
    marginals = [sum((p for o, p in joint.items() if o[i]), Fraction(0))
                 for i in range(k)]
    all_pass = sum((p for o, p in joint.items() if all(o)), Fraction(0))
    expected = sum((p * sum(o) for o, p in joint.items()), Fraction(0))
    return {"marginals": marginals, "all_pass": all_pass,
            "expected_checks_passed": expected}


# --- questions a COMPLETE subset table can answer -------------------------


def working_bundle_multiplicity(success, feasible):
    """How many feasible bundles succeed, and which succeed minimally.

    A minimal successful bundle has no successful proper subset that is also
    feasible. Relevant because Context-Picker mines ONE sufficient set by
    repeated removal; if several distinct bundles work, 'the' sufficient set is
    not well defined and coverage-of-one-set is a lossy training target.
    """
    winners = [m for m in feasible if success[m]]
    minimal = [m for m in winners
               if not any(w != m and (w & m) == w and success[w] for w in winners)]
    return {"n_feasible": len(feasible), "n_successful": len(winners),
            "n_minimal_successful": len(minimal), "minimal_masks": minimal}


def smaller_succeeds_when_full_pool_fails(success, n, feasible=None):
    """Does some proper subset succeed where the FULL pool fails?

    Exactly the case Context-Picker's mining discards. If it occurs, dropping
    those instances is not a neutral preprocessing step, and more evidence is not
    monotonically better.
    """
    full = (1 << n) - 1
    if feasible is None:
        feasible = tuple(range(1 << n))
    if full not in success or success[full]:
        return {"applicable": full in success and not success[full],
                "full_pool_succeeds": success.get(full), "witnesses": []}
    wit = [m for m in feasible if m != full and (m & full) == m and success[m]]
    return {"applicable": True, "full_pool_succeeds": False, "witnesses": wit}
