"""b1_baseline.py: solo vs independent vs communicating, at equal call count.

Declared in docs/protocols/B1-communication-baseline.md before any model call.
EXPLORATORY BASELINE. Not a novelty candidate; has not passed the novelty gate.

Task: lineage_bench instances under `source_only` exposure -- SOURCE and
DISTRACTOR messages only, so the facts are stable (no supersession, no corrupted
relay) and every call sees the whole dialogue. Scoring is programmatic and blind
to the arm label by construction.

Three arms, five calls each, all ending in the SAME aggregation prompt:

  solo           draft1 -> refine1 -> draft2 -> refine2 -> aggregate  (one persona)
  independent    A.draft, B.draft -> A.refine(own), B.refine(own) -> aggregate
  communicating  A.draft, B.draft -> A.refine(+B), B.refine(+A)     -> aggregate

independent vs communicating differ ONLY in whether the refine prompt carries the
peer's draft. That is the isolated contrast; solo also differs in persona
identity and is a compute-matched reference, not part of it.
"""
import argparse
import hashlib
import itertools
import json
import time

import lineage_bench as lb
import lineage_eval as le
from robust_client import RetryingOllamaClient

MODEL = "llama3.2:3b"
SALT = "agentcom-b1"
TEMP = 0.7
CAP_WORK, CAP_AGG = 400, 300

COMBOS = [("payments", "chain"), ("robotics", "fork"), ("pharmacy", "join"),
          ("satellite", "diamond"), ("brewery", "twochain"), ("rail", "star"),
          ("payments", "diamond"), ("robotics", "twochain")]

ARMS = ("solo", "independent", "communicating")
ORDERS = list(itertools.permutations(ARMS))       # 6, rotated across instances

PERSONA_A = ("You are the Operations Lead. You are responsible for producing a "
             "safe, ordered recovery plan that respects every requirement raised "
             "in the discussion.")
PERSONA_B = ("You are the Safety Auditor. You hold the plan to the operational "
             "constraints established in the discussion and challenge any step "
             "that violates them.")


def seed_for(instance_id, arm, idx):
    h = hashlib.sha256(f"{instance_id}|{arm}|{idx}".encode()).hexdigest()
    return int(h[:8], 16)


def brief(inst):
    return (f"Setting: {inst.setting}\n\nDiscussion so far:\n"
            + lb.render_dialogue(lb.expose(inst, "source_only")))


def draft_prompt(inst, note=""):
    return (brief(inst) + "\n\n" + note
            + "Draft the ordered plan. List the steps in order, one per line, "
              "using only these identifiers:\n  " + "  ".join(inst.actions)
            + "\nBriefly say why that order respects the discussion.")


def refine_prompt(inst, own, peer=None):
    s = brief(inst) + "\n\nYour draft plan:\n" + own
    if peer is not None:
        s += "\n\nA colleague independently drafted this plan:\n" + peer
        s += ("\n\nConsider their draft. Where it disagrees with yours, decide "
              "which order actually respects the discussion.")
    return s + ("\n\nRevise your plan. Check every requirement in the discussion "
                "is satisfied and every ordering rule is respected. Give the "
                "revised ordered list of identifiers and a one-line reason.")


def aggregate_prompt(inst, drafts):
    s = brief(inst) + "\n\nCandidate plans produced during the work:\n"
    for i, d in enumerate(drafts, 1):
        s += f"\n--- candidate {i} ---\n{d}\n"
    return s + "\n\n" + lb.plan_instruction(inst)


class Runner:
    """One process, one instance. Records every call with its position."""

    def __init__(self, client, inst, log):
        self.c, self.inst, self.log = client, inst, log
        self.pos = 0
        self.calls = 0

    def ask(self, arm, idx, system, user, cap):
        self.c.seed = seed_for(self.inst.id, arm, idx)
        self.pos += 1
        t = time.time()
        r = self.c.chat(MODEL, [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                        temperature=TEMP, num_predict=cap)
        self.calls += 1
        rec = {"instance": self.inst.id, "arm": arm, "call_index": idx,
               "request_position": self.pos, "seed": self.c.seed,
               "prompt_tokens": r.prompt_tokens,
               "completion_tokens": r.completion_tokens,
               "seconds": round(time.time() - t, 3),
               "system": system, "user": user, "response": r.text or ""}
        self.log.write(json.dumps(rec) + "\n")
        self.log.flush()
        return rec["response"]

    def run_arm(self, arm):
        i = self.inst
        if arm == "solo":
            d1 = self.ask(arm, 0, PERSONA_A, draft_prompt(i), CAP_WORK)
            r1 = self.ask(arm, 1, PERSONA_A, refine_prompt(i, d1), CAP_WORK)
            d2 = self.ask(arm, 2, PERSONA_A, draft_prompt(
                i, "Work this case from scratch, independently of any earlier "
                   "attempt.\n\n"), CAP_WORK)
            r2 = self.ask(arm, 3, PERSONA_A, refine_prompt(i, d2), CAP_WORK)
            finals = [r1, r2]
        else:
            a0 = self.ask(arm, 0, PERSONA_A, draft_prompt(i), CAP_WORK)
            b0 = self.ask(arm, 1, PERSONA_B, draft_prompt(i), CAP_WORK)
            peer_a = b0 if arm == "communicating" else None
            peer_b = a0 if arm == "communicating" else None
            a1 = self.ask(arm, 2, PERSONA_A, refine_prompt(i, a0, peer_a), CAP_WORK)
            b1 = self.ask(arm, 3, PERSONA_B, refine_prompt(i, b0, peer_b), CAP_WORK)
            finals = [a1, b1]
        agg = self.ask(arm, 4, PERSONA_A, aggregate_prompt(i, finals), CAP_AGG)
        return finals, agg


def main(n, out_calls, out_outcomes, salt, budget):
    insts = [lb.generate_instance(d, g, salt=salt) for d, g in COMBOS[:n]]
    client = RetryingOllamaClient()
    spent = 0
    with open(out_calls, "a", encoding="utf-8") as lc, \
            open(out_outcomes, "a", encoding="utf-8") as lo:
        for k, inst in enumerate(insts):
            order = ORDERS[k % len(ORDERS)]
            run = Runner(client, inst, lc)
            print(f"[{k+1}/{len(insts)}] {inst.id}  order={'>'.join(order)}")
            for arm in order:
                if spent + 5 > budget:
                    print(f"  BUDGET CAP reached at {spent} calls; stopping.")
                    return
                finals, agg = run.run_arm(arm)
                spent += 5
                chk = le.check_plan(agg, inst, constraints=inst.constraints)
                rec = {"instance": inst.id, "arm": arm,
                       "arm_order": list(order),
                       "arm_position_in_process": order.index(arm) + 1,
                       "final_texts": finals, "aggregate_text": agg,
                       **chk.as_dict()}
                lo.write(json.dumps(rec) + "\n")
                lo.flush()
                print(f"   {arm:14} parsed={chk.parsed} success={chk.success} "
                      f"violations={len(chk.violated)} "
                      f"recall={chk.constraint_recall} actions={chk.actions}")
            print(f"   calls so far: {spent}")
    print(f"\nDONE. calls this run: {spent}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--salt", default=SALT)
    ap.add_argument("--budget", type=int, default=120)
    ap.add_argument("--calls", default="results/b1_calls.jsonl")
    ap.add_argument("--outcomes", default="results/b1_outcomes.jsonl")
    a = ap.parse_args()
    main(a.n, a.calls, a.outcomes, a.salt, a.budget)
