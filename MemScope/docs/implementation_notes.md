# Implementation notes

The repository translates the paper into a reference monitor whose trusted path is explicit: signed-token verification, label projection, integrity/authorization recheck, confined ranking, and a final snapshot check. Projection and lexical ranking are replaceable optimizations; neither can grant access.

The Python store is intentionally simple and synchronous so tests can exercise the paper's invariants without Android. Items are integrity-bound to payload digest, label, provenance, and version. In-memory plaintext is **not** presented as encryption. Production ciphertext, authenticated label metadata, wrapped compartment keys, and AppSearch documents belong behind the Android adapter.

Derived writes preserve the paper's separation between deterministic policy safety and heuristic semantic support. Parent visibility/version/digest and proposed-label order are mandatory. An extractive/structured verifier is provided for synthetic tests; abstractive content returns `uncertain` and quarantines. An always-accept verifier exists only as the paper's negative control.

Compaction removes expired/revoked data before budget decisions, checks hard-pin feasibility, and then removes ascending value density. The exact small-instance oracle is for evaluating heuristic gap, never the online claim.

Two conservative interpretations are material:

1. Release reauthorizes each ranked item because the appendix's final-check-freshness lemma requires it; this is now explicit in Algorithm 1 and is the confirmed contract.
2. Cross-token derivation is supported under one composition principal. Algorithm 2 admits a token set whose tokens share `(app, consumer, purpose)`; each parent is authorized by some token, and the derived label is still the meet of all parents, so policy cannot widen. A disjoint-tool composition with an empty required scope quarantines rather than being admitted. Frozen policy semantics are in `docs/policy_spec_v0.md`.

The experiment package has a `calibrate` stage only to satisfy a uniform workflow. It reports `not_applicable`: the paper contains deterministic policy enforcement, not conformal calibration.
