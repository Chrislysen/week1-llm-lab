# E2 v1 — PRESERVED AS EVIDENCE, INVALID AS RESULTS

Every number in this directory is void. Kept so the retraction is auditable.

## Why

An adversarial audit found that `plan_instruction` printed the action vocabulary
in slot order, while every `before` edge in all six graphs ran from a lower slot
index to a higher one. The printed identifier list was therefore a valid
topological order for all 36 instances.

Verified directly: a policy that emits `{"actions": <the printed list>, "ready":
true}` and never reads the dialogue scored **success 36/36 in every exposure
condition**, including `neither`, where only two distractor lines are visible.
Corruption adoption 0/71, decision-inversion 0/71.

The benchmark had no floor. No value it produced could be attributed to reading
anything, so the headline decision-authority-inversion figure of 0.4366 and the
`neither` baseline of 0.617 are both uninterpretable.

## Three further defects, same audit

- `gated` was `diamond` relabelled (slot 3 <-> 4). Five graph shapes, not six.
- `FAITHFUL_RELAY` appeared in no exposure condition, so faithful-relay
  utilization was permanently n=0 -- a metric that could never fire.
- SUPERSESSION and CORRUPTED_RELAY were separable at 100% by first-person
  phrasing alone.

## Already retracted before the audit landed

`supersession_respected` was vacuous (always 1.0; an empty plan scored 1.0).
Found and replaced independently -- see lineage_recompute.py. The audit
confirmed it with 10,800 random plans producing the single value 1.0.

## Fixed in v2

Two independent per-instance permutations (slot->action, and print order, the
latter re-drawn until it is not itself a valid ordering); `gated` replaced with
`star`; `faithful_only` and `source_and_faithful` conditions added; epistemic
register crossed with lineage class. Echo-the-prompt-order is now a permanent
null control in the test suite: it scores 1/36.
