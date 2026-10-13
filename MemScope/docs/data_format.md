# Data and benchmark format

No adapter downloads data. Every real benchmark root must be provisioned manually as:

```text
<data.root>/
├── items.jsonl
├── queries.jsonl
├── splits.json
├── LICENSE_OR_TERMS.txt
└── PREPARATION_MANIFEST.json
```

`items.jsonl` requires one object per memory atom:

- `item_id`: stable unique string;
- `text`: payload or approved local reference;
- `source`: package/tool/channel/timestamp provenance object;
- `label`: arrays `purposes`, `apps`, `tools`, `consumers`, plus `sensitivity`, `not_before`, and `expires_at`;
- `created_at`, `expires_at`;
- optional `parents`, `parent_digests`, `transformation`, `version`, `safety_critical`, and eviction features.

`queries.jsonl` requires:

- `query_id`, `text`, and `split`;
- `context`: app, active tool, consumer, purpose, task time, and nonce;
- `entitled_item_ids`: policy-and-relevance ground truth;
- optional answer target, necessary private atoms, attack metadata, group, and trajectory/tool-call trace.

`splits.json` records immutable train/development/pilot/test IDs and a preparation hash. The paper's protocol forbids tuning after final reporting begins.

## Named adapters

- **LoCoMo:** manually obtain under its terms; atomize conversations and attach purpose/consumer/lifetime labels without replacing the official score.
- **LongMemEval:** manually obtain; preserve extraction, multi-session, temporal, update, and abstention task identifiers.
- **Memora:** manually obtain; preserve invalidation/update chains and forgetting-aware scoring fields.
- **PA-Bench:** manually obtain the allowed release; preserve future-blind compression boundaries and annotate safety-critical facts.
- **Multi-app synthetic track:** manually provision ProfileFoundry/PersonaChat inputs if used; generator provenance and policy oracle must be recorded. AndroidWorld GUI tasks are optional and version/license dependent.

Required manual metadata for each dataset: origin URL/citation, version/commit, license/registration state, download date, raw checksums, transformation command/commit, normalized checksums, exclusions, annotation handbook version, annotator agreement, and split hash.

The local `examples/synthetic_data` scenario is structurally representative only. It is not a substitute for any named dataset.
