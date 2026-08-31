"""evaluate.py: the deterministic scorer. No LLM is involved in any verdict here.

Answers exactly four questions about a final plan:

    was the JSON parseable?          -> Evaluation.parsed
    were the constraints satisfied?  -> Evaluation.satisfied / .violated
    how many violations?             -> Evaluation.violations
    did the task succeed?            -> Evaluation.success

The point of doing it this way is that the thing deciding whether the agents did
well is not itself a language model. A model cannot argue with `index(a) < index(b)`.

Parsing is deliberately forgiving about WRAPPING and strict about CONTENT: a 3B
model will happily wrap valid JSON in prose or a code fence, and throwing that
away would report a memory failure when what happened was a formatting quirk.
But once the object is found, a missing key or a wrong type is a parse failure,
not something to guess at.
"""
import json
from dataclasses import dataclass, field

from scenario import ACTIONS


@dataclass
class Evaluation:
    parsed: bool
    parse_error: str | None = None
    actions: list[str] = field(default_factory=list)
    ready: bool = False
    unknown_actions: list[str] = field(default_factory=list)
    satisfied: list[str] = field(default_factory=list)
    violated: list[str] = field(default_factory=list)
    success: bool = False

    @property
    def violations(self) -> int:
        return len(self.violated)

    @property
    def constraint_recall(self) -> float:
        total = len(self.satisfied) + len(self.violated)
        return len(self.satisfied) / total if total else 0.0

    def as_dict(self) -> dict:
        return {
            "parsed": self.parsed,
            "parse_error": self.parse_error,
            "actions": self.actions,
            "ready": self.ready,
            "unknown_actions": self.unknown_actions,
            "satisfied": self.satisfied,
            "violated": self.violated,
            "violations": self.violations,
            "constraint_recall": round(self.constraint_recall, 4),
            "success": self.success,
        }


def _extract_json_object(text: str) -> str | None:
    """Return the first balanced {...} block in `text`, or None.

    Scans for a balanced brace pair while ignoring braces inside strings, so a
    plan wrapped in prose or a ```json fence still parses.
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


def parse_plan(text: str) -> tuple[dict | None, str | None]:
    """Parse a final plan. Returns (plan, None) or (None, reason)."""
    blob = _extract_json_object(text or "")
    if blob is None:
        return None, "no JSON object found"
    try:
        plan = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(plan, dict):
        return None, "top level is not an object"
    if "actions" not in plan:
        return None, "missing key: actions"
    if not isinstance(plan["actions"], list) or not all(
        isinstance(a, str) for a in plan["actions"]
    ):
        return None, "actions is not a list of strings"
    if not isinstance(plan.get("ready"), bool):
        return None, "missing or non-boolean key: ready"
    return plan, None


def check_constraint(constraint, actions: list[str]) -> bool:
    """True if `actions` satisfies `constraint`.

    A "before" rule is vacuously satisfied when its second action is absent --
    you cannot order a step that was never proposed. Positions use the FIRST
    occurrence of each action.
    """
    if constraint.kind == "required":
        return constraint.a in actions
    if constraint.kind == "before":
        if constraint.b not in actions:
            return True
        if constraint.a not in actions:
            return False
        return actions.index(constraint.a) < actions.index(constraint.b)
    raise ValueError(f"unknown constraint kind: {constraint.kind}")


def evaluate(text: str, scenario) -> Evaluation:
    """Score one final plan against a scenario's hidden constraint key."""
    plan, error = parse_plan(text)
    if plan is None:
        return Evaluation(parsed=False, parse_error=error)

    actions = plan["actions"]
    unknown = [a for a in actions if a not in ACTIONS]

    satisfied, violated = [], []
    for c in scenario.constraints:
        (satisfied if check_constraint(c, actions) else violated).append(c.id)

    return Evaluation(
        parsed=True,
        actions=actions,
        ready=plan["ready"],
        unknown_actions=unknown,
        satisfied=satisfied,
        violated=violated,
        # Task success is CONSTRAINT SATISFACTION ONLY.
        #
        # Inventing an action name outside the vocabulary is an
        # instruction-following artefact, not a task failure, and it is kept
        # in `unknown_actions` as its own diagnostic. Folding it into success
        # would confound the context experiment: calibration runs showed the
        # invented names are drawn from ideas raised during the dialogue
        # ("notify the ops team", "check the standby node"), so their frequency
        # scales with how much dialogue is in context. A fuller context would
        # then score WORSE for a reason that has nothing to do with memory.
        success=not violated and plan["ready"],
    )
