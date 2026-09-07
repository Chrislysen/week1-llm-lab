"""e27b_sweep.py: E27 at scale -- bootstrap CIs, layer sweep, six concepts.

Declared in docs/protocols/E27-estimator.md before any run.

E27 showed the four estimators disagreeing on the binary steering verdict in 5/5
informative concepts, but on single measurements at one layer per model. Three
things could still explain it: a lucky layer, a lucky set of contrastive pairs,
or noise in a single unrepeated delta.

E27-B removes all three.

  * LAYER SWEEP        several layers per model, not one.
  * BOOTSTRAP          resample the 8 contrastive pairs with replacement, refit
                       every estimator on each resample, and report a 95%
                       interval on each estimator's delta. This is the right
                       error bar: the measurement itself is deterministic
                       (temperature 0, one forward pass), so the sampling
                       variability lives entirely in which pairs were used to
                       estimate the direction.
  * MORE CONCEPTS      six rather than three.

A cell counts as BEATS only if the bootstrap lower bound exceeds the largest
random-control |delta| -- a stricter test than E27's point estimate.
"""
import argparse
import json

import numpy as np
import torch

from e27_estimator import (CONCEPTS, ESTIMATORS, SEED, acts, direction, effect,
                           layer_module, load, steer_hook)

#: three further concepts, same shape as E27's
EXTRA = {
    "politeness": {
        "pos": ["Would you mind terribly if I asked once more?",
                "I would be grateful if you could take a look.",
                "Might I trouble you for a moment of your time?",
                "If it is not too much bother, please consider it.",
                "I do apologise for the inconvenience caused.",
                "Thank you kindly for your patience with this.",
                "May I gently suggest an alternative approach?",
                "Please do let me know if that suits you."],
        "neg": ["Do it again.", "Look at this now.", "Give me a minute.",
                "Just consider it.", "That was inconvenient.",
                "Hurry up with this.", "Try something else instead.",
                "Tell me if that works."],
        "probe": "Asking a busy colleague to redo the report, I would say:",
        "a": " Would", "b": " Do",
    },
    "technicality": {
        "pos": ["The latency arises from queue contention at the ingress node.",
                "Throughput degrades superlinearly beyond the saturation point.",
                "The estimator is consistent but not unbiased in finite samples.",
                "Cache coherence is maintained by an invalidation protocol.",
                "The gradient vanishes through repeated sigmoid composition.",
                "Entropy encoding exploits the residual symbol redundancy.",
                "The kernel is positive semi-definite by construction.",
                "Convergence is governed by the spectral radius."],
        "neg": ["Things get slow when too many people use it at once.",
                "It gets much worse once it is too busy.",
                "The guess is about right but a bit off with small numbers.",
                "The computers keep their copies in step.",
                "The learning signal fades away over many steps.",
                "You can squeeze the file smaller by spotting repeats.",
                "The maths always works out non-negative.",
                "How fast it settles depends on one key number."],
        "probe": "Explaining why the system slowed down, I would say the cause was",
        "a": " contention", "b": " traffic",
    },
    "tense": {
        "pos": ["The company reported record profits last year.",
                "She walked to the station before dawn.",
                "They finished the project ahead of schedule.",
                "The bridge collapsed during the storm.",
                "He studied physics at university.",
                "The team won three matches in a row.",
                "It rained heavily throughout the night.",
                "We arrived just before the doors closed."],
        "neg": ["The company reports record profits this year.",
                "She walks to the station before dawn.",
                "They finish the project ahead of schedule.",
                "The bridge collapses during the storm.",
                "He studies physics at university.",
                "The team wins three matches in a row.",
                "It rains heavily throughout the night.",
                "We arrive just before the doors close."],
        "probe": "Describing the incident to the committee, I would say it",
        "a": " occurred", "b": " occurs",
    },
}
ALL = {**CONCEPTS, **EXTRA}


def boot_deltas(model, tok, mod, A, B, c, alpha, est, reps, rng):
    """Bootstrap the contrastive pairs, refit the direction, measure the delta."""
    e0 = effect(model, tok, c["probe"], c["a"], c["b"])
    n = len(A)
    out = []
    for _ in range(reps):
        idx = rng.integers(0, n, n)
        try:
            w = direction(A[idx], B[idx], est)
        except Exception:
            continue
        if not np.all(np.isfinite(w)):
            continue
        h = mod.register_forward_hook(steer_hook(torch.tensor(w), alpha))
        out.append(effect(model, tok, c["probe"], c["a"], c["b"]) - e0)
        h.remove()
    return e0, np.array(out)


def main(mid, layers, alpha, reps, n_random):
    tok, model = load(mid)
    rng = np.random.default_rng(SEED)
    res, disagree, informative = {}, 0, 0
    print(f"=== E27-B {mid} | layers {layers} | alpha {alpha} | boot {reps} ===\n")
    for layer in layers:
        mod = layer_module(model, layer)
        res[layer] = {}
        for cname, c in ALL.items():
            A = acts(model, tok, c["pos"], layer)
            B = acts(model, tok, c["neg"], layer)
            e0 = effect(model, tok, c["probe"], c["a"], c["b"])
            rnd = []
            for _ in range(n_random):
                v = rng.normal(size=A.shape[1]); v /= np.linalg.norm(v)
                h = mod.register_forward_hook(steer_hook(torch.tensor(v), alpha))
                rnd.append(abs(effect(model, tok, c["probe"], c["a"], c["b"]) - e0))
                h.remove()
            rmax = max(rnd)
            cell = {"baseline": e0, "random_absmax": float(rmax), "est": {}}
            verdicts = {}
            for est in ESTIMATORS:
                _, d = boot_deltas(model, tok, mod, A, B, c, alpha, est, reps, rng)
                lo, hi = np.percentile(d, [2.5, 97.5])
                beats = bool(lo > rmax)
                verdicts[est] = beats
                cell["est"][est] = {"mean": float(d.mean()), "lo": float(lo),
                                    "hi": float(hi), "beats": beats}
            cell["verdicts"] = verdicts
            res[layer][cname] = cell
            if any(verdicts.values()):
                informative += 1
                if len(set(verdicts.values())) > 1:
                    disagree += 1
            flag = ("DISAGREE" if len(set(verdicts.values())) > 1
                    else ("all-beat" if all(verdicts.values()) else "uninformative"))
            body = "  ".join(
                f"{e}:{cell['est'][e]['mean']:+6.2f}[{cell['est'][e]['lo']:+.2f}]"
                f"{'*' if verdicts[e] else ' '}" for e in ESTIMATORS)
            print(f"  L{layer:<3} {cname:12} rnd{rmax:6.2f} | {body} | {flag}")
        print()
    tag = mid.split("/")[-1]
    json.dump({"model": mid, "alpha": alpha, "reps": reps, "results": res},
              open(f"results/e27b_{tag}.json", "w"), indent=1)
    print(f"  informative cells {informative}, of which DISAGREE {disagree}")
    print(f"  wrote results/e27b_{tag}.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--layers", type=int, nargs="+", default=[12, 18, 24])
    ap.add_argument("--alpha", type=float, default=20.0)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--n-random", type=int, default=12)
    a = ap.parse_args()
    main(a.model, a.layers, a.alpha, a.reps, a.n_random)
