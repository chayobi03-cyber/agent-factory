# AgentFactory Next Session Handoff — 2026-08-20 Project Alignment

## 0. Session Purpose

The next session is **not an M2 historical/investment execution session**.

Purpose:

> Complete the AgentFactory project-alignment audit, finish controlled quarantine of confirmed investment-specific artifacts, and then resume the canonical Factory Kernel / multi-domain engineering roadmap only when current-SHA evidence is available.

## 1. Canonical Project Identity

- project_id: `agent-factory`
- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- governance_namespace: `AgentFactory`

Canonical scope: `docs/governance/AGENT_FACTORY_SCOPE_V1.md`
Canonical roadmap: `docs/ROADMAP_WBS.md`
Forensic record: `11_Audit/REPOSITORY_CONTEXT_CONTAMINATION_2026-08-20.md`

The separate `chayobi03-cyber/investment` repository is an external boundary only. It must not provide AgentFactory governance, session state, milestone definitions, workflow rules, lessons, evidence, or project-specific HOTL policy.

Run first:

```text
python3 scripts/validate_project_context.py
```

Then verify Git remote, branch, HEAD, checkpoint ancestry, and audited baseline ancestry.

## 2. Canonical AgentFactory Objective

AgentFactory is a domain-agnostic engineering agent factory. The reusable product is the kernel: Domain Pack loading, evidence/claim handling, CER gates, HOTL control, traceability, regression, benchmarking, and controlled optimization.

Canonical milestone progression from `docs/ROADMAP_WBS.md`:

```text
M0 Foundation
 -> M0.5 Factory Kernel Verification
 -> M1 RE Hybrid RAG
 -> M2 RE Engineering Agent
 -> M3 Reporting
 -> M4 Agentic RAG
 -> M5 Method Ensemble
 -> M6 EMI/RFI
 -> M7 CST
 -> M8 Optimization
 -> M9 Domain Factory
```

Financial-investment research is not an AgentFactory core milestone or canonical domain.

## 3. Immutable Constraints

Audited OPRO baseline — **DO NOT CHANGE**:

`20a54b92aad0857f75c6200d984b13098c6f4927`

Forbidden until separately gated:

- OPRO promotion;
- GEPA implementation;
- RE domain implementation before Factory Kernel gate;
- audited baseline redefinition;
- PASS / GREEN without primary execution evidence;
- investment-specific historical performance execution;
- backtest / OOS / stress / Monte Carlo for investment research.

## 4. Confirmed Scope-Drift Finding

The forensic audit confirmed that the branch contains a set of financial/investment-specific M1-B and historical M2 artifacts that do not belong in the active canonical AgentFactory tree.

Supporting evidence:

1. AgentFactory roadmap defines M1 as RE Hybrid RAG and M2 as RE Engineering Agent.
2. The affected branch artifacts define financial source stacks, PIT/vintage financial datasets, historical performance experiments, OOS, stress, and Monte Carlo sequencing.
3. AgentFactory `main` governance already records that financial domain drift was identified and the financial experiment was moved to a historical branch.
4. `chayobi03-cyber/investment` independently defines capital-preservation public-equity research with M1 Data Integrity and M2 Portfolio Risk Engine.

Classification: **Investment-specific contamination / quarantine required**.

Generic CER/HOTL/evidence/optimization governance remains AgentFactory-native and is preserved.

## 5. Quarantine Rule

Do not rewrite Git history or force-push.

Remove confirmed investment-specific material from the active AgentFactory runtime/governance path using normal corrective commits. Git history remains the forensic recovery source.

The quarantine list is maintained in:

`11_Audit/REPOSITORY_CONTEXT_CONTAMINATION_2026-08-20.md`

Do not delete generic HOTL, CER, evidence, project-identity, or optimizer-governance artifacts merely because they were developed during the contaminated session.

## 6. Current Evidence State

Prior primary evidence remains valid only for its exact target SHA. It cannot certify later commits.

Current branch evidence must be independently retrievable as:

```text
workflow run
 -> job
 -> step logs
 -> machine artifact
 -> GitHub digest
 -> independent digest verification
```

Missing current-SHA evidence = `REVIEW_REQUIRED`, never GREEN by inference.

## 7. Required Validation After Quarantine

1. Repository identity.
2. Canonical scope guard.
3. Current branch / HEAD.
4. Forensic anchor ancestry.
5. Audited OPRO baseline unchanged.
6. No investment-specific artifact in canonical runtime/governance paths.
7. Generic CER/HOTL/evidence/optimization assets preserved.
8. Full pytest regression.
9. CER RC-01..RC-08 from current primary evidence.
10. Current-SHA workflow run/job/log/artifact/digest.

## 8. Next Product Work

Do not resume historical investment M2 work.

After repository alignment and current-SHA evidence are GREEN, resume the actual AgentFactory roadmap from the highest incomplete canonical work item, prioritizing:

1. Factory Kernel / multi-domain workflow verification;
2. engineering-document ingestion baseline;
3. Domain Pack / evidence-grounded engineering workflow;
4. only then governed RE domain onboarding.

## 9. Session Close

```text
Project Identity
-> Scope Contract
-> Forensic Classification
-> Controlled Quarantine
-> Generic Governance Preservation
-> Regression
-> Current-SHA Primary Evidence
-> Project Alignment Decision
-> Git Evidence
-> Handoff
```

Final status vocabulary:

`PROJECT_ALIGNED` / `PROJECT_REALIGNMENT_REQUIRED` / `REVIEW_REQUIRED` / `BLOCKED`
