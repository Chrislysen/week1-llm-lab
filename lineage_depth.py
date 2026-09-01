"""lineage_depth.py: relay depth. Does a distortion travel further than one hop?

Roadmap stage 5, and the one thing besides the instrument that the prior-art
scan could not place: "source bias compares POPULATIONS of texts; nothing found
compares a specific restatement to its own specific parent, or treats
derivation-chain depth as an independent variable."

CONSTRUCTION. For one constraint of a base instance we build two parallel
chains off the same SOURCE:

    faithful   S -> L1 -> L2 -> L3      each link restates the one before it
    corrupted  S -> C1,  L1 -> C2,  L2 -> C3

C_k is a distortion introduced at depth k -- it inverts the ordering, exactly as
the base benchmark's CORRUPTED_RELAY does -- and it always derives from the
faithful link at depth k-1. So the same distortion appears at three different
distances from the authoritative source, with the intervening links agreeing
with the source at every step.

DEPTH IS AN EXPOSURE VARIABLE, NOT A CORPUS VARIABLE. The instance, its
constraints and its ground truth are identical at every depth; only which
messages are shown changes. That keeps ground truth fixed across the comparison.

    depth 1   S + C1
    depth 2   S + L1 + C2
    depth 3   S + L1 + L2 + C3
    control   S + L1 + L2 + L3      no corruption, same message count as depth 3

The control matters: message count grows with depth, so without it a depth
effect cannot be told apart from a context-length effect.

Nothing here modifies lineage_bench. The base corpus stays as tagged.
"""
import random
from dataclasses import dataclass

from lineage_bench import (DOMAINS, Message, SPEAKERS, T_REVISION, _cap, _phr,
                           _seed_for)

MAX_DEPTH = 3

#: Faithful restatements. Deliberately NOT the T_REVISION pool -- a faithful
#: link agrees with its parent, it does not assert a revision.
T_LINK = [
    "So the order stands: we {a}, and only then {b}.",
    "Confirming the dependency -- {a} first, {b} after.",
    "Right, {b} waits until we {a}.",
    "Understood: {a} comes before {b}.",
]


@dataclass(frozen=True)
class DepthChain:
    """Both chains for one constraint of one instance."""
    instance_id: str
    constraint_id: str
    source: Message
    faithful: tuple          # L1..L3
    corrupted: tuple         # C1..C3, C_k derives from L_{k-1} (S when k == 1)
    padding: tuple = ()      # constraint-irrelevant filler, for the count control

    def padded(self, n_pad: int):
        """S + n_pad DISTRACTORS + C1.

        THE CONTROL THAT SEPARATES CORROBORATION FROM CONTEXT LENGTH. At depth 1
        the corruption is 1 of 2 messages; at depth 3 it is 1 of 4. So a drop in
        adoption from d1 to d3 could be faithful restatements inoculating
        against the contradiction, or it could just be dilution by more text.
        This arm holds message count and corruption position at the d3 values
        while replacing the faithful links with irrelevant filler. If adoption
        stays at the d1 level, corroboration is doing the work; if it falls to
        the d3 level, message count is.
        """
        return ([self.source] + list(self.padding[:n_pad])
                + [self.corrupted[0]])

    def exposure(self, depth: int, corrupt: bool = True):
        """Messages a model sees at this depth. Source first, chain in order."""
        if not 1 <= depth <= MAX_DEPTH:
            raise ValueError(f"depth must be 1..{MAX_DEPTH}, got {depth}")
        links = list(self.faithful[:depth - 1])
        tail = self.corrupted[depth - 1] if corrupt else self.faithful[depth - 1]
        return [self.source] + links + [tail]


def _fill(template, c, verbs):
    a, b = verbs[c.a], verbs[c.b]
    return template.format(a=_phr(a), A=_cap(a), b=_phr(b), B=_cap(b))


def build_chain(instance, constraint_id=None):
    """Build the depth chains for `instance`.

    Uses a chain-specific RNG stream so it cannot disturb the base corpus, and
    targets a `before` constraint -- an ordering is what a corruption inverts.
    """
    cmap = {c.id: c for c in instance.constraints}
    if constraint_id is None:
        # The constraint the base instance already corrupts, when it is an
        # ordering; otherwise the first ordering that is not the overridden one.
        cand = [m.constraint_id for m in instance.by_lineage("CORRUPTED_RELAY")
                if cmap[m.constraint_id].kind == "before"
                and m.constraint_id not in instance.superseded]
        if not cand:
            cand = [c.id for c in instance.constraints
                    if c.kind == "before" and c.id not in instance.superseded]
        constraint_id = cand[0]

    c = cmap[constraint_id]
    verbs = dict(DOMAINS[instance.domain]["actions"])
    rng = random.Random(_seed_for(instance.domain, instance.graph) ^ 0x5EED)

    src = next(m for m in instance.messages
               if m.lineage == "SOURCE" and m.constraint_id == constraint_id)

    # TWO CONFOUNDS THIS AVOIDS, both found by reading the generated text:
    #
    # 1. Drawing faithful links WITH replacement produced verbatim-identical
    #    consecutive links at depth 3. That is a repetition effect -- repeated
    #    assertion is known to shift LLM source preference (arXiv:2601.03746) --
    #    and it would masquerade as a depth effect. Links are sampled WITHOUT
    #    replacement, so every link is a distinct paraphrase.
    #
    # 2. Drawing the corrupted terminal per depth gave each depth a DIFFERENT
    #    corruption wording, confounding depth with phrasing. Exactly one
    #    corrupted message is ever shown, so the same template is reused at
    #    every depth and only its distance from the source varies.
    link_templates = rng.sample(T_LINK, MAX_DEPTH)
    corrupt_template = rng.choice(T_REVISION)
    corrupt_text = _fill(corrupt_template, c, verbs)

    faithful, corrupted = [], []
    prev = src
    for k in range(1, MAX_DEPTH + 1):
        # C_k first, so it derives from the link at depth k-1, not from L_k.
        corrupted.append(Message(
            msg_id=10_000 + k * 2, speaker=SPEAKERS[k % 2],
            text=corrupt_text,
            lineage="CORRUPTED_RELAY", constraint_id=constraint_id,
            derives_from=(prev.msg_id,), faithful=False))
        link = Message(
            msg_id=10_001 + k * 2, speaker=SPEAKERS[(k + 1) % 2],
            text=_fill(link_templates[k - 1], c, verbs),
            lineage="FAITHFUL_RELAY", constraint_id=constraint_id,
            derives_from=(prev.msg_id,), faithful=True)
        faithful.append(link)
        prev = link

    # Filler drawn from the instance's own distractors, so it is on-topic for
    # the domain and constraint-irrelevant by construction.
    pad = [m for m in instance.messages if m.lineage == "DISTRACTOR"]
    while len(pad) < MAX_DEPTH - 1:
        pad = pad + pad
    return DepthChain(instance_id=instance.id, constraint_id=constraint_id,
                      source=src, faithful=tuple(faithful),
                      corrupted=tuple(corrupted),
                      padding=tuple(pad[:MAX_DEPTH - 1]))


def corrupted_target(instance, chain):
    """The constraint as the corruption asserts it: the reversed ordering."""
    c = {x.id: x for x in instance.constraints}[chain.constraint_id]
    return type(c)(id=c.id, kind="before", a=c.b, b=c.a)


def follows_corruption(instance, chain, actions):
    """Did the plan adopt the distortion rather than the source's ordering?"""
    from lineage_eval import obeys
    c = {x.id: x for x in instance.constraints}[chain.constraint_id]
    alt = corrupted_target(instance, chain)
    src_ok, cor_ok = obeys(c, actions), obeys(alt, actions)
    if src_ok and not cor_ok:
        return "source"
    if cor_ok and not src_ok:
        return "corruption"
    return "neither"
