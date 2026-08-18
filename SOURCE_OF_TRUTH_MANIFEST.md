# Agent Factory — Source of Truth Manifest

This manifest defines the current canonical Source of Truth for the Agent Factory repository and separates the live Git baseline from historical design-package archives.

## 1. Canonical Source of Truth

- Repository: `chayobi03-cyber/agent-factory`
- Branch: `main`
- Canonical implementation structure is the live Git repository tree.
- Current repository content overrides historical archive/package paths unless an explicit versioned migration decision states otherwise.

## 2. Historical Design Package

The following archive is retained as a historical snapshot / handover artifact:

- Archive: `Agent-Factory-v0.1-MDD-Design.zip`
- SHA-256: `56a1d0592e2e48a70b4544610d003798fd0dc90effb0ac7280d85599cdab5a78`

The numbered package paths below describe the historical package layout only. They are not current repository paths and must not be treated as a second live Source of Truth.

## 3. Current Canonical Repository Structure

- `docs/` — vision, MDD, roadmap, RE PoC, technology survey, governance
- `schemas/` — canonical data contracts
- `workflows/` — workflow definitions
- `templates/` — benchmark, Domain Pack, lesson, and agent context templates
- `src/` — implementation interfaces/skeleton
- `11_Audit/` — audit prompts and results
- `scripts/` — executable validation and workflow support
- `README.md` — repository orientation
- `SOURCE_OF_TRUTH_MANIFEST.md` — canonical mapping and migration authority

## 4. Governance / CER Canonical Artifacts

- `docs/governance/CER_CONTEXT_CONTRACT.md` — CER definition, policy/context model, snapshot and handoff principles
- `docs/governance/CER_ARCHITECTURE_CONTRACT_V1.md` — canonical CER architecture contract v1.0
- `docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md` — session continuity, checkpoint, resume, handoff, and closure control
- `docs/governance/CURRENT_SESSION_STATE.yaml` — machine-readable session continuation pointer
- `docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md` — current human-readable session handoff
- `schemas/session_state.schema.yaml` — session state schema and resume invariants
- `scripts/validate_session_state.py` — executable resume consistency validator
- `templates/agent/AGENT_FACTORY_CONTEXT_PACKET.yaml` — external-agent context packet template
- `11_Audit/EXTERNAL_LLM_AUDIT_PROMPT.md` — independent audit prompt
- `11_Audit/AUDIT_RESULT_2026-08-14.md` — recorded external audit result

## 5. Current-to-Historical Mapping

Historical package structure is mapped conceptually to the current repository as follows:

| Historical package | Current canonical location |
|---|---|
| `00_MDD/` | `docs/` |
| `01_Architecture/` | `docs/` + `src/` + governance docs |
| `02_Schemas/` | `schemas/` |
| `03_Workflows/` | `workflows/` |
| `04_Benchmark/` | `templates/` + future benchmark implementation artifacts |
| `05_Milestone_WBS/` | `docs/ROADMAP_WBS.md` |
| `06_RE_PoC/` | `docs/RE_POC.md` |
| `07_Tech_Survey/` | `docs/TECH_SURVEY.md` |
| `08_ADR/` | repository governance/design records as migrated |
| `09_Templates/` | `templates/` |
| `10_Implementation_Skeleton/` | `src/` + `workflows/` |
| `11_Audit/` | `11_Audit/`

## 6. Source-of-Truth Resolution Rule

When two artifacts disagree:

1. current run context and frozen CER snapshot have highest runtime priority;
2. current Git repository is the canonical implementation baseline;
3. historical archives are evidence of prior design state only;
4. model memory or unpinned historical text must not override versioned repository artifacts.

Any migration from a historical package into the current repository must be recorded as an explicit versioned change.

For Session Continuity, `CURRENT_SESSION_STATE.yaml` is a continuation pointer and does not supersede the live Git state, CER snapshot, WorkflowRun evidence, or audit decisions. The actual Git branch/HEAD must be resolved from Git at resume time.

## 7. Manifest Status

`MATERIAL_DRIFT` identified during the 2026-08-14 internal/external audit cycle has been resolved by explicitly declaring the live Git repository as canonical and the numbered ZIP package as historical.

## 8. Next Contract Authority

CER implementation must follow:

`docs/governance/CER_ARCHITECTURE_CONTRACT_V1.md`

`docs/governance/CER_CONTEXT_CONTRACT.md`

Session Continuity implementation must additionally follow:

`docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md`

`schemas/session_state.schema.yaml`
