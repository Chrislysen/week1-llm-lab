"""agentcom_bundle.py: OPT-IN snapshot/selection interface + the shared schema.

Phase A/B scaffolding for the message-bundle direction
(`docs/AGENTCOM-BUNDLE-SPEC.md`, protocol `docs/protocols/PHASE-B-bundle-observability.md`).

WHAT THIS IS NOT
----------------
There is **no learned controller here, and nothing in this module is claimed to
be novel.** `QuadraticUtility` holds coefficients that somebody must supply;
`anchored_expansion` is an exact degree-2 expansion of a *supplied* utility, not
a learner and not an estimator of anything on unseen data. No model call is made
anywhere in this file. Selection quality on real decisions is unmeasured.

OPT-IN, BY CONSTRUCTION
-----------------------
Nothing here is imported by `engine.py`, `context.py`, `finalise.py` or any
existing experiment. `SnapshotPolicy` is a `ContextPolicy` subclass, so it can be
passed to `DialogueEngine(manage_context=...)` *when a caller chooses to*, and
its default behaviour is a pass-through that only records. Frozen protocols,
results and corpora are untouched.

BUDGET ACCOUNTING
-----------------
The budget is charged against the **rendered** bundle, separators and fixed
overhead included -- not against the sum of standalone message lengths. Those
two differ, and `additive_estimate` is provided only as the cheap preliminary
figure the spec warns about. `serialised_cost` is the one selection uses.
"""
from dataclasses import asdict, dataclass, field
from itertools import combinations
import math

from context import ContextPolicy, words

#: Bump on any incompatible change to the records below. The data and model
#: worktrees share these shapes; they are the interface contract.
SCHEMA_VERSION = "agentcom-bundle/1"

#: Exact subset enumeration is exponential. The laboratory is deliberately small.
MAX_CANDIDATES = 16

#: Rendering of a delivered bundle. Fixed here so cost is reproducible.
BUNDLE_HEADER = "Messages from your teammates:"
BUNDLE_SEP = "\n\n"


# --- shared schema --------------------------------------------------------


@dataclass(frozen=True)
class Candidate:
    """One offerable message. `source_id` preserves lineage; see lineage_*."""
    cid: str
    text: str
    source_id: str | None = None
    version: str | None = None

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class DecisionPoint:
    """Everything needed to replay one recipient call under a chosen subset.

    Records the literal prompt and the exact generation configuration, because a
    replay that cannot reproduce the original call is not a counterfactual.
    """
    dp_id: str
    task_id: str
    recipient_prompt: str
    recipient_context: str
    candidates: tuple
    budget: int
    model: str
    decoding: dict
    process_id: str
    request_position: int
    schema_version: str = SCHEMA_VERSION

    def to_dict(self):
        d = asdict(self)
        d["candidates"] = [c.to_dict() if isinstance(c, Candidate) else c
                           for c in self.candidates]
        return d


@dataclass(frozen=True)
class SubsetOutcome:
    """The scored result of replaying one decision point with one subset."""
    dp_id: str
    subset: tuple
    rendered_cost: int
    prompt_tokens: int
    completion_tokens: int
    seconds: float
    response: str
    score: float
    scorer: str
    extra: dict = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self):
        return asdict(self)


# --- budget accounting ----------------------------------------------------


def render_bundle(candidates, subset) -> str:
    """The literal text delivered for `subset`, in stable candidate order."""
    by_id = {c.cid: c for c in candidates}
    chosen = [by_id[i] for i in sorted(subset)]
    if not chosen:
        return ""
    return BUNDLE_HEADER + BUNDLE_SEP + BUNDLE_SEP.join(c.text for c in chosen)


def serialised_cost(candidates, subset) -> int:
    """Budget charge for `subset`: the rendered bundle, overhead included."""
    return words(render_bundle(candidates, subset))


def additive_estimate(candidates, subset) -> int:
    """Sum of standalone message lengths. PRELIMINARY ONLY.

    Kept so the gap against `serialised_cost` is visible rather than assumed
    away: the header and separators are real budget the additive figure misses.
    """
    by_id = {c.cid: c for c in candidates}
    return sum(words(by_id[i].text) for i in subset)


# --- utility representation (coefficients in, nothing learned) ------------


@dataclass(frozen=True)
class QuadraticUtility:
    """base + sum unary_i + sum pair_ij. Coefficients are SUPPLIED, not fitted."""
    base: float
    unary: dict
    pairs: dict

    def __call__(self, subset) -> float:
        s = set(subset)
        return (self.base
                + sum(self.unary[i] for i in s)
                + sum(v for (i, j), v in self.pairs.items() if i in s and j in s))


def anchored_expansion(ids, utility) -> QuadraticUtility:
    """Exact degree-2 anchored expansion of a SUPPLIED utility function.

    DIAGNOSTIC ONLY. It calls `utility` on the empty set, singletons and pairs,
    so it presupposes the very outcome table a deployed controller would not
    have. It is not a learner, not a predictor, and not usable on unseen tasks.
    It exists to measure how much a degree-2 form misses (see `max_residual`).
    """
    ids = tuple(sorted(ids))
    base = utility(frozenset())
    unary = {i: utility(frozenset([i])) - base for i in ids}
    pairs = {(i, j): utility(frozenset([i, j])) - base - unary[i] - unary[j]
             for i, j in combinations(ids, 2)}
    return QuadraticUtility(base, unary, pairs)


def all_subsets(ids):
    ids = tuple(sorted(ids))
    for k in range(len(ids) + 1):
        for g in combinations(ids, k):
            yield frozenset(g)


def max_residual(ids, utility, estimate) -> float:
    """Largest |true - degree2| over every subset. Non-zero => higher order."""
    return max(abs(utility(s) - estimate(s)) for s in all_subsets(ids))


# --- selection ------------------------------------------------------------


def _validate(ids, budget):
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("budget must be a non-negative integer")
    if len(ids) > MAX_CANDIDATES:
        raise ValueError(f"exact selection is capped at {MAX_CANDIDATES} candidates")
    if any(not isinstance(i, str) or not i for i in ids):
        raise ValueError("candidate ids must be non-empty strings")


def exact_select(ids, budget, utility, cost_of):
    """Maximise `utility` subject to `cost_of(subset) <= budget`.

    `cost_of` takes the whole subset, not per-item costs, so a caller can charge
    the rendered serialisation rather than a sum that ignores separators.
    The empty set is always a legal choice. Ties: lower cost, then lexicographic.
    """
    _validate(ids, budget)
    best, best_key = frozenset(), None
    for s in all_subsets(ids):
        c = cost_of(s)
        if c > budget:
            continue
        v = float(utility(s))
        if not math.isfinite(v):
            raise ValueError("utility must be finite")
        key = (-v, c, tuple(sorted(s)))
        if best_key is None or key < best_key:
            best, best_key = s, key
    return best


def select_bundle(ids, budget, estimate, cost_of):
    """Deployment-shaped selection: coefficients only, never an outcome oracle.

    Deliberately cannot accept a utility callable -- a controller that could
    would be reading the answer table it is supposed to predict.
    """
    if not isinstance(estimate, QuadraticUtility):
        raise TypeError("select_bundle takes predicted coefficients, not an oracle")
    ids = tuple(sorted(ids))
    if set(estimate.unary) != set(ids):
        raise ValueError("unary coefficients must cover exactly the candidate ids")
    for k in estimate.pairs:
        if len(k) != 2 or k[0] >= k[1] or any(i not in ids for i in k):
            raise ValueError("pair keys must be two distinct sorted known ids")
    vals = [estimate.base, *estimate.unary.values(), *estimate.pairs.values()]
    if not all(math.isfinite(float(v)) for v in vals):
        raise ValueError("coefficients must be finite")
    return exact_select(ids, budget, estimate, cost_of)


def conditional_greedy(ids, budget, utility, cost_of):
    """Comparator: re-computes exact marginal value per unit cost after each add.

    A strong singleton baseline. NOT an implementation of RepoShapley, QUBO
    selection, ProxySPEX or any other published system, and not a stand-in for
    one; naming it as such would be the weak-namesake error the spec warns of.
    """
    _validate(ids, budget)
    sel = frozenset()
    while True:
        cur = utility(sel)
        offers = []
        for i in sorted(ids):
            if i in sel:
                continue
            nxt = sel | {i}
            c = cost_of(nxt) - cost_of(sel)
            if cost_of(nxt) > budget or c <= 0:
                continue
            offers.append(((utility(nxt) - cur) / c, i))
        if not offers:
            return sel
        gain, pick = sorted(offers, key=lambda p: (-p[0], p[1]))[0]
        if gain <= 1e-12:
            return sel
        sel = sel | {pick}


# --- opt-in snapshot adapter ---------------------------------------------


class SnapshotPolicy(ContextPolicy):
    """Records every hook call; optionally substitutes a chosen bundle.

    Default behaviour is a PASS-THROUGH: it returns the message list unchanged
    and only records. That is what makes it safe to attach to an existing run.

    `deliver` (optional) is a callable (messages, candidates) -> subset ids. It
    receives no outcome table and no evaluator state; it is where a predictor
    would eventually sit. When None, nothing is substituted.
    """

    name = "snapshot"

    def __init__(self, candidates=(), budget=None, deliver=None):
        super().__init__()
        self.candidates = tuple(candidates)
        self.budget = budget
        self.deliver = deliver
        self.snapshots = []

    def config(self) -> dict:
        return {"schema_version": SCHEMA_VERSION,
                "n_candidates": len(self.candidates),
                "budget": self.budget,
                "delivering": self.deliver is not None}

    def select(self, messages, query=None):
        subset = frozenset()
        if self.deliver is not None and self.candidates:
            subset = frozenset(self.deliver(messages, self.candidates))
            cost = serialised_cost(self.candidates, subset)
            if self.budget is not None and cost > self.budget:
                raise ValueError(
                    f"delivered bundle costs {cost} > budget {self.budget}")
        self.snapshots.append({
            "schema_version": SCHEMA_VERSION,
            "n_messages": len(messages),
            "subset": sorted(subset),
            "rendered_cost": serialised_cost(self.candidates, subset),
            "additive_estimate": additive_estimate(self.candidates, subset),
            "messages": [dict(m) for m in messages],
        })
        if not subset:
            return list(messages)
        bundle = render_bundle(self.candidates, subset)
        out = list(messages)
        out.insert(len(out) - 1 if len(out) > 1 else len(out),
                   {"role": "user", "content": bundle})
        return out
