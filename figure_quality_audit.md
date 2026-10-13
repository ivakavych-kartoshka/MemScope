# Figure quality audit

Final PDF reviewed at 150% rasterization from the compiled `main.pdf` on 2026-10-03. Preview files are in `figure_previews/`.

| Figure file | Label | PDF page | Icons/shapes | Routing / overlap | Color + grayscale | Caption | Inspected | Result |
|---|---|---:|---|---|---|---|---|---|
| `figures/tikz_architecture.tex` | `fig:architecture` | 12 | Pure-TikZ database cylinder, service-boundary region, role-specific rounded modules, flow glyphs | Separate normal, policy, return, attack, and key lanes; query/payload labels placed on opposite curves; no node/text crossings after revision | Blue solid, green solid, orange dashed, gray dashed; shape/line styles remain distinguishable | Explains trust boundary and color grammar | `figure_previews/page_12.png` | Pass |
| `figures/tikz_method_pipeline.tex` | `fig:pipeline` | 13 | Numbered stage icons and typed boxes | Orthogonal sequential route; restart lane outside boxes; no crossings through labels | Color and box type identify data/policy/theory/maintenance | States security-critical order | `figure_previews/page_13.png` | Pass |
| `figures/tikz_threat_privacy_robustness.tex` | `fig:threat-map` | 15 | Shield, database, attacker/control modules | Attack arrows terminate at agent; read/write control lanes separate; denied branch routed below | Orange dashed attacks; green controls; blue authorized result; gray denied view | States protected and unprotected cases | `figure_previews/page_15.png` | Pass |
| `figures/tikz_theory_diagram.tex` | `fig:theory-deps` | 25 | Assumption/lemma/theorem/design node types | Routed dependency edges avoid node interiors; one deliberate convergence point, no text overlap | Gray/purple/green/blue plus node shapes | Ties guarantees to explicit assumptions | `figure_previews/page_25.png` | Pass |
| `figures/tikz_experimental_setup.tex` | `fig:experimental-setup` | 29 | Workload, attack, harness, baseline, defense, metrics, output modules | Separate workload/attack/factor inputs and baseline/MemScope branches; no cropped output after scaling | Blue normal, orange dashed attack, green defense, purple metrics | Explicitly says no completed result | `figure_previews/page_29.png` | Pass |
| `figures/pgfplots_placeholder_results.tex` | `fig:placeholder-trends` | 34 | PGFPlots marks and line styles | No label/axis collision; legends stacked within subfigure widths | Markers and solid/dashed styles make grayscale readable | Boldly labels curves conceptual/non-results | `figure_previews/page_34.png` | Pass |

Wide comparison and placeholder tables were also inspected on pages 9 and 33. Both were resized to the text width after the first compile revealed clipping.

No external icon images are used. The iconography is pure TikZ (database cylinder, shield, numbered stages, grouped trusted boundary, role-specific shapes) to avoid fragile font dependencies.
