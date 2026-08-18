# Internal Audit Re-Rating — Audit Evidence Chain Remediation

**Audit date:** 2026-08-18  
**Repository:** `chayobi03-cyber/agent-factory`  
**System-under-audit baseline:** `20a54b92aad0857f75c6200d984b13098c6f4927`  
**Historical native run:** `31821110548`  
**Remediation branch:** `audit/evidence-chain-remediation`

## Control re-rating

| ID | Control | Previous | 2026-08-18 status | Evidence requirement | Freeze impact |
|---|---|---|---|---|---|
| IA-001 | Baseline identity | GREEN | GREEN | Commit resolves to audited baseline | None |
| IA-002 | Factory Demo | GREEN/E3 | HOLD pending new E4 pack | Per-command captured execution evidence | Blocks |
| IA-003 | Deterministic Harness | GREEN/E3 | HOLD pending new E4 pack | Exit code + stdout/stderr + provenance | Blocks |
| IA-004 | Retry semantics | GREEN/E3 | HOLD pending new E4 pack | Captured harness record | Blocks |
| IA-005 | OPRO baseline | GREEN/E3 | HOLD pending new E4 pack | Captured OPRO record | Blocks |
| IA-006 | OPRO best score | GREEN/E3 | HOLD pending new E4 pack | Observed value in captured record | Blocks |
| IA-007 | OPRO regression | GREEN/E3 | HOLD pending new E4 pack | Captured regression result | Blocks |
| IA-008 | Promotion boundary | GREEN/E3 | HOLD pending evidence gate | `CANDIDATE` + no promotion | Blocks |
| IA-009 | Pytest | GREEN/E3 | HOLD pending new E4 pack | Captured pytest record | Blocks |
| IA-010 | Machine evidence | GREEN/E4 | HOLD until new artifact chain closes | Artifact digest + metadata | Blocks |
| IA-011 | Evidence distinction | GREEN/E4 | HOLD until manifest is independently resolved | expected/observed/verified/decision | Blocks |
| IA-012 | CER gate semantics | GREEN | GREEN-W | Static contract remains intact; execution gate is now stricter | No independent freeze by itself |
| IA-013 | Domain isolation | GREEN/E3 | GREEN | Commit scope remains unchanged | None |
| IA-014 | GEPA boundary | GREEN/E3 | GREEN | Commit scope remains unchanged | None |
| IA-015 | External audit reproducibility | GREEN-W | HOLD | External/Cold auditor must resolve same evidence chain | Blocks |

## Hard decision rule

Until IA-002 through IA-011 and IA-015 are independently resolved from the new machine evidence chain:

- **Internal Audit:** AMBER / PROVISIONAL
- **Evidence Gate:** BLOCKED
- **OPRO baseline freeze:** BLOCKED
- **OPRO promotion:** BLOCKED
- **GEPA:** BLOCKED
- **RE Domain:** BLOCKED

A historical GREEN rating is not silently rewritten; this re-rating supersedes it for the current release decision because the Meta Audit demonstrated insufficient primary evidence for unrestricted PASS claims.

## Re-entry criteria

Internal Audit may move to GREEN only when:

1. the new workflow run head SHA is the expected audited source revision;
2. all required execution records exist;
3. every execution record has exit code, stdout, stderr, and matching hashes;
4. raw evidence artifact and metadata are resolvable;
5. artifact digest is independently verified;
6. expected / observed / verified / decision values are consistent;
7. External/Cold Audit reaches ACCEPTED;
8. auditor sign-off is recorded.
