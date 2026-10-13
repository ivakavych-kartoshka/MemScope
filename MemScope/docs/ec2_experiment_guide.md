# EC2 and device experiment guide

## 1. Provision manually

Create an EC2 workspace and attach encrypted storage. Install this package from a pinned repository commit. Manually obtain each permitted dataset and external artifact after satisfying licenses, authentication, registrations, and repository terms. Never place credentials in YAML or Git.

For Android measurements, separately provision the named AOSP branch, MemScope service/SDK patch, AppSearch/AppFunctions-compatible build, Pixel 8/9 devices, and eligible Samsung device. Record build fingerprints and hardware-key capabilities.

## 2. Normalize and verify

Create the layout in `data_format.md`. Generate `PREPARATION_MANIFEST.json` with raw/normalized hashes, transformation revision, license state, and split hash. Add policy labels using the frozen handbook and complete the agreement/adjudication process before observing final outputs.

```bash
python -m memscope.cli validate-data --name locomo --root /data/memscope/locomo
```

## 3. Pin external systems

For GAAP, Audience-Bound Memory, MNC, AppSearch, MEXTRA, ADAM, SPORE, MINJA, and MemPoison, record artifact commit and reproduce the original setup before connecting it. Do not change attack knowledge or budgets except for the minimal logical connector, and label partial reproductions/reimplementations.

## 4. Configure

Copy `configs/experiment_template.yaml` outside the repository. Set `run.mode: real`, local `data.root`, device/build/model identifiers, artifact roots/commits, seeds, byte budgets, and output directory. Keep secrets in the EC2/device secret mechanism, not config files.

## 5. Gate before execution

Run tests, dataset validation, and the calibration/preflight stage. Resolve every item in `TODO_IMPLEMENTATION.md` relevant to the chosen cell. The present reference runner intentionally stops after real-data schema preflight until the benchmark-specific mapper/scorer and Android transport are author-verified.

## 6. Execute and preserve provenance

Run matched histories, queries, ranker, model, seed, device state, and budgets. Store raw traces and manifest hashes before analysis. Run full experiments only on EC2/devices, never as part of repository generation. Generate figures solely from result files, and retain the failed-run/exclusion log.
