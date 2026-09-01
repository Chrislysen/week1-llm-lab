"""lineage_e11.py: the multiplicity sweep. Is E10's null a k=2 artifact?

Protocol: docs/protocols/E11-multiplicity-v1.md. Preregistered before any
decider call.

WHAT THIS DISCRIMINATES, in one sentence: whether the model assigns ZERO weight
to evidential independence, or whether two agreeing messages already saturate
resistance so that any manipulation at k=2 would have shown nothing.

E10 measured `same_root` against `indep_root` at exactly k=2 support messages
and found a paired difference of +0.0000. That is either a fact about the model
or a fact about the number 2. This sweep varies k across 1, 2 and 3 and reads
the two curves against each other.

    same_k     source(b0) + k support messages, ALL citing b0        1 root
    indep_k    source(b0) + k support messages, citing b1..bk        k+1 roots
    filler_k   source(b0) + k constraint-irrelevant messages         0 roots
    bare       source(b0) alone                                      1 root

THE CONSTRUCTION IS NESTED, which matters. Templates, bases, speakers and filler
frames are drawn once per instance and then TRUNCATED to k. So the k=1 arm is a
strict prefix of the k=2 arm, which is a strict prefix of k=3. A difference
across k is therefore an effect of ADDING a message, never of showing different
messages -- without nesting, each k would be a different text and the curve
would be uninterpretable.

E10'S CORPUS IS NOT TOUCHED. This module imports E10's template pools and
builds its own corpus with its own hash. `lineage_e10.py` is unmodified, so
E10's hash 00947dde8eb0520b still reproduces.

EFFECTIVE EVIDENCE COUNT. If the curves are superimposed at every k, then k
correlated restatements are worth exactly k independent sources and the model
applies no dependence discount at all. If they separate anywhere, E10's null was
a property of k=2 and its conclusion must be narrowed to that k.
"""
import hashlib
import random

from lineage_bench import DOMAINS, all_instances
from lineage_e10 import (BASES, T_CONTRADICT, T_FILLER, T_SOURCE, T_SUPPORT,
                         _cap, target_constraint)

#: Six roles: source, three possible supporters, and a fresh contradictor.
#: The contradictor is a voice that has not spoken, in every arm and every k --
#: E9's finding, held constant so it cannot covary with the manipulation.
SRC_SPEAKER = "Operations Lead"
SUPPORT_SPEAKERS = ["Safety Auditor", "Network Engineer", "Site Supervisor"]
CONTRADICTOR = "Duty Manager"

K_VALUES = (1, 2, 3)
MAX_K = 3

#: bare + (same/indep/filler) x (1,2,3)
ARMS = (["bare"]
        + [f"{kind}_k{k}" for kind in ("filler", "same", "indep")
           for k in K_VALUES])
N_ARMS = 10


def _seed(instance_id):
    """A DIFFERENT stream from E10's, so E11's draws are not E10's draws."""
    return int(hashlib.sha256(f"e11|{instance_id}".encode()).hexdigest()[:8], 16)


def build(instance):
    """Everything E11 needs for one instance, drawn once and truncated per k."""
    c = target_constraint(instance)
    verbs = dict(DOMAINS[instance.domain]["actions"])
    a, b = verbs[c.a], verbs[c.b]
    rng = random.Random(_seed(instance.id))

    off = _seed(instance.id) % len(BASES)
    bases = tuple(BASES[(off + k) % len(BASES)] for k in range(MAX_K + 1))

    # Drawn ONCE at full length, then truncated. This is what makes k=1 a
    # strict prefix of k=2 of k=3.
    picks = rng.sample(T_SUPPORT, MAX_K)
    frames = rng.sample(T_FILLER, MAX_K)
    noise = DOMAINS[instance.domain]["noise"]

    return {
        "instance": instance.id, "domain": instance.domain,
        "constraint": c.id, "a": c.a, "b": c.b, "bases": bases,
        "source": _cap(T_SOURCE.format(a=a, b=b, basis=bases[0])),
        # same: every support message cites bases[0]
        "same": [_cap(t.format(a=a, b=b, basis=bases[0])) for t in picks],
        # indep: the j-th support message cites bases[j+1]
        "indep": [_cap(t.format(a=a, b=b, basis=bases[j + 1]))
                  for j, t in enumerate(picks)],
        "filler": [f.format(noise=n[0].lower() + n[1:])
                   for f, n in zip(frames, (noise * MAX_K)[:MAX_K])],
        "contradiction": T_CONTRADICT.format(a=a, b=b),
    }


def kind_and_k(arm):
    if arm == "bare":
        return "bare", 0
    kind, k = arm.rsplit("_k", 1)
    return kind, int(k)


def exposure(rec, arm):
    """(speaker, text) pairs for one arm. Contradiction is always last and
    always from a voice that has not spoken."""
    kind, k = kind_and_k(arm)
    mid = [] if kind == "bare" else rec[kind][:k]
    speakers = [SRC_SPEAKER] + SUPPORT_SPEAKERS[:len(mid)] + [CONTRADICTOR]
    return list(zip(speakers, [rec["source"]] + mid + [rec["contradiction"]]))


def render(msgs):
    return "\n".join(f"{s}: {t}" for s, t in msgs)


def n_roots(rec, arm):
    """Distinct evidential roots visible in the arm, counting the source's."""
    kind, k = kind_and_k(arm)
    if kind == "same":
        return 1
    if kind == "indep":
        return 1 + k
    return 1                      # bare and filler show only the source's basis


def all_e11():
    return [build(i) for i in all_instances()]


def corpus_hash():
    parts = []
    for rec in all_e11():
        for arm in ARMS:
            parts.append(f"{rec['instance']}|{arm}|" + "|".join(
                f"{s}:{t}" for s, t in exposure(rec, arm)))
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


if __name__ == "__main__":
    recs = all_e11()
    print(f"=== E11 corpus: {len(recs)} instances x {N_ARMS} arms ===")
    print(f"  hash {corpus_hash()}\n")
    r = recs[0]
    for arm in ("bare", "filler_k2", "same_k1", "same_k3", "indep_k1",
                "indep_k3"):
        print(f"--- {arm} ---  roots={n_roots(r, arm)}")
        print(render(exposure(r, arm)))
        print()
