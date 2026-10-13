# TODO before submission

## Blocking empirical work

- Implement the AOSP MemScope service, Agent SDK, token issuer, scoped AppSearch store, label propagator, compactor, audit UI, and recovery path.
- Demonstrate complete mediation and document any remaining private caches/logs/cloud stores.
- Run RQ1--RQ6 on Pixel 8, Pixel 9, and the available Samsung device.
- Replace Tables 3--4 and Figure 6 with raw-data-backed results and confidence intervals.
- Reproduce or clearly label reimplementations of MEXTRA, MINJA, ADAM, SPORE, and both MemPoison settings.
- Build and validate the synthetic multi-app workload and policy oracle.
- Release raw traces, analysis scripts, build manifests, device metadata, prompts, seeds, and checksums.

## Citations and concurrent work

- Refresh the literature search immediately before submission.
- Replace 2026 arXiv citations with archival versions where available.
- Add exact versioned Mem0/Letta references if used as executable baselines.
- Resolve MemGUI-Bench only if retained in experiments.
- Pin AOSP/AppSearch/AppFunctions documentation to the implementation version.

## Theory and security validation

- Map every formal assumption to code and an integration test.
- Add property-based tests for label meets, derivation paths, and expiry.
- Run negative controls for token forgery/replay, confused deputy, shadow cache, clock rollback, ranker bypass, and authorized-recipient copying.
- Empirically measure attribution false acceptance/rejection, especially for high-sensitivity items.
- Do not strengthen the interface theorem into semantic non-inference.

## Author and venue metadata

- Replace anonymous author/affiliation placeholders.
- Confirm author order, corresponding author, ORCIDs, acknowledgments, funding, conflicts, and ethics approval.
- Select the actual venue. The source targets ACM MobiSys, while the requested artifact uses Elsevier-compatible `elsarticle`; convert to the final venue template and page/appendix rules.
- Add highlights/graphical abstract declarations only if required by the chosen Elsevier journal.

## Figures and LaTeX

- Replace conceptual plot coordinates; never submit them as measurements.
- Regenerate figure previews after result insertion and rerun the overlap audit.
- Fix or accept remaining minor overfull/underfull box warnings under the final venue template.
- Investigate the Tectonic cached `algorithm.sty` invalid-UTF-8 warning or compile with a clean TeX Live distribution.
- Add verified page/article numbers to proceedings entries when available to remove BibTeX empty-page warnings.

## Assumptions requiring real validation

- Binder/AppFunction identity is trustworthy across nested and legacy tool adapters.
- Policy epochs and item expiry are rechecked atomically at release.
- No ranker/model path can access unauthorized plaintext or embeddings.
- StrongBox/Keystore behavior matches the tested vendor build.
- Hard-pinned safety items fit realistic storage budgets.
- Purpose defaults are understandable and do not cause unacceptable denial or prompt fatigue.

Current status: design manuscript complete; empirical submission blockers remain.
