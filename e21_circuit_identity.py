"""e21_circuit_identity.py: are entrainment heads also revocation-inertia heads?

MECHANISTIC. Declared in docs/protocols/E21-circuit-identity.md before any pass.
Gated SURROUNDED (docs/E16-CANDIDATES.md, H-1) and run anyway: the identity
question is causal and either answer is informative. NOT a novelty claim.

TRANSFER TEST, no circularity. The head set comes from E20, where it was
selected purely by its effect on SENTENCE ENTRAINMENT scoring, on SEARCH
instances (0-17). Here it is applied to a different quantity -- the model's
preference for a constrained ACTION IDENTIFIER in a plan -- on HELD-OUT
instances (18-35), which the head selection never saw.

MEASURE. For each unit, teacher-force its action identifier as the first entry
of the plan and take the mean per-token log-probability:

    a(unit) = mean_t log p(id_t | prompt + '{"actions": ["', id_<t)

Aggregated by the unit's E16 status, this gives:

    INERTIA   = a(rejected) - a(never)     persistence of a withdrawn constraint
    OBEDIENCE = a(accepted) - a(never)     uptake of an endorsed one

If entrainment heads carry the zombie, ablating them should cut INERTIA while
leaving OBEDIENCE comparatively intact.
"""
import argparse
import json
import statistics

from e10_independence import SYSTEM
from e19_entrainment import score_sentence
from e20_heads import HELDOUT, TOP_K, ablate, head_dim, load
from lineage_bench import plan_instruction
from lineage_e16 import all_dialogues, corpus_hash, render

HASH = "70f136a47f5779c8"
PREFIX = '{"actions": ["'
STATUSES = ("accepted", "proposed", "rejected", "never")
SEED = 20260906
N_RANDOM = 10


def unit_prompt(tok, inst, dia):
    """The frozen E16 plan prompt, chat-templated, prefilled up to the first
    action identifier so the scored tokens are exactly that identifier."""
    msgs = [{"role": "system", "content": SYSTEM.format(setting=inst.setting)},
            {"role": "user",
             "content": f"DISCUSSION\n----------\n{render(dia)}\n\n"
                        f"{plan_instruction(inst)}"}]
    return tok.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True) + PREFIX


def measure(model, tok, ds):
    """mean action-identifier log-prob per status."""
    acc = {s: [] for s in STATUSES}
    for d in ds:
        inst, dia = d["instance"], d["dialogue"]
        prompt = unit_prompt(tok, inst, dia)
        for u in d["units"]:
            s, _, _ = score_sentence(model, tok, prompt, u["action"])
            acc[u["status"]].append(s)
    return {s: statistics.mean(v) for s, v in acc.items() if v}


def contrasts(m):
    return {"inertia": m["rejected"] - m["never"],
            "obedience": m["accepted"] - m["never"],
            "mention": m["proposed"] - m["never"]}


def main(model_id):
    assert corpus_hash() == HASH
    top = [tuple(x) for x in json.load(open("results/e20_main.json"))["top"]]
    tok, model = load(model_id)
    hd = head_dim(model)
    nl, nh = model.config.num_hidden_layers, model.config.num_attention_heads
    ds = all_dialogues()[HELDOUT]
    print(f"=== E21 {model_id} | HELD-OUT n={len(ds)} | entrainment heads {top} ===\n")

    base = measure(model, tok, ds)
    cb = contrasts(base)
    print("  baseline   " + "  ".join(f"{s} {base[s]:+.3f}" for s in STATUSES))
    print(f"             INERTIA {cb['inertia']:+.4f}   OBEDIENCE {cb['obedience']:+.4f}"
          f"   MENTION {cb['mention']:+.4f}\n")

    hs = ablate(model, top, hd)
    abl = measure(model, tok, ds)
    for x in hs:
        x.remove()
    ca = contrasts(abl)
    print("  ablated    " + "  ".join(f"{s} {abl[s]:+.3f}" for s in STATUSES))
    print(f"             INERTIA {ca['inertia']:+.4f}   OBEDIENCE {ca['obedience']:+.4f}"
          f"   MENTION {ca['mention']:+.4f}\n")

    import random
    rng = random.Random(SEED)
    all_heads = [(l, h) for l in range(nl) for h in range(nh)]
    ctrl = []
    for i in range(N_RANDOM):
        hs = ablate(model, rng.sample(all_heads, TOP_K), hd)
        m = measure(model, tok, ds)
        for x in hs:
            x.remove()
        c = contrasts(m)
        ctrl.append(c)
        print(f"  random {i+1:2}/{N_RANDOM}  INERTIA {c['inertia']:+.4f}  "
              f"OBEDIENCE {c['obedience']:+.4f}")

    out = {"model": model_id, "heads": top, "baseline": base, "ablated": abl,
           "baseline_contrasts": cb, "ablated_contrasts": ca,
           "random_contrasts": ctrl}
    json.dump(out, open("results/e21_circuit.json", "w"), indent=1)
    print(f"\n  wrote results/e21_circuit.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    a = ap.parse_args()
    main(a.model)
