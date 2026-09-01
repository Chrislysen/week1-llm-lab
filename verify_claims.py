"""verify_claims.py: re-derive every reported number from raw artifacts.

Exits non-zero on any mismatch.

THE RULE, taken from secret-loyalty-probe: a number is verified by RECOMPUTING
it from the raw plan text, never by reading it back out of the file that asserts
it. Reading a stored score and comparing it to itself is a tautology that
verifies nothing, and that project caught exactly that mistake in its own
ledger.

This one exists because of the record. Seven results in this repo were retracted
after they had been reported:

  * the compulsory's transcripts were gitignored, so nothing could be re-derived
  * `supersession_respected` returned 1.0 for an empty plan
  * the E2 prompt printed a valid topological order (echo policy scored 36/36)
  * BM25's retrieval inversion was 94% its recency tie-break
  * `source_truster` scored 36/36, making the benchmark reward the same reflex
    as all the prior art
  * a two-word regex classified SUPERSESSION perfectly
  * the E5 "step function" was a p = 1.000 null at n = 36

Most were caught by a control or an audit, not by a checker. This is the checker.

THREE OUTCOMES per claim, and the third matters:
    VERIFIED       recomputed value matches what was reported
    MISMATCH       it does not -- the run fails
    UNVERIFIABLE   the artifact was scored against a DIFFERENT corpus, so it
                   cannot be re-derived and must not be silently counted as
                   passing. The corpus fixture has changed four times in this
                   project; results that predate a change are not comparable
                   and saying so is the whole point of recording the hash.

Run:  python verify_claims.py
"""
import csv
import glob
import hashlib
import json
import math
import os
import statistics
import sys

from lineage_bench import all_instances, expose
from lineage_eval import baseline_scores, check_plan

TOL = 1e-4
_state = {"ok": 0, "bad": 0, "skip": 0}


def corpus_hash():
    """Identifies the generated corpus. Must match test_lineage_bench.py."""
    insts = all_instances()
    return hashlib.sha256("␟".join(
        f"{i.id}|{i.announced_supersession}|" + "|".join(
            f"{m.msg_id}:{m.lineage}:{m.text}" for m in i.messages)
        for i in insts).encode()).hexdigest()[:16]


def claim(desc, got, want, tol=TOL):
    if got is None:
        _state["skip"] += 1
        print(f"  [SKIP] {desc}")
        return
    ok = (abs(got - want) <= tol if isinstance(want, (int, float))
          and isinstance(got, (int, float)) else got == want)
    if ok:
        _state["ok"] += 1
        print(f"  [ OK ] {desc}  = {got}")
    else:
        _state["bad"] += 1
        print(f"  [BAD ] {desc}  recomputed {got!r}, reported {want!r}")


def skip(desc, why):
    _state["skip"] += 1
    print(f"  [SKIP] {desc}  ({why})")


# ---------------------------------------------------------------- corpus ----

print("=== corpus fixture ===")
CORPUS = corpus_hash()
print(f"  current corpus: {CORPUS}")


# ------------------------------------------------- benchmark invariants ----
# Recomputed from the generator itself, so these are always verifiable.

print("\n=== benchmark invariants (recomputed from the generator) ===")
INSTANCES = all_instances()
claim("instance count", len(INSTANCES), 36)

bl = [baseline_scores(i) for i in INSTANCES]
claim("source_truster success (must be 0 -- the differentiator)",
      sum(b["source_truster"]["success"] for b in bl), 0)
# An INVARIANT, not a snapshot. The first version hardcoded 5, which was that
# corpus's value; the corpus changed and the checker correctly went red on its
# own stale expectation. What must hold is that the latest reflex ALSO mostly
# fails -- both trivial policies losing is the property the design rests on.
claim("latest_truster mostly fails too (invariant, not a snapshot)",
      sum(b["latest_truster"]["success"] for b in bl) <= 9, True)


def topo(inst):
    order, rem = [], list(inst.actions)
    e = [(c.a, c.b) for c in inst.effective_constraints if c.kind == "before"]
    while rem:
        for a in rem:
            if not any(b == a and x in rem for x, b in e):
                order.append(a)
                rem.remove(a)
                break
        else:
            return None
    return order


def pj(actions):
    return json.dumps({"actions": list(actions), "ready": True})


claim("optimal policy success (task must be solvable)",
      sum(check_plan(pj(topo(i)), i).success for i in INSTANCES), 36)
claim("echo-the-prompt-order success (null control, must stay low)",
      sum(check_plan(pj(list(i.actions)), i).success for i in INSTANCES) <= 4, True)

sup = [m.text for i in INSTANCES for m in i.messages if m.lineage == "SUPERSESSION"]
cor = [m.text for i in INSTANCES for m in i.messages
       if m.lineage == "CORRUPTED_RELAY"]
claim("SUPERSESSION and CORRUPTED_RELAY share surface forms",
      len(set(sup) & set(cor)) > 0, True)
claim("no message scores the old cue regex 'changed|now'",
      sum(("changed" in t.lower() or " now" in t.lower()) for t in sup), 0)


# ------------------------------------------------------------ E5 depth ----
# Re-derived from the raw plan text, not from the CSV's own verdict column.

print("\n=== E5 relay depth (re-derived from raw plan text) ===")
from lineage_depth import build_chain, follows_corruption

E5_JSON = sorted(glob.glob("results/e5_depth_*_o*.json"))
E5_CSV = sorted(glob.glob("results/e5_depth_*_o*.csv"))
if not E5_JSON:
    skip("E5 artifacts", "not found")
else:
    detail = []
    for p in E5_JSON:
        detail.extend(json.load(open(p)))
    reported = []
    for p in E5_CSV:
        reported.extend(csv.DictReader(open(p, newline="")))
    rep = {(r["instance"], r["condition"]): r["verdict"] for r in reported}

    by_cond, drift = {}, 0
    inst_by_id = {i.id: i for i in INSTANCES}
    for rec in detail:
        inst = inst_by_id.get(rec["instance"])
        if inst is None:
            continue
        chain = build_chain(inst)
        chk = check_plan(rec["plan_text"], inst)
        v = follows_corruption(inst, chain, chk.actions) if chk.parsed else ""
        drift += (rep.get((rec["instance"], rec["condition"]), v) != v)
        by_cond.setdefault(rec["condition"], []).append(v)

    claim("E5 verdicts re-derived match those recorded (0 = no drift)", drift, 0)
    for cond, want in (("d1", 0.7778), ("d2", 0.6111), ("d3", 0.4167),
                       ("control", 0.0), ("d1_padded", 0.8000)):
        vs = by_cond.get(cond)
        if not vs:
            skip(f"E5 {cond} adoption", "condition absent")
            continue
        s = sum(v == "source" for v in vs)
        c = sum(v == "corruption" for v in vs)
        claim(f"E5 {cond} adoption", round(c / (s + c), 4) if s + c else None,
              want, tol=0.001)

    # The McNemar p-values, recomputed from the same re-derived verdicts.
    per = {}
    for rec in detail:
        inst = inst_by_id.get(rec["instance"])
        if inst is None:
            continue
        chk = check_plan(rec["plan_text"], inst)
        v = (follows_corruption(inst, build_chain(inst), chk.actions)
             if chk.parsed else "")
        per.setdefault(rec["instance"], {})[rec["condition"]] = v

    def mcnemar(a, b):
        n01 = sum(1 for x in per.values()
                  if x.get(a) == "corruption" and x.get(b) == "source")
        n10 = sum(1 for x in per.values()
                  if x.get(a) == "source" and x.get(b) == "corruption")
        n = n01 + n10
        if n == 0:
            return None
        k = min(n01, n10)
        return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)

    for a, b, want in (("d1", "d2", 0.1094), ("d2", "d3", 0.0654),
                       ("d1", "d3", 0.0010), ("d1", "d1_padded", 1.0000),
                       ("d1_padded", "d3", 0.0026)):
        claim(f"E5 McNemar {a} vs {b}", round(mcnemar(a, b) or -1, 4), want,
              tol=0.0002)

    print("\n  NOTE: on the CORRECTED corpus the shape is a monotone gradient")
    print("  (0.778 -> 0.611 -> 0.417), not a step. NEITHER single step reaches")
    print("  p < 0.05; only the d1-vs-d3 span does (p = 0.0010). The earlier")
    print("  'step function' reading is dead twice over -- retracted as an")
    print("  over-read of a p = 1.000 null, and contradicted by corrected data.")
    print("  Length still does nothing: d1 vs d1_padded p = 1.0000.")


# ------------------------------------------------------- E7 Mode B ---------
# Re-derived from raw plan text against the MODE B chains, so a corpus that
# moved would show up here as a mismatch rather than as a quiet re-score.

print("\n=== E7 Mode B (re-derived from raw plan text) ===")
from lineage_modeb import certified, fixture_hash, modeb_chain

E7_JSON = sorted(glob.glob("results/e7_modeb_*_o*.json"))
if not E7_JSON:
    skip("E7 artifacts", "not found")
else:
    chains = certified()
    claim("Mode B corpus is complete", len(chains), 36)
    claim("Mode B corpus fixture", fixture_hash(), "4a2938565a36ee9f")
    claim("every Mode B chain was certified by the verifier",
          all(c["verify"] and all(v["ok"] for v in c["verify"])
              for c in chains.values()), True)

    detail = []
    for p in E7_JSON:
        detail.extend(json.load(open(p)))

    per7, by7 = {}, {}
    for rec in detail:
        inst = {i.id: i for i in INSTANCES}.get(rec["instance"])
        ch = modeb_chain(inst, chains) if inst else None
        if ch is None:
            continue
        chk = check_plan(rec["plan_text"], inst)
        v = follows_corruption(inst, ch, chk.actions) if chk.parsed else ""
        per7.setdefault(rec["instance"], {})[rec["condition"]] = v
        by7.setdefault(rec["condition"], []).append(v)

    for cond, want in (("d1", 0.7778), ("d2", 0.1944), ("d3", 0.1667),
                       ("control", 0.0), ("d1_padded", 0.6389)):
        vs = by7.get(cond, [])
        s = sum(v == "source" for v in vs)
        c = sum(v == "corruption" for v in vs)
        claim(f"E7 {cond} adoption",
              round(c / (s + c), 4) if s + c else None, want, tol=0.001)

    def mcnemar7(a, b):
        n01 = sum(1 for x in per7.values()
                  if x.get(a) == "corruption" and x.get(b) == "source")
        n10 = sum(1 for x in per7.values()
                  if x.get(a) == "source" and x.get(b) == "corruption")
        n = n01 + n10
        if n == 0:
            return None
        k = min(n01, n10)
        return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)

    # Relative tolerance, because these span seven orders of magnitude and an
    # absolute 1e-4 would call 9.5e-07 and 3.0e-06 indistinguishable.
    for a, b, want in (("d1", "d2", 9.537e-07), ("d2", "d3", 1.0),
                       ("d1", "d3", 2.980e-06), ("d1", "d1_padded", 0.2266),
                       ("d1_padded", "d3", 1.526e-05)):
        got = mcnemar7(a, b)
        claim(f"E7 McNemar {a} vs {b}",
              None if got is None else round(got / want, 3), 1.0, tol=0.002)

    # The predeclared checks, re-derived rather than read back from the report.
    a7 = {c: (lambda s, x: round(x / (s + x), 4) if s + x else None)(
              sum(v == "source" for v in vs), sum(v == "corruption" for v in vs))
          for c, vs in by7.items()}
    claim("P1 holds: adoption(d1) > adoption(d3)", a7["d1"] > a7["d3"], True)
    claim("P2 holds: d1_padded is nearer d1 than d3",
          abs(a7["d1_padded"] - a7["d1"]) < abs(a7["d1_padded"] - a7["d3"]), True)
    claim("P3 holds: control adoption is 0", a7["control"], 0.0)
    claim("no ambiguous plans to hide (neither == 0)",
          sum(v == "neither" for vs in by7.values() for v in vs), 0)

    print("\n  NOTE: Mode B replicates the DIRECTION and the length")
    print("  dissociation, not the shape -- Mode A declines gradually, Mode B")
    print("  steps at the first corroborating link. The cross-mode magnitude")
    print("  comparison is NOT made: the two corpora differ measurably in how")
    print("  the corruption is framed (revision wording 13/36 in A, 3/36 in B).")


# ------------------------------------------------------- E9 speaker 2x2 ----
# The experiment that identified the E7 effect against BOTH confounds.

print("\n=== E9 speaker 2x2 (re-derived from raw plan text) ===")
from e9_speaker import ARMS as E9_ARMS, exposure as e9_exposure

E9_JSON = sorted(glob.glob("results/e9_speaker_*_o*.json"))
if not E9_JSON:
    skip("E9 artifacts", "not found")
else:
    det9 = []
    for p in E9_JSON:
        det9.extend(json.load(open(p)))
    by_id = {i.id: i for i in INSTANCES}
    per9, by9 = {}, {}
    for rec in det9:
        inst = by_id.get(rec["instance"])
        ch = modeb_chain(inst, chains) if inst else None
        if ch is None:
            continue
        chk = check_plan(rec["plan_text"], inst)
        v = follows_corruption(inst, ch, chk.actions) if chk.parsed else ""
        per9.setdefault(rec["instance"], {})[rec["arm"]] = v
        by9.setdefault(rec["arm"], []).append(v)

    for arm, want in (("d1_fresh", 0.9167), ("d1_self", 0.8056),
                      ("d3_fresh", 0.1944), ("d3_self", 0.1389),
                      ("d1pad_fresh", 0.5278)):
        vs = by9.get(arm, [])
        s_ = sum(v == "source" for v in vs)
        c_ = sum(v == "corruption" for v in vs)
        claim(f"E9 {arm} adoption",
              round(c_ / (s_ + c_), 4) if s_ + c_ else None, want, tol=0.001)

    def mc9(a, b):
        n01 = sum(1 for x in per9.values()
                  if x.get(a) == "corruption" and x.get(b) == "source")
        n10 = sum(1 for x in per9.values()
                  if x.get(a) == "source" and x.get(b) == "corruption")
        n = n01 + n10
        if n == 0:
            return None
        k = min(n01, n10)
        return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)

    for a, b, want in (("d1pad_fresh", "d3_fresh", 1.831e-03),
                       ("d1_fresh", "d1pad_fresh", 1.221e-04),
                       ("d1_fresh", "d3_fresh", 2.980e-08),
                       ("d1_fresh", "d1_self", 0.1250),
                       ("d3_fresh", "d3_self", 0.5000)):
        got = mc9(a, b)
        claim(f"E9 McNemar {a} vs {b}",
              None if got is None else round(got / want, 3), 1.0, tol=0.005)

    # The structural fact that made E9 necessary, recomputed from the chains.
    same = {}
    for name, depth in (("d1", 1), ("d2", 2), ("d3", 3)):
        same[name] = sum(
            1 for cid in chains
            if (lambda e: e[-1].speaker == e[-2].speaker)(
                modeb_chain(by_id[cid], chains).exposure(depth, True)))
    claim("E5/E7 confound: contradiction shares a speaker with the message "
          "before it at d2", same["d2"], 36)
    claim("...and at d3", same["d3"], 36)
    claim("...but not at d1", same["d1"] < 36, True)

    # E9 holds the speaker fixed, so this must be zero everywhere.
    bad = 0
    for cid in chains:
        ch = modeb_chain(by_id[cid], chains)
        for arm, _, selfrev in E9_ARMS:
            msgs = e9_exposure(ch, arm)
            spoke = any(m.speaker == msgs[-1].speaker for m in msgs[:-1])
            bad += spoke != selfrev
    claim("E9 arms actually deliver the speaker condition they claim", bad, 0)

    print("\n  NOTE: E9 RETRACTS E7's P2. E7 concluded 'length does nothing'")
    print("  from d1 vs d1_padded (p = 0.2266). With speakers controlled that")
    print("  comparison is 14-0, p = 1.221e-04 -- filler alone moves adoption")
    print("  0.9167 -> 0.5278. Corroboration then adds a FURTHER 0.5278 ->")
    print("  0.1944 (p = 1.831e-03) on top of it. Both factors are real; E7")
    print("  attributed all of it to one.")


# ----------------------------------------------------------- E10 -----------
# The experiment that fired its own kill rule.

print("\n=== E10 lineage independence (re-derived from raw plan text) ===")
from lineage_e10 import ARMS as E10_ARMS, all_e10 as _all_e10
from lineage_e10 import corpus_hash as e10_hash
from e10_independence import mcnemar as e10_mcnemar, verdict as e10_verdict

E10_JSON = sorted(glob.glob("results/e10_*_o*.json"))
if not E10_JSON:
    skip("E10 artifacts", "not found")
else:
    claim("E10 corpus fixture", e10_hash(), "00947dde8eb0520b")
    claim("E10 arm count (deleting an arm must be a failure)", len(E10_ARMS), 9)

    d10 = []
    for p in E10_JSON:
        d10.extend(r for r in json.load(open(p))
                   if r.get("model") == "llama3.2:3b")
    by_id = {i.id: i for i in INSTANCES}
    e10_by_id = {e.instance_id: e for e in _all_e10()}
    per10, by10 = {}, {}
    for rec in d10:
        inst = by_id.get(rec["instance"])
        e = e10_by_id.get(rec["instance"])
        if inst is None or e is None:
            continue
        chk = check_plan(rec["plan_text"], inst)
        v = e10_verdict(inst, e, rec["arm"], chk.actions) if chk.parsed else ""
        per10.setdefault(rec["instance"], {})[rec["arm"]] = v
        by10.setdefault(rec["arm"], []).append(v)

    for arm, want in (("bare", 0.7222), ("filler", 0.5), ("same_root", 0.25),
                      ("indep_root", 0.25), ("same_root_nospk", 0.1944),
                      ("indep_root_nospk", 0.5556), ("bare_super", 1.0),
                      ("same_root_super", 1.0), ("indep_root_super", 0.9722)):
        vs = by10.get(arm, [])
        s_ = sum(v == "source" for v in vs)
        f_ = sum(v == "flip" for v in vs)
        claim(f"E10 {arm} flip rate",
              round(f_ / (s_ + f_), 4) if s_ + f_ else None, want, tol=0.001)

    p3 = e10_mcnemar(per10, "same_root", "indep_root")[0]
    claim("E10 H3 (PRIMARY) p-value -- INCONCLUSIVE, not a fired kill rule; "
          "see docs/protocols/E10-H3-RETRACTION.md",
          round(p3, 4) if p3 is not None else None, 1.0)
    claim("E10 H3 paired difference is exactly zero",
          round((lambda a, b: b - a)(
              sum(v == "flip" for v in by10["same_root"]) / 36,
              sum(v == "flip" for v in by10["indep_root"]) / 36), 4), 0.0)

    for a, b, want in (("bare", "filler", 0.0078),
                       ("filler", "same_root", 0.0225),
                       ("same_root", "same_root_nospk", 0.625),
                       ("indep_root", "indep_root_nospk", 0.0009766),
                       ("bare_super", "same_root_super", None)):
        got = e10_mcnemar(per10, a, b)[0]
        if want is None:
            claim(f"E10 {a} vs {b}: no discordant pairs (H5b, no hysteresis)",
                  got is None, True)
        else:
            claim(f"E10 McNemar {a} vs {b}",
                  None if got is None else round(got / want, 2), 1.0, tol=0.02)

    # The manipulation check is what makes the H3 null interpretable.
    if os.path.exists("results/e10_manip_check.csv"):
        mc = list(csv.DictReader(open("results/e10_manip_check.csv", newline="")))
        pair = {}
        for r in mc:
            pair.setdefault(r["instance"], {})[r["arm"]] = r["reported"]
        hi = sum(1 for v in pair.values()
                 if v.get("indep_root", "").isdigit()
                 and v.get("same_root", "").isdigit()
                 and int(v["indep_root"]) > int(v["same_root"]))
        lo = sum(1 for v in pair.values()
                 if v.get("indep_root", "").isdigit()
                 and v.get("same_root", "").isdigit()
                 and int(v["indep_root"]) < int(v["same_root"]))
        claim("manipulation check: reports MORE roots for indep_root", hi, 27)
        claim("manipulation check: never reports fewer", lo, 0)

    print("\n  RETRACTED READING -- docs/protocols/E10-H3-RETRACTION.md.")
    print("  H3's point estimate is 0.0000, but its 95% CI is [-0.111, +0.111]")
    print("  against a preregistered equivalence bound of 0.10, so the")
    print("  protocol's OWN decision procedure returns INCONCLUSIVE. Simulated")
    print("  power at that SESOI was 0.14. The claim that the model 'assigns")
    print("  ZERO decision weight' is WITHDRAWN.")
    print("  What survives: the CI excludes |effect| > 0.111, and in the same")
    print("  instrument corroboration moves 18-19/36 instances while")
    print("  independence moves at most 3. Far smaller -- not zero.")


# ----------------------------------------------------------- E11 ----------
# The experiment built to attack E10's null -- and it confirmed it while
# breaking one of E10's own secondary findings.

print("\n=== E11 multiplicity sweep (re-derived from raw plan text) ===")
from lineage_e11 import ARMS as E11_ARMS, all_e11
from lineage_e11 import corpus_hash as e11_hash
from e11_multiplicity import verdict as e11_verdict

E11_JSON = sorted(glob.glob("results/e11_*_o*.json"))
if not E11_JSON:
    skip("E11 artifacts", "not found")
else:
    claim("E11 corpus fixture", e11_hash(), "5c28ada4c4b899dc")
    claim("E11 arm count", len(E11_ARMS), 10)
    claim("E10 corpus still reproduces (E11 must not disturb it)",
          e10_hash(), "00947dde8eb0520b")

    # MODEL FILTER, and it is load-bearing. The glob picks up every E11 run,
    # so the moment a second decider was added the aggregate silently mixed
    # models and ten claims went red. The verifier caught it; the lesson is
    # that a glob over a results directory is a claim about what is in it.
    d11 = []
    for p in E11_JSON:
        d11.extend(r for r in json.load(open(p))
                   if r.get("model") == "llama3.2:3b")
    by_id = {i.id: i for i in INSTANCES}
    rec_by_id = {r["instance"]: r for r in all_e11()}
    per11, by11 = {}, {}
    for rec in d11:
        inst, r = by_id.get(rec["instance"]), rec_by_id.get(rec["instance"])
        if inst is None or r is None:
            continue
        chk = check_plan(rec["plan_text"], inst)
        v = e11_verdict(inst, r, chk.actions) if chk.parsed else ""
        per11.setdefault(rec["instance"], {})[rec["arm"]] = v
        by11.setdefault(rec["arm"], []).append(v)

    for arm, want in (("bare", 0.75),
                      ("filler_k1", 0.7222), ("filler_k2", 0.7778),
                      ("filler_k3", 0.6389),
                      ("same_k1", 0.4167), ("same_k2", 0.2778),
                      ("same_k3", 0.1111),
                      ("indep_k1", 0.3611), ("indep_k2", 0.25),
                      ("indep_k3", 0.0556)):
        vs = by11.get(arm, [])
        s_ = sum(v == "source" for v in vs)
        f_ = sum(v == "flip" for v in vs)
        claim(f"E11 {arm} flip rate",
              round(f_ / (s_ + f_), 4) if s_ + f_ else None, want, tol=0.001)

    def mc11(a, b):
        n01 = sum(1 for x in per11.values()
                  if x.get(a) == "flip" and x.get(b) not in (None, "flip"))
        n10 = sum(1 for x in per11.values()
                  if x.get(b) == "flip" and x.get(a) not in (None, "flip"))
        n = n01 + n10
        if n == 0:
            return None
        k = min(n01, n10)
        return min(2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n, 1.0)

    # H7: the dose-response that makes the H6 null informative.
    claim("E11 H7 step bare->same_k1 (dose-response exists)",
          round(mc11("bare", "same_k1") / 0.0004883, 2), 1.0, tol=0.02)
    claim("E11 H7 step same_k2->same_k3",
          round(mc11("same_k2", "same_k3") / 0.03125, 2), 1.0, tol=0.02)

    # H6: null at every k.
    for k, want in ((1, 0.5), (2, 1.0), (3, 0.625)):
        claim(f"E11 H6 same_k{k} vs indep_k{k} (must be null)",
              round(mc11(f"same_k{k}", f"indep_k{k}"), 4), want, tol=0.001)

    # H8: corroboration vs matched-length filler, large at every k.
    for k, want in ((1, 0.003418), (2, 7.629e-06), (3, 3.815e-06)):
        claim(f"E11 H8 filler_k{k} vs same_k{k} (corroboration)",
              round(mc11(f"filler_k{k}", f"same_k{k}") / want, 2), 1.0, tol=0.02)

    # THE NON-REPLICATION. E10's H1 said intervening text alone matters.
    for k in (1, 2, 3):
        p = mc11("bare", f"filler_k{k}")
        claim(f"E11 bare vs filler_k{k} is NULL (E10's H1 does not replicate)",
              p is None or p > 0.05, True)

    print("\n  NOTE: E11 does NOT rescue E10's overclaim. H6 is null at every k,")
    print("  but each contrast has at most 4 discordant pairs, so it is exactly")
    print("  as underpowered as E10 was and cannot establish equivalence either.")
    print("  E11's real contributions are H7 (0.75 -> 0.4167 -> 0.2778 ->")
    print("  0.1111, so the instrument demonstrably has room) and the H1")
    print("  NON-replication.")
    print("  But bare-vs-filler, which E10 reported at p = 0.0078, is null at")
    print("  all three k here. The DILUTION effect is unstable across corpus")
    print("  realisations; the CORROBORATION effect is not.")


# ------------------------------------- E11 across three model families -----
# Phase 6. The contrast replicated here is H8 (corroboration vs matched-length
# filler), NOT the retracted independence contrast.

print("\n=== E11 cross-model (re-derived from raw plan text) ===")
if not E11_JSON:
    skip("E11 cross-model", "not found")
else:
    per_model = {}
    for p in E11_JSON:
        for rec in json.load(open(p)):
            inst = by_id.get(rec["instance"])
            r = rec_by_id.get(rec["instance"])
            if inst is None or r is None:
                continue
            chk = check_plan(rec["plan_text"], inst)
            v = e11_verdict(inst, r, chk.actions) if chk.parsed else ""
            per_model.setdefault(rec["model"], {}).setdefault(
                rec["instance"], {})[rec["arm"]] = v

    def mc(per, a, b):
        n01 = sum(1 for x in per.values()
                  if x.get(a) == "flip" and x.get(b) not in (None, "flip"))
        n10 = sum(1 for x in per.values()
                  if x.get(b) == "flip" and x.get(a) not in (None, "flip"))
        n = n01 + n10
        if n == 0:
            return None, n01, n10
        k = min(n01, n10)
        return min(2 * sum(math.comb(n, i)
                           for i in range(k + 1)) / 2 ** n, 1.0), n01, n10

    claim("E11 ran on three deciders", len(per_model), 3)
    FAMILIES = {"llama3.2:3b": "Llama", "aya-expanse:8b": "Aya",
                "qwen2.5:7b-instruct": "Qwen"}
    claim("...from three DISTINCT families (scales of one family do not count)",
          len({FAMILIES.get(m) for m in per_model}), 3)

    h8_sig = h7_sig = h6_sig = 0
    for m, per in sorted(per_model.items()):
        p8 = mc(per, "filler_k3", "same_k3")[0]
        p7 = mc(per, "bare", "same_k3")[0]
        p6 = mc(per, "same_k3", "indep_k3")[0]
        h8_sig += p8 is not None and p8 < 0.05
        h7_sig += p7 is not None and p7 < 0.05
        h6_sig += p6 is not None and p6 < 0.05
    claim("E11 H8 (corroboration beats matched filler) significant in ALL "
          "three families", h8_sig, 3)
    claim("E11 H7 (dose-response) significant in all three", h7_sig, 3)
    claim("E11 H6 (independence) significant in NONE -- and underpowered in "
          "all three, so this is not evidence of absence", h6_sig, 0)

    # The power problem is universal, not a llama artefact.
    worst = max(sum(mc(per, "same_k3", "indep_k3")[1:])
                for per in per_model.values())
    claim("...max discordant pairs for H6 in any model (needs >=6 for p<.05)",
          worst <= 5, True)

    print("\n  Corroboration replicates across Meta, Cohere and Alibaba models.")
    print("  The independence contrast is null everywhere AND has at most 5")
    print("  discordant pairs in any model -- 6 are needed for p < 0.05, so no")
    print("  model could have detected it. The power ceiling is a property of")
    print("  the design, not of llama3.2:3b.")


# ----------------------------------------------------------- E12 ----------
# The experiment that earned what E10 asserted.

print("\n=== E12 powered independence (re-derived from raw plan text) ===")
from lineage_e12 import all_units as _all_units
from lineage_e12 import corpus_hash as e12_hash
from e12_powered import (cluster_bootstrap, cluster_permutation,
                         verdict as e12_verdict)

E12_JSON = sorted(glob.glob("results/e12_*_o*.json"))
if not E12_JSON:
    skip("E12 artifacts", "not found")
else:
    claim("E12 corpus fixture", e12_hash(), "ecf1f4884fa49270")
    u_by_id = {u["unit"]: u for u in _all_units()}
    claim("E12 unit count (108 propositions, not 36)", len(u_by_id), 108)
    claim("...in 36 instance clusters",
          len({u["instance"] for u in u_by_id.values()}), 36)

    d12 = []
    for p in E12_JSON:
        d12.extend(r for r in json.load(open(p))
                   if r.get("model") == "llama3.2:3b")
    per_unit = {}
    for rec in d12:
        u = u_by_id.get(rec["unit"])
        inst = by_id.get(rec["instance"])
        if u is None or inst is None:
            continue
        chk = check_plan(rec["plan_text"], inst)
        v = e12_verdict(inst, u, chk.actions) if chk.parsed else ""
        per_unit.setdefault(rec["unit"], {"instance": rec["instance"]})
        per_unit[rec["unit"]][rec["arm"]] = v

    units12 = list(per_unit.values())
    clusters = {}
    for d in units12:
        clusters.setdefault(d["instance"], []).append(d)

    for arm, want in (("bare", 0.8037), ("filler", 0.7407),
                      ("same_root", 0.2778), ("indep_root", 0.2963)):
        s_ = sum(u.get(arm) == "source" for u in units12)
        f_ = sum(u.get(arm) == "flip" for u in units12)
        claim(f"E12 {arm} flip rate",
              round(f_ / (s_ + f_), 4) if s_ + f_ else None, want, tol=0.001)

    p_perm, obs = cluster_permutation(clusters, "same_root", "indep_root")
    lo, hi = cluster_bootstrap(clusters, "same_root", "indep_root")
    claim("E12 PRIMARY observed difference", round(obs, 4), 0.0185, tol=0.0005)
    claim("E12 cluster-permutation p (instance-level swaps)",
          round(p_perm, 3), 0.749, tol=0.01)
    claim("E12 cluster-bootstrap CI lower", round(lo, 4), -0.0370, tol=0.005)
    claim("E12 cluster-bootstrap CI upper", round(hi, 4), 0.0741, tol=0.005)
    claim("E12 EQUIVALENCE HOLDS: |diff| < SESOI and CI inside +/-0.10",
          abs(obs) < 0.10 and lo > -0.10 and hi < 0.10, True)

    p_cor, obs_cor = cluster_permutation(clusters, "filler", "same_root")
    claim("E12 corroboration anchor is large", round(obs_cor, 3), -0.463,
          tol=0.005)
    claim("...and significant under clustering", p_cor < 0.001, True)

    p_dil, obs_dil = cluster_permutation(clusters, "bare", "filler")
    claim("E12 dilution is NULL again (third experiment running)",
          p_dil > 0.05, True)

    print("\n  E12 EARNS WHAT E10 ASSERTED. At 108 units in 36 clusters, with")
    print("  instance-level permutation and bootstrap, the independence effect")
    print("  is +0.0185 with a 95% CI of [-0.037, +0.074] -- entirely inside")
    print("  the preregistered SESOI of 0.10. That is an EQUIVALENCE-SUPPORTED")
    print("  null: positive evidence of no practically meaningful discount,")
    print("  not a failure to reject. The preregistered kill rule now fires")
    print("  legitimately, and the lineage direction is retired on evidence.")


# ----------------------------------------------------------- E13 ----------

print("\n=== E13 recognition -> utilization (re-derived from raw plan text) ===")
from lineage_e13 import build_prompt as e13_prompt
from lineage_e13 import corpus_hash as e13_hash
from lineage_bench import plan_instruction as _pi
from e13_recognition import _by_unit, differentiation, discordance

E13_CSV = sorted(glob.glob("results/e13_*_o*.csv"))
if not E13_CSV:
    skip("E13 artifacts", "not found")
else:
    claim("E13 prompt-corpus hash", e13_hash(_pi), "5c23297196241110")

    e13_rows = []
    for p in E13_CSV:
        e13_rows.extend(r for r in csv.DictReader(open(p, newline=""))
                        if r["model"] == "llama3.2:3b")
    claim("E13 row count (108 units x 10 cells)", len(e13_rows), 1080)
    claim("E13 parse rate is 1.00 everywhere (no parse-rate confound)",
          sum(r["parsed"] == "True" for r in e13_rows), 1080)

    # DEFAULT must be byte-identical to E12's prompt -- what makes RQ2 a
    # replication rather than a near one.
    u0 = _all_units()[0]
    from lineage_e12 import exposure as _e12x, render as _e12r
    pi0 = _pi(by_id[u0["instance"]])
    claim("E13 default prompt is byte-identical to E12's",
          e13_prompt(u0, "same_root", "default", pi0)
          == f"DISCUSSION\n----------\n{_e12r(_e12x(u0, 'same_root'))}\n\n{pi0}",
          True)

    for arm, d_want, p_want, disc_want in (
            ("default", 0.0, 1.0, 0.093),
            ("identify", -0.0093, 1.0, 0.139),
            ("normative", -0.0741, 0.0564, 0.148),
            ("sham", -0.037, 0.2946, 0.074),
            ("gold", 0.0, 1.0, 0.075)):
        per, dropped = _by_unit(e13_rows, arm)
        d = differentiation(per)
        disc, _ = discordance(per)
        claim(f"E13 {arm} differentiation", round(d["diff"], 4), d_want,
              tol=0.0005)
        claim(f"E13 {arm} cluster-permutation p", round(d["p"], 4), p_want,
              tol=0.01)
        claim(f"E13 {arm} discordance", round(disc, 3), disc_want, tol=0.002)

    # RQ2: the replication, and it must be equivalence-supported.
    per, _ = _by_unit(e13_rows, "default")
    d = differentiation(per)
    claim("E13 RQ2 DEFAULT replicates E12 as an EQUIVALENCE-SUPPORTED null",
          abs(d["diff"]) < 0.10 and d["lo"] > -0.10 and d["hi"] < 0.10, True)
    dd, _ = discordance(per)
    claim("...and its discordance is INSIDE the powered band [0.08, 0.12]",
          0.08 <= dd <= 0.12, True)

    # RQ1b: the count discriminates under identify, and NOT under normative.
    def count_sign(arm):
        per_c = {}
        for r in e13_rows:
            if r["intervention"] == arm and r["recog_count"] != "":
                try:
                    per_c.setdefault(r["unit"], {})[r["dependence"]] = int(
                        r["recog_count"])
                except ValueError:
                    pass
        hi = sum(1 for v in per_c.values()
                 if len(v) == 2 and v["indep_root"] > v["same_root"])
        lo = sum(1 for v in per_c.values()
                 if len(v) == 2 and v["indep_root"] < v["same_root"])
        n, k = hi + lo, min(hi, lo)
        return hi, lo, (min(2 * sum(math.comb(n, i)
                                    for i in range(k + 1)) / 2 ** n, 1.0)
                        if n else None)

    hi, lo, p = count_sign("identify")
    claim("E13 identify: reported count discriminates (indep > same)", hi, 49)
    claim("...against", lo, 2)
    claim("...sign test p", p < 1e-10, True)
    hi2, lo2, p2 = count_sign("normative")
    claim("E13 normative: count discrimination (post-hoc paired test; NOT "
          "'degrades' -- E13-CORRECTIONS section 2)", hi2, 36)
    claim("...against", lo2, 25)
    claim("...within-arm sign p > 0.05 (no between-arm test exists)",
          p2 > 0.05, True)

    # CORRECTIONS 2026-09-01 (docs/protocols/E13-CORRECTIONS.md). The count
    # sign test above is POST-HOC (added 459fc88 after o0.csv existed). The
    # PRIMARY boolean paired the same way shows the fields do not disagree.
    def bool_sign(arm):
        perb = {}
        for r in e13_rows:
            if r["intervention"] == arm and r["recog_bool"] != "":
                perb.setdefault(r["unit"], {})[r["dependence"]] = (
                    r["recog_bool"] == "True")
        bh = sum(1 for v in perb.values()
                 if len(v) == 2 and v["same_root"] and not v["indep_root"])
        bl = sum(1 for v in perb.values()
                 if len(v) == 2 and v["indep_root"] and not v["same_root"])
        return bh, bl

    bh, bl = bool_sign("identify")
    claim("E13 identify: PRIMARY boolean paired, same=T & indep=F", bh, 40)
    claim("...reversed", bl, 0)
    bh2, bl2 = bool_sign("normative")
    claim("E13 normative: PRIMARY boolean paired, same=T & indep=F", bh2, 34)
    claim("...reversed", bl2, 4)
    both_wrong = sum(1 for r in e13_rows
                     if r["intervention"] == "identify"
                     and r["dependence"] == "indep_root"
                     and r["recog_bool"] == "True" and r["recog_count"] == "1")
    claim("E13 identify INDEP: units misrecognised by BOTH measures "
          "(same=True and count=1)", both_wrong, 42)
    claim("E13 identify INDEP: predeclared count_strict, never reported in "
          "418bab2",
          round(sum(r["recog_count_score"] == "strict" for r in e13_rows
                    if r["intervention"] == "identify"
                    and r["dependence"] == "indep_root") / 108, 3), 0.13)

    # THE `ready` FIELD -- post-hoc, found by the panel, E13-CORRECTIONS
    # section 3. Re-derived from raw plan text with the same cluster machinery.
    from lineage_eval import parse_plan as _pp13
    _det13 = []
    for pth in sorted(glob.glob("results/e13_*_o*.json")):
        with open(pth) as f:
            _det13.extend(json.load(f))

    def ready_pairs(detail, arm_key, arm, same="same_root", indep="indep_root"):
        by = {}
        for d in detail:
            if d.get("model", "llama3.2:3b") != "llama3.2:3b":
                continue
            if arm is not None and d[arm_key] != arm:
                continue
            plan, _ = _pp13(d["plan_text"])
            u = by.setdefault(d["unit"], {"instance": d["instance"]})
            if plan is not None:
                u[d["dependence" if arm is not None else "arm"]] = (
                    "flip" if plan["ready"] else "source")
        return {k: v for k, v in by.items() if same in v and indep in v}

    for arm, want, lo_want in (("default", 0.2315, 0.139),
                               ("gold", 0.2037, 0.120)):
        per_r = ready_pairs(_det13, "intervention", arm)
        rd = differentiation(per_r)
        claim(f"E13 {arm}: READY(same) - READY(indep), post-hoc",
              round(rd["diff"], 4), want, tol=0.0005)
        claim("...cluster-permutation p < 0.001", rd["p"] < 0.001, True)
        claim("...cluster-bootstrap CI lower bound", round(rd["lo"], 3),
              lo_want, tol=0.002)
        claim("...which EXCEEDS the SESOI of 0.10", rd["lo"] > 0.10, True)

    _det12 = []
    for pth in sorted(glob.glob("results/e12_*_o*.json")):
        with open(pth) as f:
            _det12.extend(json.load(f))
    per_r = ready_pairs(_det12, "arm", None)
    rd = differentiation(per_r)
    claim("E12 raw plans: READY(same_root) - READY(indep_root), post-hoc",
          round(rd["diff"], 4), 0.2593, tol=0.0005)
    claim("...cluster-permutation p < 0.001", rd["p"] < 0.001, True)
    claim("E12 same_root plans declared ready",
          sum(u["same_root"] == "flip" for u in per_r.values()), 60)
    claim("E12 indep_root plans declared ready",
          sum(u["indep_root"] == "flip" for u in per_r.values()), 32)

    print("\n  E13 REPLICATES E12 EXACTLY on a byte-identical prompt, ON THE")
    print("  ORDERING VERDICT: DEFAULT differentiation +0.0000, CI")
    print("  [-0.056,+0.056], discordance 0.093 inside the powered band. No")
    print("  intervention moved the ORDERING; GOLD moved it by 0.0000 (and is")
    print("  INCONCLUSIVE BY RULE, not an 'oracle null'). identify and")
    print("  normative are INCONCLUSIVE BY THE PREREGISTERED RULE.")
    print("  CORRECTION 2026-09-01 (docs/protocols/E13-CORRECTIONS.md): the")
    print("  `ready` field of the same plan IS dependence-sensitive in every")
    print("  arm (~+0.2, cluster p < 0.001) and in E12. 'Prices one root")
    print("  exactly as k independent roots' is WITHDRAWN as a decision-level")
    print("  claim; it survives only for the ordering channel.")


# ------------------------------------------------------ E6 router facts ----

print("\n=== E6 router: the measurement that killed AnchorRoute ===")
try:
    from retrieval import ENCODER
    cor_src, fth_src = [], []
    for inst in INSTANCES:
        ch = build_chain(inst)
        docs = [ch.source.text] + [m.text for m in ch.faithful] + [ch.corrupted[0].text]
        v = ENCODER.encode(docs)
        sim = v @ v.T
        cor_src.append(sim[4][0])
        fth_src.extend(sim[i][0] for i in (1, 2, 3))
    claim("contradiction is at least as similar to the source as the "
          "LEAST similar faithful restatement, in all 36",
          sum(1 for c in cor_src if c >= min(fth_src)), 36)
    claim("mean cos(contradiction, source) exceeds mean cos(faithful, source)",
          statistics.mean(cor_src) > statistics.mean(fth_src), True)
except Exception as exc:                       # pragma: no cover
    skip("E6 similarity facts", f"encoder unavailable: {exc}")


# ------------------------------------------------- cross-corpus results ----
# E1/E2/E4 were scored against EARLIER corpora. Saying so is the point.

print("\n=== results scored against earlier corpora ===")
for pattern, name in (("results/e1_runs.csv", "E1 landscape"),
                      ("results/e2_matrix_runs.csv", "E2 exposure matrix"),
                      ("results/e4_summary.csv", "E4 authority")):
    if os.path.exists(pattern):
        skip(f"{name} ({pattern})",
             "scored against an earlier corpus fixture; not re-derivable here")

print("\n" + "=" * 64)
print(f"  {_state['ok']} verified, {_state['bad']} mismatched, "
      f"{_state['skip']} unverifiable")
print(f"  corpus {CORPUS}")
if _state["bad"]:
    print("  FAIL: a reported number does not re-derive from its artifacts.")
    sys.exit(1)
print("  OK")
