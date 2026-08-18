# AgentFactory External Audit — Verification Checklist

**Audit target:** OPRO baseline freeze  
**Evidence baseline:** `20a54b92aad0857f75c6200d984b13098c6f4927`  
**Native run:** `31821110548`  
**Artifact:** `9226960041`  
**Artifact SHA256:** `6ec70c288a7582e76a7c1c77e7af7a0e8b45463b6e40cea033e36f2f43780525`

## 0. Chain-of-custody gate

- [ ] Record auditor date/time and timezone.
- [ ] Record repository URL and branch.
- [ ] Record audited commit SHA.
- [ ] Record native workflow run ID.
- [ ] Verify run head SHA equals audited commit SHA.
- [ ] Record artifact ID and digest.
- [ ] Preserve a copy/reference of the evidence artifact.

**Gate:** FAIL if commit/run identity cannot be reconciled.

## 1. Source and contract verification

- [ ] Verify Git is canonical source of truth.
- [ ] Verify CER Architecture Contract is present.
- [ ] Verify CER decision semantics: PASS / REVIEW / CHANGE / BLOCK.
- [ ] Verify BLOCK is fail-closed.
- [ ] Verify WorkflowRun supports retry/loop semantics.
- [ ] Verify benchmark and regression are versioned.

**Gate:** FAIL if the implementation baseline cannot be mapped to the contract.

## 2. Factory Demo verification

- [ ] Locate exact CI command.
- [ ] Verify command ran on audited commit.
- [ ] Verify exit status is successful.
- [ ] Verify PASS scenario.
- [ ] Verify REVIEW scenario reaches required human-decision path.
- [ ] Verify BLOCK scenario remains blocked.

**Expected disposition:** PASS.

## 3. Deterministic Harness verification

- [ ] Verify case count = 10.
- [ ] Verify passed = 10.
- [ ] Verify failed = 0.
- [ ] Verify `green=true`.
- [ ] Verify retry-loop expected state/result is represented correctly.
- [ ] Verify no protected case is silently skipped.

**Expected disposition:** 10/10 PASS.

## 4. OPRO baseline verification

- [ ] Record benchmark ID/version.
- [ ] Record optimizer identity/version.
- [ ] Record run ID.
- [ ] Record baseline score.
- [ ] Record best score.
- [ ] Independently calculate `best - baseline`.
- [ ] Verify regression = PASS.
- [ ] Verify promotion_status = CANDIDATE.
- [ ] Search for evidence of promotion and confirm none exists.

**Expected:** baseline `0.7777777777777777`; best `0.8888888888888888`; regression `PASS`; status `CANDIDATE`.

## 5. Pytest verification

- [ ] Locate exact pytest command.
- [ ] Verify exit status = 0.
- [ ] Verify failed = 0.
- [ ] Record total passed tests.

**Expected:** `29 passed`, `0 failed`.

## 6. Machine evidence verification

- [ ] Verify artifact exists and is not expired.
- [ ] Verify artifact ID.
- [ ] Verify artifact digest.
- [ ] Download/inspect artifact where permitted.
- [ ] Verify artifact references the audited commit/run.
- [ ] Verify Factory Demo output exists.
- [ ] Verify Harness output exists.
- [ ] Verify OPRO output exists.

## 7. Scope and prohibited-change verification

- [ ] Compare audited baseline with its predecessor.
- [ ] Confirm stale assertion was the intended test change.
- [ ] Confirm no GEPA implementation was introduced.
- [ ] Confirm no RE Domain implementation was introduced.
- [ ] Confirm no OPRO promotion was introduced.
- [ ] Confirm audit-document commits are not being treated as implementation-baseline changes.

## 8. Evidence quality classification

For each claim, classify evidence:

- E0 = narrative only
- E1 = static source evidence
- E2 = manual/local execution
- E3 = native CI execution
- E4 = native CI + machine artifact + digest + reproducible procedure

Freeze-critical claims must be E3+.

## 9. Final auditor worksheet

| Domain | Result | Evidence level | Finding ID |
|---|---|---|---|
| Chain of custody | | | |
| Contract compliance | | | |
| Factory Demo | | | |
| Deterministic Harness | | | |
| OPRO baseline | | | |
| Pytest | | | |
| Machine evidence | | | |
| Scope control | | | |
| Reproducibility | | | |

## 10. Final decision

### ACCEPTED
All freeze-critical gates pass and no contradictory evidence exists.

### ACCEPTED_WITH_FINDINGS
All freeze-critical gates pass, but one or more non-blocking evidence/process findings remain.

### REJECTED
Any hard-fail gate fails, evidence is contradictory, or the audited baseline cannot be reproduced/identified.

**Important:** An auditor must never upgrade E0 documentation into execution evidence merely because the document says that execution occurred.
