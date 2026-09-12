"""Zero-model-call checks for the E29-E encoding designs."""
from lineage_bench import DOMAINS
from lineage_e29 import all_e29_dialogues, context_block, store_addonly
from lineage_e29e import DESIGNS_E, FLAG, T_META, context_block_e, store_e

DS = all_e29_dialogues()


def _rej(d):
    return next(u for u in d["units"] if u["status"] == "rejected")


def _verb(d, u):
    return dict(DOMAINS[d["instance"].domain]["actions"])[u["action"]]


def test_addonly_variant_is_byte_identical_to_e29_addonly():
    for d in DS:
        for arm in ("restated", "neutral"):
            mine, _ = store_e("addonly", d["instance"], d["arms"][arm])
            theirs, _ = store_addonly(d["instance"], d["arms"][arm])
            assert mine == theirs, (d["instance"].id, arm)
            assert (context_block_e("addonly", d["instance"], d["arms"][arm])
                    == context_block("addonly", d["instance"], d["arms"][arm]))


def test_meta_holds_line_count_and_position_and_changes_only_that_line():
    for d in DS:
        u = _rej(d)
        for arm in ("restated", "neutral"):
            a, _ = store_e("addonly", d["instance"], d["arms"][arm])
            m, _ = store_e("addonly_meta", d["instance"], d["arms"][arm])
            assert len(a) == len(m)
            diffs = [i for i, (x, y) in enumerate(zip(a, m)) if x != y]
            assert len(diffs) == 1, (d["instance"].id, arm, diffs)
            i = diffs[0]
            assert a[i].startswith(("Operations Lead rejected", "Safety Auditor rejected"))
            assert m[i] == T_META.format(a=_verb(d, u))
            assert m[i].endswith("it is not needed for this case.")
            assert a[i].endswith("it is not needed for this case.")


def test_flag_removes_the_rejection_line_and_marks_its_proposal():
    for d in DS:
        u = _rej(d)
        verb = _verb(d, u)
        for arm in ("restated", "neutral"):
            a, _ = store_e("addonly", d["instance"], d["arms"][arm])
            f, ev = store_e("addonly_flag", d["instance"], d["arms"][arm])
            assert len(f) == len(a) - 1
            flagged = [x for x in f if x.startswith(FLAG)]
            assert len(flagged) == 1 and verb in flagged[0]
            assert "rejected" not in " ".join(f)
            assert sum(1 for e, _ in ev if e == "FLAG") == 1
            # every other line survives untouched and in order
            rest = [x for x in f if not x.startswith(FLAG)]
            keep = [x for x in a if "rejected the proposal" not in x and verb not in x.split(";")[0]
                    or ("rejected the proposal" not in x and not x.endswith(f"proposed to {verb}."))]
            assert rest == [x for x in a if "rejected the proposal" not in x
                            and x != f"{flagged[0][len(FLAG):]}"], (d["instance"].id, arm)


def test_the_rejected_step_is_mentioned_the_expected_number_of_times():
    for d in DS:
        u = _rej(d)
        verb = _verb(d, u)
        for arm in ("restated", "neutral"):
            for design in DESIGNS_E:
                lines, _ = store_e(design, d["instance"], d["arms"][arm])
                n = sum(verb in x for x in lines)
                # proposal + rejection(-encoding) (+ restatement in the restated arm)
                want = 2 + (1 if arm == "restated" else 0)
                if design == "addonly_flag":
                    want -= 1          # the flag rides on the proposal line
                assert n == want, (design, arm, d["instance"].id, lines)


def test_headers_match_e29():
    d = DS[0]
    for design in DESIGNS_E:
        assert context_block_e(design, d["instance"], d["arms"]["restated"]).startswith(
            "MEMORY NOTES FROM THE DISCUSSION\n")
