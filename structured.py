"""structured.py: ask a model for structured output, with one bounded retry.

There is exactly ONE retry loop in this project, and it lives here. Both the
final plan (finalise.py) and the judge (judge.py) go through it, so "the same
parse/retry discipline" is the same code rather than two copies that can drift.

The bound is the Budget's own turn cap: Budget(max_turns=2) is literally "one
attempt plus one correction", so the course's no-uncapped-loop rule covers this
loop by the same mechanism as everything else. `max_attempts` is a second,
independent ceiling so a caller who passes a looser Budget still cannot get an
unbounded retry loop.

Every call is recorded as an Entry carrying its measured cost, including
attempts whose output failed to validate. `len(result.attempts)` is exactly the
number of times the model was asked -- there are no invisible calls.
"""
from dataclasses import dataclass, field

from engine import Entry

#: One attempt, then at most one corrective retry. Never more.
MAX_ATTEMPTS = 2


def extract_json_object(text: str) -> str | None:
    """Return the first balanced {...} block in `text`, or None.

    Scans for a balanced brace pair while ignoring braces inside strings, so a
    reply wrapped in prose or a ```json fence still parses. Shared by every
    structured reader in the project.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def corrective_prompt(error: str, expected: str) -> str:
    """The follow-up sent when an attempt did not validate."""
    return (
        f"That could not be read: {error}.\n\n"
        "Reply with the JSON object only -- no explanation, no code fence, no "
        f"text before or after it. {expected}"
    )


@dataclass
class StructuredResult:
    """Everything one structured request cost, and what it produced."""

    attempts: list[Entry] = field(default_factory=list)
    attempt_errors: list[str | None] = field(default_factory=list)
    value: object = None
    stop_reason: str = ""

    @property
    def retries(self) -> int:
        return max(0, len(self.attempts) - 1)

    @property
    def accepted_text(self) -> str | None:
        if self.stop_reason != "accepted" or not self.attempts:
            return None
        return self.attempts[-1].content

    @property
    def last_text(self) -> str | None:
        return self.attempts[-1].content if self.attempts else None

    def as_dict(self) -> dict:
        return {
            "stop_reason": self.stop_reason,
            "retries": self.retries,
            "attempts": [
                {
                    "attempt": e.turn_index,
                    "speaker": e.speaker,
                    "content": e.content,
                    "parse_error": err,
                    "prompt_tokens": e.prompt_tokens,
                    "completion_tokens": e.completion_tokens,
                    "seconds": round(e.seconds, 3),
                }
                for e, err in zip(self.attempts, self.attempt_errors)
            ],
            "totals": {
                "attempts": len(self.attempts),
                "prompt_tokens": sum(e.prompt_tokens for e in self.attempts),
                "completion_tokens": sum(e.completion_tokens for e in self.attempts),
                "seconds": round(sum(e.seconds for e in self.attempts), 3),
            },
        }


def ask_structured(client, model, temperature, messages, validate, budget,
                   speaker, expected="", max_attempts=MAX_ATTEMPTS):
    """Ask for structured output. `validate(text) -> (value, error)`.

    On a failed validation the model is shown its own output and the error, and
    asked once more. The failed attempt is kept either way.
    """
    result = StructuredResult()

    while len(result.attempts) < max_attempts and not budget.exhausted():
        reply = client.chat(model, messages, temperature)
        result.attempts.append(
            Entry(
                speaker=speaker,
                content=reply.text,
                prompt_tokens=reply.prompt_tokens,
                completion_tokens=reply.completion_tokens,
                seconds=reply.seconds,
                turn_index=len(result.attempts),
            )
        )
        budget.record(turns=1, tokens=reply.tokens)

        value, error = validate(reply.text)
        result.attempt_errors.append(error)
        if error is None:
            result.value = value
            result.stop_reason = "accepted"
            return result

        messages = messages + [
            {"role": "assistant", "content": reply.text},
            {"role": "user", "content": corrective_prompt(error, expected)},
        ]

    result.stop_reason = (
        "parse_failed" if len(result.attempts) >= max_attempts else "budget_exhausted"
    )
    return result
