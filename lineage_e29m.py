"""lineage_e29m.py: E29-M corpus -- does a read-time rewrite fix the tag?

DECLARED in docs/protocols/E29M-fix.md before any decider call.

E29-T showed that in-place revocation fields such as `[is_active: false]` and
`[invalid_at: ...]` are largely ignored, while the same rejection written as a
sentence is honoured. E29-M tests the fix a memory system could apply when it
renders its records into a prompt: turn the field into a sentence.

    sentence             E29-T's control (E29-S's add-only store), byte for byte
    is_active_false      E29-T's cell, byte for byte (anchor)
    invalid_at           E29-T's cell, byte for byte (anchor)
    rewrite              the flagged record without its field, followed by its own
                         item "The proposal to X was withdrawn." (the same store
                         whichever field it came from)
    annotate_is_active   the flagged record kept as it is, followed by that sentence
    annotate_invalid_at  the same for `[invalid_at: ...]`
"""
import re

from lineage_e29t import HEADER, store_t

CELLS = ("sentence", "is_active_false", "invalid_at", "rewrite", "annotate_is_active", "annotate_invalid_at")
FLAGS = {"is_active_false": " [is_active: false]", "invalid_at": " [invalid_at: 2026-09-12 10:04]"}
PROPOSAL = re.compile(r"^(?P<who>.+?) proposed to (?P<x>.+)\.$")


def withdrawn_sentence(record):
    """The sentence the fix writes for a revoked proposal record."""
    m = PROPOSAL.match(record)
    if not m:
        raise ValueError(f"not a proposal record: {record!r}")
    return f"The proposal to {m.group('x')} was withdrawn."


def rewrite_revocations(items, flag):
    """Read-time fix: a record carrying `flag` loses it and is followed by a sentence."""
    out = []
    for it in items:
        if it.endswith(flag):
            base = it[: -len(flag)]
            out += [base, withdrawn_sentence(base)]
        else:
            out.append(it)
    return out


def annotate_revocations(items, flag):
    """Weaker fix: keep the flagged record as it is and add the sentence after it."""
    out = []
    for it in items:
        out.append(it)
        if it.endswith(flag):
            out.append(withdrawn_sentence(it[: -len(flag)]))
    return out


def store_m(cell, instance, dialogue):
    if cell in ("sentence", "is_active_false", "invalid_at"):
        return store_t(cell, instance, dialogue)
    if cell == "rewrite":
        return rewrite_revocations(store_t("is_active_false", instance, dialogue), FLAGS["is_active_false"])
    if cell == "annotate_is_active":
        return annotate_revocations(store_t("is_active_false", instance, dialogue), FLAGS["is_active_false"])
    if cell == "annotate_invalid_at":
        return annotate_revocations(store_t("invalid_at", instance, dialogue), FLAGS["invalid_at"])
    raise ValueError(cell)


def context_block_m(cell, instance, dialogue):
    return HEADER + "\n".join(f"- {x}" for x in store_m(cell, instance, dialogue))
