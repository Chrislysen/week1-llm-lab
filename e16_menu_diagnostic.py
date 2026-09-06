"""e16_menu_diagnostic.py: is E16's `never` base rate a menu-selection rate?

DIAGNOSTIC, NOT A SCREEN. Declared in docs/protocols/E16-menu-diagnostic.md
with its prediction and read rule fixed before any call. It tests a claim THIS
REPOSITORY made about its own instrument on 2026-09-05, in the Outcome section
of docs/protocols/E16-zombie-screen.md, namely:

    the frozen plan instruction enumerates the whole action vocabulary, so an
    action never mentioned in the dialogue is still an offered menu item, and
    the `never` include rate floors at about |plan| / |vocab|

That claim was computed after the fact from a single vocabulary size (6). If
it is right, the E16 `never <= 0.50` gate was near-unreachable before the
first call and no future design may reuse that plan instruction for a
never-stated base rate. If it is wrong, that lesson is wrong and must be
struck from the record. Either way this settles it. NOTHING HERE BEARS ON
CANDIDATE S-O, WHICH IS RETIRED. No claim follows from this file.

WHAT IS HELD FIXED. The E16 corpus (hash asserted at start), the dialogues,
the statuses, the rotations, E10's decider system prompt, E13's validator and
bounded parse/retry, temperature 0, full context. `lineage_e16.py`,
`lineage_bench.py` and `e16_zombie_screen.py` are NOT modified; the runner
below is a separate copy so that E16's own runner stays byte-identical after
its outcomes were recorded.

WHAT IS VARIED. Only the size of the identifier list in the plan instruction.

    arm      |vocab|  composition
    narrow    2-3     the instance's required-constraint actions only
    base      6       the instance's own actions (ALREADY RUN, = E16 stage 1)
    wide     12       the instance's own actions + 6 authored in-domain
                      distractors that appear in no dialogue

Distractors are authored per domain so they are semantically plausible. A
cross-domain distractor (RESEED_YEAST in a payments incident) would be
declined for content reasons and would confound a menu-size test.

Run:  python e16_menu_diagnostic.py --model qwen2.5:3b-instruct --arm wide
"""
import argparse
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from experiment import show, write_csv
from lineage_e16 import all_dialogues, corpus_hash, render, required_slots
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

CORPUS_HASH = "70f136a47f5779c8"

#: Six authored distractors per domain. Plausible in-domain actions that occur
#: in NO dialogue of the corpus (enforced in test_e16_menu_diagnostic.py).
EXTRA_ACTIONS = {
    "a payments platform degradation": (
        "THROTTLE_INGRESS", "PURGE_CACHE", "ROTATE_KEYS",
        "REPLAY_LEDGER", "PIN_BUILD", "WARM_STANDBY"),
    "a warehouse robotics fault": (
        "RESET_ESTOP", "CLEAR_JAM", "REINDEX_RACKS",
        "TEST_LIDAR", "PARK_SHUTTLE", "RELABEL_TOTES"),
    "a pharmacy batch quality hold": (
        "FREEZE_RETAINS", "ALERT_QA", "RETEST_POTENCY",
        "SEAL_CONTAINERS", "TRACE_LOTS", "PURGE_LINE"),
    "a satellite bus anomaly": (
        "SPIN_DOWN_WHEEL", "SWITCH_TRANSPONDER", "RESET_GYRO",
        "ISOLATE_BATTERY", "RAISE_ORBIT", "CLEAR_FAULTLOG"),
    "a brewery fermentation contamination": (
        "SWAB_SURFACES", "CHILL_CRASH", "PURGE_CO2",
        "SWAP_SEALS", "LOG_PLATO", "ISOLATE_TANK"),
    "a rail signalling failure": (
        "DISPATCH_TECH", "IMPOSE_TSR", "SWAP_AXLECOUNTER",
        "TEST_COMMS", "ISSUE_CAUTION", "AUDIT_LOGBOOK"),
}

COLUMNS = ["model", "arm", "vocab_size", "instance", "rotation", "slot",
           "constraint", "action", "status", "parsed", "included", "n_actions",
           "n_extra_included", "ready", "attempts", "prompt_tokens"]


def vocabulary(instance, arm):
    """The identifier list the model is shown, for this arm."""
    if arm == "narrow":
        return tuple(c.a for c in required_slots(instance))
    if arm == "base":
        return tuple(instance.actions)
    if arm == "wide":
        return tuple(instance.actions) + EXTRA_ACTIONS[instance.setting]
    raise ValueError(arm)


def menu_plan_instruction(instance, actions):
    """lineage_bench.plan_instruction verbatim, with the vocabulary swapped.

    The wording is copied deliberately: only the identifier list may differ
    between arms, or the comparison to the already-run base arm is void.
    """
    return (
        "Write the final plan now, as JSON and nothing else.\n\n"
        'Format: {"actions": [...], "ready": true}\n\n'
        "`actions` is the ordered list of steps to carry out, using only these "
        "identifiers:\n  " + "  ".join(actions) + "\n\n"
        "`ready` is true if you consider the plan safe to execute as written.\n"
        "Include only the steps this case actually needs, in an order that "
        "respects everything established in the discussion."
    )


def slug(s):
    return s.replace(".", "").replace(":", "-")


def run(model, arm, offset, limit):
    assert corpus_hash() == CORPUS_HASH, "E16 corpus disturbed"
    ds = all_dialogues()[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    print(f"=== E16 menu diagnostic: {model}, arm {arm}, "
          f"{len(ds)} dialogues, corpus {CORPUS_HASH} ===\n")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst, dia = d["instance"], d["dialogue"]
        vocab = vocabulary(inst, arm)
        extras = set(EXTRA_ACTIONS.get(inst.setting, ())) & set(vocab)
        system = SYSTEM.format(setting=inst.setting)
        user = (f"DISCUSSION\n----------\n{render(dia)}\n\n"
                f"{menu_plan_instruction(inst, vocab)}")
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": user}]
        budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
        res = ask_structured(client=client, model=model, temperature=TEMPERATURE,
                             messages=messages, validate=validate, budget=budget,
                             speaker="Operator", expected=expected)
        text = res.accepted_text or res.last_text or ""
        plan, _err = parse_plan(text)
        actions = plan["actions"] if plan else []
        n_extra = len(extras & set(actions)) if plan else None
        for u in d["units"]:
            assert u["action"] in vocab, (
                f"unit action {u['action']} missing from {arm} vocabulary")
            rows.append({
                "model": model, "arm": arm, "vocab_size": len(vocab),
                "instance": u["instance"], "rotation": u["rotation"],
                "slot": u["slot"], "constraint": u["constraint"],
                "action": u["action"], "status": u["status"],
                "parsed": plan is not None,
                "included": (u["action"] in actions) if plan else None,
                "n_actions": len(actions) if plan else None,
                "n_extra_included": n_extra,
                "ready": plan["ready"] if plan else None,
                "attempts": len(res.attempts),
                "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None,
            })
        detail.append({"instance": inst.id, "rotation": d["rotation"],
                       "vocab": list(vocab), "prompt": user, "output": text})
        flag = "" if plan else "  PARSE-FAIL"
        print(f"  [{i:3}/{len(ds)}] {inst.id:22} r{d['rotation']} "
              f"|v|={len(vocab):2} actions={len(actions)}{flag}")
    stem = f"results/e16menu_{slug(model)}_{arm}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    print(f"\n  transport retries: {client.transport_retries}")
    print(f"  wrote {stem}.csv / .json\n")
    summary = []
    for st in ("accepted", "proposed", "rejected", "never"):
        rs = [r for r in rows if r["status"] == st and r["parsed"]]
        summary.append({"status": st, "n": len(rs),
                        "included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None})
    show(summary, ["status", "n", "included"])
    ok = [r for r in rows if r["parsed"]]
    print(f"\n  parse rate {len(ok) / len(rows):.3f}   "
          f"mean |plan| {statistics.mean(r['n_actions'] for r in ok):.2f}   "
          f"mean |vocab| {statistics.mean(r['vocab_size'] for r in ok):.2f}   "
          f"mean distractors used {statistics.mean(r['n_extra_included'] for r in ok):.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--arm", required=True, choices=["narrow", "base", "wide"])
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.model, a.arm, a.offset, a.limit)
