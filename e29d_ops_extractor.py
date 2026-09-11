"""e29d_ops_extractor.py: E29-D -- the Mem0 write path run for real, with an
extraction prompt that stores OPERATIONAL facts, on the E29 dialogues; then
the decider reads the store it actually produced.

DECLARED in docs/protocols/E29D-real-ops-extractor.md before any call.

Everything is E29-B (`e29b_real_extractor.py`) except the extraction prompt:
the update router is Mem0's DEFAULT_UPDATE_MEMORY_PROMPT verbatim, the 48
dialogues are E29-B's subset, the common prefix is processed once and forked,
snapshots are kept per line, and the decider reads the store rendered as E29's
`delete` design rendered its oracle store. Extractor/router model and decider
model are separate arguments.

Run:  python e29d_ops_extractor.py --extractor qwen2.5:7b-instruct --decider llama3.2:3b --dry-run
      python e29d_ops_extractor.py --extractor qwen2.5:7b-instruct --decider llama3.2:3b --offset 0 --limit 6
"""
import argparse
import json
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e17_menu_law import plan_instruction
from e29b_real_extractor import (COLUMNS, E29_HASH, Mem0WritePath, _parse_json,
                                 mentions, render_store, slug, subset)
from experiment import show, write_csv
from lineage_bench import DOMAINS
from lineage_e16 import corpus_hash as e16_hash
from lineage_e29 import ARMS, E16_HASH, corpus_hash
from lineage_eval import parse_plan
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured

#: Same form as Mem0's FACT_RETRIEVAL_PROMPT (JSON {"facts": [...]}, few-shot,
#: latest exchange only), asking for operational facts. The examples use a
#: domain and wordings that appear nowhere in the corpus.
OPS_FACT_PROMPT = """You are an Operations Memory Organizer for an incident-response team. Your role is to extract the operationally relevant facts from each exchange of a technical discussion and organize them into distinct, manageable facts, so that a planner can later recall what was proposed, what was agreed, and what was ruled out.

Types of Information to Remember:

1. Proposed steps: any operational step a speaker proposes or asks to have on the plan, and who proposed it. Name the step as the speaker named it.
2. Decisions on steps: whether a proposed step was accepted or rejected, and by whom. A short reply such as "no, leave that out" or "fine, keep it" refers to the step named in the previous message; record the decision against that step by name.
3. References back: when a speaker refers to a step that was raised earlier, record that the step was raised again and by whom.
4. Other operational context: schedules, hand-offs, requests from other teams, status-page state, meeting logistics.

Here are some few shot examples:

Input: user: Release Manager: Let's also warm the edge caches before we open the rollout.
Output: {"facts" : ["Release Manager proposed to warm the edge caches"]}

Input: user: Release Manager: Let's also warm the edge caches before we open the rollout.
user: Reliability Lead: Fine, that goes in.
Output: {"facts" : ["Reliability Lead accepted warming the edge caches"]}

Input: user: Release Manager: I want us to purge the origin cache as one of the steps.
user: Reliability Lead: Not this time, that stays out.
Output: {"facts" : ["Reliability Lead rejected purging the origin cache"]}

Input: user: Reliability Lead: Not this time, that stays out.
user: Release Manager: The vendor call moved to Thursday afternoon.
Output: {"facts" : ["The vendor call moved to Thursday afternoon"]}

Input: user: Reliability Lead: Legal wants the customer notice reviewed first.
user: Release Manager: As I said before, I did bring up purging the origin cache earlier on.
Output: {"facts" : ["Release Manager raised purging the origin cache again, saying they had brought it up earlier"]}

Return the facts in a json format as shown above.

Remember the following:
- Today's date is not relevant; do not add dates.
- Do not return anything from the custom few shot example prompts provided above.
- If you do not find anything operationally relevant in the exchange, return an empty list for the "facts" key.
- Extract facts from the latest exchange only. The previous message is included so that a short reply can be resolved against the step it answers.
- Create the facts based on the user messages only. Do not pick anything from the system messages.
- Make sure to return the response in the format mentioned in the examples. The response should be in json with a key as "facts" and corresponding value will be a list of strings.

Following is an exchange from a technical discussion between two colleagues. You have to extract the operationally relevant facts, if any, and return them in the json format as shown above."""


class OpsWritePath(Mem0WritePath):
    """Mem0's write path with the extraction prompt swapped; router untouched."""

    def extract(self, prev_line, line):
        exchange = "".join(f"user: {s}: {t}\n" for s, t in ([prev_line] if prev_line else []) + [line])
        text = self._chat([{"role": "system", "content": OPS_FACT_PROMPT},
                           {"role": "user", "content": exchange}])
        obj = _parse_json(text)
        if not isinstance(obj, dict) or not isinstance(obj.get("facts"), list):
            self.malformed_extract += 1
            return []
        return [str(f) for f in obj["facts"] if str(f).strip()]

    def fork(self):
        c = OpsWritePath(self.client, self.model)
        c.store, c.next_id = dict(self.store), self.next_id
        c.events, c.snapshots = list(self.events), list(self.snapshots)
        c.malformed_extract, c.malformed_update = self.malformed_extract, self.malformed_update
        c.write_calls, c.seconds = self.write_calls, self.seconds
        return c


def stem_for(extractor, decider, offset):
    return f"results/e29d_{slug(extractor)}_{slug(decider)}_o{offset}"


def run(extractor, decider, offset, limit, dry_run):
    assert e16_hash() == E16_HASH and corpus_hash() == E29_HASH, "corpus disturbed"
    ds = subset()[offset:None if limit is None else offset + limit]
    print(f"=== E29-D real ops extractor: extractor/router {extractor}, decider {decider}, "
          f"{len(ds)} dialogues{' (DRY RUN, no calls)' if dry_run else ''} ===\n")
    if dry_run:
        d = ds[0]; dia = d["arms"]["restated"]
        print(OPS_FACT_PROMPT[:400] + "...\n")
        print("first exchange:\n" + "".join(f"user: {s}: {t}\n" for s, t, _ in dia[:2]))
        print(f"lines per dialogue: {[len(x['arms']['restated']) for x in ds]}")
        return
    client = RetryingOllamaClient()
    validate, expected = make_validator("default"), schema_hint("default")
    rows, detail = [], []
    for i, d in enumerate(ds, 1):
        inst = d["instance"]
        verbs = dict(DOMAINS[inst.domain]["actions"])
        rej = next(u for u in d["units"] if u["status"] == "rejected")
        phrase = verbs[rej["action"]]
        a, b = d["arms"]["restated"], d["arms"]["neutral"]
        split = next(k for k, (x, y) in enumerate(zip(a, b)) if x != y)
        wp = OpsWritePath(client, extractor)
        prev = None
        after_prop = after_reply = None
        for k in range(split):
            s, t, tag = a[k]
            wp.process(prev, (s, t), k); prev = (s, t)
            if tag == ("proposal", rej["constraint"]):
                after_prop = mentions(wp.store, phrase)
            if tag == ("reply", rej["constraint"]):
                after_reply = mentions(wp.store, phrase)
        forks = {arm: wp.fork() for arm in ARMS}
        for arm in ARMS:
            dia = d["arms"][arm]
            w = forks[arm]
            prev_arm = prev
            for k in range(split, len(dia)):
                s, t, _ = dia[k]
                w.process(prev_arm, (s, t), k); prev_arm = (s, t)
            user = render_store(w.store) + "\n\n" + plan_instruction(tuple(inst.actions), "pin4")
            budget = Budget(max_turns=MAX_ATTEMPTS, max_tokens=200_000, max_seconds=600)
            res = ask_structured(client=client, model=decider, temperature=TEMPERATURE,
                                 messages=[{"role": "system", "content": SYSTEM.format(setting=inst.setting)},
                                           {"role": "user", "content": user}],
                                 validate=validate, budget=budget, speaker="Operator", expected=expected)
            text = res.accepted_text or res.last_text or ""
            plan, _ = parse_plan(text)
            actions = plan["actions"] if plan else []
            evc = {e: sum(1 for _, x, _ in w.events if x == e) for e in ("ADD", "UPDATE", "DELETE", "NONE")}
            for u in d["units"]:
                rows.append({
                    "model": f"{extractor}>{decider}", "arm": arm, "instance": u["instance"], "rotation": u["rotation"],
                    "slot": u["slot"], "constraint": u["constraint"], "action": u["action"],
                    "status": u["status"], "parsed": plan is not None,
                    "included": (u["action"] in actions) if plan else None,
                    "n_actions": len(actions) if plan else None,
                    "ready": plan["ready"] if plan else None, "attempts": len(res.attempts),
                    "prompt_tokens": res.attempts[0].prompt_tokens if res.attempts else None,
                    "store_size": len(w.store), "store_mentions_action": mentions(w.store, phrase),
                    "after_proposal_mentions": after_prop, "after_reply_mentions": after_reply,
                    "n_add": evc["ADD"], "n_update": evc["UPDATE"], "n_delete": evc["DELETE"], "n_none": evc["NONE"],
                    "malformed_extract": w.malformed_extract, "malformed_update": w.malformed_update,
                    "write_calls": w.write_calls, "seconds": round(w.seconds, 2),
                })
            detail.append({"instance": inst.id, "rotation": d["rotation"], "arm": arm,
                           "rejected_action": rej["action"], "phrase": phrase, "split": split,
                           "lines": [[s, t, list(tag)] for s, t, tag in dia],
                           "snapshots": [[k, st] for k, st in w.snapshots],
                           "events": [list(e) for e in w.events],
                           "final_store": w.store, "decider_prompt": user, "decider_output": text})
            print(f"  [{i:2}/{len(ds)}] {inst.id:20} r{d['rotation']} {arm:8} store={len(w.store):2} "
                  f"mentions={'Y' if mentions(w.store, phrase) else '.'} prop={after_prop} reply={after_reply} "
                  f"D={evc['DELETE']} bad={w.malformed_extract}/{w.malformed_update} "
                  f"n={len(actions)}{'' if plan else '  PARSE-FAIL'}")
    stem = stem_for(extractor, decider, offset)
    write_csv(stem + ".csv", rows, COLUMNS)
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=1)
    print(f"\n  wrote {stem}.csv / .json")
    rej_rows = [r for r in rows if r["status"] == "rejected" and r["parsed"]]
    summary = []
    for arm in ARMS:
        rs = [r for r in rej_rows if r["arm"] == arm]
        summary.append({"arm": arm, "n": len(rs),
                        "rejected_included": round(statistics.mean(r["included"] for r in rs), 3) if rs else None,
                        "store_mentions": round(statistics.mean(r["store_mentions_action"] for r in rs), 3) if rs else None})
    show(summary, ["arm", "n", "rejected_included", "store_mentions"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", required=True)
    ap.add_argument("--decider", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(a.extractor, a.decider, a.offset, a.limit, a.dry_run)
