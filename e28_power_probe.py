"""e28_power_probe.py: can a 12-instance paired cost study resolve anything?

NOT an experiment. A power probe, run BEFORE building anything, in the spirit
of E22 -- where a circuit search was designed, power-checked against a control
distribution that already ate most of the effect, and correctly NOT run.

THE QUESTION. The AgentCom proposal compares communication protocols on ~12
development instances using PAIRED differences by task. Paired designs cancel
between-instance variance in the LEVELS, so the quantity that governs power is
not the spread of absolute costs. It is the spread of the per-instance
DIFFERENCE. That spread has two components, and they have different remedies:

  (1) HETEROGENEITY -- instances differ in how much a protocol change saves.
      Remedy: more instances.
  (2) RUN NOISE -- the same instance, same protocols, re-run, lands elsewhere.
      Remedy: repeats per instance. More instances does NOT fix this cheaply.

A probe reporting a single pooled SD cannot tell the two apart, and so cannot
say what to buy. This one measures them separately.

  ARM H  n instances x {full, budgeted}, once each   -> SD of paired diff
  ARM R  one instance x {full, budgeted}, R times    -> SD of the SAME paired
                                                        diff under repetition

Both agents run at temperature 0, so ARM R measures the instrument's realised
nondeterminism rather than simulating it. If ARM R is ~0, all spread is
heterogeneity and instances are the thing to buy. If ARM R rivals ARM H, a
12-instance single-shot pilot is partly measuring its own decoder.

WHAT COUNTS AS COST. Realised prompt + completion tokens summed over the run --
the quantity a recovery study counts, and the one `Entry` already records per
turn. Full-transcript vs budgeted-context is the cheapest available stand-in
for "two communication protocols doing identical work"; this probe does NOT
simulate revisions or recovery. It bounds the noise floor any such study must
clear.
"""
import argparse
import json
import statistics

from budget import Budget
from context import RecencyBudget
from engine import DialogueEngine, Entry
from robust_client import RetryingOllamaClient
from scenario import AGENT_A, AGENT_B

#: 12 distinct opening situations -- the "instances" of this probe
SEEDS = [
    "The payment gateway is returning 502s for about a third of requests.",
    "A batch job wrote duplicate ledger rows overnight.",
    "The on-call pager did not fire when latency crossed the threshold.",
    "Two regions disagree about the current account balance.",
    "A config push reached production before review.",
    "The reconciliation report is short by a few hundred transactions.",
    "A third-party webhook has been retrying the same event for hours.",
    "Customer refunds are queued but not settling.",
    "The audit log stopped receiving events at 03:00.",
    "A schema migration left one column nullable that should not be.",
    "Rate limits are rejecting traffic from an internal service.",
    "The nightly backup completed but restores fail verification.",
]


def cost_of(transcript):
    """Realised token spend. The seeded opener contributes zero by construction."""
    return sum(e.prompt_tokens + e.completion_tokens for e in transcript)


class Binding:
    """Counts how often the context policy actually DROPPED something.

    PRECONDITION, not a metric. A paired difference of zero has two very
    different causes: the policy engaged and saved nothing, or the policy never
    engaged at all because the budget never bound. The second is no treatment,
    and reporting it as a null would be a false negative. The smoke run at
    turns=2 hit exactly this -- 120 words never bound on a 1-message history.
    """

    def __init__(self, policy):
        self.policy = policy
        self.calls = 0
        self.bound = 0

    def __call__(self, messages):
        out = self.policy.select(messages)
        self.calls += 1
        last = getattr(self.policy, "_last", None)
        if last and last.get("n_selected", 0) < last.get("n_candidates", 0):
            self.bound += 1
        return out


def run_one(client, turns, seed_note, policy=None):
    """One dialogue, opened by a seeded situation statement."""
    manage = policy if policy is not None else None
    eng = DialogueEngine(
        agents=[AGENT_A, AGENT_B], client=client,
        budget=Budget(max_turns=turns, max_tokens=200_000, max_seconds=900),
        manage_context=manage)
    # The opener is transcript content, not a model call: zero cost, and it
    # leaves AGENT_B to speak first, identically under both protocols.
    eng.transcript.append(Entry(speaker=AGENT_A.name, content=seed_note,
                                prompt_tokens=0, completion_tokens=0,
                                seconds=0.0, turn_index=0))
    return eng.run()


def paired_diff(client, turns, words, seed_note):
    """Cost(full) - Cost(budgeted) for one instance. Positive = budgeting saves."""
    full = run_one(client, turns, seed_note, policy=None)
    b = Binding(RecencyBudget(words))
    budgeted = run_one(client, turns, seed_note, policy=b)
    cf, cb = cost_of(full), cost_of(budgeted)
    return cf, cb, cf - cb, b.bound, b.calls


#: paired t-test, two-sided alpha=.05, power=.80: MDE = (t_a + t_b) * SD/sqrt(n)
#: df=11 -> t_.025 = 2.201, t_.20 = 0.876
T_FACTOR_N12 = 2.201 + 0.876


def main(n, repeats, turns, words, out):
    client = RetryingOllamaClient()
    print(f"=== E28 power probe | ARM H: {n} instances | ARM R: {repeats} repeats "
          f"| turns={turns} | recency budget={words} words ===\n")

    print("  ARM H -- heterogeneity across instances")
    rows, bound_total, call_total = [], 0, 0
    for i, seed in enumerate(SEEDS[:n], 1):
        cf, cb, d, bound, calls = paired_diff(client, turns, words, seed)
        bound_total += bound
        call_total += calls
        rows.append({"instance": i, "seed": seed[:46], "cost_full": cf,
                     "cost_budgeted": cb, "diff": d,
                     "rel": d / cf if cf else 0.0,
                     "policy_bound": bound, "policy_calls": calls})
        print(f"    [{i:2}/{n}] full {cf:6}  budgeted {cb:6}  diff {d:+6}  "
              f"rel {100 * d / max(cf, 1):+6.1f}%   bound {bound}/{calls}")

    print(f"\n  ARM R -- run noise, instance 1 repeated {repeats}x")
    reps = []
    for r in range(1, repeats + 1):
        cf, cb, d, bound, calls = paired_diff(client, turns, words, SEEDS[0])
        reps.append(d)
        print(f"    [{r}/{repeats}] full {cf:6}  budgeted {cb:6}  diff {d:+6}"
              f"   bound {bound}/{calls}")

    if bound_total == 0:
        print("\n  PRECONDITION FAILED: the context budget never bound in any "
              "run.\n  There was no treatment to measure, so no verdict is "
              "reported.\n  Raise --turns or lower --words and re-declare.")
        json.dump({"precondition": "FAILED", "reason": "policy never bound",
                   "arm_h": rows, "turns": turns, "words": words},
                  open(out, "w"), indent=1)
        return

    d = [r["diff"] for r in rows]
    mean_d, sd_h = statistics.mean(d), statistics.stdev(d)
    sd_r = statistics.stdev(reps) if len(reps) > 1 else 0.0
    base = statistics.mean(r["cost_full"] for r in rows)
    mde = T_FACTOR_N12 * sd_h / (12 ** 0.5)
    mde_pct = 100 * mde / base

    print("\n  --- variance decomposition ---")
    print(f"    mean paired difference        {mean_d:+9.1f} tokens "
          f"({100 * mean_d / base:+.1f}% of run cost)")
    print(f"    SD_H  across instances        {sd_h:9.1f} tokens")
    print(f"    SD_R  repeats, one instance   {sd_r:9.1f} tokens")
    share = (sd_r / sd_h) if sd_h else float("nan")
    print(f"    SD_R / SD_H                   {share:9.2f}   "
          f"({'run noise dominates' if share > 0.7 else 'heterogeneity dominates'})")

    print("\n  --- power for a 12-instance paired pilot (alpha .05, power .80) ---")
    print(f"    mean full-protocol cost       {base:9.0f} tokens/instance")
    print(f"    minimum detectable difference {mde:9.1f} tokens = {mde_pct:.1f}% of cost")
    print("    REVISE reports 31-56% model-call reductions.")
    verdict = ("POWERED" if mde_pct < 31 else
               "MARGINAL" if mde_pct < 56 else "UNDERPOWERED")
    print(f"    => {verdict} to detect a REVISE-scale effect at n=12.")
    if mde_pct >= 31:
        need = (T_FACTOR_N12 * sd_h / (0.31 * base)) ** 2
        print(f"    instances needed for a 31% effect: {need:.0f}")

    json.dump({"precondition": "PASSED", "policy_bound": bound_total,
               "policy_calls": call_total,
               "arm_h": rows, "arm_r": reps, "turns": turns, "words": words,
               "mean_diff": mean_d, "sd_heterogeneity": sd_h, "sd_run_noise": sd_r,
               "mean_full_cost": base, "mde_tokens": mde, "mde_pct": mde_pct,
               "verdict": verdict}, open(out, "w"), indent=1)
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--repeats", type=int, default=4)
    ap.add_argument("--turns", type=int, default=6)
    ap.add_argument("--words", type=int, default=120)
    ap.add_argument("--out", default="results/e28_power_probe.json")
    a = ap.parse_args()
    main(a.n, a.repeats, a.turns, a.words, a.out)
