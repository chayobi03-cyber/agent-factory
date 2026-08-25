# Governance Documents Index
**Purpose:** so a new session can tell in under a minute which of the 22 documents in `docs/governance/` are the live, actively-enforced contracts versus historical record. Nothing below was deleted — this is a status index, not a cleanup.

Status legend: **CANONICAL** (actively read/enforced by code, or the current live contract) · **HISTORICAL** (valid record of a past session, not enforced) · **SUPERSEDED** (replaced by a newer canonical doc, kept for history) · **NEEDS REVIEW** (stale reference found)

| Document | Status | Why |
|---|---|---|
| `CURRENT_SESSION_STATE.yaml` | **CANONICAL** | The live state pointer. Read by `validate_project_context.py` and `validate_session_resume.py` on every run. |
| `NEXT_SESSION_HANDOFF_2026-08-18.md` | **CANONICAL** | Read by RC-03..RC-07 (identity/baseline/constraint checks). Contains the structured YAML front-matter added 2026-08-24. |
| `AGENT_FACTORY_SCOPE_V1.md` | **CANONICAL** | Read by `validate_project_context.py` (canonical scope contract identity check). |
| `AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` | **CANONICAL** | Referenced by `CURRENT_SESSION_STATE.yaml.audit_evidence_contract`; defines the evidence-only-branch/PR pattern. |
| `CER_SESSION_CONTINUITY_CONTRACT_V1.md` | **CANONICAL** | Read directly by RC-08 (`resume_contract` target). |
| `CER_TARGET_SHA_EXECUTION_CONTRACT_V1.md` | **CANONICAL** | Read directly by RC-08 (`execution_sha == target_sha` check). |
| `HOTL_FAILURE_ANALYSIS_LOOP_V1.md` | **CANONICAL** | Referenced by `CURRENT_SESSION_STATE.yaml.hotl_rule`; the 3-cycle RCA rule actually followed this session (LSN-0001, LSN-0002). |
| `LESSONS_LEARNED_2026-08-20_CONTEXT_BOUNDARY.md` | **CANONICAL** | In `validate_project_context.py`'s `BOUNDARY_REFERENCE_FILES` allowlist. |
| `CER_CONTEXT_CONTRACT.md` | **CANONICAL** | Defines CER itself (Gap/Method/Risk/Evidence/Regression/Learning) — the conceptual root the runtime implements. |
| `OPTIMIZATION_BENCHMARK_CONTRACT_V1.md` | **CANONICAL** | Governs `src/opro*.py` / `scripts/opro_baseline.py` benchmark behavior. |
| `OPTIMIZATION_METHOD_CONTROL_V1.md` | **CANONICAL** | Governs which optimization methods (OPRO vs GEPA) are permitted; GEPA remains forbidden per this doc. |
| `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` | **CANONICAL** | States the active architecture direction (domain-agnostic engineering platform; provenance as generic evidence) and the implementation sequence `Factory Kernel GREEN → RE Domain Pack → ingestion → parsing → hybrid retrieval → …`. Recovered to the trunk 2026-08-25: it existed only on four unmerged branches, so the trunk carried no statement of its own refactor direction. |
| `CER_CI_PR_EXECUTION_LESSONS_2026-08-20.md` | **CANONICAL** | Cited by name in `scripts/validate_project_context.py` and `tests/test_project_context_guard.py`. Recovered to the trunk 2026-08-25 — those citations were dangling, pointing at a file that existed only on unmerged branches. Establishes the rule that historical CI success is never reusable after a new commit. |
| `RESUME_CONTRACT_V1.md` | **SUPERSEDED** by `CER_SESSION_CONTINUITY_CONTRACT_V1.md` | Both are "v1.1", same purpose (cross-session resume). Code only ever reads the Continuity Contract; this one is not referenced anywhere. Recommend keeping as history, not deleting. |
| `CER_ARCHITECTURE_CONTRACT_V1.md` | **NEEDS REVIEW** | States *"Canonical source: Git repository `main`"* — written before the `p0/opro-baseline` divergence. The architecture it describes is still accurate, but the branch pointer is stale. Should be corrected once the main/p0 branch reconciliation (structural refactor Phase 3) is decided. |
| `CER_SESSION_CLOSURE_2026-08-14.md` | **HISTORICAL** | Session-close record, 08-14. |
| `CER_SESSION_CLOSURE_2026-08-18_META_AUDIT.md` | **HISTORICAL** | Session-close record, 08-18. |
| `CER_SESSION_CLOSURE_2026-08-18_OPTIMIZATION_LESSONS.md` | **HISTORICAL** | Session-close record, 08-18. |
| `CER_SESSION_CLOSURE_2026-08-18_SESSION_CONTINUITY.md` | **HISTORICAL** | Session-close record, 08-18. |
| `CER_OPRO_GEPA_LESSONS_2026-08-18.md` | **HISTORICAL** | Lessons captured 08-18; content now reflected in `OPTIMIZATION_METHOD_CONTROL_V1.md`. |
| `EVIDENCE_EXECUTION_ARCHITECTURE_RCA_2026-08-18.md` | **HISTORICAL** | RCA record, 08-18. |
| `EVIDENCE_MANIFEST_2026-08-18_RUN-32126799804.yaml` | **HISTORICAL** | Frozen evidence manifest for one specific past run. |

## Notes
- Files quarantined from the Investment/M1B/M2 contamination episode (`M1B_*`, `M2_*`, `CER_M1B_LESSONS_*`) are intentionally absent from this tree — they are still enumerated in `scripts/validate_project_context.py`'s `FORBIDDEN_CANONICAL_PATHS` as a permanent guard against their reintroduction. See `11_Audit/REPOSITORY_CONTEXT_CONTAMINATION_2026-08-20.md`.
- This index itself should be updated whenever a governance doc is added, superseded, or its enforcement status changes — otherwise it will drift the same way the documents it describes did.
