"""test_lineage_e12.py: gates E12 must clear before any decider call.

Gate 1 protects two already-scored, preregistered corpora. E12 imports E10's
template pools, so a careless edit there would invalidate both without warning.
"""
import statistics

from lineage_bench import all_instances
from lineage_e10 import BASES, _cap
from lineage_e10 import corpus_hash as e10_hash
from lineage_e11 import corpus_hash as e11_hash
from lineage_e12 import (ARMS, K, N_ARMS, PER_INSTANCE, all_units, corpus_hash,
                         eligible, exposure, render)

UNITS = all_units()
BY_INST = {i.id: i for i in all_instances()}


def cited(msgs):
    low = [m.lower() for m in msgs]
    return {b for b in BASES if any(b.lower() in m for m in low)}


def test_frozen_corpora_undisturbed():
    assert e10_hash() == "00947dde8eb0520b", "E10 corpus disturbed"
    assert e11_hash() == "5c28ada4c4b899dc", "E11 corpus disturbed"


def test_unit_count_and_clustering():
    assert len(UNITS) == 108, f"expected 108 units, got {len(UNITS)}"
    clusters = {}
    for u in UNITS:
        clusters.setdefault(u["instance"], []).append(u)
    assert len(clusters) == 36
    assert all(len(v) == PER_INSTANCE for v in clusters.values()), (
        "clusters must be balanced or the cluster bootstrap is biased")


def test_units_target_distinct_propositions():
    """Three units per instance must be three DIFFERENT orderings, or they are
    replicates and the extra n is fake."""
    seen = {}
    for u in UNITS:
        seen.setdefault(u["instance"], set()).add((u["a"], u["b"]))
    for inst, props in seen.items():
        assert len(props) == PER_INSTANCE, f"{inst}: propositions repeat"


def test_targets_are_not_already_superseded():
    for u in UNITS:
        inst = BY_INST[u["instance"]]
        assert u["constraint"] not in inst.superseded
        assert u["constraint"] in {c.id for c in eligible(inst)}


def test_root_counts():
    for u in UNITS:
        assert cited([t for _, t in exposure(u, "same_root")]) == {u["bases"][0]}
        assert cited([t for _, t in exposure(u, "indep_root")]) == set(u["bases"])
        assert len(set(u["bases"])) == K + 1


def test_arms_differ_only_in_basis_tokens():
    def strip(t):
        for b in BASES:
            t = t.replace(b, "<B>").replace(_cap(b), "<B>")
        return t
    for u in UNITS:
        s, d = exposure(u, "same_root"), exposure(u, "indep_root")
        assert [x[0] for x in s] == [x[0] for x in d]
        assert [strip(t) for _, t in s] == [strip(t) for _, t in d], u["unit"]


def test_no_ngram_separates_arms():
    def grams(msgs):
        out = set()
        for m in msgs:
            w = m.lower().replace(",", " ").replace(".", " ").replace(":", " ").split()
            out |= set(w) | {f"{x} {y}" for x, y in zip(w, w[1:])}
        return out
    same = grams([t for u in UNITS for _, t in exposure(u, "same_root")])
    ind = grams([t for u in UNITS for _, t in exposure(u, "indep_root")])
    assert not (same - ind), sorted(same - ind)[:8]
    assert not (ind - same), sorted(ind - same)[:8]


def test_contradiction_identical_and_speaker_fresh():
    for u in UNITS:
        tails = {exposure(u, a)[-1][1] for a in ARMS}
        assert tails == {u["contradiction"]}
        for a in ARMS:
            msgs = exposure(u, a)
            assert msgs[-1][0] not in [s for s, _ in msgs[:-1]]


def test_no_labels_leak():
    banned = set(ARMS) | {c.id for i in all_instances() for c in i.constraints} \
             | {x for i in all_instances() for x in i.actions}
    for u in UNITS:
        for a in ARMS:
            text = render(exposure(u, a))
            for tok in banned:
                assert tok not in text, f"{u['unit']}/{a} leaks {tok}"


def test_lengths_matched():
    s = statistics.mean(len(t.split()) for u in UNITS
                        for _, t in exposure(u, "same_root"))
    d = statistics.mean(len(t.split()) for u in UNITS
                        for _, t in exposure(u, "indep_root"))
    f = statistics.mean(len(t.split()) for u in UNITS
                        for _, t in exposure(u, "filler"))
    assert abs(s - d) <= 1.0, f"same {s:.2f} vs indep {d:.2f}"
    assert abs(s - f) <= 3.0, f"same {s:.2f} vs filler {f:.2f}"


def test_filler_constraint_irrelevant():
    from lineage_bench import DOMAINS
    for u in UNITS:
        verbs = dict(DOMAINS[u["domain"]]["actions"])
        for t in u["filler"]:
            for act in (verbs[u["a"]], verbs[u["b"]]):
                for w in act.split():
                    if len(w) > 4:
                        assert w.lower() not in t.lower(), u["unit"]


def test_regenerates_bit_identically():
    assert corpus_hash() == corpus_hash()
    assert all_units() == UNITS


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(TESTS)} gates passed over {len(UNITS)} units "
          f"in 36 clusters x {N_ARMS} arms")
    print(f"  E12 corpus: {corpus_hash()}")
    print(f"  E10 {e10_hash()} and E11 {e11_hash()} both intact")
