"""e16_preflight.py: does a budgeted retrieval policy orphan the rejection?

OFFLINE. No model is called. This is the mechanism half of the E16 zombie
screen, decided before a token is spent: under a word-budgeted context policy,
how often is a PROPOSAL retrieved into context while the REPLY that rejected
it (or accepted it) is dropped? A content-scoring policy is expected to keep
the action-bearing proposal and drop the content-poor reply; recency should
keep or drop the adjacent pair together; random should split them at chance.

If no policy orphans rejections at a usable rate, stage 2 of the screen has
nothing to test and is not run. If one does, stage 2 feeds exactly that
policy's selection to the decider.

Run:  python e16_preflight.py --budgets 25 35 50
"""
import argparse
import statistics

from context import (BM25Budget, DenseBudget, FusionBudget, RandomBudget,
                     RecencyBudget, query_for_finalisation, words)
from e10_independence import SYSTEM
from experiment import show, write_csv
from lineage_bench import plan_instruction
from lineage_e16 import all_dialogues, message_list, render

COLUMNS = ["budget", "policy", "n_pairs", "p_proposal_kept", "p_reply_kept",
           "p_reply_kept_given_proposal", "orphan_rate", "orphan_rate_rejected",
           "p_proposed_only_kept", "mean_words_kept"]


def policies(budget, seed=0):
    return [RecencyBudget(budget), RandomBudget(budget, seed=seed),
            BM25Budget(budget), DenseBudget(budget), FusionBudget(budget)]


def kept_positions(policy, msgs, query):
    """Dialogue positions kept by `policy`, current message included."""
    policy.select(msgs, query=query)
    sel = policy._last["selected_ids"]        # indices into the pool = dialogue[:-1]
    n = len(msgs) - 1
    return set(sel) | {n - 1}


def run(budgets):
    ds = all_dialogues()
    lengths = [sum(words(t) for _, t, _ in d["dialogue"]) for d in ds]
    print(f"=== E16 preflight: {len(ds)} dialogues, words per dialogue "
          f"min {min(lengths)} median {statistics.median(lengths)} max {max(lengths)} ===\n")
    rows = []
    for W in budgets:
        for pol in policies(W):
            pairs = []      # (status, proposal_kept, reply_kept)
            singles = []    # proposed-only: proposal_kept
            wk = []
            for d in ds:
                inst, dia = d["instance"], d["dialogue"]
                msgs = message_list(SYSTEM.format(setting=inst.setting), dia)
                query = query_for_finalisation(msgs, plan_instruction(inst))
                kept = kept_positions(pol, msgs, query)
                wk.append(pol._last["words_history"])
                pos = {}
                for i, (_, _, tag) in enumerate(dia):
                    pos.setdefault(tag[1], {})[tag[0]] = i
                for u in d["units"]:
                    p = pos.get(u["constraint"], {})
                    if u["status"] in ("accepted", "rejected"):
                        pairs.append((u["status"], p["proposal"] in kept, p["reply"] in kept))
                    elif u["status"] == "proposed":
                        singles.append(p["proposal"] in kept)
            n = len(pairs)
            pk = sum(a for _, a, _ in pairs) / n
            rk = sum(b for _, _, b in pairs) / n
            both = sum(a and b for _, a, b in pairs)
            orphan = sum(a and not b for _, a, b in pairs) / n
            rej = [(a, b) for s, a, b in pairs if s == "rejected"]
            orphan_rej = sum(a and not b for a, b in rej) / len(rej)
            rows.append({
                "budget": W, "policy": pol.label, "n_pairs": n,
                "p_proposal_kept": round(pk, 3), "p_reply_kept": round(rk, 3),
                "p_reply_kept_given_proposal": round(both / max(1, sum(a for _, a, _ in pairs)), 3),
                "orphan_rate": round(orphan, 3),
                "orphan_rate_rejected": round(orphan_rej, 3),
                "p_proposed_only_kept": round(sum(singles) / len(singles), 3),
                "mean_words_kept": round(statistics.mean(wk), 1),
            })
    show(rows, COLUMNS)
    write_csv("results/e16_preflight.csv", rows, COLUMNS)
    print("\n  wrote results/e16_preflight.csv")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budgets", type=int, nargs="+", default=[25, 35, 50])
    run(ap.parse_args().budgets)
