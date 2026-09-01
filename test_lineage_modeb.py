"""test_lineage_modeb.py: gates on the Mode B corpus.

Mode A's tests ENFORCE properties, because a generator can be made to obey.
Mode B's cannot: a model writes the text, so half of these gates enforce (the
generator is rejected until it complies) and half MEASURE and report (the
property is a fact about the corpus, and hiding it would defeat the purpose of
having an external validity check at all).

Which is which is stated at every gate below. Run:  python test_lineage_modeb.py
"""
import json
import os

from lineage_bench import DOMAINS, all_instances
from lineage_depth import MAX_DEPTH, build_chain
from lineage_modeb import (FIXTURE, MAX_OVERLAP, _check_filler, _check_relay,
                           _mentions, _overlap, _too_similar, fixture_hash,
                           load, modeb_chain)

INSTANCES = all_instances()
BY_ID = {i.id: i for i in INSTANCES}


# ------------------------------------------------ offline unit gates --------
# No model calls. These lock the gate logic itself, so a later edit that
# loosened a gate to make generation "work" would fail here first.

def test_mentions_survives_paraphrase():
    assert _mentions("shift routing to the spare region now", "shift routing "
                     "to the spare region")
    assert _mentions("route traffic over to the spare region first",
                     "shift routing to the spare region")
    assert not _mentions("the on-call rota rolled over at 06:00",
                         "shift routing to the spare region")


def test_overlap_is_symmetric_and_bounded():
    assert _overlap("drain the failing node", "drain the failing node") == 1.0
    a, b = "snapshot the store first", "capture a copy of the datastore"
    assert _overlap(a, b) == _overlap(b, a)
    assert 0.0 <= _overlap(a, b) <= 1.0


def test_identical_relays_are_rejected():
    """THE PILOT BUG. First run produced L1 == L2 == L3 verbatim in every
    instance, which would have measured repetition and called it depth."""
    s = "Shift routing to the spare region must happen before we reopen it."
    assert _too_similar(s, [s]) is not None
    assert _too_similar("Before reopening, move traffic across to the spare "
                        "site", [s]) is None


def test_relay_gate_rejects_leaked_identifiers_and_missing_actions():
    inst = BY_ID["payments-chain"]
    verbs = dict(DOMAINS[inst.domain]["actions"])
    pa, pb = verbs["SHIFT_ROUTING"], verbs["REOPEN_GATEWAY"]
    assert _check_relay("SHIFT_ROUTING must come before we reopen the gateway "
                        "in every case here", inst, pa, pb)
    assert _check_relay("shift routing to the spare region comes first, "
                        "obviously, no question", inst, pa, pb)   # no pb
    assert _check_relay("too short", inst, pa, pb)
    assert _check_relay("shift routing to the spare region must happen before "
                        "we reopen the gateway", inst, pa, pb) is None


def test_filler_gate_rejects_constraint_talk():
    inst = BY_ID["payments-chain"]
    verbs = dict(DOMAINS[inst.domain]["actions"])
    pa, pb = verbs["SHIFT_ROUTING"], verbs["REOPEN_GATEWAY"]
    assert _check_filler("we should shift routing to the spare region soon "
                         "today", inst, pa, pb)
    assert _check_filler("the on-call rota rolled over at 06:00 this morning "
                         "as usual", inst, pa, pb) is None


# ------------------------------------------------ corpus gates (enforced) ---

def test_fixture_shape():
    chains = load()
    assert chains, "no Mode B fixture yet -- run lineage_modeb.py"
    for r in chains.values():
        assert len(r["faithful"]) == MAX_DEPTH, r["instance"]
        assert isinstance(r["corrupted"], str) and r["corrupted"]
        assert len(r["padding"]) == MAX_DEPTH - 1, r["instance"]
        assert all(v["ok"] for v in r["verify"]), (
            f"{r['instance']}: a message the verifier rejected was admitted")


def test_every_admitted_message_passes_its_own_gate():
    """The fixture is on disk; re-run the gates against it rather than trusting
    that they ran at generation time. A gate that is not re-checkable is a claim,
    not a gate."""
    for r in load().values():
        inst = BY_ID[r["instance"]]
        c = {x.id: x for x in inst.constraints}[r["constraint"]]
        verbs = dict(DOMAINS[inst.domain]["actions"])
        pa, pb = verbs[c.a], verbs[c.b]
        seen = [build_chain(inst).source.text]
        for k, t in enumerate(r["faithful"], 1):
            assert _check_relay(t, inst, pa, pb) is None, f"{r['instance']} L{k}"
            assert _too_similar(t, seen) is None, f"{r['instance']} L{k}"
            seen.append(t)
        assert _check_relay(r["corrupted"], inst, pa, pb) is None, r["instance"]
        for t in r["padding"]:
            assert _check_filler(t, inst, pa, pb) is None, r["instance"]


def test_exposure_schedule_is_identical_to_mode_a():
    """THE ONLY THING MODE B IS ALLOWED TO CHANGE IS THE TEXT.

    If Mode B also changed how many messages each condition shows, or where the
    corruption sits, an E5-vs-E7 difference would be uninterpretable. This pins
    the schedule to Mode A's, message for message.
    """
    for r in load().values():
        inst = BY_ID[r["instance"]]
        a, b = build_chain(inst), modeb_chain(inst)
        assert b is not None
        assert a.constraint_id == b.constraint_id
        for d in range(1, MAX_DEPTH + 1):
            for corrupt in (True, False):
                ea, eb = a.exposure(d, corrupt), b.exposure(d, corrupt)
                assert len(ea) == len(eb)
                assert [m.lineage for m in ea] == [m.lineage for m in eb]
        assert (len(a.padded(MAX_DEPTH - 1)) == len(b.padded(MAX_DEPTH - 1)))
        # The source is the SAME message object in both modes: only relays are
        # regenerated, so the authoritative claim is held fixed across modes.
        assert a.source.text == b.source.text


def test_corruption_reused_at_every_depth():
    """Mode A's discipline: one corruption wording, shown at three distances.
    Per-depth wordings would confound depth with phrasing."""
    for r in load().values():
        ch = modeb_chain(BY_ID[r["instance"]])
        assert len({m.text for m in ch.corrupted}) == 1, r["instance"]


# ------------------------------------------------ corpus facts (measured) ---

def measure_separability():
    """MEASURED, NOT ENFORCED, and the difference matters.

    Mode A FORCES faithful and corrupted relays to share surface forms, because
    a benchmark whose classes are separable by a keyword is measuring the
    keyword. Mode B cannot force anything -- a model chose the words. So the
    number is reported instead, and it is load-bearing in one direction: if some
    single word split the two classes perfectly, Mode B's task would be EASIER
    than Mode A's for a reason unrelated to depth, and any E5-vs-E7 difference
    could be that instead.
    """
    chains = load()
    fth = [t for r in chains.values() for t in r["faithful"]]
    cor = [r["corrupted"] for r in chains.values()]

    def grams(t):
        w = t.lower().replace(",", " ").replace(".", " ").split()
        return set(w) | {f"{x} {y}" for x, y in zip(w, w[1:])}

    fs, cs = [grams(t) for t in fth], [grams(t) for t in cor]
    perfect = [g for g in set().union(*cs) if all(g in c for c in cs)
               and not any(g in f for f in fs)]
    return len(fth), len(cor), sorted(perfect)


#: Words per intervening message by which filler may differ from a faithful
#: link. Beyond this, `d1_padded` and `d3` stop being a length-matched pair.
MAX_LENGTH_GAP = 1.5


def test_padded_control_is_token_matched():
    """MODE A'S LENGTH CONTROL WAS NEVER ACTUALLY LENGTH-MATCHED.

    `d1_padded` exists to show that what protects a decision is CORROBORATION
    and not sheer text volume: it holds message count and corruption position at
    the d3 values while swapping the faithful links for filler. It held the
    COUNT. It did not hold the LENGTH -- Mode A's filler comes from the domain
    noise bank and averages 7.6 words against the links' 12.4, so d1_padded
    carries about nine fewer words than d3.

    That leaves a live alternative reading of E5 which the arm was built to
    close: d3 simply has more text. The direction is unfavourable to the
    confound -- d1_padded is SHORTER than d3 and yet shows LESS protection,
    where a volume account predicts the opposite -- but "the confound points the
    wrong way" is weaker than "the confound is absent".

    Mode B closes it. Both filler and links are model-written to one length
    spec, so the pair matches to a fraction of a word. This gate keeps it that
    way: it is the reason Mode B's P2 is a stricter test than Mode A's, and it
    was measured and written down BEFORE any decision call was made.
    """
    chains = load()
    L = [len(t.split()) for r in chains.values() for t in r["faithful"]]
    P = [len(t.split()) for r in chains.values() for t in r["padding"]]
    gap = abs(sum(P) / len(P) - sum(L) / len(L))
    assert gap <= MAX_LENGTH_GAP, (
        f"filler and links differ by {gap:.1f} words/message; d1_padded and d3 "
        f"are no longer a length-matched pair")


def measure_condition_words():
    """Total words each condition puts in front of the decider, per mode."""
    from lineage_depth import build_chain as chain_a
    out = {}
    for mode, fn in (("A", chain_a), ("B", modeb_chain)):
        rows = {}
        for r in load().values():
            ch = fn(BY_ID[r["instance"]])
            for name, depth, corrupt in (("d1", 1, True), ("d2", 2, True),
                                         ("d3", 3, True), ("control", 3, False)):
                rows.setdefault(name, []).append(
                    sum(len(m.text.split()) for m in ch.exposure(depth, corrupt)))
            rows.setdefault("d1_padded", []).append(
                sum(len(m.text.split()) for m in ch.padded(MAX_DEPTH - 1)))
        out[mode] = {k: round(sum(v) / len(v), 1) for k, v in rows.items()}
    return out


def measure_drift():
    """How far the chain travels from its source, in content words retained."""
    rows = []
    for r in load().values():
        src = build_chain(BY_ID[r["instance"]]).source.text
        rows.append([_overlap(t, src) for t in r["faithful"]])
    return [round(sum(c[k] for c in rows) / len(rows), 3)
            for k in range(MAX_DEPTH)] if rows else []


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    if not os.path.exists(FIXTURE):
        raise SystemExit("no fixture; run: python lineage_modeb.py")
    for t in TESTS:
        t()
        print(f"  ok  {t.__name__}")

    chains = load()
    log = json.load(open(FIXTURE)).get("attempts", [])
    admitted = sum(1 for a in log if a["error"] is None)
    print(f"\n  {len(TESTS)} gates passed")
    print(f"  corpus: {len(chains)}/{len(INSTANCES)} instances, "
          f"hash {fixture_hash()}")
    print(f"  generation: {len(log)} attempts, {admitted} admitted, "
          f"{len(log) - admitted} rejected by a gate "
          f"({(len(log) - admitted) / max(1, len(log)):.0%})")

    dis = [v for r in chains.values() for v in r["verify"] if not v["ok"]]
    print(f"  verifier ({json.load(open(FIXTURE))['verify_model']}) "
          f"disagreements among admitted messages: {len(dis)}")

    n_f, n_c, perfect = measure_separability()
    print(f"\n  MEASURED  n-grams that perfectly separate {n_c} corrupted from "
          f"{n_f} faithful relays: {len(perfect)}")
    if perfect:
        print(f"            {perfect[:8]}")
        print("            Mode A forbids this by construction; Mode B can only")
        print("            report it. Read it as a caveat on E5-vs-E7, not as a")
        print("            defect in either run.")
    else:
        print("            none -- the two classes are not keyword-separable, "
              "the same\n            property Mode A enforces.")

    print(f"  MEASURED  content-word overlap with the source at L1/L2/L3: "
          f"{measure_drift()}")
    print("            Falling overlap is paraphrase drift. It is what a real")
    print("            relay chain does, and it is why Mode B is worth running.")

    w = measure_condition_words()
    print("\n  MEASURED  mean words shown to the decider, by condition:")
    print(f"            {'':<12}" + "".join(f"{c:>11}" for c in w["A"]))
    for mode in ("A", "B"):
        print(f"            mode {mode}      "
              + "".join(f"{v:>11}" for v in w[mode].values()))
    ga = abs(w["A"]["d1_padded"] - w["A"]["d3"])
    gb = abs(w["B"]["d1_padded"] - w["B"]["d3"])
    print(f"            d1_padded vs d3 length gap:  Mode A {ga:.1f} words, "
          f"Mode B {gb:.1f} words.")
    print("            That pair is the length control. Mode B matches it; Mode")
    print("            A did not, which is a limit on E5 and is now on record.")
