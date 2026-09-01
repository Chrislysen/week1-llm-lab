# Research-lead memo — what is still standing, 2026-09-02

**Bottom line.** After re-reading every artifact, mining the one variable the
project had never analysed, six adversarial reviews (about 150 searches), and
two declared exploratory screens on three further deciders, the novelty space
this project was chasing is **closed**. The dependence null on the substantive
decision is real and replicated but already published. The readiness effect
that E13's audit discovered is real in one 3B model, is a repetition and
consistency effect rather than a dependence effect, is absent in the only
other decider whose readiness varies, and its abstraction is already published
and named. The normative-principle backfire is real in the same one model,
already shown on that model by KAIROS, and absent in two other families. The
instrument is a resource, not a contribution.

This is outcome **E** in the brief: a rigorous negative that says stop. E14
stays aborted and no E14-v2 is opened. Nothing here is a paper claim.

---

## 1. What was investigated

1. **Reconstruction from raw artifacts.** E1–E14, every tag, every protocol,
   both retractions, the verifier, the git history. All checks green
   throughout: 167 verified / 0 mismatched, 13 suites, every frozen hash.
2. **Latent-variable mining.** The plan field `ready` ("true if you consider
   the plan safe to execute as written") was re-parsed from every raw plan on
   disk — E2 (9 exposure conditions), E4 (5 deciders × rule variants), E7,
   E8 (5 deciders), E9, E10 (9 arms), E11 (3 deciders × 10 arms), E12, E13.
   Outside E13's audit it had never been analysed.
3. **Six adversarial reviewers**, each told to destroy: prior art for the
   readiness dissociation (43 searches, 32 papers); prior art for the
   instrument (36 searches; two summariser claims checked against PDFs and
   rejected); a confound review computed from raw files; the human-cognition
   literature on dependent evidence (35 papers); causal design after the
   FIXED floor; prior art for the normative backfire (33 searches).
4. **Two exploratory screens**, declared in git with zero outcomes before
   running, hypothesis-blind in decider choice, unable to become claims:
   Qwen-14B's readiness on the frozen E12 corpus (E12-X, 432 calls); the
   normative backfire on Aya-8B and Qwen-7B (E13-X, 1296 calls; the third
   decider was not run because the declared rule was already decided).
5. **Re-derivation.** Every load-bearing number a reviewer produced was
   recomputed from raw output before being written anywhere.

## 2. What died

| candidate | how it died |
|---|---|
| **Readiness dissociation as a general finding (C9)** | The channel does not exist outside two deciders: Aya-8B, Qwen-3B and Qwen-7B answer `ready = true` in at least 358 of 360 responses in every arm of E4, E8 and E11. The abstraction — an evidence property moves the act/commit gate while judgment stays put — is published and named (arXiv:2608.27167), and Whose Facts Win (arXiv:2601.03746) ran the same-source-twice contrast on Llama-3.2-3B with an abstention channel at floor. The declared Qwen-14B screen, the only other decider with a varying channel, shows −0.046 with CI [−0.111, +0.018]: no effect in llama's direction. |
| **Readiness as a *dependence* effect (C10)** | On E11's nested dose curve, same-root readiness *rises* with each repetition of the identical citation (19 → 21 → 27; k1 vs k3 paired 0/8, p = 0.008) while independent-root readiness is flat (17, 17, 17). Adding two agreeing reports of either kind *lowers* readiness from about 0.78 to about 0.5 (bare > same in E10 10/2, E11 11/2 and 12/1, E12 31/8). The gap runs from +0.5 to 0 by which document names the rotation draws (platform spec 24/0; incident review 1/0). `ready = true` in 129/242 responses where the model itself wrote *same source* and 1/190 where it wrote *different*. Qwen-14B's readiness moves the opposite way with corroboration (0.40 → 0.88). The human literature has no case of independent corroboration lowering commitment below no corroboration, and conflict-aversion and consistency heuristics produce exactly this ordering. |
| **E14 in any form** | The best remaining design (three-arm section-locator, 1320 calls) separates citation-count diversity from document independence but cannot separate "represents independence" from "reads distinct names as disagreement", and only on the one decider that has the channel. E14-v1 stays ABORTED; no v2. |
| **The benchmark as a contribution (C11)** | Its founding premise — every conflict benchmark treats the source as the answer key — is false: ManyIH-Bench (arXiv:2604.09443) and IHEval (NAACL 2025) already build contexts where neither position heuristic can win; a family of memory benchmarks rewards the latest statement; Manufactured Confidence crosses forged and legitimate authority with ground truth by construction. Corrected in `docs/agent-lineage-bench.md` with the original sentence left standing. |
| **The verification apparatus as methodology (C12)** | Prospective paired-design power with discordance dependence and clustering ships as a package (Kotawala 2026, `llm-power`); preregistered TOST with precomputed n and synthetic self-validation (arXiv:2606.16511); regenerate-every-number-from-raw (showyourwork); agentic falsification panels (POPPER; arXiv:2604.22080). |
| **Latest-trusters (C13)** | IHEval: Qwen-2 7B at 16.4 % on conflicts and an explicit priority prompt that does not help; Control Illusion: GPT-4o at 63.8 % with emphasised separation; PRIME: small models are not uniformly latest-preferring. E3/E4 replicate this in a new format. |
| **Normative backfire (C14)** | Real in llama (+0.10 pooled, 29 vs 7, cluster p 0.006; the principle's own contribution +0.09 over the structure-matched control). KAIROS (arXiv:2508.18321) already shows on Llama-3.2-3B that a critical-evaluation prompt worsens peer-pressure robustness; "blanket skepticism" and "algorithmic ironic rebound" are the names. The declared screen found the principle's effect +0.037 in Aya-8B and +0.005 in Qwen-7B: llama-specific. |

## 3. What survived

- **The ordering-channel equivalence null** (E12, replicated byte-for-byte
  by E13's default arm): +0.0185, CI [−0.037, +0.074]; +0.0000, CI [−0.056,
  +0.056]; preregistered SESOI 0.10; 108 units in 36 clusters with
  instance-level inference. Sound. Not novel (GroupQA, arXiv:2601.06189, on
  four larger models).
- **The corroboration dose-response in three families** (E11): 0.75 → 0.42
  → 0.28 → 0.11 in llama, replicated in Aya and Qwen-7B. Sound. Not novel
  (Xie et al. 2024; Jin et al. 2024; the repetition literature).
- **A characterised single-model artefact**: llama-3B's `ready` token is a
  readout of perceived uniformity of citations. Well enough understood to
  say what it is not. Not claimable.
- **Two model-specific prompt effects, observed and not claimed**: the
  principle backfires only in llama; the structured "state the evidence
  structure first" request reduces adoption by 0.17 only in Qwen-7B.

## 4. What is actually new versus merely interesting

New to this project but not to the literature: the null and the
dose-response. Interesting but not new: the readiness effect (a named
commit-gate effect; a repetition effect), the backfire (a named prompt
backfire on this very model), the benchmark (instruction-hierarchy benchmarks
got there with more items). Nothing in the repository is both new and
general.

## 5. Strongest evidence

- For the null: preregistration with zero outcomes, a prospective power
  check, clustering handled, a byte-identical replication, and every number
  re-derived from raw text by `verify_claims.py`.
- For the readiness reinterpretation: E11's arms are nested prefixes — going
  from k to k+1 adds one message and shows nothing else — so the rise of
  same-root readiness with k is the effect of one more identical citation and
  nothing else; and the Qwen-14B screen shows the sign of the corroboration
  effect on readiness is not even stable across deciders.

## 6. Strongest remaining threat to the closing verdict

That a decider with a genuine, non-degenerate abstention or readiness
channel — larger, or trained to abstain — would show a dependence-sensitive
commitment gate with the substantive decision invariant. The local evidence
only shows that in the two deciders with any readiness variance the effect is
absent (Qwen-14B) or is repetition (llama). Testing that is a new programme
with a new decider and a decider-eligibility protocol, not a continuation of
this one, and arXiv:2608.27167 already owns the framing it would land in.

## 7. What changed in the repository

- `docs/novelty_matrix.md`: rows C9–C14 in the candidate / closest work /
  what it showed / what ours shows / overlap / distinction / experiment /
  status format, with a search log. No row is NOVEL.
- `docs/agent-lineage-bench.md`: the false premise corrected in place.
- `docs/protocols/E12X-qwen14b-ready-screen.md`,
  `docs/protocols/E13X-backfire-screen.md`, `e13x_backfire_screen.py`,
  `screen_analysis.py`: the two declared exploratory screens, their
  outcomes, and their reader.
- `results/e12_qwen25-14b-instruct_*`, `results/e13x_*`: screen outputs,
  exploratory, never entering a claim; the verifier filters them out and
  still reports 167 verified / 0 mismatched.
- `docs/findings.md`, `docs/CLAIM-E13.md`, `docs/RESUME.md`: propagated.
- Nothing frozen was touched; every historical hash re-verifies.

## 8. Should this become a paper?

**Not as a findings paper.** Every behavioural row is pre-empted, closed,
or single-model. **Possibly as a short negative-results or reproducibility
report**, if the case history is judged useful: seven results retracted by
their own controls; a p = 1.0 null read as a plateau, caught twice; an E10
conclusion reported against its own preregistered output; a post-hoc channel
found by one adversarial panel and dismantled by another; and a confirmatory
experiment correctly aborted by its own design rule after 149 blind pilot
calls. The reviewers rated the methodology components pre-empted, so the
value would be the record, not the method.

## 9. The exact next step

None inside this programme. If the project continues at all, it continues
as the negative-results write-up in §8, drawn from `docs/findings.md`,
`docs/novelty_matrix.md`, the two retraction documents and this memo — with
no new model calls.
