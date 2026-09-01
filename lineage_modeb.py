"""lineage_modeb.py: Mode B -- relays written by a model, not by a template.

THE CHECK THIS PROJECT PROMISED ITSELF. docs/agent-lineage-bench.md sec.8 states
the tension plainly and then commits to resolving it empirically:

    "Mode A -- scripted lineage. Lineage is exact. Dialogue is synthetic.
     Mode B -- agent-generated. Dialogue is natural. Labels are noisy.
     E2 is Mode A. Mode B is its external validity check: if the effect
     measured in Mode A does not also appear in Mode B, the benchmark is
     measuring an artefact of scripting, and that must be reported rather
     than explained away."

E5 found its effect on scripted relays drawn from four templates. Every relay in
a condition therefore shares a sentence skeleton, and a corroboration effect
measured on four fixed skeletons could be a fact about those skeletons. This
module regenerates the same chains with a model writing every relay in its own
words, so the E5 comparison can be re-run on natural text.

WHAT MODE B KEEPS AND WHAT IT GIVES UP.

  keeps    exact lineage. The relay is natural but its provenance is not
           inferred -- we know L2 derives from L1 because we handed the model
           L1 and asked for a restatement of it. Natural text, known parentage.
  keeps    ground truth. Constraints, actions and scoring are the base
           instance's, untouched.
  gives up template control. Wording now varies freely, so the surface-form
           separability that Mode A ENFORCES can only be MEASURED here.

THREE DIFFERENT MODELS, AND THAT IS THE POINT.

    generator   qwen2.5:7b-instruct    writes the relays
    verifier    qwen2.5:14b-instruct   certifies what each relay says
    decider     llama3.2:3b            makes the plan  (E5's model, unchanged)

No model verifies its own output and no model decides on text it wrote. That
last one also rules out a specific rival explanation for free: source bias
(Dai et al., KDD 2024) is about a model preferring ITS OWN generations. Here the
decider wrote none of the text it reads, so any depth effect that survives
cannot be self-preference.

THE VERIFICATION GATE, AND ITS LIMIT. A generated relay is only admitted if an
INDEPENDENT model, shown that message alone with no context, reports the same
ordering we asked for. This is not proof; it is one model certifying another.
What makes it worth doing is asymmetry: the verifier's task (read one sentence,
say which of two steps it puts first) is far easier than the decider's (weigh
conflicting messages, emit a six-action plan). The disagreement rate is recorded
and reported rather than hidden -- it is a property of the corpus.

Deterministic gates run first and cost nothing: length bounds, both actions
mentioned, no action IDENTIFIER leaked into prose (that would change the task),
and for filler, neither action mentioned.

THE FIXTURE IS FROZEN BEFORE ANY DECISION RUN, hashed exactly like the Mode A
corpus, so the decision experiment cannot be re-rolled against a corpus that
moved underneath it.

Run:  python lineage_modeb.py --limit 4          # generate, chunked
      python lineage_modeb.py --report           # inspect what was generated
"""
import argparse
import hashlib
import json
import os
import re
from dataclasses import replace

from budget import Budget
from lineage_bench import DOMAINS, all_instances
from lineage_depth import MAX_DEPTH, DepthChain, build_chain
from llm_client import OllamaClient
from structured import extract_json_object

GEN_MODEL = "qwen2.5:7b-instruct"
VERIFY_MODEL = "qwen2.5:14b-instruct"
FIXTURE = "fixtures/modeb.json"

#: Generation gets more attempts than the decision path's MAX_ATTEMPTS=2. That
#: cap is a rule about MODEL-CALLING LOOPS IN A DIALOGUE, where an unbounded
#: retry would hide cost inside a scored run. This loop is corpus construction:
#: it runs once, offline, and every attempt is counted and reported. Still
#: bounded -- rejection is a recorded outcome, never an infinite retry.
MAX_GEN_ATTEMPTS = 4

MIN_WORDS, MAX_WORDS = 8, 45

_STOP = {"the", "a", "an", "to", "of", "and", "or", "on", "in", "for", "with",
         "at", "by", "we", "it", "is", "be", "that", "this", "all", "from"}


def _stems(phrase):
    """Distinctive stems of an action phrase, for a paraphrase-tolerant check."""
    return {w[:5] for w in re.findall(r"[a-z]+", phrase.lower())
            if w not in _STOP and len(w) > 3}


def _mentions(text, phrase):
    """Does `text` plausibly refer to `phrase`? Prefix match survives paraphrase.

    "shift routing to the spare region" -> {shift, routi, spare, regio}; a relay
    saying "route traffic to the spare region first" still matches on `spare`
    and `regio`. Exact substring matching would reject almost every paraphrase,
    which is the whole reason Mode B exists.
    """
    want = _stems(phrase)
    have = {w[:5] for w in re.findall(r"[a-z]+", text.lower())}
    return bool(want) and len(want & have) >= max(1, len(want) // 2)


def _leaks_id(text, instance):
    return any(a in text for a in instance.actions)


#: Content-word overlap above which two relays count as the same sentence.
MAX_OVERLAP = 0.75


def _content(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP}


def _overlap(x, y):
    a, b = _content(x), _content(y)
    return len(a & b) / len(a | b) if a | b else 1.0


def _too_similar(msg, earlier):
    """THE FIRST PILOT PRODUCED L1 == L2 == L3, VERBATIM, IN EVERY INSTANCE.

    At temperature 0, asking a model to restate an already-minimal sentence is a
    fixed point: it returns the sentence. So depth 3 showed the same claim three
    times, and Mode B would have measured REPETITION -- repeated assertion is
    known to shift LLM source preference (arXiv:2601.03746) -- while reporting
    it as depth. Mode A had already found and fixed exactly this confound by
    sampling its four templates WITHOUT replacement; Mode B was about to
    reintroduce it in a form no template check would catch.

    Each link must therefore be a genuine rewording of everything before it.
    That is not a cosmetic requirement: it is what makes the chain a chain of
    restatements rather than a chain of copies.
    """
    for prev in earlier:
        ov = _overlap(msg, prev)
        if ov > MAX_OVERLAP:
            return (f"too close to an earlier message ({ov:.2f} content-word "
                    f"overlap, limit {MAX_OVERLAP}); reword it substantially")
    return None


# ------------------------------------------------------------ generation ----

GEN_SYSTEM = (
    "You are an engineer in an operations chat about {setting}. You write short, "
    "natural chat messages. You reply with a JSON object and nothing else."
)

RELAY_TASK = (
    "A colleague just wrote this in the channel:\n\n"
    '  "{parent}"\n\n'
    "Relay that to another engineer IN YOUR OWN WORDS. Say the same thing: "
    "{first_phrase} must happen BEFORE {second_phrase}. Do not change which "
    "step comes first. Do not use quotation marks or bullet points. "
    "One sentence, 10 to 30 words."
)

CORRUPT_TASK = (
    "A colleague just wrote this in the channel:\n\n"
    '  "{parent}"\n\n'
    "Relay this to another engineer IN YOUR OWN WORDS, but state the ordering "
    "the other way round: say that {first_phrase} must happen BEFORE "
    "{second_phrase}. Write it as a normal chat message, not as a correction "
    "or a question. Do not use quotation marks. One sentence, 10 to 30 words."
)

FILLER_TASK = (
    "Write one short chat message an engineer might send during {setting}, "
    "about a routine operational detail such as {topic}. "
    "It must NOT mention {avoid_a} or {avoid_b}, and must not discuss the "
    "order of any steps. One sentence, 10 to 25 words."
)

RELAY_FORMAT = (
    'Reply with exactly: {{"message": "<the chat message>", '
    '"first_step": "<which step you said comes first, in plain words>"}}'
)
FILLER_FORMAT = 'Reply with exactly: {{"message": "<the chat message>"}}'


def _read(text, keys):
    blob = extract_json_object(text or "")
    if blob is None:
        return None, "no JSON object in the reply"
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON ({exc.msg})"
    if not isinstance(obj, dict):
        return None, "top level is not an object"
    for k in keys:
        if not isinstance(obj.get(k), str) or not obj[k].strip():
            return None, f'"{k}" must be a non-empty string'
    return {k: obj[k].strip() for k in keys}, None


def _check_relay(msg, instance, first_phrase, second_phrase):
    """Deterministic gates. Returns an error string, or None to admit."""
    n = len(msg.split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        return f"message is {n} words, must be {MIN_WORDS}-{MAX_WORDS}"
    if _leaks_id(msg, instance):
        return "message contains a raw action identifier; use plain words"
    for phrase in (first_phrase, second_phrase):
        if not _mentions(msg, phrase):
            return f'message does not mention "{phrase}"'
    return None


def _check_filler(msg, instance, avoid_a, avoid_b):
    n = len(msg.split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        return f"message is {n} words, must be {MIN_WORDS}-{MAX_WORDS}"
    if _leaks_id(msg, instance):
        return "message contains a raw action identifier"
    for phrase in (avoid_a, avoid_b):
        if _mentions(msg, phrase):
            return f'message must not mention "{phrase}"'
    return None


def _generate(client, instance, task, fmt, gate, tag, log):
    """Bounded generate-and-gate. Every attempt is recorded, accepted or not."""
    messages = [
        {"role": "system", "content": GEN_SYSTEM.format(setting=instance.setting)},
        {"role": "user", "content": f"{task}\n\n{fmt}"},
    ]
    budget = Budget(max_turns=MAX_GEN_ATTEMPTS, max_tokens=200_000,
                    max_seconds=900)
    for attempt in range(MAX_GEN_ATTEMPTS):
        if budget.exhausted():
            break
        # Attempt 1 is deterministic. Later attempts must actually differ, and
        # at temperature 0 a repeated prompt returns the same rejected text, so
        # retrying without raising it would be a guaranteed-identical no-op.
        reply = client.chat(GEN_MODEL, messages, 0.0 if attempt == 0 else 0.8)
        budget.record(turns=1, tokens=reply.tokens)
        obj, err = _read(reply.text, ("message",) if fmt is FILLER_FORMAT
                         else ("message", "first_step"))
        if obj is not None:
            err = gate(obj["message"])
        log.append({"tag": tag, "attempt": attempt, "error": err,
                    "text": (obj or {}).get("message", reply.text)[:200],
                    "seconds": round(reply.seconds, 2)})
        if err is None:
            return obj
        messages = messages + [
            {"role": "assistant", "content": reply.text},
            {"role": "user", "content":
                f"That does not work: {err}. Try again. {fmt}"},
        ]
    return None


# ---------------------------------------------------------- verification ----

VERIFY_SYSTEM = (
    "You read one chat message and report what ordering it states. "
    "You reply with a JSON object and nothing else."
)
VERIFY_TASK = (
    "Message:\n\n  \"{msg}\"\n\n"
    "Two steps are involved:\n"
    "  A: {phrase_a}\n"
    "  B: {phrase_b}\n\n"
    "According to this message alone, which step must be done FIRST? "
    'Reply with exactly: {{"first": "A"}} or {{"first": "B"}}. '
    'If the message does not state an order, reply {{"first": "unclear"}}.'
)


def verify(client, msg, phrase_a, phrase_b, expect):
    """Independent certification. `expect` is "A" or "B". Returns what it said."""
    messages = [
        {"role": "system", "content": VERIFY_SYSTEM},
        {"role": "user", "content": VERIFY_TASK.format(
            msg=msg, phrase_a=phrase_a, phrase_b=phrase_b)},
    ]
    reply = client.chat(VERIFY_MODEL, messages, 0.0)
    obj, err = _read(reply.text, ("first",))
    said = (obj or {}).get("first", "").strip().upper()[:1] if not err else "?"
    return said, said == expect


# --------------------------------------------------------------- corpus ----

def _actions_of(instance, constraint_id):
    c = {x.id: x for x in instance.constraints}[constraint_id]
    verbs = dict(DOMAINS[instance.domain]["actions"])
    return verbs[c.a], verbs[c.b]                  # source says: pa before pb


def generate_one(client, instance, log):
    """Write one Mode B chain. GENERATOR ONLY -- no verifier call in here.

    Split out of a single interleaved loop for a mundane reason with a
    non-mundane payoff. Interleaving a 7B writer with a 14B verifier made Ollama
    swap models ten times per instance: generation cost 44s of compute per
    instance and roughly 150s of wall clock, nearly all of it loading weights.
    Two single-model passes remove the thrash.

    It also happens to be the right shape. Certification is a separate pass over
    a finished artefact, not a step inside the loop that produces it, and the
    generator never sees a verifier verdict either way -- the verifier only ever
    admits or drops.
    """
    ref = build_chain(instance)                    # same constraint as Mode A
    pa, pb = _actions_of(instance, ref.constraint_id)

    out = {"instance": instance.id, "constraint": ref.constraint_id,
           "faithful": [], "corrupted": None, "padding": [], "verify": []}

    parent, seen = ref.source.text, [ref.source.text]
    for k in range(1, MAX_DEPTH + 1):
        got = _generate(
            client, instance,
            RELAY_TASK.format(parent=parent, first_phrase=pa, second_phrase=pb),
            RELAY_FORMAT,
            lambda m, s=tuple(seen): (_check_relay(m, instance, pa, pb)
                                      or _too_similar(m, s)), f"L{k}", log)
        if got is None:
            return None
        out["faithful"].append(got["message"])
        seen.append(got["message"])
        parent = got["message"]                    # L_{k+1} derives from L_k

    # ONE corruption text, reused at every depth -- the Mode A discipline. If
    # each depth drew its own wording, depth would be confounded with phrasing.
    got = _generate(
        client, instance,
        CORRUPT_TASK.format(parent=ref.source.text, first_phrase=pb,
                            second_phrase=pa),
        RELAY_FORMAT,
        lambda m: _check_relay(m, instance, pa, pb), "C", log)
    if got is None:
        return None
    out["corrupted"] = got["message"]

    topics = DOMAINS[instance.domain]["noise"]
    for k in range(MAX_DEPTH - 1):
        got = _generate(
            client, instance,
            FILLER_TASK.format(setting=instance.setting,
                               topic=topics[k % len(topics)].rstrip("."),
                               avoid_a=pa, avoid_b=pb),
            FILLER_FORMAT,
            lambda m: _check_filler(m, instance, pa, pb), f"P{k + 1}", log)
        if got is None:
            return None
        out["padding"].append(got["message"])
    return out


def certify_one(client, instance, rec):
    """VERIFIER ONLY. Every relay is shown alone, with no context and no clue
    about which class it belongs to, and must report the ordering we asked for.

    Records the verdict on every message before deciding, so a chain that gets
    dropped still leaves evidence of WHY. Returns True if the chain is admitted.
    """
    pa, pb = _actions_of(instance, rec["constraint"])
    rec["verify"] = []
    for k, t in enumerate(rec["faithful"], 1):
        said, ok = verify(client, t, pa, pb, "A")
        rec["verify"].append({"tag": f"L{k}", "said": said, "ok": ok})
    said, ok = verify(client, rec["corrupted"], pa, pb, "B")
    rec["verify"].append({"tag": "C", "said": said, "ok": ok})
    return all(v["ok"] for v in rec["verify"])


def load(path=FIXTURE):
    if not os.path.exists(path):
        return {}
    return {r["instance"]: r for r in json.load(open(path))["chains"]}


def save(chains, log, path=FIXTURE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = sorted(chains.values(), key=lambda r: r["instance"])
    json.dump({"gen_model": GEN_MODEL, "verify_model": VERIFY_MODEL,
               "chains": rows, "attempts": log}, open(path, "w"), indent=2)


def fixture_hash(path=FIXTURE):
    """Freezes the generated corpus, exactly as the Mode A corpus is frozen."""
    chains = load(path)
    if not chains:
        return None
    return hashlib.sha256("␟".join(
        f"{r['instance']}|{r['constraint']}|" + "|".join(
            r["faithful"] + [r["corrupted"]] + r["padding"])
        for r in sorted(chains.values(), key=lambda r: r["instance"])
    ).encode()).hexdigest()[:16]


def certified(path=FIXTURE):
    """Only chains the verifier has actually passed.

    `load()` returns whatever is on disk, including chains written by pass 1 but
    not yet certified by pass 2 -- the generator needs that to know what to
    skip. A DECISION RUN MUST NOT SEE THEM. The distinction matters because the
    obvious shape check, `all(v["ok"] for v in rec["verify"])`, is vacuously
    true on an empty verify list, so an uncertified chain would sail through the
    gate that exists to stop it.
    """
    return {k: r for k, r in load(path).items() if r["verify"]}


def modeb_chain(instance, chains=None):
    """A DepthChain whose text is model-written.

    Deliberately returns the SAME type as Mode A, so e5_depth's exposure and
    padding logic is reused verbatim rather than reimplemented. The exposure
    schedule is the independent variable; only the text differs between modes,
    which is the one thing this comparison is allowed to change.
    """
    chains = certified() if chains is None else chains
    rec = chains.get(instance.id)
    if rec is None:
        return None
    assert rec["verify"] and all(v["ok"] for v in rec["verify"]), (
        f"{instance.id} was never certified; it must not reach a decision run")
    ref = build_chain(instance)

    # BUILT BY REPLACING TEXT ON MODE A'S OWN MESSAGES, not by constructing new
    # ones. The first version assembled fresh Message objects and assigned
    # speakers from the message index, which made every faithful relay come from
    # one speaker and every corruption from the other. That is not a cosmetic
    # difference: at depth 3 it turns two different people agreeing with the
    # source into ONE PERSON RESTATING THEMSELVES TWICE. Corroboration by
    # independent parties is the mechanism under test, so Mode B would have
    # removed the thing it exists to check -- while every count-and-lineage
    # assertion still passed.
    #
    # Deriving from Mode A instead makes msg_id, speaker, lineage, derives_from
    # and the faithful flag identical by construction. Text is the only field
    # that can differ, which is exactly what this experiment is allowed to vary.
    def swap(m, text):
        return replace(m, text=text)

    faithful = tuple(swap(m, t) for m, t in zip(ref.faithful, rec["faithful"]))
    corrupted = tuple(swap(m, rec["corrupted"]) for m in ref.corrupted)
    padding = tuple(swap(m, t) for m, t in zip(ref.padding, rec["padding"]))
    return DepthChain(instance_id=instance.id, constraint_id=rec["constraint"],
                      source=ref.source, faithful=faithful,
                      corrupted=corrupted, padding=padding)


def main(offset, limit, report):
    instances = all_instances()
    chains = load()

    if report:
        print(f"=== Mode B fixture: {len(chains)}/{len(instances)} instances ===")
        print(f"  hash {fixture_hash()}")
        for inst in instances[offset:offset + (limit or 3)]:
            r = chains.get(inst.id)
            if not r:
                continue
            ref = build_chain(inst)
            print(f"\n  {inst.id}  [{r['constraint']}]")
            print(f"    SRC  {ref.source.text}")
            for k, t in enumerate(r["faithful"], 1):
                print(f"    L{k}   {t}")
            print(f"    C    {r['corrupted']}")
            for k, t in enumerate(r["padding"], 1):
                print(f"    P{k}   {t}")
        return

    window = instances[offset:offset + (limit or len(instances))]
    client = OllamaClient()
    log = json.load(open(FIXTURE)).get("attempts", []) if os.path.exists(FIXTURE) else []

    # --- pass 1: the writer, alone ---------------------------------------
    todo = [i for i in window if i.id not in chains]
    if todo:
        print(f"=== pass 1/2: {GEN_MODEL} writes ({len(todo)} instances, "
              f"{len(chains)} already cached) ===\n")
    dropped = []
    for k, inst in enumerate(todo, 1):
        before = len(log)
        rec = generate_one(client, inst, log)
        marks = "".join("." if a["error"] is None else "x" for a in log[before:])
        if rec is None:
            dropped.append((inst.id, "no message passed the gates"))
            print(f"  [{k:>2}/{len(todo)}] {inst.id:<20} DROPPED   {marks}")
            continue
        chains[inst.id] = rec
        save(chains, log)                     # checkpoint: a kill loses one item
        print(f"  [{k:>2}/{len(todo)}] {inst.id:<20} written   {marks}")

    # --- pass 2: the verifier, alone -------------------------------------
    pending = [i for i in window if i.id in chains and not chains[i.id]["verify"]]
    if pending:
        print(f"\n=== pass 2/2: {VERIFY_MODEL} certifies ({len(pending)} "
              f"instances) ===\n")
    for k, inst in enumerate(pending, 1):
        rec = chains[inst.id]
        ok = certify_one(client, inst, rec)
        bad = [f"{v['tag']}->{v['said']}" for v in rec["verify"] if not v["ok"]]
        if not ok:
            del chains[inst.id]
            dropped.append((inst.id, f"verifier disagreed on {bad}"))
        save(chains, log)
        print(f"  [{k:>2}/{len(pending)}] {inst.id:<20} "
              + ("certified" if ok else f"DROPPED   {bad}"))

    save(chains, log)
    admitted = sum(1 for a in log if a["error"] is None)
    print(f"\n  corpus {len(chains)}/{len(instances)} instances")
    print(f"  generation attempts {len(log)}, admitted {admitted}, "
          f"rejected by a gate {len(log) - admitted}")
    for iid, why in dropped:
        print(f"  DROPPED {iid}: {why}")
    print(f"  fixture hash {fixture_hash()}  ->  {FIXTURE}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    main(a.offset, a.limit, a.report)
