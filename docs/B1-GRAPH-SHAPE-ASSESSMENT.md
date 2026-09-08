# Decision memo — does B1's graph-shape observation support a next experiment?

Zero model calls. Assesses the observation in `docs/B1-REPORT.md`; B1 stays
exploratory and its records are unchanged.

## Recommendation: STOP. Do not run the graph-shape experiment.

The observation is **not identified** by B1's design, and the two mechanisms that
would make it interesting are respectively **contradicted by our own data** and
**already covered by prior work**.

## 1. Units of evidence — the reported counts were pseudo-replication

| shape | distinct instances | domains | arm runs |
|---|---|---|---|
| chain | **1** | payments | 3 |
| fork | **1** | robotics | 3 |
| join | **1** | pharmacy | 3 |
| star | **1** | rail | 3 |
| diamond | 2 | satellite, payments | 6 |
| twochain | 2 | brewery, robotics | 6 |

B1 reported "twochain 0/6, fork 3/3". Those denominators are **arm runs on 1–2
instances**, not independent instances. Three arms on one instance share the
instance's wording, identifiers and description order, so they are correlated,
not replicates. **For four of six shapes, shape is perfectly confounded with
domain.**

**Withdrawn:** "task structure dominates communication architecture." B1 shows no
demonstrated architecture difference *and* no identified shape effect. The
supported statement is: **most observed variation in B1 sits at the instance
level, with 1–2 instances per shape and no control for wording, identifiers or
description order; neither an architecture effect nor a shape effect is
identified.** Absence of a demonstrated architecture difference is not evidence
of architectural equivalence.

## 2. The decisive internal check: within-shape ≈ between-shape

Per-instance mean violations (3 correlated arm runs each):

| shape | instance means | within-shape gap |
|---|---|---|
| **diamond** | payments **0.33**, satellite **2.33** | **2.00** |
| twochain | brewery 2.33, robotics 2.33 | 0.00 |

Between-shape range of shape means: **0.00 (fork) to 2.33 (twochain) = 2.33**.

**The largest within-shape gap (2.00) is nearly the entire between-shape range
(2.33).** Two instances of the *same* shape, differing only in domain, span
almost the full spread I attributed to shape.

## 3. Graph properties — the natural mechanism runs backwards

Valid full permutations of the 6 identifiers (of 720), computed exactly:

| shape | nodes | before-edges | required | components | valid perms | mean violations |
|---|---|---|---|---|---|---|
| chain | 5 | 4 | 2 | 1 | **6** | 1.33 |
| fork | 5 | 5 | 2 | 1 | 12 | **0.00** |
| join | 5 | 4 | 3 | 1 | 12 | 1.33 |
| diamond | 5 | 5 | 3 | 1 | 12 | 1.33 |
| **twochain** | 6 | 4 | 3 | **2** | **20** | **2.33** |
| star | 5 | 4 | 3 | 1 | **144** | 1.00 |

- **Solution-space size does not explain difficulty, and points the wrong way.**
  `twochain` has *more* valid orderings than chain, fork, join and diamond, yet
  scored worst. `chain` has the *fewest* (6) and scored mid-pack.
- **`fork` and `diamond` are matched on nodes, edges and valid permutations (12)**
  and differ by 1.33 mean violations — while two *diamond* instances differ by
  2.00. Structural features do not separate them; instance identity does.
- `twochain` is the only 2-component shape, but it is also the only shape (with
  diamond) using all 6 identifiers, and it is confounded with domain.

**Structural features of interest:** component count, chain depth, required-node
count. **Uncontrolled instance differences:** domain setting, action identifiers,
natural-language wording, message order, and the display order of identifiers —
which `lineage_bench` *deliberately* randomises to a **non-topological** order
(`generate_instance` rejects topological display orders), varying per instance.

## 4. Prior-work overlap — GraphDO covers the presentation half

[Ge et al., "Can Graph Descriptive Order Affect Solving Graph Problems with
LLMs?", ACL 2025 (acl-long.321)](https://aclanthology.org/2025.acl-long.321/):

- **T5 is Topological Sort** — "generate a linear ordering ... such that for every
  directed edge (u,v), u precedes v ... multiple correct solutions may exist."
  Exactly our task.
- Compares **Random / BFS / DFS / PageRank / Personalized PageRank** description
  orders. Finding: "ordered graph descriptions consistently outperform the random
  baseline across all traditional graph tasks" (connectivity 89.43 % BFS vs
  78.36 % random; cycle 72.71 % vs 64.50 %), with TopoSort showing a large
  order-dependent spread in Fig. 3.
- Graphs are **Erdős–Rényi**; topology class is *not* systematically varied, and
  disconnectedness appears only as a description-generation detail ("for a
  disconnected graph, the root node will be reselected randomly until the graph
  is fully described ... does not alter the topology").

**Consequence.** B1's descriptions are effectively *random order* — GraphDO's
worst condition — and that order is uncontrolled and confounded with shape. The
presentation half of the residual is **COVERED**. The remaining residual is
narrow: *does topology class (disjoint components vs connected) affect
constrained-ordering accuracy holding description order fixed?* GraphDO does not
answer it; targeted searches did not surface a direct treatment, so that is
**UNRESOLVED coverage, not novelty**.

## 5. The brewery regression, checked directly

**It survives the prose check, with a caveat.** The refined drafts contain
**explicit plan blocks** ("Revised Plan: 1. DRAIN_VESSEL 2. RESEED_YEAST …"), and
the surrounding prose uses natural language ("reseeding the yeast"), not the
identifiers — so the first-occurrence scan recovered the stated plan, not prose
mentions. The solo draft (v=1) → aggregate (v=3) regression is real.

**But it is one instance**, three correlated arms, and it is *not* the corpus's
dominant behaviour. Across all 24 arm-runs:

- **16 of 18 invalid plans were emitted with `ready: true`** — silent failure.
- Only **2 of 18 (11 %)** were self-flagged `ready: false`.
- **0 clean plans were needlessly refused** — the flag has perfect precision and
  ~11 % recall.

The brewery case I highlighted is **one of the two self-flagged exceptions**, not
the pattern. In it the model emitted a plan violating K6 and then correctly wrote
that it violated K6 — detecting the error without fixing it. That is the shape of
this repo's own E23 knowledge–action gap and of STALE's retrieve-vs-act gap; it is
not new, and n=1 supports nothing.

## 6. Strongest alternative explanation

**Uncontrolled instance-level variation.** With 1–2 instances per shape, shape
confounded with domain in four of six cases, description order randomised
per-instance in the condition GraphDO identifies as worst, and a within-shape gap
as large as the entire between-shape range — the ranking across shapes is
consistent with instance-level noise plus description-order effects, and the
solution-space measure that would support a topology account points the opposite
way.

## 7. What a valid design would require (specified, not recommended)

Recorded so it need not be re-derived; **not** endorsed on current evidence.

- **Matched graph families**: ≥10 fresh instances *per shape*, with shape crossed
  against domain so neither is confounded with identifiers or wording.
- **Crossed presentation**: description order (topological / reverse / random) ×
  identifier labelling (semantic / arbitrary) × constraint statement order,
  applied to the *same* underlying graphs. Without this the topology question
  cannot be separated from GraphDO's established effect.
- **Estimand**: the shape contrast (disjoint vs connected) on violation count,
  holding description order fixed, with **instance as the unit** and arms nested
  within instance — arm runs are not replicates.
- **More models do not substitute for these controls**, and every B1 instance is
  burned as development data.
- **Deterministic topological-sort baseline**: on the *gold* constraint set it is
  a **gold-graph oracle**, not an end-to-end comparator — it skips the
  natural-language extraction the model must perform, so it upper-bounds ordering
  competence only. An end-to-end comparator would have to extract constraints
  from text and then sort, which reintroduces extraction as a confound. Report
  them as two different quantities, never as one baseline.

## 8. Decision

**Stop.** No experiment is justified. The observation is unidentified in B1, its
natural mechanism is contradicted by our own solution-space counts, its
presentation half is covered by GraphDO, and the follow-up case reduces to a
known knowledge–action gap on a single instance. B1 is retained as engineering
evidence exactly as reported; no candidate is opened; the ledger stays 22 gated,
22 closed. E27, E28 and C2 remain closed.
