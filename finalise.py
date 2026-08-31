"""finalise.py: ask the Operations Lead for the final plan, with one retry.

Why this is not part of DialogueEngine.run(): finalisation is not a dialogue
turn. It is a different question asked of one agent after the conversation has
ended, it has its own stopping rule, and its cost should not be pooled with the
dialogue's. The engine stays a dialogue engine.

The retry loop itself lives in structured.py and is shared with the judge.
"""
from dataclasses import dataclass

from context import query_for_finalisation
from engine import view_for
from evaluate import Evaluation, evaluate, parse_plan
from scenario import FINAL_PLAN_INSTRUCTION
from structured import MAX_ATTEMPTS, StructuredResult, ask_structured

EXPECTED = (
    'It must have exactly two keys: "actions", a list of action identifier '
    'strings, and "ready", true or false.'
)


@dataclass
class Finalisation:
    """The outcome of asking for the final plan, and everything it cost."""

    result: StructuredResult
    evaluation: Evaluation

    @property
    def attempts(self):
        return self.result.attempts

    @property
    def attempt_errors(self):
        return self.result.attempt_errors

    @property
    def stop_reason(self) -> str:
        return self.result.stop_reason

    @property
    def retries(self) -> int:
        return self.result.retries

    @property
    def plan_text(self) -> str | None:
        return self.result.accepted_text

    def as_dict(self) -> dict:
        return {**self.result.as_dict(), "evaluation": self.evaluation.as_dict()}


def finalise(agent, transcript, client, budget, scenario,
             instruction=FINAL_PLAN_INSTRUCTION, manage_context=None):
    """Ask `agent` for the final plan. Returns a Finalisation.

    `manage_context` is applied to the DIALOGUE ONLY. The instruction, and the
    corrective exchange on a retry, sit outside the window -- they are the
    current question, not history, and have the same always-present status as
    the system prompt. Windowing them away would make the retry unanswerable.

    This matters: the final plan is the thing being scored, so if finalisation
    ignored the context policy the whole comparison would be measuring dialogue
    quality while the graded decision was made with full history.
    """
    select = manage_context or (lambda messages, query=None: messages)
    view = view_for(agent, transcript)
    # The instruction is not in `view` yet, so a scoring policy cannot derive
    # the finalisation query itself. Pass the frozen definition in explicitly.
    messages = select(view, query=query_for_finalisation(view, instruction)) + [
        {"role": "user", "content": instruction}
    ]

    result = ask_structured(
        client=client,
        model=agent.model,
        temperature=agent.temperature,
        messages=messages,
        validate=parse_plan,
        budget=budget,
        speaker=agent.name,
        expected=EXPECTED,
    )

    # Score whatever was actually produced. With no attempt at all there is
    # nothing to score, so say that rather than inventing a verdict.
    if result.last_text is None:
        evaluation = Evaluation(
            parsed=False, parse_error="no attempt made: budget exhausted"
        )
    else:
        evaluation = evaluate(result.last_text, scenario)

    return Finalisation(result=result, evaluation=evaluation)
