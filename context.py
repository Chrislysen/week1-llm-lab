"""context.py: context-selection policies for the engine's manage_context hook.

A policy is a callable `messages -> messages`. It runs AFTER view_for, so it
receives an already role-mapped list: the system prompt at index 0, then the
dialogue in chronological order with roles relative to the speaking agent.

Two invariants every policy must hold:

  * the system prompt is always kept, and stays at index 0;
  * the messages that survive stay in chronological order.

Only two policies exist so far, and only one of them is experimental:

  FullHistory    diagnostic ceiling. Keeps everything. Not one of the three
                 compulsory configurations.
  RecencyWindow  the experimental policy. Keeps the most recent N dialogue
                 messages. The three compulsory configurations are N = 4, 8, 12
                 and differ in nothing else.

Policies record what they did on every call, so the saved run can answer "what
was actually dropped" rather than only "what was configured". The realised
prompt-token count is recorded separately, by the engine, on each Entry --
Ollama reports it exactly, so cost is measured rather than assumed.
"""
import random as _random

SYSTEM = "system"


def words(text: str) -> int:
    """The budget unit. Whitespace-delimited words.

    Words, not tokens, because there is no tokenizer in this project and adding
    one buys no fairness -- what matters is that the SAME proxy is applied to
    every arm. Realised prompt tokens are reported separately, from Ollama's
    exact count, as the parity audit.
    """
    return len(text.split())


# --- Query definition. FROZEN before any result was seen. -----------------
#
# Built only from what the agent can already see. It never contains constraint
# ids, evaluator state, or any part of the hidden key. Nothing in the pilot
# consumes these -- recency, random and oracle do not score against a query --
# but they are committed now so the definition cannot be chosen after the fact.


def query_for_turn(messages) -> str:
    """Ordinary turn: the latest incoming message.

    `messages` is a rendered view (system first). Its last entry is the other
    agent's most recent message, because the current speaker has not spoken yet.
    """
    return messages[-1]["content"] if len(messages) > 1 else ""


def query_for_finalisation(messages, instruction: str) -> str:
    """Finalisation: the final-plan instruction plus the latest dialogue message."""
    latest = messages[-1]["content"] if len(messages) > 1 else ""
    return f"{instruction}\n\n{latest}" if latest else instruction


class ContextPolicy:
    """Base class. Subclasses implement `select`; `__call__` adds the logging."""

    name = "policy"
    #: True when the policy holds the latest message out as mandatory current
    #: context, outside the budget and out of the candidate pool.
    reserves_current = False

    def __init__(self):
        self.calls = []
        self._last = None

    @property
    def label(self) -> str:
        return self.name

    def config(self) -> dict:
        return {}

    def select(self, messages, query=None):
        raise NotImplementedError

    def __call__(self, messages, query=None):
        """`query` is supplied by the caller only at finalisation.

        On an ordinary turn the engine calls this with one argument and the
        policy derives the query itself via `query_for_turn`. At finalisation
        the instruction is not part of the message list yet, so `finalise`
        passes the frozen `query_for_finalisation` value in explicitly.
        """
        out = self.select(messages, query=query)
        # Counts exclude the system prompt, which is never a candidate and is
        # never charged against the budget.
        available, kept = len(messages) - 1, len(out) - 1
        record = {
            "available": available,
            "kept": kept,
            "dropped": available - kept,
            "words_available": sum(words(m["content"]) for m in messages[1:]),
            "words_kept": sum(words(m["content"]) for m in out[1:]),
        }
        # Budgeted policies additionally split what was BUDGETED (retrieved
        # history) from what was MANDATORY (current context), so the parity
        # audit compares like with like.
        if self.reserves_current and self._last is not None:
            record.update(self._last)
        self.calls.append(record)
        return out

    def as_dict(self) -> dict:
        return {
            "policy": self.name,
            "label": self.label,
            "config": self.config(),
            "calls": self.calls,
            "totals": {
                "calls": len(self.calls),
                "messages_available": sum(c["available"] for c in self.calls),
                "messages_kept": sum(c["kept"] for c in self.calls),
                "messages_dropped": sum(c["dropped"] for c in self.calls),
            },
        }


def _split_system(messages):
    if not messages or messages[0].get("role") != SYSTEM:
        raise ValueError("manage_context expected a system message at index 0")
    return messages[0], list(messages[1:])


class FullHistory(ContextPolicy):
    """Keep everything. The diagnostic ceiling, not an experimental arm."""

    name = "full"

    def select(self, messages, query=None):
        _split_system(messages)
        return list(messages)


class RecencyWindow(ContextPolicy):
    """Keep the system prompt plus the most recent `max_messages` messages."""

    name = "recency"

    def __init__(self, max_messages: int):
        super().__init__()
        if max_messages < 0:
            raise ValueError("max_messages must be >= 0")
        self.max_messages = max_messages

    @property
    def label(self) -> str:
        return f"recency-{self.max_messages}"

    def config(self) -> dict:
        return {"max_messages": self.max_messages}

    def select(self, messages, query=None):
        system, rest = _split_system(messages)
        # rest[-0:] is the WHOLE list, not the empty one. Guard it explicitly.
        kept = rest[-self.max_messages :] if self.max_messages > 0 else []
        return [system] + kept


# --- Word-budgeted policies (the research extension) ----------------------


class BudgetedPolicy(ContextPolicy):
    """Greedy-fill W words of RETRIEVABLE HISTORY, then restore chronological order.

    Subclasses supply `priority(rest, query)`: candidate indices in preference
    order.

    CURRENT-MESSAGE SEPARATION (protocol amendment, 2026-08-31)
    ----------------------------------------------------------
    The most recent dialogue message is CURRENT CONTEXT, not retrievable
    history. It is always present, sits outside the word budget, and is
    excluded from the candidate pool -- identically for every policy, including
    recency, random and the oracle.

    Why: the frozen finalisation query is FINAL_PLAN_INSTRUCTION + the latest
    dialogue message, and that message was also a retrieval candidate, so it
    matched itself. The offline selector preflight measured BM25 scoring it
    +45.38 against a next-best +12.71 -- an order of magnitude, guaranteeing its
    selection for every scoring arm and burning budget on a message recency
    would have taken anyway. A candidate that is part of its own query is a
    measurement artefact.

    This is a PROTOCOL CORRECTION, not outcome tuning: it was found by an
    offline selector-only preflight, before any scored selector run, and it is
    applied uniformly to every arm rather than to the ones it happens to help.
    No scoring function, alpha, prompt or budget was touched.

    NOTE: the completed stage-1 pilot (`transcripts/pilot/`, `1def040`) ran
    under the PRE-amendment pool. Its numbers are not directly comparable to
    post-amendment selector runs and must not be pooled with them.

    Fill SKIPS a message that would overflow and keeps going, rather than
    stopping at the first non-fit. That is deliberate: stopping early would let
    one long message leave an arm systematically under budget, and unequal
    realised spend between arms is exactly the confound this design exists to
    avoid. Every arm fills as close to W as its priority order allows.
    """

    name = "budgeted"
    reserves_current = True

    def __init__(self, max_words: int):
        super().__init__()
        if max_words < 0:
            raise ValueError("max_words must be >= 0")
        self.max_words = max_words

    @property
    def label(self) -> str:
        return f"{self.name}-{self.max_words}"

    def config(self) -> dict:
        return {"max_words": self.max_words}

    def priority(self, rest, query) -> list:
        raise NotImplementedError

    def select(self, messages, query=None):
        system, rest = _split_system(messages)
        # Ordinary turn: derive the frozen query ourselves. Finalisation: the
        # caller passes it, because the instruction is not in `messages` yet.
        if query is None:
            query = query_for_turn(messages)

        if not rest:
            self._last = {"n_candidates": 0, "n_selected": 0,
                          "words_history": 0, "words_current": 0}
            return [system]

        # Current-message separation: the latest message is mandatory current
        # context, outside the budget and out of the candidate pool.
        current, pool = rest[-1], rest[:-1]

        chosen, used = [], 0
        for i in self.priority(pool, query):
            w = words(pool[i]["content"])
            if used + w <= self.max_words:
                chosen.append(i)
                used += w
        chosen.sort()  # chronological restoration

        self._last = {
            "n_candidates": len(pool),
            "n_selected": len(chosen),
            "words_history": used,
            "words_current": words(current["content"]),
            # Which candidates were actually chosen, by position in the pool.
            # Recorded rather than reconstructed: a replay would depend on the
            # policy still behaving identically, which is the thing under study.
            "selected_ids": list(chosen),
        }
        return [system] + [pool[i] for i in chosen] + [current]


class RecencyBudget(BudgetedPolicy):
    """Most recent first."""

    name = "recency"

    def priority(self, rest, query):
        return list(range(len(rest) - 1, -1, -1))


class RandomBudget(BudgetedPolicy):
    """Uniformly random order. The chance bar any retriever must clear.

    Seeded, so a run is reproducible from its saved config.
    """

    name = "random"

    def __init__(self, max_words: int, seed: int = 0):
        super().__init__(max_words)
        self.seed = seed

    @property
    def label(self) -> str:
        return f"random-{self.max_words}-s{self.seed}"

    def config(self) -> dict:
        return {"max_words": self.max_words, "seed": self.seed}

    def priority(self, rest, query):
        order = list(range(len(rest)))
        _random.Random(self.seed).shuffle(order)
        return order


class OracleBudget(BudgetedPolicy):
    """Constraint-bearing source messages first, then the most recent.

    Budget-matched: it competes under the same W as every other arm.

    It uses hidden evaluator knowledge to CHOOSE -- it is told which message
    texts carry planted constraints -- but it can only ever return messages that
    are already in the dialogue. It never injects, rewrites or summarises
    anything. `select` filters its input; a test asserts the output is a subset.

    This is the upper bound on what any retriever could achieve at this budget.
    If it does not beat recency, no retriever will.
    """

    name = "oracle"

    def __init__(self, max_words: int, source_texts):
        super().__init__(max_words)
        self.source_texts = frozenset(source_texts)

    def config(self) -> dict:
        return {"max_words": self.max_words, "n_source_texts": len(self.source_texts)}

    def priority(self, rest, query):
        sources = [i for i, m in enumerate(rest) if m["content"] in self.source_texts]
        rest_by_recency = [
            i for i in range(len(rest) - 1, -1, -1) if i not in set(sources)
        ]
        return sources + rest_by_recency


# --- Scoring policies (the four selectors) --------------------------------


class ScoringPolicy(BudgetedPolicy):
    """Rank candidates by a relevance score against the frozen query.

    Subclasses implement `scores(docs, query) -> array`. None of them receives
    constraints, evaluator state, or which messages are planted -- they see
    message text and a query string, and nothing else. Only `OracleBudget` is
    given the hidden labels, and it is a diagnostic, not a selector.

    Deterministic tie-breaking: descending score, then MORE RECENT first. Ties
    are common on a 16-message pool -- BM25 gives exactly 0.0 to every message
    sharing no query term -- so an unstated rule would silently become "whatever
    order numpy happened to produce".
    """

    def scores(self, docs, query):
        raise NotImplementedError

    def priority(self, rest, query):
        docs = [m["content"] for m in rest]
        s = self.scores(docs, query)
        return sorted(range(len(rest)), key=lambda i: (-float(s[i]), -i))

    def ranking(self, rest, query):
        """(index, score) in priority order. For the offline preflight only."""
        docs = [m["content"] for m in rest]
        s = self.scores(docs, query)
        return [(i, float(s[i])) for i in self.priority(rest, query)]


class BM25Budget(ScoringPolicy):
    """Message-level BM25. Lexical only."""

    name = "bm25"

    def scores(self, docs, query):
        from retrieval import bm25_scores

        return bm25_scores(docs, query)


class DenseBudget(ScoringPolicy):
    """Message-level dense cosine, all-MiniLM-L6-v2. No pooling, no late interaction."""

    name = "dense"

    def __init__(self, max_words: int, encoder=None):
        super().__init__(max_words)
        self.encoder = encoder

    def scores(self, docs, query):
        from retrieval import dense_scores

        return dense_scores(docs, query, encoder=self.encoder)


class FusionBudget(ScoringPolicy):
    """alpha * z(bm25) + (1 - alpha) * z(dense), alpha fixed a priori at 0.40.

    From OpSem's measured global optimum. Not tuned here, and not to be.
    """

    name = "fusion"

    def __init__(self, max_words: int, alpha=None, encoder=None):
        from retrieval import ALPHA

        super().__init__(max_words)
        self.alpha = ALPHA if alpha is None else alpha
        self.encoder = encoder

    @property
    def label(self) -> str:
        return f"fusion-{self.max_words}-a{self.alpha}"

    def config(self) -> dict:
        return {"max_words": self.max_words, "alpha": self.alpha}

    def scores(self, docs, query):
        from retrieval import bm25_scores, dense_scores, fuse

        return fuse(
            bm25_scores(docs, query),
            dense_scores(docs, query, encoder=self.encoder),
            alpha=self.alpha,
        )


def make_policy(spec):
    """Build a policy from a config value.

    None/'full' -> FullHistory, int -> RecencyWindow(n), or pass a policy
    instance straight through (used by the research pilot).
    """
    if isinstance(spec, ContextPolicy):
        return spec
    if spec is None or spec == "full":
        return FullHistory()
    return RecencyWindow(int(spec))


def _fingerprint(messages):
    return tuple((m["role"], m["content"]) for m in messages)


def preflight(messages, policies) -> dict:
    """Would these policies actually see different things on this transcript?

    If every policy selects the identical context, the run cannot distinguish
    them and measures nothing -- the comparison is INERT. This is cheap to check
    and expensive to discover afterwards, so it is checked before spending runs.

    Uses `select`, not `__call__`, so a preflight never pollutes a policy's log.
    """
    prints = {p.label: _fingerprint(p.select(list(messages))) for p in policies}
    kept = {p.label: len(p.select(list(messages))) - 1 for p in policies}

    labels = list(prints)
    identical = [
        (a, b)
        for i, a in enumerate(labels)
        for b in labels[i + 1 :]
        if prints[a] == prints[b]
    ]
    return {
        "available_messages": len(messages) - 1,
        "kept": kept,
        "identical_pairs": identical,
        "distinct_contexts": len(set(prints.values())),
        "inert": len(set(prints.values())) == 1,
    }
