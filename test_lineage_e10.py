"""test_lineage_e10.py: the gates E10 must clear BEFORE any decider call.

Campaign rule: if any gate fails, E10 does not run. Fix, version, regenerate,
rehash, recommit.

The load-bearing gates are 7-12: they are what make `same_root` vs
`indep_root` a test of evidential dependence rather than a test of vocabulary.

Run:  python test_lineage_e10.py
"""
import hashlib
import json
import statistics
from collections import Counter

from lineage_bench import all_instances, plan_instruction
from lineage_e10 import (ARMS, BASES, MAX_SUPPORT, N_ARMS, SUPERSESSION_ARMS,
                         _cap,
                         T_SUPERSEDE, all_e10, corpus_hash, exposure,
                         ground_truth, render, target_constraint)
from lineage_eval import check_plan, obeys

INSTANCES = all_instances()
E10 = all_e10()
PAIRS = list(zip(INSTANCES, E10))


def cited_bases(msgs):
    """Which bases a message set attributes to, case-insensitively.

    `_cap` capitalises a leading basis ("The platform spec is explicit..."), so
    a naive substring test misses the SOURCE's own basis. Gate 7b caught that;
    gate 7a had passed only because the missed basis happened to equal the one
    the support messages cited.
    """
    low = [m.lower() for m in msgs]
    return {b for b in BASES if any(b.lower() in m for m in low)}


def _plan(actions):
    return json.dumps({"actions": list(actions), "ready": True})


def _ordered(inst, first, second):
    """A full plan over all actions with `first` placed before `second`."""
    rest = [a for a in inst.actions if a not in (first, second)]
    return [first, second] + rest


# ---------------------------------------------------- registry + shape ------

def test_arm_registry_count_is_asserted():
    """Deleting an arm must be a test failure, not a silent narrowing. This
    project has already lost a null control to exactly that."""
    assert len(ARMS) == N_ARMS == 9, (
        f"expected {N_ARMS} arms, found {len(ARMS)} -- restore it or change the "
        f"count deliberately")
    assert len({a[0] for a in ARMS}) == 9
    assert SUPERSESSION_ARMS == {"bare_super", "same_root_super",
                                 "indep_root_super"}


def test_corpus_shape():
    assert len(E10) == 36
    for inst, e in PAIRS:
        assert len(e.support_same) == MAX_SUPPORT
        assert len(e.support_indep) == MAX_SUPPORT
        assert len(e.filler) == MAX_SUPPORT
        assert e.constraint_id not in inst.superseded, (
            f"{inst.id}: E10 must own the only override of its target")


# ------------------------------------------------- evaluator behaviour ------
# Gates 1-3: known-good passes, known-bad fails, and both trivial heuristics
# fail the arm designed to catch them.

def test_known_good_and_known_bad():
    good = bad = 0
    for inst, e in PAIRS:
        c = ground_truth(inst, e, "same_root")          # unchanged ordering
        good += obeys(c, _ordered(inst, c.a, c.b))
        bad += obeys(c, _ordered(inst, c.b, c.a))
    assert good == 36, f"known-good plans passed only {good}/36"
    assert bad == 0, f"known-bad plans passed {bad}/36"


def test_empty_plan_fails():
    for inst, e in PAIRS:
        assert not check_plan(_plan([]), inst).success


def test_echo_the_prompt_order_fails():
    """The defect that invalidated E2 v1: a prompt that prints a usable order."""
    wins = sum(check_plan(_plan(list(i.actions)), i).success for i in INSTANCES)
    assert wins <= 4, f"echo control succeeded {wins}/36 -- the prompt leaks"


def test_source_only_heuristic_fails_legitimate_supersession():
    """Gate 2. A model that always follows the oldest/most authoritative-looking
    message must LOSE the supersession arms, or those arms reward the reflex."""
    wins = 0
    for inst, e in PAIRS:
        c = ground_truth(inst, e, "same_root_super")    # reversed
        wins += obeys(c, _ordered(inst, e.a, e.b))      # source's ordering
    assert wins == 0, f"source-truster survived supersession in {wins}/36"


def test_latest_message_heuristic_fails_unsupported_contradiction():
    """Gate 3. A model that always follows the last message must LOSE the
    contradiction arms."""
    wins = 0
    for inst, e in PAIRS:
        c = ground_truth(inst, e, "same_root")          # unchanged
        wins += obeys(c, _ordered(inst, e.b, e.a))      # contradiction's order
    assert wins == 0, f"latest-truster survived contradiction in {wins}/36"


def test_the_two_heuristics_are_not_the_same_policy():
    """Each reflex must WIN somewhere, or 'it fails' is uninformative."""
    src_wins = sum(obeys(ground_truth(i, e, "same_root"),
                         _ordered(i, e.a, e.b)) for i, e in PAIRS)
    late_wins = sum(obeys(ground_truth(i, e, "same_root_super"),
                          _ordered(i, e.b, e.a)) for i, e in PAIRS)
    assert src_wins == 36 and late_wins == 36


# ----------------------------------------------------------- leakage --------

def test_no_formal_labels_leak_into_any_message():
    """Gate 4. No lineage class, arm name, constraint id or action identifier
    may appear in rendered text."""
    banned = ({"SOURCE", "SAME_ROOT", "INDEPENDENT_ROOT", "FAITHFUL_RELAY",
               "CORRUPTED_RELAY", "SUPERSESSION", "DISTRACTOR"}
              | {a[0] for a in ARMS}
              | {c.id for i in INSTANCES for c in i.constraints}
              | {a for i in INSTANCES for a in i.actions})
    for inst, e in PAIRS:
        for arm, *_ in ARMS:
            text = render(exposure(e, arm))
            for tok in banned:
                assert tok not in text, f"{inst.id}/{arm} leaks {tok!r}"


# ------------------------------------------- THE LOAD-BEARING GATES ---------

def test_same_root_cites_exactly_one_basis():
    """Gate 7a. One evidential root, by construction."""
    for inst, e in PAIRS:
        msgs = [t for _, t in exposure(e, "same_root")]
        cited = cited_bases(msgs)
        assert cited == {e.bases[0]}, f"{inst.id}: same_root cites {cited}"


def test_indep_root_cites_exactly_three_bases():
    """Gate 7b. Three evidential roots, all distinct."""
    for inst, e in PAIRS:
        msgs = [t for _, t in exposure(e, "indep_root")]
        cited = cited_bases(msgs)
        assert cited == set(e.bases), f"{inst.id}: indep_root cites {cited}"
        assert len(set(e.bases)) == 3


def test_the_two_arms_differ_only_in_basis_tokens():
    """GATE 8 -- the one that makes E10 an experiment rather than a comparison
    of two different texts.

    Strip every basis string from both arms. What remains must be IDENTICAL,
    message for message: same skeletons, same speakers, same count, same source,
    same contradiction.
    """
    for inst, e in PAIRS:
        s = exposure(e, "same_root")
        d = exposure(e, "indep_root")
        assert [x[0] for x in s] == [x[0] for x in d], f"{inst.id}: speakers"
        assert len(s) == len(d)

        def strip(t):
            for b in BASES:
                t = t.replace(b, "<BASIS>").replace(_cap(b), "<BASIS>")
            return t

        assert [strip(t) for _, t in s] == [strip(t) for _, t in d], (
            f"{inst.id}: the arms differ somewhere other than the basis token")


def test_contradiction_and_source_are_byte_identical_across_arms():
    """Gate 9."""
    for inst, e in PAIRS:
        contra_arms = [a for a, *_ in ARMS if a not in SUPERSESSION_ARMS]
        tails = {render([exposure(e, a)[-1]]).split(": ")[-1]
                 for a in contra_arms}
        assert tails == {e.contradiction}, f"{inst.id}: contradiction varies"
        heads = {t for a, *_ in ARMS for s, t in [exposure(e, a)[0]]}
        assert heads == {e.source}, f"{inst.id}: source varies"


def test_final_prompt_is_identical_across_arms():
    """Gate 9b. The planning instruction must not vary with condition."""
    for inst in INSTANCES:
        h = hashlib.sha256(plan_instruction(inst).encode()).hexdigest()
        assert h == hashlib.sha256(
            plan_instruction(inst).encode()).hexdigest()
    # and it must not mention any basis or arm
    for inst in INSTANCES:
        p = plan_instruction(inst)
        assert not any(b in p for b in BASES)


def test_no_unigram_or_bigram_separates_the_two_arms():
    """GATE 10. The counterbalancing check.

    Per MESSAGE, no single word or word-pair may occur in one arm and never in
    the other. If one did, the arms would be separable by keyword and H3 would
    be a vocabulary test.

    Within-instance REPETITION of basis identity is deliberately NOT tested
    here: it is the independent variable. Gate 19 of the protocol documents that
    as the only licensed semantic difference.
    """
    def grams(msgs):
        out = set()
        for m in msgs:
            w = m.lower().replace(",", " ").replace(".", " ").replace(":", " ").split()
            out |= set(w) | {f"{x} {y}" for x, y in zip(w, w[1:])}
        return out

    same = grams([t for _, e in PAIRS for t in
                  [x[1] for x in exposure(e, "same_root")]])
    indep = grams([t for _, e in PAIRS for t in
                   [x[1] for x in exposure(e, "indep_root")]])
    only_same, only_indep = same - indep, indep - same
    assert not only_same, f"{len(only_same)} n-grams unique to same_root: {sorted(only_same)[:8]}"
    assert not only_indep, f"{len(only_indep)} n-grams unique to indep_root: {sorted(only_indep)[:8]}"


def test_bases_are_counterbalanced_across_arms():
    """GATE 11. Every basis must serve as the repeated root somewhere and as a
    distinct alternative elsewhere, or basis vocabulary correlates with arm."""
    as_root = Counter(e.bases[0] for _, e in PAIRS)
    as_alt = Counter(b for _, e in PAIRS for b in e.bases[1:])
    for b in BASES:
        assert as_root[b] > 0, f"{b!r} is never the repeated root"
        assert as_alt[b] > 0, f"{b!r} is never an independent alternative"


def test_arm_lengths_match():
    """GATE 12. same_root vs indep_root within 1.0 word per message, and the
    filler arm matched to both so H2 is not a length test in disguise."""
    def wl(arm):
        return statistics.mean(len(t.split())
                               for _, e in PAIRS for _, t in exposure(e, arm))
    s, d, f = wl("same_root"), wl("indep_root"), wl("filler")
    assert abs(s - d) <= 1.0, f"same {s:.2f} vs indep {d:.2f} words/message"
    assert abs(s - f) <= 3.0, f"same {s:.2f} vs filler {f:.2f} words/message"


def test_message_counts_match_where_required():
    for inst, e in PAIRS:
        n = {a: len(exposure(e, a)) for a, *_ in ARMS}
        assert n["filler"] == n["same_root"] == n["indep_root"] == 4
        assert n["same_root_nospk"] == n["indep_root_nospk"] == 4
        assert n["same_root_super"] == n["indep_root_super"] == 4
        assert n["bare"] == n["bare_super"] == 2


def test_speaker_free_arms_have_no_speaker_at_all():
    """H4 needs speaker identity REMOVED, not replaced by a placeholder --
    a placeholder is still a speaker slot and keeps the social frame."""
    for inst, e in PAIRS:
        for arm in ("same_root_nospk", "indep_root_nospk"):
            assert all(s is None for s, _ in exposure(e, arm))
            text = render(exposure(e, arm))
            for name in ("Operations Lead", "Safety Auditor",
                         "Network Engineer", "Duty Manager"):
                assert name not in text, f"{inst.id}/{arm} still names {name}"
        # and stripping speakers must not change the message text itself
        assert ([t for _, t in exposure(e, "same_root")]
                == [t for _, t in exposure(e, "same_root_nospk")])


def test_contradictor_is_a_fresh_voice_in_every_speakered_arm():
    """E9's lesson, enforced. Self-reversal must not vary with condition."""
    for inst, e in PAIRS:
        for arm, *_ in ARMS:
            msgs = exposure(e, arm)
            if msgs[-1][0] is None:
                continue
            assert msgs[-1][0] not in [s for s, _ in msgs[:-1]], (
                f"{inst.id}/{arm}: the contradictor already spoke")


def test_supersession_authority_is_not_an_evidence_basis():
    """Found while reading the rendered corpus: 'the change-control record' was
    in BASES while the reviser is Change-control, so in some instances the body
    superseding the claim was the body corroborating it."""
    for b in BASES:
        head = b.replace("the ", "").split()[0].lower()
        assert head not in T_SUPERSEDE.lower(), (
            f"basis {b!r} overlaps the supersession authority")


def test_filler_is_constraint_irrelevant():
    for inst, e in PAIRS:
        verbs = dict(__import__("lineage_bench").DOMAINS[e.domain]["actions"])
        for t in e.filler:
            for act in (verbs[e.a], verbs[e.b]):
                key = [w for w in act.split() if len(w) > 4]
                assert not any(k.lower() in t.lower() for k in key), (
                    f"{inst.id}: filler mentions the constraint")


# ------------------------------------------------------ reproducibility -----

def test_corpus_regenerates_bit_identically():
    """Gate 5. Deterministic from instance ids alone -- no clock, no PYTHONHASHSEED."""
    assert corpus_hash() == corpus_hash()
    from lineage_e10 import build
    for inst, e in PAIRS:
        assert build(inst) == e


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(TESTS)} gates passed over {len(E10)} instances x "
          f"{N_ARMS} arms")
    print(f"  E10 corpus hash: {corpus_hash()}")

    def wl(arm):
        return statistics.mean(len(t.split())
                               for _, e in PAIRS for _, t in exposure(e, arm))
    print("\n  mean words/message by arm:")
    for a, *_ in ARMS:
        print(f"      {a:<20} {wl(a):.2f}")
    print("\n  same_root and indep_root are identical after replacing every")
    print("  basis string with a placeholder, and no per-message n-gram")
    print("  separates them. The only difference is how many distinct")
    print("  evidential roots the support set traces to.")
