"""scenario.py: one incident-recovery scenario, with a hidden evaluator key.

The split this file exists to enforce:

  WHAT THE AGENTS SEE   natural-language dialogue. Operational facts stated the
                        way a colleague would state them. No rule ids, no action
                        identifiers, no hint that anything is being scored.

  WHAT THE SCORER SEES  a list of Constraint objects. Machine-checkable, never
                        rendered into any prompt.

Two rules govern the design, and both exist so the later context experiment can
measure anything at all:

1. Constraints live in the DIALOGUE, never in a system prompt. A system prompt
   survives every context-management policy by construction, so a constraint
   placed there can never be forgotten and would make the experiment inert.

2. The dialogue stays natural. The closed action vocabulary appears in exactly
   one place -- the final-plan instruction -- so the task measures whether the
   agent remembered a fact, not whether it can carry arbitrary tokens.

`stated_at_turn` records which seeded turn carries each constraint. Nothing uses
it yet; it is what a later experiment needs in order to stratify constraints by
distance-from-end, and it is free to record now.
"""
from dataclasses import dataclass

from agents import Agent
from engine import Entry

#: The closed action vocabulary. Shown to the agents ONLY in the final-plan
#: instruction, never during the dialogue.
ACTIONS = (
    "ISOLATE_NODE",
    "RUN_DIAGNOSTICS",
    "RUN_BACKUP",
    "FAILOVER_API",
    "RESTART_DB",
    "RESTORE_TRAFFIC",
)


@dataclass(frozen=True)
class Constraint:
    """One machine-checkable rule. HIDDEN -- never rendered into a prompt.

    kind="required"  -- action `a` must appear in the plan.
    kind="before"    -- if `b` appears, `a` must appear earlier. If `b` is absent
                        the rule is vacuously satisfied: you cannot order an
                        action that was never proposed.

    `natural` is the sentence in the seeded dialogue that conveys this rule. It
    is recorded so the mapping from natural language to rule is auditable, and
    so a test can assert the two never drift apart.
    """

    id: str
    kind: str
    a: str
    b: str | None = None
    stated_at_turn: int = -1
    natural: str = ""


@dataclass(frozen=True)
class Scenario:
    """One incident: the framing, the opening dialogue, and the hidden key."""

    id: str
    brief: str
    seed_dialogue: tuple[tuple[str, str], ...]
    constraints: tuple[Constraint, ...]

    def seed_entries(self) -> list[Entry]:
        """The opening dialogue as Entry objects, ready to pre-load the engine.

        Costs are zero because no model call produced these turns.
        """
        return [
            Entry(
                speaker=speaker,
                content=text,
                prompt_tokens=0,
                completion_tokens=0,
                seconds=0.0,
                turn_index=i,
            )
            for i, (speaker, text) in enumerate(self.seed_dialogue)
        ]

    def required_actions(self) -> list[str]:
        return [c.a for c in self.constraints if c.kind == "required"]


OPS = "Operations Lead"
AUDITOR = "Safety Auditor"

BRIEF = (
    "A production incident is in progress. The payments database on node db-04 is "
    "returning errors under load, and the customer-facing API is degraded. You and "
    "one colleague are working out the recovery plan together."
)

#: The opening exchange. Six turns, alternating, so the engine's turn parity
#: leaves the Operations Lead to speak next. Every task-critical fact is stated
#: here, in the dialogue body, several turns before it is needed.
SEED_DIALOGUE = (
    (
        OPS,
        "We've traced the errors to node db-04. It's still taking cluster traffic "
        "and I want to start looking at it properly.",
    ),
    (
        AUDITOR,
        "Before anything else, that node has to be isolated -- it cannot stay on "
        "the cluster network while it's in this state. And do not run diagnostics "
        "on it until the node is isolated, or you'll be reading numbers polluted "
        "by live traffic.",
    ),
    (
        OPS,
        "Understood. I'll also want a backup -- our policy is that we take a "
        "backup before any destructive step, no exceptions, and I'd rather not "
        "explain that one afterwards.",
    ),
    (
        AUDITOR,
        "Agreed, and note the dependency: the database cannot be restarted until "
        "the backup has completed. A restart mid-backup leaves us with neither a "
        "clean database nor a usable copy.",
    ),
    (
        OPS,
        "Fine. Once it's isolated and backed up I expect the restart is what "
        "actually clears the fault. Customers are still seeing errors, so I want "
        "traffic back as soon as we can.",
    ),
    (
        AUDITOR,
        "Two more things and then it's your plan. Restarting the database drops "
        "the API with it, so the API has to be failed over before the restart, not "
        "after. And traffic stays off until the database is back and serving -- "
        "we are not restoring traffic to a database that isn't up.",
    ),
)

#: The hidden key. Never rendered into a prompt.
CONSTRAINTS = (
    Constraint(
        id="C1",
        kind="required",
        a="ISOLATE_NODE",
        stated_at_turn=1,
        natural="that node has to be isolated",
    ),
    Constraint(
        id="C2",
        kind="before",
        a="ISOLATE_NODE",
        b="RUN_DIAGNOSTICS",
        stated_at_turn=1,
        natural="do not run diagnostics on it until the node is isolated",
    ),
    Constraint(
        id="C3",
        kind="required",
        a="RUN_BACKUP",
        stated_at_turn=2,
        natural="we take a backup before any destructive step",
    ),
    Constraint(
        id="C4",
        kind="before",
        a="RUN_BACKUP",
        b="RESTART_DB",
        stated_at_turn=3,
        natural="the database cannot be restarted until the backup has completed",
    ),
    Constraint(
        id="C5",
        kind="before",
        a="FAILOVER_API",
        b="RESTART_DB",
        stated_at_turn=5,
        natural="the API has to be failed over before the restart",
    ),
    Constraint(
        id="C6",
        kind="before",
        a="RESTART_DB",
        b="RESTORE_TRAFFIC",
        stated_at_turn=5,
        natural="traffic stays off until the database is back and serving",
    ),
    # Without this the ordering rules are all vacuously satisfiable: a plan of
    # just [ISOLATE_NODE, RUN_BACKUP] would score a perfect 6/6 by proposing
    # nothing that could be mis-ordered. Requiring the incident to actually be
    # resolved forces RESTART_DB in, which in turn re-arms C4, C5 and C6.
    Constraint(
        id="C7",
        kind="required",
        a="RESTORE_TRAFFIC",
        stated_at_turn=4,
        natural="I want traffic back",
    ),
)

INCIDENT = Scenario(
    id="db04-payments",
    brief=BRIEF,
    seed_dialogue=SEED_DIALOGUE,
    constraints=CONSTRAINTS,
)


def _persona(role: str, duty: str) -> str:
    return (
        f"You are the {role} handling a live production incident. {duty}\n\n"
        f"{BRIEF}\n\n"
        "Speak naturally, as you would to a colleague. Keep each reply to at "
        "most three sentences. Respond to what the other person actually said."
    )


AGENT_A = Agent(
    name=OPS,
    system_prompt=_persona(
        OPS,
        "You are responsible for producing a safe recovery plan and restoring "
        "service. Propose concrete operational steps and keep track of what has "
        "been agreed.",
    ),
    temperature=0,
)

AGENT_B = Agent(
    name=AUDITOR,
    system_prompt=_persona(
        AUDITOR,
        "You challenge unsafe actions and hold the plan to the operational "
        "constraints that have been established. Do not invent new restrictions; "
        "hold the line on the ones already raised.",
    ),
    temperature=0,
)

#: Asked of the Operations Lead once the dialogue ends. This is the ONLY place
#: the agents ever see the action vocabulary.
FINAL_PLAN_INSTRUCTION = (
    "Write the final recovery plan now, as JSON and nothing else.\n\n"
    'Format: {"actions": [...], "ready": true}\n\n'
    "`actions` is the ordered list of steps to carry out, using only these "
    "identifiers:\n"
    + "  " + "  ".join(ACTIONS) + "\n\n"
    "`ready` is true if you consider the plan safe to execute as written.\n"
    "Include only the steps this incident actually needs, in an order that "
    "respects everything agreed during the discussion."
)
