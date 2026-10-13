# Claim-strength audit

| Strong term/claim | Location or source | Decision | Rationale |
|---|---|---|---|
| “first” / “first evidence” | Idea concept novelty boundary and killer experiment | Removed from manuscript claims | Recent Audience-Bound Memory, MNC, GAAP, and other 2026 papers make exhaustive priority verification unsafe. |
| “optimal” eviction | Possible interpretation of the storage objective | Removed | Online compaction is a greedy heuristic; exact knapsack is only a small-instance oracle. |
| “sharp threshold” | Not required by idea | Not used | No threshold theorem exists. |
| “matching lower bound” | Not required by idea | Not used | No lower-bound construction exists. |
| “state of the art” | Concurrent memory systems sometimes claim it | Not used for MemScope | There are no MemScope results. |
| “superior” | Would require completed matched experiments | Not used | Tables and plots are placeholders. |
| “guarantees privacy” | Tempting summary of Theorem 1 | Weakened to interface-level admission/returned-plaintext safety under assumptions | Semantic inference, side channels, and authorized-recipient behavior remain. |
| “derived-item verification prevents leakage” | Core idea | Weakened | Deterministic meet prevents policy widening; semantic attribution is empirical and can fail. |
| “expiry deletes memory” | Core idea | Weakened | Retrieval-time inaccessibility is proven; physical deletion and external copies are separate states. |
| “hardware-backed keys secure the store” | Core idea | Weakened | Keys provide offline defense in depth; they do not protect against a compromised authorized system service. |
| “under 50 ms / single-digit extraction / under three accuracy points” | Idea killer experiment | Retained only as source viability criteria in fidelity report, absent as achieved manuscript result | No measurements exist. |
| “submission-ready” | User objective | Not claimed | Empirical work, author metadata, and final venue format remain TODO. |

Result: all unsupported priority, optimality, sharpness, universal-security, and empirical-superiority claims were removed or narrowed.
