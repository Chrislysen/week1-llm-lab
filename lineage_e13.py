"""lineage_e13.py: E13 arms -- routing recognised dependence into the decision.

Protocol: docs/protocols/E13-recognition-utilization-v1.md.

THE QUESTION. E12 established that the model prices k reports from ONE evidential
root exactly as it prices k INDEPENDENT roots (difference +0.0185, cluster CI
[-0.037, +0.074], inside the preregistered SESOI of 0.10) -- while a frozen probe
shows it can *report* the difference (27/36 vs 0/36, p = 1.5e-08). E13 asks what,
if anything, makes that recognition govern the decision.

MATERIALS ARE E12'S, UNMUTATED. Every unit, every message, every speaker and the
byte-identical contradiction come from `lineage_e12.all_units()`. E13 changes
ONLY the instruction appended after the discussion and the JSON shape requested.
A gate asserts E12's corpus hash still reproduces.

THE ARMS, and what each is for:

    DEFAULT   E12's instruction verbatim. Replicates the null. No recognition
              is requested, which is the condition the dissociation is about.
    IDENTIFY  same, plus a required machine-parseable assessment of the evidence
              structure BEFORE the plan. The model is never told the answer.
    NORMATIVE IDENTIFY plus one frozen sentence of normative principle.
    SHAM      matched structured-output burden -- one boolean, one integer, then
              the plan -- about a TASK-IRRELEVANT property. If IDENTIFY moves
              behaviour and SHAM moves it equally, the cause is the output
              burden, not the dependence reasoning.
    GOLD      DEFAULT plus the CORRECT structure stated outright. DIAGNOSTIC
              ONLY, never pooled: if even handing the model the right answer
              leaves behaviour unchanged, the failure is utilisation, not
              recognition.

WHY NO REPORT LABELS. An earlier draft numbered the support messages [R1], [R2]
so grouping would be easy to express. That would have changed the DISCUSSION
text, so DEFAULT would no longer be E12's condition and the replication would be
worthless. Recognition is therefore requested as a boolean plus a count, both of
which are answerable without labels, and the discussion text stays byte-identical
across every arm.
"""
import hashlib

from lineage_e12 import ARMS as E12_ARMS
from lineage_e12 import all_units, exposure, render

#: (arm, requests_recognition, is_diagnostic)
INTERVENTIONS = [
    ("default", False, False),
    ("identify", True, False),
    ("normative", True, False),
    ("sham", False, False),
    ("gold", False, True),
]
N_INTERVENTIONS = 5

#: The two dependence levels, reusing E12's exposures by name.
DEPENDENCE = ["same_root", "indep_root"]

#: Diagnostic arms are NEVER pooled with the rest.
DIAGNOSTIC = {a for a, _, d in INTERVENTIONS if d}
RECOGNITION_ARMS = {a for a, r, _ in INTERVENTIONS if r}

#: Frozen. Quoted verbatim in NORMATIVE and nowhere else.
NORMATIVE_PRINCIPLE = (
    "Multiple reports derived from the same underlying evidence should not be "
    "treated as multiple independent confirmations. Distinct independent "
    "evidence may provide additional corroborative weight.")

_PLAN_KEYS = ('"actions", a list of action identifier strings, and "ready", '
              'true or false')

#: Each override RESTATES the full four-key shape, because it is appended after
#: the frozen `plan_instruction` whose Format line shows only two keys. Stating
#: "this overrides the format above" is what stops the model being handed a
#: contradiction in the very arms under test.
_ASSESS = (
    "\n\nIMPORTANT -- this overrides the Format line above. Before deciding the "
    "plan, assess the structure of the supporting evidence in the discussion. "
    "Reply with ONE JSON object having exactly these four keys, in this order: "
    '"same_underlying_source" (true if the supporting reports all trace back to '
    "the same underlying record, false if they trace to different ones), "
    '"independent_source_count" (how many distinct underlying records the '
    'support rests on, an integer), then "actions" and "ready" exactly as '
    "described above.")

#: Matched to `_ASSESS` in shape and burden -- one boolean, one integer, then
#: the plan -- but about a property with no bearing on evidential structure.
_SHAM = (
    "\n\nIMPORTANT -- this overrides the Format line above. Before deciding the "
    "plan, note two surface details of the discussion. Reply with ONE JSON "
    "object having exactly these four keys, in this order: "
    '"mentions_a_clock_time" (true if any message above states a time of day '
    'such as an hour on the clock, false if none of them does), '
    '"longest_message_word_count" (how many words are in the single longest '
    'message above, an integer), then "actions" and "ready" exactly as '
    "described above.")

INSTRUCTIONS = {
    "default": "",
    "identify": _ASSESS,
    "normative": "\n\n" + NORMATIVE_PRINCIPLE + _ASSESS,
    "sham": _SHAM,
    "gold": "",
}

#: Recognition keys per arm, in the order the model must emit them.
RECOG_KEYS = {
    "identify": ("same_underlying_source", "independent_source_count"),
    "normative": ("same_underlying_source", "independent_source_count"),
    "sham": ("mentions_a_clock_time", "longest_message_word_count"),
}


def gold_note(dependence):
    """The correct structure, stated outright. GOLD only.

    Deliberately phrased WITHOUT the benchmark's vocabulary -- no `SAME_ROOT`,
    no `lineage`, no basis names -- so it supplies the structural fact and not a
    label the model could pattern-match to the arm.
    """
    if dependence == "same_root":
        return ("\n\nFor reference: the supporting reports above all draw on "
                "the same single underlying record.")
    return ("\n\nFor reference: the supporting reports above each draw on a "
            "different underlying record.")


def expected_recognition(dependence):
    """Ground truth for the recognition probe. Never shown to the model."""
    if dependence == "same_root":
        return {"same_underlying_source": True, "independent_source_count": 1}
    return {"same_underlying_source": False, "independent_source_count": 3}


def build_prompt(rec, dependence, intervention, plan_instruction):
    """The user message. Discussion text is E12's, byte for byte.

    ORDERING MATTERS AND THE FIRST DRAFT GOT IT WRONG. The frozen
    `plan_instruction` ends with `Format: {"actions": [...], "ready": true}`.
    Putting the four-key requirement BEFORE it meant the model was told to emit
    four keys and then immediately shown a two-key format -- a contradiction
    that would have depressed parse rates in exactly the arms under test and
    looked like an intervention effect.

    So the intervention instruction now comes LAST, where it overrides, and
    `default` appends nothing at all -- making its prompt byte-identical to
    E12's, which is what makes RQ2 a real replication rather than a near one.

    GOLD is the exception: its note is EVIDENCE, not an output instruction, so
    it sits with the discussion. GOLD is diagnostic-only and never pooled, and
    that structural difference is recorded rather than hidden.
    """
    body = render(exposure(rec, dependence))
    if intervention == "gold":
        return (f"DISCUSSION\n----------\n{body}{gold_note(dependence)}"
                f"\n\n{plan_instruction}")
    return (f"DISCUSSION\n----------\n{body}\n\n{plan_instruction}"
            f"{INSTRUCTIONS[intervention]}")


def schema_hint(intervention):
    """What `ask_structured` tells the model on a parse failure."""
    keys = RECOG_KEYS.get(intervention)
    if not keys:
        return f"It must have exactly two keys: {_PLAN_KEYS}."
    return (f'It must have exactly four keys: "{keys[0]}" (true or false), '
            f'"{keys[1]}" (an integer), and then {_PLAN_KEYS}.')


def cells():
    """Every (intervention, dependence) cell, diagnostic ones included."""
    return [(a, d) for a, _, _ in INTERVENTIONS for d in DEPENDENCE]


def corpus_hash(plan_instruction_fn):
    """Hashes every rendered PROMPT, so a wording change is detectable."""
    from lineage_bench import all_instances
    by_id = {i.id: i for i in all_instances()}
    parts = []
    for rec in all_units():
        pi = plan_instruction_fn(by_id[rec["instance"]])
        for arm, dep in cells():
            parts.append(f"{rec['unit']}|{arm}|{dep}|"
                         f"{build_prompt(rec, dep, arm, pi)}")
    return hashlib.sha256("␟".join(parts).encode()).hexdigest()[:16]


if __name__ == "__main__":
    from lineage_bench import all_instances, plan_instruction
    by_id = {i.id: i for i in all_instances()}
    units = all_units()
    print(f"=== E13: {len(units)} units x {len(cells())} cells "
          f"({N_INTERVENTIONS} interventions x 2 dependence) ===")
    print(f"  {len(units) * len(cells())} decider calls per model")
    print(f"  prompt-corpus hash {corpus_hash(plan_instruction)}\n")
    u = units[0]
    pi = plan_instruction(by_id[u["instance"]])
    for arm in ("default", "identify", "normative", "sham", "gold"):
        p = build_prompt(u, "same_root", arm, pi)
        tail = p.split("----------\n")[1]
        print(f"--- {arm} (same_root) --- {len(p.split())} words")
        print("    ..." + tail[tail.index("Duty Manager"):][:400].strip())
        print()
