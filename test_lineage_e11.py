"""test_lineage_e11.py: gates E11 must clear before any decider call.

Gate 1 is the one that protects everything already committed: E10's corpus hash
must still reproduce. E11 imports E10's template pools, so a careless edit there
would silently invalidate a preregistered, already-scored corpus.
"""
import statistics

from lineage_bench import all_instances
from lineage_e10 import BASES, _cap
from lineage_e10 import corpus_hash as e10_hash
from lineage_e11 import (ARMS, K_VALUES, MAX_K, N_ARMS, all_e11, corpus_hash,
                         exposure, kind_and_k, n_roots, render)

INSTANCES = all_instances()
RECS = all_e11()
PAIRS = list(zip(INSTANCES, RECS))


def cited(msgs):
    low = [m.lower() for m in msgs]
    return {b for b in BASES if any(b.lower() in m for m in low)}


def test_e10_corpus_is_undisturbed():
    """GATE 1. E10 is preregistered AND already scored. E11 reuses its template
    pools, so any edit there would invalidate a frozen corpus without warning."""
    assert e10_hash() == "00947dde8eb0520b", (
        "E10's corpus hash changed -- a scored, preregistered corpus has been "
        "disturbed. Revert before doing anything else.")


def test_arm_registry():
    assert len(ARMS) == N_ARMS == 10
    assert len(set(ARMS)) == 10
    assert K_VALUES == (1, 2, 3)


def test_nesting_k1_prefix_of_k2_prefix_of_k3():
    """GATE 2 -- the property that makes the k-curve interpretable.

    Without it, each k shows DIFFERENT messages and a difference across k could
    be wording rather than multiplicity. The support/filler messages at k must
    be a strict prefix of those at k+1.
    """
    for inst, r in PAIRS:
        for kind in ("filler", "same", "indep"):
            mids = {k: [t for _, t in exposure(r, f"{kind}_k{k}")][1:-1]
                    for k in K_VALUES}
            assert mids[1] == mids[2][:1], f"{inst.id}/{kind}: k1 not a prefix"
            assert mids[2] == mids[3][:2], f"{inst.id}/{kind}: k2 not a prefix"
            assert [len(mids[k]) for k in K_VALUES] == [1, 2, 3]


def test_root_counts_are_what_the_arms_claim():
    """GATE 3."""
    for inst, r in PAIRS:
        for k in K_VALUES:
            same = [t for _, t in exposure(r, f"same_k{k}")]
            ind = [t for _, t in exposure(r, f"indep_k{k}")]
            assert cited(same) == {r["bases"][0]}, f"{inst.id} same_k{k}"
            assert cited(ind) == set(r["bases"][:k + 1]), f"{inst.id} indep_k{k}"
            assert len(cited(ind)) == k + 1
            assert n_roots(r, f"same_k{k}") == 1
            assert n_roots(r, f"indep_k{k}") == k + 1


def test_same_and_indep_differ_only_in_basis_tokens():
    """GATE 4. Strip the bases; what remains must be identical."""
    def strip(t):
        for b in BASES:
            t = t.replace(b, "<B>").replace(_cap(b), "<B>")
        return t

    for inst, r in PAIRS:
        for k in K_VALUES:
            s = exposure(r, f"same_k{k}")
            d = exposure(r, f"indep_k{k}")
            assert [x[0] for x in s] == [x[0] for x in d], f"{inst.id}: speakers"
            assert [strip(t) for _, t in s] == [strip(t) for _, t in d], (
                f"{inst.id} k{k}: arms differ outside the basis token")


def test_no_ngram_separates_same_from_indep():
    """GATE 5."""
    def grams(msgs):
        out = set()
        for m in msgs:
            w = m.lower().replace(",", " ").replace(".", " ").replace(":", " ").split()
            out |= set(w) | {f"{x} {y}" for x, y in zip(w, w[1:])}
        return out

    same = grams([t for _, r in PAIRS for k in K_VALUES
                  for _, t in exposure(r, f"same_k{k}")])
    ind = grams([t for _, r in PAIRS for k in K_VALUES
                 for _, t in exposure(r, f"indep_k{k}")])
    assert not (same - ind), f"unique to same: {sorted(same - ind)[:8]}"
    assert not (ind - same), f"unique to indep: {sorted(ind - same)[:8]}"


def test_contradiction_identical_and_speaker_always_fresh():
    """GATE 6."""
    for inst, r in PAIRS:
        tails = {exposure(r, a)[-1][1] for a in ARMS}
        assert tails == {r["contradiction"]}, f"{inst.id}: contradiction varies"
        for a in ARMS:
            msgs = exposure(r, a)
            assert msgs[-1][0] not in [s for s, _ in msgs[:-1]], (
                f"{inst.id}/{a}: contradictor already spoke")
            assert len({s for s, _ in msgs}) == len(msgs), (
                f"{inst.id}/{a}: a speaker appears twice")


def test_no_labels_leak():
    """GATE 7."""
    banned = (set(ARMS) | {"SOURCE", "SAME_ROOT", "INDEPENDENT_ROOT"}
              | {c.id for i in INSTANCES for c in i.constraints}
              | {a for i in INSTANCES for a in i.actions})
    for inst, r in PAIRS:
        for a in ARMS:
            text = render(exposure(r, a))
            for tok in banned:
                assert tok not in text, f"{inst.id}/{a} leaks {tok!r}"


def test_corpus_regenerates_bit_identically():
    """GATE 9."""
    assert corpus_hash() == corpus_hash()
    from lineage_e11 import build
    for inst, r in PAIRS:
        assert build(inst) == r


def test_length_matched_at_every_k():
    """GATE 10."""
    for k in K_VALUES:
        s = statistics.mean(len(t.split()) for _, r in PAIRS
                            for _, t in exposure(r, f"same_k{k}"))
        d = statistics.mean(len(t.split()) for _, r in PAIRS
                            for _, t in exposure(r, f"indep_k{k}"))
        assert abs(s - d) <= 1.0, f"k{k}: same {s:.2f} vs indep {d:.2f}"


def test_filler_is_constraint_irrelevant():
    from lineage_bench import DOMAINS
    for inst, r in PAIRS:
        verbs = dict(DOMAINS[r["domain"]]["actions"])
        for t in r["filler"]:
            for act in (verbs[r["a"]], verbs[r["b"]]):
                for w in act.split():
                    if len(w) > 4:
                        assert w.lower() not in t.lower(), (
                            f"{inst.id}: filler mentions {w!r}")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(TESTS)} gates passed over {len(RECS)} instances x "
          f"{N_ARMS} arms")
    print(f"  E11 corpus hash: {corpus_hash()}")
    print(f"  E10 corpus hash: {e10_hash()}  (unchanged)")
    print("\n  mean words/message and roots by arm:")
    for a in ARMS:
        wl = statistics.mean(len(t.split()) for _, r in PAIRS
                             for _, t in exposure(r, a))
        print(f"      {a:<12} {wl:5.2f} words   {n_roots(RECS[0], a)} roots")
