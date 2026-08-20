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

## HOTL cycle 1 — confirm scope drift

**Observation:** AgentFactory roadmap says M1 = RE Hybrid RAG and M2 = RE Engineering Agent, while the branch introduced financial M1-B and historical M2 artifacts.

**Cause:** Project milestone context had drifted from AgentFactory into investment-research semantics.

**Countermeasure:** Establish `AGENT_FACTORY_SCOPE_V1.md`, classify ownership by purpose, and record the finding in the audit tree.

**Verification:** Cross-check against AgentFactory `main` state and the separate Investment repository objective. Scope mismatch confirmed.

## HOTL cycle 2 — verify that the finding is not a false-positive

**Observation:** The affected artifacts were internally coherent and included legitimate generic concepts such as PIT, provenance, evidence, HOTL, and fail-closed gates.

**Cause assessment:** Generic engineering concepts are not contamination by themselves; the decisive signal is their binding to financial source stacks, historical performance, OOS/stress/Monte Carlo, and an M1-B/M2 milestone chain that belongs to the investment project.

**Countermeasure:** Preserve generic CER/HOTL/evidence/optimization governance; quarantine only the high-confidence investment-specific files and remove their workflow references.

**Verification:** Compare against the canonical AgentFactory roadmap and Investment repository README. Classification remains investment-specific for the quarantined set.

## HOTL cycle 3 — recurrence/control-gap remediation

**Observation:** Existing tests checked internal correctness but did not check project ownership. The workflow also retained a direct dependency on the quarantined M2 entry runner.

**Cause:** No canonical machine-readable project scope existed, and the CI gate did not enforce the project boundary before execution.

**Countermeasure:**

1. Add `docs/governance/AGENT_FACTORY_SCOPE_V1.md`.
2. Strengthen `scripts/validate_project_context.py` with identity checks and a high-confidence forbidden-artifact set.
3. Preserve false-positive protection for explicit boundary documentation.
4. Remove quarantined M1-B/M2 financial runtime, schemas, fixtures, tests, governance, and workflow references.
5. Keep Git history intact.

**Verification:** Current checkpoint comparison shows the investment-specific files as removals; current search returns no M1-B/M2 historical artifacts. The Factory Kernel workflow no longer invokes the removed M2 entry runner.

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

## Current remediation result

The confirmed investment-specific active artifacts have been removed by normal corrective commits. No reset, force-push, or history rewrite was used.

Generic AgentFactory-native assets intentionally retained include:

- CER / evidence contracts;
- HOTL failure-analysis loop;
- project/repository identity guard;
- generic optimization governance;
- Factory Kernel workflow;
- Factory Runtime / evaluation harness;
- OPRO baseline regression and candidate status;
- session continuity and evidence-chain governance.

## Remaining validation boundary

The current branch has not yet produced independently retrievable primary CI evidence after this remediation. Therefore repository remediation is **not** promoted to a GREEN/CLEAN claim until the current-SHA workflow run/job/log/artifact/digest chain is independently retrievable.

## Required permanent controls

Project identity must be checked before governance/resume validation, and project scope must be machine-readable. Generic governance terms must be classified by ownership rather than keyword matching.
