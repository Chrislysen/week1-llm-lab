"""phaseb_fixtures.py: fresh Phase B fixtures, manifest and request schedule.

ZERO MODEL CALLS. Building and validating fixtures only. Running the receiver
campaign is NOT authorised here (see docs/protocols/PHASE-B-bundle-observability.md).

STRUCTURE
---------
8 study tasks, each with 2 recipient contexts and 4 candidate messages, and all
16 subsets enumerated per context. **The 2 contexts are NESTED observations on
one task, not independent tasks** -- the unit of independence is the task, so
the study has 8 units, not 16.

8 qualification fixtures are SEPARATE tasks (own salt, disjoint domain/graph
pairs), used only to ask whether the receiver can solve this family at all when
given full evidence.

HOW A TASK IS MADE
------------------
From a fresh `lineage_bench` instance (salt below, so it collides with no
previously used corpus) we take the authored constraints and their SOURCE
message texts. The last four constraints become the four candidate messages
A/B/C/D; the remaining ones are shared recipient context present in both
variants. The two variants then differ in exactly one thing: variant
`knows_A` additionally pre-knows candidate A's constraint, variant `knows_B`
pre-knows candidate B's. That is the "recipient already has it" contrast the
direction rests on, and it changes which bundle is useful without changing the
scoring key.

SCORING KEY. Always the full authored constraint set, identical for both
variants. Constraints that are neither pre-known nor delivered can only be
satisfied by luck -- that is the point.

BUDGET UNIT. Rendered words (`agentcom_bundle.serialised_cost`). Model tokens
are a different quantity and are recorded only once calls happen.
"""
import hashlib
import json
import random
from itertools import permutations

import lineage_bench as lb
import lineage_eval as le
from agentcom_bundle import (Candidate, DecisionPoint, SubsetOutcome,
                             all_subsets, render_bundle, serialised_cost,
                             additive_estimate)

STUDY_SALT = "phaseb-v1"
QUAL_SALT = "phaseb-qual-v1"
MODEL = "llama3.2:3b"
DECODING = {"temperature": 0.0, "num_predict": 300}
SCORER = "lineage_eval.check_plan/authored-constraints"

#: 8 study tasks. Distinct (domain, graph) pairs, spread over both factors.
STUDY_COMBOS = [("payments", "join"), ("robotics", "star"), ("pharmacy", "fork"),
                ("satellite", "twochain"), ("brewery", "diamond"),
                ("rail", "chain"), ("payments", "star"), ("robotics", "join")]

#: 8 qualification fixtures. Disjoint pairs AND a different salt.
QUAL_COMBOS = [("pharmacy", "twochain"), ("satellite", "fork"),
               ("brewery", "chain"), ("rail", "diamond"), ("payments", "fork"),
               ("robotics", "chain"), ("pharmacy", "star"), ("satellite", "join")]

CIDS = ("A", "B", "C", "D")
QUAL_REALISATIONS = 2

CEILING = {"qualification": 16, "subset": 256, "reserve": 16, "total": 288}


def _seed(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def source_text(inst, cid):
    """The SOURCE statement of constraint `cid`; every constraint has one."""
    for m in inst.messages:
        if m.lineage == "SOURCE" and m.constraint_id == cid:
            return m.text
    raise KeyError(f"{inst.id}: no SOURCE message for {cid}")


def build_task(domain, graph, salt=STUDY_SALT):
    """One task: 4 candidates, shared context, 2 nested recipient variants."""
    inst = lb.generate_instance(domain, graph, salt=salt)
    ids = sorted(c.id for c in inst.constraints)
    if len(ids) < 5:
        raise ValueError(f"{inst.id}: needs >=5 constraints for 4 candidates")
    cand_ks, shared_ks = ids[-4:], ids[:-4]
    candidates = tuple(Candidate(cid=c, text=source_text(inst, k),
                                 source_id=k, version="authored")
                       for c, k in zip(CIDS, cand_ks))
    variants = {"knows_A": tuple(shared_ks) + (cand_ks[0],),
                "knows_B": tuple(shared_ks) + (cand_ks[1],)}
    return {"instance": inst, "task_id": inst.id, "candidates": candidates,
            "shared_context_ids": tuple(shared_ks), "variants": variants}


def render_context(inst, known_ids) -> str:
    lines = [f"Setting: {inst.setting}", "", "What you already know:"]
    lines += [f"- {source_text(inst, k)}" for k in known_ids]
    return "\n".join(lines)


def render_prompt(task, variant, subset) -> str:
    """The literal recipient prompt for one (variant, subset). Deterministic."""
    inst = task["instance"]
    parts = [render_context(inst, task["variants"][variant])]
    bundle = render_bundle(task["candidates"], subset)
    if bundle:
        parts += ["", bundle]
    parts += ["", lb.plan_instruction(inst)]
    return "\n".join(parts)


def reference_plan(inst):
    """A full ordering satisfying every AUTHORED constraint, or None."""
    for p in permutations(inst.actions):
        if all(le.obeys(c, list(p)) for c in inst.constraints):
            return list(p)
    return None


def score_response(text, inst):
    """Executable scoring. Blind to variant and subset by construction."""
    return le.check_plan(text, inst, constraints=inst.constraints)


# --- manifest and schedule ------------------------------------------------


def decision_points(tasks):
    """One DecisionPoint per (task, variant). Execution fields stay empty."""
    dps = []
    for t in tasks:
        for variant in sorted(t["variants"]):
            full = frozenset(CIDS)
            dps.append(DecisionPoint(
                dp_id=f"{t['task_id']}|{variant}",
                task_id=t["task_id"],
                recipient_prompt=render_prompt(t, variant, frozenset()),
                recipient_context=render_context(t["instance"],
                                                 t["variants"][variant]),
                candidates=t["candidates"],
                budget=serialised_cost(t["candidates"], full),
                model=MODEL, decoding=dict(DECODING),
                process_id=f"block:{t['task_id']}|{variant}",
                request_position=0))
    return dps


def schedule(tasks):
    """Reproducible request schedule.

    One PROCESS BLOCK per (task, variant): all 16 subsets for that decision
    point run inside one process. Subset order is randomised per block from a
    seeded RNG, and the realised request position is recorded, so an order or
    position effect can be detected rather than assumed absent (the E28-C
    lesson). Blocks themselves are ordered by a seeded shuffle too.
    """
    blocks = []
    for t in tasks:
        for variant in sorted(t["variants"]):
            block_id = f"{t['task_id']}|{variant}"
            subsets = sorted((tuple(sorted(s)) for s in all_subsets(CIDS)),
                             key=lambda s: (len(s), s))
            rng = random.Random(_seed("subset-order", block_id))
            rng.shuffle(subsets)
            calls = [{"process_block": block_id, "request_position": i,
                      "dp_id": block_id, "task_id": t["task_id"],
                      "variant": variant, "subset": list(s),
                      "rendered_words": serialised_cost(t["candidates"], frozenset(s)),
                      "additive_estimate_words": additive_estimate(
                          t["candidates"], frozenset(s)),
                      "kind": "subset"}
                     for i, s in enumerate(subsets, 1)]
            blocks.append({"process_block": block_id, "kind": "subset",
                           "n_calls": len(calls), "calls": calls})
    rng = random.Random(_seed("block-order", STUDY_SALT))
    rng.shuffle(blocks)
    return blocks


def qualification_schedule(qual_tasks):
    """Full-evidence calls on the separate qualification fixtures.

    EACH REALISATION IS ITS OWN PROCESS BLOCK. At `temperature 0.0` two repeats
    inside one process are bit-identical, so same-process repeats would measure
    nothing. E28-D found this instrument is bit-reproducible WITHIN a process
    and occasionally shifts ACROSS processes, so cross-process is the only
    instability these repeats can detect -- and it is the instability that
    matters for a table collected block by block.

    LIMITATION, STATED: this does NOT estimate decoding-sampling variability.
    That would need a non-zero temperature and its own call allocation.
    """
    blocks = []
    for t in qual_tasks:
        for r in range(1, QUAL_REALISATIONS + 1):
            block_id = f"qual:{t['task_id']}|r{r}"
            calls = [{"process_block": block_id, "request_position": 1,
                      "dp_id": f"qual:{t['task_id']}", "task_id": t["task_id"],
                      "variant": "knows_A", "subset": list(CIDS),
                      "rendered_words": serialised_cost(t["candidates"],
                                                        frozenset(CIDS)),
                      "realisation": r, "kind": "qualification"}]
            blocks.append({"process_block": block_id, "kind": "qualification",
                           "n_calls": 1, "calls": calls})
    return blocks


def manifest(tasks, qual_tasks, blocks, qual_blocks):
    n_subset = sum(b["n_calls"] for b in blocks)
    n_qual = sum(b["n_calls"] for b in qual_blocks)
    return {
        "schema_version": DecisionPoint.__dataclass_fields__[
            "schema_version"].default,
        "status": "FIXTURES PREPARED, ZERO MODEL CALLS, NOT AUTHORISED TO RUN",
        "budget_unit": "rendered_words",
        "token_note": "model prompt/completion tokens are a different quantity; "
                      "unpopulated until calls occur",
        "study_salt": STUDY_SALT, "qualification_salt": QUAL_SALT,
        "model": MODEL, "decoding": DECODING, "scorer": SCORER,
        "independence": {
            "unit_of_independence": "task",
            "n_independent_study_tasks": len(tasks),
            "recipient_contexts_per_task": 2,
            "note": "the 2 recipient contexts are NESTED observations on one "
                    "task; they are not independent tasks",
        },
        "counts": {"study_tasks": len(tasks), "qualification_tasks": len(qual_tasks),
                   "candidates_per_task": len(CIDS),
                   "subsets_per_context": 2 ** len(CIDS),
                   "subset_calls": n_subset, "qualification_calls": n_qual},
        "ceiling": CEILING,
        "ceiling_check": {
            "planned_subset_calls": n_subset,
            "planned_qualification_calls": n_qual,
            "planned_total": n_subset + n_qual,
            "reserve": CEILING["reserve"],
            "within_ceiling": n_subset + n_qual + CEILING["reserve"] <= CEILING["total"],
            "note": "retries and failures consume the ceiling; there are no "
                    "unlogged calls",
        },
        "tasks": [{"task_id": t["task_id"],
                   "domain": t["instance"].domain, "graph": t["instance"].graph,
                   "shared_context_ids": list(t["shared_context_ids"]),
                   "candidates": [c.to_dict() for c in t["candidates"]],
                   "variants": {k: list(v) for k, v in t["variants"].items()},
                   "n_constraints": len(t["instance"].constraints),
                   "reference_plan": reference_plan(t["instance"])}
                  for t in tasks],
        "qualification_tasks": [
            {"task_id": t["task_id"], "domain": t["instance"].domain,
             "graph": t["instance"].graph,
             "reference_plan": reference_plan(t["instance"])}
            for t in qual_tasks],
    }


# --- validation (zero model calls) ---------------------------------------


def validate(tasks, qual_tasks, blocks, qual_blocks):
    """Fixture checks only. Says NOTHING about whether a model can solve these."""
    rep, fail = [], 0

    def check(name, ok, detail=""):
        nonlocal fail
        rep.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fail += 1

    study_ids = {t["task_id"] for t in tasks}
    qual_ids = {t["task_id"] for t in qual_tasks}
    check("study and qualification fixtures are disjoint",
          not (study_ids & qual_ids), f"{len(study_ids)}+{len(qual_ids)}")
    check("all study task ids unique", len(study_ids) == len(tasks))

    for t in tasks + qual_tasks:
        inst = t["instance"]
        ref = reference_plan(inst)
        check(f"{t['task_id']}: reference solution exists", ref is not None)
        if ref is None:
            continue
        good = json.dumps({"actions": ref, "ready": True})
        check(f"{t['task_id']}: reference scores success",
              score_response(good, inst).success)
        bad_order = json.dumps({"actions": list(reversed(ref)), "ready": True})
        check(f"{t['task_id']}: reversed order rejected",
              not score_response(bad_order, inst).success)
        missing = json.dumps({"actions": ref[:-1], "ready": True})
        check(f"{t['task_id']}: dropping an action is not silently accepted",
              not score_response(missing, inst).success
              or ref[-1] not in [c.a for c in inst.constraints if c.kind == "required"])
        check(f"{t['task_id']}: unparseable output rejected",
              not score_response("I cannot answer that.", inst).parsed)
        check(f"{t['task_id']}: ready=false is not success",
              not score_response(json.dumps({"actions": ref, "ready": False}),
                                 inst).success)

    for t in tasks:
        check(f"{t['task_id']}: 4 candidates", len(t["candidates"]) == 4)
        check(f"{t['task_id']}: candidate texts non-empty and distinct",
              len({c.text for c in t["candidates"]}) == 4
              and all(c.text.strip() for c in t["candidates"]))
        va, vb = t["variants"]["knows_A"], t["variants"]["knows_B"]
        check(f"{t['task_id']}: variants differ in exactly one pre-known item",
              len(set(va) ^ set(vb)) == 2, f"{sorted(set(va) ^ set(vb))}")
        check(f"{t['task_id']}: variant pre-knowledge matches candidates A/B",
              va[-1] == t["candidates"][0].source_id
              and vb[-1] == t["candidates"][1].source_id)
        empty = render_prompt(t, "knows_A", frozenset())
        full = render_prompt(t, "knows_A", frozenset(CIDS))
        check(f"{t['task_id']}: empty-subset prompt carries no candidate text",
              all(c.text not in empty for c in t["candidates"][2:]))
        check(f"{t['task_id']}: full-subset prompt carries every candidate",
              all(c.text in full for c in t["candidates"]))
        check(f"{t['task_id']}: rendered words exceed additive estimate",
              serialised_cost(t["candidates"], frozenset(CIDS))
              > additive_estimate(t["candidates"], frozenset(CIDS)))

    for b in blocks:
        pos = [c["request_position"] for c in b["calls"]]
        subs = [tuple(c["subset"]) for c in b["calls"]]
        check(f"{b['process_block']}: 16 distinct subsets",
              len(set(subs)) == 16 and len(subs) == 16)
        check(f"{b['process_block']}: positions are 1..16",
              sorted(pos) == list(range(1, 17)))

    again = schedule(tasks)
    check("schedule is reproducible from its seeds",
          [c["subset"] for b in again for c in b["calls"]]
          == [c["subset"] for b in blocks for c in b["calls"]])

    n = sum(b["n_calls"] for b in blocks) + sum(b["n_calls"] for b in qual_blocks)
    check("planned calls + reserve within the 288 ceiling",
          n + CEILING["reserve"] <= CEILING["total"], f"{n}+16")
    check("subset calls == 256", sum(b["n_calls"] for b in blocks) == 256)
    check("qualification calls == 16", sum(b["n_calls"] for b in qual_blocks) == 16)

    dps = decision_points(tasks)
    check("one decision point per (task, variant)", len(dps) == 2 * len(tasks))
    o = SubsetOutcome(dp_id=dps[0].dp_id, subset=("A",), rendered_words=1,
                      scorer=SCORER)
    check("unexecuted outcome has empty execution fields",
          o.score is None and o.prompt_tokens is None and not o.executed)
    return rep, fail


def main():
    tasks = [build_task(d, g) for d, g in STUDY_COMBOS]
    qual = [build_task(d, g, salt=QUAL_SALT) for d, g in QUAL_COMBOS]
    blocks, qblocks = schedule(tasks), qualification_schedule(qual)
    rep, fail = validate(tasks, qual, blocks, qblocks)

    man = manifest(tasks, qual, blocks, qblocks)
    man["validation"] = {"checks": len(rep), "failed": fail,
                         "note": "fixture validity only; says nothing about "
                                 "whether any model can solve these tasks"}
    with open("results/phaseb_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    with open("results/phaseb_schedule.jsonl", "w", encoding="utf-8") as fh:
        for b in qblocks + blocks:
            for c in b["calls"]:
                fh.write(json.dumps(c) + "\n")

    for r in rep:
        if not r["ok"]:
            print("FAIL", r["check"], r["detail"])
    print(f"validation: {len(rep) - fail}/{len(rep)} checks passed")
    print(f"planned calls: {man['ceiling_check']['planned_total']} "
          f"(+{CEILING['reserve']} reserve) vs ceiling {CEILING['total']}")
    print("wrote results/phaseb_manifest.json, results/phaseb_schedule.jsonl")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
