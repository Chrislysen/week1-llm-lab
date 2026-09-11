"""Benchmark validation for AgentLineageBench Mode A.

Run:  python test_lineage_bench.py

Offline. No model calls. Five groups, matching the validation gate:
  evaluator known-good / known-bad
  lineage text <-> metadata consistency
  hidden-state leakage
  deterministic regeneration from seed
  metric conditioning (denominators, and rates that must be None not 0.0)
"""
import json

from lineage_bench import AUTHORITY_RULE, BENCH_DOMAINS, DOMAINS, EXPOSURES, GRAPHS, LINEAGE_CLASSES, all_instances, expose, generate_instance, plan_instruction, render_dialogue
from lineage_eval import (check_plan, corrupted_form,
                          corruption_susceptibility, decision_authority_inversion,
                          obeys, presence, recovery_rate,
                          retrieval_authority_inversion, score,
                          supersession_collateral, supersession_respected,
                          utilization)

from lineage_validate import SYSTEM as SYSTEM_PROMPT

INSTANCES = all_instances()


def plan_json(actions, ready=True):
    return json.dumps({"actions": list(actions), "ready": ready})


def topo_order(instance, constraints=None):
    """A valid ordering of every action, respecting the constraint set."""
    cs = constraints if constraints is not None else instance.effective_constraints
    order, remaining = [], list(instance.actions)
    edges = [(c.a, c.b) for c in cs if c.kind == "before"]
    while remaining:
        for a in remaining:
            if not any(b == a and x in remaining for x, b in edges):
                order.append(a)
                remaining.remove(a)
                break
        else:
            raise AssertionError(f"{instance.id}: constraint graph has a cycle")
    return order


# -- Shape --------------------------------------------------------------

assert len(INSTANCES) == 36, len(INSTANCES)
assert len({i.id for i in INSTANCES}) == 36, "instance ids must be unique"
assert len(BENCH_DOMAINS) == 6 and len(GRAPHS) == 6

for inst in INSTANCES:
    assert len(inst.actions) == 6, inst.id
    assert len(set(inst.actions)) == 6, f"{inst.id} has duplicate actions"
    assert 6 <= len(inst.constraints) <= 8, (inst.id, len(inst.constraints))
    assert len({c.id for c in inst.constraints}) == len(inst.constraints)
    for c in inst.constraints:
        assert c.a in inst.actions, (inst.id, c)
        if c.kind == "before":
            assert c.b in inst.actions and c.b != c.a, (inst.id, c)
    # Every non-distractor lineage class is represented.
    have = {m.lineage for m in inst.messages}
    for cls in ("SOURCE", "FAITHFUL_RELAY", "CORRUPTED_RELAY",
                "RECOVERY", "DISTRACTOR", "SUPERSESSION"):
        assert cls in have, f"{inst.id} missing {cls}"
    assert have <= set(LINEAGE_CLASSES), have
    assert len(inst.superseded) >= 1, inst.id
    assert inst.announced_supersession in inst.superseded, inst.id

# Vocabularies are disjoint across domains, so no single domain's lexical
# accident can dominate the benchmark.
vocabs = {d: {a for a, _ in DOMAINS[d]["actions"]} for d in BENCH_DOMAINS}
for d1 in vocabs:
    for d2 in vocabs:
        if d1 < d2:
            assert not (vocabs[d1] & vocabs[d2]), f"{d1}/{d2} share actions"

# Every graph is satisfiable -- a full ordering exists.
for inst in INSTANCES:
    topo_order(inst)
    topo_order(inst, inst.constraints)

# THE DIFFERENTIATOR. A legitimate override REPLACES an ordering with its
# reverse, so ignoring it costs something.
#
# An earlier design had the override merely DELETE the rule. That made the
# effective set a strict subset of the authored set, so a plan obeying every
# authored rule satisfied ground truth perfectly: source_truster scored 1.0000
# recall and 36/36 success. That is precisely the property every conflict
# benchmark in the prior-art scan has -- the authoritative source is always the
# answer key -- and it is the one thing this benchmark exists to break.
from lineage_eval import baseline_scores as _bl

_b = [_bl(i) for i in INSTANCES]
_src_wins = sum(x["source_truster"]["success"] for x in _b)
_lat_wins = sum(x["latest_truster"]["success"] for x in _b)
assert _src_wins == 0, (
    f"always-trust-the-source succeeds on {_src_wins}/36 -- the override has no "
    "cost and the benchmark rewards the same reflex as all the prior art")
assert _lat_wins < len(INSTANCES) // 2, (
    f"always-trust-the-latest succeeds on {_lat_wins}/36 -- the corruption has "
    "no cost")

# Both reflexes must fail while the task stays solvable, or the fix has just
# made it impossible.
assert all(check_plan(plan_json(topo_order(i)), i).success for i in INSTANCES)

for inst in INSTANCES:
    ann = {c.id: c for c in inst.constraints}[inst.announced_supersession]
    assert ann.kind == "before", (inst.id, ann.kind)
    # The effective set carries the REVERSED rule, not a hole.
    eff = {c.id: c for c in inst.effective_constraints}
    assert ann.id in eff, (inst.id, "override deleted rather than replaced")
    assert (eff[ann.id].a, eff[ann.id].b) == (ann.b, ann.a), (inst.id, ann.id)

# CRITICAL CONTROLS -- REGISTERED, NOT INLINE.
#
# The echo-the-prompt-order control was written once, caught the worst defect in
# this project (a printed valid topological order that scored 36/36), and was
# then SILENTLY DELETED by a later edit whose slice replacement spanned it. The
# suite kept passing for several commits. verify_claims.py found it, not this
# file.
#
# Controls now live in a registry with an asserted count, so removing one is
# itself a test failure rather than a quiet reduction in coverage.
def _ctrl_echo():
    """Emitting the printed vocabulary order must not solve the task."""
    n = sum(check_plan(plan_json(list(i.actions)), i).success for i in INSTANCES)
    assert n <= 2, (f"echo-the-prompt-order scores {n}/36 -- the printed "
                    "vocabulary is leaking a valid ordering again")
    return f"echo {n}/36"


def _ctrl_solvable():
    """...but the task must still be solvable, or the fix broke it."""
    n = sum(check_plan(plan_json(topo_order(i)), i).success for i in INSTANCES)
    assert n == len(INSTANCES), f"only {n}/36 solvable"
    return f"optimal {n}/36"


def _ctrl_source_truster():
    """Always-trust-the-source must FAIL -- the differentiator vs prior art."""
    from lineage_eval import baseline_scores
    n = sum(baseline_scores(i)["source_truster"]["success"] for i in INSTANCES)
    assert n == 0, (f"always-trust-the-source succeeds on {n}/36 -- the override "
                    "has no cost and this rewards the same reflex as all the "
                    "prior art")
    return f"source_truster {n}/36"


def _ctrl_empty_plan():
    """An empty plan must never score as a success."""
    n = sum(check_plan(plan_json([]), i).success for i in INSTANCES)
    assert n == 0, f"empty plan succeeds on {n}/36"
    return f"empty {n}/36"


CRITICAL_CONTROLS = [_ctrl_echo, _ctrl_solvable, _ctrl_source_truster,
                     _ctrl_empty_plan]
assert len(CRITICAL_CONTROLS) == 4, (
    "a critical control was removed -- restore it or update this count "
    "deliberately, never silently")
_results = [c() for c in CRITICAL_CONTROLS]
print("critical controls (4):       " + ", ".join(_results))

print("shape + satisfiability:      OK")

# -- Evaluator known-good / known-bad ------------------------------------

for inst in INSTANCES:
    good = topo_order(inst)
    chk = check_plan(plan_json(good), inst)
    assert chk.parsed and chk.violated == [], (inst.id, chk.violated)
    assert chk.constraint_recall == 1.0 and chk.success, inst.id

    # Known-bad: invert one `before` rule and the plan must fail on exactly it.
    befores = [c for c in inst.effective_constraints if c.kind == "before"]
    if befores:
        c = befores[0]
        bad = good[:]
        # Indices FIRST. Doing bad[bad.index(a)], bad[bad.index(b)] = b, a
        # re-evaluates .index() after the first write, finds the duplicate it
        # just created, and silently undoes the swap.
        ia, ib = bad.index(c.a), bad.index(c.b)
        bad[ia], bad[ib] = c.b, c.a
        assert bad != good, "the swap must actually change the plan"
        chk = check_plan(plan_json(bad), inst)
        assert c.id in chk.violated, (inst.id, c.id, chk.violated)
        assert not chk.success

    # Known-bad: drop a required action.
    reqs = [c for c in inst.effective_constraints if c.kind == "required"]
    if reqs:
        c = reqs[0]
        chk = check_plan(plan_json([a for a in good if a != c.a]), inst)
        assert c.id in chk.violated, (inst.id, c.id, chk.violated)
        assert not chk.success

    # Empty plan cannot score vacuously well.
    assert not check_plan(plan_json([]), inst).success

    # Malformed output is caught, and carries no constraint verdict.
    for bad in ("", "no json", '{"actions": ["X"]', '{"actions": "X", "ready": true}',
                '{"actions": [], "ready": "yes"}', '[1,2]'):
        chk = check_plan(bad, inst)
        assert not chk.parsed and chk.parse_error and not chk.success
        assert chk.violated == [] and chk.constraint_recall is None

    # Invented actions are recorded, not fatal (matches the compulsory rule).
    chk = check_plan(plan_json(good + ["NOT_AN_ACTION"]), inst)
    assert chk.unknown_actions == ["NOT_AN_ACTION"] and chk.success

print("evaluator good/bad:          OK")

# -- Lineage text <-> metadata consistency -------------------------------

for inst in INSTANCES:
    verbs = dict(DOMAINS[inst.domain]["actions"])
    cmap = {c.id: c for c in inst.constraints}
    ids = {m.msg_id for m in inst.messages}
    for m in inst.messages:
        # SUPERSESSION is spoken by the Duty Manager: authority is carried
        # by the speaker, not the wording. Enforced in the n-gram gate.
        assert m.speaker in ("Operations Lead", "Safety Auditor",
                             "Duty Manager")
        assert m.text and m.text[-1] in ".!?", (inst.id, m.text)
        low = m.text.lower()          # templates may capitalise a leading verb
        if m.lineage == "DISTRACTOR":
            assert m.constraint_id is None and m.derives_from == ()
            # A distractor must not mention any action's verb phrase.
            for c in inst.constraints:
                assert verbs[c.a].lower() not in low, (inst.id, m.msg_id)
            continue
        assert m.constraint_id in cmap, (inst.id, m.msg_id)
        c = cmap[m.constraint_id]
        # The text must actually mention the actions the metadata claims.
        assert verbs[c.a].lower() in low, (inst.id, m.msg_id, c.id)
        if c.kind == "before":
            assert verbs[c.b].lower() in low, (inst.id, m.msg_id, c.id)
        # Derivatives point at real, EARLIER messages.
        if m.lineage == "SOURCE":
            assert m.derives_from == () and m.faithful is True
        else:
            assert m.derives_from, (inst.id, m.msg_id)
            for d in m.derives_from:
                assert d in ids and d < m.msg_id, (inst.id, m.msg_id, d)
        assert m.faithful is (m.lineage != "CORRUPTED_RELAY"), (inst.id, m.msg_id)

    # Exactly one source per constraint, and the corrupted/recovered/superseded
    # assignments are distinct constraints.
    for c in inst.constraints:
        srcs = [m for m in inst.representations(c.id) if m.lineage == "SOURCE"]
        assert len(srcs) == 1, (inst.id, c.id)
    cor = {m.constraint_id for m in inst.by_lineage("CORRUPTED_RELAY")}
    rec = {m.constraint_id for m in inst.by_lineage("RECOVERY")}
    sup = {m.constraint_id for m in inst.by_lineage("SUPERSESSION")}
    fai = {m.constraint_id for m in inst.by_lineage("FAITHFUL_RELAY")}
    assert rec <= cor, f"{inst.id}: recovery without a corruption"
    assert not (sup & cor) and not (sup & fai), f"{inst.id}: role collision"
    assert sup == {inst.announced_supersession}, inst.id
    # Distractors are drawn without replacement.
    dtexts = [m.text for m in inst.by_lineage("DISTRACTOR")]
    assert len(dtexts) == len(set(dtexts)), f"{inst.id}: duplicate distractor"

    # A corruption must actually conflict with its source.
    for m in inst.by_lineage("CORRUPTED_RELAY"):
        c = cmap[m.constraint_id]
        alt = corrupted_form(c)
        if alt is not None:
            assert (alt.a, alt.b) == (c.b, c.a), (inst.id, c.id)

print("lineage consistency:         OK")

# -- Hidden-state leakage ------------------------------------------------

# Nothing a model can see may carry constraint ids, lineage labels, derivation
# links, or the word "constraint". This is the check that keeps the ground truth
# hidden; without it the benchmark measures reading comprehension of its own key.
FORBIDDEN = (list(LINEAGE_CLASSES)
             + [c.lower() for c in LINEAGE_CLASSES]
             + ["constraint", "derives_from", "lineage", "authoritative",
                "superseded", "faithful", "corrupted", "ground truth",
                "msg_id", "hidden"])

for inst in INSTANCES:
    for condition in EXPOSURES:
        visible = render_dialogue(expose(inst, condition))
        # The REAL prompt, system message included. The guard whose whole job is
        # to keep the key out of the prompt must run over the whole prompt --
        # the earlier version checked only the dialogue and the instruction.
        text = (SYSTEM_PROMPT.format(setting=inst.setting) + "\n"
                + visible + "\n" + plan_instruction(inst))
        # The standing authority rule is a DELIBERATE part of the prompt -- org
        # policy about who may revise a procedure, not part of the hidden key --
        # and it legitimately contains the word "authoritative". Excise exactly
        # that text and scan everything else with the full forbidden list.
        low = text.replace(AUTHORITY_RULE, "").lower()
        for term in FORBIDDEN:
            assert term.lower() not in low, (inst.id, condition, term)
        for c in inst.constraints:
            assert c.id not in text, (inst.id, condition, c.id)
        # The action vocabulary appears ONLY in the plan instruction.
        for a in inst.actions:
            assert a not in visible, (inst.id, condition, a)
            assert a in plan_instruction(inst), (inst.id, a)

print("no hidden-state leakage:     OK")

# N-GRAM SEPARABILITY GATE.
#
# An adversarial audit found that changed|now classified SUPERSESSION
# perfectly -- 36/36 hits, 0/468 on every other message -- so a two-word regex
# scored 1.0000 recall and 36/36 success, identical to optimal, with no
# authority reasoning at all. The differentiator was recoverable by string
# matching, which meant it was not a differentiator.
#
# Authority now lives in the SPEAKER, not the wording, and this gate makes that
# checkable rather than asserted: no n-gram up to length 3 may separate a
# legitimate override from an unauthorised revision of the same kind.
def _grams(text, n):
    w = text.lower().replace(".", " ").replace(",", " ").replace("--", " ").split()
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


_sup = [m.text for i in INSTANCES for m in i.messages if m.lineage == "SUPERSESSION"]
_cmap_all = {(i.id, c.id): c for i in INSTANCES for c in i.constraints}
_cor = [m.text for i in INSTANCES for m in i.messages
        if m.lineage == "CORRUPTED_RELAY"
        and _cmap_all[(i.id, m.constraint_id)].kind == "before"]
assert _sup and _cor, "nothing to compare"

for _n in (1, 2, 3):
    _sg = [_grams(t, _n) for t in _sup]
    _cg = [_grams(t, _n) for t in _cor]
    for _g in set().union(*_sg):
        _hit_s = sum(_g in x for x in _sg)
        _hit_c = sum(_g in x for x in _cg)
        assert not (_hit_s == len(_sg) and _hit_c == 0), (
            f"the {_n}-gram {_g!r} separates SUPERSESSION from CORRUPTED_RELAY "
            f"perfectly ({_hit_s}/{len(_sg)} vs {_hit_c}/{len(_cg)}) -- the "
            "override is detectable by string match, so it is not testing "
            "authority reasoning")

# The two classes must in fact SHARE wording, not merely fail to be separable.
assert set(_sup) & set(_cor), "no shared surface form between the two classes"

# And authority must be carried by the speaker instead.
for inst in INSTANCES:
    for m in inst.messages:
        if m.lineage == "SUPERSESSION":
            assert m.speaker == "Duty Manager", (inst.id, m.speaker)
        else:
            assert m.speaker in ("Operations Lead", "Safety Auditor"), (inst.id, m.speaker)

print("n-gram separability gate:  OK")


# -- Deterministic regeneration from seed --------------------------------

for d in BENCH_DOMAINS:
    for g in GRAPHS:
        a, b = generate_instance(d, g), generate_instance(d, g)
        assert a == b, f"{d}-{g} is not deterministic"
        assert a.seed == b.seed

# Regenerating the whole benchmark twice gives identical text everywhere.
again = all_instances()
assert [i.id for i in again] == [i.id for i in INSTANCES], "unstable ordering"
for x, y in zip(INSTANCES, again):
    assert [m.text for m in x.messages] == [m.text for m in y.messages], x.id

# Different (domain, graph) pairs give different seeds.
seeds = {(i.domain, i.graph): i.seed for i in INSTANCES}
assert len(set(seeds.values())) == 36, "seed collision"

# CORPUS FIXTURE. In-process determinism proves the function is pure, not
# that the corpus is STABLE across code edits -- and it has changed twice
# (supersession closure, then the position/permutation fixes), each time
# silently invalidating result files that named no corpus. This hash
# identifies the corpus a result was scored against. If it changes,
# previously saved numbers are not comparable and must be re-run.
import hashlib as _h
CORPUS_HASH = _h.sha256("␟".join(
    f"{i.id}|{i.announced_supersession}|" + "|".join(
        f"{m.msg_id}:{m.lineage}:{m.text}" for m in i.messages)
    for i in INSTANCES).encode()).hexdigest()[:16]
print(f"corpus fixture:              {CORPUS_HASH}")
print("deterministic regeneration:  OK")

# -- Metric conditioning -------------------------------------------------

inst = INSTANCES[0]
good = topo_order(inst)

# `both`: source AND corruption present -> decision inversion is eligible.
pres = presence(inst, expose(inst, "both"))
chk = check_plan(plan_json(good), inst)
dai = decision_authority_inversion(inst, pres, chk)
assert dai["eligible"] >= 1, dai
assert dai["follows_corruption"] == 0, "a correct plan follows no corruption"
assert dai["rate"] == 0.0

# `source_only`: no corruption present -> NOT eligible, rate is None not 0.0.
pres = presence(inst, expose(inst, "source_only"))
dai = decision_authority_inversion(inst, pres, chk)
assert dai["eligible"] == 0 and dai["rate"] is None, dai

# A plan that adopts the corruption is detected as an inversion.
cid = next(iter({m.constraint_id for m in inst.by_lineage("CORRUPTED_RELAY")}
                - set(inst.superseded)))
c = {x.id: x for x in inst.constraints}[cid]
if c.kind == "before":
    swapped = good[:]
    ia, ib = swapped.index(c.a), swapped.index(c.b)
    swapped[ia], swapped[ib] = c.b, c.a
    assert swapped != good
else:
    swapped = [a for a in good if a != c.a]
pres = presence(inst, expose(inst, "both"))
dai = decision_authority_inversion(inst, pres, check_plan(plan_json(swapped), inst))
assert dai["follows_corruption"] >= 1, dai
assert dai["rate"] > 0, dai

# Unparsed plans yield no verdict anywhere, never a 0.0 that reads as evidence.
bad = check_plan("nonsense", inst)
assert decision_authority_inversion(inst, pres, bad)["rate"] is None
assert supersession_respected(inst, pres, bad)["rate"] is None
assert corruption_susceptibility(inst, pres, bad)["rate"] is None
assert recovery_rate(inst, pres, bad)["rate"] is None
assert utilization(inst, pres, bad)["direct_source"] is None

# Retrieval inversion counts only eligible source/derived PAIRS.
ranking = [m.msg_id for m in inst.messages]           # chronological
rai = retrieval_authority_inversion(inst, ranking)
assert rai["eligible_pairs"] >= 1
assert rai["inverted_pairs"] == 0, "sources precede derivatives chronologically"
assert rai["rate"] == 0.0
# Reverse the ranking and every eligible pair inverts.
rai = retrieval_authority_inversion(inst, list(reversed(ranking)))
assert rai["rate"] == 1.0, rai
# A ranking containing no derivatives has no eligible pairs at all.
only_src = [m.msg_id for m in inst.by_lineage("SOURCE")]
assert retrieval_authority_inversion(inst, only_src)["rate"] is None

# Supersession. The FIRST version of this metric scored "the lifted constraint
# is not in violated", which was vacuous: superseded ids are excluded from
# effective_constraints and can never be in violated, so it returned 1.0 for
# any parsed plan including an empty one. The replacement scores against the
# PRE-lift rule, so it can actually distinguish outcomes.
pres = presence(inst, expose(inst, "supersession"))
sr = supersession_respected(inst, pres, chk)
assert sr["eligible"] == 1, sr
assert sr["exercised"] + sr["ambiguous"] == sr["eligible"], sr

# NON-VACUITY: an empty plan must not be credited with exercising an override.
empty = supersession_respected(inst, pres, check_plan(plan_json([]), inst))
assert empty["exercised"] == 0, (
    "an empty plan must not count as having used the override -- this is the "
    "vacuity the first version of the metric had")

# The metric MUST be able to return 1.0, or it is unfalsifiable in the other
# direction. Since the override REVERSES the rule, a plan satisfying the
# effective (post-override) set necessarily violates the original -- which is
# exactly what "exercised" means.
ann = {c.id: c for c in inst.constraints}[inst.announced_supersession]
used = supersession_respected(
    inst, pres, check_plan(plan_json(topo_order(inst)), inst))
assert used["exercised"] == 1 and used["rate"] == 1.0, used
# And a plan built against the OLD rule must NOT count as exercising it.
old_plan = topo_order(inst, inst.constraints)
stayed = supersession_respected(
    inst, pres, check_plan(plan_json(old_plan), inst))
assert stayed["exercised"] == 0, stayed

# Collateral damage is only applicable where an override was actually present.
assert supersession_collateral(inst, pres, chk)["applicable"] is True
assert supersession_collateral(
    inst, presence(inst, expose(inst, "source_only")), chk)["applicable"] is False

# And under `source_only` the override is absent, so it is not eligible.
assert supersession_respected(
    inst, presence(inst, expose(inst, "source_only")), chk)["rate"] is None

# Recovery is only eligible where corruption AND correction are both present.
assert recovery_rate(inst, presence(inst, expose(inst, "both")), chk)["eligible"] == 0
assert recovery_rate(
    inst, presence(inst, expose(inst, "both_recovery")), chk)["eligible"] >= 1

print("metric conditioning:         OK")

# -- Exposure conditions -------------------------------------------------

for inst in INSTANCES:
    sizes = {}
    for condition, keep in EXPOSURES.items():
        msgs = expose(inst, condition)
        assert all(m.lineage in keep for m in msgs), (inst.id, condition)
        assert [m.msg_id for m in msgs] == sorted(m.msg_id for m in msgs)
        sizes[condition] = len(msgs)
    assert sizes["neither"] < sizes["source_only"] < sizes["both"], (inst.id, sizes)
    assert sizes["both"] < sizes["both_recovery"], (inst.id, sizes)
    # `both` and `source_only` differ by exactly the corruptions.
    assert (sizes["both"] - sizes["source_only"]
            == len(inst.by_lineage("CORRUPTED_RELAY"))), inst.id

print("exposure conditions:         OK")
print(f"\nAll checks passed over {len(INSTANCES)} instances.")
