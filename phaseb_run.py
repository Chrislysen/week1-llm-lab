"""phaseb_run.py: execute ONE declared Phase B block and exit.

Runs exactly one process block, so the declared blocking is real OS-process
blocking rather than a loop inside one interpreter. Invoke once per block.

Authorised 2026-09-08 under docs/protocols/PHASE-B-bundle-observability.md
(Amendments 1-3), ceiling 288 model-call ATTEMPTS. Failures and transport
retries count. Every attempt is logged; nothing is unlogged.

The recipient prompt is sent as the sole user message, exactly as recorded in
DecisionPoint.recipient_prompt. No extra system prompt is introduced, because
none was declared.
"""
import argparse
import json
import time

from agentcom_analysis import check_vector, failure_mode
from agentcom_bundle import SubsetOutcome, serialised_cost
from phaseb_fixtures import (CIDS, DECODING, MODEL, QUAL_COMBOS, QUAL_SALT,
                             SCORER, STUDY_COMBOS, build_task,
                             qualification_schedule, render_prompt, schedule,
                             score_response)
from robust_client import RetryingOllamaClient

CALLS_LOG = "results/phaseb_calls.jsonl"


def all_blocks():
    tasks = [build_task(d, g) for d, g in STUDY_COMBOS]
    qual = [build_task(d, g, salt=QUAL_SALT) for d, g in QUAL_COMBOS]
    by_id = {t["task_id"]: t for t in tasks + qual}
    return qualification_schedule(qual) + schedule(tasks), by_id


def run_block(block, by_id, log_path):
    client = RetryingOllamaClient()
    client.seed = 0
    n_attempts = 0
    for call in block["calls"]:
        task = by_id[call["task_id"]]
        inst = task["instance"]
        subset = frozenset(call["subset"])
        prompt = render_prompt(task, call["variant"], subset)
        before = client.transport_retries
        t0 = time.time()
        failure = None
        try:
            r = client.chat(MODEL, [{"role": "user", "content": prompt}],
                            temperature=DECODING["temperature"],
                            num_predict=DECODING["num_predict"])
            text = r.text or ""
            ptok, ctok = r.prompt_tokens, r.completion_tokens
        except Exception as exc:                       # a failed attempt still counts
            text, ptok, ctok = "", None, None
            failure = f"{type(exc).__name__}: {exc}"
        retries = client.transport_retries - before
        n_attempts += 1 + retries
        chk = score_response(text, inst)
        cids = [c.id for c in inst.constraints]
        rec = SubsetOutcome(
            dp_id=call["dp_id"], subset=tuple(sorted(subset)),
            rendered_words=serialised_cost(task["candidates"], subset),
            scorer=SCORER,
            task_family_id=f"{inst.domain}-{inst.graph}",
            recipient_context_id=call["variant"],
            process_block=block["process_block"],
            request_position=call["request_position"],
            inclusion_order=tuple(sorted(subset)),
            rendered_input=prompt,
            attempt=1 + retries, failure=failure,
            prompt_tokens=ptok, completion_tokens=ctok,
            seconds=round(time.time() - t0, 3),
            response=text, score=float(chk.success), executed=True,
            check_vector=check_vector(chk, cids),
            failure_mode=failure_mode(chk),
            extra={"kind": call["kind"], "task_id": call["task_id"],
                   "realisation": call.get("realisation"),
                   "violated": chk.violated, "satisfied": chk.satisfied,
                   "parsed": chk.parsed, "ready": chk.ready,
                   "actions": chk.actions,
                   "constraint_recall": chk.constraint_recall,
                   "unknown_actions": chk.unknown_actions,
                   "transport_retries": retries})
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec.to_dict()) + "\n")
        print(f"  pos{call['request_position']:>3} {''.join(sorted(subset)) or '-':<5} "
              f"{failure_mode(chk):<9} success={chk.success} "
              f"viol={len(chk.violated)} words={rec.rendered_words}")
    return n_attempts


def main(index, log_path):
    blocks, by_id = all_blocks()
    if not 0 <= index < len(blocks):
        raise SystemExit(f"block index out of range 0..{len(blocks)-1}")
    b = blocks[index]
    print(f"[block {index}/{len(blocks)-1}] {b['process_block']} "
          f"({b['kind']}, {b['n_calls']} calls)")
    spent = run_block(b, by_id, log_path)
    print(f"  attempts this block: {spent}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", type=int, required=True)
    ap.add_argument("--log", default=CALLS_LOG)
    a = ap.parse_args()
    main(a.block, a.log)
