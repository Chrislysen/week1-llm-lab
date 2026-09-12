"""lineage_e29s.py: E29-S corpus -- the 2x2 that isolates WHY a stored
rejection is honoured or ignored.

DECLARED in docs/protocols/E29S-structure.md before any decider call.

E29-E established two things and conflated a third. Re-wording a rejection
from a proposition to a key-value assertion, holding its line and position
fixed, changed nothing (+0.052, -0.115, -0.031 across three deciders).
Collapsing it onto the record it negates changed a great deal (+0.385,
+0.219, +0.292). But that collapse changed TWO things at once: the negation
stopped being a separate item AND stopped being a proposition.

The 2x2, over the same add-only fact stream:

                        own item                     same item as the proposal
    proposition    addonly                      addonly_merged   <-- MISSING
                   "- A proposed to X."         "- A proposed to X. B rejected
                   "- B rejected ... case."      the proposal to X; ... case."
    attribute      addonly_meta                 addonly_flag
                   "- status(X) = WITHDRAWN..." "- [withdrawn] A proposed to X."

`addonly` and `addonly_merged` contain **byte-identical text**. The only
difference is that one newline and one "- " are removed, so the two
propositions share a bullet instead of occupying two. Nothing else in either
store differs. If enactment moves across that pair, the operative variable is
item separation itself, not wording, not content, not length.
"""
from lineage_bench import DOMAINS
from lineage_e29 import facts_for
from lineage_e29e import FLAG, T_META

DESIGNS_S = ("addonly", "addonly_merged", "addonly_meta", "addonly_flag")


def store_s(design, instance, dialogue):
    """The add-only fact stream with the rejection re-structured."""
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    out, events, prop_at = [], [], {}
    for speaker, ev, cid, fact in facts_for(instance, dialogue):
        if ev == "proposal":
            prop_at[cid] = len(out)
            out.append(fact); events.append(("ADD", fact))
        elif ev == "reject":
            phrase = verbs[cid_action[cid]]
            i = prop_at.get(cid)
            if design == "addonly":
                out.append(fact); events.append(("ADD", fact))
            elif design == "addonly_merged":
                assert i is not None, "rejection before its proposal"
                out[i] = out[i] + " " + fact          # same text, one bullet
                events.append(("MERGE", out[i]))
            elif design == "addonly_meta":
                line = T_META.format(a=phrase)
                out.append(line); events.append(("ADD", line))
            elif design == "addonly_flag":
                assert i is not None, "rejection before its proposal"
                out[i] = FLAG + out[i]
                events.append(("FLAG", out[i]))
            else:
                raise ValueError(design)
        else:
            out.append(fact); events.append(("ADD", fact))
    return out, events


def context_block_s(design, instance, dialogue):
    facts, _ = store_s(design, instance, dialogue)
    return ("MEMORY NOTES FROM THE DISCUSSION\n"
            "-------------------------------\n" + "\n".join(f"- {f}" for f in facts))
