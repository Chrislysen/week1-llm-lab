"""e17_menu_law.py: does pinning plan length restore 1/|vocab| scaling?

INSTRUMENT STUDY, NOT A SCREEN, NOT A CLAIM. Declared in
docs/protocols/E17-menu-law.md with predictions and read rule fixed before any
call. It exists to ESTABLISH OR KILL one thing the 2026-09-06 gate could not
find in the literature (docs/E16-CANDIDATES.md, MEASUREMENT CANDIDATES):

    |plan| is ENDOGENOUS to |vocab|. Doubling the menu 6 -> 12 cut per-item
    chance by only ~22%, not 50%, because the model lengthened its plan
    (x1.54, x1.59). If that is real, normalising an adherence rate by
    action-space size does not fix the confound, because the numerator moves
    with the denominator.

The E16 menu diagnostic returned UNINFORMATIVE precisely because |plan| was
observed and never controlled. This controls it, by instruction.

DESIGN. 3 vocabulary sizes x 2 length conditions, fully crossed.

    |vocab|   6      the instance's own actions (free arm == E16 stage 1)
             12      + 6 authored in-domain distractors  (== E16 wide arm)
             24      + 18 authored in-domain distractors

    length   free    the frozen plan instruction, unmodified
             pin4    one sentence added: exactly 4 identifiers

THE DECISIVE COMPARISON. Under `pin4`, |plan| is fixed by instruction, so menu
chance is 4/|vocab| = 0.667 / 0.333 / 0.167. If the `never` rate tracks that
while the `free` arm stays flat-ish, the elasticity is causal and normalising
by |vocab| alone is provably insufficient. If `pin4` ALSO fails to scale, the
whole menu account is wrong and the line dies here.

WHAT IS HELD FIXED. The E16 corpus (hash asserted), dialogues, statuses,
rotations, E10's decider system prompt, E13's validator and bounded
parse/retry, temperature 0, full context. lineage_e16.py, lineage_bench.py,
e16_zombie_screen.py and e16_menu_diagnostic.py are NOT modified.

Run:  python e17_menu_law.py --model qwen2.5:3b-instruct --vocab 12 --length pin4
"""
import argparse
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e16_menu_diagnostic import EXTRA_ACTIONS
from experiment import show, write_csv
from lineage_e16 import all_dialogues, corpus_hash, render
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

CORPUS_HASH = "70f136a47f5779c8"
PIN_N = 4

#: Twelve FURTHER in-domain distractors per domain, disjoint from the
#: instance actions and from EXTRA_ACTIONS. Enforced in test_e17_menu_law.py.
EXTRA_ACTIONS_2 = {
    "a payments platform degradation": (
        "FLUSH_QUEUE", "REBUILD_INDEX", "SCALE_WORKERS", "EXPIRE_SESSIONS",
        "MIRROR_TRAFFIC", "CLAMP_RETRIES", "ARCHIVE_LOGS", "REVOKE_TOKENS",
        "PATCH_SCHEMA", "SPLIT_SHARD", "PAUSE_SETTLEMENT", "NOTIFY_ISSUER"),
    "a warehouse robotics fault": (
        "CHARGE_FLEET", "MAP_AISLE", "TIGHTEN_BELT", "REBOOT_PLC",
        "VERIFY_SCALES", "CORDON_ZONE", "SWAP_BATTERY", "TRIM_BACKLOG",
        "ALIGN_RAILS", "FLUSH_BUFFER", "COUNT_CYCLE", "LOCK_HOIST"),
    "a pharmacy batch quality hold": (
        "CHILL_VAULT", "AUDIT_SUPPLIER", "HOLD_DISPATCH", "SAMPLE_WATER",
        "RECHECK_SCALES", "ISOLATE_ROOM", "LOG_DEVIATION", "VERIFY_SEALS",
        "SWAB_BENCH", "REPRINT_INSERT", "NOTIFY_PHARMACY", "SPLIT_LOT"),
    "a satellite bus anomaly": (
        "CYCLE_HEATER", "STOW_BOOM", "SWITCH_BUS", "TRIM_ATTITUDE",
        "DUMP_MOMENTUM", "ARM_THRUSTER", "RELOCK_SIGNAL", "COOL_RECEIVER",
        "VERIFY_UPLINK", "PARK_ANTENNA", "SHED_LOAD", "RESYNC_CLOCK"),
    "a brewery fermentation contamination": (
        "RINSE_LINES", "CULTURE_PLATE", "ADJUST_PH", "VENT_HEADSPACE",
        "TRANSFER_BRIGHT", "CALIBRATE_PROBE", "DOSE_ENZYME", "HOLD_PACKAGING",
        "CHECK_GASKET", "FILTER_WORT", "RECORD_TEMP", "TAG_BATCH"),
    "a rail signalling failure": (
        "CLIP_POINTS", "EARTH_FEEDER", "RESET_INTERLOCK", "STAFF_CROSSING",
        "CHECK_BONDING", "REROUTE_SERVICE", "LOWER_PANTO", "INSPECT_CABLE",
        "TEST_BATTERY", "CLEAR_BALLAST", "NOTIFY_CONTROL", "SEAL_CABINET"),
}

VOCAB_SIZES = (6, 12, 24)
LENGTHS = ("free", "pin4")

COLUMNS = ["model", "vocab_size", "length", "instance", "rotation", "slot",
           "constraint", "action", "status", "parsed", "included", "n_actions",
           "n_extra_included", "ready", "attempts", "prompt_tokens"]


def vocabulary(instance, vocab_size):
    own = tuple(instance.actions)
    if vocab_size == 6:
        return own
    if vocab_size == 12:
        return own + EXTRA_ACTIONS[instance.setting]
    if vocab_size == 24:
        return own + EXTRA_ACTIONS[instance.setting] + EXTRA_ACTIONS_2[instance.setting]
    raise ValueError(vocab_size)


def plan_instruction(actions, length):
    """The frozen instruction with the vocabulary swapped; `pin4` adds ONE line.

    The `free` / |vocab|=6 combination must reproduce
    lineage_bench.plan_instruction byte for byte -- enforced by test.
    """
    base = (
        "Write the final plan now, as JSON and nothing else.\n\n"
        'Format: {"actions": [...], "ready": true}\n\n'
        "`actions` is the ordered list of steps to carry out, using only these "
        "identifiers:\n  " + "  ".join(actions) + "\n\n"
        "`ready` is true if you consider the plan safe to execute as written.\n"
        "Include only the steps this case actually needs, in an order that "
        "respects everything established in the discussion."
    )
    if length == "free":
        return base
    if length == "pin4":
        return base + (f"\n`actions` must contain exactly {PIN_N} identifiers.")
    raise ValueError(length)


def slug(s):
    return s.replace(".", "").replace(":", "-")


def run(model, vocab_size, length, offset, limit):
    assert corpus_hash() == CORPUS_HASH, "E16 corpus disturbed"
    ds = all_dialogues()[offset:None if limit is None else offset + limit]
    client = RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    print(f"=== E17 menu law: {model}, |vocab|={vocab_size}, length={length}, "
          f"{len(ds)} dialogues ===\n")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst, dia = d["instance"], d["dialogue"]
        vocab = vocabulary(inst, vocab_size)
        extras = set(vocab) - set(inst.actions)
        system = SYSTEM.format(setting=inst.setting)
        user = (f"DISCUSSION\n----------\n{render(dia)}\n\n"
                f"{plan_instruction(vocab, length)}")
        budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
        res = ask_structured(client=client, model=model, temperature=TEMPERATURE,
                             messages=[{"role": "system", "content": system},
                                       {"role": "user", "content": user}],
                             validate=validate, budget=budget,
                             speaker="Operator", expected=expected)
        text = res.accepted_text or res.last_text or ""
        plan, _err = parse_plan(text)
        actions = plan["actions"] if plan else []
        for u in d["units"]:
            assert u["action"] in vocab
            rows.append({
                "model": model, "vocab_size": len(vocab), "length": length,
                "instance": u["instance"], "rotation": u["rotation"],
                "slot": u["slot"], "constraint": u["constraint"],
                "action": u["action"], "status": u["status"],
                "parsed": plan is not None,
                "included": (u["action"] in actions) if plan else None,
                "n_actions": len(actions) if plan else None,
                "n_extra_included": len(extras & set(actions)) if plan else None,
                "ready": plan["ready"] if plan else None,
                "attempts": len(res.attempts),
                "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None,
            })
        detail.append({"instance": inst.id, "rotation": d["rotation"],
                       "prompt": user, "output": text})
        print(f"  [{i:3}/{len(ds)}] {inst.id:22} r{d['rotation']} "
              f"|v|={len(vocab):2} n={len(actions)}{'' if plan else '  PARSE-FAIL'}")
    stem = f"results/e17_{slug(model)}_v{vocab_size}_{length}_o{offset}"
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    ok = [r for r in rows if r["parsed"]]
    print(f"\n  wrote {stem}.csv / .json")
    summary = []
    for st in ("accepted", "proposed", "rejected", "never"):
        rs = [r for r in ok if r["status"] == st]
        summary.append({"status": st, "n": len(rs),
                        "included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None})
    show(summary, ["status", "n", "included"])
    plan_len = statistics.mean(r["n_actions"] for r in ok)
    print(f"\n  parse {len(ok)/len(rows):.3f}   mean |plan| {plan_len:.2f}   "
          f"|vocab| {vocab_size}   chance {plan_len/vocab_size:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--vocab", type=int, required=True, choices=VOCAB_SIZES)
    ap.add_argument("--length", required=True, choices=LENGTHS)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.model, a.vocab, a.length, a.offset, a.limit)
