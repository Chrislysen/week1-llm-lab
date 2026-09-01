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

from lineage_bench import (DOMAINS, EXPOSURES, GRAPHS, LINEAGE_CLASSES,
                           all_instances, expose, generate_instance,
                           plan_instruction, render_dialogue)
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
assert len(DOMAINS) == 6 and len(GRAPHS) == 6

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
vocabs = {d: {a for a, _ in DOMAINS[d]["actions"]} for d in DOMAINS}
for d1 in vocabs:
    for d2 in vocabs:
        if d1 < d2:
            assert not (vocabs[d1] & vocabs[d2]), f"{d1}/{d2} share actions"

# Every graph is satisfiable -- a full ordering exists.
for inst in INSTANCES:
    topo_order(inst)
    topo_order(inst, inst.constraints)

# SUPERSESSION CLOSURE: lifting required(a) must also lift before(a, ...),
# or a plan that correctly omits `a` is punished by an orphaned ordering
# rule. Found in validation on brewery-twochain. The check: after the lift,
# a valid plan omitting the lifted action must exist.
for inst in INSTANCES:
    ann = {c.id: c for c in inst.constraints}[inst.announced_supersession]
    if ann.kind != "required":
        continue
    plan = [a for a in topo_order(inst) if a != ann.a]
    chk = check_plan(plan_json(plan), inst)
    assert chk.violated == [], (
        f"{inst.id}: omitting the lifted action {ann.a} still violates "
        f"{chk.violated} -- the supersession closure is incomplete")
    # And every orphaned ordering rule really was lifted.
    orphans = {c.id for c in inst.constraints
               if c.kind == "before" and c.a == ann.a}
    assert orphans <= inst.superseded, (inst.id, orphans - inst.superseded)

# NULL CONTROL: echoing the printed vocabulary order must NOT work.
#
# In the first build every `before` edge ran low->high slot index and
# plan_instruction printed the actions in slot order, so the printed list WAS a
# valid topological order. A policy that echoed it and never read the dialogue
# scored 36/36 success in every exposure condition, including `neither`. The
# benchmark had no floor and no measured value could be attributed to reading
# anything. Found by adversarial audit, not by this suite -- which is why the
# control is now permanent.
echo_wins = sum(
    check_plan(plan_json(list(i.actions)), i).success for i in INSTANCES)
assert echo_wins <= 4, (
    f"echo-the-prompt-order scores {echo_wins}/36 -- the printed vocabulary is "
    "leaking a valid ordering again")

# It must still be SOLVABLE, or the fix has just made it impossible.
assert all(check_plan(plan_json(topo_order(i)), i).success for i in INSTANCES)

# The two permutations must be independent: slot order and print order should
# not coincide across instances.
same = sum(tuple(i.actions) == tuple(
    dict(DOMAINS[i.domain]["actions"]).keys()) for i in INSTANCES)
assert same < len(INSTANCES), "print order never permuted"

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
        assert m.speaker in ("Operations Lead", "Safety Auditor")
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
        low = text.lower()
        for term in FORBIDDEN:
            assert term.lower() not in low, (inst.id, condition, term)
        for c in inst.constraints:
            assert c.id not in text, (inst.id, condition, c.id)
        # The action vocabulary appears ONLY in the plan instruction.
        for a in inst.actions:
            assert a not in visible, (inst.id, condition, a)
            assert a in plan_instruction(inst), (inst.id, a)

print("no hidden-state leakage:     OK")

# -- Deterministic regeneration from seed --------------------------------

for d in DOMAINS:
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
# direction. Build a plan that violates the lifted rule on purpose.
ann = {c.id: c for c in inst.constraints}[inst.announced_supersession]
if ann.kind == "before":
    p2 = topo_order(inst)
    ia, ib = p2.index(ann.a), p2.index(ann.b)
    p2[ia], p2[ib] = ann.b, ann.a
else:
    p2 = [a for a in topo_order(inst) if a != ann.a]
used = supersession_respected(inst, pres, check_plan(plan_json(p2), inst))
assert used["exercised"] == 1 and used["rate"] == 1.0, used

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
