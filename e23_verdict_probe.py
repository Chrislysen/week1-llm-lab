"""e23_verdict_probe.py: is the dialogue verdict ABSENT, or PRESENT BUT UNREAD?

Declared in docs/protocols/E23-verdict-probe.md before any extraction.
Gated SURROUNDED (A-1) and run anyway, because the ANSWER is unknown and
decision-relevant. NOT a novelty claim.

THE QUESTION. arXiv:2608.23651 decomposes small-model repetition of a failed
call behaviourally: "the failed call's surface form accounts for 83% of the
damage, while the semantic contribution of marking it failed is small." That is
equally consistent with two very different situations:

    ABSENT            the model never computes the verdict
    PRESENT-BUT-UNREAD it computes it, and its output distribution ignores it

A linear probe decides between them, and the answer matters: if the verdict is
present but unread, revocation inertia is addressable at decoding time; if it is
absent, it is not.

DESIGN. For each of the 384 E16 units, build the frozen plan prompt, append
'{"actions": ["' and the unit's own action identifier, and take the
residual-stream activation at the LAST token of that identifier -- so the
representation is specific to that action in that dialogue. Label = the unit's
status.

    rejected vs proposed   the decisive pair: identical except for the verdict
    rejected vs accepted   the wider contrast
    rejected vs never      mention plus verdict, against no mention

GroupKFold by instance (36 groups), so no dialogue from a training instance
appears in test. AUROC per layer; the reported figure is the best layer.
"""
import argparse
import json

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from e20_heads import load
from e21_circuit_identity import PREFIX, unit_prompt
from lineage_e16 import all_dialogues, corpus_hash

HASH = "70f136a47f5779c8"
PAIRS = [("rejected", "proposed"), ("rejected", "accepted"), ("rejected", "never")]
SEED = 20260906


@torch.no_grad()
def extract(model, tok, ds):
    """Per-unit residual-stream activations at the last identifier token."""
    X, y, g = [], [], []
    for d in ds:
        inst, dia = d["instance"], d["dialogue"]
        base = unit_prompt(tok, inst, dia)          # ends with '{"actions": ["'
        for u in d["units"]:
            ids = tok(base + u["action"], return_tensors="pt",
                      add_special_tokens=False).input_ids.to(model.device)
            hs = model(ids, output_hidden_states=True).hidden_states
            X.append(np.stack([h[0, -1].float().cpu().numpy() for h in hs]))
            y.append(u["status"])
            g.append(u["instance"])
    return np.stack(X), np.array(y), np.array(g)


def probe(X, y, g, a, b):
    """Grouped-CV AUROC per layer for class a vs b."""
    m = (y == a) | (y == b)
    Xs, ys, gs = X[m], (y[m] == a).astype(int), g[m]
    out = []
    for layer in range(Xs.shape[1]):
        Z = Xs[:, layer, :]
        preds = np.zeros(len(ys), dtype=float)
        for tr, te in GroupKFold(n_splits=6).split(Z, ys, gs):
            sc = StandardScaler().fit(Z[tr])
            clf = LogisticRegression(max_iter=2000, C=1.0, random_state=SEED)
            clf.fit(sc.transform(Z[tr]), ys[tr])
            preds[te] = clf.predict_proba(sc.transform(Z[te]))[:, 1]
        out.append(roc_auc_score(ys, preds))
    return out


def main(model_id):
    assert corpus_hash() == HASH
    tok, model = load(model_id)
    ds = all_dialogues()
    print(f"=== E23 {model_id} | extracting {sum(len(d['units']) for d in ds)} units ===")
    X, y, g = extract(model, tok, ds)
    print(f"  activations {X.shape}  (units, layers, hidden)\n")
    res = {}
    for a, b in PAIRS:
        aucs = probe(X, y, g, a, b)
        best = int(np.argmax(aucs))
        res[f"{a}_vs_{b}"] = {"auroc_by_layer": [round(v, 4) for v in aucs],
                              "best_layer": best, "best_auroc": round(aucs[best], 4)}
        print(f"  {a:9} vs {b:9}  best AUROC {aucs[best]:.4f} at layer {best}"
              f"   (final layer {aucs[-1]:.4f}, chance 0.50)")
    out = {"model": model_id, "n_layers": int(X.shape[1]), "results": res}
    tag = model_id.split("/")[-1]
    json.dump(out, open(f"results/e23_probe_{tag}.json", "w"), indent=1)
    print(f"\n  wrote results/e23_probe_{tag}.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    a = ap.parse_args()
    main(a.model)
