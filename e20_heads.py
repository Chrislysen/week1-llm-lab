"""e20_heads.py: do 2-4% of attention heads carry contextual entrainment?

MECHANISTIC REPLICATION of arXiv:2606.24077's third claim. Declared in
docs/protocols/E20-entrainment-heads.md with the read rule fixed before any
pass. Reuses E19's entrainment measure and prompts unchanged.

Ablation: zero a head's slice of the o_proj input via a forward pre-hook,
verified to change logits and restore exactly on removal.

Split (instance-level, no leakage): dialogues 0-71 SEARCH, 72-143 HELD-OUT.

Modes
  --mode sweep     ablate each head singly, mean delta on a SEARCH subsample
  --mode heldout   baseline, top-k joint ablation, and random-set controls
"""
import argparse
import csv
import json
import random
import statistics

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from e19_entrainment import (CORPUS_HASH, build_prompt, score_sentence,
                             target_and_variants)
from lineage_e16 import all_dialogues, corpus_hash

SEARCH = slice(0, 72)
HELDOUT = slice(72, 144)
TOP_K = 10
N_RANDOM = 20
SEED = 20260906


def load(model_id):
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, dtype=torch.bfloat16, device_map="cuda",
        low_cpu_mem_usage=True).eval()
    return tok, model


def head_dim(model):
    a = model.model.layers[0].self_attn
    return a.o_proj.in_features // model.config.num_attention_heads


def ablate(model, heads, hd):
    """heads: iterable of (layer, head). Returns handles to remove."""
    by_layer = {}
    for l, h in heads:
        by_layer.setdefault(l, []).append(h)
    handles = []
    for l, hs in by_layer.items():
        def pre(mod, args, hs=tuple(hs)):
            x = args[0].clone()
            for h in hs:
                x[..., h * hd:(h + 1) * hd] = 0
            return (x,)
        handles.append(model.model.layers[l].self_attn.o_proj
                       .register_forward_pre_hook(pre))
    return handles


def mean_delta(model, tok, ds):
    out = []
    for d in ds:
        S, present, absent, _ = target_and_variants(d)
        setting = d["instance"].setting
        sp, _, _ = score_sentence(model, tok, build_prompt(tok, setting, present), S)
        sa, _, _ = score_sentence(model, tok, build_prompt(tok, setting, absent), S)
        out.append((sp - sa, sa))
    return statistics.mean(x for x, _ in out), statistics.mean(y for _, y in out)


def run_sweep(model_id, l0, l1, n_sub):
    assert corpus_hash() == CORPUS_HASH
    tok, model = load(model_id)
    hd = head_dim(model)
    nh = model.config.num_attention_heads
    ds = all_dialogues()[SEARCH]
    rng = random.Random(SEED)
    sub = rng.sample(ds, n_sub)
    base, _ = mean_delta(model, tok, sub)
    print(f"=== E20 sweep {model_id} layers {l0}-{l1} | SEARCH n={n_sub} "
          f"baseline delta {base:+.4f} ===\n")
    path = f"results/e20_sweep_L{l0}-{l1}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["layer", "head", "delta", "reduction"])
        for l in range(l0, l1 + 1):
            for h in range(nh):
                hs = ablate(model, [(l, h)], hd)
                d, _ = mean_delta(model, tok, sub)
                for x in hs:
                    x.remove()
                w.writerow([l, h, round(d, 6), round(base - d, 6)])
            f.flush()
            print(f"  layer {l:2} done")
    print(f"\n  wrote {path}  (baseline {base:+.6f})")


def run_heldout(model_id, sweep_glob, n_random, rand_start, do_main):
    import glob
    assert corpus_hash() == CORPUS_HASH
    rows = []
    for p in sorted(glob.glob(sweep_glob)):
        rows.extend(list(csv.DictReader(open(p, newline=""))))
    assert rows, "no sweep files"
    rows.sort(key=lambda r: -float(r["reduction"]))
    top = [(int(r["layer"]), int(r["head"])) for r in rows[:TOP_K]]
    print(f"=== E20 held-out {model_id} | {len(rows)} heads swept ===")
    print(f"  top-{TOP_K}: {top}\n")

    tok, model = load(model_id)
    hd = head_dim(model)
    nh = model.config.num_attention_heads
    nl = model.config.num_hidden_layers
    ds = all_dialogues()[HELDOUT]

    if do_main:
        d0, a0 = mean_delta(model, tok, ds)
        print(f"  baseline        delta {d0:+.4f}   score_absent {a0:+.4f}")
        hs = ablate(model, top, hd)
        dk, ak = mean_delta(model, tok, ds)
        for x in hs:
            x.remove()
        red = (d0 - dk) / d0
        print(f"  top-{TOP_K} ablated  delta {dk:+.4f}   score_absent {ak:+.4f}"
              f"   reduction {red:.3f}")
        json.dump({"d0": d0, "a0": a0, "dk": dk, "ak": ak, "red": red,
                   "top": top, "n_heads": len(rows)},
                  open("results/e20_main.json", "w"), indent=1)
    main = json.load(open("results/e20_main.json"))
    d0, a0, dk, ak, red = main["d0"], main["a0"], main["dk"], main["ak"], main["red"]

    # controls: the full 20-set sequence is fixed by SEED; chunks take a slice
    rng = random.Random(SEED)
    all_heads = [(l, h) for l in range(nl) for h in range(nh)]
    picks = [rng.sample(all_heads, TOP_K) for _ in range(N_RANDOM)]
    import os
    seen = {}
    if os.path.exists("results/e20_controls.csv"):
        for r in csv.DictReader(open("results/e20_controls.csv", newline="")):
            seen[int(r["i"])] = float(r["reduction"])
    for i in range(rand_start, min(rand_start + n_random, N_RANDOM)):
        if i in seen:
            continue
        hs = ablate(model, picks[i], hd)
        d, _ = mean_delta(model, tok, ds)
        for x in hs:
            x.remove()
        seen[i] = (d0 - d) / d0
        print(f"  random {i + 1:2}/{N_RANDOM}  reduction {seen[i]:+.3f}")
    with open("results/e20_controls.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["i", "reduction"])
        for i in sorted(seen): w.writerow([i, round(seen[i], 6)])
    ctrl = [seen[i] for i in sorted(seen)]
    if len(ctrl) < N_RANDOM:
        print(f"\n  {len(ctrl)}/{N_RANDOM} controls done; "
              f"rerun with a later --rand-start")
        return

    ctrl_sorted = sorted(ctrl)
    p95 = ctrl_sorted[int(0.95 * (len(ctrl_sorted) - 1))]
    out = {"model": model_id, "top_heads": top, "n_heads": len(rows),
           "pct_ablated": round(100 * TOP_K / len(rows), 2),
           "baseline_delta": d0, "ablated_delta": dk, "reduction": red,
           "baseline_absent": a0, "ablated_absent": ak,
           "absent_degradation": a0 - ak,
           "random_reductions": ctrl, "random_p95": p95}
    json.dump(out, open("results/e20_heldout.json", "w"), indent=1)

    a = red >= 0.30
    b = red > p95
    c = abs(a0 - ak) < 0.5
    print(f"\n=== READ RULE (declared before any pass) ===")
    print(f"  (a) reduction {red:.3f} >= 0.30                  {'PASS' if a else 'FAIL'}")
    print(f"  (b) reduction > random p95 ({p95:+.3f})          {'PASS' if b else 'FAIL'}")
    print(f"  (c) |score_absent shift| {abs(a0-ak):.3f} < 0.5   {'PASS' if c else 'FAIL'}")
    if not a:
        v = "MECHANISM FAILS"
    elif not b:
        v = "SPECIFICITY FAILS -- any 10 heads would do it"
    elif not c:
        v = "PERFORMANCE COST -- mitigated, but not without hurting the model"
    else:
        v = "MECHANISM REPLICATES"
    print(f"\n  VERDICT: {v}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--mode", required=True, choices=["sweep", "heldout"])
    ap.add_argument("--l0", type=int, default=0)
    ap.add_argument("--l1", type=int, default=23)
    ap.add_argument("--n-sub", type=int, default=12)
    ap.add_argument("--sweep-glob", default="results/e20_sweep_L*.csv")
    ap.add_argument("--n-random", type=int, default=20)
    ap.add_argument("--rand-start", type=int, default=0)
    ap.add_argument("--no-main", action="store_true")
    a = ap.parse_args()
    if a.mode == "sweep":
        run_sweep(a.model, a.l0, a.l1, a.n_sub)
    else:
        run_heldout(a.model, a.sweep_glob, a.n_random, a.rand_start, not a.no_main)
