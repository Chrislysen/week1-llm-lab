"""lineage_retrieval.py: retrieval authority inversion across all 36 instances.

OFFLINE. No model calls (the dense encoder runs locally on CPU).

Measured on the RANKING, not on the selection, exactly as
lineage_eval.retrieval_authority_inversion defines it: a constraint is an
eligible pair only when the ranking contains both its authoritative SOURCE and
at least one derivative (FAITHFUL_RELAY or CORRUPTED_RELAY). A constraint with
no derivative is evidence in neither direction and is excluded from the
denominator.

The query is the plan instruction -- the decision point, and the only place the
action vocabulary is ever visible.

CAVEAT ON THE RECENCY ROW, which must be read before the numbers.

Recency scores 1.0 inversion on all 36 instances, and that is a STRUCTURAL
CONSEQUENCE, not a finding. In Mode A every derivative is emitted after the
source it derives from, so a recency ordering places derivatives first by
construction. Recency cannot do anything else here.

It is reported because the number is real and hiding it would be worse, but it
is evidence about the generator's message order, not about retrieval. Only the
content-based selectors -- bm25, dense, fusion -- carry information about
whether relevance and authority come apart, and only against the random
baseline. The same caution does NOT apply to E1, where relays were produced by
live agents at unpredictable positions.

Run:  python lineage_retrieval.py
"""
import statistics

from context import (BM25Budget, DenseBudget, FusionBudget, RandomBudget,
                     RecencyBudget)
from experiment import show, write_csv
from lineage_bench import all_instances, plan_instruction
from lineage_eval import retrieval_authority_inversion

W = 250          # irrelevant to ranking, but keeps the constructors honest
N_RANDOM_SEEDS = 20


def selectors():
    return [
        ("recency", RecencyBudget(W)),
        ("bm25", BM25Budget(W)),
        ("dense", DenseBudget(W)),
        ("fusion", FusionBudget(W)),
    ]


def as_messages(instance):
    """The candidate pool, in the shape a policy expects."""
    return [{"role": "user", "content": m.text} for m in instance.messages]


def ranked_ids(policy, instance, query):
    pool = as_messages(instance)
    order = policy.priority(pool, query)
    return [instance.messages[i].msg_id for i in order]


def main():
    instances = all_instances()
    print(f"=== retrieval authority inversion, {len(instances)} instances ===")
    print("    ranking-based, eligible source/derived pairs only, offline\n")

    rows = []
    for inst in instances:
        query = plan_instruction(inst)
        for name, pol in selectors():
            rai = retrieval_authority_inversion(inst, ranked_ids(pol, inst, query))
            pos = {m: i for i, m in enumerate(ranked_ids(pol, inst, query))}
            src = [pos[m.msg_id] for m in inst.by_lineage("SOURCE")]
            der = [pos[m.msg_id] for m in inst.messages
                   if m.lineage in ("FAITHFUL_RELAY", "CORRUPTED_RELAY")]
            rows.append({
                "instance": inst.id,
                "domain": inst.domain,
                "graph": inst.graph,
                "selector": name,
                "eligible_pairs": rai["eligible_pairs"],
                "inverted_pairs": rai["inverted_pairs"],
                "inversion_rate": rai["rate"],
                "mean_rank_source": round(statistics.mean(src), 2),
                "mean_rank_derived": round(statistics.mean(der), 2),
                "gap": round(statistics.mean(der) - statistics.mean(src), 2),
            })

        # Chance baseline: a uniformly random ranking, averaged over seeds.
        vals = []
        for seed in range(N_RANDOM_SEEDS):
            pol = RandomBudget(W, seed=seed)
            r = retrieval_authority_inversion(inst, ranked_ids(pol, inst, query))
            if r["rate"] is not None:
                vals.append(r["rate"])
        rows.append({
            "instance": inst.id, "domain": inst.domain, "graph": inst.graph,
            "selector": f"random_x{N_RANDOM_SEEDS}",
            "eligible_pairs": rai["eligible_pairs"],
            "inverted_pairs": None,
            "inversion_rate": round(statistics.mean(vals), 4) if vals else None,
            "mean_rank_source": None, "mean_rank_derived": None, "gap": None,
        })

    write_csv("results/e2_retrieval_runs.csv", rows, list(rows[0].keys()))

    print("=== per selector, over 36 instances ===")
    agg = []
    names = [n for n, _ in selectors()] + [f"random_x{N_RANDOM_SEEDS}"]
    for name in names:
        g = [r for r in rows if r["selector"] == name]
        rates = [r["inversion_rate"] for r in g if r["inversion_rate"] is not None]
        row = {
            "selector": name,
            "n_instances": len(g),
            "mean_inversion_rate": round(statistics.mean(rates), 4),
            "instances_fully_inverted": sum(r == 1.0 for r in rates),
            "instances_never_inverted": sum(r == 0.0 for r in rates),
            "total_eligible_pairs": sum(r["eligible_pairs"] for r in g),
        }
        if g[0]["gap"] is not None:
            row["mean_rank_source"] = round(
                statistics.mean(r["mean_rank_source"] for r in g), 2)
            row["mean_rank_derived"] = round(
                statistics.mean(r["mean_rank_derived"] for r in g), 2)
            row["gap_derived_minus_source"] = round(
                statistics.mean(r["gap"] for r in g), 2)
        else:
            row["mean_rank_source"] = row["mean_rank_derived"] = None
            row["gap_derived_minus_source"] = None
        agg.append(row)
    show(agg, list(agg[0].keys()))
    write_csv("results/e2_retrieval_summary.csv", agg, list(agg[0].keys()))

    print("\n=== inversion rate by domain (rows) x selector (cols) ===")
    doms = sorted({r["domain"] for r in rows})
    grid = []
    for d in doms:
        cell = {"domain": d}
        for name in names:
            g = [r["inversion_rate"] for r in rows
                 if r["domain"] == d and r["selector"] == name
                 and r["inversion_rate"] is not None]
            cell[name] = round(statistics.mean(g), 3) if g else None
        grid.append(cell)
    show(grid, list(grid[0].keys()))

    print("\n=== inversion rate by graph ===")
    graphs = sorted({r["graph"] for r in rows})
    ggrid = []
    for gr in graphs:
        cell = {"graph": gr}
        for name in names:
            g = [r["inversion_rate"] for r in rows
                 if r["graph"] == gr and r["selector"] == name
                 and r["inversion_rate"] is not None]
            cell[name] = round(statistics.mean(g), 3) if g else None
        ggrid.append(cell)
    show(ggrid, list(ggrid[0].keys()))

    # TIE-BREAK DIAGNOSTIC. Reported with every BM25 number, permanently.
    #
    # BM25 gives exactly 0.0 to any message sharing no query term, and the
    # documented tie-break is (-score, -index): higher score, then MORE RECENT.
    # So on a mostly-tied score vector BM25 DEGENERATES TO RECENCY, and its
    # inversion rate stops being evidence about content.
    #
    # That is what is happening here. The query is the plan instruction, which
    # names actions by identifier (DRAIN_NODE -> one token "drain_node"), while
    # the dialogue uses verb phrases ("drain the failing node"). The two share
    # almost no vocabulary.
    print("\n=== BM25 tie-break diagnostic ===")
    from context import BM25Budget as _BM
    zero = tot = ident = 0
    agree = pairs = 0
    for inst in instances:
        q = plan_instruction(inst)
        docs = [m["content"] for m in as_messages(inst)]
        s = _BM(W).scores(docs, q)
        zero += sum(1 for x in s if x == 0.0)
        tot += len(s)
        rr = ranked_ids(RecencyBudget(W), inst, q)
        bb = ranked_ids(_BM(W), inst, q)
        ident += (rr == bb)
        ri = {m: i for i, m in enumerate(rr)}
        bi = {m: i for i, m in enumerate(bb)}
        ids = list(ri)
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                a, c = ids[x], ids[y]
                agree += (ri[a] < ri[c]) == (bi[a] < bi[c])
                pairs += 1
    print(f"  messages scoring exactly 0.0      {zero}/{tot} ({zero / tot:.1%})")
    print(f"  BM25 ranking identical to recency {ident}/{len(instances)} instances")
    print(f"  pairwise order agreement          {agree / pairs:.1%}")
    print("  -> BM25's inversion rate is largely the recency tie-break, NOT a")
    print("     content signal. Do not read it as independent evidence.")

    print("\nwrote results/e2_retrieval_runs.csv, e2_retrieval_summary.csv")


if __name__ == "__main__":
    main()
