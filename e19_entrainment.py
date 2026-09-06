"""e19_entrainment.py: does contextual entrainment decrease with model size?

REPLICATION. Declared in docs/protocols/E19-entrainment.md with predictions and
read rule fixed before any scoring run. It tests SOMEONE ELSE'S published claim:

    arXiv:2606.24077, "Sentence-Level Contextual Entrainment in Large Language
    Models" (Liu & Chu, 23 Jun 2026), 26 LLMs from seven families:
      * sentences present in the prompt -- even counterfactual ones --
        significantly increase their own probability at inference;
      * "As the model size increases, contextual entrainment gradually
        decreases."

WHY THIS RUNTIME. Ollama exposes logprobs for GENERATED tokens only: there is no
echo/scoring mode (`num_predict: 0` still generates), and forced decoding through
`top_logprobs` silently misses targets outside the top-k. Exact teacher-forced
scoring of a given sentence -- the paper's actual measure -- needs HF. The
Qwen2.5-Instruct ladder at 0.5B / 1.5B / 7B is already in the local HF cache, so
no download is required and the ladder is within one family across 14x.

THE MEASURE. For a target sentence S and a prompt P,

    score(S | P) = (1/|S|) * sum_t log p(s_t | P, s_<t)

teacher-forced over S's own tokens. Entrainment is the difference between a
prompt that contains S and an otherwise identical prompt that does not:

    delta = score(S | P_present) - score(S | P_absent)

S is the first PROPOSAL message of an E16 dialogue. `P_absent` replaces that one
message, in place and from the same speaker, with a fixed neutral line, so the
message count and speaker alternation are preserved. The instruction that
follows never asks for a restatement.

Run:  python e19_entrainment.py --model Qwen/Qwen2.5-0.5B-Instruct
"""
import argparse
import csv
import json
import statistics

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from e10_independence import SYSTEM
from lineage_e16 import all_dialogues, corpus_hash, render

CORPUS_HASH = "70f136a47f5779c8"

#: replaces the target message in the ABSENT condition. Fixed, so the two
#: conditions differ in exactly one message and nothing else.
FILLER = "The incident channel has been quiet for the last few minutes."

#: deliberately does not ask for a restatement of anything.
INSTRUCTION = "Write one sentence about this incident."

COLUMNS = ["model", "instance", "rotation", "constraint", "n_tokens",
           "score_present", "score_absent", "delta"]


def target_and_variants(d):
    """(S, present_render, absent_render) for one dialogue."""
    dia = d["dialogue"]
    idx = next(i for i, m in enumerate(dia) if m[2][0] == "proposal")
    speaker, text, tag = dia[idx]
    absent = list(dia)
    absent[idx] = (speaker, FILLER, ("noise", None))
    return text, render(dia), render(absent), tag[1]


def build_prompt(tok, setting, discussion):
    msgs = [{"role": "system", "content": SYSTEM.format(setting=setting)},
            {"role": "user",
             "content": f"DISCUSSION\n----------\n{discussion}\n\n{INSTRUCTION}"}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


@torch.no_grad()
def score_sentence(model, tok, prompt_text, sentence):
    """Mean per-token log-probability of `sentence` continuing `prompt_text`."""
    p_ids = tok(prompt_text, return_tensors="pt", add_special_tokens=False).input_ids
    s_ids = tok(sentence, return_tensors="pt", add_special_tokens=False).input_ids
    ids = torch.cat([p_ids, s_ids], dim=1).to(model.device)
    logits = model(ids).logits.float()
    # logits[:, i] predicts token i+1
    start = p_ids.shape[1]
    lp = torch.log_softmax(logits[0, start - 1:-1], dim=-1)
    tgt = ids[0, start:]
    return lp.gather(-1, tgt.unsqueeze(-1)).squeeze(-1).mean().item(), s_ids.shape[1]


def run(model_id, limit, offset):
    assert corpus_hash() == CORPUS_HASH, "E16 corpus disturbed"
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, dtype=torch.bfloat16, device_map="cuda", low_cpu_mem_usage=True)
    model.eval()
    ds = all_dialogues()[offset:None if limit is None else offset + limit]
    print(f"=== E19 entrainment: {model_id}, {len(ds)} dialogues ===\n")
    rows = []
    for i, d in enumerate(ds, 1):
        S, present, absent, kid = target_and_variants(d)
        setting = d["instance"].setting
        sp, n = score_sentence(model, tok, build_prompt(tok, setting, present), S)
        sa, _ = score_sentence(model, tok, build_prompt(tok, setting, absent), S)
        rows.append({"model": model_id, "instance": d["instance"].id,
                     "rotation": d["rotation"], "constraint": kid, "n_tokens": n,
                     "score_present": round(sp, 6), "score_absent": round(sa, 6),
                     "delta": round(sp - sa, 6)})
        if i % 24 == 0 or i == len(ds):
            md = statistics.mean(r["delta"] for r in rows)
            print(f"  [{i:3}/{len(ds)}]  running mean delta = {md:+.4f}")
    stem = f"results/e19_{model_id.split('/')[-1]}_o{offset}"
    with open(stem + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        w.writerows(rows)
    ds_ = [r["delta"] for r in rows]
    print(f"\n  wrote {stem}.csv")
    print(f"  mean delta {statistics.mean(ds_):+.4f}   "
          f"median {statistics.median(ds_):+.4f}   "
          f"positive {sum(x > 0 for x in ds_)}/{len(ds_)}")
    print(f"  mean score present {statistics.mean(r['score_present'] for r in rows):+.4f}   "
          f"absent {statistics.mean(r['score_absent'] for r in rows):+.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--offset", type=int, default=0)
    a = ap.parse_args()
    run(a.model, a.limit, a.offset)
