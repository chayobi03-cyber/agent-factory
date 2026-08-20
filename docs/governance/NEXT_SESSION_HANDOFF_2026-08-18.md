# AgentFactory Next Session Handoff — 2026-08-20 Project Context Remediation

## Canonical identity
- project_id: `agent-factory`
- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- governance_namespace: `AgentFactory`
- external_project_reference: `chayobi03-cyber/investment` (boundary reference only)

## Canonical scope
AgentFactory is a domain-agnostic engineering Agent Factory. The canonical roadmap is M0 Foundation -> M0.5 Factory Kernel Verification -> M1 RE Hybrid RAG -> M2 RE Engineering Agent -> M3 Reporting -> M4 Agentic RAG -> M5 Method Ensemble -> M6 EMI/RFI -> M7 CST -> M8 Optimization -> M9 Domain Factory.

Investment-specific financial M1-B/M2 historical-performance work is not part of the canonical AgentFactory milestone sequence.

## Forensic anchor
`41259e233e5273ad2fe1577e71935702956476b1`

## Remediation outcome
Confirmed investment-specific artifacts were removed from the active AgentFactory tree without history rewrite or force-push. Generic CER/HOTL/evidence/optimization governance was preserved. The Factory Kernel workflow no longer invokes the removed investment M2 entry runner.

Forensic record:
`11_Audit/REPOSITORY_CONTEXT_CONTAMINATION_2026-08-20.md`

Context guard:
`scripts/validate_project_context.py`

## Current gate
```text
project-context remediation = COMPLETE_BY_TREE_REVIEW
current-SHA primary CI evidence = REVIEW_REQUIRED
M2 historical execution = FORBIDDEN
OPRO promotion = FORBIDDEN
GEPA implementation = FORBIDDEN
RE domain implementation until Factory Kernel gate = FORBIDDEN
```

## Primary evidence rule
Documentation and state are not execution evidence. A GREEN/REMEDIATED claim requires:
`target SHA -> workflow run -> job -> logs -> artifact -> GitHub digest -> independent verification`

The available workflow-run connector only exposes pull-request-triggered runs for commit lookup. Absence of a returned run must remain `EVIDENCE_UNAVAILABLE`, not inferred failure or success.

## Preserved generic governance
- CER Session Continuity / Resume Contract
- Audit Evidence Chain CI Contract
- Generic HOTL failure-analysis loop
- Generic evidence/provenance architecture
- Factory Kernel regression
- OPRO baseline contract and regression
- Project/repository identity guard
- AgentFactory scope and roadmap

## Quarantined investment-specific material
Financial source/PIT/vintage/provenance stack, financial fixtures, historical-performance M2 contract/matrix, related runtime, and related tests were removed from the active canonical AgentFactory tree. They remain recoverable through Git history.

## Next session
Do not begin M2 historical work. First establish current-SHA primary CI evidence and re-run repository/project boundary validation. Once evidence is independently retrievable, reassess final repository status and then choose the next canonical AgentFactory milestone from the roadmap.
