"""lineage_e29o.py: E29-O corpus -- why does a revocation marker work after a record and not before it?

DECLARED in docs/protocols/E29O-order.md before any decider call.

E29-A: a bracketed revocation placed before the proposal text is under-applied, and the same
marker after the text is honoured, whatever the bracket. The cells below separate the
accounts in the protocol's prediction table: narrative order (NARR), last mention (REC),
attachment direction (BIND), a self-contained clause (CLAUSE), the marker's distance to the
step's name (PROX), and field form (META).

Corpus: E29's first and second corpora, 192 dialogues. Main block: the add-only stream with
the rejected proposal re-rendered as below, and the fixed atemporal item N inserted directly
before it, so the record never opens the list and always follows the same item. The rejection
is recorded once and nowhere else (`open` records none: X is then undecided, the ceiling).
A is the proposer, B the rejector, X the rejected step, Xc the step with a capital letter.

    open             - N  - A proposed to X.
    sentence_short   - N  - A proposed to X.  - B rejected the proposal to X.
    withdrawn_pre    - N  - [withdrawn] A proposed to X.
    withdrawn_post   - N  - A proposed to X. [withdrawn]
    later_pre        - N  - [subsequently withdrawn] A proposed to X.
    later_post       - N  - A proposed to X. [subsequently withdrawn]
    formally_pre     - N  - [formally withdrawn] A proposed to X.
    named_pre        - N  - [B rejected the proposal to X] A proposed to X.
    named_post       - N  - A proposed to X. [B rejected the proposal to X]
    label_pre        - N  - [withdrawn: X] A proposed to X.
    label_post       - N  - A proposed to X. [withdrawn: X]
    clause_pre       - N  - [B rejected the proposal] A proposed to X.
    clause_post      - N  - A proposed to X. [B rejected the proposal]
    xfirst_pre       - N  - [withdrawn] Xc (proposed by A).
    xfirst_post      - N  - Xc (proposed by A). [withdrawn]
    field_pre        - N  - [status: withdrawn] A proposed to X.
    field_post       - N  - A proposed to X. [status: withdrawn]

Top block: the same items, but the record moved to the top of the list; N stays where the
record was.

    first_sentence   - A proposed to X.  - B rejected the proposal to X.  ...  - N  ...
    first_pre        - [withdrawn] A proposed to X.  ...  - N  ...
    first_post       - A proposed to X. [withdrawn]  ...  - N  ...
"""
from lineage_bench import NEW_DOMAINS
from lineage_e29 import all_e29_dialogues, corpus_hash
from lineage_e29a import _parts
from lineage_e29t import HEADER

NEUTRAL = "The team's office is on the third floor."
CELLS = ("open", "sentence_short", "withdrawn_pre", "withdrawn_post", "later_pre", "later_post",
         "formally_pre", "named_pre", "named_post", "label_pre", "label_post", "clause_pre", "clause_post",
         "xfirst_pre", "xfirst_post", "field_pre", "field_post", "first_sentence", "first_pre", "first_post")
TOP = {"first_sentence": "sentence_short", "first_pre": "withdrawn_pre", "first_post": "withdrawn_post"}
CORPUS_HASHES = ("187a426616f26598", "e965c5fd022d6e37")      # E29's first and second corpora


def dialogues():
    """E29's two corpora, first then second: 192 dialogues with disjoint instance ids."""
    return all_e29_dialogues() + all_e29_dialogues(NEW_DOMAINS)


def corpora_ok():
    return (corpus_hash(), corpus_hash(NEW_DOMAINS)) == CORPUS_HASHES


def _record(cell, prop, a, b, x):
    """The items standing for the rejected proposal in `cell`."""
    if cell == "open":
        return [prop]
    if cell == "sentence_short":
        return [prop, f"{b} rejected the proposal to {x}."]
    kind, where = cell.rsplit("_", 1)
    body = f"{x[0].upper()}{x[1:]} (proposed by {a})." if kind == "xfirst" else prop
    mark = {"withdrawn": "[withdrawn]", "later": "[subsequently withdrawn]", "formally": "[formally withdrawn]",
            "named": f"[{b} rejected the proposal to {x}]", "label": f"[withdrawn: {x}]",
            "clause": f"[{b} rejected the proposal]", "xfirst": "[withdrawn]", "field": "[status: withdrawn]"}[kind]
    return [f"{mark} {body}"] if where == "pre" else [f"{body} {mark}"]


def store_o(cell, instance, dialogue):
    items, p, r, a, b, x = _parts(instance, dialogue)
    rest = items[:p] + items[r + 1:]       # the stream without the proposal and the rejection
    if cell in TOP:
        return _record(TOP[cell], items[p], a, b, x) + rest[:p] + [NEUTRAL] + rest[p:]
    return rest[:p] + [NEUTRAL] + _record(cell, items[p], a, b, x) + rest[p:]


def context_block_o(cell, instance, dialogue):
    return HEADER + "\n".join(f"- {x}" for x in store_o(cell, instance, dialogue))
