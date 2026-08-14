# AgentFactory Internal Audit — Formal Rating Matrix

**Audit date:** 2026-08-15  
**Repository:** `chayobi03-cyber/agent-factory`  
**Branch under review:** `p0/opro-baseline`  
**Audited implementation baseline:** `20a54b92aad0857f75c6200d984b13098c6f4927`  
**Native execution:** GitHub Actions run `31821110548`  
**Artifact:** `factory-kernel-machine-evidence` / ID `9226960041`  
**Artifact SHA256:** `6ec70c288a7582e76a7c1c77e7af7a0e8b45463b6e40cea033e36f2f43780525`

## 1. Rating scale

| Rating | Meaning | Release effect |
|---|---|---|
| GREEN | Requirement directly evidenced and no material finding | May pass gate |
| GREEN-W | Evidence sufficient, but documentation/automation weakness exists | May pass with tracked improvement |
| AMBER | Material gap; workaround or compensating evidence exists | Cannot claim unrestricted freeze if gate-critical |
| RED | Failed requirement or contradictory evidence | Blocks release/freeze |
| N/A | Not applicable to this baseline | No effect |

## 2. Evidence strength

| Level | Definition |
|---|---|
| E0 | Documentation/claim only |
| E1 | Source/static inspection |
| E2 | Local/manual execution evidence |
| E3 | Native CI machine execution with immutable commit/run identity |
| E4 | Native CI + machine artifact + digest + independently reproducible procedure |

**Freeze-critical controls should target E3 or higher.**

## 3. Formal control matrix

| ID | Control | Acceptance test | Evidence | Rating | Gate |
|---|---|---|---|---|---|
| IA-001 | Baseline identity | audited commit is immutable and identified | commit `20a54b92...` | GREEN / E3 | Required |
| IA-002 | Factory Demo | all scenarios execute successfully | native Actions stdout | GREEN / E3 | Required |
| IA-003 | Deterministic Harness | 10/10 pass and `green=true` | `factory-harness.stdout.json` | GREEN / E3 | Required |
| IA-004 | Retry semantics | retry-loop reaches `REJECT_EXECUTION/RETRYING` as expected | harness output | GREEN / E3 | Required |
| IA-005 | OPRO baseline | baseline score recorded | OPRO stdout | GREEN / E3 | Required |
| IA-006 | OPRO best score | best score recorded and exceeds baseline | OPRO stdout | GREEN / E3 | Required |
| IA-007 | OPRO regression | regression=`PASS` | OPRO stdout | GREEN / E3 | Required |
| IA-008 | Promotion boundary | `promotion_status=CANDIDATE` and no promotion performed | OPRO stdout / workflow | GREEN / E3 | Required |
| IA-009 | Pytest | zero failed tests | `29 passed` | GREEN / E3 | Required |
| IA-010 | Machine evidence | artifact exists and digest is available | artifact ID + SHA256 | GREEN / E4 | Required |
| IA-011 | Evidence distinction | execution claims trace to machine evidence | run/artifact linkage | GREEN / E4 | Required |
| IA-012 | CER gate semantics | PASS/REVIEW/CHANGE/BLOCK semantics are contract-aligned | CER contract + tests | GREEN / E1-E3 | Required |
| IA-013 | Domain isolation | RE domain implementation is not introduced as part of OPRO freeze | commit diff | GREEN / E3 | Required |
| IA-014 | GEPA boundary | GEPA implementation is absent | commit diff | GREEN / E3 | Required |
| IA-015 | External audit reproducibility | auditor can resolve exact baseline and evidence | audit pack | GREEN-W / E2 | Improvement |

## 4. Hard-fail rules

Any of the following is automatically RED:

1. audited commit cannot be resolved;
2. native run does not correspond to audited commit;
3. Factory Demo failure;
4. harness `green=false` or any protected case fails;
5. OPRO regression != `PASS`;
6. pytest has any failure;
7. machine evidence artifact missing;
8. artifact digest cannot be verified;
9. evidence relies only on documentation where execution evidence is required;
10. OPRO promotion is performed while status is required to remain `CANDIDATE`;
11. GEPA or RE Domain implementation is introduced before the freeze gate is closed.

## 5. Current disposition

**INTERNAL AUDIT: GREEN**

Freeze-critical controls IA-001 through IA-014 are GREEN. IA-015 is GREEN-W because the evidence package is sufficient for review but should be strengthened with a fully machine-generated Evidence Pack manifest containing explicit per-command exit codes and captured stderr.

**OPRO baseline freeze: ACCEPTED.**

**OPRO promotion: NOT ACCEPTED / NOT PERFORMED.**

**GEPA: BLOCKED by scope.**  
**RE Domain: BLOCKED by scope.**

## 6. Required follow-up

- Generate per-command execution records with explicit `exit_code`, `stdout`, `stderr`, timestamp, and commit SHA.
- Add independent artifact verification procedure.
- Preserve the audited baseline SHA even if audit documentation receives later commits.
