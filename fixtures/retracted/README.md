# Retracted Mode B corpus v1 (`modeb_v1_31of36.json`, hash 25e7307d1892914f)

Superseded before any decision call was made. No result was ever computed from
it, so nothing downstream is retracted with it — this is a discarded draft of an
instrument, kept because the reason it was discarded is informative.

**Why it was replaced.** Two of its gates contradicted each other. `_check_relay`
*requires* both action phrases in every relay; those phrases are most of the
content words in a one-sentence claim; so `_too_similar`'s ≤ 0.75 content-word
overlap limit asked the generator to name the same two actions without reusing
the words that name them. The generation log shows the collision precisely:

    109 of 311 attempts rejected
      58  length
      46  overlap          <- concentrated at L2/L3, where rewording room runs out
       5  missing action

    rejections by message:  L1 20   L2 35   L3 37   C 16   P2 1

Five instances died on it — `pharmacy-fork`, `satellite-diamond`,
`brewery-fork`, `rail-diamond`, `rail-twochain` — leaving 31/36. Dropping 14% of
a paired benchmark for a reason that has nothing to do with the phenomenon is a
selection effect, not an acceptable cost.

**What changed in v2.** Distinctness is now measured on *framing* words only,
with the two action phrases excluded from the comparison. It still catches
verbatim repeats (identical sentences have identical framing) while allowing a
relay to do the one thing it is required to do. `MAX_GEN_ATTEMPTS` 4 → 6, and
retries are seeded so the fixture is reproducible.

**Applied by regenerating everything.** Not by retrying only the five failures —
that would spend extra effort on exactly the instances that resisted, which is
selection dressed as persistence.
