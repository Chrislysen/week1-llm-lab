"""lineage_e29c.py: E29-C corpus -- is the negative full-context restatement
effect the "for the record" framing, or any late mention of the rejected step?

DECLARED in docs/protocols/E29C-framing.md before any decider call.

E29 found, under the `full` design on both deciders, that the proposer's late
restatement LOWERED enactment of the rejected step relative to the neutral
line (llama3.2:3b 0.198 vs 0.281; qwen2.5:7b-instruct 0.240 vs 0.312). E29's
P3 predicted "small"; the sign was a miss. Two readings were left open:

    H-frame    "For the record, I did raise X earlier" is a dispute about
               authorship, not a request to do X; it sends the decider back to
               the exchange where X was rejected.
    H-mention  any late mention of a rejected step in a full transcript makes
               the rejection salient again, whatever the framing.

E29-C keeps E29's two lines and adds a second pair with a plain framing that
claims nothing and asks for nothing:

    restated        For the record, I did raise {action phrase} earlier in this discussion.
    neutral         For the record, I did raise {neutral referent} earlier in this discussion.
    plain           Just to note it, {action phrase} came up earlier in this discussion.
    plain_neutral   Just to note it, {neutral referent} came up earlier in this discussion.

Every line is 10 words plus the referent; the neutral referent has the action
phrase's word count (NEUTRAL_BY_WORDS, unchanged from E29). Same speaker
(the original proposer), same slot, same tail rule as E29; the `restated` and
`neutral` arms are byte-identical to E29's (a test asserts it). Design `full`
only: this is a question about the decider reading a transcript, not about a
store.
"""
import hashlib

from lineage_bench import DOMAINS, SPEAKERS
from lineage_e16 import all_dialogues, build_dialogue, units_of
from lineage_e29 import (NEUTRAL_BY_WORDS, T_RESTATE, _rejected_unit,
                         _unused_noise, build_arm)

ARMS_C = ("restated", "neutral", "plain", "plain_neutral")
T_PLAIN = "Just to note it, {a} came up earlier in this discussion."

#: arm -> (template, referent is the action phrase?)
TEMPLATES = {
    "restated": (T_RESTATE, True),
    "neutral": (T_RESTATE, False),
    "plain": (T_PLAIN, True),
    "plain_neutral": (T_PLAIN, False),
}


def build_arm_c(instance, rotation, arm):
    """E29's build_arm with a template per arm. Slot and tail rule identical."""
    assert arm in ARMS_C
    base = build_dialogue(instance, rotation)
    units = units_of(instance, rotation)
    rej = _rejected_unit(units)
    assert rej is not None, "E29-C uses only dialogues with a rejected slot"
    verbs = dict(DOMAINS[instance.domain]["actions"])
    phrase = verbs[rej["action"]]
    p = next(i for i, (_, _, tag) in enumerate(base)
             if tag == ("proposal", rej["constraint"]))

    n = len(base)
    if (n - 1 - p) % 2 == 0:
        insert_at, tail = n - 1, []
    else:
        insert_at, tail = n, [(_unused_noise(instance, base), ("noise", None))]

    template, is_action = TEMPLATES[arm]
    if is_action:
        text, tag = template.format(a=phrase), ("restate", rej["constraint"])
    else:
        k = len(phrase.split())
        text, tag = template.format(a=NEUTRAL_BY_WORDS[k]), ("neutral", None)

    flat = [(t, tag_) for _, t, tag_ in base]
    flat = flat[:insert_at] + [(text, tag)] + flat[insert_at:] + tail
    return [(SPEAKERS[i % 2], t, tg) for i, (t, tg) in enumerate(flat)]


def all_e29c_dialogues():
    """Every E16 dialogue with a rejected slot, all four arms, in E16 order."""
    out = []
    for d in all_dialogues():
        if _rejected_unit(d["units"]) is None:
            continue
        inst, r = d["instance"], d["rotation"]
        arms = {a: build_arm_c(inst, r, a) for a in ARMS_C}
        # E29's own two arms, byte for byte.
        for a in ("restated", "neutral"):
            assert arms[a] == build_arm(inst, r, a), (inst.id, r, a)
        out.append({"instance": inst, "rotation": r, "units": d["units"], "arms": arms})
    return out


def corpus_hash():
    parts = []
    for d in all_e29c_dialogues():
        for arm in ARMS_C:
            for sp, t, tag in d["arms"][arm]:
                parts.append(f"{d['instance'].id}|{d['rotation']}|{arm}|{sp}|{t}|{tag}")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]
