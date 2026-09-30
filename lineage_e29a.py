"""lineage_e29a.py: E29-A corpus -- attachment, the verb, or at-issueness?

DECLARED in docs/protocols/E29A-at-issue.md before any decider call.

E29-S found that of four renderings of a rejection only the `[withdrawn]` tag on the
proposal fails. Its separated status line kept a reason clause with a finite verb
("it is not needed for this case"), so E29-S cannot tell attachment to the record
apart from the plain absence of a verb. E29-A adds a truly verb-less line in its own
item (the headline), a sentence-medial appositive-versus-main-clause pair for the
at-issue account, and cells that settle E29-T's "(withdrawn)" exception.

Every cell is E29-S's add-only fact stream. The rejection is recorded once, as below,
and nowhere else. A is the proposer, B the rejector named in E29-S's own rejection
sentence, X the rejected step.

    sentence          - A proposed to X.  - B rejected the proposal to X; <reason>     (E29-S addonly)
    sentence_short    - A proposed to X.  - B rejected the proposal to X.
    status_long       - A proposed to X.  - status(X) = WITHDRAWN; <reason>           (E29-S addonly_meta)
    status_short      - A proposed to X.  - status(X) = WITHDRAWN.
    tag_prefix        - [withdrawn] A proposed to X.                                    (E29-S addonly_flag)
    tag_suffix        - A proposed to X. [withdrawn]
    paren_prefix      - (withdrawn) A proposed to X.
    paren_suffix      - A proposed to X. (withdrawn)                                    (E29-T withdrawn_suffix)
    verbal_tag        - [B rejected this] A proposed to X.
    arc_medial        - A's proposal, which was rejected by B, was to X.
    main_medial       - A's proposal was rejected by B; it was to X.
    appositive        - A proposed to X, a proposal that B rejected.
    coordination      - A proposed to X, and B rejected the proposal.
    parenthetical     - A proposed to X. (B rejected this.)
    bare_second       - A proposed to X. B rejected this.
"""
import re

from lineage_e29s import store_s
from lineage_e29t import HEADER

CELLS = ("sentence", "sentence_short", "status_long", "status_short", "tag_prefix", "tag_suffix",
         "paren_prefix", "paren_suffix", "verbal_tag", "arc_medial", "main_medial", "appositive",
         "coordination", "parenthetical", "bare_second")
REJ = re.compile(r"^(?P<b>.+?) rejected the proposal to (?P<x>.+?); .+$")
PROPOSAL = re.compile(r"^(?P<a>.+?) proposed to (?P<x>.+)\.$")


def _parts(instance, dialogue):
    """The add-only store, the proposal's and the rejection's indexes, and A, B, X."""
    items = store_s("addonly", instance, dialogue)[0]
    r = next(k for k, x in enumerate(items) if REJ.match(x))
    m = REJ.match(items[r])
    p = r - 1
    pm = PROPOSAL.match(items[p])
    assert pm and pm.group("x") == m.group("x"), "the rejection must directly follow its proposal"
    return items, p, r, pm.group("a"), m.group("b"), m.group("x")


def store_a(cell, instance, dialogue):
    items, p, r, a, b, x = _parts(instance, dialogue)
    if cell == "sentence":
        return list(items)
    if cell == "status_long":
        return list(store_s("addonly_meta", instance, dialogue)[0])
    prop = items[p]
    base = prop[:-1]                       # "A proposed to X" without the final full stop
    rest = items[:p] + items[r + 1:]       # the stream without the proposal and the rejection
    new = {
        "sentence_short": [prop, f"{b} rejected the proposal to {x}."],
        "status_short": [prop, f"status({x}) = WITHDRAWN."],
        "tag_prefix": [f"[withdrawn] {prop}"],
        "tag_suffix": [f"{prop} [withdrawn]"],
        "paren_prefix": [f"(withdrawn) {prop}"],
        "paren_suffix": [f"{prop} (withdrawn)"],
        "verbal_tag": [f"[{b} rejected this] {prop}"],
        "arc_medial": [f"{a}'s proposal, which was rejected by {b}, was to {x}."],
        "main_medial": [f"{a}'s proposal was rejected by {b}; it was to {x}."],
        "appositive": [f"{base}, a proposal that {b} rejected."],
        "coordination": [f"{base}, and {b} rejected the proposal."],
        "parenthetical": [f"{prop} ({b} rejected this.)"],
        "bare_second": [f"{prop} {b} rejected this."],
    }[cell]
    return rest[:p] + new + rest[p:]


def context_block_a(cell, instance, dialogue):
    return HEADER + "\n".join(f"- {x}" for x in store_a(cell, instance, dialogue))
