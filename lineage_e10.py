"""lineage_e10.py: E10 corpus -- evidential dependence, held apart from everything else.

Protocol: docs/protocols/E10-lineage-independence-v1.md, committed before any
decider call. Nothing here modifies a historical corpus; E10 builds its own and
hashes it.

THE ONE VARIABLE. Does k support messages tracing to ONE evidential root behave
differently from k INDEPENDENT roots supporting the same proposition, when count,
wording, speakers, order, position and length are all matched?

HOW DEPENDENCE IS MADE REAL WITHOUT A LEXICAL GIVEAWAY. Every support message
attributes its claim to a NAMED BASIS -- a document, drawn from one pool shared
by every domain and every arm:

    SAME_ROOT         S(runbook), R1(runbook), R2(runbook), X
    INDEPENDENT_ROOT  S(runbook), R1(compliance sheet), R2(incident review), X

Three statements either way. In the first they are three reports of ONE artifact
and add no independent information. In the second, three artifacts agree.

COUNTERBALANCING IS WHAT MAKES THIS SAFE. Which basis is the repeated one rotates
across instances, so every basis string appears in SAME_ROOT for some instances
and INDEPENDENT_ROOT for others, and both arms draw sentence templates from the
same pool. No per-message unigram or bigram can separate the arms -- gate 18,
enforced by test_lineage_e10.

What does differ, necessarily, is the WITHIN-INSTANCE REPETITION OF BASIS
IDENTITY. That is not an artefact to scrub. It is the independent variable, and
saying so plainly is what gate 19 asks for.

WHY NOT "as the Ops Lead said". Attribution to a speaker would encode dependence
in speaker reference -- precisely the confound E9 had to clean up, and not
counterbalanceable. Basis identity is.
"""
import hashlib
import random
from dataclasses import dataclass, replace

from lineage_bench import DOMAINS, Message, all_instances

#: Speakers. D contradicts or supersedes in EVERY arm, so "the contradictor is
#: a fresh voice" is constant and cannot vary with condition -- E9's lesson.
A, B, C, D = ("Operations Lead", "Safety Auditor", "Network Engineer",
              "Duty Manager")

#: Shared across all domains and both arms, so basis vocabulary is not a domain
#: cue and not an arm cue.
#:
#: TWO ENTRIES WERE REMOVED BEFORE ANY DECIDER CALL, both found by reading the
#: rendered corpus:
#:
#:   "the change-control record"  collided with the supersession authority,
#:       which is Change-control. In instances where that basis was the repeated
#:       root, the body superseding the claim WAS the body corroborating it --
#:       a different manipulation in those instances than in the others.
#:   "the vendor support note"    shares "vendor" with "the vendor runbook", so
#:       two supposedly INDEPENDENT roots read as one organisation's paperwork.
#:       Independence has to be plausible to a reader, not merely asserted by
#:       the label.
#:
#: Six distinct entities remain, none of them the revising authority.
BASES = ["the vendor runbook", "the compliance sheet",
         "last quarter's incident review", "the platform spec",
         "the safety case", "the site handover notes"]

#: ONE pool, used by SAME_ROOT and INDEPENDENT_ROOT alike. If each arm had its
#: own templates the arms would be separable by sentence shape rather than by
#: evidential structure.
#:
#: THE BASIS ALWAYS SITS IN THE SAME SLOT: sentence-final, preceded by "per".
#: The first version placed it mid-sentence ("Going by {basis}, {a} ...") and
#: gate 10 failed with 26 n-grams unique to same_root -- 'by last', 'case
#: clear', 'notes ground'. Those are BOUNDARY BIGRAMS: the basis sat next to
#: varying text, so each (basis, template) pairing produced its own crossing
#: bigram, and with 36 instances the pairings could not counterbalance.
#:
#: Pinning the basis to one slot removes every crossing bigram except "per the",
#: which both arms share. Nothing about the manipulation is weakened: what
#: differs between arms is still exactly which basis is named.
T_SUPPORT = [
    "{a} comes before {b}, per {basis}.",
    "the order is {a} then {b}, per {basis}.",
    "{a} has to come before {b}, per {basis}.",
    "we do {a} first, then {b}, per {basis}.",
]

T_SOURCE = "{a} has to happen before {b}, per {basis}."

#: FILLER HAD TO BE LENGTHENED, and gate 12 is why. The domain noise bank
#: averages 7.75 words against the support messages' 13.83 -- a six-word gap per
#: message. H2 compares `same_root` against `filler`, so an unmatched gap would
#: have made H2 partly a length test, which is the exact defect E9 exposed in
#: Mode A's `d1_padded`. Found before any decider call, by a gate, not after.
#:
#: These frames are deliberately EMPTY: no basis citation (that would make
#: filler a weak form of support), and no meta-commentary such as "unrelated to
#: the ordering" (that would tell the model to discount it, making filler less
#: distracting than it should be). Six words of neutral operational packaging,
#: nothing more.
#: Frames were SELECTED PROGRAMMATICALLY against the union of every domain's
#: action vocabulary (69 keywords), not chosen by eye. The first hand-written
#: set said "for the shift log", and `shift` is the payments action verb
#: (`shift routing`), so the filler mentioned the constraint it exists to avoid.
#: A later candidate, "for the record", collided with the pharmacy verb
#: (`update the labelling record`). Both were caught by a gate before any
#: decider call; neither was visible by reading.
T_FILLER = [
    "One more item from the handover: {noise}",
    "Also worth a mention from today: {noise}",
    "Noting this down for the team: {noise}",
    "Separate item from earlier this morning: {noise}",
]

#: Byte-identical across every arm that carries it. No basis, no authority
#: language -- a bare assertion, so the arms differ only where they must.
T_CONTRADICT = "We should {b} before we {a}."

#: The legitimate update. Spoken by the authorised reviser, and it CHANGES
#: GROUND TRUTH: the evaluator scores these arms against the reversed relation.
#: Framed as a decision, not as a competing report, which is what separates it
#: from T_CONTRADICT.
T_SUPERSEDE = ("Change-control approved a revision this morning: the order is "
               "now {b} before {a}. That supersedes the earlier sequence.")

MAX_SUPPORT = 2

#: Deleting an arm must be a test failure, not a silent narrowing.
ARMS = [
    ("bare", 0, None, False, True),
    ("filler", 0, None, False, True),
    ("same_root", MAX_SUPPORT, "same", False, True),
    ("indep_root", MAX_SUPPORT, "indep", False, True),
    ("same_root_nospk", MAX_SUPPORT, "same", True, True),
    ("indep_root_nospk", MAX_SUPPORT, "indep", True, True),
    ("bare_super", 0, None, False, False),
    ("same_root_super", MAX_SUPPORT, "same", False, False),
    ("indep_root_super", MAX_SUPPORT, "indep", False, False),
]
N_ARMS = 9

#: Arms whose ground truth is the REVERSED relation, because a legitimate
#: authority changed it.
SUPERSESSION_ARMS = {a for a, _, _, _, contra in ARMS if not contra}


@dataclass(frozen=True)
class E10Instance:
    """One formal instance dressed for E10. Text only -- formal content is the
    frozen benchmark's."""
    instance_id: str
    domain: str
    constraint_id: str
    a: str                 # action that must come first, per the SOURCE
    b: str
    bases: tuple           # (root, alt1, alt2); root is cited by the SOURCE
    source: str
    support_same: tuple    # 2 messages, all citing bases[0]
    support_indep: tuple   # 2 messages, citing bases[1] and bases[2]
    filler: tuple          # 2 constraint-irrelevant messages
    contradiction: str
    supersession: str


def _cap(s):
    return s[0].upper() + s[1:] if s else s


def _seed(instance_id):
    return int(hashlib.sha256(f"e10|{instance_id}".encode()).hexdigest()[:8], 16)


def target_constraint(instance):
    """The ordering E10 manipulates: a `before` rule the instance does not
    already supersede, so E10's own supersession arm is the only override."""
    cand = [c for c in instance.constraints
            if c.kind == "before" and c.id not in instance.superseded]
    if not cand:
        raise ValueError(f"{instance.id}: no usable before-constraint")
    return cand[0]


def build(instance):
    """Dress one formal instance. Deterministic from the instance id alone."""
    c = target_constraint(instance)
    verbs = dict(DOMAINS[instance.domain]["actions"])
    a, b = verbs[c.a], verbs[c.b]
    rng = random.Random(_seed(instance.id))

    # COUNTERBALANCING. The rotation makes every basis serve as the repeated
    # root in some instances and as a distinct alternative in others, so basis
    # vocabulary is matched between arms across the corpus.
    off = _seed(instance.id) % len(BASES)
    bases = tuple(BASES[(off + k) % len(BASES)] for k in range(3))

    # Templates are drawn WITHOUT replacement and the SAME draw is used for
    # both arms, so the two arms share sentence skeletons exactly and differ
    # only in the basis token.
    picks = rng.sample(T_SUPPORT, MAX_SUPPORT)

    def support(basis_for):
        return tuple(_cap(t.format(basis=basis_for(k), a=a, b=b))
                     for k, t in enumerate(picks))

    noise = DOMAINS[instance.domain]["noise"]
    frames = rng.sample(T_FILLER, MAX_SUPPORT)
    filler = tuple(f.format(noise=n[0].lower() + n[1:])
                   for f, n in zip(frames, noise[:MAX_SUPPORT]))
    return E10Instance(
        instance_id=instance.id, domain=instance.domain, constraint_id=c.id,
        a=c.a, b=c.b, bases=bases,
        source=_cap(T_SOURCE.format(basis=bases[0], a=a, b=b)),
        support_same=support(lambda k: bases[0]),
        support_indep=support(lambda k: bases[k + 1]),
        filler=filler,
        contradiction=T_CONTRADICT.format(a=a, b=b),
        supersession=T_SUPERSEDE.format(a=a, b=b),
    )


def exposure(e10, arm):
    """Rendered messages for one arm, as (speaker, text) pairs.

    `speaker` is None in the speaker-free arms, and the renderer omits the
    prefix entirely rather than substituting a placeholder -- a placeholder is
    still a speaker slot and would leave the social frame in place.
    """
    name, n_sup, kind, nospk, contra = next(x for x in ARMS if x[0] == arm)
    tail = e10.contradiction if contra else e10.supersession
    if n_sup == 0 and name.startswith("bare"):
        mid = []
    elif name == "filler":
        mid = list(e10.filler)
    else:
        mid = list(e10.support_same if kind == "same" else e10.support_indep)
    speakers = [A] + [B, C][:len(mid)] + [D]
    texts = [e10.source] + mid + [tail]
    if nospk:
        speakers = [None] * len(texts)
    return list(zip(speakers, texts))


def render(msgs):
    return "\n".join(t if s is None else f"{s}: {t}" for s, t in msgs)


def ground_truth(instance, e10, arm):
    """The relation the plan is scored against for this arm.

    Unsupported contradiction leaves ground truth alone. Legitimate
    supersession REVERSES it -- the corrected semantics, not the historically
    broken metric that returned 1.0 for an empty plan.
    """
    from lineage_bench import Constraint
    c = {x.id: x for x in instance.constraints}[e10.constraint_id]
    if arm in SUPERSESSION_ARMS:
        return Constraint(id=c.id, kind="before", a=c.b, b=c.a)
    return c


def all_e10():
    return [build(i) for i in all_instances()]


def corpus_hash():
    """Written before scoring. Covers every rendered string in every arm."""
    parts = []
    for inst, e in zip(all_instances(), all_e10()):
        for arm, *_ in ARMS:
            parts.append(f"{e.instance_id}|{arm}|" + "|".join(
                f"{s or '-'}:{t}" for s, t in exposure(e, arm)))
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


if __name__ == "__main__":
    es = all_e10()
    print(f"=== E10 corpus: {len(es)} instances x {N_ARMS} arms ===")
    print(f"  hash {corpus_hash()}\n")
    e = es[0]
    inst = all_instances()[0]
    for arm, *_ in ARMS:
        print(f"--- {arm} ---   ground truth: "
              f"{ground_truth(inst, e, arm).a} before "
              f"{ground_truth(inst, e, arm).b}")
        for s, t in exposure(e, arm):
            print(f"    {'' if s is None else s + ': '}{t}")
        print()
