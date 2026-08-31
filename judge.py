"""judge.py: the LLM judge. SECONDARY evidence only.

The deterministic evaluator in evaluate.py decides whether the task succeeded.
This does not. A model can be argued with; `index(a) < index(b)` cannot. The
judge exists because the compulsory requires one, and because a qualitative
read of the conversation is genuinely informative alongside the hard metric --
but if it were deleted, the experiment would still stand on constraint recall.

It is a separate model call. It is not one of the two agents, it takes no part
in the dialogue, and it never sees which context policy produced the run --
there is nothing in its prompt naming the condition, so single-run judging is
blind by construction.

Same bounded parse/retry discipline as the final plan: shared code in
structured.py, one attempt plus at most one correction, every call logged with
its measured cost.
"""
import json
from dataclasses import dataclass

from structured import (MAX_ATTEMPTS, StructuredResult, ask_structured,
                        extract_json_object)

JUDGE_NAME = "Judge"
DEFAULT_JUDGE_MODEL = "llama3.2:3b"

#: Kept modest on purpose. A 1-5 score, a boolean, and a sentence. Asking a 3B
#: model for a finer rubric produces more confident noise, not more signal.
JUDGE_SYSTEM = (
    "You review recorded incident-response conversations between two engineers "
    "and the recovery plan they produced. You are strict, brief and concrete."
)

EXPECTED = (
    'It must have exactly three keys: "score", an integer from 1 to 5; '
    '"success", true or false; and "reason", one short sentence.'
)

RUBRIC = (
    "Score the exchange from 1 to 5:\n"
    "  1  the plan ignores what was agreed, or the discussion never converged\n"
    "  3  the plan mostly follows the discussion but misses or reorders something\n"
    "  5  the plan follows everything the two engineers agreed, in a safe order\n\n"
    '"success" is true only if you would let this plan be executed as written.\n'
    '"reason" is ONE short sentence naming the single most important factor.\n\n'
    'Reply with the JSON object only: {"score": 3, "success": false, "reason": "..."}'
)


def parse_judgement(text: str):
    """Validate a judge reply. Returns (value, None) or (None, reason)."""
    blob = extract_json_object(text or "")
    if blob is None:
        return None, "no JSON object found"
    try:
        data = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(data, dict):
        return None, "top level is not an object"
    score = data.get("score")
    # bool is a subclass of int in Python, so True would pass an isinstance
    # check for int. Exclude it explicitly.
    if isinstance(score, bool) or not isinstance(score, int):
        return None, "missing or non-integer key: score"
    if not 1 <= score <= 5:
        return None, f"score out of range 1-5: {score}"
    if not isinstance(data.get("success"), bool):
        return None, "missing or non-boolean key: success"
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return None, "missing or empty key: reason"
    return {"score": score, "success": data["success"], "reason": reason.strip()}, None


def judge_messages(transcript, plan_text) -> list:
    """The judge's prompt. Contains no hint of which context policy was used."""
    conversation = "\n".join(f"{e.speaker}: {e.content}" for e in transcript)
    plan = plan_text if plan_text else "(no valid plan was produced)"
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {
            "role": "user",
            "content": (
                f"CONVERSATION\n------------\n{conversation}\n\n"
                f"FINAL PLAN\n----------\n{plan}\n\n{RUBRIC}"
            ),
        },
    ]


@dataclass
class Judgement:
    """A judge verdict, and everything the call cost."""

    result: StructuredResult
    model: str = DEFAULT_JUDGE_MODEL

    @property
    def score(self) -> int | None:
        return self.result.value["score"] if self.result.value else None

    @property
    def success(self) -> bool | None:
        return self.result.value["success"] if self.result.value else None

    @property
    def reason(self) -> str | None:
        return self.result.value["reason"] if self.result.value else None

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

    def as_dict(self) -> dict:
        return {
            **self.result.as_dict(),
            "model": self.model,
            "score": self.score,
            "success": self.success,
            "reason": self.reason,
            "note": "secondary evidence; the deterministic evaluator is primary",
        }


def judge(client, transcript, plan_text, budget,
          model=DEFAULT_JUDGE_MODEL, temperature=0) -> Judgement:
    """Ask the judge for a verdict. Returns a Judgement."""
    result = ask_structured(
        client=client,
        model=model,
        temperature=temperature,
        messages=judge_messages(transcript, plan_text),
        validate=parse_judgement,
        budget=budget,
        speaker=JUDGE_NAME,
        expected=EXPECTED,
    )
    return Judgement(result=result, model=model)
