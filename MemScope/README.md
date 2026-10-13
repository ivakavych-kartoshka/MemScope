# MemScope

Reference implementation and reproducibility harness for **“MemScope: A Purpose-Bound Memory Service for Mobile Personal Agents.”** MemScope enforces per-item purpose, app, tool, consumer, sensitivity, provenance, and lifetime labels before ranking; derived records inherit a conservative meet of their parents.

> **No paper-level experimental results are claimed by this repository unless real benchmark outputs are generated and their provenance is recorded.**

> **This repository does not automatically download datasets or run paper-level experiments. Real experiments are intended to be executed on EC2 after the required datasets, benchmarks, models, and credentials are manually provisioned.**

The code is a typed Python reference model and matched experiment harness. It is not an AOSP service, does not establish complete mediation on a desktop, and stores test payloads in process rather than claiming Android Keystore encryption.

## Paper-to-code map

| Paper object | Implementation |
|---|---|
| Eqs. 1-2: task, token, label, item, provenance | `memscope.data.schemas` |
| Eq. 3: authorization | `memscope.methods.policy.authorize` |
| Eq. 4: conservative meet | `memscope.methods.policy.meet_labels` |
| Eq. 5 / Algorithm 1: pre-ranking retrieval | `memscope.methods.retrieval.MemScopeService` |
| Eqs. 6-8: violations, misses, entitled recall | `memscope.metrics.core` |
| Eq. 9 / Algorithm 2: derived admission (multi-token composition) | `memscope.methods.derivation.admit_derivation` |
| Eqs. 10-11 / Algorithm 3: eviction | `memscope.methods.compaction` |
| Eq. 12: token attenuation | `memscope.methods.tokens.TokenIssuer.attenuate` |
| AOSP, benchmarks, attacks | explicit adapters under `memscope.adapters`, `memscope.data.adapters`, and `memscope.baselines.external` |

The complete mapping is in [`audits/paper_to_code_traceability.csv`](audits/paper_to_code_traceability.csv).

## Installation

Use Python 3.11 or newer:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

The test suite and synthetic demo make no network calls.

## Quick start

```bash
python -m memscope.cli --help
python scripts/run_synthetic_demo.py --config configs/synthetic_demo.yaml
python scripts/make_plots.py \
  --input outputs/synthetic_demo/metrics.json \
  --output outputs/synthetic_demo/metrics.png
python scripts/run_harness.py --config configs/synthetic_harness.yaml
python scripts/make_harness_report.py \
  --summary outputs/synthetic_harness/harness_summary.json \
  --output-dir outputs/synthetic_harness/report
python -m pytest -q
```

All demo records and plots carry the label **“synthetic smoke-test output, not a paper result.”** The demo compares MemScope with unscoped, namespace, and prompt-only reference baselines using the same fictional store, queries, lexical ranker, seed, and result limit.

`run_harness.py` runs the offline synthetic RQ1--RQ6 harness over the scaled multi-app workload (multiple seeds) and writes `harness_summary.json` plus per-run `harness_runs.jsonl`. It reports RQ1 enforcement, RQ2 utility, RQ3 derivation, RQ4 lifecycle, and RQ6 retention as **controlled synthetic** measurements, and reports RQ5 (on-device cost) as `not_measured_offline`. None of these are paper results. RQ2 sweeps entitled-scope width against retrieval depth `k` (config `scope_widths`), RQ3 exercises faithful, unsupported, laundering, cross-scope, stale-parent, expired-parent, composition-mismatch, and composition-disjoint-tool derivations, and RQ4 covers post-expiry releases, epoch-change denial, revocation, and the TTL boundary.

`make_harness_report.py` (or `memscope harness-report`) renders CSV/Markdown tables (`rq1_enforcement`, `rq2_utility`, `rq3_derivation`, `rq4_lifecycle`, `rq6_retention`, `negative_controls`) and PNG figures from `harness_summary.json`. Every table and figure is derived from the summary and carries the synthetic notice; nothing is hard-coded.

The harness also runs the paper's Section 11.6 negative controls (shadow cache, stale-token replay, always-accept verifier, authorized-copy-after-release). Each control deliberately breaks one assumption and reports whether it defeats the matching guarantee, alongside the MemScope-mediated path, so the guarantee boundaries are explicit. The authorized-copy control is out of scope by design (`mediated_guarantee_holds = False`).

## Verification

Local gate: `pytest -q`, `ruff check .`, and `mypy .` (strict, package and full tree). A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the same three gates on Python 3.11 and 3.12; a remote green run must be confirmed before any CI pass is claimed. Tests include a final-check freshness race (`test_release_time_expiry_race_fails_closed`) and a randomized multi-token composition property (Theorem 2 non-widening).

## Implemented algorithms

- HMAC-signed reference tokens bound to app, active tool chain, purpose, consumer, policy epoch, expiry, nonce, and query budget; child tokens attenuate.
- Exact authorization across label sets and trusted release time.
- Index-projection over-approximation followed by integrity and policy rechecks before ranking.
- Final epoch, token, item-expiry, and integrity checks before release with bounded restart (explicit per-item reauthorization, matching Algorithm 1).
- Direct observation writes and source-cited derivation admission with a multi-token composition principal, label meet, version/digest checks, and quarantine.
- Extractive/structured attribution verifier plus an explicit test-only always-accept negative control.
- Expiry/revocation-first greedy compaction and a small exact knapsack evaluation oracle.
- Content-free audit events and tombstone digests.

## Metrics and statistics

Implemented metrics include authorization violations, out-of-scope retrieval rate, unique-record extraction yield, entitled misses and Recall@k, exact match, token F1, safety-critical survival, label widening/narrowing, attribution error rates, and latency quantiles. Wilson intervals, seeded bootstrap median intervals, and Holm adjustment implement the preregistered statistical utilities.

Device energy, thermal state, key-operation cost, Android CPU/NPU time, benchmark-specific accuracy/FAMA, and model/tool trajectory measures require the real device harness and are not fabricated locally.

## Baselines

- **Runnable reference baselines:** unscoped, namespace-only, prompt-only, and deterministic dummy test baseline.
- **Adapter-only baselines:** Android AppSearch visibility, GAAP-style IFC, Audience-Bound Memory, and MNC. Their repositories/APIs are not invented; manually provision a version-pinned artifact and implement the documented connector.

## Configuration

- `configs/synthetic_demo.yaml`: runnable offline demo.
- `configs/synthetic_harness.yaml`: offline synthetic RQ1--RQ6 harness (RQ5 marked not measured).
- `configs/default.yaml`: small reference defaults.
- `configs/experiment_template.yaml`: EC2 template; real paths and provenance fields are deliberately unconfigured.
- `configs/policies.example.yaml`: illustrative policy fragment, not a production Android policy language.

The CLI reads YAML with `safe_load`; configs cannot execute shell commands. Relative output paths resolve from the current working directory.

## Real-data usage

Do not place licensed/private data in Git. On EC2, manually create the normalized layout in `docs/data_format.md`, then run:

```bash
python -m memscope.cli validate-data --name locomo --root /data/memscope/locomo
python scripts/run_experiment.py --config /path/to/verified-real-config.yaml --stage calibrate
python scripts/run_experiment.py --config /path/to/verified-real-config.yaml --stage evaluate
```

`calibrate` is intentionally a policy/config preflight: the MemScope paper contains no conformal or statistical calibration algorithm. Real evaluation stops after schema preflight until the benchmark-specific annotation/scorer TODO is author-verified. See `docs/ec2_experiment_guide.md` for the exact preparation gate.

## Repository layout

```text
MemScope/
├── audits/                 paper mapping, math, gaps, and result integrity
├── configs/                synthetic and EC2 templates
├── docs/                   schemas, adapters, implementation, reproducibility
├── examples/synthetic_data/
├── outputs/                generated artifacts only
├── scripts/                demo, experiment, and plotting entry points
├── src/memscope/
│   ├── adapters/           AOSP and attack contracts
│   ├── baselines/          runnable and external baselines
│   ├── data/               schemas, adapters, synthetic generator
│   ├── experiments/        evaluation, preflight, ablation, RQ harness, negative controls, report, plotting
│   ├── methods/            tokens, policy, retrieval, derivation, compaction
│   ├── metrics/            metrics and statistical helpers
│   ├── models/             ranker and attribution interfaces
│   └── utils/              safe I/O, logging, seeds, validation
└── tests/                  unit, property, CLI, and reproducibility tests
```

## Reproducibility

Each generated result stores the config hash, seed, Python/platform metadata, result class, and a false `paper_result_claimed` flag. Every runner also writes a deterministic `run_manifest.json` listing the files that stage produced, so stale artifacts from another platform or stage are detectable rather than silently mistaken for fresh output. Query-level records are JSONL; figures read those generated results rather than hard-coded values. External runs must add AOSP commit, device/build fingerprint, model version/date, dataset checksums/licenses, attack commits, prompts, seed lists, thermal state, exclusions, and raw trace hashes.

## Limitations and known gaps

- Python cannot replace Binder identity, system-server mediation, AppFunctions, AppSearch, Android Keystore/StrongBox, or a device monotonic-time trust root.
- The paper's scheduling example composes parents with disjoint tool scopes. Algorithm 2 supports this with a token set under one composition principal `(app, consumer, purpose)`; each parent need only be authorized by some token, and the derived label is still the meet. The empty required tool scope quarantines (fails closed). Frozen policy semantics are in [`docs/policy_spec_v0.md`](docs/policy_spec_v0.md).
- The final release check is explicit in Algorithm 1 (per-item integrity, authorization, and item-expiry reauthorization) and in the implementation.
- Entitled Recall@k excludes queries with empty entitled ground truth; eligible and excluded counts are reported.
- The provided semantic verifier handles extractive/structured synthetic transforms only; abstractive outputs quarantine until an independently validated verifier is supplied.
- No external dataset, model, attack, baseline, Android patch, or device measurement ships here.

See [`TODO_IMPLEMENTATION.md`](TODO_IMPLEMENTATION.md) and [`audits/implementation_gaps.md`](audits/implementation_gaps.md) for the full gate to paper-level experiments.
