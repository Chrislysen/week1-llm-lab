"""e6_router.py: does corroboration-aware routing beat relevance at fixed budget?

The payoff experiment. E5 showed corroboration inoculates against a later
contradiction. If that is real and usable, a selector that spends its budget on
CORROBORATED claims should suppress adoption of a contradiction relative to one
that spends it on RELEVANT claims -- at the same budget, on the same pool.

THE POOL, per instance, is deliberately larger than the budget so selection
matters:

    SOURCE                    the authoritative ordering
    L1, L2, L3                faithful restatements of it
    C                         the contradiction (reverses the ordering)
    4 distractors             on-topic, constraint-irrelevant
                              -> 9 candidates, budget fits roughly 3

Every arm sees the same 9 candidates and the same word budget. Only the
selection rule changes.

    recency        newest first
    random         chance, averaged over seeds
    bm25           lexical relevance to the query
    dense          embedding relevance to the query
    anchorroute    relevance fused with corroboration support
    supportonly    corroboration support alone (ablation)
    oracle_corrob  hands over SOURCE + L1  -- the upper bound E5 predicts
    oracle_worst   hands over C + distractors -- the sabotage floor

Primary measure: adoption of the contradiction, among plans that resolve the
ordering either way. Secondary: whether the SOURCE and at least one faithful
restatement both survived selection, which is the mechanism E5 identified.

Run:  python e6_router.py --model llama3.2:3b
"""
import argparse
import json
import statistics

from budget import Budget
from context import RandomBudget, RecencyBudget, BM25Budget, DenseBudget, words
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_depth import build_chain, follows_corruption
from lineage_eval import check_plan, parse_plan
from lineage_router import AnchorRouteBudget, SupportOnlyBudget
from llm_client import OllamaClient
from structured import MAX_ATTEMPTS, ask_structured

TEMPERATURE = 0
BUDGET_WORDS = 60          # fits ~3 of 9 candidates; selection must bite
N_RANDOM_SEEDS = 5

SYSTEM = (
    "You are an operations engineer. You have just read a short discussion "
    "about {setting}. Produce the plan they agreed on, following everything "
    "that was established in the discussion."
)


#: A neutral closing turn. BudgetedPolicy reserves the LAST message as mandatory
#: current context, outside the budget. On a dialogue that is correct; on a bare
#: candidate pool it silently hands one arbitrary candidate a free pass -- which
#: is why the first inspection showed 65 words selected against a 60-word cap.
#: Appending an explicit closing turn gives the reserved slot something to be,
#: so all real candidates compete on the same budget.
CLOSING = "So what is the plan?"


def pool(instance, chain):
    """The 9 competing candidates, plus a neutral closing turn.

    Distractors come from the domain's own noise bank rather than from the
    instance's two DISTRACTOR messages. Padding those to four duplicated them
    verbatim, which both looks unnatural and inflates corroboration support --
    two identical messages corroborate each other perfectly.
    """
    from lineage_bench import DOMAINS, Message, SPEAKERS
    noise = DOMAINS[instance.domain]["noise"][:4]
    distract = [Message(msg_id=20_000 + i, speaker=SPEAKERS[i % 2], text=t,
                        lineage="DISTRACTOR")
                for i, t in enumerate(noise)]
    close = Message(msg_id=29_999, speaker=SPEAKERS[1], text=CLOSING,
                    lineage="DISTRACTOR")
    return ([chain.source] + list(chain.faithful) + [chain.corrupted[0]]
            + distract + [close])


def as_messages(cands):
    return [{"role": "user", "content": m.text} for m in cands]


def select(policy, cands, query):
    """Run a ContextPolicy over the pool and return the chosen candidates."""
    view = [{"role": "system", "content": "s"}] + as_messages(cands)
    out = policy.select(view, query=query)
    picked = []
    for m in out[1:]:
        for c in cands:
            if c.text == m["content"] and c not in picked:
                picked.append(c)
                break
    return picked


def arms():
    return ([("recency", RecencyBudget(BUDGET_WORDS)),
             ("bm25", BM25Budget(BUDGET_WORDS)),
             ("dense", DenseBudget(BUDGET_WORDS)),
             ("anchorroute", AnchorRouteBudget(BUDGET_WORDS)),
             ("supportonly", SupportOnlyBudget(BUDGET_WORDS))]
            + [(f"random{s}", RandomBudget(BUDGET_WORDS, seed=s))
               for s in range(N_RANDOM_SEEDS)])


def oracle_sets(chain, cands):
    dis = [m for m in cands if m.lineage == "DISTRACTOR"]
    return {
        "oracle_corrob": [chain.source, chain.faithful[0]],
        "oracle_worst": [chain.corrupted[0]] + dis[:1],
    }


def ask(client, model, instance, picked):
    body = "\n".join(f"{m.speaker}: {m.text}" for m in picked)
    messages = [
        {"role": "system", "content": SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content":
            f"DISCUSSION\n----------\n{body}\n\n{plan_instruction(instance)}"},
    ]
    budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
    return ask_structured(
        client=client, model=model, temperature=TEMPERATURE, messages=messages,
        validate=parse_plan, budget=budget, speaker="Operator",
        expected='It must have exactly two keys: "actions", a list of action '
                 'identifier strings, and "ready", true or false.')


def main(model, offset, limit):
    client = OllamaClient()
    instances = all_instances()[offset:None if limit is None else offset + limit]
    tag = model.replace(":", "-").replace(".", "")
    print(f"=== E6 router: {model}, {len(instances)} instances, "
          f"budget {BUDGET_WORDS} words of a 9-message pool ===\n")

    rows, detail = [], []
    for k, inst in enumerate(instances, 1):
        chain = build_chain(inst)
        cands = pool(inst, chain)
        query = plan_instruction(inst)
        picks = {n: select(p, cands, query) for n, p in arms()}
        picks.update(oracle_sets(chain, cands))

        for name, chosen in picks.items():
            res = ask(client, model, inst, chosen)
            text = res.accepted_text or res.last_text or ""
            chk = check_plan(text, inst)
            verdict = (follows_corruption(inst, chain, chk.actions)
                       if chk.parsed else None)
            # The closing turn is scaffolding, not a candidate.
            chosen = [m for m in chosen if m.text != CLOSING]
            lin = [m.lineage for m in chosen]
            rows.append({
                "model": model, "instance": inst.id, "domain": inst.domain,
                "arm": name, "n_selected": len(chosen),
                "words": sum(words(m.text) for m in chosen),
                "has_source": "SOURCE" in lin,
                "has_corrob": "FAITHFUL_RELAY" in lin,
                "has_corruption": "CORRUPTED_RELAY" in lin,
                "n_distractor": lin.count("DISTRACTOR"),
                "anchor_pair": "SOURCE" in lin and "FAITHFUL_RELAY" in lin,
                "parsed": chk.parsed,
                "verdict": verdict or "",
                "follows_source": verdict == "source",
                "follows_corruption": verdict == "corruption",
                "constraint_recall": chk.constraint_recall,
                "seconds": round(sum(e.seconds for e in res.attempts), 2),
            })
            detail.append({"instance": inst.id, "arm": name,
                           "selected": lin, "plan_text": text})
        print(f"  [{k:>2}/{len(instances)}] {inst.id}")

    write_csv(f"results/e6_router_{tag}_o{offset}.csv", rows, list(rows[0].keys()))
    with open(f"results/e6_router_{tag}_o{offset}.json", "w") as f:
        json.dump(detail, f, indent=2)

    print("\n=== selection composition and adoption, at matched budget ===")
    out = []
    names = [n for n, _ in arms() if not n.startswith("random")]
    names += ["random(mean)", "oracle_corrob", "oracle_worst"]
    for name in names:
        if name == "random(mean)":
            g = [r for r in rows if r["arm"].startswith("random") and r["parsed"]]
        else:
            g = [r for r in rows if r["arm"] == name and r["parsed"]]
        if not g:
            continue
        src = sum(r["follows_source"] for r in g)
        cor = sum(r["follows_corruption"] for r in g)
        out.append({
            "arm": name, "n": len(g),
            "words": round(statistics.mean(r["words"] for r in g), 1),
            "kept": round(statistics.mean(r["n_selected"] for r in g), 2),
            "has_source": round(statistics.mean(r["has_source"] for r in g), 3),
            "has_corrob": round(statistics.mean(r["has_corrob"] for r in g), 3),
            "anchor_pair": round(statistics.mean(r["anchor_pair"] for r in g), 3),
            "has_corrupt": round(statistics.mean(r["has_corruption"] for r in g), 3),
            "adoption": round(cor / (src + cor), 4) if src + cor else None,
            "recall": round(statistics.mean(
                r["constraint_recall"] for r in g
                if r["constraint_recall"] is not None), 4),
        })
    show(out, list(out[0].keys()))
    write_csv(f"results/e6_router_summary_{tag}.csv", out, list(out[0].keys()))
    print("\n  `anchor_pair` = SOURCE and at least one faithful restatement both")
    print("  survived selection. E5 says that is the mechanism; this column says")
    print("  whether each selector actually achieves it under the budget.")
    print(f"\nwrote results/e6_router_{tag}_o{offset}.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="llama3.2:3b")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    a = p.parse_args()
    main(a.model, a.offset, a.limit)
