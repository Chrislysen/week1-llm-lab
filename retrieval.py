"""retrieval.py: scoring primitives. Adapted from prior work -- see docs/PRIOR_WORK.md.

Three functions, all operating on INDIVIDUAL MESSAGES:

    bm25_scores   lexical, self-contained, numpy
    dense_scores  plain cosine over one vector per message
    fuse          alpha * z(bm25) + (1 - alpha) * z(dense), alpha fixed

ADAPTED FROM OpSem (github.com/Chrislysen/opsem, public, MIT, predates this
course): the tokenizer discipline and BM25 from `lme_maxsim.py`; `_z` and the
weighted linear fusion from `tune13_interaction.py`; ALPHA = 0.40 from the
global optimum measured in `analysis_deep.py`.

NOT taken from OpSem, deliberately: the session-level retrieval unit, and
turn-level late interaction / max-sim pooling. OpSem's max-sim runs over 16-25+
turn vectors inside a session and its released bucket data contains zero
evaluated containers under 8 turns; the measured benefit grows monotonically
with container size because it is a dilution effect. At the message level there
is nothing to pool over, so the mechanism has a size precondition this setting
does not meet. Dense scoring here is plain cosine, one vector per message.

Nothing in this file has any access to constraints, evaluator state, or which
messages are planted. It sees message text and a query string, and that is all.
"""
import math
import re
from collections import Counter

import numpy as np

#: Fixed a priori from OpSem's measured optimum (broad plateau 0.30-0.45).
#: NOT tuned on this project's scenarios, and not to be.
ALPHA = 0.40

#: OpSem's tokenizer discipline: lowercase, keep alphanumeric-initial tokens of
#: 2-31 chars, drop a small stopword list and anything under 3 characters.
_TOKEN = re.compile(r"[a-z0-9][a-z0-9\-_']{1,30}")

_STOPWORDS = frozenset("""
a an and are as at be been but by can could did do does for from had has have
he her his how i if in into is it its me my no nor not of on or our out own she
so than that the their them then there these they this those to too was we were
what when where which who will with would you your
""".split())


def tokenize(text: str) -> list:
    return [
        t for t in _TOKEN.findall(text.lower())
        if len(t) >= 3 and t not in _STOPWORDS
    ]


class BM25:
    """Okapi BM25 over a fixed set of documents. Adapted from opsem/lme_maxsim.py."""

    def __init__(self, docs, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(tokenize(d)) for d in docs]
        self.dl = np.array([sum(c.values()) for c in self.tf], dtype=float)
        self.avgdl = float(self.dl.mean()) if len(self.dl) else 0.0
        n = len(docs)
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        # Standard BM25 idf with the +1 that keeps it non-negative.
        self.idf = {
            t: math.log(1.0 + (n - k + 0.5) / (k + 0.5)) for t, k in df.items()
        }

    def score(self, query: str) -> np.ndarray:
        out = np.zeros(len(self.tf), dtype=float)
        if self.avgdl == 0.0:
            return out
        for term in tokenize(query):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, c in enumerate(self.tf):
                f = c.get(term, 0)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl)
                out[i] += idf * f * (self.k1 + 1) / denom
        return out


def bm25_scores(docs, query: str) -> np.ndarray:
    return BM25(docs).score(query)


def zscore(v: np.ndarray) -> np.ndarray:
    """Per-query z-normalisation within the candidate set. From opsem/tune13_interaction._z.

    Guarded for a degenerate spread, where every candidate scored the same and
    the normalised vector must be all zeros rather than NaN or a divide error.
    """
    v = np.asarray(v, dtype=float)
    sd = v.std()
    if sd < 1e-9:
        return np.zeros_like(v)
    return (v - v.mean()) / sd


def fuse(bm: np.ndarray, dense: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """alpha * z(bm25) + (1 - alpha) * z(dense). From opsem/tune13_interaction.py."""
    return alpha * zscore(bm) + (1.0 - alpha) * zscore(dense)


class DenseEncoder:
    """all-MiniLM-L6-v2 sentence embeddings, cached by exact text.

    CPU, deterministic, normalised so a dot product IS the cosine. Loaded lazily
    so that importing this module -- which the offline preflight and every other
    test do -- never pays for a model load it does not use.
    """

    MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model_name: str = MODEL):
        self.model_name = model_name
        self._model = None
        self._cache = {}

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    def encode(self, texts) -> np.ndarray:
        missing = [t for t in dict.fromkeys(texts) if t not in self._cache]
        if missing:
            vecs = self._load().encode(
                missing, normalize_embeddings=True, show_progress_bar=False
            )
            for t, v in zip(missing, vecs):
                self._cache[t] = np.asarray(v, dtype=float)
        return np.stack([self._cache[t] for t in texts])


#: One process-wide encoder, so the model loads once and vectors are reused
#: across the ~11 selection calls in a run.
ENCODER = DenseEncoder()


def dense_scores(docs, query: str, encoder: DenseEncoder = None) -> np.ndarray:
    """Plain cosine between the query and each message. No pooling, no late interaction."""
    enc = encoder or ENCODER
    if not docs:
        return np.zeros(0, dtype=float)
    doc_vecs = enc.encode(list(docs))
    q = enc.encode([query])[0]
    return doc_vecs @ q
