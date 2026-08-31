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
SYSTEM = "system"


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
        # Counts exclude the system prompt, which is never a candidate.
        available, kept = len(messages) - 1, len(out) - 1
        self.calls.append(
            {"available": available, "kept": kept, "dropped": available - kept}
        )
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


def make_policy(spec):
    """Build a policy from a config value: None/'full' -> FullHistory, int -> window."""
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
