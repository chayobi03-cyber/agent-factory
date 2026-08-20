# AgentFactory Next Session Handoff — 2026-08-20 Project Audit

## 0. Session Purpose

The next session is **not an M2 historical execution session**.

Purpose:

> Perform a cold, evidence-driven audit of the AgentFactory project itself: objective, target outcomes, milestones, workstreams, task inventory, completed work, gaps, risks, dependencies, and next action items.

The audit must determine whether the repository is still building the intended AgentFactory product or merely accumulating technically correct but locally optimized artifacts.

Do not begin new implementation until the project-level audit establishes what should happen next.

## 1. Canonical Project Identity

- project_id: `agent-factory`
- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- governance_namespace: `AgentFactory`
- external_project_reference: `chayobi03-cyber/investment`

The Investment repository is a boundary reference only. It is not a source of AgentFactory governance, state, workflow rules, lessons, evidence, or policy.

Run first:

```text
python3 scripts/validate_project_context.py
```

Then verify Git branch, remote, HEAD, and checkpoint ancestry.

## 2. Immutable Constraints

Audited OPRO baseline — **DO NOT CHANGE**:

`20a54b92aad0857f75c6200d984b13098c6f4927`

Forbidden in this session:

- OPRO promotion;
- GEPA implementation;
- RE domain implementation;
- audited baseline redefinition;
- M2 historical performance execution;
- OOS;
- optimization;
- stress;
- Monte Carlo.

No `PASS` / `GREEN` from state or documentation without primary execution evidence.

## 3. Forensic / Governance Anchors

- M2 transition checkpoint: `41259e233e5273ad2fe1577e71935702956476b1`
- latest context-boundary remediation HEAD at handoff creation: `7a06aa7ae77ee9fb412be245a20fe398333c515a`
- project-context guard: `scripts/validate_project_context.py`
- context regression: `tests/test_project_context_guard.py`
- context lesson/rules: `docs/governance/LESSONS_LEARNED_2026-08-20_CONTEXT_BOUNDARY.md`

HOTL is an AgentFactory-native concept. HOTL terminology alone is not contamination evidence.

## 4. Current Known State

```text
Audit Evidence Chain: existing prior primary evidence path
CER Resume: must be revalidated from current HEAD evidence
M1-B: GREEN
M2: REVIEW_REQUIRED
M2 historical execution: NOT_EXECUTED
OPRO promotion: FORBIDDEN
GEPA: FORBIDDEN
```

The M2 contract, 12-case matrix, and M2 regression definitions must be preserved during this audit. Their presence does not authorize historical execution.

## 5. Project-Level Audit Objective

Answer these questions with evidence:

### A. What is AgentFactory actually supposed to become?

Extract the current canonical product objective from repository source-of-truth documents. Do not assume the objective from the latest task or branch name.

### B. What outcomes prove the objective was achieved?

Convert the objective into observable outcomes and acceptance criteria.

### C. What are the major milestones?

Build the milestone chain from the repository's current governance/roadmap artifacts.

### D. What workstreams exist?

Group current tasks into coherent workstreams such as:

- Factory kernel / CER;
- evidence and provenance;
- Domain Pack / multi-domain architecture;
- engineering document ingestion;
- evaluation / regression;
- HOTL / human governance;
- model optimization / OPRO / GEPA gates;
- deployment / operationalization;
- documentation / governance.

Do not assume these categories are final; derive them from repository evidence.

### E. What has actually been completed?

For every claimed milestone or major task, distinguish:

```text
DEFINED
IMPLEMENTED
TESTED
PRIMARY-EVIDENCE-VERIFIED
PROMOTED
```

Do not collapse these states.

### F. What is currently incomplete?

Identify:

- blocked tasks;
- stale tasks;
- duplicated tasks;
- orphaned artifacts;
- work that no longer supports the project objective;
- governance debt;
- missing tests/evidence;
- unclear ownership.

### G. What should happen next?

Produce a ranked action list based on:

```text
Objective impact
×
Risk reduction
×
Dependency criticality
×
Evidence readiness
```

## 6. Required Audit Deliverables

Create an evidence-backed project audit containing:

1. **Project objective statement**
2. **Target outcomes / success criteria**
3. **Milestone map**
4. **Workstream map**
5. **Task inventory**
6. **Completed vs merely implemented vs evidence-verified matrix**
7. **Current blockers / risks / dependencies**
8. **Scope-drift findings**
9. **Governance duplication/conflict findings**
10. **Technical debt / evidence debt**
11. **Priority-ranked action items**
12. **Recommended next milestone**

## 7. Cold-Audit Rules

The auditor must actively challenge the project rather than confirm the existing narrative.

Ask:

- Are we solving the correct problem?
- Is the architecture broader than the current domain work?
- Are current tasks necessary for the stated objective?
- Are we confusing artifact creation with product progress?
- Are any milestones defined without a meaningful acceptance outcome?
- Are any “GREEN” states based only on declarations?
- Are any gates blocking because of real product requirements versus tooling limitations?
- Are there duplicate governance rules?
- Are there unresolved project-boundary risks?

When evidence conflicts with documentation, report the conflict rather than choosing the more convenient interpretation.

## 8. M2 Boundary During Audit

M2 remains a readiness-controlled milestone.

Preserve:

- `docs/governance/M2_HISTORICAL_INTEGRATION_CONTRACT_V1.md`
- `docs/governance/M2_ENTRY_REVIEW_2026-08-20.yaml`
- `fixtures/m2/historical_experiment_12_case.yaml`
- `schemas/m2_historical_experiment.schema.yaml`
- `tests/test_m2_historical_contract.py`

But do not execute the historical experiment during the project audit.

## 9. Required End State of Next Session

The next session must end with one of:

`PROJECT_ALIGNED`

or

`PROJECT_REALIGNMENT_REQUIRED`

or

`REVIEW_REQUIRED`

or

`BLOCKED`

Use `PROJECT_ALIGNED` only when the objective, milestones, task inventory, evidence state, and next actions are mutually consistent.

## 10. Next Session Closing Sequence

```text
Project Identity Check
-> Source-of-Truth Review
-> Objective Audit
-> Outcome Audit
-> Milestone Audit
-> Workstream / Task Audit
-> Evidence-State Audit
-> Scope / Governance Drift Audit
-> Gap Analysis
-> Priority Ranking
-> Recommended Next Milestone
-> Git Evidence
-> Session Handoff
```

Do not silently convert this audit into implementation work.
