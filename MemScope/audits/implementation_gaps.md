# Implementation gaps

This file records every gap between the executable Python reference model and a paper-level MemScope artifact. None is hidden behind a dummy implementation.

## System implementation

1. **AOSP service and SDK:** `MemScopeManagerService`, Binder API, AppFunctions interception, UID/package/certificate binding, cross-user profiles, replay persistence, and public SDK objects require a named AOSP revision and patch series.
2. **AppSearch:** system-UID database ownership, indexable keyed-hash projection, privileged global session, ranking integration, transaction/version behavior, and native-index variant are not implemented on this host.
3. **Cryptography:** the Python HMAC token issuer is a reference protocol only. Production canonical encoding, Keystore/StrongBox signing, per-compartment AEAD, wrapped key lifecycle, rotation/destruction, and offline-database tests require Android.
4. **Complete mediation:** this repository cannot disable or instrument shadow vector stores, caches, logs, and cloud-memory APIs. The formal assumption is tested only as a model property.
5. **Trusted time and recovery:** Android monotonic high-water persistence, reboot replay state, write-ahead recovery, idempotent compaction, and audit-root durability remain device work.
6. **Audit/UI:** user explanations, narrowing/widening confirmation, review of quarantine, correction/revocation UI, storage-conflict UI, and content-minimized persistent audit partition remain unimplemented.

## Resolved author decisions

The appendix scheduling example composes two parents whose tool sets have empty intersection. This was previously in conflict with Algorithm 2, which required every parent to satisfy `Auth(m_j,q)` for one derivation token. **Resolved:** Algorithm 2 now admits a *token set* `Γ` under one trusted composition principal `(app, consumer, purpose)`; each parent need only be authorized by some `κ∈Γ`, and the derived label is still the meet of all cited parents, so non-widening (Theorem 2) is unchanged. The disjoint-tool example therefore reaches the empty-required-scope quarantine branch. Implemented in `methods/derivation.admit_derivation` (`tokens: Sequence[RetrievalToken]`), with `test_disjoint_tool_composition_quarantines`, `test_composition_context_mismatch_rejected`, and `test_empty_composition_rejected`; proof added as Lemma `lem:compose`.

Algorithm 1 previously abbreviated the final check to policy epoch and token expiry, while the appendix requires item-expiry authorization at the release snapshot. **Resolved:** Algorithm 1 now shows the explicit per-item integrity/authorization/item-expiry recheck before decryption, and this is the confirmed contract. The reference implementation already performed the stronger recheck in `methods/retrieval.py`.

Frozen policy semantics (purpose taxonomy, AppFunction mapping, precedence, wildcard policy, declassification) are recorded in `docs/policy_spec_v0.md` and paper `\cref{app:policy-frozen}`. The empty-ground-truth Recall@k convention is frozen to *exclude* empty queries and report eligible/excluded counts.

## Semantic and policy components

- Abstractive attribution needs a version-pinned local/cloud NLI or structured verifier, frozen thresholds, high-sensitivity policy, and human-labeled evaluation corpus.
- The actual production policy compiler still needs signing, encoding, inheritance/conflict resolution, and readable explanations. The frozen *semantics* (canonical IDs, precedence, wildcard expansion, declassification non-propagation) are in `docs/policy_spec_v0.md`; the implementation of a signed compiler and validation remains device work.
- Purpose taxonomy, AppFunction mappings, compound-task decomposition, and confirmation UI need a reviewed policy corpus.
- Direct-write label defaults currently enter as already policy-capped input; the production source/task/data-class compiler is absent.
- Declassification is deliberately out of the ordinary derivation path and has no implementation.

## Data and benchmarks

No real files are included for LoCoMo, LongMemEval, Memora, PA-Bench, ProfileFoundry, PersonaChat, AndroidWorld, or the multi-app mobile workload. Licenses/registration, versions, checksums, normalized schemas, policy annotation handbook, two-annotator agreement/adjudication, split hashes, and benchmark-specific scorers must be supplied manually.

## Baselines and attacks

AppSearch visibility, GAAP-style IFC, Audience-Bound Memory, and MNC require version-pinned external artifacts and verified connectors. MEXTRA, ADAM, SPORE, MINJA, both MemPoison formulations, MemEvoBench-style drift, always-allow/no-memory controls, and ToolPrivacyBench-style atom scoring require the same. No external API or result is simulated under those names.

## Measurement and analysis

- Pixel 8, Pixel 9, and Samsung device builds, matched agent/model/ranker prompts, battery/thermal protocol, power rails, CPU/NPU instrumentation, storage accounting, and key-operation timing are unavailable.
- Benchmark accuracy/FAMA, abstention, tool-argument atoms, attack success strata, annotation agreement, energy, compaction pause, and thermal throttling require real traces.
- Prospective power analysis, three restarts, paired bootstrap, exact binomial/Wilson selection, Holm families, effect sizes, device blocking, failed-run logs, and exclusion handling must be finalized before real execution.
- The real runner deliberately stops after normalized-schema preflight until the benchmark mapper/scorer and Android transport are author-verified.

## Packaging/verification environment

The project declares Python 3.11+. Local verification used Python 3.11.9 on Windows: `pytest` (52 passed), `ruff check .` (clean), and `mypy` strict over both the `memscope` package and the full tree (clean) now pass; `types-PyYAML` is a dev dependency and `src/memscope/py.typed` marks the package typed. A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the same pytest/ruff/mypy gates on Python 3.11 and 3.12; EC2 CI must still confirm a green remote run, and no CI pass is claimed from local runs or from the workflow file alone.
