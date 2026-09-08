"""plansel_fixtures.py: PLAN-SELECTION fixture family. Zero model calls.

Prepared 2026-09-08 after the Phase B qualification gate failed 0/8 on plan
CONSTRUCTION. **Not authorised to run.** The failed Phase B campaign stays
frozen; a repaired qualification arm needs its own declaration and allocation.

WHAT CHANGES AND WHAT DOES NOT
------------------------------
The receiver answers with a plan **identifier** instead of assembling a
sequence, which lowers the generation burden. The logical need to **combine
messages** is preserved exactly:

    P?  pair-1 in order   then pair-2 in order      (4 options total)

One message fixes the ordering within pair 1; another fixes it within pair 2.

    neither message -> 4 options consistent
    either alone    -> 2 consistent
    both            -> exactly 1 consistent
    already holding fact 1 -> only the second message is needed

SCOPE, STATED PLAINLY. This narrows the task to plan selection. Separating
planning knowledge from assembling executable plans is an established
distinction (LLM-Modulo, §2.3). Any result here is about **selecting among
supplied plans**, not about constructing them, and must be reported that way.

NO ANSWER IS SUPPLIED. The option table lists sequences without marking which is
consistent; the receiver must decide from the messages it holds. Labels are
assigned to sequences by one permutation and **displayed** in an independent
order, so the correct answer's identity and its position are separable and are
balanced across the family.
"""
import json
from dataclasses import dataclass, field

import lineage_bench as lb
from lineage_bench import Constraint
from lineage_eval import obeys
from structured import extract_json_object

LABELS = ("P1", "P2", "P3", "P4")
CIDS = ("A", "B", "C", "D")          # A,B carry the ordering facts; C,D distract
FAMILY_SALT = "plansel-v1"

#: 8 fixtures over distinct domains, balanced on correct label and position.
DOMAIN_CYCLE = ("payments", "robotics", "pharmacy", "satellite",
                "brewery", "rail", "payments", "robotics")


@dataclass(frozen=True)
class Option:
    label: str
    sequence: tuple


@dataclass(frozen=True)
class PlanSelFixture:
    fid: str
    domain: str
    setting: str
    actions: tuple            # 4 (identifier, phrase)
    constraints: tuple        # the two authored `before` facts
    options: tuple            # 4 Option, in DISPLAY order
    correct_label: str
    correct_position: int     # 1-based, in display order
    candidates: tuple         # 4 (cid, text) -- A,B facts; C,D distractors
    variants: dict = field(default_factory=dict)


def _order(pair, forward):
    return (pair[0], pair[1]) if forward else (pair[1], pair[0])


def build_fixture(i, domain=None):
    """Fixture i. `i % 4` sets the true assignment; label/display are permuted."""
    domain = domain or DOMAIN_CYCLE[i % len(DOMAIN_CYCLE)]
    dom = lb.DOMAINS[domain]
    acts = tuple(dom["actions"][:4])
    ids = tuple(a[0] for a in acts)
    phr = dict(acts)
    p1, p2 = (ids[0], ids[1]), (ids[2], ids[3])

    fwd1, fwd2 = bool(i & 1), bool(i & 2)          # the two ordering facts
    c1 = Constraint(id="F1", kind="before", a=_order(p1, fwd1)[0],
                    b=_order(p1, fwd1)[1])
    c2 = Constraint(id="F2", kind="before", a=_order(p2, fwd2)[0],
                    b=_order(p2, fwd2)[1])

    # the four semantic sequences: pair-1 block then pair-2 block
    seqs = [tuple(_order(p1, f1)) + tuple(_order(p2, f2))
            for f1 in (True, False) for f2 in (True, False)]
    correct_seq = tuple(_order(p1, fwd1)) + tuple(_order(p2, fwd2))

    # label permutation -> which LABEL is correct; display permutation -> WHERE
    want_label = i % 4
    want_pos = (i % 4 + i // 4) % 4
    # assign labels so that LABELS[want_label] lands on correct_seq
    order_of_seqs = [correct_seq] + [s for s in seqs if s != correct_seq]
    labels_for = {}
    labels_for[correct_seq] = LABELS[want_label]
    rest = [L for j, L in enumerate(LABELS) if j != want_label]
    for s, L in zip(order_of_seqs[1:], rest):
        labels_for[s] = L
    opts = [Option(labels_for[s], s) for s in seqs]

    # display order so the correct option sits at want_pos
    correct_opt = next(o for o in opts if o.sequence == correct_seq)
    others = [o for o in opts if o is not correct_opt]
    shown = others[:want_pos] + [correct_opt] + others[want_pos:]

    fact_text = {
        "A": f"Do not {phr[c1.b]} before we {phr[c1.a]}.",
        "B": f"We cannot {phr[c2.b]} until we {phr[c2.a]}.",
    }
    noise = list(dom["noise"])
    cands = ((("A", fact_text["A"]), ("B", fact_text["B"]),
              ("C", noise[i % len(noise)]),
              ("D", noise[(i + 1) % len(noise)])))
    fx = PlanSelFixture(
        fid=f"{domain}-plansel-{i}~{FAMILY_SALT}", domain=domain,
        setting=dom["setting"], actions=acts, constraints=(c1, c2),
        options=tuple(shown), correct_label=correct_opt.label,
        correct_position=want_pos + 1, candidates=cands,
        variants={"knows_neither": (), "knows_first_fact": ("F1",)})
    return fx


def family(n=8):
    return [build_fixture(i) for i in range(n)]


# --- consistency logic -----------------------------------------------------


def consistent_options(fx, known_facts):
    """Options compatible with the ordering facts the receiver actually holds."""
    cs = [c for c in fx.constraints if c.id in known_facts]
    return [o for o in fx.options
            if all(obeys(c, list(o.sequence)) for c in cs)]


# --- rendering -------------------------------------------------------------


def render_options(fx):
    phr = dict(fx.actions)
    lines = ["Candidate plans:"]
    for o in fx.options:
        lines.append(f"  {o.label}: " + " -> ".join(o.sequence))
    return "\n".join(lines)


def render_context(fx, variant):
    known = fx.variants[variant]
    lines = [f"Setting: {fx.setting}", "", "What you already know:"]
    if not known:
        lines.append("- (nothing beyond the plans below)")
    else:
        phr = dict(fx.actions)
        for c in fx.constraints:
            if c.id in known:
                lines.append(f"- Do not {phr[c.b]} before we {phr[c.a]}.")
    return "\n".join(lines)


def render_bundle(fx, subset):
    txt = [t for cid, t in fx.candidates if cid in subset]
    if not txt:
        return ""
    return "Messages from your teammates:\n\n" + "\n\n".join(txt)


INSTRUCTION = (
    "Choose the one candidate plan that respects everything you know.\n\n"
    'Answer as JSON and nothing else: {"option": "P?", "ready": true}\n\n'
    "`option` is the identifier of the plan you choose.\n"
    "`ready` is true if you consider that plan safe to execute as written."
)


def render_prompt(fx, variant, subset):
    parts = [render_context(fx, variant), "", render_options(fx)]
    b = render_bundle(fx, subset)
    if b:
        parts += ["", b]
    parts += ["", INSTRUCTION]
    return "\n".join(parts)


# --- scoring: the ID is mapped to its sequence, then executably checked ----


def score_option(text, fx):
    """Parse an option id, map it to its sequence, run the executable check.

    The mapping supplies no answer: a wrong identifier maps to a sequence that
    violates a real constraint, exactly as a wrongly-ordered plan would.
    """
    blob = extract_json_object(text or "")
    if blob is None:
        return {"parsed": False, "error": "no JSON object found", "success": False}
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as exc:
        return {"parsed": False, "error": f"invalid JSON: {exc.msg}", "success": False}
    label = obj.get("option")
    if not isinstance(label, str) or label not in {o.label for o in fx.options}:
        return {"parsed": False, "error": f"unknown option {label!r}", "success": False}
    if not isinstance(obj.get("ready"), bool):
        return {"parsed": False, "error": "missing or non-boolean ready",
                "success": False}
    seq = next(o.sequence for o in fx.options if o.label == label)
    sat = [c.id for c in fx.constraints if obeys(c, list(seq))]
    vio = [c.id for c in fx.constraints if not obeys(c, list(seq))]
    return {"parsed": True, "option": label, "sequence": list(seq),
            "ready": obj["ready"], "satisfied": sat, "violated": vio,
            "success": not vio and obj["ready"]}


# --- QUARTETS: one fixture, four assignments of the two ordering facts -----
#
# Within a quartet the option->label mapping, the display order, the action
# descriptions and the unrelated (distractor) text are held FIXED. Only the two
# fact orientations change, and they change consistently everywhere they appear:
# in the delivered message text and in the constraints used for scoring.
#
# Because the label map and display order are bijections held fixed, the four
# assignments necessarily make four DIFFERENT options correct, at four different
# display positions. That is a built-in control, verified rather than assumed.

ASSIGNMENTS = ((True, True), (True, False), (False, True), (False, False))


def _perm_for(seed, k=4):
    """Deterministic permutation of range(k) from an integer seed."""
    import hashlib
    items = list(range(k))
    out = []
    h = int(hashlib.sha256(str(seed).encode()).hexdigest(), 16)
    while items:
        h, j = divmod(h, len(items))
        out.append(items.pop(j))
    return out


def build_quartet(i, domain=None):
    """The 4 assignment variants of fixture `i`, sharing everything else."""
    domain = domain or DOMAIN_CYCLE[i % len(DOMAIN_CYCLE)]
    dom = lb.DOMAINS[domain]
    acts = tuple(dom["actions"][:4])
    ids = tuple(a[0] for a in acts)
    phr = dict(acts)
    p1, p2 = (ids[0], ids[1]), (ids[2], ids[3])

    seqs = [tuple(_order(p1, f1)) + tuple(_order(p2, f2))
            for f1, f2 in ASSIGNMENTS]
    # label map and display order drawn from INDEPENDENT seeds, fixed per fixture
    lab_perm = _perm_for(("label", i))
    dis_perm = _perm_for(("display", i))
    labels_for = {seqs[j]: LABELS[lab_perm[j]] for j in range(4)}
    opts_canonical = [Option(labels_for[s], s) for s in seqs]
    shown = tuple(opts_canonical[j] for j in dis_perm)

    noise = list(dom["noise"])
    out = []
    for a, (fwd1, fwd2) in enumerate(ASSIGNMENTS):
        c1 = Constraint(id="F1", kind="before", a=_order(p1, fwd1)[0],
                        b=_order(p1, fwd1)[1])
        c2 = Constraint(id="F2", kind="before", a=_order(p2, fwd2)[0],
                        b=_order(p2, fwd2)[1])
        correct_seq = tuple(_order(p1, fwd1)) + tuple(_order(p2, fwd2))
        correct = labels_for[correct_seq]
        cands = (("A", f"Do not {phr[c1.b]} before we {phr[c1.a]}."),
                 ("B", f"We cannot {phr[c2.b]} until we {phr[c2.a]}."),
                 ("C", noise[i % len(noise)]),
                 ("D", noise[(i + 1) % len(noise)]))
        out.append(PlanSelFixture(
            fid=f"{domain}-plansel-{i}-a{a}~{FAMILY_SALT}", domain=domain,
            setting=dom["setting"], actions=acts, constraints=(c1, c2),
            options=shown, correct_label=correct,
            correct_position=[o.label for o in shown].index(correct) + 1,
            candidates=cands,
            variants={"knows_neither": (), "knows_first_fact": ("F1",)}))
    return out


def quartets(n=8):
    return [build_quartet(i) for i in range(n)]
