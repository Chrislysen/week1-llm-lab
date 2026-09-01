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


# ------------------------------------------------------------- E14 ----------
# E14 tests an INTERACTION -- does evidential dependence move the READY
# channel materially more than the ORDERING channel? -- as a paired
# difference-of-differences inside one response. Its power is not the power of
# either channel's test, so it is simulated on its own.

def simulate_interaction(units, clusters, ready_eff, ready_disc, order_eff,
                         order_disc, reps=400, boot=300, seed=20260902):
    """Power of the paired difference-of-differences test.

    Per unit: r = READY(same) - READY(indep) in {-1, 0, +1}, non-zero with
    probability `ready_disc` and positive with the probability that yields a
    mean of `ready_eff`; o likewise for ORDERING. delta = r - o. Returns
    P(cluster-bootstrap 95% CI lower bound of mean delta > 0), which is the
    preregistered criterion for "READY moves more than ORDERING".
    """
    rng = random.Random(seed)
    per = max(1, round(units / clusters))
    qr = min(1.0, max(0.0, 0.5 + (ready_eff / ready_disc / 2 if ready_disc else 0)))
    qo = min(1.0, max(0.0, 0.5 + (order_eff / order_disc / 2 if order_disc else 0)))
    hits = 0
    for _ in range(reps):
        data = []
        for _ in range(clusters):
            cell = []
            for _ in range(per):
                r = (1 if rng.random() < qr else -1) if rng.random() < ready_disc else 0
                o = (1 if rng.random() < qo else -1) if rng.random() < order_disc else 0
                cell.append(r - o)
            data.append(cell)
        diffs = []
        for _ in range(boot):
            pick = [data[rng.randrange(clusters)] for _ in range(clusters)]
            m = sum(len(c) for c in pick)
            diffs.append(sum(sum(c) for c in pick) / m)
        diffs.sort()
        hits += diffs[int(0.025 * boot)] > 0
    return hits / reps


#: The discordance ranges E14 must be powered over, fixed from the E13
#: discovery data as PLAUSIBILITY only (E13 READY discordance ran 0.19-0.31
#: across arms; ORDERING ran 0.07-0.15). Wider than observed on purpose.
E14_PLAUSIBLE = {"primary": (0.15, 0.40),
                 "interaction": (0.15, 0.35),
                 "equivalence": (0.05, 0.15)}
E14_ORDER_DISC = 0.09          # ORDERING discordance assumed for the DoD sim


def _band(curve, target):
    """Contiguous grid points at or above `target`, or None."""
    ok = sorted(d for d, v in curve.items() if v >= target)
    if not ok:
        return None
    grid = sorted(curve)
    lo, hi = grid.index(ok[0]), grid.index(ok[-1])
    if grid[lo:hi + 1] != ok:
        return None                    # a hole in the middle: not one band
    return (ok[0], ok[-1])


def _covers(band, need):
    return band is not None and band[0] <= need[0] and band[1] >= need[1]


def check_e14(units, clusters, sesoi=0.10, target=0.80, reps=500,
              grid=(0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50),
              eq_grid=(0.05, 0.08, 0.10, 0.12, 0.15, 0.20)):
    """Can this design reach E14's three preregistered readings?

      PRIMARY       FIXED-plan READY difference at the SESOI
      INTERACTION   READY-minus-ORDERING difference-of-differences, with a
                    READY effect at the SESOI and a null ORDERING effect
      EQUIVALENCE   ORDERING control: CI inside +/-SESOI under a true zero

    Each is reported as an OPERATING BAND of observed discordance, and the
    design passes only if every band covers its plausible range.
    """
    ok_gran, steps, res = granularity_ok(units, clusters, sesoi)
    primary = {d: simulate(units, clusters, sesoi, d, sesoi, reps=reps)[0]
               for d in grid}
    inter = {d: simulate_interaction(units, clusters, sesoi, d, 0.0,
                                     E14_ORDER_DISC, reps=reps) for d in grid}
    equiv = {d: simulate(units, clusters, 0.0, d, sesoi, reps=reps)[1]
             for d in eq_grid}
    bands = {"primary": _band(primary, target),
             "interaction": _band(inter, target),
             "equivalence": _band(equiv, target)}
    ok = ok_gran and all(_covers(bands[k], E14_PLAUSIBLE[k]) for k in bands)
    return {"units": units, "clusters": clusters, "sesoi": sesoi,
            "target": target, "granularity_ok": ok_gran,
            "sesoi_in_resolution_steps": steps, "cluster_resolution": res,
            "primary_curve": primary, "interaction_curve": inter,
            "equivalence_curve": equiv, "bands": bands,
            "plausible": E14_PLAUSIBLE, "ok": ok}


def report_e14(r):
    print(f"  units {r['units']} in {r['clusters']} clusters   SESOI {r['sesoi']}"
          f"   target {r['target']}")
    print(f"  GRANULARITY   {'OK' if r['granularity_ok'] else 'FAIL'}"
          f"   (SESOI is {r['sesoi_in_resolution_steps']:.1f} resolution steps "
          f"from zero)")
    for name, curve in (("PRIMARY     fixed READY, power at SESOI", r["primary_curve"]),
                        ("INTERACTION DoD, READY at SESOI vs ORDERING null",
                         r["interaction_curve"]),
                        ("EQUIVALENCE ORDERING, CI inside +/-SESOI | true 0",
                         r["equivalence_curve"])):
        key = name.split()[0].lower()
        print(f"\n  {name}")
        print("    " + "  ".join(f"{d:.2f}:{v:.2f}" for d, v in sorted(curve.items())))
        b = r["bands"][key]
        need = r["plausible"][key]
        print(f"    operating band {b}   must cover {need}   "
              f"{'OK' if _covers(b, need) else 'FAIL'}")
    print(f"\n  VERDICT: {'PROCEED' if r['ok'] else 'ABORT -- DO NOT RUN'}")


def self_test():
    """FALSIFICATION TESTS. A checker that cannot fail is not a checker.

    Each case has a known right answer that does not depend on this project's
    data, so the module can be validated independently of any experiment.
    """
    cases = []

    # 1. The historical failure it exists to prevent.
    r = check(36, 36, 0.10, 0.111, "equivalence", reps=400)
    cases.append(("E10 config must ABORT", not r["ok"]))
    cases.append(("E10 power must be far below 0.80", r["power_at_sesoi"] < 0.4))

    # 2. A design that is obviously fine must PROCEED.
    r = check(2000, 500, 0.10, 0.10, "difference", reps=200)
    cases.append(("large design must PROCEED", r["ok"]))

    # 3. Granularity must fail when the SESOI is finer than the resolution.
    ok, steps, res = granularity_ok(20, 20, 0.02)
    cases.append(("SESOI below resolution must fail granularity", not ok))
    ok, _, _ = granularity_ok(2000, 500, 0.10)
    cases.append(("coarse SESOI on a fine grid must pass", ok))

    # 4. Power must be monotone in n at fixed discordance.
    p_small, _ = simulate(36, 36, 0.10, 0.10, 0.10, reps=300)
    p_big, _ = simulate(216, 72, 0.10, 0.10, 0.10, reps=300)
    cases.append(("power must rise with n", p_big > p_small))

    # 5. A true zero effect must NOT be called significant more than ~alpha.
    p_null, _ = simulate(108, 36, 0.0, 0.10, 0.10, reps=400)
    cases.append(("false-positive rate near alpha", p_null <= 0.12))

    # 6. E14's interaction test: power must rise with n ...
    i_small = simulate_interaction(108, 36, 0.10, 0.27, 0.0, 0.09, reps=150)
    i_big = simulate_interaction(432, 144, 0.10, 0.27, 0.0, 0.09, reps=150)
    cases.append(("interaction power must rise with n", i_big > i_small))
    # ... and must NOT fire when both channels move equally.
    i_fp = simulate_interaction(324, 108, 0.10, 0.27, 0.10, 0.09, reps=200)
    cases.append(("interaction false-positive near alpha when channels move "
                  "equally", i_fp <= 0.08))
    # 7. E13's own configuration could not have CONFIRMED the READY effect.
    r = check_e14(108, 36, reps=120)
    cases.append(("E13 config (108/36) must ABORT for E14", not r["ok"]))

    print("=== prospective_design_check self-test ===")
    bad = 0
    for name, ok in cases:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}")
        bad += not ok
    print(f"\n  {len(cases) - bad}/{len(cases)} passed")
    return bad == 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--units", type=int)
    p.add_argument("--clusters", type=int)
    p.add_argument("--sesoi", type=float, default=0.10)
    p.add_argument("--disc-rate", type=float, default=0.20)
    p.add_argument("--conclusion", default="both",
                   choices=["both", "difference", "equivalence"])
    p.add_argument("--compare-e10", action="store_true",
                   help="show that this module would have stopped E10")
    p.add_argument("--e14", action="store_true",
                   help="E14: primary / interaction / equivalence bands")
    p.add_argument("--reps", type=int, default=DEFAULT_REPS)
    a = p.parse_args()

    if a.self_test:
        raise SystemExit(0 if self_test() else 1)

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
    if a.e14:
        r = check_e14(a.units, a.clusters, a.sesoi, reps=a.reps)
        print("=== prospective design check: E14 ===")
        report_e14(r)
        sys.exit(0 if r["ok"] else 1)
    r = check(a.units, a.clusters, a.sesoi, a.disc_rate, a.conclusion)
    print("=== prospective design check ===")
    report(r)
    sys.exit(0 if r["ok"] else 1)
