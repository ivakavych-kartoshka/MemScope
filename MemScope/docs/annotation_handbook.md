# Policy annotation handbook (draft v0)

Status: **draft, not yet frozen.** This handbook is the working procedure for
attaching MemScope policy labels to real benchmark items before any licensed
dataset is run. The label *semantics* it applies are already frozen in
`policy_spec_v0.md`; this document only standardizes how a human annotator
derives those labels from a benchmark item. It must be frozen, and annotator
agreement reported, before final evaluation splits are touched.

No real dataset is bundled with this repository. This handbook exists so the
annotation step is reproducible and auditable once data is provisioned under
`docs/data_format.md`.

## 1. What is annotated

For every memory **atom** (`items.jsonl`) the annotator fills the label object
consumed by `data/adapters.py` and `MemoryLabel.from_mapping`:

| Field | Meaning |
|---|---|
| `purposes` | closed set of purposes the atom may serve (§2) |
| `apps` | source/consuming app identities allowed to receive the atom |
| `tools` | tool/function IDs under which the atom may be released |
| `consumers` | consumer identities (agent/task principals) permitted |
| `sensitivity` | maximum sensitivity floor implied by the purposes (§2) |
| `not_before` | earliest trusted time the atom is valid |
| `expires_at` | latest trusted time the atom is valid |

For every **query / task** (`queries.jsonl`) the annotator records the task
context (`app`, `tool`, `consumer`, `purpose`, `task_time`, `nonce`) and the
`entitled_item_ids` ground truth (§5).

## 2. Purpose and sensitivity

Purposes come only from the frozen taxonomy in `policy_spec_v0.md` §1. Unknown
identifiers are **rejected**, never treated as wildcards. Each purpose carries a
sensitivity floor and a default TTL cap:

| Purpose | Sensitivity floor | Default TTL cap |
|---|---|---|
| `scheduling` | PERSONAL | 30 d |
| `health`, `food-safety` | HEALTH_SENSITIVE | 365 d |
| `communication` | PERSONAL | 90 d |
| `navigation` | PERSONAL | 7 d |
| `travel` | PERSONAL | 90 d |
| `finance` | (finance-sensitive floor) | 30 d |
| `personalized-ads` | PUBLIC | 7 d |
| `system-diagnostics` | PUBLIC | 1 d |
| `review` | HEALTH_SENSITIVE | 7 d |

Rules:

- An atom is annotated with the **narrowest** purpose set that a real task would
  need it for. If in doubt, exclude the purpose (default-deny).
- `sensitivity` is the **maximum** floor over the atom's purposes; an atom that
  is health-relevant is `HEALTH_SENSITIVE` even if also usable for `scheduling`.
- `review` compartments are never annotated for agent-consumable items.
- The AppFunction/tool→purpose mapping is taken from the signed mapping table
  (`policy_spec_v0.md` §2); a language model may explain a mapping but is never
  the mapping authority.

## 3. Apps, tools, and consumers

- `apps`: the package identities that the atom's own source or an authorized
  task may consume it with. Do **not** include an app merely because it could
  technically read the file.
- `tools`: concrete AppFunction/tool IDs. Prefer the narrowest tool that
  satisfies the task; a broad wildcard is never used unless a signed
  enterprise/device-owner manifest grants it (`policy_spec_v0.md` §4).
- `consumers`: the agent/task principals. For a single-user assistant this is
  the consumer ID named in the query context, not a human name.

## 4. Lifetime

- `not_before` is the earliest trusted time the atom becomes usable (usually the
  source timestamp; use a later value only with a documented reason).
- `expires_at` is `min(not_before + purpose TTL cap, dataset lifetime)`. When a
  dataset provides an explicit invalidation time, that time wins.
- `not_before < expires_at` is mandatory; an empty interval is an annotation
  error, not a valid label.
- Derived items are **not** hand-annotated: their label is the computed meet of
  cited parents (`policy_spec_v0.md` §5). Annotators label only source atoms.

## 5. Entitled ground truth

For each query, `entitled_item_ids` lists the atoms that are both
policy-authorized for the query's context **and** relevance-grounded in the
benchmark's own answer evidence. This is the MethodScope-independent ground truth
`G(q)`:

- Include an atom only if the task context's `(app, consumer, purpose)` and
  active `tool` are all permitted by the atom's label at the query time.
- If the benchmark's answer is not supported by any authorized atom, the query
  keeps an **empty** `G(q)`. Empty-ground-truth queries are excluded from
  `ER@k` per the frozen convention (`policy_spec_v0.md` §7); the eligible and
  excluded counts must be reported.
- Original benchmark answers and official scores are preserved separately and
  never overwritten by annotation.

## 6. Ambiguity and confidence

The annotator records a confidence flag per atom: `clear` or `ambiguous`.

- `clear`: one reading follows directly from the taxonomy and the benchmark
  evidence.
- `ambiguous`: two or more defensible readings. The atom is annotated with the
  **narrowest** reading and flagged for adjudication (§7). Ambiguous atoms are
  never silently widened.

Decision precedence when rules conflict mirrors `policy_spec_v0.md` §3:
mandatory denial > enterprise/device-owner > explicit user rules >
agent-declared defaults; set dimensions intersect, lifetimes take the minimum,
sensitivity takes the maximum.

## 7. Agreement procedure

1. Two annotators independently label a **stratified** sample of atoms and
   queries (stratify by purpose, sensitivity, and source app), blind to any
   system output.
2. Report agreement **per dimension** (purpose, app, tool, consumer, sensitivity,
   lifetime, entitled set) as raw agreement and an appropriate chance-corrected
   statistic (Cohen's κ for categorical dimensions).
3. A third party adjudicates disagreements without inspecting system outputs;
   adjudications are recorded with rationale and a handbook-version reference.
4. Natural-language task items receive an additional leakage audit before entry
   into a split.
5. The annotated corpus inherits deterministic labels from this handbook, but
   any atom whose label was changed after seeing system output is marked
   exploratory and excluded from the frozen split.

## 8. Recording and freezing

Per dataset, the preparation manifest (`PREPARATION_MANIFEST.json`) must record:
origin URL/citation, version/commit, license/registration state, download date,
raw checksums, transformation command/commit, normalized checksums, exclusions,
handbook version, annotator agreement, and the split hash (`splits.json`
`preparation_hash`). Splits are frozen before final runs; pilot traces are kept
separate and never mixed with final data.

## 9. Non-claims

This handbook does not create results. It prepares the annotation step for
real-benchmark runs; all such runs remain blocked until datasets are licensed
and provisioned by a human operator, and until the corresponding scorers are
author-verified.
