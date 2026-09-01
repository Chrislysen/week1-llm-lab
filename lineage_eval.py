"""lineage_eval.py: deterministic scorer and the predefined lineage metrics.

No language model takes part in any verdict. Constraint obedience is membership
and index comparison; every metric below is arithmetic over recorded presence.

The metric definitions are fixed HERE, before the benchmark is run, so they
cannot be chosen to suit an outcome. Two of them are conditional by
construction, and the conditioning is the point:

  retrieval authority inversion   scored ONLY over eligible source/derived
                                  PAIRS -- a constraint with no derivative is
                                  not evidence either way.

  decision authority inversion    scored ONLY when the authoritative source AND
                                  a conflicting derived representation are BOTH
                                  actually in the model's context. Otherwise a
                                  retrieval failure would be counted as a
                                  decision failure.

Every rate is reported with its denominator. A rate whose denominator is zero is
None, never 0.0.
"""
from dataclasses import dataclass, field

from structured import extract_json_object

import json


@dataclass
class PlanCheck:
    parsed: bool
    parse_error: str | None = None
    actions: list = field(default_factory=list)
    ready: bool = False
    unknown_actions: list = field(default_factory=list)
    satisfied: list = field(default_factory=list)      # constraint ids
    violated: list = field(default_factory=list)
    success: bool = False

    @property
    def constraint_recall(self):
        n = len(self.satisfied) + len(self.violated)
        return round(len(self.satisfied) / n, 4) if n else None

    def as_dict(self):
        return {
            "parsed": self.parsed, "parse_error": self.parse_error,
            "actions": self.actions, "ready": self.ready,
            "unknown_actions": self.unknown_actions,
            "satisfied": self.satisfied, "violated": self.violated,
            "violations": len(self.violated),
            "constraint_recall": self.constraint_recall,
            "success": self.success,
        }


def parse_plan(text):
    blob = extract_json_object(text or "")
    if blob is None:
        return None, "no JSON object found"
    try:
        plan = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(plan, dict):
        return None, "top level is not an object"
    if not isinstance(plan.get("actions"), list) or not all(
            isinstance(a, str) for a in plan["actions"]):
        return None, "actions is not a list of strings"
    if not isinstance(plan.get("ready"), bool):
        return None, "missing or non-boolean key: ready"
    return plan, None


def obeys(constraint, actions):
    """True if `actions` satisfies `constraint`.

    A `before` rule is vacuously satisfied when its second action is absent --
    an action never proposed cannot be mis-ordered. First occurrence wins.
    """
    if constraint.kind == "required":
        return constraint.a in actions
    if constraint.kind == "before":
        if constraint.b not in actions:
            return True
        if constraint.a not in actions:
            return False
        return actions.index(constraint.a) < actions.index(constraint.b)
    raise ValueError(constraint.kind)


def check_plan(text, instance, constraints=None):
    """Score a plan against a constraint set (default: effective ground truth)."""
    plan, err = parse_plan(text)
    if plan is None:
        return PlanCheck(parsed=False, parse_error=err)

    cs = instance.effective_constraints if constraints is None else constraints
    actions = plan["actions"]
    unknown = [a for a in actions if a not in instance.actions]
    sat, vio = [], []
    for c in cs:
        (sat if obeys(c, actions) else vio).append(c.id)

    return PlanCheck(
        parsed=True, actions=actions, ready=plan["ready"],
        unknown_actions=unknown, satisfied=sat, violated=vio,
        # Consistent with the compulsory evaluator: invented action names are a
        # recorded diagnostic, not a task failure.
        success=not vio and plan["ready"],
    )


def corrupted_form(constraint):
    """What the CORRUPTED_RELAY asserts instead. The distortion is exact.

    before(a, b)  ->  before(b, a)   (inverted ordering)
    required(a)   ->  no constraint  (demoted to optional)
    """
    if constraint.kind == "before":
        return type(constraint)(id=constraint.id + "~", kind="before",
                                a=constraint.b, b=constraint.a)
    return None


# ------------------------------------------------------------- presence ----


def presence(instance, exposed_messages):
    """Per constraint, which lineage representations reached the context.

    This is the record the conditional metrics are computed from.
    """
    ids = {m.msg_id for m in exposed_messages}
    out = {}
    for c in instance.constraints:
        reps = instance.representations(c.id)
        out[c.id] = {
            "source_present": any(
                m.lineage == "SOURCE" and m.msg_id in ids for m in reps),
            "faithful_present": any(
                m.lineage == "FAITHFUL_RELAY" and m.msg_id in ids for m in reps),
            "corruption_present": any(
                m.lineage == "CORRUPTED_RELAY" and m.msg_id in ids for m in reps),
            "recovery_present": any(
                m.lineage == "RECOVERY" and m.msg_id in ids for m in reps),
            "supersession_present": any(
                m.lineage == "SUPERSESSION" and m.msg_id in ids for m in reps),
            "superseded": c.id in instance.superseded,
        }
    return out


# -------------------------------------------------------------- metrics ----


def _rate(num, den):
    return round(num / den, 4) if den else None


def retrieval_authority_inversion(instance, ranking):
    """Rank-based, over ELIGIBLE PAIRS only.

    `ranking` is msg_id in retrieval-priority order. For each constraint that
    has BOTH a source and at least one derivative, the pair is inverted when the
    best-ranked derivative outranks the source. Constraints with no derivative
    are not eligible and are excluded from the denominator entirely.
    """
    pos = {m: i for i, m in enumerate(ranking)}
    inverted = eligible = 0
    detail = []
    for c in instance.constraints:
        reps = instance.representations(c.id)
        src = [m for m in reps if m.lineage == "SOURCE" and m.msg_id in pos]
        der = [m for m in reps
               if m.lineage in ("FAITHFUL_RELAY", "CORRUPTED_RELAY")
               and m.msg_id in pos]
        if not src or not der:
            continue
        eligible += 1
        s = pos[src[0].msg_id]
        d = min(pos[m.msg_id] for m in der)
        if d < s:
            inverted += 1
        detail.append({"constraint": c.id, "source_rank": s,
                       "best_derived_rank": d, "inverted": d < s})
    return {"eligible_pairs": eligible, "inverted_pairs": inverted,
            "rate": _rate(inverted, eligible), "detail": detail}


def decision_authority_inversion(instance, pres, check):
    """Scored ONLY where source AND conflicting corruption were both present.

    For each such constraint: the decision follows the SOURCE if the plan obeys
    the authored rule, and follows the CORRUPTION if it obeys the corrupted form
    instead. A plan obeying neither is counted separately and excluded from the
    inversion ratio, because it is evidence of confusion rather than of
    misplaced authority.

    Superseded constraints are excluded: there the derived statement is
    legitimately authoritative, so "following the derivative" is correct.
    """
    if not check.parsed:
        return {"eligible": 0, "follows_source": 0, "follows_corruption": 0,
                "follows_neither": 0, "rate": None, "detail": []}

    actions = check.actions
    src = cor = neither = 0
    detail = []
    for c in instance.constraints:
        p = pres[c.id]
        if p["superseded"] or not (p["source_present"] and p["corruption_present"]):
            continue
        alt = corrupted_form(c)
        follows_src = obeys(c, actions)
        # For a demoted `required`, the corrupted form is "no constraint", so
        # following the corruption means simply omitting the action.
        follows_cor = (obeys(alt, actions) if alt is not None
                       else c.a not in actions)
        if follows_src and not follows_cor:
            src += 1
            outcome = "source"
        elif follows_cor and not follows_src:
            cor += 1
            outcome = "corruption"
        else:
            neither += 1
            outcome = "ambiguous" if follows_src else "neither"
        detail.append({"constraint": c.id, "outcome": outcome})

    return {"eligible": src + cor + neither, "follows_source": src,
            "follows_corruption": cor, "follows_neither": neither,
            "rate": _rate(cor, src + cor), "detail": detail}


def supersession_respected(instance, pres, check):
    """Where a legitimate override was in context, was the NEW rule followed?

    A system that blindly prefers authoritative sources fails this, which is
    exactly why the class exists.
    """
    if not check.parsed:
        return {"eligible": 0, "respected": 0, "rate": None}
    n = ok = 0
    for c in instance.constraints:
        p = pres[c.id]
        if not (p["superseded"] and p["supersession_present"]):
            continue
        n += 1
        # The rule was lifted, so the plan is free of it. Respecting the
        # supersession means NOT being bound by the old constraint -- scored as
        # "the plan is valid without it", which is true by construction once the
        # constraint is dropped from the effective set. What we can check is
        # that the plan was not penalised for it: c.id must not be in violated.
        if c.id not in check.violated:
            ok += 1
    return {"eligible": n, "respected": ok, "rate": _rate(ok, n)}


def utilization(instance, pres, check):
    """Did the plan obey constraints whose representation was present?

    Split by which representation carried the information:
      direct source  -- SOURCE present, no corruption present
      faithful relay -- FAITHFUL_RELAY present, source absent
    Both exclude superseded constraints.
    """
    if not check.parsed:
        return {"direct_source": None, "direct_source_n": 0,
                "faithful_relay": None, "faithful_relay_n": 0}
    ds_ok = ds_n = fr_ok = fr_n = 0
    for c in instance.constraints:
        p = pres[c.id]
        if p["superseded"]:
            continue
        obeyed = c.id not in check.violated
        if p["source_present"] and not p["corruption_present"]:
            ds_n += 1
            ds_ok += obeyed
        if p["faithful_present"] and not p["source_present"]:
            fr_n += 1
            fr_ok += obeyed
    return {"direct_source": _rate(ds_ok, ds_n), "direct_source_n": ds_n,
            "faithful_relay": _rate(fr_ok, fr_n), "faithful_relay_n": fr_n}


def corruption_susceptibility(instance, pres, check):
    """Corruption present and source ABSENT: was the distortion adopted?

    The clean read on whether a derived misstatement propagates when nothing
    contradicts it.
    """
    if not check.parsed:
        return {"eligible": 0, "adopted": 0, "rate": None}
    n = adopted = 0
    for c in instance.constraints:
        p = pres[c.id]
        if p["superseded"] or not p["corruption_present"] or p["source_present"]:
            continue
        n += 1
        alt = corrupted_form(c)
        if (obeys(alt, check.actions) if alt is not None
                else c.a not in check.actions):
            adopted += 1
    return {"eligible": n, "adopted": adopted, "rate": _rate(adopted, n)}


def recovery_rate(instance, pres, check):
    """Corruption AND a later correction both present: was the truth restored?"""
    if not check.parsed:
        return {"eligible": 0, "recovered": 0, "rate": None}
    n = ok = 0
    for c in instance.constraints:
        p = pres[c.id]
        if p["superseded"] or not (p["corruption_present"] and p["recovery_present"]):
            continue
        n += 1
        ok += c.id not in check.violated
    return {"eligible": n, "recovered": ok, "rate": _rate(ok, n)}


def score(instance, exposed_messages, plan_text, ranking=None):
    """Everything, for one (instance, exposure, plan)."""
    pres = presence(instance, exposed_messages)
    check = check_plan(plan_text, instance)
    out = {
        "instance": instance.id,
        "plan": check.as_dict(),
        "presence": pres,
        "decision_authority_inversion": decision_authority_inversion(
            instance, pres, check),
        "supersession_respected": supersession_respected(instance, pres, check),
        "utilization": utilization(instance, pres, check),
        "corruption_susceptibility": corruption_susceptibility(
            instance, pres, check),
        "recovery": recovery_rate(instance, pres, check),
    }
    if ranking is not None:
        out["retrieval_authority_inversion"] = retrieval_authority_inversion(
            instance, ranking)
    return out
