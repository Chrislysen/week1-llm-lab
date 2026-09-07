"""e26_steer.py: can the unused verdict be RECOVERED by steering?

Declared in docs/protocols/E26-steering.md before any run.

THE PREDICTION UNDER TEST IS MY OWN. E23-B/C established that at 0.8B-1.5B the
dialogue verdict is 86-94% linearly decodable and action-bound, while the output
distribution barely uses it (behavioural verdict effect -0.058 to +0.121 nats).
From that I predicted decoding-time repair should work. This tests it.

It also tests that prediction against a published negative: arXiv:2603.18353
reports probes at 98.2% AUROC against 45.1% output sensitivity in clinical
triage, and finds steering largely FAILS to close the gap -- "concept bottleneck
steering corrected 20% of missed hazards but disrupted 53% of correct
detections". If steering works here, this instrument is a case where the gap is
actionable; if it does not, that is a replication of their negative in a new
domain. Both outcomes are informative.

METHOD. Fit the same logistic probe E23 used (rejected vs proposed) at the
model's best layer, take its weight vector as the verdict direction, and add
alpha * w_hat to the residual stream at that layer during the forward pass.
Measure the behavioural verdict effect exactly as E22/E23 did:

    VERDICT EFFECT = a(proposed) - a(rejected)

where a() is the mean per-token log-probability of the unit's action identifier
at first-plan position. Steering is applied at every token position.

CONTROLS. Random unit directions at the same alpha, and the negative direction
(-alpha), which should move the effect the other way if the direction is real.
"""
import argparse
import json

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from transformers import AutoModelForCausalLM, AutoTokenizer

from e19_entrainment import score_sentence
from e21_circuit_identity import STATUSES, contrasts, unit_prompt
from lineage_e16 import all_dialogues, corpus_hash

HASH = "70f136a47f5779c8"
SEED = 20260907
BEST_LAYER = {"Qwen/Qwen3.5-0.8B": 13, "Qwen/Qwen2.5-1.5B-Instruct": 18}
SEARCH, HELDOUT = slice(0, 72), slice(72, 144)


def load(mid):
    tok = AutoTokenizer.from_pretrained(mid)
    m = AutoModelForCausalLM.from_pretrained(
        mid, dtype=torch.bfloat16, device_map="cuda", low_cpu_mem_usage=True).eval()
    return tok, m


def layer_module(model, layer):
    """The decoder block whose OUTPUT is residual-stream layer `layer`."""
    base = getattr(model, "model", model)
    base = getattr(base, "language_model", base)
    return base.layers[layer - 1]


@torch.no_grad()
def collect(model, tok, ds, layer):
    X, y = [], []
    for d in ds:
        base = unit_prompt(tok, d["instance"], d["dialogue"])
        for u in d["units"]:
            ids = tok(base + u["action"], return_tensors="pt",
                      add_special_tokens=False).input_ids.to(model.device)
            hs = model(ids, output_hidden_states=True).hidden_states
            X.append(hs[layer][0, -1].float().cpu().numpy())
            y.append(u["status"])
    return np.stack(X), np.array(y)


def verdict_direction(model, tok, layer, method="logistic"):
    """Unit-norm verdict direction for rejected-vs-proposed, fitted on SEARCH.

    method="logistic"  logistic-regression weight (E26's original choice)
    method="dim"       difference-in-means, the CAA/ActAdd standard
    """
    X, y = collect(model, tok, all_dialogues()[SEARCH], layer)
    m = (y == "rejected") | (y == "proposed")
    if method == "dim":
        w = X[y == "rejected"].mean(0) - X[y == "proposed"].mean(0)
    else:
        sc = StandardScaler().fit(X[m])
        clf = LogisticRegression(max_iter=2000, random_state=SEED)
        clf.fit(sc.transform(X[m]), (y[m] == "rejected").astype(int))
        w = clf.coef_[0] / sc.scale_
    return w / np.linalg.norm(w), float(np.linalg.norm(
        X[y == "rejected"].mean(0) - X[y == "proposed"].mean(0)))


def steer_hook(vec, alpha):
    def hook(mod, args, out):
        h = out[0] if isinstance(out, tuple) else out
        h = h + alpha * vec.to(h.dtype).to(h.device)
        return (h,) + out[1:] if isinstance(out, tuple) else h
    return hook


@torch.no_grad()
def measure(model, tok, ds):
    acc = {s: [] for s in STATUSES}
    for d in ds:
        p = unit_prompt(tok, d["instance"], d["dialogue"])
        for u in d["units"]:
            s, _, _ = score_sentence(model, tok, p, u["action"])
            acc[u["status"]].append(s)
    import statistics
    return {s: statistics.mean(v) for s, v in acc.items() if v}


def effect(m):
    return m["proposed"] - m["rejected"]


def main(mid, alphas, n_random, method):
    assert corpus_hash() == HASH
    layer = BEST_LAYER[mid]
    tok, model = load(mid)
    ds = all_dialogues()[HELDOUT]
    print(f"=== E26 {mid} | steering layer {layer} | HELD-OUT n={len(ds)} ===\n")

    w, dim_norm = verdict_direction(model, tok, layer, method)
    print(f"  direction method={method}   ||mean(rej)-mean(prop)|| = {dim_norm:.3f}")
    hidden = w.shape[0]
    wt = torch.tensor(w)
    mod = layer_module(model, layer)

    base = measure(model, tok, ds)
    e0 = effect(base)
    print(f"  baseline           verdict effect {e0:+.4f}   "
          f"(acc {base['accepted']:+.3f} rej {base['rejected']:+.3f} "
          f"prop {base['proposed']:+.3f} nev {base['never']:+.3f})\n")

    out = {"model": mid, "layer": layer, "baseline": base, "baseline_effect": e0,
           "hidden": hidden, "steered": {}, "random": {}}
    for a in alphas:
        for sign, tag in ((+1, "+"), (-1, "-")):
            h = mod.register_forward_hook(steer_hook(wt, sign * a))
            m = measure(model, tok, ds)
            h.remove()
            out["steered"][f"{tag}{a}"] = {"levels": m, "effect": effect(m)}
            print(f"  alpha {tag}{a:<6}      verdict effect {effect(m):+.4f}   "
                  f"delta {effect(m)-e0:+.4f}")
    rng = np.random.default_rng(SEED)
    a = alphas[-1]
    rs = []
    for i in range(n_random):
        v = rng.normal(size=hidden); v /= np.linalg.norm(v)
        h = mod.register_forward_hook(steer_hook(torch.tensor(v), a))
        m = measure(model, tok, ds)
        h.remove()
        rs.append(effect(m))
        print(f"  random {i+1}/{n_random} a={a}  verdict effect {effect(m):+.4f}   "
              f"delta {effect(m)-e0:+.4f}")
    out["random"][str(a)] = rs
    tag = mid.split("/")[-1] + ("_dim" if method == "dim" else "")
    out["method"] = method
    json.dump(out, open(f"results/e26_steer_{tag}.json", "w"), indent=1)
    print(f"\n  wrote results/e26_steer_{tag}.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--alphas", type=float, nargs="+", default=[2.0, 5.0])
    ap.add_argument("--n-random", type=int, default=4)
    ap.add_argument("--method", default="logistic", choices=["logistic","dim"])
    a = ap.parse_args()
    main(a.model, a.alphas, a.n_random, a.method)
