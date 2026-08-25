# Governance Documents Index
**Purpose:** so a new session can tell in under a minute which of the 26 documents in `docs/governance/` are the live, actively-enforced contracts versus historical record. Nothing below was deleted — this is a status index, not a cleanup.

Status legend: **CANONICAL** (actively read/enforced by code, or the current live contract) · **HISTORICAL** (valid record of a past session, not enforced) · **SUPERSEDED** (replaced by a newer canonical doc, kept for history) · **NEEDS REVIEW** (stale reference found)

| Document | Status | Why |
|---|---|---|
| `CURRENT_SESSION_STATE.yaml` | **CANONICAL** | The live state pointer. Read by `validate_project_context.py` and `validate_session_resume.py` on every run. |
| `NEXT_SESSION_HANDOFF_2026-08-18.md` | **CANONICAL** | Read by RC-03..RC-07 (identity/baseline/constraint checks). Contains the structured YAML front-matter added 2026-08-24. |
| `AGENT_FACTORY_SCOPE_V1.md` | **CANONICAL** | Read by `validate_project_context.py` (canonical scope contract identity check). |
| `AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` | **CANONICAL** | Referenced by `CURRENT_SESSION_STATE.yaml.audit_evidence_contract`; defines the evidence-only-branch/PR pattern. **Now actually enforced** — `scripts/evidence_gate.py` validates the execution-evidence records and `scripts/verify_artifact_sha256.py` performs the independent digest check this contract requires. Until 2026-08-25 the trunk declared it with no implementation at all (OPEN_DECISIONS D-09). |
| `CER_SESSION_CONTINUITY_CONTRACT_V1.md` | **CANONICAL** | Read directly by RC-08 (`resume_contract` target). |
| `CER_TARGET_SHA_EXECUTION_CONTRACT_V1.md` | **CANONICAL** | Read directly by RC-08 (`execution_sha == target_sha` check). |
| `HOTL_FAILURE_ANALYSIS_LOOP_V1.md` | **CANONICAL** | Referenced by `CURRENT_SESSION_STATE.yaml.hotl_rule`; the 3-cycle RCA rule actually followed this session (LSN-0001, LSN-0002). |
| `LESSONS_LEARNED_2026-08-20_CONTEXT_BOUNDARY.md` | **CANONICAL** | In `validate_project_context.py`'s `BOUNDARY_REFERENCE_FILES` allowlist. |
| `CER_CONTEXT_CONTRACT.md` | **CANONICAL** | Defines CER itself (Gap/Method/Risk/Evidence/Regression/Learning) — the conceptual root the runtime implements. |
| `OPTIMIZATION_BENCHMARK_CONTRACT_V1.md` | **CANONICAL** | Governs `src/opro*.py` / `scripts/opro_baseline.py` benchmark behavior. |
| `OPTIMIZATION_METHOD_CONTROL_V1.md` | **CANONICAL** | Governs which optimization methods (OPRO vs GEPA) are permitted; GEPA remains forbidden per this doc. |
| `OPEN_DECISIONS_2026-08-25.md` | **CANONICAL** | The live decision register: every item that needs a person, with what was verified and what it costs to be wrong. Read this before planning a session; retire each entry as it is decided. All nine entries were resolved 2026-08-25 and are retained there as the record of why. Add new decisions to this register rather than starting a fresh one. |
| `GENERIC_ENGINEERING_EVIDENCE_CONTRACT_V1.md` | **CANONICAL** | Defines the domain-independent evidence envelope the Kernel owns (identity → provenance → execution → artifact integrity → validation → governance). Implemented by `src/engineering_evidence.py` and enforced by `tests/test_engineering_evidence_contract.py`. Recovered to the trunk 2026-08-25 (OPEN_DECISIONS D-04). |
| `GENERIC_ENGINEERING_EVIDENCE_RCA_2026-08-20.md` | **HISTORICAL** | RCA behind the contract above. Recovered alongside it 2026-08-25. |
| `GENERIC_ENGINEERING_EVIDENCE_RUNTIME_INTEGRATION_STATUS.md` | **HISTORICAL** | Runtime integration status captured when the contract was written. Recovered alongside it 2026-08-25; re-verify before treating any status line as current. |
| `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` | **CANONICAL** | States the active architecture direction (domain-agnostic engineering platform; provenance as generic evidence) and the implementation sequence `Factory Kernel GREEN → RE Domain Pack → ingestion → parsing → hybrid retrieval → …`. Recovered to the trunk 2026-08-25: it existed only on four unmerged branches, so the trunk carried no statement of its own refactor direction. |
| `CER_CI_PR_EXECUTION_LESSONS_2026-08-20.md` | **CANONICAL** | Cited by name in `scripts/validate_project_context.py` and `tests/test_project_context_guard.py`. Recovered to the trunk 2026-08-25 — those citations were dangling, pointing at a file that existed only on unmerged branches. Establishes the rule that historical CI success is never reusable after a new commit. |
| `RESUME_CONTRACT_V1.md` | **SUPERSEDED** by `CER_SESSION_CONTINUITY_CONTRACT_V1.md` | Both are "v1.1", same purpose (cross-session resume). Code only ever reads the Continuity Contract; this one is referenced nowhere. Settled 2026-08-25 (D-07): kept as history, and its own header — which read *"Active governance contract"* — corrected, since two documents each claiming to be the live contract is how this drift starts. |
| `CER_ARCHITECTURE_CONTRACT_V1.md` | **CANONICAL** | States *"Canonical source: Git repository `main`"*. This was flagged NEEDS REVIEW while the trunk lived on `p0/opro-baseline`; the 2026-08-25 reconciliation moved the trunk to `main`, so the pointer is now accurate and the flag is cleared. The document was right the whole time — the repository had drifted away from it, not the reverse. |
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
