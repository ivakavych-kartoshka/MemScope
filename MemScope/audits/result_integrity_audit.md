# Result integrity audit

## Status

- **Real experiments run:** no.
- **Paper-level benchmark/device results claimed:** no.
- **Paper placeholder numbers replaced:** no.
- **External datasets, models, repositories, attacks, or baselines downloaded/executed:** no.
- **Generated output class:** synthetic smoke-test output, not a paper result.

## Output provenance

| Output | Producer | Inputs | Classification |
|---|---|---|---|
| `outputs/synthetic_demo/query_results.jsonl` | `run_evaluation` via `scripts/run_synthetic_demo.py` | deterministic fictional scenario, seed 7, `configs/synthetic_demo.yaml` | synthetic query trace |
| `outputs/synthetic_demo/metrics.json` | `memscope.metrics.core.evaluate_queries` | the generated query-result records | synthetic aggregate; not mobile timing |
| `outputs/synthetic_demo/audit_events.json` | in-memory reference store | the three synthetic MemScope reads | synthetic content-free audit trace |
| `outputs/synthetic_demo/metrics.png` | `scripts/make_plots.py` | `metrics.json` only | synthetic plot, visibly labeled |
| `outputs/synthetic_demo/calibration_preflight.json` | `run_calibration` | config validation | `not_applicable`; no threshold or result |
| `outputs/synthetic_demo/ablation.json` | `run_ablation` | deterministic fictional scenario with one label coordinate removed per variant | controlled synthetic ablation, not empirical paper evidence |
| `outputs/synthetic_demo/resolved_config.json` | all configured stages | resolved `configs/synthetic_demo.yaml` | reproducibility/config capture |

All JSON outputs include an explicit notice and/or `paper_result_claimed: false`. Host latency values are deliberately zero because Python desktop timing is not a paper systems measurement.

## Tables and plots

The repository ships no hard-coded empirical result table. The only plot is generated from `metrics.json` produced by code and was visually inspected for title, labels, clipping, and legibility. It is neither conceptual paper evidence nor a real measurement; it is a synthetic pipeline demonstration.

## Integrity checks performed

- Fixed-seed tests compare aggregate metrics and complete query-result JSONL across runs.
- Tests assert that generated metadata uses `result_class: synthetic_smoke_test` and `paper_result_claimed: false`.
- Plotting refuses files without both a MemScope metrics object and result notice.
- No source module contains a network client or an automatic dataset/model download path.
