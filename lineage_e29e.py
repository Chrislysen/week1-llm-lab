"""lineage_e29e.py: E29-E corpus -- does the ENCODING of a rejection decide
whether a superseded step comes back, with the store's length held fixed?

DECLARED in docs/protocols/E29E-encoding.md before any decider call.

WHY. E29-X compared add-only (rejection stored as a sentence) with a
tombstone store (rejection stored as a "[withdrawn]" prefix) and found a large
enactment gap. That comparison is confounded: add-only holds 8.28 lines on
average and the tombstone store 6.66, because add-only also keeps each
acceptance as its own fact. The gap could be the wording or it could be the
length. Concurrent work (arXiv:2609.08258) shows a flagged revocation is not
enforced, but has no prose-rejection arm, so it cannot separate the two
either.

THE ISOLATION. All three designs here are add-only stores over the same
oracle fact stream. They differ only in how the rejection of the rejected
proposal is written:

    addonly        the rejection as a sentence, exactly as E29 stored it:
                   "{B} rejected the proposal to {phrase}; it is not needed
                    for this case."
    addonly_meta   the SAME LINE COUNT, the SAME POSITION and the same
                   trailing clause, with the negation expressed as a
                   key-value assertion instead of a verb phrase:
                   "status({phrase}) = WITHDRAWN; it is not needed for this
                    case."
    addonly_flag   the rejection line REMOVED and the proposal it negates
                   prefixed "[withdrawn] ", i.e. one line fewer -- the
                   tombstone encoding carried on an add-only store.

`addonly` vs `addonly_meta` isolates the wording at constant line count and
position. `addonly_meta` vs `addonly_flag` isolates the extra line with the
wording already metadata-like. Every other line in all three stores is
byte-identical, and the header is E29's.
"""
from lineage_bench import DOMAINS
from lineage_e29 import facts_for

DESIGNS_E = ("addonly", "addonly_meta", "addonly_flag")

T_META = "status({a}) = WITHDRAWN; it is not needed for this case."
FLAG = "[withdrawn] "


def _rejected_cid(instance, dialogue):
    for _, ev, cid, _ in facts_for(instance, dialogue):
        if ev == "reject":
            return cid
    return None


def store_e(design, instance, dialogue):
    """The add-only fact stream with the rejection re-encoded. Returns
    (lines, events) like the E29 stores."""
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    out, events = [], []
    # index of the proposal line for each constraint, so the flag can find it
    prop_at = {}
    for speaker, ev, cid, fact in facts_for(instance, dialogue):
        if ev == "proposal":
            prop_at[cid] = len(out)
            out.append(fact); events.append(("ADD", fact))
        elif ev == "reject":
            phrase = verbs[cid_action[cid]]
            if design == "addonly":
                out.append(fact); events.append(("ADD", fact))
            elif design == "addonly_meta":
                line = T_META.format(a=phrase)
                out.append(line); events.append(("ADD", line))
            elif design == "addonly_flag":
                i = prop_at.get(cid)
                assert i is not None, "rejection before its proposal"
                out[i] = FLAG + out[i]
                events.append(("FLAG", out[i]))
            else:
                raise ValueError(design)
        else:
            out.append(fact); events.append(("ADD", fact))
    return out, events


def context_block_e(design, instance, dialogue):
    facts, _ = store_e(design, instance, dialogue)
    return ("MEMORY NOTES FROM THE DISCUSSION\n"
            "-------------------------------\n" + "\n".join(f"- {f}" for f in facts))
