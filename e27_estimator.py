"""e27_estimator.py: is a steering NULL an artefact of the direction estimator?

Declared in docs/protocols/E27-estimator.md before any run.

THE CLAIM. E26 -> E26-B found, by accident, that the same probe, layer, data and
measurement gave "indistinguishable from random" with a logistic-regression
direction and "beats every random control" with difference-in-means. If that
generalises, published steering NULLS are estimator-dependent, and a literature
full of "steering does not work here" results is under-determined.

WHAT IS AND IS NOT PUBLISHED (gate, 2026-09-07):
  * estimators (MD / LR / PCA) are compared descriptively in method surveys;
  * arXiv:2608.08159 audits steering measurement confounds across 17 models and
    flips a null -- but audits units, readout metric, operating point, layer and
    neuron selection, NOT the direction estimator;
  * arXiv:2505.22637 studies steering unreliability and explicitly does not
    compare estimators, attributing it to prompt type and activation geometry.
Not found: estimator choice demonstrated as a null-flipping confound.

DESIGN. Several concepts x several estimators, one measurement, random controls.
For each (concept, estimator) the verdict is binary -- does the steered effect
exceed every random-direction control? -- and the question is how often two
estimators disagree on that verdict for the same concept.

Estimators:
  dim       mean(A) - mean(B)                      (CAA / ActAdd standard)
  logistic  logistic-regression weight             (E26's original choice)
  pca       top principal component of paired diffs
  lda       within-class-whitened mean difference  (mass-mean probing)
"""
import argparse
import json

import numpy as np
import torch
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 20260907
ESTIMATORS = ("dim", "logistic", "pca", "lda")

#: concept -> (contrastive pairs for extraction, probe prompt, token A, token B)
#: the measured effect is logprob(A) - logprob(B) on the probe prompt.
CONCEPTS = {
    "sentiment": {
        "pos": ["The film was wonderful and moving.", "A delightful, warm story.",
                "I loved every minute of it.", "An excellent and joyful piece.",
                "Beautifully made and uplifting.", "A charming, superb result.",
                "Genuinely brilliant work.", "It was a pleasure throughout."],
        "neg": ["The film was dreadful and dull.", "A tedious, bleak story.",
                "I hated every minute of it.", "An awful and miserable piece.",
                "Badly made and depressing.", "A dismal, terrible result.",
                "Genuinely appalling work.", "It was a chore throughout."],
        "probe": "Overall, my honest opinion of it is that it was",
        "a": " excellent", "b": " terrible",
    },
    "formality": {
        "pos": ["I would be most grateful for your assistance.",
                "Please find the requested document enclosed.",
                "It is my pleasure to inform you of the outcome.",
                "We shall proceed in accordance with the agreement.",
                "Kindly advise on the appropriate course of action.",
                "I write to confirm receipt of your correspondence.",
                "Allow me to express my sincere appreciation.",
                "The matter has been considered at some length."],
        "neg": ["Thanks a bunch for the help!", "Here's that thing you wanted.",
                "Good news, it worked out!", "We'll just go with the deal.",
                "Let me know what you reckon.", "Got your message, cheers.",
                "Really, thanks loads.", "We had a think about it."],
        "probe": "Writing to a colleague about the delay, I would begin:",
        "a": " Furthermore", "b": " Anyway",
    },
    "certainty": {
        "pos": ["This is certainly the case.", "The result is definitive.",
                "There is no doubt about the outcome.", "It is unquestionably true.",
                "The evidence is conclusive.", "This is established beyond dispute.",
                "We know this with certainty.", "The answer is unambiguous."],
        "neg": ["This might possibly be the case.", "The result is unclear.",
                "There is considerable doubt about the outcome.",
                "It may perhaps be true.", "The evidence is inconclusive.",
                "This remains disputed.", "We cannot be sure of this.",
                "The answer is ambiguous."],
        "probe": "Asked whether the treatment works, a careful expert would say it",
        "a": " definitely", "b": " possibly",
    },
}


def load(mid):
    tok = AutoTokenizer.from_pretrained(mid)
    m = AutoModelForCausalLM.from_pretrained(
        mid, dtype=torch.bfloat16, device_map="cuda", low_cpu_mem_usage=True).eval()
    return tok, m


def layer_module(model, layer):
    base = getattr(model, "model", model)
    base = getattr(base, "language_model", base)
    return base.layers[layer - 1]


@torch.no_grad()
def acts(model, tok, texts, layer):
    out = []
    for t in texts:
        ids = tok(t, return_tensors="pt").input_ids.to(model.device)
        hs = model(ids, output_hidden_states=True).hidden_states
        out.append(hs[layer][0, -1].float().cpu().numpy())
    return np.stack(out)


def direction(A, B, method):
    """Unit-norm direction pointing from B toward A."""
    if method == "dim":
        w = A.mean(0) - B.mean(0)
    elif method == "logistic":
        X = np.vstack([A, B]); y = np.r_[np.ones(len(A)), np.zeros(len(B))]
        sc = StandardScaler().fit(X)
        clf = LogisticRegression(max_iter=5000, random_state=SEED)
        clf.fit(sc.transform(X), y)
        w = clf.coef_[0] / sc.scale_
    elif method == "pca":
        D = A - B                       # paired differences
        w = PCA(n_components=1, random_state=SEED).fit(D).components_[0]
        if w @ (A.mean(0) - B.mean(0)) < 0:
            w = -w
    elif method == "lda":
        X = np.vstack([A - A.mean(0), B - B.mean(0)])
        cov = np.cov(X.T) + 1e-3 * np.eye(X.shape[1])
        w = np.linalg.solve(cov, A.mean(0) - B.mean(0))
    else:
        raise ValueError(method)
    return w / np.linalg.norm(w)


def steer_hook(vec, alpha):
    def hook(mod, args, out):
        h = out[0] if isinstance(out, tuple) else out
        h = h + alpha * vec.to(h.dtype).to(h.device)
        return (h,) + out[1:] if isinstance(out, tuple) else h
    return hook


@torch.no_grad()
def effect(model, tok, probe, a, b):
    """logprob(a) - logprob(b) as the continuation of `probe`."""
    ids = tok(probe, return_tensors="pt").input_ids.to(model.device)
    lp = torch.log_softmax(model(ids).logits[0, -1].float(), dim=-1)
    ta = tok(a, add_special_tokens=False).input_ids[0]
    tb = tok(b, add_special_tokens=False).input_ids[0]
    return (lp[ta] - lp[tb]).item()


def main(mid, layer, alpha, n_random):
    tok, model = load(mid)
    mod = layer_module(model, layer)
    rng = np.random.default_rng(SEED)
    results = {}
    print(f"=== E27 {mid} | layer {layer} | alpha {alpha} ===\n")
    for cname, c in CONCEPTS.items():
        A = acts(model, tok, c["pos"], layer)
        B = acts(model, tok, c["neg"], layer)
        e0 = effect(model, tok, c["probe"], c["a"], c["b"])
        hidden = A.shape[1]
        rnd = []
        for _ in range(n_random):
            v = rng.normal(size=hidden); v /= np.linalg.norm(v)
            h = mod.register_forward_hook(steer_hook(torch.tensor(v), alpha))
            rnd.append(effect(model, tok, c["probe"], c["a"], c["b"]) - e0)
            h.remove()
        rmax = max(abs(x) for x in rnd)
        print(f"  {cname:11} baseline {e0:+7.3f}   random |delta| max {rmax:.3f}")
        results[cname] = {"baseline": e0, "random": rnd, "random_absmax": rmax,
                          "estimators": {}}
        for est in ESTIMATORS:
            w = torch.tensor(direction(A, B, est))
            h = mod.register_forward_hook(steer_hook(w, alpha))
            d = effect(model, tok, c["probe"], c["a"], c["b"]) - e0
            h.remove()
            beats = d > rmax
            results[cname]["estimators"][est] = {"delta": d, "beats_random": bool(beats)}
            print(f"      {est:9} delta {d:+7.3f}   {'BEATS random' if beats else 'no'}")
        verdicts = {e: results[cname]["estimators"][e]["beats_random"] for e in ESTIMATORS}
        if len(set(verdicts.values())) > 1:
            print(f"      -> ESTIMATORS DISAGREE: {verdicts}")
        print()
    tag = mid.split("/")[-1]
    json.dump({"model": mid, "layer": layer, "alpha": alpha, "results": results},
              open(f"results/e27_estimator_{tag}_L{layer}.json", "w"), indent=1)
    print(f"  wrote results/e27_estimator_{tag}_L{layer}.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--layer", type=int, default=18)
    ap.add_argument("--alpha", type=float, default=20.0)
    ap.add_argument("--n-random", type=int, default=8)
    a = ap.parse_args()
    main(a.model, a.layer, a.alpha, a.n_random)
