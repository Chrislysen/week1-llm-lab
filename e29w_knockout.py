"""e29w_knockout.py: E29-W runner -- does a trailing marker work by reading its record?

DECLARED in docs/protocols/E29W-knockout.md before any call on an E29-O prompt. The model
is Llama-3.2-3B-Instruct in bf16 under Hugging Face transformers (the weights Ollama's
llama3.2:3b quantises), decoded greedily from the exact string Ollama's llama3.2 template
renders. Prompts, validator, retry and plan parsing are E29-O's. Only the attention
changes (knockout.py).

    python e29w_knockout.py --hash
    python e29w_knockout.py --smoke          # one non-experimental prompt: load, template, speed
    python e29w_knockout.py --run            # all conditions, resumable
"""
import argparse
import csv
import hashlib
import json
import os
import time

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import make_validator, schema_hint
from e29_memory_semantics import COLUMNS
from e29o_order import build_user
from experiment import write_csv
from lineage_e29a import _parts
from lineage_e29o import NEUTRAL, dialogues
from lineage_eval import parse_plan
from llm_client import ChatResponse
from structured import MAX_ATTEMPTS, ask_structured

MODEL_ID = "unsloth/Llama-3.2-3B-Instruct"
REVISION = "006f5dcd1393c3add266de40994ba96225e9689d"
VERSIONS = {"transformers": "5.9.0", "torch": "2.11.0+cu128"}
N_LAYERS = 28
NUM_PREDICT_CAP = 512
STEM = "results/e29w_llama32-3b-hf_r0"
E29W_HASH = "dc5bf68e6b69c82a"

# condition: (E29-O cell, knockout, layers). Knockouts, all heads:
#   marker>record   the marker's tokens may not attend to the record's tokens
#   marker>neutral  the marker's tokens may not attend to N's tokens (control)
#   after>marker    no later token, prompt or generated, may attend to the marker's tokens
#   record>marker   the record's tokens may not attend to the marker's tokens (prefix cell)
CONDITIONS = {
    "base_open": ("open", None, None),
    "base_sentence": ("sentence_short", None, None),
    "base_pre": ("withdrawn_pre", None, None),
    "base_post": ("withdrawn_post", None, None),
    "kb_post": ("withdrawn_post", "marker>record", "all"),
    "kc_post": ("withdrawn_post", "marker>neutral", "all"),
    "kr_post": ("withdrawn_post", "after>marker", "all"),
    "kb_early": ("withdrawn_post", "marker>record", "early"),
    "kb_late": ("withdrawn_post", "marker>record", "late"),
    "kf_pre": ("withdrawn_pre", "record>marker", "all"),
}
LAYERS = {"all": range(0, N_LAYERS), "early": range(0, N_LAYERS // 2), "late": range(N_LAYERS // 2, N_LAYERS)}


def render(messages):
    """The string Ollama 0.34.4 renders for llama3.2:3b (no tools), with llama.cpp's BOS."""
    out = "<|begin_of_text|>"
    sys_msgs = [m for m in messages if m["role"] == "system"]
    out += "<|start_header_id|>system<|end_header_id|>\n\nCutting Knowledge Date: December 2023\n\n"
    out += (sys_msgs[0]["content"] if sys_msgs else "") + "<|eot_id|>"
    rest = [m for m in messages if m["role"] != "system"]
    for i, m in enumerate(rest):
        last = i == len(rest) - 1
        if m["role"] == "user":
            out += "<|start_header_id|>user<|end_header_id|>\n\n" + m["content"] + "<|eot_id|>"
            if last:
                out += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        else:
            out += "<|start_header_id|>assistant<|end_header_id|>\n\n" + m["content"] + ("" if last else "<|eot_id|>")
    return out


def spans(cell, instance, dialogue):
    """Character spans, inside the user message, of the record, the marker and N."""
    user = build_user(cell, instance, dialogue)
    items, p, _, _, _, x = _parts(instance, dialogue)
    prop = items[p]
    line = {"withdrawn_pre": f"- [withdrawn] {prop}\n", "withdrawn_post": f"- {prop} [withdrawn]\n"}.get(cell)
    out = {}
    n0 = user.index(f"- {NEUTRAL}\n") + 2
    out["neutral"] = (n0, n0 + len(NEUTRAL))
    if line:
        assert user.count(line) == 1, cell
        l0 = user.index(line)
        body = line[2:-1]
        r0 = l0 + 2 + body.index(prop)
        m0 = l0 + 2 + body.index("[withdrawn]")
        out["record"] = (r0, r0 + len(prop))
        out["marker"] = (m0, m0 + len("[withdrawn]"))
    return user, out


def blocks_hash():
    h = hashlib.sha256()
    for d in dialogues():
        for name, (cell, ko, layers) in CONDITIONS.items():
            system = SYSTEM.format(setting=d["instance"].setting)
            user, sp = spans(cell, d["instance"], d["arms"]["neutral"])
            h.update(f"{d['instance'].id}|{d['rotation']}|{name}|{ko}|{layers}|{sorted(sp.items())}|".encode())
            h.update(render([{"role": "system", "content": system}, {"role": "user", "content": user}]).encode())
    return h.hexdigest()[:16]


class HFClient:
    """ask_structured's client interface over a local HF model, with the current knockout."""

    def __init__(self):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        assert transformers.__version__ == VERSIONS["transformers"] and torch.__version__ == VERSIONS["torch"], \
            (transformers.__version__, torch.__version__)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION, local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, revision=REVISION, local_files_only=True, dtype=torch.bfloat16,
            attn_implementation="sdpa").to("cuda").eval()
        assert len(self.model.model.layers) == N_LAYERS
        self.stop = [self.tok.convert_tokens_to_ids(t) for t in ("<|eot_id|>", "<|start_header_id|>", "<|end_header_id|>")]
        self.stop.append(self.tok.eos_token_id)
        self.plan = None          # (knockout, layers, {name: (start, end) in the user message})

    def _token_sets(self, text, user, sp, offsets):
        from knockout import char_span_to_tokens
        base = text.index(user)
        tok = {k: set(char_span_to_tokens(offsets, base + a, base + b)) for k, (a, b) in sp.items()}
        if "marker" in tok and "record" in tok:
            tok["record"] -= tok["marker"]
        return tok

    def chat(self, model, messages, temperature=0.0):
        from knockout import greedy
        text = render(messages)
        enc = self.tok(text, add_special_tokens=False, return_offsets_mapping=True)
        ids = self.torch.tensor([enc["input_ids"]], device="cuda")
        blocks, new_keys, layers = [], [], None
        if self.plan and self.plan[0]:
            ko, lay, user, sp = self.plan
            t = self._token_sets(text, user, sp, enc["offset_mapping"])
            m = t["marker"]
            if ko == "marker>record":
                blocks = [(m, t["record"])]
            elif ko == "marker>neutral":
                blocks = [(m, t["neutral"])]
            elif ko == "record>marker":
                blocks = [(t["record"], m)]
            elif ko == "after>marker":
                blocks = [(range(max(m) + 1, ids.shape[1]), m)]
                new_keys = sorted(m)
            else:
                raise ValueError(ko)
            layers = LAYERS[lay]
        t0 = time.monotonic()
        out, n_new = greedy(self.model, self.tok, ids, blocks=blocks, new_keys=new_keys, layers=layers,
                            max_new_tokens=NUM_PREDICT_CAP, stop_ids=self.stop)
        return ChatResponse(text=out.strip(), prompt_tokens=ids.shape[1], completion_tokens=n_new,
                            seconds=time.monotonic() - t0)


def run(limit=None):
    assert blocks_hash() == E29W_HASH, f"E29-W prompts disturbed: {blocks_hash()}"
    client = HFClient()
    validate, expected = make_validator("default"), schema_hint("default")
    done = set()
    if os.path.exists(STEM + ".csv"):
        done = {(r["instance"], r["rotation"], r["design"]) for r in csv.DictReader(open(STEM + ".csv", encoding="utf-8"))
                if r["parsed"] == "True"}
    rows = list(csv.DictReader(open(STEM + ".csv", encoding="utf-8"))) if os.path.exists(STEM + ".csv") else []
    detail = json.load(open(STEM + ".json", encoding="utf-8")) if os.path.exists(STEM + ".json") else []
    ds = dialogues()[:limit] if limit else dialogues()
    print(f"=== E29-W knockout: {MODEL_ID}@{REVISION[:12]}, {len(ds)} dialogues x {len(CONDITIONS)} conditions ===", flush=True)
    for n, d in enumerate(ds, 1):
        inst = d["instance"]
        system = SYSTEM.format(setting=inst.setting)
        for name, (cell, ko, lay) in CONDITIONS.items():
            if (inst.id, str(d["rotation"]), name) in done:
                continue
            user, sp = spans(cell, inst, d["arms"]["neutral"])
            client.plan = (ko, lay, user, sp)
            res = ask_structured(client=client, model=MODEL_ID, temperature=0.0,
                                 messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                                 validate=validate, budget=Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600),
                                 speaker="Operator", expected=expected)
            text = res.accepted_text or res.last_text or ""
            plan, _ = parse_plan(text)
            actions = plan["actions"] if plan else []
            rows = [r for r in rows if not (r["instance"] == inst.id and str(r["rotation"]) == str(d["rotation"])
                                            and r["design"] == name)]
            for u in d["units"]:
                rows.append({"model": MODEL_ID, "design": name, "arm": "neutral", "instance": u["instance"],
                             "rotation": u["rotation"], "slot": u["slot"], "constraint": u["constraint"],
                             "action": u["action"], "status": u["status"], "parsed": plan is not None,
                             "included": (u["action"] in actions) if plan else None,
                             "n_actions": len(actions) if plan else None, "ready": plan["ready"] if plan else None,
                             "attempts": len(res.attempts),
                             "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None,
                             "completion_tokens": sum(a.completion_tokens or 0 for a in res.attempts),
                             "seconds": round(sum(a.seconds or 0 for a in res.attempts), 3)})
            detail.append({"instance": inst.id, "rotation": d["rotation"], "design": name, "cell": cell,
                           "knockout": ko, "layers": lay, "prompt": user, "output": text,
                           "model": MODEL_ID, "revision": REVISION, **VERSIONS})
        write_csv(STEM + ".csv", rows, COLUMNS)
        with open(STEM + ".json", "w", encoding="utf-8") as f:
            json.dump(detail, f, indent=1)
        print(f"  [{n:2}/{len(ds)}] {inst.id:22} r{d['rotation']}", flush=True)
    print(f"  wrote {STEM}.csv / .json", flush=True)
    print("E29-W ALL DONE", flush=True)


def smoke():
    """Load, template and speed on a prompt that is not part of any experiment."""
    c = HFClient()
    msgs = [{"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": 'Reply with the JSON object {"ok": true} and nothing else.'}]
    r = c.chat(MODEL_ID, msgs)
    print(repr(r.text), r.prompt_tokens, r.completion_tokens, round(r.seconds, 2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.hash:
        print(blocks_hash())
    elif a.smoke:
        smoke()
    elif a.run:
        run(a.limit)
