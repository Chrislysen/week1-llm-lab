"""qwq_export_evidence.py: export fixtures 0 and 1 for independent semantic review.

ZERO MODEL CALLS. Reads only `results/qwq_calls.jsonl` and rebuilds the
deterministic fixture metadata. Modifies no fixture, model, prompt or record.

PROVENANCE LABELLING is the point of this file. Every exported item is marked:

  CAPTURED      recorded during execution and read back from the log verbatim
  RECONSTRUCTED rebuilt now from deterministic code, NOT recorded at run time

The message content sent to the model is CAPTURED (`rendered_input`). The JSON
envelope around it was never logged, so it is RECONSTRUCTED from the runner's
module constants and is labelled as such.
"""
import json

from plansel_fixtures import INSTRUCTION, build_quartet
import qwen_qual_run as runner

LOG = "results/qwq_calls.jsonl"
OUT_MD = "docs/QWQ-EVIDENCE-FIXTURES-0-1.md"
OUT_JSON = "results/qwq_evidence_fixtures_0_1.json"
FIXTURES = (0, 1)


def load():
    return [json.loads(l) for l in open(LOG, encoding="utf-8") if l.strip()]


def envelope(prompt):
    """RECONSTRUCTED request envelope. The body was not logged at run time."""
    return {"model": runner.MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False, "think": runner.THINK,
            "options": dict(runner.OPTIONS)}


def build():
    recs = [r for r in load() if r["fixture_index"] in FIXTURES]
    out = {"purpose": "independent semantic inspection of the delivered task",
           "model_calls_made_by_this_export": 0,
           "provenance_key": {
               "CAPTURED": "read verbatim from results/qwq_calls.jsonl",
               "RECONSTRUCTED": "rebuilt from deterministic code; not logged at run time"},
           "system_message": None,
           "system_message_note":
               "There is NO system message. The entire task is a single user "
               "message. RECONSTRUCTED from the runner, which builds "
               "[{'role':'user','content':prompt}].",
           "response_format_example": INSTRUCTION,
           "response_format_note":
               "CAPTURED: this exact text is the tail of every rendered_input. "
               "It is the only schema or format example the receiver is given.",
           "fixtures": []}

    for fi in FIXTURES:
        quartet = build_quartet(fi)
        rs = sorted([r for r in recs if r["fixture_index"] == fi],
                    key=lambda r: r["assignment"])
        fx0 = quartet[0]
        entry = {
            "fixture_index": fi,
            "domain": fx0.domain,
            "pattern": ("INVARIANT: same label on all four assignments"
                        if len({r["chosen"] for r in rs}) == 1
                        else "VARYING: label changed across assignments"),
            "option_to_sequence_mapping_RECONSTRUCTED": {
                o.label: list(o.sequence) for o in fx0.options},
            "display_order_RECONSTRUCTED": [o.label for o in fx0.options],
            "action_identifier_to_phrase_RECONSTRUCTED": dict(fx0.actions),
            "calls": []}
        for r in rs:
            fx = quartet[r["assignment"]]
            entry["calls"].append({
                "assignment": r["assignment"],
                "process_block_CAPTURED": r["block"],
                "process_position_CAPTURED": r["process_position"],
                "request_envelope_RECONSTRUCTED": envelope(r["rendered_input"]),
                "message_content_CAPTURED": r["rendered_input"],
                "raw_response_CAPTURED": r["response"],
                "thinking_field_CAPTURED": r["thinking_field"],
                "done_reason_CAPTURED": r["done_reason"],
                "truncated_CAPTURED": r["truncated"],
                "prompt_tokens_CAPTURED": r["prompt_tokens"],
                "completion_tokens_CAPTURED": r["completion_tokens"],
                "seconds_CAPTURED": r["seconds"],
                "decoded_choice_CAPTURED": r["chosen"],
                "gold_constraints_RECONSTRUCTED": [
                    {"id": c.id, "kind": c.kind, "before": c.a, "then": c.b}
                    for c in fx.constraints],
                "correct_label_RECONSTRUCTED": fx.correct_label,
                "executable_score_CAPTURED": {
                    "parsed": r["parsed"], "ready": r["ready"],
                    "violated": r["violated"], "success": r["success"]},
            })
        out["fixtures"].append(entry)
    return out


def to_markdown(ev):
    L = []
    A = L.append
    A("# QWQ evidence export — fixtures 0 and 1")
    A("")
    A("For **independent semantic inspection**: does the complete delivered task "
      "unambiguously ask for what the scorer rewards? The earlier wiring audit "
      "answered a different question (whether the intended bytes reached the "
      "client), and does not bear on this one.")
    A("")
    A("**Zero model calls were made to produce this export.** Nothing was "
      "modified, tuned or re-run.")
    A("")
    A("## Provenance key")
    A("")
    A("| label | meaning |")
    A("|---|---|")
    A("| **CAPTURED** | read verbatim from `results/qwq_calls.jsonl` |")
    A("| **RECONSTRUCTED** | rebuilt now from deterministic code; **not** logged at run time |")
    A("")
    A("The message content sent to the model is CAPTURED. The JSON envelope "
      "around it was never logged, so it is RECONSTRUCTED from the runner's "
      "module constants.")
    A("")
    A("## System instructions")
    A("")
    A("**There is no system message.** RECONSTRUCTED from the runner, which "
      "builds `[{\"role\": \"user\", \"content\": prompt}]`. The entire task is "
      "one user message; the complete text of all eight is below.")
    A("")
    A("## Response schema / format example (the only one given)")
    A("")
    A("CAPTURED — this exact text is the tail of every message:")
    A("")
    A("```")
    A(ev["response_format_example"])
    A("```")
    for f in ev["fixtures"]:
        A("")
        A(f"## Fixture {f['fixture_index']} — {f['domain']} — {f['pattern']}")
        A("")
        A("**Option → sequence mapping** (RECONSTRUCTED; identical across all "
          "four assignments):")
        A("")
        A("| label | sequence |")
        A("|---|---|")
        for k, v in f["option_to_sequence_mapping_RECONSTRUCTED"].items():
            A(f"| {k} | {' → '.join(v)} |")
        A("")
        A(f"**Display order** (RECONSTRUCTED): "
          f"{', '.join(f['display_order_RECONSTRUCTED'])}")
        A("")
        A("**Action identifier → natural phrase** (RECONSTRUCTED; note that the "
          "prompt itself never states this mapping):")
        A("")
        A("| identifier | phrase used in the fact messages |")
        A("|---|---|")
        for k, v in f["action_identifier_to_phrase_RECONSTRUCTED"].items():
            A(f"| `{k}` | {v} |")
        for c in f["calls"]:
            A("")
            A(f"### Fixture {f['fixture_index']}, assignment {c['assignment']}")
            A("")
            A(f"- process block (CAPTURED): `{c['process_block_CAPTURED']}`, "
              f"position {c['process_position_CAPTURED']}")
            A(f"- gold constraints (RECONSTRUCTED): " + "; ".join(
                f"**{g['id']}** {g['before']} before {g['then']}"
                for g in c["gold_constraints_RECONSTRUCTED"]))
            A(f"- correct label (RECONSTRUCTED): **{c['correct_label_RECONSTRUCTED']}**")
            A(f"- decoded choice (CAPTURED): **{c['decoded_choice_CAPTURED']}**")
            A(f"- executable score (CAPTURED): parsed="
              f"{c['executable_score_CAPTURED']['parsed']}, ready="
              f"{c['executable_score_CAPTURED']['ready']}, violated="
              f"{c['executable_score_CAPTURED']['violated']}, success="
              f"**{c['executable_score_CAPTURED']['success']}**")
            A(f"- done_reason={c['done_reason_CAPTURED']}, "
              f"truncated={c['truncated_CAPTURED']}, "
              f"thinking field={c['thinking_field_CAPTURED']!r}, "
              f"tokens {c['prompt_tokens_CAPTURED']}+"
              f"{c['completion_tokens_CAPTURED']}, {c['seconds_CAPTURED']}s")
            A("")
            A("**Request envelope — RECONSTRUCTED** (the envelope was not logged; "
              "`messages[0].content` below is CAPTURED and shown in full after it):")
            A("")
            A("```json")
            env = dict(c["request_envelope_RECONSTRUCTED"])
            env["messages"] = [{"role": "user",
                                "content": "<< CAPTURED, reproduced verbatim below >>"}]
            A(json.dumps(env, indent=2))
            A("```")
            A("")
            A("**Message content — CAPTURED, exact text:**")
            A("")
            A("```")
            A(c["message_content_CAPTURED"])
            A("```")
            A("")
            A("**Raw response — CAPTURED, exact text:**")
            A("")
            A("```")
            A(c["raw_response_CAPTURED"])
            A("```")
    A("")
    A("## For the reviewer")
    A("")
    A("The question is whether the delivered task unambiguously asks for what "
      "the scorer rewards. Two features are surfaced without interpretation:")
    A("")
    A("1. The fact messages refer to actions by **natural-language phrase** "
      "(\"snapshot the store\"); the candidate plans list them by **identifier** "
      "(`SNAPSHOT_STORE`). The prompt **never states the mapping** between the "
      "two. It is recoverable by inference, and no claim is made here about "
      "whether that inference is reliable.")
    A("2. Success additionally requires `ready=true`; a correct option chosen "
      "with `ready=false` scores as failure. In these 32 calls `ready` was true "
      "every time, so this did not bind — it is listed because it is part of "
      "what the scorer rewards.")
    A("")
    A("No recommendation for a further experiment is made in this document.")
    return "\n".join(L)


if __name__ == "__main__":
    ev = build()
    json.dump(ev, open(OUT_JSON, "w", encoding="utf-8"), indent=1)
    open(OUT_MD, "w", encoding="utf-8", newline="").write(to_markdown(ev))
    n = sum(len(f["calls"]) for f in ev["fixtures"])
    print(f"exported {n} calls across {len(ev['fixtures'])} fixtures")
    print(f"wrote {OUT_MD} and {OUT_JSON}")
