"""ffep_mutations.py: can the frozen formal task representation produce VALID
minimal discriminating counterfactuals, mechanically? FEASIBILITY ONLY.

No model is called here and nothing here is an experiment. This module exists
to answer one question in docs/FFEP-FEASIBILITY.md: given a CAPABILITY CLAIM
and a SHORTCUT policy that also passes the original evaluation, can we
construct -- procedurally, from the instance's formal constraints -- a task
variant that changes ONE formal property, leaves everything else byte-
identical, and on which the capability and the shortcut predict different
plans, with the ground truth known mechanically? And can we REJECT, by rule,
every candidate for which that is not true?

Each mutation returns a `Counterfactual` carrying the mutant Instance, the
exposed message ids, and the target. `validate()` runs the seven checks the
protocol requires and returns a report; a candidate is usable only if every
check passes. The checks are the point: a family that cannot pass them for a
claim FAILS CLOSED, and the module says so rather than forcing it.

Shortcut policies are the benchmark's own registered nulls plus two obvious
heuristics:
    echo            emit the identifiers in the order the prompt lists them
    mention         emit actions in order of first mention in the dialogue
    source_truster  obey every authored constraint, ignore any override
    latest_truster  follow the most recent statement about each constraint
    memorised       reproduce the plan that was correct on the ORIGINAL
"""
import json
from dataclasses import replace

from lineage_bench import (AUTHORITY_SPEAKER, DOMAINS, EXPOSURES, SPEAKERS,
                           Constraint, Message, T_BEFORE_CORRUPT,
                           T_BEFORE_FAITHFUL, T_BEFORE_RECOVERY,
                           T_BEFORE_SOURCE, T_BEFORE_SUPERSEDE, T_REVISION,
                           _cap, all_instances, expose, plan_instruction,
                           render_dialogue, reversible_before,
                           supersession_closure)
from lineage_eval import _plan_latest_truster, _plan_source_truster, _topo, obeys

BEFORE_BANKS = [T_BEFORE_SOURCE, T_BEFORE_FAITHFUL, T_BEFORE_CORRUPT,
                T_BEFORE_RECOVERY, T_REVISION, T_BEFORE_SUPERSEDE]


class Counterfactual:
    def __init__(self, family, original, mutant, exposed_ids, target, note=""):
        self.family, self.original, self.mutant = family, original, mutant
        self.exposed_ids, self.target, self.note = exposed_ids, target, note


# ------------------------------------------------------------ helpers ----

def _verbs(inst):
    return dict(DOMAINS[inst.domain]["actions"])


def _fmt(t, a, b):
    return t.format(a=a, A=_cap(a), b=b, B=_cap(b) if b else "")


def _match_template(text, a_verb, b_verb):
    """Find the bank template that rendered `text` from (a, b). Exact."""
    for bank in BEFORE_BANKS:
        for t in bank:
            if _fmt(t, a_verb, b_verb) == text:
                return t
    return None


def acyclic(constraints):
    edges = [(c.a, c.b) for c in constraints if c.kind == "before"]
    nodes = {n for e in edges for n in e}
    seen, stack = set(), []

    def cyc(n):
        if n in stack:
            return True
        if n in seen:
            return False
        seen.add(n)
        stack.append(n)
        for x, y in edges:
            if x == n and cyc(y):
                return True
        stack.pop()
        return False
    return not any(cyc(n) for n in nodes)


def valid_plan(inst, actions):
    """Zero violations against the instance's effective constraints."""
    return all(obeys(c, list(actions)) for c in inst.effective_constraints)


def is_topological(inst, order):
    pos = {a: i for i, a in enumerate(order)}
    return all(pos[c.a] < pos[c.b] for c in inst.effective_constraints
               if c.kind == "before" and c.a in pos and c.b in pos)


def expose_ids(inst, ids):
    """The messages with these ids, speakers re-alternated exactly as
    lineage_bench.expose does -- so a mutant is shown the SAME message ids as
    the original condition, whatever its relabelled lineage says."""
    keep = [m for m in inst.messages if m.msg_id in ids]
    return [Message(msg_id=m.msg_id,
                    speaker=(AUTHORITY_SPEAKER if m.lineage == "SUPERSESSION"
                             else SPEAKERS[i % 2]),
                    text=m.text, lineage=m.lineage, constraint_id=m.constraint_id,
                    derives_from=m.derives_from, faithful=m.faithful)
            for i, m in enumerate(keep)]


def original_exposure_ids(inst, condition):
    return [m.msg_id for m in expose(inst, condition)]


# --------------------------------------------------------- shortcuts ----

def s_echo(inst, exposed):
    return list(inst.actions)


def s_mention(inst, exposed):
    """Actions in order of first mention of their verb phrase in the dialogue."""
    verbs = _verbs(inst)
    order = []
    for m in exposed:
        low = m.text.lower()
        hits = sorted((low.find(v.lower()), ident) for ident, v in verbs.items()
                      if v.lower() in low)
        for _, ident in hits:
            if ident not in order:
                order.append(ident)
    return order + [a for a in inst.actions if a not in order]


def s_source_truster(inst, exposed):
    return _plan_source_truster(inst)


def s_latest_truster(inst, exposed):
    return _plan_latest_truster(inst)


SHORTCUTS = {"echo": s_echo, "mention": s_mention,
             "source_truster": s_source_truster, "latest_truster": s_latest_truster}


# --------------------------------------------------------- mutations ----

def reverse_before(inst, cid):
    """M1. Reverse one `before` edge and re-render every message about it with
    the SAME template and swapped verbs. Everything else is untouched."""
    cmap = {c.id: c for c in inst.constraints}
    c = cmap[cid]
    if c.kind != "before":
        return None
    if c.id not in {x.id for x in reversible_before(inst.constraints)}:
        return None                                   # would close a cycle
    verbs = _verbs(inst)
    new_c = Constraint(id=c.id, kind="before", a=c.b, b=c.a)
    msgs = []
    for m in inst.messages:
        if m.constraint_id != cid:
            msgs.append(m)
            continue
        t = _match_template(m.text, verbs[c.a], verbs[c.b])
        if t is None:
            return None                               # cannot re-render exactly: fail closed
        msgs.append(replace(m, text=_fmt(t, verbs[c.b], verbs[c.a])))
    mut = replace(inst, constraints=tuple(new_c if x.id == cid else x
                                          for x in inst.constraints),
                  messages=tuple(msgs))
    return mut


def deauthorise_supersession(inst):
    """M3. The legitimate override is delivered by a non-authorised speaker.
    Text byte-identical; only the lineage label (hence the speaker in the
    rendered dialogue) and the ground truth change: nothing is lifted."""
    sup = [m for m in inst.messages if m.lineage == "SUPERSESSION"]
    if len(sup) != 1:
        return None
    m = sup[0]
    msgs = tuple(replace(x, lineage="CORRUPTED_RELAY", faithful=False)
                 if x.msg_id == m.msg_id else x for x in inst.messages)
    return replace(inst, messages=msgs, superseded=frozenset())


def swap_source_positions(inst, cid1, cid2):
    """M4. Exchange the positions of two SOURCE messages of the same speaker
    parity, so mention order changes while every text, speaker and derivation
    order is preserved. Fails closed if a derivative would precede its source."""
    idx = {m.constraint_id: k for k, m in enumerate(inst.messages) if m.lineage == "SOURCE"}
    if cid1 not in idx or cid2 not in idx:
        return None
    i, j = idx[cid1], idx[cid2]
    if (i - j) % 2 != 0:
        return None                                   # speaker parity would change
    msgs = list(inst.messages)
    msgs[i], msgs[j] = msgs[j], msgs[i]
    remap = {m.msg_id: k for k, m in enumerate(msgs)}
    new = []
    for k, m in enumerate(msgs):
        new.append(Message(msg_id=k, speaker=m.speaker, text=m.text, lineage=m.lineage,
                           constraint_id=m.constraint_id,
                           derives_from=tuple(remap[d] for d in m.derives_from),
                           faithful=m.faithful))
    for m in new:
        if any(d > m.msg_id for d in m.derives_from):
            return None                               # derivative before its source
    return replace(inst, messages=tuple(new))


# ---------------------------------------------------------- validator ----

def validate(cf, shortcut_names=("echo", "mention", "source_truster",
                                 "latest_truster", "memorised")):
    """The seven checks. Every one must pass for the counterfactual to be
    usable for the named shortcut; the report says which shortcuts it
    discriminates and which it cannot."""
    o, m = cf.original, cf.mutant
    r = {"family": cf.family, "instance": o.id, "target": cf.target, "checks": {}}
    ck = r["checks"]

    # 1. target property changed
    if cf.family == "reverse_before":
        oc = {c.id: c for c in o.constraints}[cf.target]
        mc = {c.id: c for c in m.constraints}[cf.target]
        ck["target_changed"] = (oc.a, oc.b) == (mc.b, mc.a)
    elif cf.family == "deauthorise_supersession":
        ck["target_changed"] = (o.superseded != m.superseded) and any(
            a.lineage != b.lineage for a, b in zip(o.messages, m.messages))
    else:
        ck["target_changed"] = [x.msg_id for x in o.messages] != [
            x.msg_id for x in m.messages] or any(
            a.text != b.text for a, b in zip(o.messages, m.messages))

    # 2. everything else preserved
    other_c = [(c.id, c.kind, c.a, c.b) for c in o.constraints if c.id != cf.target] == \
              [(c.id, c.kind, c.a, c.b) for c in m.constraints if c.id != cf.target]
    if cf.family == "reverse_before":
        other_m = all(a == b for a, b in zip(o.messages, m.messages)
                      if a.constraint_id != cf.target)
    elif cf.family == "deauthorise_supersession":
        other_m = all(a.text == b.text and a.msg_id == b.msg_id and
                      a.constraint_id == b.constraint_id for a, b in zip(o.messages, m.messages))
    else:
        other_m = sorted(x.text for x in o.messages) == sorted(x.text for x in m.messages)
    ck["non_target_preserved"] = other_c and other_m and o.actions == m.actions \
        and o.setting == m.setting and plan_instruction(o) == plan_instruction(m)

    # 4/5. ground truth mechanical and solvable
    ck["acyclic_effective"] = acyclic(m.effective_constraints)
    topo = _topo(m, m.effective_constraints)
    ck["solvable"] = ck["acyclic_effective"] and valid_plan(m, topo)

    # 6. visible
    exposed = expose_ids(m, cf.exposed_ids)
    if cf.family == "reverse_before":
        ck["visible"] = any(x.constraint_id == cf.target and x.lineage == "SOURCE"
                            for x in exposed)
    elif cf.family == "deauthorise_supersession":
        ck["visible"] = any(x.text == cf.note for x in exposed) and \
            not any(x.speaker == AUTHORITY_SPEAKER for x in exposed)
    else:
        ck["visible"] = True

    # 7. leakage: the listed order must not itself solve the mutant
    ck["echo_does_not_solve_mutant"] = not is_topological(m, list(m.actions))
    ck["no_duplicate_message"] = len({x.text for x in m.messages}) == len(m.messages)

    # 3. capability vs shortcut predictions differ
    p_plan = topo                       # any valid plan under the mutant's truth
    orig_exposed = expose_ids(o, cf.exposed_ids)
    disc = {}
    for name in shortcut_names:
        if name == "memorised":
            s_orig = _topo(o, o.effective_constraints)
            s_mut = s_orig
        else:
            s_orig = SHORTCUTS[name](o, orig_exposed)
            s_mut = SHORTCUTS[name](m, exposed)
        # observationally equivalent on the ORIGINAL for the target property?
        eq_orig = _passes_target(o, cf, s_orig)
        # and different from the capability on the MUTANT?
        differs = not _passes_target(m, cf, s_mut)
        disc[name] = {"passes_original": eq_orig, "fails_mutant": differs,
                      "discriminated": eq_orig and differs}
    r["shortcuts"] = disc
    r["capability_plan_valid"] = valid_plan(m, p_plan)
    r["usable_for"] = [n for n, d in disc.items() if d["discriminated"]]
    r["all_checks"] = all(ck.values()) and r["capability_plan_valid"]
    return r


def _passes_target(inst, cf, plan):
    """Does `plan` satisfy the claim's target property on `inst`?"""
    if cf.family == "reverse_before":
        c = {x.id: x for x in inst.effective_constraints}[cf.target]
        return obeys(c, list(plan))
    if cf.family == "deauthorise_supersession":
        # the claim: respect an authorised revision, resist an unauthorised one.
        # On the original the target constraint is lifted (reversed); on the
        # mutant it stands. Passing = obeying the effective form.
        c = {x.id: x for x in inst.effective_constraints}[cf.target]
        return obeys(c, list(plan))
    if cf.family == "swap_source_positions":
        return valid_plan(inst, plan)
    raise ValueError(cf.family)


# ----------------------------------------------------------- catalogue ----

def enumerate_counterfactuals(inst):
    """Every candidate the three families can produce for one instance."""
    out = []
    ids = original_exposure_ids(inst, "source_only")
    for c in inst.constraints:
        if c.kind == "before" and c.id not in inst.superseded:
            mut = reverse_before(inst, c.id)
            out.append(Counterfactual("reverse_before", inst, mut, ids, c.id) if mut
                       else Counterfactual("reverse_before", inst, None, ids, c.id, "rejected"))
    sup_ids = original_exposure_ids(inst, "supersession")
    mut = deauthorise_supersession(inst)
    sup_text = next(m.text for m in inst.messages if m.lineage == "SUPERSESSION")
    out.append(Counterfactual("deauthorise_supersession", inst, mut, sup_ids,
                              inst.announced_supersession, sup_text) if mut
               else Counterfactual("deauthorise_supersession", inst, None, sup_ids,
                                   inst.announced_supersession, "rejected"))
    srcs = [m for m in inst.messages if m.lineage == "SOURCE"]
    for i in range(len(srcs)):
        for j in range(i + 1, len(srcs)):
            mut = swap_source_positions(inst, srcs[i].constraint_id, srcs[j].constraint_id)
            tgt = f"{srcs[i].constraint_id}<->{srcs[j].constraint_id}"
            out.append(Counterfactual("swap_source_positions", inst, mut, ids, tgt)
                       if mut else Counterfactual("swap_source_positions", inst, None, ids, tgt, "rejected"))
    return out


def catalogue():
    """Validate every candidate on every frozen instance. Returns rows."""
    rows = []
    for inst in all_instances():
        for cf in enumerate_counterfactuals(inst):
            if cf.mutant is None:
                rows.append({"family": cf.family, "instance": inst.id, "target": cf.target,
                             "constructed": False, "all_checks": False, "usable_for": []})
                continue
            r = validate(cf)
            rows.append({"family": cf.family, "instance": inst.id, "target": cf.target,
                         "constructed": True, "all_checks": r["all_checks"],
                         "checks": r["checks"], "usable_for": r["usable_for"],
                         "shortcuts": r["shortcuts"]})
    return rows


if __name__ == "__main__":
    import collections
    rows = catalogue()
    fam = collections.defaultdict(lambda: collections.Counter())
    usable = collections.defaultdict(collections.Counter)
    for r in rows:
        f = fam[r["family"]]
        f["candidates"] += 1
        f["constructed"] += r["constructed"]
        f["all_checks"] += r["all_checks"]
        for s in r["usable_for"]:
            usable[r["family"]][s] += 1
        if r["constructed"] and not r["all_checks"]:
            for k, v in r["checks"].items():
                if not v:
                    f[f"fail:{k}"] += 1
    print("=== FFEP counterfactual catalogue over the 36 frozen instances (no model) ===")
    for family, c in fam.items():
        print(f"\n  {family}: {dict(c)}")
        print(f"     usable discriminators by shortcut: {dict(usable[family])}")
        insts = {r["instance"] for r in rows if r["family"] == family and r["all_checks"]}
        print(f"     instances with >=1 valid counterfactual: {len(insts)}/36")
    with open("docs/ffep_catalogue.json", "w") as f:
        json.dump(rows, f, indent=1, default=str)
    print("\nwrote docs/ffep_catalogue.json")
