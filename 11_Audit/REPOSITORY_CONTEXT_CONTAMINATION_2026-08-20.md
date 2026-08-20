# Repository Context Contamination Forensic Record — 2026-08-20

## Finding

A post-checkpoint branch review found a set of financial/investment-specific M1-B/M2 historical artifacts in `p0/opro-baseline` that do not belong to the canonical AgentFactory project roadmap.

The canonical AgentFactory roadmap defines M1 as RE Hybrid RAG and M2 as RE Engineering Agent. The affected artifacts instead define financial-source ingestion, PIT/vintage financial datasets, historical performance experiments, OOS, stress, and Monte Carlo sequencing.

The AgentFactory `main` session state independently records that financial domain drift had been identified and that the financial experiment was moved to a historical branch. This is supporting evidence that the material is not canonical AgentFactory scope.

The separate `chayobi03-cyber/investment` repository is explicitly a capital-preservation public-equity research project with M0 Risk Contract, M1 Data Integrity, M2 Portfolio Risk Engine, and M3 Asset Allocation Backtest. Its milestone semantics match the affected M1-B/M2 material much more closely than the AgentFactory roadmap.

## Classification

| Category | Classification |
|---|---|
| Generic HOTL / CER / evidence governance | AgentFactory-native |
| Generic optimization governance | AgentFactory-native |
| Project/repository identity guard | AgentFactory-native |
| Financial M1-B source/provenance stack | Investment-specific contamination |
| Financial M1-B fixtures/evidence | Investment-specific contamination |
| Historical-performance M2 contract/matrix/implementation | Investment-specific contamination |
| M2 CI readiness tied to historical performance | Investment-specific contamination |
| Cross-project boundary lesson | Audit evidence, not canonical project context |

## Forensic anchor

`41259e233e5273ad2fe1577e71935702956476b1`

All affected content remains recoverable through Git history. The remediation removes the material from the active AgentFactory tree; it does not rewrite history or force-push.

## Remediation policy

1. Preserve Git history.
2. Remove investment-specific material from active AgentFactory governance/runtime/tests.
3. Keep generic factory governance and HOTL mechanisms.
4. Restore canonical AgentFactory project context.
5. Add machine-checkable project scope and repository identity guards.
6. Require primary CI evidence before declaring GREEN.

## Root cause

The immediate cause was project-context drift: a branch-level historical investment experiment was allowed to become represented as the active AgentFactory M1-B/M2 governance context. The deeper control failure was the absence of a canonical project-scope contract enforced at session start and CI.

## Detection gap

Existing tests and CER checks verified internal consistency of the affected artifacts. They did not verify that the milestone, dataset, and governance vocabulary belonged to the AgentFactory project. Therefore internally coherent but wrong-project artifacts could pass their own local contracts.

## Required permanent control

Project identity must be checked before governance/resume validation, and project scope must be machine-readable. Generic governance terms must be classified by ownership rather than keyword matching.
