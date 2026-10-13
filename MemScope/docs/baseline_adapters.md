# Baseline and attack adapters

Runnable baselines operate on `query`, the matched sequence of `MemoryItem`, `TaskContext`, and `k`, returning only selected items.

- `UnscopedBaseline`: one store; no authorization filtering.
- `NamespaceBaseline`: filters only a user/agent namespace.
- `PromptOnlyBaseline`: identical retrieval to unscoped; the prompt instruction is deliberately outside store enforcement.
- `DummyFirstBaseline`: deterministic unit-test helper and never an external baseline substitute.

External wrappers intentionally raise `NotImplementedError` until an artifact is manually provisioned. A connector must record name, source URL, paper/artifact version, commit and patches, environment, supported policy dimensions, request/response mapper, unsupported fields, reproduction status, and deviations. It must return `unsupported` when the system cannot represent a policy.

Required external baseline tracks are Android AppSearch visibility, GAAP-style IFC, Audience-Bound Memory, and MNC. Required attack tracks are MEXTRA, ADAM, SPORE, MINJA, and both paper-mentioned MemPoison formulations. Do not map an unrelated implementation under one of these names.

Every attack adapter must default to a synthetic local endpoint. Network sinks and credentials require explicit EC2 configuration outside version control. Report direct service return, attributable paraphrase, unauthorized tool argument, poisoned admission, behavioral activation, and availability degradation separately.
