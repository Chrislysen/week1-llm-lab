"""lineage_e29.py: E29 corpus -- a rejected proposal, later restated by its
proposer, delivered to the decider through four memory designs.

DECLARED in docs/protocols/E29-memory-semantics.md before any decider call.

THE QUESTION. E16/E18 measured revocation inertia with the raw transcript in
front of the decider. Deployed agents put a memory layer between the dialogue
and the decision, and the three designs actually shipped do different things
with a proposal that was later rejected. Does a partner's later RESTATEMENT of
the rejected step raise enactment, and by an amount that depends on the design?

    full      the transcript, as E17/E18 delivered it
    delete    write-time ADD/UPDATE/DELETE (Mem0 paper, arXiv:2504.19413):
              the rejection is consumed by a DELETE of the proposal and stores
              nothing itself; a later restatement contradicts nothing and is
              ADDed.  Source: DEFAULT_UPDATE_MEMORY_PROMPT, DELETE example.
    addonly   ADD-only, no recency ranking (Mem0 OSS v3, April 2026): every
              extracted fact is kept; proposal, rejection and restatement
              coexist.  Source: mem0/memory/main.py, "V3 PHASED BATCH PIPELINE".
    wiki      merge-in-place pages (Karpathy LLM-wiki pattern, nashsu/llm_wiki):
              one page per entity, "merge old + new instead of clobbering";
              contradictions are queued for a human and never resolved in the
              page.  Source: src/lib/ingest.ts, page-merge.ts.

ORACLE EXTRACTION. Stage 1 renders each design's store from the scorer's own
tags with a fixed template per event, so the store is the design's SEMANTIC
IDEAL: what the system would hold if its extractor never erred. What is
measured is therefore the decider's response to each design's store, not the
extractor's reliability. A real-extractor stage is a separate declaration.

CORPUS. The 96 E16 dialogues (hash 70f136a47f5779c8) that carry a `rejected`
slot. Each is rendered in two ARMS that differ in exactly one line, spoken by
the original proposer, placed as late as speaker alternation allows:

    restated   "For the record, I did raise {action phrase} earlier ..."
    neutral    the same sentence with a non-action referent of the same
               word count in place of the action phrase

The dialogue still ends on a noise line. When speaker alternation would give
the late slot to the other speaker, the line goes after the third noise line
and the domain's fourth (unused) noise line closes the dialogue instead; both
arms share the structure, so the arm contrast is always one line.
"""
import hashlib

from lineage_bench import DOMAINS, SPEAKERS
from lineage_e16 import N_NOISE, all_dialogues, build_dialogue, units_of

ARMS = ("restated", "neutral")
DESIGNS = ("full", "delete", "addonly", "wiki")
E16_HASH = "70f136a47f5779c8"

T_RESTATE = "For the record, I did raise {a} earlier in this discussion."

#: Neutral referents by word count, so the neutral line matches the restated
#: line word for word except the referent. None names an action or a domain.
NEUTRAL_BY_WORDS = {
    2: "the summary",
    3: "the written summary",
    4: "the written summary deadline",
    5: "the written summary for finance",
    6: "the written summary for finance today",
    7: "the written summary for the finance team",
    8: "the written summary for the finance team's review",
}


def _rejected_unit(units):
    for u in units:
        if u["status"] == "rejected":
            return u
    return None


def _unused_noise(instance, base):
    used = {t for _, t, tag in base if tag[0] == "noise"}
    rest = [n for n in DOMAINS[instance.domain]["noise"] if n not in used]
    assert len(rest) == len(DOMAINS[instance.domain]["noise"]) - N_NOISE
    return rest[0]


def build_arm(instance, rotation, arm):
    """One arm of one dialogue: list of (speaker, text, tag) like E16, plus
    one inserted line tagged ("restate", cid) or ("neutral", None)."""
    assert arm in ARMS
    base = build_dialogue(instance, rotation)
    units = units_of(instance, rotation)
    rej = _rejected_unit(units)
    assert rej is not None, "E29 uses only dialogues with a rejected slot"
    verbs = dict(DOMAINS[instance.domain]["actions"])
    phrase = verbs[rej["action"]]
    p = next(i for i, (_, _, tag) in enumerate(base)
             if tag == ("proposal", rej["constraint"]))

    n = len(base)
    if (n - 1 - p) % 2 == 0:
        insert_at, tail = n - 1, []
    else:
        insert_at, tail = n, [(_unused_noise(instance, base), ("noise", None))]

    if arm == "restated":
        text, tag = T_RESTATE.format(a=phrase), ("restate", rej["constraint"])
    else:
        k = len(phrase.split())
        text, tag = T_RESTATE.format(a=NEUTRAL_BY_WORDS[k]), ("neutral", None)

    flat = [(t, tag_) for _, t, tag_ in base]
    flat = flat[:insert_at] + [(text, tag)] + flat[insert_at:] + tail
    return [(SPEAKERS[i % 2], t, tg) for i, (t, tg) in enumerate(flat)]


def all_e29_dialogues(domains=None):
    """Every E16 dialogue with a rejected slot, both arms, in E16 order.
    `domains` selects the second corpus (E29-N); default: the frozen one."""
    out = []
    for d in all_dialogues(domains):
        if _rejected_unit(d["units"]) is None:
            continue
        inst, r = d["instance"], d["rotation"]
        out.append({"instance": inst, "rotation": r, "units": d["units"],
                    "arms": {a: build_arm(inst, r, a) for a in ARMS}})
    return out


# ---------------------------------------------------------------------------
# Oracle extraction: one fact per line, from the tags.

def facts_for(instance, dialogue):
    """(speaker, event, cid, fact_text) per line. `event` is the write-time
    event a faithful extractor would raise: proposal / accept / reject /
    noise / restate / neutral."""
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    out = []
    for speaker, text, tag in dialogue:
        kind, cid = tag
        if kind == "proposal":
            out.append((speaker, "proposal", cid,
                        f"{speaker} proposed to {verbs[cid_action[cid]]}."))
        elif kind == "reply":
            verb = verbs[cid_action[cid]]
            if text.startswith(("No", "Let's not")):
                out.append((speaker, "reject", cid,
                            f"{speaker} rejected the proposal to {verb}; "
                            "it is not needed for this case."))
            else:
                out.append((speaker, "accept", cid,
                            f"{speaker} accepted the proposal to {verb}."))
        elif kind == "noise":
            out.append((speaker, "noise", None, text))
        elif kind == "restate":
            out.append((speaker, "restate", cid,
                        f"{speaker} noted that {verbs[cid_action[cid]]} had "
                        "been raised earlier in the discussion."))
        elif kind == "neutral":
            ref = text[len("For the record, I did raise "):-len(" earlier in this discussion.")]
            out.append((speaker, "neutral", None,
                        f"{speaker} noted that {ref} had been raised earlier "
                        "in the discussion."))
        else:
            raise ValueError(kind)
    return out


def store_delete(instance, dialogue):
    """Mem0 paper semantics on the oracle fact stream.

    ADD on proposal / noise / restate / neutral. UPDATE the proposal fact on
    acceptance (same id, richer text). On rejection: DELETE the proposal fact
    and store nothing -- the prompt's DELETE example returns only the DELETE
    event, the contradicting fact is not added. A later restatement finds
    nothing to contradict and is ADDed.
    """
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    store = []  # list of [cid_or_None, text]; order = insertion order
    events = []
    for speaker, ev, cid, fact in facts_for(instance, dialogue):
        if ev in ("proposal", "noise", "restate", "neutral"):
            store.append([cid if ev == "proposal" else None, fact]); events.append(("ADD", fact))
        elif ev == "accept":
            for item in store:
                if item[0] == cid:
                    item[1] = (f"{item[1][:-1]}; {speaker} accepted it.")
                    events.append(("UPDATE", item[1]))
        elif ev == "reject":
            before = len(store)
            store = [item for item in store if item[0] != cid]
            events.append(("DELETE", f"proposal to {verbs[cid_action[cid]]}") if len(store) < before
                          else ("NONE", fact))
    return [t for _, t in store], events


def store_addonly(instance, dialogue):
    """Mem0 OSS v3 semantics: every fact ADDed, nothing updated or deleted,
    delivered in insertion order (the store is smaller than any top-k)."""
    facts = [f for _, _, _, f in facts_for(instance, dialogue)]
    return facts, [("ADD", f) for f in facts]


def store_wiki(instance, dialogue):
    """LLM-wiki semantics: one page per action mentioned, merged in place --
    every distinct claim survives, contradictions are left on the page for a
    human reviewer who never comes. Other lines go to a discussion-log page."""
    verbs = dict(DOMAINS[instance.domain]["actions"])
    cid_action = {c.id: c.a for c in instance.constraints}
    pages = {}   # title -> bullets, first-mention order
    order = []
    def page(title):
        if title not in pages:
            pages[title] = []; order.append(title)
        return pages[title]
    for speaker, ev, cid, fact in facts_for(instance, dialogue):
        if ev in ("proposal", "accept", "reject", "restate"):
            title = verbs[cid_action[cid]]
            line = {"proposal": f"proposed by {speaker}",
                    "accept": f"accepted by {speaker}",
                    "reject": f"rejected by {speaker}: not needed for this case",
                    "restate": f"noted again by {speaker}: raised earlier in the discussion"}[ev]
            page(title).append(line)
        else:
            page("discussion log").append(fact)
    rendered = []
    for title in order:
        rendered.append(f"## {title}\n" + "\n".join(f"- {b}" for b in pages[title]))
    return rendered, [("MERGE", t) for t in order]


def render_transcript(dialogue):
    return "\n".join(f"{s}: {t}" for s, t, _ in dialogue)


def store_timeline(design, instance, dialogue):
    """For each line k, the rendered store after lines[:k+1], as a list of
    strings (facts, pages, or transcript lines). Used by the X-ray replay;
    it recomputes the same store functions on each prefix, so it cannot
    drift from what the decider is given."""
    out = []
    for k in range(1, len(dialogue) + 1):
        part = dialogue[:k]
        if design == "full":
            out.append([f"{s}: {t}" for s, t, _ in part])
        elif design == "delete":
            out.append(store_delete(instance, part)[0])
        elif design == "addonly":
            out.append(store_addonly(instance, part)[0])
        elif design == "wiki":
            out.append(store_wiki(instance, part)[0])
        else:
            raise ValueError(design)
    return out


def context_block(design, instance, dialogue):
    """The block that replaces E17's DISCUSSION block for each design."""
    if design == "full":
        return "DISCUSSION\n----------\n" + render_transcript(dialogue)
    if design == "delete":
        facts, _ = store_delete(instance, dialogue)
        return ("MEMORY NOTES FROM THE DISCUSSION\n"
                "-------------------------------\n" + "\n".join(f"- {f}" for f in facts))
    if design == "addonly":
        facts, _ = store_addonly(instance, dialogue)
        return ("MEMORY NOTES FROM THE DISCUSSION\n"
                "-------------------------------\n" + "\n".join(f"- {f}" for f in facts))
    if design == "wiki":
        pages, _ = store_wiki(instance, dialogue)
        return ("WIKI PAGES BUILT FROM THE DISCUSSION\n"
                "------------------------------------\n" + "\n\n".join(pages))
    raise ValueError(design)


def corpus_hash(domains=None):
    parts = []
    for d in all_e29_dialogues(domains):
        for arm in ARMS:
            for design in DESIGNS:
                parts.append(f"{d['instance'].id}|{d['rotation']}|{arm}|{design}|"
                             + context_block(design, d["instance"], d["arms"][arm]))
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


if __name__ == "__main__":
    ds = all_e29_dialogues()
    print(f"=== E29 corpus: {len(ds)} dialogues x {len(ARMS)} arms x {len(DESIGNS)} designs ===")
    print(f"  hash {corpus_hash()}")
    d = ds[0]
    for arm in ARMS:
        print(f"\n--- {d['instance'].id} r{d['rotation']} [{arm}] ---")
        for design in DESIGNS:
            print(f"\n[{design}]\n{context_block(design, d['instance'], d['arms'][arm])}")
