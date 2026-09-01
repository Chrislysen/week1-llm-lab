"""prospective_design_check.py: can this design reach the conclusion it wants?

RUN BEFORE ANY MODEL CALL. Aborts non-zero if the answer is no.

WHY THIS EXISTS. E10 preregistered a SESOI of 0.10 at n = 36 and then reported
an equivalence-supported null. It could not have had one. Bootstrap differences
at n = 36 are multiples of 1/36 = 0.0278, so the attainable interval bounds jump
from +/-0.0833 to +/-0.1111 and a 0.10 bound is UNREACHABLE -- it falls strictly
between two adjacent achievable values. Power at that SESOI was 0.14. Both facts
were computable before a single token was spent, and neither was computed.
See docs/protocols/E10-H3-RETRACTION.md.

So this module answers, in advance and mechanically:

  1. GRANULARITY  -- given the sampling unit and cluster structure, can an
                     interval bound of +/-SESOI even be expressed?
  2. POWER        -- can a true effect at the SESOI be detected?
  3. EQUIVALENCE  -- if the true effect is ~0, will the CI actually land inside
                     +/-SESOI often enough to license the conclusion?

A design that fails (1) can NEVER support an equivalence claim, regardless of
what the data do. That is the failure mode that has to become impossible.

Usage:
    python prospective_design_check.py --units 108 --clusters 36 --sesoi 0.10
    from prospective_design_check import check, require
    require(units=108, clusters=36, sesoi=0.10, conclusion="equivalence")
"""
import argparse
import math
import random
import sys

DEFAULT_REPS = 2000
BOOT_REPS = 2000


def attainable_bounds(units, clusters):
    """The finest interval bound this design can express.

    A cluster bootstrap resamples CLUSTERS, so a difference is a count of units
    over the total unit count. Resolution is 1/units, but the *effective*
    resolution of a cluster resample is coarser: whole clusters move together,
    so the smallest non-zero shift is (units/clusters)/units = 1/clusters.
    Both are reported, and the conservative one governs.
    """
    per_cluster = units / clusters
    return {"unit_resolution": 1.0 / units,
            "cluster_resolution": 1.0 / clusters,
            "units_per_cluster": per_cluster}


def granularity_ok(units, clusters, sesoi):
    """Can a bound of +/-sesoi be expressed at all?

    Requires the SESOI to be at least a few resolution steps away from zero,
    otherwise the interval endpoints straddle it and the equivalence test is
    decided by rounding rather than by data.
    """
    res = 1.0 / clusters                  # conservative
    steps = sesoi / res
    return steps >= 3.0, steps, res


def simulate(units, clusters, true_diff, disc_rate, sesoi,
             reps=DEFAULT_REPS, boot=BOOT_REPS, seed=20260901):
    """Cluster-resampled simulation of the planned analysis.

    Returns (power, equivalence_rate). `power` is P(permutation p < .05);
    `equivalence_rate` is P(cluster-bootstrap 95% CI lies inside +/-sesoi).
    """
    rng = random.Random(seed)
    per = max(1, round(units / clusters))
    q = 0.5 + (true_diff / disc_rate / 2) if disc_rate > 0 else 0.5
    q = min(1.0, max(0.0, q))

    sig = equiv = 0
    for _ in range(reps):
        # Build one dataset: each cluster's units share a cluster effect.
        data = []
        for _ in range(clusters):
            cell = []
            for _ in range(per):
                if rng.random() < disc_rate:
                    cell.append(1 if rng.random() < q else -1)
                else:
                    cell.append(0)
            data.append(cell)
        n = sum(len(c) for c in data)
        obs = sum(sum(c) for c in data) / n

        # cluster permutation
        hits = 0
        PERM = 400
        for _ in range(PERM):
            tot = sum(sum(c) * (1 if rng.random() < 0.5 else -1) for c in data)
            if abs(tot / n) >= abs(obs) - 1e-12:
                hits += 1
        if (hits + 1) / (PERM + 1) < 0.05:
            sig += 1

        # cluster bootstrap CI
        diffs = []
        for _ in range(boot // 10):
            pick = [data[rng.randrange(clusters)] for _ in range(clusters)]
            m = sum(len(c) for c in pick)
            diffs.append(sum(sum(c) for c in pick) / m)
        diffs.sort()
        lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs))]
        if lo > -sesoi and hi < sesoi:
            equiv += 1
    return sig / reps, equiv / reps


def powered_range(units, clusters, sesoi, conclusion="difference",
                  target=0.80, reps=600,
                  grid=(0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30)):
    """The discordance rates at which this design actually reaches `target`.

    POWER FALLS AS DISCORDANCE RISES for a fixed absolute effect: the effect is
    a shift inside the discordant subset, and a larger discordant subset carries
    more variance than signal. So a design is not simply "powered" or not -- it
    has an OPERATING RANGE, and whether a given run lands inside it is not known
    until the run happens.

    Reporting that range up front is what turns "we were underpowered" from a
    post-hoc excuse into a preregistered contingency: a contrast whose observed
    discordance falls outside the range is declared INCONCLUSIVE by rule, not
    reinterpreted as a null.
    """
    out = {}
    for d in grid:
        power, equiv = simulate(units, clusters, sesoi, d, sesoi, reps=reps)
        out[d] = power if conclusion == "difference" else equiv
    ok = [d for d, v in out.items() if v >= target]
    return {"curve": out, "max_disc": max(ok) if ok else None,
            "min_disc": min(ok) if ok else None}


def check(units, clusters, sesoi, disc_rate=0.20, conclusion="both",
          reps=DEFAULT_REPS):
    """Full prospective report. Returns a dict; `ok` says whether to proceed."""
    ok_gran, steps, res = granularity_ok(units, clusters, sesoi)
    bounds = attainable_bounds(units, clusters)

    power, _ = simulate(units, clusters, sesoi, disc_rate, sesoi, reps=reps)
    _, equiv = simulate(units, clusters, 0.0, disc_rate, sesoi, reps=reps)

    need_power = conclusion in ("both", "difference")
    need_equiv = conclusion in ("both", "equivalence")
    ok = ok_gran and (power >= 0.80 or not need_power) \
        and (equiv >= 0.80 or not need_equiv)
    return {"units": units, "clusters": clusters, "sesoi": sesoi,
            "disc_rate": disc_rate, "conclusion": conclusion,
            "cluster_resolution": res, "sesoi_in_resolution_steps": steps,
            "granularity_ok": ok_gran, "power_at_sesoi": power,
            "equivalence_rate_under_null": equiv, "ok": ok, **bounds}


def report(r):
    print(f"  units {r['units']} in {r['clusters']} clusters "
          f"({r['units_per_cluster']:.1f} per cluster)")
    print(f"  SESOI {r['sesoi']}   assumed discordance {r['disc_rate']}")
    print(f"  cluster resolution 1/{r['clusters']} = {r['cluster_resolution']:.4f}"
          f"  -> SESOI is {r['sesoi_in_resolution_steps']:.1f} steps from zero")
    print(f"  GRANULARITY   {'OK' if r['granularity_ok'] else 'FAIL'}"
          f"   (a bound of +/-{r['sesoi']} "
          f"{'can' if r['granularity_ok'] else 'CANNOT'} be expressed)")
    print(f"  POWER at SESOI                    {r['power_at_sesoi']:.2f}")
    print(f"  P(CI inside +/-SESOI | true 0)    "
          f"{r['equivalence_rate_under_null']:.2f}")
    print(f"  VERDICT: {'PROCEED' if r['ok'] else 'ABORT -- DO NOT RUN'}")


def require(units, clusters, sesoi, disc_rate=0.20, conclusion="both",
            reps=DEFAULT_REPS):
    """Abort the caller if the design cannot reach its intended conclusion."""
    r = check(units, clusters, sesoi, disc_rate, conclusion, reps)
    print("=== prospective design check ===")
    report(r)
    if not r["ok"]:
        raise SystemExit(
            "\nABORTED BEFORE ANY MODEL CALL. This design cannot support the "
            f"'{conclusion}' conclusion it was written for. Fix n, the cluster "
            "structure, or the SESOI -- and fix it BEFORE scoring, not after.")
    return r


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--units", type=int)
    p.add_argument("--clusters", type=int)
    p.add_argument("--sesoi", type=float, default=0.10)
    p.add_argument("--disc-rate", type=float, default=0.20)
    p.add_argument("--conclusion", default="both",
                   choices=["both", "difference", "equivalence"])
    p.add_argument("--compare-e10", action="store_true",
                   help="show that this module would have stopped E10")
    a = p.parse_args()

    if a.compare_e10:
        print("=== would this have stopped E10? ===")
        print("\nE10 as run: 36 units, 36 clusters, SESOI 0.10, "
              "observed discordance 4/36 = 0.111")
        r = check(36, 36, 0.10, 0.111, "equivalence", reps=600)
        report(r)
        print("\nE12 as run: 108 units, 36 clusters, SESOI 0.10, "
              "discordance ~0.093")
        r2 = check(108, 36, 0.10, 0.093, "equivalence", reps=600)
        report(r2)
        sys.exit(0)

    if a.units is None or a.clusters is None:
        raise SystemExit("--units and --clusters are required")
    r = check(a.units, a.clusters, a.sesoi, a.disc_rate, a.conclusion)
    print("=== prospective design check ===")
    report(r)
    sys.exit(0 if r["ok"] else 1)
