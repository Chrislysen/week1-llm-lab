"""EXPLORATORY DIAGNOSTIC after the Phase B qualification gate FAILED (0/8).

Not part of the declared subset table. Does NOT revive the gate: the Q verdict
stands. Purpose is the one the stop rule points at -- "fix task/receiver
qualification first" -- by asking whether the binding constraint is the
single-call design rather than the receiver.

Reuses each fixture's already-logged full-evidence output and adds ONE refine
call per fixture. 8 attempts, drawn from the declared 16-call reserve, logged.
"""
import json, time
import lineage_bench as lb
from agentcom_analysis import check_vector, failure_mode
from agentcom_bundle import SubsetOutcome
from phaseb_fixtures import DECODING, MODEL, SCORER, score_response
from robust_client import RetryingOllamaClient

recs = [json.loads(l) for l in open("results/phaseb_calls.jsonl", encoding="utf-8")]
first = {}
for r in recs:
    if r["extra"]["kind"] == "qualification" and r["extra"]["realisation"] == 1:
        first[r["extra"]["task_id"]] = r

client = RetryingOllamaClient(); client.seed = 0
spent = 0
for tid, r in sorted(first.items()):
    d, g = tid.split("~")[0].split("-")
    inst = lb.generate_instance(d, g, salt="phaseb-qual-v1")
    prompt = (r["rendered_input"] + "\n\nYour previous answer was:\n" + r["response"]
              + "\n\nCheck it against EVERY ordering rule stated above, one rule at a "
                "time. If any rule is broken, fix the order. Reply with the corrected "
                "JSON and nothing else.")
    before = client.transport_retries
    t0 = time.time()
    resp = client.chat(MODEL, [{"role": "user", "content": prompt}],
                       temperature=DECODING["temperature"],
                       num_predict=DECODING["num_predict"])
    retries = client.transport_retries - before
    spent += 1 + retries
    chk = score_response(resp.text or "", inst)
    cids = [c.id for c in inst.constraints]
    rec = SubsetOutcome(
        dp_id=f"diag:{tid}", subset=("A", "B", "C", "D"),
        rendered_words=r["rendered_words"], scorer=SCORER,
        task_family_id=f"{inst.domain}-{inst.graph}",
        recipient_context_id="knows_A", process_block=f"diag:{tid}",
        request_position=1, inclusion_order=("A", "B", "C", "D"),
        rendered_input=prompt, attempt=1 + retries, failure=None,
        prompt_tokens=resp.prompt_tokens, completion_tokens=resp.completion_tokens,
        seconds=round(time.time() - t0, 3), response=resp.text or "",
        score=float(chk.success), executed=True,
        check_vector=check_vector(chk, cids), failure_mode=failure_mode(chk),
        extra={"kind": "diagnostic", "exploratory": True, "task_id": tid,
               "realisation": None, "violated": chk.violated,
               "satisfied": chk.satisfied, "parsed": chk.parsed,
               "ready": chk.ready, "actions": chk.actions,
               "constraint_recall": chk.constraint_recall,
               "unknown_actions": chk.unknown_actions,
               "transport_retries": retries,
               "before_violations": len(r["extra"]["violated"])})
    with open("results/phaseb_calls.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec.to_dict()) + "\n")
    print(f"  {tid.split('~')[0]:22} viol {len(r['extra']['violated'])} -> "
          f"{len(chk.violated)}  success={chk.success}  {failure_mode(chk)}")
print(f"\ndiagnostic attempts: {spent}")
