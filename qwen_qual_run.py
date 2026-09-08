"""qwen_qual_run.py: QWQ receiver qualification on qwen3:14b. One block per call.

Declared in docs/protocols/QWQ-qwen3-receiver-qualification.md.
Allocation: 36 attempts = 32 scheduled generation calls + 4 transport-only retries.

SELF-CONTAINED TRANSPORT. This posts to /api/chat directly rather than through
`robust_client`, because the run needs Ollama's TOP-LEVEL `think: false` and the
extra sampling options, and because `llm_client.py` / `robust_client.py` are used
by frozen experiments and are not modified here.

Wrong answers, refusals, malformed responses and OUTPUT TRUNCATION are OUTCOMES
and are never re-run. Only transport failures may consume the 4-attempt reserve;
an unresolved transport failure is logged as MISSING.
"""
import argparse
import hashlib
import json
import random
import time

import requests

from plansel_fixtures import build_quartet, render_prompt, score_option

MODEL = "qwen3:14b"
HOST = "http://localhost:11434"
CLEAN = frozenset({"A", "B"})          # the two necessary facts only
VARIANT = "knows_neither"
#: Qwen's recommended NON-THINKING sampling settings, plus a fixed seed.
OPTIONS = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0,
           "seed": 0, "num_predict": 300}
THINK = False
MAX_TRANSPORT_RETRIES = 4              # the whole reserve, shared across the run
LOG = "results/qwq_calls.jsonl"


def block_order(i):
    seed = int(hashlib.sha256(f"qwq-order-{i}".encode()).hexdigest()[:8], 16)
    order = list(range(4))
    random.Random(seed).shuffle(order)
    return order


def post_chat(prompt, retries_left):
    """Returns (data, retries_used, missing). Retries transport failures only."""
    used = 0
    last = None
    while True:
        try:
            r = requests.post(f"{HOST}/api/chat",
                              json={"model": MODEL,
                                    "messages": [{"role": "user",
                                                  "content": prompt}],
                                    "stream": False, "think": THINK,
                                    "options": OPTIONS},
                              timeout=1800)
            r.raise_for_status()
            return r.json(), used, None
        except (requests.HTTPError, requests.ConnectionError,
                requests.Timeout) as exc:
            last = exc
            if used >= retries_left:
                return None, used, f"TRANSPORT_FAILURE {type(exc).__name__}: {exc}"
            used += 1
            time.sleep(2)


def main(i, log_path):
    quartet = build_quartet(i)
    order = block_order(i)
    block = f"qwq:block{i}:{quartet[0].domain}"
    print(f"[block {i}] {block}  assignment order {order}")
    # reserve is global: count what previous blocks already consumed
    used_before = 0
    try:
        for line in open(log_path, encoding="utf-8"):
            used_before += json.loads(line).get("transport_retries", 0)
    except FileNotFoundError:
        pass
    reserve_left = MAX_TRANSPORT_RETRIES - used_before
    print(f"  transport reserve remaining: {reserve_left}")

    attempts = 0
    for pos, a in enumerate(order, 1):
        fx = quartet[a]
        prompt = render_prompt(fx, VARIANT, CLEAN)
        t0 = time.time()
        data, used, missing = post_chat(prompt, max(reserve_left, 0))
        reserve_left -= used
        attempts += 1 + used
        if missing is None:
            msg = data.get("message", {})
            text = (msg.get("content") or "").strip()
            thinking = (msg.get("thinking") or "") or None
            done_reason = data.get("done_reason")
            ptok = data.get("prompt_eval_count")
            ctok = data.get("eval_count")
        else:
            text, thinking, done_reason, ptok, ctok = "", None, None, None, None
        truncated = (done_reason == "length")
        sc = (score_option(text, fx) if missing is None
              else {"parsed": False, "success": False, "error": missing})
        rec = {"protocol": "QWQ", "block": block, "process_position": pos,
               "fixture_index": i, "assignment": a, "fid": fx.fid,
               "domain": fx.domain, "variant": VARIANT,
               "subset": sorted(CLEAN), "model": MODEL,
               "model_digest": "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8",
               "quantization": "Q4_K_M", "runtime": "ollama 0.33.3",
               "think": THINK, "options": OPTIONS,
               "rendered_input": prompt, "response": text,
               "thinking_field": thinking, "done_reason": done_reason,
               "truncated": truncated,
               "prompt_tokens": ptok, "completion_tokens": ctok,
               "seconds": round(time.time() - t0, 3),
               "transport_retries": used, "missing": missing,
               "attempt": 1 + used,
               "chosen": sc.get("option"), "correct_label": fx.correct_label,
               "parsed": sc["parsed"], "ready": sc.get("ready"),
               "violated": sc.get("violated"),
               "success": bool(sc["success"]), "error": sc.get("error")}
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"  pos{pos} a{a} chose={sc.get('option')} correct={fx.correct_label}"
              f" success={sc['success']} trunc={truncated} {rec['seconds']}s"
              + (f"  {missing}" if missing else ""))
    print(f"  attempts this block: {attempts}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", type=int, required=True)
    ap.add_argument("--log", default=LOG)
    a = ap.parse_args()
    main(a.block, a.log)
