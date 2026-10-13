# MemScope policy semantics v0 (frozen)

Status: **frozen** for the v0 reference model, the paper appendix
(`app:policy-frozen`), and the evaluation annotation handbook. Any change is a
versioned policy change, not a per-task decision. This document resolves the
author decision "freeze the purpose taxonomy, AppFunction mapping, policy
precedence, wildcard policy, and declassification rules."

The policy *syntax* in the paper and `configs/policies.example.yaml` remains
illustrative. Only the *semantics* below are frozen, and any production compiler
must preserve them.

## 1. Purpose taxonomy

Purposes are a closed, versioned set of canonical identifiers with fixed
definitions. Unknown identifiers are rejected at policy-compile time; they are
never treated as wildcards.

| Canonical purpose | Meaning | Sensitivity floor | Default TTL cap |
|---|---|---|---|
| `scheduling` | Time/calendar coordination | personal | 30 d |
| `health` | Health/medical information | health_sensitive | 365 d |
| `food-safety` | Allergy and ingestion safety | health_sensitive | 365 d |
| `communication` | Messaging/contact actions | personal | 90 d |
| `navigation` | Location and routing | personal | 7 d |
| `travel` | Trip planning | personal | 90 d |
| `finance` | Payments and financial data | finance_sensitive | 30 d |
| `personalized-ads` | Ad personalization | public | 7 d |
| `system-diagnostics` | Service telemetry | public | 1 d |
| `review` | Administrative review of quarantine | health_sensitive | 7 d |

Rules:

- Canonical identifiers are lowercase ASCII with hyphens. The illustrative YAML
  fragment (`configs/policies.example.yaml`) and the paper use a few underscore
  spellings of the same identifiers (for example `food_safety`); a production
  compiler normalizes these to the canonical form.
- A purpose identifier denotes exactly one definition; there is no implicit
  hierarchy. If a hierarchical vocabulary is later added, inheritance must be
  explicit and membership in a child purpose never grants siblings.
- `review` is reachable only by the administrative surface, never by an agent
  token.
- Adding or redefining a purpose is a policy-version change and re-expands all
  wildcard rules at the next epoch.

## 2. AppFunction mapping

- Every installed agent declares its AppFunctions and requested memory classes.
- A manifest-matched action maps to exactly one purpose through a signed mapping
  table (for example, calendar creation → `scheduling`; grocery allergen check →
  `food-safety`).
- A compound task is decomposed into subtasks, each with its own token, all
  sharing one composition principal `(app, consumer, purpose)`
  (see Section 5 and the paper's Algorithm 2).
- An unmapped or unusually sensitive action requires explicit user confirmation
  and yields the narrowest applicable purpose and tool set.
- A language model may explain a mapping but is never the mapping authority and
  cannot mint a token or widen a label.

## 3. Precedence

Rules are combined in a total precedence order, most restrictive first:

1. Mandatory system/device denial (cannot be overridden).
2. Enterprise / device-owner policy.
3. Explicit user rules.
4. Agent-declared defaults.

Semantics:

- An access is permitted only if **every** level permits it. A denial at a
  higher-precedence level is final and cannot be re-opened by a lower level.
- Set-valued dimensions (purposes, apps, tools, consumers) are intersected down
  the order; lifetimes take the minimum cap; sensitivity takes the maximum
  floor.
- Any operation that would **widen** an effective rule requires a distinct,
  object-specific user confirmation. Widening cannot be granted by an agent or
  by a lower-precedence rule.

## 4. Wildcards

- Wildcards are **disabled by default**.
- A wildcard is permitted only inside a signed enterprise/device-owner manifest.
- Wildcards are expanded at policy-compile time to the concrete set of installed
  or registered entities valid at that policy epoch. Expansion is logged and
  versioned.
- Installing or removing a matching entity re-expands the rule at the next epoch
  or fails closed; a rule never silently gains access to a newly installed app
  or tool.
- A wildcard never authorizes cross-sensitivity access that the rule does not
  name explicitly, and it can never select the `review` compartment or any
  compartment whose sensitivity floor exceeds the rule's declared sensitivity.

## 5. Composition principal

Derived writes may cite several tokens, but every token must share one
composition context `w = (app, consumer, purpose)`. Each cited parent must be
authorized by **some** token in the set; the derived label is the meet of all
cited parents regardless, so composition cannot widen policy. When the token set
has size one this reduces to single-token admission. An empty required scope
(for example, disjoint tool sets across parents) is committed to quarantine, not
admitted — this is the paper's scheduling example.

## 6. Declassification

- Declassification is a separate, object-specific policy event **outside**
  ordinary derivation.
- It requires direct user confirmation naming both the item and the broader
  scope.
- It emits a signed declassification-edge provenance entry recorded in the audit
  log; the original restrictive label is retained in provenance.
- Declassification does **not** propagate. A descendant remains bounded by the
  meet of its cited sources (using the pre-declassification label of the
  declassified item) unless that descendant is separately declassified.

## 7. Frozen empty-ground-truth convention (Recall@k)

Queries with empty entitled ground truth `G(q) = ∅` contribute to no denominator
and are excluded from the reported mean `ER@k`. This choice depends only on the
method-independent ground truth, so `ER@k` remains comparable across methods
evaluated on the identical query set. Reported results state the eligible count
`|Q⁺|` and the excluded count `|Q \ Q⁺|`. The `zero` scoring mode remains
available only as a diagnostic and is never the reported headline metric.
