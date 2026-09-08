# AgentCom bundle direction — comparator specification

Updated 2026-09-08 from the research addendum. **Specification only: no model
calls, no Phase C authorisation.** The direction has not passed
`docs/NOVELTY-GATE.md`.

## The research target, stated so it can fail

> On fresh task families and recipient contexts, a shared interaction model
> learns useful bundle choices with **lower outcome-labelling token cost** than
> equally informed set distillation, general set prediction, structured
> skill-utility prediction, and active subset-search adaptations, while meeting a
> declared task-quality target.

**Unestablished.** No component of that sentence is claimed new. In particular:

- **A quadratic selector is not a contribution.** Semantic QUBO evidence
  selection already builds an explicit objective with relevance, complementarity
  and redundancy terms.
- **Active subset exploration is not a contribution.** CASE already searches
  subsets with model feedback and challenger-arm exploration.
- Winning only against independent retrieval, or against an empty-set greedy
  rule, supports a **narrow engineering claim** and nothing more.

What is left to attempt is **transferable recipient-conditioned selection at
lower labelling cost**. That is a comparative claim, and it needs the comparators
below to be implemented faithfully.

## Comparators added by the addendum

| source | sections | what it already establishes | consequence here |
|---|---|---|---|
| **Optimal Skill Selection for LLM Agents**, arXiv:2608.19993 | §§3.1, 3.3, 5.1–5.4 | Learns a structured capability score from **frozen-executor outcomes** and selects **under a token budget**; compares additive, Shapley, Datamodels, DeepSets, Set Transformer on shared execution records; has lookup-table *and* text-encoder variants. | Outcome-trained budgeted set selection is a **close existing method**. Give it the same recipient context. **Do not equate its settings with zero-label transfer**: the lookup-table experiment refits from observations of each test task, and the text variant also receives online feedback. |
| **CASE**, ICML 2025 | §§3.1–3.3 | Searches strong exemplar subsets using LLM feedback, a **linear subset-score model**, and challenger-arm exploration; features combine membership with similarity to validation examples. | "Actively choose which bundles to evaluate" is **already established**. A faithful adaptation *plus* an interaction-feature extension is a serious baseline. Swapping exemplars for messages, or lifting linear features to include pairs, establishes nothing by itself. |
| **OptiSet** | §§3.2–3.3 | Generates candidate evidence sets, scores them by **gold-answer likelihood change**, trains with a best-set target **and a distribution over set preferences**. | Distillation need not discard everything but the winning set. Supply an **equally informed set-level supervision** baseline. Substituting executable correctness for likelihood is a design change whose benefit must be **demonstrated**. |
| **GenICL** §3, **SetR** §3 | — | Generator-preferred demonstration selection; holistic evidence-set selection. | Query-conditioned selection from outcome/preference supervision is not untouched. **Recipient context goes into competitors' inputs too.** |
| **Targeted Active Learning for Bayesian Decision-Making** | §3 | Selects observations to reduce uncertainty about an **optimal decision**, including for a population of inputs. | Decision-targeted acquisition is established: a foundation and comparator, **not** a new theorem here. |
| **Sequential Experimental Design for Transductive Linear Bandits** | §§1–3 | Separates available **measurements** from the alternatives ultimately **chosen**, under a linear response model with explicit noise assumptions. | A useful measurement need not be a likely winner: **do not restrict acquisition to current contenders**. Guarantees do **not** transfer to a learned, misspecified LLM utility model. |
| **Melding the Data-Decisions Pipeline / SPO** | — | Train predictions for downstream **decision** quality. | "Select good bundles" and "reconstruct the utility surface" are different objectives — established methodology, and the reason this repo now reports regret and reconstruction error separately. |

Carried forward from the earlier screen and **not** replaced with easier
stand-ins: **RepoShapley** (verified-coalition distillation), **ProxySPEX**
(masked-output interaction models), **semantic QUBO** selection.

## Fairness rules that bind the comparison

- **Same inputs.** Every learned comparator gets the same recipient context,
  candidate pool, budget and model identity. Denying a comparator the recipient
  context would manufacture an interaction advantage.
- **Same records for the representation comparison.** Additive / quadratic /
  general-set / structured-capability / direct-set-prediction may share one
  revealed table.
- **Acquisition is charged.** Different acquisition policies necessarily reveal
  different records; each pays for the measurements it requests, and all are
  evaluated on a **common independent test set**.
- **Multi-budget labels are free to everyone.** Any method may derive labels for
  all tested budgets from the same revealed table without extra receiver calls.
  A value model gets **no** automatic sample-efficiency credit for handling
  multiple budgets.
- **Equal calls are not equal cost.** Cumulative teacher calls, teacher
  input/output tokens, failures, training compute and selector inference are
  separate quantities and are reported separately.
- **Adaptations must be labelled as such**, and validated against published code
  where feasible. Beating a weak namesake is not beating the method.

## Three factors, separated

| comparison | hold fixed | vary | a gain would support |
|---|---|---|---|
| **Representation** | revealed records, permitted inputs, budgets, receiver, optimizer quality | additive / quadratic / general set / structured capability / direct set prediction | a useful inductive bias **at the tested data budget** |
| **Acquisition** | predictor, optimizer, training pool, evaluation tasks | uniform / decision-targeted / CASE-style | better use of the labelling budget |
| **Recipient information** | schedule, architecture, budget, all other inputs | real recipient state vs a declared ablation | value of conditioning **under this intervention** |

## Cautions that constrain what any result can mean

- **Any one already-known feasible target is additively encodable** (+1 members,
  −1 non-members). So evidence for explicit interactions must concern
  **learnability and generalisation**, never the existence of an
  additive-vs-quadratic policy at a fixed cell. A **direct budget-conditioned set
  selector** is therefore a required strong comparator; a restricted additive
  value model remains a useful ablation.
- **Interaction claims are scale-dependent.** Probabilities (0.2, 0.4, 0.4, 0.8)
  show synergy 0.2 whose logarithms are exactly additive, and both orders choose
  identically under a hard budget. Positive success-scale interaction therefore
  does **not** refute a comparator using a submodular latent score with a
  monotone link. Inspect the model and its preconditions.
- **Changing interaction coefficients ≠ valuable recipient adaptation.** Context
  headroom is zero whenever the contexts share an optimal bundle. Match feasible
  sets across contexts before attributing a difference to recipient information.
- **Observed adaptation gain is optimistic.** In an exact null with identical
  contexts, six equally good actions and one Bernoulli(½) observation each, the
  expected *apparent* gain is **301/4096 ≈ 7.35 %** at **zero** true gain. More
  tasks do not remove this selection bias.
- **Do not read unconstrained fitted scores outside [0, 1] as probabilities.**
