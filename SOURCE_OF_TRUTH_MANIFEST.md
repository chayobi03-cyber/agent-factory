# Agent Factory — Source of Truth Manifest

This manifest defines the current canonical Source of Truth for the Agent Factory repository and separates the live Git baseline from historical design-package and experiment artifacts.

## 1. Canonical Source of Truth

- Repository: `chayobi03-cyber/agent-factory`
- Canonical implementation is the live Git repository tree.
- The active engineering roadmap is governed by `docs/governance/AGENT_FACTORY_SCOPE_V1.md` and `docs/ROADMAP_WBS.md`.
- Historical ZIP/design-package paths and isolated experiment branches do not override the live baseline.

## 2. Product Scope Authority

- `docs/governance/AGENT_FACTORY_SCOPE_V1.md` — mission, Kernel/Domain Pack boundary, provenance boundary, non-goals
- `docs/governance/ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` — current architecture refocus
- `README.md` — repository orientation
- `docs/ROADMAP_WBS.md` — implementation roadmap and dependencies

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

- `docs/governance/CER_CONTEXT_CONTRACT.md`
- `docs/governance/CER_ARCHITECTURE_CONTRACT_V1.md`
- `docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md`
- `docs/governance/CURRENT_SESSION_STATE.yaml`
- `docs/governance/CER_OPRO_GEPA_LESSONS_2026-08-18.md`
- `docs/governance/OPTIMIZATION_METHOD_CONTROL_V1.md`
- `schemas/session_state.schema.yaml`
- `scripts/validate_session_state.py`
- `templates/agent/AGENT_FACTORY_CONTEXT_PACKET.yaml`
- `11_Audit/EXTERNAL_LLM_AUDIT_PROMPT.md`
- `11_Audit/AUDIT_RESULT_2026-08-14.md`

## 5. Evidence Baseline

The latest verified primary Factory Kernel execution remains:

- target SHA: `2adbf5304491cde04f02fb997f766b40460ccf60`
- workflow run: `32126799804`
- job: `95679046613`
- artifact: `factory-kernel-machine-evidence`
- independently verified artifact digest: `sha256:11f629929a433945447af706662353885f1419c437017be938d5b18fafa1010d`
- Factory Kernel: `10/10`
- RC-01..RC-08: PASS
- OPRO regression: PASS
- pytest: `44/44`

## 6. Historical Experiment Policy

Domain-specific experiments remain historical unless explicitly promoted through a versioned architecture decision.

The 2026-08-19 financial provenance experiment is intentionally outside the core product path. Its history is retained on a dedicated branch for traceability and must not be treated as a kernel requirement.

## 7. Source-of-Truth Resolution Rule

When artifacts disagree:

1. current run context and frozen CER snapshot have highest runtime priority;
2. current Git repository is the canonical implementation baseline;
3. current scope and architecture contracts govern roadmap interpretation;
4. historical archives and experiment branches are evidence of prior state only;
5. model memory or unpinned historical text must not override versioned repository artifacts.

Any promotion of an experiment into the core must be recorded as an explicit versioned architecture decision with impact analysis and regression requirements.

## 8. Optimization Authority

Optimization is method-independent. OPRO, GEPA, or another optimizer may vary internally, but evaluator, evidence, regression, approval, promotion, HOTL, and CER controls remain canonical.
