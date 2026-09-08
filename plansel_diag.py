"""plansel_diag.py: execute ONE declared PSD process block and exit.

Declared in docs/protocols/PSD-clean-evidence-diagnostic.md. Ceiling 36 attempts
(32 scheduled + 4 transport-only retries). One OS process per (fixture,
assignment) block; the two conditions run inside it, counterbalanced.

`clean` is an ORACLE EVIDENCE CONTROL: the subset is chosen from construction
metadata, which a deployed selector would not have. No selection method is
evaluated here.

Wrong answers, refusals and malformed outputs are OUTCOMES and are never re-run.
"""
import argparse
import json
import time

from plansel_fixtures import build_quartet, render_prompt, score_option
from robust_client import RetryingOllamaClient

MODEL = "llama3.2:3b"
DECODING = {"temperature": 0.0, "num_predict": 300}
VARIANT = "knows_neither"
FULL = frozenset({"A", "B", "C", "D"})
CLEAN = frozenset({"A", "B"})          # the two necessary facts only
LOG = "results/psd_calls.jsonl"


def cells():
    """16 (fixture, assignment) cells with counterbalanced condition order."""
    out = []
    for f in range(4):
        for a in range(4):
            first = "full" if (f + a) % 2 == 0 else "clean"
            second = "clean" if first == "full" else "full"
            out.append((f, a, (first, second)))
    return out


def main(index, log_path):
    cs = cells()
    f, a, order = cs[index]
    fx = build_quartet(f)[a]
    block = f"psd:f{f}:a{a}"
    print(f"[cell {index}/15] {block} {fx.domain}  order={order}")
    client = RetryingOllamaClient()
    client.seed = 0
    attempts = 0
    for pos, cond in enumerate(order, 1):
        subset = FULL if cond == "full" else CLEAN
        prompt = render_prompt(fx, VARIANT, subset)
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
        rec = {"protocol": "PSD", "block": block, "process_position": pos,
               "condition": cond, "condition_order": list(order),
               "oracle_control": cond == "clean",
               "fixture_index": f, "assignment": a, "fid": fx.fid,
               "domain": fx.domain, "variant": VARIANT,
               "subset": sorted(subset), "model": MODEL, "decoding": DECODING,
               "rendered_input": prompt, "response": text,
               "prompt_tokens": ptok, "completion_tokens": ctok,
               "seconds": round(time.time() - t0, 3),
               "transport_retries": retries, "missing": missing,
               "attempt": 1 + retries,
               "chosen": sc.get("option"), "correct_label": fx.correct_label,
               "parsed": sc["parsed"], "ready": sc.get("ready"),
               "violated": sc.get("violated"),
               "success": bool(sc["success"]), "error": sc.get("error")}
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"  pos{pos} {cond:<5} chose={sc.get('option')} "
              f"correct={fx.correct_label} success={sc['success']}"
              + (f"  {missing}" if missing else ""))
    print(f"  attempts this cell: {attempts}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", type=int, required=True)
    ap.add_argument("--log", default=LOG)
    a = ap.parse_args()
    main(a.cell, a.log)
