# Agent Factory Next Session Handoff — 2026-08-20 Domain Matrix CI Remediation

## Canonical identity

- repository: `chayobi03-cyber/agent-factory`
- branch: `p1/domain-matrix-workflow-v0.1`
- audited OPRO baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927`

## Constraints

- GEPA implementation forbidden
- OPRO promotion forbidden
- RE Domain implementation forbidden before the governed workflow gate
- audited OPRO baseline SHA immutable
- PASS without primary execution evidence forbidden
- financial data is not a core Agent Factory requirement
- synthetic Domain Matrix fixtures are fixture-only and not production domain knowledge

## Objective

Validate the shared Factory Kernel workflow across synthetic RE / EMI / CST / ESD Domain Packs and preserve the Kernel / Domain Pack boundary.

## Acceptance

- actual CI execution is observed for the current PR HEAD
- CER RC-01..RC-08 PASS
- Domain Matrix E2E executes for all four synthetic domains
- lifecycle coverage is ingest → parse → normalize → retrieve → verify → evaluate → CER gate → execute → report → trace
- Domain Matrix evidence artifact is produced
- no Runtime-GREEN claim without primary execution evidence
