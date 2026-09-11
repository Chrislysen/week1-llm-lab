"""e29b_real_extractor.py: E29-B -- the Mem0 paper write path, run for real
by a small local model, on the E29 dialogues; then the decider reads the
store it actually produced.

DECLARED in docs/protocols/E29-memory-semantics.md (E29-B section) before
any call.

WHAT IS RUN. For every line of a dialogue, in order:
  1. extraction   system = FACT_RETRIEVAL_PROMPT (mem0, verbatim); user = the
                  latest exchange (previous line + this line), formatted as
                  mem0's parse_messages does ("user: <content>").  Parse
                  {"facts": [...]}.  Malformed -> no facts, counted.
  2. update       if any facts: one user message built by mem0's own
                  get_update_memory_messages(old_memories, facts) with the
                  WHOLE live store as "old memories" (the store never exceeds
                  a dozen items, so this is a superset of mem0's top-k
                  retrieval).  Parse {"memory": [{id, text, event}]} and apply
                  ADD / UPDATE / DELETE / NONE exactly as mem0 does; unknown
                  ids ignored; malformed -> store unchanged, counted.
The two arms share every line before the inserted one, so the common prefix
is processed once and the store is forked; the inserted line and any tail are
processed per arm.  Every store snapshot is kept, line by line.

Then the decider (E29's prompt, `pin4`, temperature 0) reads the final store
rendered exactly as E29's `delete` design rendered its oracle store.

Deviations from mem0, stated: temperature 0 for both steps (mem0's OSS default
is 0.1); no embedding retrieval (whole store shown); one line per add().

Run:  python e29b_real_extractor.py --model llama3.2:3b --offset 0 --limit 7
      python e29b_real_extractor.py --model llama3.2:3b --dry-run
"""
import argparse
import json
import re
import statistics

from budget import Budget
from e10_independence import SYSTEM
from e13_recognition import TEMPERATURE, make_validator, schema_hint
from e17_menu_law import plan_instruction
from experiment import show, write_csv
from lineage_bench import DOMAINS
from lineage_e16 import corpus_hash as e16_hash
from lineage_e29 import ARMS, E16_HASH, all_e29_dialogues, corpus_hash
from lineage_eval import parse_plan
from mem0_vendored import DEFAULT_UPDATE_MEMORY_PROMPT, FACT_RETRIEVAL_PROMPT, get_update_memory_messages
from robust_client import RetryingOllamaClient
from structured import MAX_ATTEMPTS, ask_structured, extract_json_object

E29_HASH = "187a426616f26598"
COLUMNS = ["model", "arm", "instance", "rotation", "slot", "constraint", "action",
           "status", "parsed", "included", "n_actions", "ready", "attempts",
           "prompt_tokens", "store_size", "store_mentions_action",
           "after_proposal_mentions", "after_reply_mentions",
           "n_add", "n_update", "n_delete", "n_none", "malformed_extract",
           "malformed_update", "write_calls", "seconds"]
STOP = {"the", "a", "an", "to", "of", "and", "on", "in", "for", "at", "by", "with"}


def slug(s):
    return s.replace(".", "").replace(":", "-")


def subset():
    """Every second E29 dialogue, in E29 order: 48 of 96. Declared."""
    return all_e29_dialogues()[::2]


def content_words(phrase):
    return [w for w in re.findall(r"[a-z0-9\-']+", phrase.lower()) if w not in STOP]


def mentions(store, phrase):
    words = content_words(phrase)
    for text in store.values():
        t = text.lower()
        if all(w in t for w in words):
            return True
    return False


def _parse_json(text):
    blob = extract_json_object(text or "")
    if not blob:
        return None
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


class Mem0WritePath:
    """One live store; mem0's paper pipeline on a stream of lines."""

    def __init__(self, client, model):
        self.client, self.model = client, model
        self.store = {}          # id(str) -> text
        self.next_id = 0
        self.events = []         # (line_index, event, text)
        self.malformed_extract = 0
        self.malformed_update = 0
        self.write_calls = 0
        self.seconds = 0.0
        self.snapshots = []      # (line_index, dict(store))

    def fork(self):
        c = Mem0WritePath(self.client, self.model)
        c.store, c.next_id = dict(self.store), self.next_id
        c.events, c.snapshots = list(self.events), list(self.snapshots)
        c.malformed_extract, c.malformed_update = self.malformed_extract, self.malformed_update
        c.write_calls, c.seconds = self.write_calls, self.seconds
        return c

    def _chat(self, messages):
        self.write_calls += 1
        r = self.client.chat(self.model, messages, TEMPERATURE)
        self.seconds += r.seconds or 0
        return r.text

    def extract(self, prev_line, line):
        exchange = "".join(f"user: {s}: {t}\n" for s, t in ([prev_line] if prev_line else []) + [line])
        text = self._chat([{"role": "system", "content": FACT_RETRIEVAL_PROMPT},
                           {"role": "user", "content": exchange}])
        obj = _parse_json(text)
        if not isinstance(obj, dict) or not isinstance(obj.get("facts"), list):
            self.malformed_extract += 1
            return []
        return [str(f) for f in obj["facts"] if str(f).strip()]

    def update(self, facts, line_index):
        old = [{"id": k, "text": v} for k, v in self.store.items()]
        prompt = get_update_memory_messages(old, json.dumps(facts))
        text = self._chat([{"role": "user", "content": prompt}])
        obj = _parse_json(text)
        if not isinstance(obj, dict) or not isinstance(obj.get("memory"), list):
            self.malformed_update += 1
            return
        for item in obj["memory"]:
            if not isinstance(item, dict):
                continue
            ev = str(item.get("event", "NONE")).upper()
            mid = str(item.get("id", ""))
            txt = str(item.get("text", "")).strip()
            if ev == "ADD" and txt:
                self.store[str(self.next_id)] = txt; self.next_id += 1
                self.events.append((line_index, "ADD", txt))
            elif ev == "UPDATE" and mid in self.store and txt:
                self.store[mid] = txt
                self.events.append((line_index, "UPDATE", txt))
            elif ev == "DELETE" and mid in self.store:
                self.events.append((line_index, "DELETE", self.store.pop(mid)))
            else:
                self.events.append((line_index, "NONE", txt))

    def process(self, prev_line, line, line_index):
        facts = self.extract(prev_line, line)
        if facts:
            self.update(facts, line_index)
        self.snapshots.append((line_index, dict(self.store)))


def render_store(store):
    return ("MEMORY NOTES FROM THE DISCUSSION\n"
            "-------------------------------\n" + "\n".join(f"- {t}" for t in store.values()))


def run(model, offset, limit, dry_run):
    assert e16_hash() == E16_HASH and corpus_hash() == E29_HASH, "corpus disturbed"
    ds = subset()[offset:None if limit is None else offset + limit]
    print(f"=== E29-B real extractor: {model}, {len(ds)} dialogues"
          f"{' (DRY RUN, no calls)' if dry_run else ''} ===\n")
    if dry_run:
        d = ds[0]; dia = d["arms"]["restated"]
        print(FACT_RETRIEVAL_PROMPT[:300] + "...\n")
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
        # common prefix once
        wp = Mem0WritePath(client, model)
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
            res = ask_structured(client=client, model=model, temperature=TEMPERATURE,
                                 messages=[{"role": "system", "content": SYSTEM.format(setting=inst.setting)},
                                           {"role": "user", "content": user}],
                                 validate=validate, budget=budget, speaker="Operator", expected=expected)
            text = res.accepted_text or res.last_text or ""
            plan, _ = parse_plan(text)
            actions = plan["actions"] if plan else []
            evc = {e: sum(1 for _, x, _ in w.events if x == e) for e in ("ADD", "UPDATE", "DELETE", "NONE")}
            for u in d["units"]:
                rows.append({
                    "model": model, "arm": arm, "instance": u["instance"], "rotation": u["rotation"],
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
    stem = f"results/e29b_{slug(model)}_o{offset}"
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
    ap.add_argument("--model", required=True)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(a.model, a.offset, a.limit, a.dry_run)
