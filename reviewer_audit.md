# Reviewer-style self-audit

## Locked topic and fit

MemScope is an Android OS-enforced, purpose-bound persistent memory service for mobile personal agents. The title, abstract, system entities, formal objects, algorithms, attacks, baselines, and experiments match the idea PDF. No central topic drift was found.

## Final contributions and evidence

1. **Per-item mobile-agent memory labels and task-rooted tokens.** Evidence: formal item/context definitions, authorization predicate, Android AppSearch/AppFunctions implementation mapping, architecture figure.
2. **Conservative propagation for generated summaries/reflections.** Evidence: meet equation, Algorithm 2, Lemma 1, Lemma 2 (composition principal), Theorem 2, path lemma, policy examples.
3. **Retrieval-time expiry and policy-aware mobile eviction.** Evidence: authorization time conjunct, Theorem 4, compaction algorithm, explicit non-optimal storage objective.
4. **Interface-level safety analysis.** Evidence: four assumptions, complete proofs of admission, derivation, cross-scope returned-plaintext, expiry, plus complexity proposition and countermodels.
5. **Phone-based evaluation plan.** Evidence: RQ1--RQ6, device/software controls, attacks, baselines, metrics, ablations, statistics, reproducibility appendix. This is planned evidence only.

## Novelty boundary

The manuscript does not claim to invent lifecycle authorization, purpose scopes, IFC, or restrictive label propagation. Audience-Bound Memory, MNC, and GAAP narrow the contribution. The remaining proposed novelty is the Android systems combination: task/AppFunction-bound tokens, per-document pre-ranking views, derived-memory restrictions, read-time TTL, mobile eviction, and phone evaluation.

## Citation audit

- 53 verified entries; 53 cited; no missing or unused keys.
- 9 candidates rejected/deferred.
- Recent arXiv papers are used only for abstract-supported claims unless noted otherwise.
- Platform pages support platform behavior only.
- Main risk: several 2026 preprints may change or receive archival versions before submission; a fresh search is mandatory.

## Mathematical risks

- The proofs are correct only under strong complete-mediation, identity, state/time, and ranker-confinement assumptions.
- The cross-scope theorem concerns returned stored plaintext, not semantic inference or external copies.
- Attribution verification is empirical and may accept unsupported content; label safety does not prove truth.
- The compaction heuristic has no optimality or approximation guarantee.

## Experimental gaps

- No AOSP implementation, attack run, utility score, latency, energy, or storage measurement exists in the supplied project.
- Mem0/Letta and GAAP-style baselines need exact versioned implementations.
- Some attack papers may lack public artifacts and require labeled reimplementations.
- Device access, power instrumentation, and vendor API availability are unconfirmed.
- The multi-app benchmark and policy labels require validation and ethics review if real-user data is ever introduced.

## Likely reviewer objections

1. “This is ACLs on a database.” Response needed from implementation/evaluation: derived LLM memory, task/tool tokens, complete mediation, and lifecycle attacks must demonstrate why ordinary package ACLs are insufficient.
2. “Purpose is unverifiable.” The design authenticates declared task context, not human intent; usability and policy-error studies are necessary.
3. “An authorized model can leak.” Correct; downstream IFC/DP is complementary and the claim is deliberately narrower.
4. “No empirical systems contribution yet.” Correct and currently fatal for submission; all results remain TODO.
5. “Concurrent work already covers the idea.” The paper must empirically establish its mobile/OS-specific value and rerun the literature search.
6. “The trusted computing base is too large.” Prototype code paths and mediation tests must quantify and minimize it.

## Figure and LaTeX status

- Six figures rendered and visually inspected; all pass the readability audit after resizing/rerouting.
- Elsevier `elsarticle` manuscript compiles with Tectonic to a 56-page preprint.
- No undefined citations or cross-references.
- Remaining warnings are minor box-quality warnings, a Tectonic-cache UTF-8 warning in `algorithm.sty`, and BibTeX empty-page warnings for records whose page ranges were not verified.

## Overall assessment

The manuscript is a credible design-and-analysis draft and a detailed experiment plan, but not yet a submission-ready empirical systems paper. Its scientific credibility depends on maintaining the current narrow claims and completing the implementation and evaluation without replacing placeholders with selective or fabricated numbers.
