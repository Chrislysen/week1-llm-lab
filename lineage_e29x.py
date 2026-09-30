"""lineage_e29x.py: the two reviewer controls for E29 (E29-X).

DECLARED in docs/protocols/E29X-reviewer-controls.md before any decider call.

Two objections from an outside adversarial review (Gemini Deep Research run
1, objections 2 and 4) name controls E29 did not run. Both are oracle-store
designs on the E29 corpus, rendered by the same functions as the four E29
designs.

    full_explicit   E29-R, the rendering control. The transcript, with each
                    accept/reject reply's bare referent ("that one", "that")
                    replaced by the store's explicit referent ("the proposal
                    to {phrase}"). Every other character of the transcript is
                    unchanged. If the level gap between `full` and the store
                    designs in E29 was the explicitness of the rejection's
                    referent rather than the design, this arm closes it.

    tombstone       E29-T, the soft-supersede design (Mem0's proposed
                    is_active:false flag; Lethe-style tombstones). On
                    rejection the proposal fact is RETAINED and flagged
                    "[withdrawn]" instead of deleted; nothing else is stored
                    for the rejection (the flag consumes it, as DELETE did).
                    A later restatement is ADDed as a fresh fact, as under
                    delete. The decider sees the flag. The question is whether
                    a flagged-but-present proposal protects like add-only's
                    explicit rejection or re-admits like delete's absence.
"""
from lineage_bench import DOMAINS
from lineage_e16 import T_ACCEPT, T_ACCEPT2, T_REJECT, T_REJECT2
from lineage_e29 import facts_for

DESIGNS_X = ("full_explicit", "tombstone")

#: reply template -> explicit template; {a} is the action phrase.
EXPLICIT = {
    # frozen bank
    "No, drop that one -- it is not needed for this case.":
        "No, drop the proposal to {a} -- it is not needed for this case.",
    "Let's not; that one is not needed here.":
        "Let's not; the proposal to {a} is not needed here.",
    "No -- leave that out this time.":
        "No -- leave the proposal to {a} out this time.",
    "Agreed, keep that in.":
        "Agreed, keep the proposal to {a} in.",
    "Yes, that one stays on the list.":
        "Yes, the proposal to {a} stays on the list.",
    "Fine by me -- that is in.":
        "Fine by me -- the proposal to {a} is in.",
    # second bank
    "No, take that one off; we don't need it here.":
        "No, take the proposal to {a} off; we don't need it here.",
    "I'd leave that out; it is not needed this time.":
        "I'd leave the proposal to {a} out; it is not needed this time.",
    "Not that one -- drop it for this case.":
        "Not the proposal to {a} -- drop it for this case.",
    "Yes, keep it.":
        "Yes, keep the proposal to {a}.",
    "Agreed -- that stays in.":
        "Agreed -- the proposal to {a} stays in.",
    "Fine, that one is in.":
        "Fine, the proposal to {a} is in.",
}
assert set(EXPLICIT) == set(T_ACCEPT + T_REJECT + T_ACCEPT2 + T_REJECT2)


def explicit_dialogue(instance, dialogue):
    """The same (speaker, text, tag) triples with reply referents made explicit."""
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    out = []
    for speaker, text, tag in dialogue:
        if tag[0] == "reply":
            text = EXPLICIT[text].format(a=verbs[cid_action[tag[1]]])
        out.append((speaker, text, tag))
    return out


def store_tombstone(instance, dialogue):
    """Soft supersede on the oracle fact stream: ADD on proposal / noise /
    restate / neutral; UPDATE on acceptance; on rejection FLAG the proposal
    fact "[withdrawn]" and store nothing else; restatement ADDed fresh."""
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    store = []   # [cid_or_None, text]
    events = []
    for speaker, ev, cid, fact in facts_for(instance, dialogue):
        if ev in ("proposal", "noise", "restate", "neutral"):
            store.append([cid if ev == "proposal" else None, fact]); events.append(("ADD", fact))
        elif ev == "accept":
            for item in store:
                if item[0] == cid:
                    item[1] = f"{item[1][:-1]}; {speaker} accepted it."
                    events.append(("UPDATE", item[1]))
        elif ev == "reject":
            hit = False
            for item in store:
                if item[0] == cid and not item[1].startswith("[withdrawn] "):
                    item[1] = "[withdrawn] " + item[1]; hit = True
                    events.append(("FLAG", item[1]))
            if not hit:
                events.append(("NONE", fact))
    return [t for _, t in store], events


def context_block_x(design, instance, dialogue):
    if design == "full_explicit":
        lines = explicit_dialogue(instance, dialogue)
        return "DISCUSSION\n----------\n" + "\n".join(f"{s}: {t}" for s, t, _ in lines)
    if design == "tombstone":
        facts, _ = store_tombstone(instance, dialogue)
        return ("MEMORY NOTES FROM THE DISCUSSION\n"
                "-------------------------------\n" + "\n".join(f"- {f}" for f in facts))
    raise ValueError(design)
