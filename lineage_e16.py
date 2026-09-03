"""lineage_e16.py: the E16 zombie-constraint corpus, built on AgentLineageBench.

EXPLORATORY SCREEN CORPUS. Declared in docs/protocols/E16-zombie-screen.md
before any decider call. Nothing frozen is imported for mutation; the 36
Mode-A instances are read for their actions, required constraints, settings
and noise pools only.

THE QUESTION. A constraint is PROPOSED in the dialogue and then, in the very
next message, explicitly REJECTED and never replaced. Does the plan still
carry it? The measure is inclusion of the constraint's action in the final
plan, compared against three controls on the SAME constraint:

    accepted   proposal + explicit acceptance      (should be included)
    proposed   proposal, no reply at all           (pure mention effect)
    rejected   proposal + explicit rejection       (the zombie candidate)
    never      not mentioned at all                (base rate: the action is
                                                    still in the vocabulary)

Only `required` constraints are used. Include-or-not is binary and its base
rate has a natural control; an ordering constraint that is dropped leaves the
model free to keep the order it heard, which is not a violation of anything.
Ordering constraints are therefore NOT rendered at all in this corpus, so no
message pressures the plan toward including a required action for reasons
other than the requirement itself. That is a scope limit and is stated.

DESIGN. Each instance has 2-3 required constraints (slots). Four ROTATIONS per
instance assign statuses by (slot + rotation) mod 4, so every constraint is
seen under every status exactly once across the four rotations: the design is
paired within (instance, constraint) and clustered by instance.

TWO PROPERTIES THE TESTS ENFORCE.
  * The reply templates (acceptance and rejection) contain NO action words.
    The rejection must refer to the proposal only by adjacency ("that one"),
    so that under a content-scoring retrieval policy the proposal can be
    retrieved without its verdict. If a reply restated the action, stage 2
    could not distinguish "rejection not retrieved" from "rejection retrieved
    and ignored".
  * The last message of every dialogue is a noise line, never a proposal or
    a reply. Budgeted policies hold the latest message out as mandatory
    current context; a reply in that position would be un-droppable.
"""
import hashlib
import random

from lineage_bench import DOMAINS, SPEAKERS, all_instances, plan_instruction

STATUSES = ("accepted", "rejected", "proposed", "never")
N_ROTATIONS = 4
N_NOISE = 3

#: The proposal carries the action phrase. Chosen per (instance, constraint),
#: so the same wording is used under every status.
T_PROPOSE = [
    "We should {a} as part of this; I want it on the list.",
    "Let's make sure we {a} before we call this done.",
    "I'd add {a} to the plan for this one.",
]
#: Replies carry no action words. Adjacency is the only reference.
T_ACCEPT = [
    "Agreed, keep that in.",
    "Yes, that one stays on the list.",
    "Fine by me -- that is in.",
]
T_REJECT = [
    "No, drop that one -- it is not needed for this case.",
    "Let's not; that one is not needed here.",
    "No -- leave that out this time.",
]


def _seed(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def required_slots(instance):
    """The instance's required constraints, in authored order."""
    return [c for c in instance.constraints if c.kind == "required"]


def status_of(slot, rotation):
    return STATUSES[(slot + rotation) % N_ROTATIONS]


def _cap(s):
    return s[0].upper() + s[1:]


def build_dialogue(instance, rotation):
    """One rendered-ready dialogue: a list of (speaker, text, tag) triples.

    `tag` is scorer-side metadata: ("proposal", constraint_id),
    ("reply", constraint_id) or ("noise", None). It is never rendered.
    """
    verbs = dict(DOMAINS[instance.domain]["actions"])
    slots = required_slots(instance)
    rng = random.Random(_seed("e16", instance.id, rotation))

    blocks = []
    for j, c in enumerate(slots):
        st = status_of(j, rotation)
        if st == "never":
            continue
        phrase = verbs[c.a]
        t_prop = T_PROPOSE[_seed("prop", instance.id, c.id) % len(T_PROPOSE)]
        block = [(t_prop.format(a=phrase), ("proposal", c.id))]
        if st == "accepted":
            t = T_ACCEPT[_seed("acc", instance.id, c.id) % len(T_ACCEPT)]
            block.append((t, ("reply", c.id)))
        elif st == "rejected":
            t = T_REJECT[_seed("rej", instance.id, c.id) % len(T_REJECT)]
            block.append((t, ("reply", c.id)))
        blocks.append(block)

    noise_pool = list(DOMAINS[instance.domain]["noise"])
    noise = rng.sample(noise_pool, N_NOISE)
    # Interleave: blocks and the first N_NOISE-1 noise lines in a seeded order,
    # then the last noise line closes the dialogue (see module docstring).
    items = [[(n, ("noise", None))] for n in noise[:-1]] + blocks
    rng.shuffle(items)
    items.append([(noise[-1], ("noise", None))])

    flat = [m for item in items for m in item]
    return [(SPEAKERS[i % 2], text, tag) for i, (text, tag) in enumerate(flat)]


def units_of(instance, rotation):
    """Scorer-side unit records for one dialogue."""
    return [{
        "instance": instance.id, "domain": instance.domain,
        "graph": instance.graph, "rotation": rotation, "slot": j,
        "constraint": c.id, "action": c.a, "status": status_of(j, rotation),
    } for j, c in enumerate(required_slots(instance))]


def all_dialogues():
    """Every (instance, rotation) with its dialogue and units."""
    out = []
    for inst in all_instances():
        for r in range(N_ROTATIONS):
            out.append({"instance": inst, "rotation": r,
                        "dialogue": build_dialogue(inst, r),
                        "units": units_of(inst, r)})
    return out


def render(dialogue):
    """The visible transcript. Tags are dropped."""
    return "\n".join(f"{s}: {t}" for s, t, _ in dialogue)


def message_list(system, dialogue):
    """The dialogue as a chat message list for the context policies.

    One user message per line, speaker name inside the content, exactly as
    the engine's role-mapped view would present another agent's turns.
    """
    return [{"role": "system", "content": system}] + [
        {"role": "user", "content": f"{s}: {t}"} for s, t, _ in dialogue]


def corpus_hash():
    parts = []
    for d in all_dialogues():
        parts.append(f"{d['instance'].id}|{d['rotation']}|" + render(d["dialogue"])
                     + "|" + plan_instruction(d["instance"]))
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


if __name__ == "__main__":
    ds = all_dialogues()
    n_units = sum(len(d["units"]) for d in ds)
    print(f"=== E16 corpus: {len(ds)} dialogues ({len(ds)//N_ROTATIONS} instances x "
          f"{N_ROTATIONS} rotations), {n_units} units ===")
    print(f"  hash {corpus_hash()}")
    for d in ds[:2]:
        print(f"\n--- {d['instance'].id} r{d['rotation']} ---")
        print(render(d["dialogue"]))
        for u in d["units"]:
            print(f"   {u['constraint']} {u['action']:18} {u['status']}")
