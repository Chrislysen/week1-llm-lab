"""Self-check for the retrieval primitives and the three scoring selectors.

Run:  python test_retrieval.py

The dense encoder loads a real model, so this suite is slower than the others.
"""
import numpy as np

from context import (BM25Budget, DenseBudget, FusionBudget, OracleBudget,
                     RandomBudget, RecencyBudget, words)
from retrieval import ALPHA, bm25_scores, dense_scores, fuse, tokenize, zscore

SYS = {"role": "system", "content": "You are the Operations Lead."}

DOCS = [
    "We must run the backup before restarting the database.",          # 0
    "The weather today is unusually mild for the season.",             # 1
    "Failover the API to the standby node first.",                     # 2
    "I agree with that, it sounds reasonable to me.",                   # 3
    "Do not restore traffic until the database is serving again.",     # 4
]

# -- Tokenizer -----------------------------------------------------------

t = tokenize("We MUST run the Backup before re-starting the DB, no?")
assert "the" not in t and "we" not in t, t          # stopwords dropped
assert "db" not in t, t                              # under 3 chars dropped
assert "backup" in t and "must" in t, t
assert "re-starting" in t, t                         # hyphen kept inside a token
assert all(x == x.lower() for x in t)
assert tokenize("") == []

print("tokenizer:           OK")

# -- BM25 ----------------------------------------------------------------

s = bm25_scores(DOCS, "backup before restarting the database")
assert len(s) == len(DOCS)
assert s.argmax() == 0, s
assert s[1] == 0.0, "a document sharing no query term must score exactly 0"
assert (s >= 0).all(), "idf is the +1 variant, so scores are non-negative"

# A query with no shared vocabulary scores everything zero.
assert (bm25_scores(DOCS, "zzzz qqqq") == 0).all()
assert len(bm25_scores([], "anything")) == 0

# Deterministic.
assert (bm25_scores(DOCS, "failover standby")
        == bm25_scores(DOCS, "failover standby")).all()
assert bm25_scores(DOCS, "failover standby").argmax() == 2

print("bm25:                OK")

# -- z-normalisation -----------------------------------------------------

z = zscore(np.array([1.0, 2.0, 3.0]))
assert abs(z.mean()) < 1e-9 and abs(z.std() - 1.0) < 1e-9
# Degenerate spread must give zeros, not NaN. Very common here: BM25 returns an
# all-zero vector whenever the query shares no term with any message.
assert (zscore(np.zeros(5)) == 0).all()
assert not np.isnan(zscore(np.full(4, 7.0))).any()

# Fusion with a dead component reduces to the live one, up to scale.
bm = np.array([3.0, 1.0, 2.0])
dead = np.zeros(3)
assert fuse(bm, dead).argmax() == bm.argmax()
assert fuse(dead, bm).argmax() == bm.argmax()
assert ALPHA == 0.40, "alpha is fixed a priori from OpSem and must not drift"

print("z-norm + fusion:     OK")

# -- Dense (loads the model) ---------------------------------------------

d = dense_scores(DOCS, "when can we restart the database safely?")
assert len(d) == len(DOCS)
assert (np.abs(d) <= 1.0 + 1e-6).all(), "normalised embeddings -> cosine in [-1, 1]"
assert d.argmax() in (0, 4), f"expected a database-ordering message, got {d.argmax()}"
# The off-topic message should not win.
assert d[1] < d[0], "weather should score below the backup/restart message"
# Deterministic and cached.
assert (dense_scores(DOCS, "restart the database")
        == dense_scores(DOCS, "restart the database")).all()
assert len(dense_scores([], "q")) == 0

print("dense cosine:        OK")

# -- The selectors -------------------------------------------------------

POOL = [SYS] + [{"role": "user", "content": d} for d in DOCS]
QUERY = "when can we restart the database, and what must happen first?"


def retrieved(policy, query=QUERY):
    """The RETRIEVED HISTORY only -- excludes the mandatory current message."""
    return [m["content"] for m in policy.select(POOL, query=query)[1:-1]]


BUDGET = 20  # words of history; DOCS are 9-10 words each, so ~2 fit

for pol in (BM25Budget(BUDGET), DenseBudget(BUDGET), FusionBudget(BUDGET),
            RecencyBudget(BUDGET), RandomBudget(BUDGET, seed=3)):
    sel = pol.select(POOL, query=QUERY)
    assert sel[0] == SYS, f"{pol.label} dropped the system prompt"
    assert all(m in POOL for m in sel[1:]), f"{pol.label} injected content"
    # Current-message separation: DOCS[4] is mandatory current context, always
    # last, outside the budget, and never a retrieval candidate.
    assert sel[-1]["content"] == DOCS[4], f"{pol.label} lost the current message"
    history = sel[1:-1]
    assert DOCS[4] not in [m["content"] for m in history], \
        f"{pol.label} retrieved the current message as history"
    assert sum(words(m["content"]) for m in history) <= BUDGET, f"{pol.label} overspent"
    idx = [POOL.index(m) for m in sel[1:]]
    assert idx == sorted(idx), f"{pol.label} broke chronological order"

# The scoring selectors should prefer the on-topic messages; recency cannot.
assert DOCS[1] not in retrieved(BM25Budget(BUDGET)), "BM25 kept the weather message"
assert DOCS[1] not in retrieved(FusionBudget(BUDGET)), "fusion kept the weather message"
# Recency reaches back from the newest CANDIDATE, which is the filler at DOCS[3].
assert DOCS[3] in retrieved(RecencyBudget(BUDGET))

# Selectors genuinely differ from recency on this pool.
assert retrieved(BM25Budget(BUDGET)) != retrieved(RecencyBudget(BUDGET))

print("selectors:           OK")

# -- Deterministic tie-breaking ------------------------------------------

# A query sharing no vocabulary makes every BM25 score exactly 0.0. The
# documented rule is: descending score, then MORE RECENT first.
flat = BM25Budget(1000)
order = [i for i, _ in flat.ranking(POOL[1:], "zzzz qqqq")]
assert order == [4, 3, 2, 1, 0], f"tie-break must fall back to recency, got {order}"
# And it is stable across repeated calls.
assert order == [i for i, _ in flat.ranking(POOL[1:], "zzzz qqqq")]

print("tie-breaking:        OK")

# -- No selector may see evaluator or constraint information -------------

# Constructed with a budget and nothing else. If a selector ever needed the
# scenario, it could not be built by this line.
for pol in (BM25Budget(250), DenseBudget(250), FusionBudget(250),
            RecencyBudget(250), RandomBudget(250, seed=0)):
    cfg = pol.config()
    assert "source" not in str(cfg).lower(), cfg
    assert not hasattr(pol, "source_texts"), f"{pol.label} holds source labels"

# The oracle is the ONE exception, and it is a diagnostic, not a selector.
oracle = OracleBudget(250, [DOCS[0]])
assert hasattr(oracle, "source_texts")
assert oracle.config()["n_source_texts"] == 1

print("no leakage:          OK")

# -- alpha is fixed, not tuned -------------------------------------------

assert FusionBudget(250).alpha == 0.40
assert FusionBudget(250).config()["alpha"] == 0.40
assert "a0.4" in FusionBudget(250).label, FusionBudget(250).label

print("alpha fixed:         OK")
print("\nAll checks passed.")
