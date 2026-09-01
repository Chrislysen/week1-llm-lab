"""lineage_router.py: AnchorRoute -- corroboration-aware context selection.

EARNED, NOT ASSUMED. docs/agent-lineage-bench.md set five gates before any
router could be built. E5 is what clears the load-bearing one (gate 4: "lineage
must carry information a lineage-blind method cannot get"):

    adoption of a contradiction is governed by whether the original claim was
    CORROBORATED, not by how much text separates them
    d1 0.750 -> d2 0.417 (McNemar p = 0.0005)
    d1 -> d1_padded, length only:      p = 0.6250   (nothing)
    d1_padded -> d2, filler->corrob.:  p = 0.0020

That gives a routing rule a MECHANISM rather than a hope: under a fixed budget,
spend it on corroborated claims rather than on isolated ones.

IT READS NO HIDDEN STATE. The benchmark's lineage labels are scorer-only and a
real router cannot have them, so AnchorRoute INFERS corroboration from the text:
two messages corroborate each other when their embeddings are close. That is a
property of the candidate set, invisible to a relevance score against the query,
which is exactly why a lineage-blind selector cannot reproduce it.

    support(i) = |{ j != i : cos(v_i, v_j) >= tau }|
    score(i)   = alpha * z(relevance to query) + (1 - alpha) * z(support)

Relevance asks "does this match what I am being asked?". Support asks "has
anyone else independently said this?". The second is the one E5 says predicts
whether a later contradiction gets adopted.

Failure modes it can produce, stated up front so the evaluation can look for
them: a cluster of mutually-similar DISTRACTORS scores high support and can
crowd out an uncorroborated but critical source; and a corruption that echoes
its own source is textually similar to it, so support cannot tell a faithful
restatement from a contradicting one. Both are measured rather than assumed
away -- see e6_router.py.
"""
import numpy as np

from context import ScoringPolicy, words
from retrieval import ALPHA, dense_scores, zscore

#: Cosine at or above which two messages count as saying the same thing.
#: Fixed a priori from the same reasoning as OpSem's alpha: chosen before any
#: scored run and not tuned on outcomes.
TAU = 0.72


def support_scores(docs, tau=TAU, encoder=None):
    """How many OTHER candidates each candidate is corroborated by."""
    from retrieval import ENCODER
    enc = encoder or ENCODER
    if len(docs) < 2:
        return np.zeros(len(docs), dtype=float)
    v = enc.encode(list(docs))          # rows are unit-normalised
    sim = v @ v.T
    np.fill_diagonal(sim, -1.0)         # a message does not corroborate itself
    return (sim >= tau).sum(axis=1).astype(float)


class AnchorRouteBudget(ScoringPolicy):
    """Relevance fused with corroboration support, under the same word budget."""

    name = "anchorroute"

    def __init__(self, max_words, alpha=ALPHA, tau=TAU, encoder=None):
        super().__init__(max_words)
        self.alpha = alpha
        self.tau = tau
        self.encoder = encoder

    @property
    def label(self):
        return f"anchorroute-{self.max_words}-a{self.alpha}-t{self.tau}"

    def config(self):
        return {"max_words": self.max_words, "alpha": self.alpha, "tau": self.tau}

    def scores(self, docs, query):
        rel = dense_scores(docs, query, encoder=self.encoder)
        sup = support_scores(docs, self.tau, self.encoder)
        return self.alpha * zscore(rel) + (1.0 - self.alpha) * zscore(sup)


class SupportOnlyBudget(ScoringPolicy):
    """Corroboration support alone, no relevance term.

    The ablation that says whether the fusion is doing anything: if this matches
    AnchorRoute, the relevance half is decoration.
    """

    name = "supportonly"

    def __init__(self, max_words, tau=TAU, encoder=None):
        super().__init__(max_words)
        self.tau = tau
        self.encoder = encoder

    @property
    def label(self):
        return f"supportonly-{self.max_words}-t{self.tau}"

    def config(self):
        return {"max_words": self.max_words, "tau": self.tau}

    def scores(self, docs, query):
        return support_scores(docs, self.tau, self.encoder)
