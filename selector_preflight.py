"""selector_preflight.py: do the real selectors actually select differently?

OFFLINE. Replays saved real transcripts through every selector and reports what
each one would have chosen. No model is called and no run is scored, so this
costs nothing and can be repeated freely.

It exists to answer one question before spending a 15-run experiment:

    on REAL dialogues, do BM25 / dense / fusion produce meaningfully different
    context from recency -- or do they converge on the same messages?

The pool audit in docs/research-design.md S0 gives concrete reason to worry: the
domain vocabulary is spread across the generated paraphrases, so a lexical
retriever can rank recent restatements above the originals and land exactly
where recency already was. `context.preflight` only checks that selections
differ at all; this measures HOW MUCH, and whether the difference buys any
task-critical source information.

Run:  python selector_preflight.py
"""
import glob
import json
import statistics

from context import (BM25Budget, DenseBudget, FusionBudget, OracleBudget,
                     RandomBudget, RecencyBudget, ScoringPolicy,
                     query_for_finalisation, words)
from engine import Entry, view_for
from experiment import show, write_csv
from scenario import AGENT_A, CONSTRAINTS, FINAL_PLAN_INSTRUCTION, INCIDENT

W = 250
N_SEEDS = 20        # seeds averaged for the chance baseline

SOURCE_TURNS = sorted({c.stated_at_turn for c in CONSTRAINTS})
SOURCE_TEXTS = [INCIDENT.seed_dialogue[t][1] for t in SOURCE_TURNS]


def selectors(seed=0):
    """Every arm. Oracle is included as the diagnostic upper bound, not an arm."""
    return [
        ("recency", RecencyBudget(W)),
        ("random", RandomBudget(W, seed=seed)),
        ("bm25", BM25Budget(W)),
        ("dense", DenseBudget(W)),
        ("fusion", FusionBudget(W)),
        ("oracle*", OracleBudget(W, SOURCE_TEXTS)),
    ]


def load(path):
    with open(path) as f:
        data = json.load(f)
    transcript = [Entry(**m) for m in data["messages"]]
    view = view_for(AGENT_A, transcript)
    query = query_for_finalisation(view, FINAL_PLAN_INSTRUCTION)
    return view, query, data["meta"]["seeded_turns"]


def indices_of(view, chosen):
    """Positions in the RETRIEVED HISTORY (0-based over the candidate pool).

    Excludes the system prompt and the mandatory current message, so this is
    exactly what the policy chose to spend its budget on.
    """
    rest = view[1:]
    return [rest.index(m) for m in chosen[1:-1]]


def mean_rank(ranked, subset):
    """Mean 1-based rank of `subset` within a priority ordering."""
    pos = {i: r for r, (i, _) in enumerate(ranked, start=1)}
    vals = [pos[i] for i in subset if i in pos]
    return round(statistics.mean(vals), 2) if vals else None


def jaccard(a, b):
    a, b = set(a), set(b)
    return round(len(a & b) / len(a | b), 3) if (a | b) else 1.0


def main():
    paths = sorted(glob.glob("transcripts/pilot/*.json") + glob.glob("transcripts/exp/*.json"))
    if not paths:
        raise SystemExit("no saved transcripts found")

    print(f"=== selector preflight: {len(paths)} saved real transcripts, W = {W} ===")
    print(f"    source messages per transcript: {len(SOURCE_TEXTS)}")
    print("    OFFLINE -- no model calls, nothing scored\n")

    rows, picks, ranks = [], {}, []
    for path in paths:
        view, query, seeded = load(path)
        rest = view[1:]
        pool = rest[:-1]                      # candidates: the current message is out
        source_idx = {i for i, m in enumerate(pool) if m["content"] in SOURCE_TEXTS}
        generated_idx = {i for i in range(len(pool)) if i >= seeded}

        for name, pol in selectors(seed=1):
            chosen = pol.select(view, query=query)
            idx = indices_of(view, chosen)
            got = source_idx & set(idx)
            rows.append({
                "transcript": path.split("/")[-1].replace(".json", ""),
                "selector": name,
                "n_candidates": len(pool),
                "n_selected": len(idx),
                "history_words": sum(words(m["content"]) for m in chosen[1:-1]),
                "current_words": words(chosen[-1]["content"]),
                "selected_ids": "|".join(map(str, idx)),
                "source_available": len(source_idx),
                "source_retrieved": len(got),
                "retrieval_recall": round(len(got) / len(source_idx), 4) if source_idx else None,
            })
            picks.setdefault(path, {})[name] = idx

            # Source vs generated-message ranking: where does each scorer put
            # the authoritative originals relative to the agents' own restatements?
            if isinstance(pol, ScoringPolicy):
                ranked = pol.ranking(pool, query)
                ranks.append({
                    "selector": name,
                    "mean_rank_source": mean_rank(ranked, sorted(source_idx)),
                    "mean_rank_generated": mean_rank(ranked, sorted(generated_idx)),
                })

    print("=== per selector, aggregated over transcripts ===")
    agg = []
    for name, _ in selectors():
        g = [r for r in rows if r["selector"] == name]
        agg.append({
            "selector": name,
            "n": len(g),
            "mean_selected": round(statistics.mean(r["n_selected"] for r in g), 2),
            "mean_history_words": round(
                statistics.mean(r["history_words"] for r in g), 1),
            "mean_current_words": round(
                statistics.mean(r["current_words"] for r in g), 1),
            "mean_retrieval_recall": round(
                statistics.mean(r["retrieval_recall"] for r in g), 4),
            "perfect_recall_runs": sum(r["retrieval_recall"] == 1.0 for r in g),
            "zero_recall_runs": sum(r["retrieval_recall"] == 0.0 for r in g),
        })
    show(agg, list(agg[0].keys()))

    # A single-seed random arm is NOT a chance estimate. RandomBudget shuffles
    # range(len(pool)) and the pool is the same size on every transcript, so one
    # seed reproduces the identical index pattern 21 times -- n=1 dressed as
    # n=21. Averaging over many seeds gives the actual chance level. This is a
    # broken control being repaired, not a method being tuned.
    print(f"\n=== random baseline over {N_SEEDS} seeds (the real chance level) ===")
    per_seed = []
    for seed in range(N_SEEDS):
        vals = []
        for path in paths:
            view, query, _ = load(path)
            pool = view[1:-1]
            src = {i for i, m in enumerate(pool) if m["content"] in SOURCE_TEXTS}
            idx = set(indices_of(view, RandomBudget(W, seed=seed).select(view, query=query)))
            vals.append(len(src & idx) / len(src))
        per_seed.append(statistics.mean(vals))
    print(f"  mean over seeds : {statistics.mean(per_seed):.4f}")
    print(f"  spread          : {min(per_seed):.4f} - {max(per_seed):.4f} "
          f"(sd {statistics.stdev(per_seed):.4f})")
    print(f"  single seed=1   : {[a for a in agg if a['selector'] == 'random'][0]['mean_retrieval_recall']}"
          f"   <- one draw, reported above, NOT a chance estimate")
    chance = statistics.mean(per_seed)

    print("\n=== source vs generated-message ranking (mean 1-based rank, lower = preferred) ===")
    rank_agg = []
    for name in ("bm25", "dense", "fusion"):
        g = [r for r in ranks if r["selector"] == name]
        src = statistics.mean(r["mean_rank_source"] for r in g)
        gen = statistics.mean(r["mean_rank_generated"] for r in g)
        rank_agg.append({
            "selector": name,
            "mean_rank_source": round(src, 2),
            "mean_rank_generated": round(gen, 2),
            "gap_src_minus_gen": round(src - gen, 2),
            "inverted": src > gen,
        })
    show(rank_agg, list(rank_agg[0].keys()))
    print("  inverted = the agents' own restatements outrank the authoritative "
          "originals they came from")

    print(f"\n=== retrieval recall vs chance ({chance:.4f}) ===")
    for a in agg:
        if a["selector"] == "oracle*":
            continue
        d = a["mean_retrieval_recall"] - chance
        print(f"  {a['selector']:<9} {a['mean_retrieval_recall']:.4f}  "
              f"{d:+.4f} vs chance  "
              f"{'BELOW chance' if d < 0 else 'above chance'}")

    print("\n=== pairwise selection overlap (mean Jaccard over transcripts) ===")
    names = [n for n, _ in selectors()]
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            vals = [jaccard(picks[p][a], picks[p][b]) for p in paths]
            pairs.append({
                "pair": f"{a} vs {b}",
                "mean_jaccard": round(statistics.mean(vals), 3),
                "identical_runs": sum(v == 1.0 for v in vals),
                "of": len(vals),
            })
    pairs.sort(key=lambda r: -r["mean_jaccard"])
    show(pairs, list(pairs[0].keys()))

    # One transcript in detail: what each scorer actually ranks for the
    # finalisation query, and whether the planted messages come near the top.
    sample = paths[0]
    view, query, seeded = load(sample)
    pool = view[1:-1]
    source_idx = {i for i, m in enumerate(pool) if m["content"] in SOURCE_TEXTS}
    print(f"\n=== rankings for the finalisation query on {sample} ===")
    print(f"    candidates: {len(pool)} (the current message is excluded)"
          f"  source messages at {sorted(source_idx)}")
    print(f"    query: {query[:70]!r}...\n")
    for name in ("bm25", "dense", "fusion"):
        pol = dict(selectors())[name]
        ranked = pol.ranking(pool, query)
        chosen = set(indices_of(view, pol.select(view, query=query)))
        line = "  ".join(
            f"{'*' if i in source_idx else ' '}{i}{'+' if i in chosen else ' '}"
            f":{s:+.2f}" for i, s in ranked
        )
        print(f"  {name:<7} {line}")
    print("\n  legend: *idx = planted source message, idx+ = selected under the budget")

    write_csv("results/selector_preflight_v2_corrected.csv", rows, list(rows[0].keys()))
    write_csv("results/selector_preflight_v2_corrected_overlap.csv", pairs,
              list(pairs[0].keys()))
    write_csv("results/selector_preflight_v2_corrected_ranks.csv", rank_agg,
              list(rank_agg[0].keys()))
    print("\nwrote results/selector_preflight_v2_corrected{,_overlap,_ranks}.csv")
    print("  (pre-correction artifacts preserved as *_v1_precorrection*.csv)")


if __name__ == "__main__":
    main()
