"""Zero-model-call checks for the second corpus (E29-N) and for the frozen
corpora being untouched by its introduction."""
import re

from lineage_bench import BENCH_DOMAINS, DOMAINS, NEW_DOMAINS, all_instances
from lineage_e16 import (T_ACCEPT2, T_PROPOSE2, T_REJECT2, all_dialogues,
                         corpus_hash as e16_hash)
from lineage_e29 import E16_HASH, NEUTRAL_BY_WORDS, all_e29_dialogues, corpus_hash

STOP = {"the", "a", "an", "to", "of", "and", "on", "in", "for", "at", "by", "with"}
E29_HASH = "187a426616f26598"
E29N_HASH = "e965c5fd022d6e37"   # 7d33038c6c1a9912 before the 2026-09-12 extractor correction


def words(s):
    return [w for w in re.findall(r"[a-z0-9\-']+", s.lower()) if w not in STOP]


def test_frozen_corpora_are_untouched():
    assert BENCH_DOMAINS == ("payments", "robotics", "pharmacy", "satellite", "brewery", "rail")
    assert len(all_instances()) == 36
    assert e16_hash() == E16_HASH
    assert corpus_hash() == E29_HASH
    assert len(all_e29_dialogues()) == 96


def test_second_corpus_shape_and_hash():
    assert NEW_DOMAINS == ("grid", "airline", "newsroom", "water", "checkout", "telecom")
    assert not set(NEW_DOMAINS) & set(BENCH_DOMAINS)
    assert len(all_instances(NEW_DOMAINS)) == 36
    assert len(all_dialogues(NEW_DOMAINS)) == 144
    ds = all_e29_dialogues(NEW_DOMAINS)
    assert len(ds) == 96
    assert corpus_hash(NEW_DOMAINS) == E29N_HASH


def test_new_domains_have_the_declared_shape():
    for d in NEW_DOMAINS:
        dom = DOMAINS[d]
        assert len(dom["actions"]) == 6 and len(dom["noise"]) == 4
        ids = [a for a, _ in dom["actions"]]
        assert len(set(ids)) == 6
        phrases = [p for _, p in dom["actions"]]
        # every phrase length has a neutral referent
        assert {len(p.split()) for p in phrases} <= set(NEUTRAL_BY_WORDS)
        # content words distinguish the actions inside a domain
        cw = [frozenset(words(p)) for p in phrases]
        for i in range(6):
            for j in range(6):
                if i != j:
                    assert not cw[i] <= cw[j], (d, phrases[i], phrases[j])
        # noise lines never carry a full action phrase
        for n in dom["noise"]:
            nw = set(words(n))
            for p in phrases:
                assert not set(words(p)) <= nw, (d, n, p)


def test_second_bank_is_used_and_replies_carry_no_action_words():
    all_phrase_words = {w for d in NEW_DOMAINS for _, p in DOMAINS[d]["actions"] for w in words(p)}
    seen_bank2 = False
    for x in all_dialogues(NEW_DOMAINS):
        for _, t, tag in x["dialogue"]:
            if tag[0] == "reply":
                assert t in T_ACCEPT2 + T_REJECT2, t
                assert not set(words(t)) & all_phrase_words, t
                seen_bank2 = True
            if tag[0] == "proposal":
                assert any(t == tp.format(a=p) for tp in T_PROPOSE2
                           for _, p in DOMAINS[x["instance"].domain]["actions"]), t
    assert seen_bank2


def test_e29n_arms_follow_the_e29_rules():
    for d in all_e29_dialogues(NEW_DOMAINS):
        a, b = d["arms"]["restated"], d["arms"]["neutral"]
        assert len(a) == len(b)
        diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        assert len(diffs) == 1
        i = diffs[0]
        assert a[i][0] == b[i][0]
        assert len(a[i][1].split()) == len(b[i][1].split())
        assert a[-1][2][0] == "noise" and b[-1][2][0] == "noise"
        assert sum(u["status"] == "rejected" for u in d["units"]) == 1


def test_oracle_reply_polarity_matches_unit_status_on_both_corpora():
    """The E29-N correction: a rejection wording in the second bank was stored
    as an acceptance by a prefix rule. Polarity must follow the unit status."""
    from lineage_e29 import facts_for
    for doms in (None, NEW_DOMAINS):
        for d in all_e29_dialogues(doms):
            status = {u["constraint"]: u["status"] for u in d["units"]}
            for arm in ("restated", "neutral"):
                dia = d["arms"][arm]
                for (_, text, tag), (_, ev, cid, _) in zip(dia, facts_for(d["instance"], dia)):
                    if tag[0] == "reply":
                        want = "reject" if status[cid] == "rejected" else "accept"
                        assert ev == want, (d["instance"].id, d["rotation"], text, ev)
