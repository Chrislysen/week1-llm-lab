"""finalise.py: ask the Operations Lead for the final plan, with one retry.

Why this is not part of DialogueEngine.run(): finalisation is not a dialogue
turn. It is a different question asked of one agent after the conversation has
ended, it has its own stopping rule, and its cost should not be pooled with the
dialogue's. The engine stays a dialogue engine.

The retry bound is the Budget's own turn cap, not a hand-rolled counter. A
Budget(max_turns=2) is literally "one attempt plus one correction", so the
course's one hard rule -- no model-calling loop without a Budget -- covers this
loop too. MAX_ATTEMPTS is a second, independent ceiling so a caller who passes a
looser Budget still cannot get an unbounded retry loop.

Every model call made here is recorded as an Entry with its measured cost,
including attempts whose output failed to parse. There are no invisible calls:
`len(result.attempts)` is exactly the number of times the model was asked.
"""
from dataclasses import dataclass, field

from engine import Entry, view_for
from evaluate import Evaluation, evaluate
from scenario import FINAL_PLAN_INSTRUCTION

#: One attempt, then at most one corrective retry. Never more.
MAX_ATTEMPTS = 2


def corrective_prompt(error: str) -> str:
    """The follow-up sent when the first attempt did not parse."""
    return (
        f"That could not be read as a valid plan: {error}.\n\n"
        "Reply with the JSON object only -- no explanation, no code fence, no "
        'text before or after it. It must have exactly two keys: "actions", a '
        'list of action identifier strings, and "ready", true or false.'
    )


@dataclass
class Finalisation:
    """The outcome of asking for the final plan, and everything it cost."""

    attempts: list[Entry] = field(default_factory=list)
    attempt_errors: list[str | None] = field(default_factory=list)
    evaluation: Evaluation | None = None
    stop_reason: str = ""

    @property
    def retries(self) -> int:
        return max(0, len(self.attempts) - 1)

    @property
    def plan_text(self) -> str | None:
        """The raw text of the accepted attempt, or None if none was accepted."""
        if self.stop_reason != "accepted" or not self.attempts:
            return None
        return self.attempts[-1].content

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
            "evaluation": self.evaluation.as_dict() if self.evaluation else None,
        }


def finalise(agent, transcript, client, budget, scenario,
             instruction=FINAL_PLAN_INSTRUCTION):
    """Ask `agent` for the final plan. Returns a Finalisation.

    The agent sees the dialogue from its own point of view (same role mapping as
    every other turn), then the instruction. If the reply does not parse, it is
    shown its own output and the parse error, and asked once more.
    """
    result = Finalisation()
    messages = view_for(agent, transcript) + [
        {"role": "user", "content": instruction}
    ]
    last_evaluation = None

    while len(result.attempts) < MAX_ATTEMPTS and not budget.exhausted():
        reply = client.chat(agent.model, messages, agent.temperature)
        result.attempts.append(
            Entry(
                speaker=agent.name,
                content=reply.text,
                prompt_tokens=reply.prompt_tokens,
                completion_tokens=reply.completion_tokens,
                seconds=reply.seconds,
                turn_index=len(result.attempts),
            )
        )
        budget.record(turns=1, tokens=reply.tokens)

        evaluation = evaluate(reply.text, scenario)
        result.attempt_errors.append(evaluation.parse_error)
        last_evaluation = evaluation

        if evaluation.parsed:
            result.evaluation = evaluation
            result.stop_reason = "accepted"
            return result

        # Show the model its own malformed output and ask once more. The bad
        # attempt stays in result.attempts either way.
        messages = messages + [
            {"role": "assistant", "content": reply.text},
            {"role": "user", "content": corrective_prompt(evaluation.parse_error)},
        ]

    # Nothing was accepted. Say precisely why.
    if not result.attempts:
        result.stop_reason = "budget_exhausted"
        result.evaluation = Evaluation(
            parsed=False, parse_error="no attempt made: budget exhausted"
        )
    elif len(result.attempts) >= MAX_ATTEMPTS:
        result.stop_reason = "parse_failed"
        result.evaluation = last_evaluation
    else:
        result.stop_reason = "budget_exhausted"
        result.evaluation = last_evaluation
    return result
