"""ffep_power.py: prospective attainability for the FFEP estimand. No model.

THE ESTIMAND. Units are (instance, claim-target) pairs on which the agent
PASSED the original evaluation. On the paired counterfactual each such unit
is scored mechanically as one of

    P   the plan follows the capability's prediction
    S   the plan follows the shortcut's prediction
    N   neither

The quantity of interest is pi_S = P(S | original pass): how often success
on the original was produced by the shortcut. The capability claim is
UNDERDETERMINED to the degree pi_S is materially above zero, and the
original evaluation is said to IDENTIFY the capability only if pi_S is
bounded below a preregistered SESOI. Both directions therefore need
attainability: detecting pi_S >= SESOI, and bounding pi_S < SESOI.

Units cluster in instances (up to 3-4 claim-targets per instance share a
domain, an action vocabulary and a setting), so intervals inflate by a
design effect 1 + (m - 1) * ICC. Exact Clopper-Pearson bounds are computed
on the effective n.

Run:  python ffep_power.py
"""
import math

SESOI = 0.10


def _tail_ge(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial interval by bisection on the binomial tails (no scipy)."""
    def solve(target_fn):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if target_fn(mid):
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    lo = 0.0 if k == 0 else solve(lambda p: _tail_ge(k, n, p) >= alpha / 2)
    hi = 1.0 if k == n else solve(lambda p: 1 - _tail_ge(k + 1, n, p) <= alpha / 2)
    return lo, hi


def effective_n(n_units, units_per_cluster, icc):
    return n_units / (1 + (units_per_cluster - 1) * icc)


def power_detect(n_eff, true_pi, sesoi=SESOI, alpha=0.05):
    """Power that the exact lower bound exceeds 0 AND the point estimate >= SESOI,
    i.e. the reading 'the shortcut is followed at a material rate'."""
    n = int(round(n_eff))
    hits = 0.0
    for k in range(n + 1):
        pk = math.comb(n, k) * true_pi ** k * (1 - true_pi) ** (n - k)
        lo, _ = clopper_pearson(k, n, alpha)
        if lo > 0 and k / n >= sesoi:
            hits += pk
    return hits


def power_bound(n_eff, true_pi, sesoi=SESOI, alpha=0.05):
    """Power that the exact upper bound falls below the SESOI, i.e. the
    reading 'the original evaluation identifies the capability'."""
    n = int(round(n_eff))
    hits = 0.0
    for k in range(n + 1):
        pk = math.comb(n, k) * true_pi ** k * (1 - true_pi) ** (n - k)
        _, hi = clopper_pearson(k, n, alpha)
        if hi < sesoi:
            hits += pk
    return hits


if __name__ == "__main__":
    print(f"SESOI on pi_S = {SESOI}")
    print("\nCI half-width resolution (Clopper-Pearson, 95%) at k/n = 0.2:")
    for n in (36, 54, 72, 108, 144, 216, 324):
        lo, hi = clopper_pearson(round(0.2 * n), n)
        print(f"  n={n:<4} [{lo:.3f}, {hi:.3f}]  width {hi - lo:.3f}")
    print("\nPower to DETECT pi_S >= SESOI (lower bound > 0 and estimate >= 0.10)")
    print("  rows: effective n; columns: true pi_S")
    pis = (0.10, 0.15, 0.20, 0.30)
    print("  n_eff  " + "  ".join(f"{p:>5.2f}" for p in pis))
    for n in (36, 54, 72, 108, 144, 216):
        print(f"  {n:<6} " + "  ".join(f"{power_detect(n, p):>5.2f}" for p in pis))
    print("\nPower to BOUND pi_S < SESOI (upper bound < 0.10) when the truth is small")
    pis = (0.0, 0.02, 0.05)
    print("  n_eff  " + "  ".join(f"{p:>5.2f}" for p in pis))
    for n in (36, 54, 72, 108, 144, 216, 324):
        print(f"  {n:<6} " + "  ".join(f"{power_bound(n, p):>5.2f}" for p in pis))
    print("\nDesign effect: effective n for m claim-targets per instance cluster")
    for n, m in ((108, 3), (144, 4), (216, 3), (432, 3)):
        for icc in (0.1, 0.3, 0.5):
            print(f"  n={n} m={m} icc={icc}: n_eff={effective_n(n, m, icc):.0f}")
    print("\nEligible-pool shrinkage: only units that PASSED the original count.")
    for pass_rate in (0.3, 0.5, 0.7):
        for n in (108, 216, 432):
            print(f"  pass {pass_rate}: n={n} -> eligible {n * pass_rate:.0f}")
