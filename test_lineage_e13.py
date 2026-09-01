"""test_lineage_e13.py: gates E13 must clear before any decider call."""
import statistics

from lineage_bench import all_instances, plan_instruction
from lineage_e10 import corpus_hash as e10_hash
from lineage_e11 import corpus_hash as e11_hash
from lineage_e12 import all_units, exposure, render
from lineage_e12 import corpus_hash as e12_hash
from lineage_e13 import (DEPENDENCE, DIAGNOSTIC, INSTRUCTIONS, INTERVENTIONS,
                         NORMATIVE_PRINCIPLE, N_INTERVENTIONS, RECOGNITION_ARMS,
                         build_prompt, cells, corpus_hash, expected_recognition,
                         gold_note)

UNITS = all_units()
BY_ID = {i.id: i for i in all_instances()}
PI = {u["unit"]: plan_instruction(BY_ID[u["instance"]]) for u in UNITS}


def test_all_frozen_corpora_undisturbed():
    """E13 reuses E12's materials; a careless edit would invalidate three
    already-scored, preregistered corpora at once."""
    assert e10_hash() == "00947dde8eb0520b"
    assert e11_hash() == "5c28ada4c4b899dc"
    assert e12_hash() == "ecf1f4884fa49270"


def test_registry_counts_asserted():
    assert len(INTERVENTIONS) == N_INTERVENTIONS == 5
    assert len(cells()) == 10
    assert DEPENDENCE == ["same_root", "indep_root"]
    assert DIAGNOSTIC == {"gold"}
    assert RECOGNITION_ARMS == {"identify", "normative"}


def test_default_prompt_is_byte_identical_to_e12():
    """RQ2 is a replication only if DEFAULT sends exactly what E12 sent."""
    for u in UNITS:
        for dep in DEPENDENCE:
            e12 = (f"DISCUSSION\n----------\n{render(exposure(u, dep))}"
                   f"\n\n{PI[u['unit']]}")
            assert build_prompt(u, dep, "default", PI[u["unit"]]) == e12, u["unit"]


def test_discussion_text_identical_across_all_non_gold_arms():
    """Only the trailing instruction may vary. GOLD is exempt and diagnostic."""
    for u in UNITS:
        for dep in DEPENDENCE:
            bodies = set()
            for arm, _, diag in INTERVENTIONS:
                if diag:
                    continue
                p = build_prompt(u, dep, arm, PI[u["unit"]])
                bodies.add(p.split("\n\n" + PI[u["unit"]])[0])
            assert len(bodies) == 1, f"{u['unit']}/{dep}: discussion varies"


def test_no_lineage_labels_or_basis_names_leak_into_instructions():
    from lineage_e10 import BASES
    banned = (["SAME_ROOT", "INDEPENDENT_ROOT", "same_root", "indep_root",
               "lineage", "SOURCE", "corpus"] + list(BASES))
    for arm, text in INSTRUCTIONS.items():
        for tok in banned:
            assert tok not in text, f"{arm} leaks {tok!r}"
    for dep in DEPENDENCE:
        for tok in banned:
            assert tok not in gold_note(dep), f"gold_note leaks {tok!r}"


def test_gold_note_states_the_truth_and_differs_by_dependence():
    a, b = gold_note("same_root"), gold_note("indep_root")
    assert a != b
    assert "same single underlying record" in a
    assert "different underlying record" in b


def test_expected_recognition_matches_the_construction():
    for u in UNITS:
        assert expected_recognition("same_root") == {
            "same_underlying_source": True, "independent_source_count": 1}
        assert expected_recognition("indep_root") == {
            "same_underlying_source": False, "independent_source_count": 3}
        assert len(set(u["bases"])) == 3
        break


def test_sham_is_burden_matched_but_task_irrelevant():
    """Same key count, same types, similar length -- different subject."""
    ident, sham = INSTRUCTIONS["identify"], INSTRUCTIONS["sham"]
    assert abs(len(ident.split()) - len(sham.split())) <= 6, (
        f"identify {len(ident.split())} vs sham {len(sham.split())} words")
    for k in ("same_underlying_source", "independent_source_count",
              "evidence", "source"):
        assert k not in sham, f"sham mentions {k!r}"
    assert '"actions"' in sham and '"ready"' in sham


def test_normative_contains_the_frozen_principle_and_identify_does_not():
    assert NORMATIVE_PRINCIPLE in INSTRUCTIONS["normative"]
    assert NORMATIVE_PRINCIPLE not in INSTRUCTIONS["identify"]
    assert NORMATIVE_PRINCIPLE not in INSTRUCTIONS["sham"]
    # normative = identify + principle, nothing else
    assert INSTRUCTIONS["identify"] in INSTRUCTIONS["normative"]


def test_prompt_lengths_recorded_and_default_is_shortest():
    wl = {}
    for arm, _, _ in INTERVENTIONS:
        wl[arm] = statistics.mean(
            len(build_prompt(u, d, arm, PI[u["unit"]]).split())
            for u in UNITS for d in DEPENDENCE)
    assert wl["default"] == min(wl.values())
    assert abs(wl["identify"] - wl["sham"]) <= 8, wl


def test_corpus_regenerates_bit_identically():
    assert corpus_hash(plan_instruction) == corpus_hash(plan_instruction)


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(TESTS)} gates passed over {len(UNITS)} units x "
          f"{len(cells())} cells")
    print(f"  E13 prompt-corpus hash: {corpus_hash(plan_instruction)}")
    print("  frozen: E10 %s  E11 %s  E12 %s" % (e10_hash(), e11_hash(), e12_hash()))
    print("\n  mean prompt words by arm:")
    for arm, _, _ in INTERVENTIONS:
        w = statistics.mean(len(build_prompt(u, d, arm, PI[u["unit"]]).split())
                            for u in UNITS for d in DEPENDENCE)
        print(f"      {arm:<10} {w:6.1f}")
