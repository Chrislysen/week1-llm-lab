"""test_lineage_e14.py: gates E14 must clear before any decider call, plus the
three adversarial fixture tests the protocol requires of its own verifier."""
import json
import statistics
from collections import Counter

from lineage_bench import all_instances, generate_instance, plan_instruction
from lineage_e10 import BASES, _cap
from lineage_e10 import corpus_hash as e10_hash
from lineage_e11 import corpus_hash as e11_hash
from lineage_e12 import all_units as e12_units
from lineage_e12 import corpus_hash as e12_hash
from lineage_e12 import render
from lineage_e13 import corpus_hash as e13_hash
from lineage_e14 import (CELLS, DEPENDENCE, DIAGNOSTIC_CELLS, DIAG_EVERY, K,
                         N_CELLS, N_SALTS, PER_INSTANCE, PRIMARY_CELLS,
                         READY_INSTRUCTION, SALTS, SYSTEM_FIXED, all_units,
                         build_prompt, by_instance, cells_for, corpus_hash,
                         discussion, eligible, exposure, fixed_plan,
                         fixed_plan_manifest, invalid_plan, is_diag_unit,
                         plan_hash, plan_is_valid, plan_text, system_prompt)
from lineage_eval import obeys

UNITS = all_units()
INSTS = by_instance()
FROZEN = {i.id: i for i in all_instances()}


def cited(msgs):
    low = [m.lower() for m in msgs]
    return {b for b in BASES if any(b.lower() in m for m in low)}


# ------------------------------------------------------- frozen things ----

def test_frozen_corpora_undisturbed():
    """The salt parameter must not have moved a single frozen byte."""
    assert e10_hash() == "00947dde8eb0520b"
    assert e11_hash() == "5c28ada4c4b899dc"
    assert e12_hash() == "ecf1f4884fa49270"
    assert e13_hash(plan_instruction) == "5c23297196241110"
    for i in all_instances():
        d, g = i.id.split("-")
        assert generate_instance(d, g) == i
        assert generate_instance(d, g, salt=None) == i


def test_registry_counts_asserted():
    assert len(SALTS) == N_SALTS == 4
    assert len(CELLS) == N_CELLS == 7
    assert len(PRIMARY_CELLS) == 4 and len(DIAGNOSTIC_CELLS) == 3
    assert DEPENDENCE == ["same_root", "indep_root"]
    assert PER_INSTANCE == 3 and K == 2


# --------------------------------------------------------- fresh corpus ----

def test_fresh_corpus_shape():
    assert len(INSTS) == 144
    assert len(UNITS) == 432
    assert all("~" in i for i in INSTS), "fresh ids must carry their salt"
    assert not (set(INSTS) & set(FROZEN)), "a fresh id collides with a frozen one"
    clusters = Counter(u["instance"] for u in UNITS)
    assert len(clusters) == 144
    assert set(clusters.values()) == {PER_INSTANCE}, "clusters must be balanced"
    assert Counter(u["salt"] for u in UNITS) == {s: 108 for s in SALTS}


def test_units_target_distinct_unsuperseded_propositions():
    seen = {}
    for u in UNITS:
        inst = INSTS[u["instance"]]
        assert u["constraint"] not in inst.superseded
        assert u["constraint"] in {c.id for c in eligible(inst)}
        seen.setdefault(u["instance"], set()).add((u["a"], u["b"]))
    assert all(len(v) == PER_INSTANCE for v in seen.values())


def test_fresh_instances_are_new_propositions_not_relabelled_old_ones():
    """A salted instance shares (domain, graph) with a frozen one; its slot
    permutation must differ, so its propositions are new."""
    old = {(u["domain"], u["instance"].split("-")[1], u["a"], u["b"])
           for u in e12_units()}
    overlap = sum((u["domain"], u["graph"], u["a"], u["b"]) in old for u in UNITS)
    assert overlap / len(UNITS) < 0.20, f"{overlap}/{len(UNITS)} units repeat E12"
    same_perm = sum(INSTS[f"{d}-{g}~{s}"].actions == FROZEN[f"{d}-{g}"].actions
                    for s in SALTS for d, g in (i.split("-") for i in FROZEN))
    assert same_perm < 8, f"{same_perm} salted instances reuse a frozen display order"


# ------------------------------------------------- dependence matching ----

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
        assert len(s) == len(d) == K + 2


def test_no_ngram_separates_arms():
    """LEXICAL-SEPARABILITY GATE. No unigram or bigram may occur in one arm
    and never in the other, over the whole corpus."""
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


def test_bases_are_counterbalanced():
    as_root = Counter(u["bases"][0] for u in UNITS)
    as_alt = Counter(b for u in UNITS for b in u["bases"][1:])
    for b in BASES:
        assert as_root[b] > 0 and as_alt[b] > 0, b
    assert max(as_root.values()) - min(as_root.values()) <= 24


def test_contradiction_identical_and_speaker_fresh():
    for u in UNITS:
        tails = {exposure(u, a)[-1][1] for a in ("bare", "same_root", "indep_root")}
        assert tails == {u["contradiction"]}
        for a in ("bare", "same_root", "indep_root"):
            msgs = exposure(u, a)
            assert msgs[-1][0] not in [s for s, _ in msgs[:-1]]


def test_lengths_and_word_parity():
    s = statistics.mean(len(t.split()) for u in UNITS for _, t in exposure(u, "same_root"))
    d = statistics.mean(len(t.split()) for u in UNITS for _, t in exposure(u, "indep_root"))
    assert abs(s - d) <= 1.0, f"same {s:.2f} vs indep {d:.2f}"
    for mode in ("generated", "fixed"):
        diffs = [len(build_prompt(u, INSTS[u["instance"]], mode, "same_root").split())
                 - len(build_prompt(u, INSTS[u["instance"]], mode, "indep_root").split())
                 for u in UNITS]
        assert abs(statistics.mean(diffs)) <= 1.0, (mode, statistics.mean(diffs))
        assert max(abs(x) for x in diffs) <= 4, (mode, max(abs(x) for x in diffs))


def test_no_labels_leak_into_discussion():
    banned = ({"same_root", "indep_root", "SAME_ROOT", "INDEPENDENT_ROOT",
               "lineage", "generated", "fixed_invalid"}
              | {c.id for i in INSTS.values() for c in i.constraints}
              | {x for i in INSTS.values() for x in i.actions})
    for u in UNITS:
        for dep in ("bare", "same_root", "indep_root"):
            text = discussion(u, dep)
            for tok in banned:
                assert tok not in text, f"{u['unit']}/{dep} leaks {tok}"


def test_instructions_carry_no_evaluator_language():
    for tok in ("constraint", "violat", "lineage", "SAME_ROOT", "INDEPENDENT",
                "same_root", "indep_root", "evaluator", "score", "source",
                "corroborat", "independent", "basis", "root"):
        assert tok.lower() not in READY_INSTRUCTION.lower(), tok
        assert tok.lower() not in SYSTEM_FIXED.lower(), tok


# ---------------------------------------------------------- fixed plans ----

def test_fixed_plan_valid_deterministic_and_identical_across_arms():
    """PLAN-VALIDITY CONTROL and the byte-identity assertion."""
    for u in UNITS:
        inst = INSTS[u["instance"]]
        plan = fixed_plan(inst)
        assert plan_is_valid(inst, plan, u), u["unit"]
        assert plan == fixed_plan(inst)
        ps = build_prompt(u, inst, "fixed", "same_root")
        pi = build_prompt(u, inst, "fixed", "indep_root")
        blk = "Candidate plan:\n" + plan_text(plan)
        assert blk in ps and blk in pi
        assert ps.split("\n\n", 1)[1] == pi.split("\n\n", 1)[1] or \
            ps[ps.index("Candidate plan"):] == pi[pi.index("Candidate plan"):]
        assert plan_hash(plan) == plan_hash(fixed_plan(inst))


def test_fixed_plan_manifest_matches_the_generator():
    m = fixed_plan_manifest()
    assert set(m) == set(INSTS)
    for iid, entry in m.items():
        assert entry["actions"] == fixed_plan(INSTS[iid])
        assert entry["hash"] == plan_hash(entry["actions"])


def test_invalid_plan_violates_the_discussed_ordering_only_by_construction():
    from lineage_bench import Constraint
    for u in UNITS:
        inst = INSTS[u["instance"]]
        bad = invalid_plan(inst, u)
        c = {x.id: x for x in inst.constraints}[u["constraint"]]
        assert not obeys(c, bad), u["unit"]
        assert obeys(Constraint(id=c.id, kind="before", a=c.b, b=c.a), bad)
        assert sorted(bad) == sorted(fixed_plan(inst))


def test_prompts_share_the_discussion_and_generated_matches_e12_format():
    for u in UNITS:
        inst = INSTS[u["instance"]]
        for dep in DEPENDENCE:
            g = build_prompt(u, inst, "generated", dep)
            f = build_prompt(u, inst, "fixed", dep)
            assert g == (f"DISCUSSION\n----------\n{render(exposure(u, dep))}"
                         f"\n\n{plan_instruction(inst)}")
            assert f.startswith(discussion(u, dep) + "\n\n")
            assert g.startswith(discussion(u, dep) + "\n\n")
        assert system_prompt("fixed", inst) == system_prompt("fixed_invalid", inst)


def test_diagnostic_subset_is_fixed_and_spread():
    idx = [i for i in range(len(UNITS)) if is_diag_unit(i)]
    assert len(idx) == 24 and DIAG_EVERY == 18
    assert {UNITS[i]["salt"] for i in idx} == set(SALTS)
    assert len({UNITS[i]["domain"] for i in idx}) == 6
    assert len({UNITS[i]["graph"] for i in idx}) == 6, "subset must cover every graph"
    assert len({UNITS[i]["constraint"] for i in idx}) >= 3, "and more than one proposition"
    for i in range(len(UNITS)):
        assert len(cells_for(i)) == (7 if is_diag_unit(i) else 4)


def test_corpus_regenerates_bit_identically():
    assert corpus_hash() == corpus_hash()
    assert all_units() == UNITS


# --------------------------------------------- adversarial fixture tests ----

def _synthetic():
    """Two units, both modes, both arms, plus a diagnostic-free record."""
    import e14_ready as R
    u0, u1 = UNITS[0], UNITS[1]
    insts = INSTS
    rows, detail = [], []
    for u in (u0, u1):
        inst = insts[u["instance"]]
        plan = fixed_plan(inst)
        for mode in ("generated", "fixed"):
            for dep in DEPENDENCE:
                if mode == "generated":
                    text = json.dumps({"actions": plan, "ready": dep == "same_root"})
                else:
                    text = json.dumps({"ready": dep == "same_root"})
                parsed, ready, v = R.score_text(text, inst, u, mode)
                rows.append({"unit": u["unit"], "instance": u["instance"],
                             "mode": mode, "dependence": dep, "parsed": str(parsed),
                             "ready": str(ready), "verdict": v})
                detail.append({"unit": u["unit"], "instance": u["instance"],
                               "mode": mode, "dependence": dep,
                               "candidate_plan": plan_text(plan) if mode == "fixed" else "",
                               "plan_text": text})
    return rows, detail


def test_fixture_1_flipping_one_ready_value_is_caught():
    import e14_ready as R
    rows, detail = _synthetic()
    assert R.mismatches(rows, R.recompute_from_detail(detail)) == []
    rows[0]["ready"] = "False" if rows[0]["ready"] == "True" else "True"
    bad = R.mismatches(rows, R.recompute_from_detail(detail))
    assert len(bad) == 1 and bad[0][0][0] == rows[0]["unit"]


def test_fixture_2_mutating_one_fixed_plan_is_caught():
    import e14_ready as R
    rows, detail = _synthetic()
    m = fixed_plan_manifest()
    assert R.fixed_plan_gate(detail, m) == []
    d = next(x for x in detail if x["mode"] == "fixed")
    acts = json.loads(d["candidate_plan"])["actions"]
    acts[0], acts[1] = acts[1], acts[0]
    d["candidate_plan"] = plan_text(acts)
    probs = R.fixed_plan_gate(detail, m)
    assert any(p[2] == "plan differs from manifest" for p in probs)
    assert any(p[2] == "arms were shown different plans" for p in probs)


def test_fixture_3_removing_one_arm_drops_the_unit_and_says_so():
    import e14_ready as R
    rows, _ = _synthetic()
    per, dropped = R.pairs(rows, "fixed", "ready")
    assert len(per) == 2 and dropped == 0
    rows = [r for r in rows if not (r["mode"] == "fixed" and r["unit"] == UNITS[0]["unit"]
                                    and r["dependence"] == "indep_root")]
    per, dropped = R.pairs(rows, "fixed", "ready")
    assert len(per) == 1 and dropped == 1
    assert UNITS[0]["unit"] not in per


def test_fixture_4_unparsed_response_never_counts_as_a_value():
    import e14_ready as R
    rows, _ = _synthetic()
    for r in rows:
        if r["mode"] == "fixed" and r["unit"] == UNITS[1]["unit"] and r["dependence"] == "same_root":
            r["parsed"], r["ready"] = "False", ""
    per, dropped = R.pairs(rows, "fixed", "ready")
    assert dropped == 1 and UNITS[1]["unit"] not in per


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n  {len(TESTS)} gates passed over {len(UNITS)} units in "
          f"{len(INSTS)} clusters")
    print(f"  E14 corpus hash: {corpus_hash()}")
