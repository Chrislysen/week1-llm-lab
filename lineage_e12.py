"""lineage_e12.py: the adequately-powered independence test.

Protocol: docs/protocols/E12-powered-independence-v1.md.

WHY THIS EXISTS. E10's H3 was reported as a fired kill rule and RETRACTED
(docs/protocols/E10-H3-RETRACTION.md): at n = 36 the design had power 0.14 to
detect an effect at its own SESOI of 0.10, and the equivalence branch was
structurally unreachable because attainable bootstrap bounds jump from 0.0833 to
0.1111 around 0.10. So the load-bearing question was left UNRESOLVED, not
answered. E12 answers it.

HOW n GOES FROM 36 TO 108 WITHOUT INVENTING A SINGLE NEW INSTANCE. Each formal
instance carries 3-4 eligible `before` constraints; E10 and E11 used only the
first. Taking three per instance gives 108 (instance, proposition) units from
the same frozen benchmark.

THE UNITS ARE CLUSTERED AND THE ANALYSIS SAYS SO. Three propositions inside one
instance share a domain, an action vocabulary and a setting. They test DIFFERENT
orderings, but they are not independent draws, and treating 108 clustered units
as 108 independent ones would manufacture exactly the false precision this
experiment exists to avoid. Every interval and every p-value in e12 resamples or
permutes at the INSTANCE level, never the unit level.

Nothing here touches E10's corpus (00947dde8eb0520b) or E11's (5c28ada4c4b899dc);
both are asserted intact by the gate suite.
"""
import hashlib
import random

from lineage_bench import DOMAINS, all_instances
from lineage_e10 import (BASES, T_CONTRADICT, T_FILLER, T_SOURCE, T_SUPPORT,
                         _cap)

SRC_SPEAKER = "Operations Lead"
SUPPORT_SPEAKERS = ["Safety Auditor", "Network Engineer"]
CONTRADICTOR = "Duty Manager"

#: Propositions taken per formal instance. Three is what every instance can
#: supply; taking four where available would unbalance the clusters.
PER_INSTANCE = 3
K = 2                      # matches E10's k, the condition that was retracted

ARMS = ["bare", "filler", "same_root", "indep_root"]
N_ARMS = 4


def eligible(instance):
    """`before` constraints E12 may target, in a fixed order."""
    return [c for c in instance.constraints
            if c.kind == "before" and c.id not in instance.superseded]


def _seed(unit_id):
    return int(hashlib.sha256(f"e12|{unit_id}".encode()).hexdigest()[:8], 16)


def build_unit(instance, constraint):
    """One (instance, proposition) unit."""
    uid = f"{instance.id}:{constraint.id}"
    verbs = dict(DOMAINS[instance.domain]["actions"])
    a, b = verbs[constraint.a], verbs[constraint.b]
    rng = random.Random(_seed(uid))

    off = _seed(uid) % len(BASES)
    bases = tuple(BASES[(off + j) % len(BASES)] for j in range(K + 1))
    picks = rng.sample(T_SUPPORT, K)
    frames = rng.sample(T_FILLER, K)
    noise = DOMAINS[instance.domain]["noise"]

    return {
        "unit": uid, "instance": instance.id, "domain": instance.domain,
        "constraint": constraint.id, "a": constraint.a, "b": constraint.b,
        "bases": bases,
        "source": _cap(T_SOURCE.format(a=a, b=b, basis=bases[0])),
        "same": [_cap(t.format(a=a, b=b, basis=bases[0])) for t in picks],
        "indep": [_cap(t.format(a=a, b=b, basis=bases[j + 1]))
                  for j, t in enumerate(picks)],
        "filler": [f.format(noise=n[0].lower() + n[1:])
                   for f, n in zip(frames, (noise * K)[:K])],
        "contradiction": T_CONTRADICT.format(a=a, b=b),
    }


def all_units():
    out = []
    for inst in all_instances():
        for c in eligible(inst)[:PER_INSTANCE]:
            out.append(build_unit(inst, c))
    return out


def exposure(rec, arm):
    if arm == "bare":
        mid = []
    elif arm == "filler":
        mid = list(rec["filler"])
    elif arm == "same_root":
        mid = list(rec["same"])
    else:
        mid = list(rec["indep"])
    speakers = [SRC_SPEAKER] + SUPPORT_SPEAKERS[:len(mid)] + [CONTRADICTOR]
    return list(zip(speakers, [rec["source"]] + mid + [rec["contradiction"]]))


def render(msgs):
    return "\n".join(f"{s}: {t}" for s, t in msgs)


def corpus_hash():
    parts = []
    for rec in all_units():
        for arm in ARMS:
            parts.append(f"{rec['unit']}|{arm}|" + "|".join(
                f"{s}:{t}" for s, t in exposure(rec, arm)))
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


if __name__ == "__main__":
    units = all_units()
    inst = {u["instance"] for u in units}
    print(f"=== E12 corpus: {len(units)} units in {len(inst)} instance clusters "
          f"x {N_ARMS} arms ===")
    print(f"  hash {corpus_hash()}")
    print(f"  {len(units) * N_ARMS} decider calls per model\n")
    for u in units[:3]:
        print(f"--- {u['unit']} ---")
        print(render(exposure(u, "indep_root")))
        print()
