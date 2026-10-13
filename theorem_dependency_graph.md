# Theorem dependency graph

```text
Definitions: item label, product order, Auth, View, Meet
       |
       +--> Assumption 1: authentic caller/tool-bound tokens
       +--> Assumption 2: complete mediation
       +--> Assumption 3: state integrity + atomic epoch + trusted time
       +--> Assumption 4: ranker confinement
       |
       +--> Lemma 1: meet monotonicity
       |       |
       |       +--> Lemma 2: composition principal (multi-token admission)
       |       |       |
       |       |       +--> (supports) Theorem 2: derived-label safety
       |       |
       |       +--> Theorem 2: derived-label safety
       |               |
       |               +--> Corollary 1: expiry inheritance
       |               +--> Lemma 4: derivation-path monotonicity
       |                               |
       |                               +--> Theorem 3: cross-scope returned-plaintext safety
       |
       +--> Lemma 3: authorized-view invariant
       |       |
       |       +--> Theorem 1: retrieval admission soundness
       |               |
       |               +--> Theorem 3: cross-scope returned-plaintext safety
       |
       +--> Lemma 5: final-check freshness
                |
                +--> Theorem 4: retrieval-time expiry safety

Algorithm/data-structure assumptions
       |
       +--> Proposition 1: retrieval and label-storage complexity

Theorems -> implementation tests -> experiments
  Theorem 1 -> token mutation, identity swap, shadow-cache negative control -> RQ1/RQ4
  Theorem 2 -> random DAG/property tests, broad-label rejection -> RQ3
  Lemma 2 -> multi-token composition, disjoint-tool quarantine, context-mismatch rejection -> RQ3
  Theorem 3 -> cross-purpose/app/tool attack matrix -> RQ1
  Theorem 4 -> expiry/reboot/race/clock tests -> RQ4
  Proposition 1 -> store-size and candidate-count microbenchmarks -> RQ5
```

No experimental result is used as a premise for a theorem.
