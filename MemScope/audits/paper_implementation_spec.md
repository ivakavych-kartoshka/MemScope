# Paper implementation specification

## Identity and scope

- **Paper:** *MemScope: A Purpose-Bound Memory Service for Mobile Personal Agents*.
- **Central task:** mediate persistent personal-agent memory on Android so every plaintext read is authorized for the authenticated app, tool, consumer, purpose, and trusted time, while derived memories never widen source policy.
- **Method:** MemScope, an OS-owned reference monitor and scoped persistent store.
- **Implementation boundary:** this repository is a Python reference model, policy/evaluation harness, and adapter surface. It is not an AOSP Binder service and does not claim complete mediation on a stock host.

## Executable objects and data structures

- `TaskContext q=(a_q,t_q,c_q,p_q,tau_q,n_q)` and a signed token carrying expiry, issue time, policy epoch, permitted tools, parent-token digest, nonce, query budget, and one-shot status.
- `MemoryItem m_i=(i,x_i,z_i,l_i,h_i)` with immutable ID, payload, provenance, integrity digest, state, version, size, ranking representation, and eviction features.
- `MemoryLabel l_i=(P_i,A_i,T_i,C_i,s_i,b_i,e_i)` with purpose/app/tool/consumer sets, ordered sensitivity, not-before, and expiry.
- Provenance contains source app/certificate/tool/channel, acquisition-token digest, creation time, parent IDs and digests, transformation, and content digest.
- Store snapshot, policy epoch, derivation DAG, append-only audit events, and lifecycle states: proposed, admitted, quarantined, expired, tombstoned, compacted.

## Algorithms and equations

1. **Eq. 1:** task context schema and token binding.
2. **Eq. 2:** labeled memory item and label schema.
3. **Eq. 3:** `authorize(item, context, token_expiry)` checks all four set memberships, `b <= tau < e`, token freshness, and provenance validity.
4. **Eq. 4:** `meet_labels(parents)` intersects allowed sets, joins sensitivity upward, uses maximum not-before and minimum expiry.
5. **Eq. 5 / Algorithm 1:** `MemScopeService.retrieve` verifies token/caller/tool chain, uses an index projection only as an optimization, rechecks integrity and authorization before ranking, performs an explicit per-item release reauthorization (integrity, authorization, item expiry) before decryption, bounds epoch/time restarts, and decrypts only authorized results.
6. **Eqs. 6-8:** authorization violations, misses, and entitled Recall@k. The Recall@k convention is frozen: queries with empty entitled ground truth are excluded from the mean, and eligible/excluded counts are reported.
7. **Eq. 9 / Algorithm 2:** `admit_derivation` accepts a token set that shares one composition principal `(app, consumer, purpose)` and atomically validates parents, per-parent source visibility/version/digest, proposed-label restrictiveness, required-scope intersection, and attribution; failures reject or quarantine.
8. **Eqs. 10-11 / Algorithm 3:** policy-aware greedy compaction removes expired/revoked records first, respects hard pins or raises a resource conflict, then evicts by value density `(alpha*u + beta*r + gamma*c - delta*d - eta*g)/w`.
9. **Eq. 12:** child-token attenuation; child app/consumer/purpose/tool scope, expiry, and budget cannot exceed the parent.

The greedy compactor is an approximation, with an exact small-instance knapsack oracle included only for evaluation.

## Inputs and outputs

- **Inputs:** policy/config YAML, JSONL memory/task records, signed synthetic tokens, benchmark-adapter records, result limits and byte budgets.
- **Outputs:** JSON/JSONL result records, content-free audit traces, metric summaries, provenance/config manifests, and plots generated only from those results.
- The reference store keeps plaintext in process for testability. Production encryption/Keystore/AppSearch operations are adapter interfaces and remain external implementation work.

## Metrics

- Security: authorization violations/out-of-scope retrieval rate, unique-record extraction yield, sensitive-atom disclosure, poisoned-write acceptance, trigger activation, and attack cost.
- Utility: entitled Recall@k, misses, exact match/F1 helpers, task completion, abstention, and safety-critical survival.
- Lifecycle/labels: post-expiry release count, false widening/narrowing, exact-label match, per-dimension precision/recall, attribution FAR/FRR, and quarantine rate.
- Systems: generic latency summaries (p50/p95/p99), bytes/item and index amplification hooks. Device energy/thermal/key costs require Android instrumentation.
- Statistics: paired bootstrap CI, Wilson interval, and Holm correction.

## Baselines

- Implemented reference baselines: unscoped store, identity namespace, prompt-only policy, and deterministic dummy baseline.
- Adapter-only: Android AppSearch visibility, GAAP-style IFC, Audience-Bound Memory, MNC, and external attack implementations.
- All matched comparisons must share histories, queries, ranking, seeds, model calls, device state, and byte budgets. Unsupported policy dimensions are reported as `unsupported`.

## Datasets, attacks, and protocol

- Utility adapters: LoCoMo, LongMemEval, Memora, PA-Bench.
- Synthetic/multi-app inputs: ProfileFoundry, PersonaChat-derived dialogue, and optional AndroidWorld GUI tasks.
- Attack adapters: MEXTRA, ADAM, SPORE, MINJA, two MemPoison formulations, and MemEvoBench-style drift.
- Devices planned by the paper: Pixel 8, Pixel 9, and a recent Samsung flagship. These experiments are not run here.
- Factors: item count, scope width, app/tool count, TTL, sensitivity/safety mix, read/write ratio, pressure, attack budget, ranker, verifier, and network availability.
- Required negative controls: shadow cache, stale-token replay, always-accept attribution, and copying by an authorized tool.

## Assumptions and guarantees

- Token/caller/tool-chain authenticity; complete mediation; integrity-protected state and trusted monotonic time; confined ranker.
- The reference model checks these contracts but cannot establish Android OS enforcement.
- Properties represented in tests: meet monotonicity, composition principal (multi-token admission), authorized-view invariant, retrieval admission soundness, derived-label safety, expiry inheritance, cross-scope stored-plaintext safety, read-time expiry, final-check freshness, and ranking independence.

## Limitations and conceptual components

- No semantic non-inference, revocation after authorized copying, complete access-pattern hiding, screen-capture defense, kernel/TEE defense, or truth guarantee for in-scope content.
- The attribution verifier is heuristic; this repository supplies an exact extractive verifier and a configurable stub, not an invented NLI model.
- Policy compilation remains human/administrative, but the v0 *semantics* (purpose taxonomy, AppFunction mapping, precedence, wildcard expansion, declassification non-propagation) are frozen in `docs/policy_spec_v0.md`. The policy syntax in the paper remains illustrative.
- Cryptographic compartments, Binder identity, AppFunction interception, AppSearch projection, Android audit storage, energy rails, and StrongBox are adapter contracts only.
- Every result table and curve in the paper is a placeholder. This repository generates only labeled synthetic smoke-test output.

## External-data requirements

All named datasets, model providers, attack artifacts, Android builds, device instrumentation, licenses, registrations, and credentials must be provisioned manually on EC2 or a device. Tests make no network calls and download nothing.
