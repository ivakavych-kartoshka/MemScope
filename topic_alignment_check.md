# Topic alignment check

Source of truth: `idea.pdf`, `idea.tex`, `idea_fidelity_report.md`, and `topic_signature.json`.

## Canonical comparisons

| Dimension | Idea PDF | Final manuscript | Status |
|---|---|---|---|
| Title | *MemScope: A Purpose-Bound Memory Service for Mobile Personal Agents* | Exact title preserved | Pass |
| Core keywords | purpose, provenance, lifetime, consumer/app/tool scope, on-device Android, derived items, eviction | All appear in abstract/introduction/system/method sections | Pass |
| System entities | system service, AppSearch store, token issuer, monitor, label propagator, Agent SDK, hardware keys | Preserved as named components and shown in architecture | Pass |
| Algorithm | labeled documents, task tokens, filter before ranking, source-meet derivation, TTL, eviction | Implemented as three named MemScope algorithms | Pass |
| Theorem directions | implied enforcement, derivation, expiry, performance | admission soundness, label monotonicity, cross-scope returned-plaintext safety, expiry safety, complexity | Pass; semantic non-inference explicitly excluded |
| Experiment plan | Pixel/Samsung, MobiMem context, LoCoMo/LongMemEval/Memora/PA-Bench, attacks, mobile overhead | Preserved as preregistered protocol with exact baselines/factors/metrics; no fake results | Pass |
| Baseline family | unscoped; Mem0/Letta namespaces; AppSearch visibility; GAAP-style IFC; prompt instructions | Preserved | Pass |
| Seed literature | recent memory governance/attacks, Android platform, classic privacy systems | Resolved where verifiable; unresolved candidates rejected or TODO | Pass |
| Non-topics | not generic cloud-only memory, DP central method, mechanism design, FL, blockchain | None dominates; DP appears only as inference boundary | Pass |

## Major-section checklist

- **Abstract:** MemScope, purpose-bound mobile service, Android/on-device boundary, labels, token, pre-ranking filter, derivation meet, expiry, eviction, formal limits, pending experiments — pass.
- **Introduction:** exact problem, mobile enforcement point, attack motivation, five idea-derived contributions — pass.
- **Related work:** centered on agent memory authorization/governance/attacks/mobile constraints; neighboring IFC/DP clearly bounded — pass.
- **Preliminaries/system/threat:** all canonical entities and label dimensions defined; trusted/untrusted principals match the idea — pass.
- **Problem/method:** authorization equation, view-before-ranking, meet propagation, TTL, eviction objective — pass.
- **Algorithms:** retrieval, derived admission, and policy-aware compaction preserve the source idea — pass.
- **Theory:** proves only the directions supported by the system model; no unrelated mathematical framework — pass.
- **Implementation:** Android AppSearch/AppFunctions/Keystore mapping retained — pass.
- **Evaluation:** datasets, attacks, baselines, devices, variables, metrics, ablations from the idea preserved; unresolved MemGUI-Bench deferred — pass.
- **Figures:** architecture, pipeline, proof dependencies, threat/control, experimental harness, conceptual trends all depict MemScope objects — pass.
- **Discussion/limitations/conclusion:** novelty bounded against concurrent work; no drift or unsupported empirical claim — pass.

## Revisions made after alignment audit

- Removed any priority claim such as “first.”
- Recast the main guarantee as returned-plaintext admission safety rather than general privacy/non-inference.
- Removed the unresolved AICore statelessness claim and did not build on missing IntentGuard details.
- Kept MemGUI-Bench out of the verified bibliography until metadata is resolved.
- Marked every evaluation number/table/curve as pending or conceptual.

Final decision: **aligned with the canonical idea; no topic restart required.**
