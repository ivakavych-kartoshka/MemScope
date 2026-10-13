# Citation consistency report

Audit date: 2026-10-03.

- Bibliography entries: **53**.
- Distinct cited keys: **53**.
- Missing bibliography keys: **0**.
- Uncited bibliography entries: **0**.
- Duplicate keys: **0**.
- Invented/anonymous entries retained: **0**.
- Seed identifiers cross-checked against official arXiv/ACL/ACM/USENIX/platform pages: **yes**.
- Recent preprint claims limited to abstract-supported statements unless the map says full-text verified: **yes**.
- Official product/API pages used only for documented platform behavior: **yes**.
- Different-topic references dominating the paper: **no**; more than 60% of entries directly concern agent memory, agent-memory attacks/governance, mobile-agent memory, or its evaluation.

## Automated checks

A recursive scan of all `.tex` files extracted citation keys and compared them with `references_verified.bib`: 53 cited, 53 present, no missing and no unused keys. BibTeX completed. Remaining BibTeX warnings are empty page fields for proceedings/preprints where page ranges were not verified; no identifier/key warning remains.

## Metadata caveats

- 2026 arXiv records may later acquire conference versions; the current entries intentionally cite the verified preprints.
- Product documentation is temporally unstable and must be rechecked at submission.
- The bibliography does not include AME because its author metadata was not resolved in this pass.
- Author order in retained recent seed references follows official arXiv pages; MEXTRA follows ACL Anthology; Riverbed/Vanish/TaintDroid follow USENIX; classic DOI metadata follows publisher pages.

## Claim-support conclusion

No citation is used to claim completed MemScope performance. Attack papers support the existence and threat-model direction of the corresponding attacks, not that MemScope defeats them. Benchmark papers support dataset/task descriptions. Formal/security papers support conceptual foundations rather than transferring their theorems to MemScope without proof.
