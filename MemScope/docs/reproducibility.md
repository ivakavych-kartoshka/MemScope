# Reproducibility

Synthetic runs fix a seed and emit config SHA-256, environment metadata, query-level JSONL, aggregate JSON, and content-free audit events. Every runner also writes a deterministic `run_manifest.json` recording the stage and the files it produced, so a directory mixing stages or platforms is detectable. Plotting reads `metrics.json`; there are no hard-coded table or curve values. Repeated fixed-seed runs are tested for identical metrics and query records.

The RQ harness (`scripts/run_harness.py`, `configs/synthetic_harness.yaml`) runs RQ1--RQ6 over the scaled synthetic multi-app workload across a seed list and writes `harness_summary.json` and `harness_runs.jsonl`. RQ5 (on-device cost) is reported as `not_measured_offline`; the other RQs are controlled synthetic measurements, not paper results. RQ2 sweeps entitled-scope width (config `scope_widths`) against retrieval depth `k`, RQ3 covers faithful, unsupported, laundering, cross-scope, stale-parent, expired-parent, composition-mismatch, and composition-disjoint-tool derivations, and RQ4 covers post-expiry releases, epoch-change denial, revocation, and the TTL boundary.

The report renderer (`scripts/make_harness_report.py`, `memscope harness-report`) reads `harness_summary.json` and writes CSV/Markdown tables and PNG figures under `tables/` and `figures/`. It derives every cell and point from the summary (no hard-coded values) and stamps the synthetic notice on each table and figure.

The harness also reports the paper's Section 11.6 negative controls (`negative_controls`). For each control it records `control_defeats_guarantee` (breaking the assumption makes the boundary visible) and `mediated_guarantee_holds` (the MemScope-mediated path keeps the guarantee). The authorized-copy-after-release control is out of scope by design, so its mediated guarantee is reported as not held rather than as a failure.

The synthetic harness deliberately sets latency to zero rather than pretending Python host timing is a mobile systems measurement. Real latency, energy, thermal, storage, and key-operation measurements require the Android instrumentation plan.

For real runs, archive:

- repository commit and clean/dirty status;
- exact Python lockfile and analysis container/AMI;
- AOSP commit/patch series, compiler/JDK/SDK/NDK/kernel/AppSearch versions and build flags;
- device model, firmware/build fingerprint, battery health, secure-hardware capabilities, ambient/thermal/charging state;
- model provider/version/date, local hashes/quantization, prompts and decoding;
- dataset version/license/checksums/transforms/exclusions/policy annotation version;
- attack and baseline commit hashes, reproduction status and deviations;
- seed list, raw JSONL traces, failed runs, exclusions, power method, and artifact hashes.

Use at least three process/device restarts for microbenchmarks. Keep pilots separate from final runs. Apply paired comparisons, bootstrap intervals, Wilson/exact intervals for rates, declared Holm families, effect sizes, and device blocking as specified by the paper.
