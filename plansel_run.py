"""plansel_run.py: execute ONE declared PSQ process block and exit.

Declared in docs/protocols/PSQ-plan-selection-qualification.md. Ceiling 36
attempts: 32 scheduled + 4 transport-only retries. One OS process per block.

Wrong answers, refusals and malformed outputs are OUTCOMES and are never
re-run. Only transport failures may consume the reserve, and an unresolved
transport failure is logged as MISSING with qualification INCOMPLETE.
"""
import argparse
import hashlib
import json
import random
import time

from plansel_fixtures import CIDS, build_quartet, render_prompt, score_option
from robust_client import RetryingOllamaClient

MODEL = "llama3.2:3b"
DECODING = {"temperature": 0.0, "num_predict": 300}
FULL = frozenset(CIDS)
VARIANT = "knows_neither"
LOG = "results/psq_calls.jsonl"


def block_order(i):
    seed = int(hashlib.sha256(f"psq-order-{i}".encode()).hexdigest()[:8], 16)
    order = list(range(4))
    random.Random(seed).shuffle(order)
    return order


def main(i, log_path):
    quartet = build_quartet(i)
    order = block_order(i)
    block = f"psq:block{i}:{quartet[0].domain}"
    print(f"[block {i}] {block}  assignment order {order}")
    client = RetryingOllamaClient()
    client.seed = 0
    attempts = 0
    for pos, a in enumerate(order, 1):
        fx = quartet[a]
        prompt = render_prompt(fx, VARIANT, FULL)
        before = client.transport_retries
        t0 = time.time()
        missing = None
        try:
            r = client.chat(MODEL, [{"role": "user", "content": prompt}],
                            temperature=DECODING["temperature"],
                            num_predict=DECODING["num_predict"])
            text, ptok, ctok = r.text or "", r.prompt_tokens, r.completion_tokens
        except Exception as exc:
            text, ptok, ctok = "", None, None
            missing = f"TRANSPORT_FAILURE {type(exc).__name__}: {exc}"
        retries = client.transport_retries - before
        attempts += 1 + retries
        sc = (score_option(text, fx) if missing is None
              else {"parsed": False, "success": False, "error": missing})
        rec = {"protocol": "PSQ", "block": block, "process_position": pos,
               "fixture_index": i, "assignment": a, "fid": fx.fid,
               "domain": fx.domain, "variant": VARIANT,
               "subset": sorted(FULL), "model": MODEL, "decoding": DECODING,
               "rendered_input": prompt, "response": text,
               "prompt_tokens": ptok, "completion_tokens": ctok,
               "seconds": round(time.time() - t0, 3),
               "transport_retries": retries, "missing": missing,
               "attempt": 1 + retries,
               "chosen": sc.get("option"), "correct_label": fx.correct_label,
               "correct_position": fx.correct_position,
               "parsed": sc["parsed"], "ready": sc.get("ready"),
               "violated": sc.get("violated"), "satisfied": sc.get("satisfied"),
               "success": bool(sc["success"]), "error": sc.get("error")}
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"  pos{pos} a{a}  chose={sc.get('option')} "
              f"correct={fx.correct_label} parsed={sc['parsed']} "
              f"ready={sc.get('ready')} success={sc['success']}"
              + (f"  {missing}" if missing else ""))
    print(f"  attempts this block: {attempts}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", type=int, required=True)
    ap.add_argument("--log", default=LOG)
    a = ap.parse_args()
    main(a.block, a.log)
