"""e23c_binding.py: does the verdict probe bind to the ACTION, or just to the context?

CONTROL for E23/E23-B. Declared in docs/protocols/E23-verdict-probe.md before
any run. The threat E23-B named as most pressing: a probe reading `rejected` vs
`proposed` at 0.86-0.94 AUROC might be detecting *surface features of the reply
templates present in the dialogue* rather than a verdict bound to the specific
action being scored.

THE CONTROL. E16 rotations put units of DIFFERENT statuses inside the SAME
dialogue: 60 dialogues contain both a rejected and a proposed unit. For those,
the context is byte-identical -- both an acceptance-shaped and a
rejection-shaped reply are present -- and the only thing that differs is which
action identifier is scored.

If the probe is reading "this dialogue contains a rejection", it cannot separate
two units inside one dialogue and paired accuracy collapses to chance. If it is
reading "THIS action was rejected", it separates them.

Reported: standard grouped-CV AUROC (as E23), then WITHIN-DIALOGUE PAIRED
ACCURACY over dialogues holding both classes, using the same out-of-fold
predictions.
"""
import argparse
import json

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from transformers import AutoModelForCausalLM, AutoTokenizer

from e21_circuit_identity import unit_prompt
from lineage_e16 import all_dialogues, corpus_hash

HASH = "70f136a47f5779c8"
SEED = 20260906
PAIRS = [("rejected", "proposed"), ("rejected", "accepted")]


@torch.no_grad()
def extract(model, tok, ds):
    X, y, inst, dlg = [], [], [], []
    for d in ds:
        base = unit_prompt(tok, d["instance"], d["dialogue"])
        did = f"{d['instance'].id}_r{d['rotation']}"
        for u in d["units"]:
            ids = tok(base + u["action"], return_tensors="pt",
                      add_special_tokens=False).input_ids.to(model.device)
            hs = model(ids, output_hidden_states=True).hidden_states
            X.append(np.stack([h[0, -1].float().cpu().numpy() for h in hs]))
            y.append(u["status"]); inst.append(u["instance"]); dlg.append(did)
    return np.stack(X), np.array(y), np.array(inst), np.array(dlg)


def oof_predictions(X, y, g, layer, a, b):
    """Out-of-fold P(class a) at one layer, grouped by instance."""
    m = (y == a) | (y == b)
    Z, ys, gs = X[m][:, layer, :], (y[m] == a).astype(int), g[m]
    preds = np.zeros(len(ys))
    for tr, te in GroupKFold(n_splits=6).split(Z, ys, gs):
        sc = StandardScaler().fit(Z[tr])
        clf = LogisticRegression(max_iter=2000, random_state=SEED)
        clf.fit(sc.transform(Z[tr]), ys[tr])
        preds[te] = clf.predict_proba(sc.transform(Z[te]))[:, 1]
    return m, preds, ys


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return c - h, c + h


def main(model_id, gpu_gb):
    assert corpus_hash() == HASH
    tok = AutoTokenizer.from_pretrained(model_id)
    kw = dict(dtype=torch.bfloat16, low_cpu_mem_usage=True)
    kw.update(device_map="auto", max_memory={0: f"{gpu_gb}GiB", "cpu": "48GiB"}) \
        if gpu_gb else kw.update(device_map="cuda")
    model = AutoModelForCausalLM.from_pretrained(model_id, **kw).eval()
    X, y, inst, dlg = extract(model, tok, all_dialogues())
    print(f"=== E23-C {model_id} | {X.shape[0]} units, {X.shape[1]} layers ===\n")

    res = {}
    for a, b in PAIRS:
        # best layer by AUROC, as in E23
        best_l, best_auc = -1, -1.0
        for layer in range(X.shape[1]):
            _, p, ys = oof_predictions(X, y, inst, layer, a, b)
            auc = roc_auc_score(ys, p)
            if auc > best_auc:
                best_auc, best_l = auc, layer
        m, preds, ys = oof_predictions(X, y, inst, best_l, a, b)
        sub_dlg, sub_y = dlg[m], y[m]

        wins = tot = 0
        for did in set(sub_dlg):
            k = sub_dlg == did
            pa = preds[k][sub_y[k] == a]
            pb = preds[k][sub_y[k] == b]
            if len(pa) and len(pb):
                tot += 1
                wins += int(pa.mean() > pb.mean())
        acc = wins / tot if tot else float("nan")
        lo, hi = wilson(wins, tot)
        res[f"{a}_vs_{b}"] = {"best_layer": best_l, "auroc": round(best_auc, 4),
                              "paired_dialogues": tot, "paired_wins": wins,
                              "paired_acc": round(acc, 4),
                              "paired_ci": [round(lo, 4), round(hi, 4)]}
        print(f"  {a} vs {b}")
        print(f"     grouped-CV AUROC        {best_auc:.4f}  (layer {best_l})")
        print(f"     WITHIN-DIALOGUE paired  {wins}/{tot} = {acc:.4f}  "
              f"95% CI [{lo:.3f}, {hi:.3f}]   chance 0.500\n")

    tag = model_id.split("/")[-1]
    json.dump({"model": model_id, "results": res},
              open(f"results/e23c_binding_{tag}.json", "w"), indent=1)
    print(f"  wrote results/e23c_binding_{tag}.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--gpu-gb", type=float, default=None)
    a = ap.parse_args()
    main(a.model, a.gpu_gb)
