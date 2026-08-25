# Repository Context Contamination Forensic Record — 2026-08-20

## Final finding
A post-checkpoint review confirmed that `p0/opro-baseline` had allowed investment-specific financial M1-B/M2 historical-performance artifacts to become part of the active AgentFactory tree. This was real project-context contamination, not a HOTL keyword false-positive.

AgentFactory canonical roadmap: M1 RE Hybrid RAG, M2 RE Engineering Agent. Quarantined material: financial source ingestion, PIT/vintage financial datasets, historical performance experiments, OOS, stress, Monte Carlo, and related regression machinery.

The separate `chayobi03-cyber/investment` repository is a capital-preservation public-equity research program whose M0/M1/M2/M3 milestone semantics match the quarantined material.

## Classification
- Generic CER / HOTL / evidence governance: AgentFactory-native
- Generic optimization governance: AgentFactory-native
- Project/repository identity guard: AgentFactory-native
- Financial M1-B source/provenance stack: Investment-specific contamination
- Financial M1-B fixtures/evidence: Investment-specific contamination
- Historical-performance M2 contract/matrix/runtime/tests: Investment-specific contamination
- Investment-specific M2 readiness CI: Investment-specific contamination
- Cross-project boundary documentation: AgentFactory audit evidence

## Forensic anchor
`41259e233e5273ad2fe1577e71935702956476b1`

All contaminated content remains recoverable through Git history. Active-tree remediation used file-level inverse changes only; no history rewrite and no force-push were used.

## Root cause
### Why did the wrong context enter?
A branch-level historical Investment experiment was allowed to become represented as active AgentFactory M1-B/M2 governance context. The immediate failure was project-context identification; the deeper failure was that milestone/workstream ownership was not machine-enforced.

### Why was it not detected?
Existing tests and CER checks primarily verified internal consistency of the introduced artifacts. They did not independently verify that the milestone, dataset, governance vocabulary, and workflow belonged to AgentFactory. A coherent but wrong-project artifact set could therefore pass its local contracts.

## Remediation
1. Added canonical scope contract `docs/governance/AGENT_FACTORY_SCOPE_V1.md`.
2. Added machine-checkable context guard `scripts/validate_project_context.py`.
3. Added context regression tests.
4. Removed investment-specific M1-B/M2 financial runtime, schema, fixtures, governance, and tests from the active tree.
5. Removed the investment M2 readiness step from `.github/workflows/factory-kernel.yml`.
6. Preserved generic CER/HOTL/evidence/optimization governance.
7. Corrected stale evidence-only PR metadata.
8. Preserved audited OPRO baseline SHA unchanged.

## RCA cycles
### Cycle 1 — Scope verification
Confirmed mismatch between AgentFactory roadmap and active branch milestone structure.

### Cycle 2 — Ownership discrimination
Confirmed HOTL/CER/evidence/optimization are valid AgentFactory concepts; only financial/investment-specific workflow material was contaminated.

### Cycle 3 — Control-gap closure
Added scope contract, identity guard, provenance-aware boundary scan, regression coverage, and workflow decontamination.

## Evidence boundary
Tree remediation is complete by static forensic inspection. Final `CLEAN` / `REMEDIATED` requires primary current-SHA runtime evidence:

`target SHA -> workflow run -> job -> logs -> artifact -> digest -> independent digest verification`

The available workflow-run connector exposes pull-request-triggered runs only. A missing returned run is therefore `EVIDENCE_UNAVAILABLE`, not inferred PASS or FAIL.

## Final status
`REVIEW_REQUIRED`

Reason: contamination was found and remediated, but current-SHA primary CI evidence is not independently retrievable through the available evidence path.
