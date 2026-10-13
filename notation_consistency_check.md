# Notation consistency check

- `\mathcal{M}`: system-owned labeled-memory store only.
- `m_i`: item; `x_i`: payload; `z_i`: provenance; `\ell_i`: label; `h_i`: digest.
- `P_i`, `A_i`, `T_i`, `C_i`: allowed purpose, app, tool, and consumer sets. Uppercase script alphabets denote their universes.
- `s_i`, `b_i`, `e_i`: sensitivity, not-before time, and expiry.
- `q`: authenticated task context; `\kappa_q`: signed retrieval token.
- `\Gamma`: token set admitted together for one derived write; `w=(a^*,c^*,p^*)`: the shared composition context (caller app, consumer, purpose). `|\Gamma|=1` reduces to single-token admission.
- `\tau_q`: trusted evaluation time; `e_q`: token expiry. Item and token expiry are not conflated.
- `\Auth`: authorization predicate; `\View`: authorized pre-ranking view; `\Meet`: derived-label meet.
- `\mathcal{G}`/`\DAG`: derivation graph; no graph symbol is reused for gradients or datasets.
- `B`: byte budget; `R`: ranker; `k`: requested result count; `c`: projected candidate count; `d`: embedding dimension; `n`: store size.

Checks:

- All equation symbols are introduced before use: pass.
- No symbol has two conflicting meanings: pass.
- Set/order direction is consistent: `\ell \preceq \ell'` means `\ell` is no more permissive: pass.
- Time comparisons consistently use `b_i <= tau < e_i`: pass.
- Theorem variables match the system model: pass.
- Undefined theorem constants: none.
- Equation labels referenced by `\cref`/`\eqref`: pass after compile.
- Citation keys and cross-references undefined: none in final compile.

Implementation caveat: the release-snapshot item-expiry recheck is now shown explicitly as the per-item loop in Algorithm 1 and is implemented in `methods/retrieval.py` (`final_items` reauthorization); the earlier caveat that Algorithm 1 "abbreviates" this check no longer applies. Multi-token derived admission uses one composition context `w` shared by all tokens in `\Gamma`.
