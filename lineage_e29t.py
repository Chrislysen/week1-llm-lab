"""lineage_e29t.py: E29-T corpus -- do the revocation idioms shipped systems use
fail the way E29-S's `[withdrawn]` tag does?

DECLARED in docs/protocols/E29T-idioms.md before any decider call.

E29-S found that a rejection is ignored when it is BOTH written onto the record
it rejects AND verb-less. Its tag was one spelling, `[withdrawn] `. Shipped
memory systems and tool registries mark revocation with other in-place idioms:
a status label, a boolean flag, an invalidation timestamp, strikethrough. Each
cell below keeps E29-S's add-only fact stream and puts one idiom on the
rejected proposal's own item, with nothing else recording the rejection. The
control is E29-S's `addonly` store (the rejection as its own sentence).

    sentence          - A proposed to X.  /  - B rejected the proposal to X; ...
    withdrawn_prefix  - [withdrawn] A proposed to X.          (E29-S's tag, the anchor)
    withdrawn_suffix  - A proposed to X. (withdrawn)
    status_revoked    - A proposed to X. [status: revoked]
    is_active_false   - A proposed to X. [is_active: false]
    invalid_at        - A proposed to X. [invalid_at: 2026-09-12 10:04]
    strikethrough     - ~~A proposed to X.~~
"""
from lineage_e29s import store_s

IDIOMS = ("sentence", "withdrawn_prefix", "withdrawn_suffix", "status_revoked",
          "is_active_false", "invalid_at", "strikethrough")
REAL_WORLD = ("withdrawn_suffix", "status_revoked", "is_active_false", "invalid_at", "strikethrough")
HEADER = ("MEMORY NOTES FROM THE DISCUSSION\n"
          "-------------------------------\n")


def _mark(idiom, item):
    if idiom == "withdrawn_prefix":
        return "[withdrawn] " + item
    if idiom == "withdrawn_suffix":
        return item + " (withdrawn)"
    if idiom == "status_revoked":
        return item + " [status: revoked]"
    if idiom == "is_active_false":
        return item + " [is_active: false]"
    if idiom == "invalid_at":
        return item + " [invalid_at: 2026-09-12 10:04]"
    if idiom == "strikethrough":
        return "~~" + item + "~~"
    raise ValueError(idiom)


def store_t(idiom, instance, dialogue):
    """E29-S's add-only stream with the rejection written as one idiom."""
    if idiom == "sentence":
        return store_s("addonly", instance, dialogue)[0]
    # E29-S's flag store tells us which item is the rejected proposal and that the
    # rejection line is gone; re-mark that item with this idiom instead of "[withdrawn] ".
    flagged = store_s("addonly_flag", instance, dialogue)[0]
    out = []
    for item in flagged:
        out.append(_mark(idiom, item[len("[withdrawn] "):]) if item.startswith("[withdrawn] ") else item)
    return out


def context_block_t(idiom, instance, dialogue):
    return HEADER + "\n".join(f"- {x}" for x in store_t(idiom, instance, dialogue))
