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

    def __init__(self):
        self.calls = []

    @property
    def label(self) -> str:
        return self.name

    def config(self) -> dict:
        return {}

    def select(self, messages):
        raise NotImplementedError

    def __call__(self, messages):
        out = self.select(messages)
        # Counts exclude the system prompt, which is never a candidate and is
        # never charged against the budget.
        available, kept = len(messages) - 1, len(out) - 1
        self.calls.append({
            "available": available,
            "kept": kept,
            "dropped": available - kept,
            "words_available": sum(words(m["content"]) for m in messages[1:]),
            "words_kept": sum(words(m["content"]) for m in out[1:]),
        })
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

    def select(self, messages):
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

    def select(self, messages):
        system, rest = _split_system(messages)
        # rest[-0:] is the WHOLE list, not the empty one. Guard it explicitly.
        kept = rest[-self.max_messages :] if self.max_messages > 0 else []
        return [system] + kept


# --- Word-budgeted policies (the research extension) ----------------------


class BudgetedPolicy(ContextPolicy):
    """Greedy-fill W words of dialogue history, then restore chronological order.

    Subclasses supply `priority(rest)`: candidate indices in preference order.

    Fill SKIPS a message that would overflow and keeps going, rather than
    stopping at the first non-fit. That is deliberate: stopping early would let
    one long message leave an arm systematically under budget, and unequal
    realised spend between arms is exactly the confound this design exists to
    avoid. Every arm fills as close to W as its priority order allows.
    """

    name = "budgeted"

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

    def priority(self, rest) -> list:
        raise NotImplementedError

    def select(self, messages):
        system, rest = _split_system(messages)
        chosen, used = [], 0
        for i in self.priority(rest):
            w = words(rest[i]["content"])
            if used + w <= self.max_words:
                chosen.append(i)
                used += w
        chosen.sort()  # chronological restoration
        return [system] + [rest[i] for i in chosen]


class RecencyBudget(BudgetedPolicy):
    """Most recent first."""

    name = "recency"

    def priority(self, rest):
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

    def priority(self, rest):
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

    def priority(self, rest):
        sources = [i for i, m in enumerate(rest) if m["content"] in self.source_texts]
        rest_by_recency = [
            i for i in range(len(rest) - 1, -1, -1) if i not in set(sources)
        ]
        return sources + rest_by_recency


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
