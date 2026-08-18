# AgentFactory External Auditor Questionnaire

**Audit target:** OPRO baseline freeze  
**Audited implementation commit:** `20a54b92aad0857f75c6200d984b13098c6f4927`  
**Native run:** `31821110548`

## Auditor instructions

Do not accept repository documentation as proof of execution by itself. For every execution claim, require a machine-generated execution record or CI run linked to the exact audited commit.

Record one of: `PASS`, `PASS-WITH-FINDING`, `FAIL`, `N/A`.

## A. Identity and scope

| ID | Question | Required evidence | Result | Auditor notes |
|---|---|---|---|---|
| EXT-001 | Is the audited commit explicitly identified? | Git commit SHA | | |
| EXT-002 | Does the native run point to the same commit? | Actions run metadata | | |
| EXT-003 | Is the audit scope limited to OPRO baseline freeze? | Audit pack | | |
| EXT-004 | Are GEPA and RE Domain explicitly outside scope? | Scope declaration + diff | | |

## B. Execution integrity

| ID | Question | Required evidence | Result | Auditor notes |
|---|---|---|---|---|
| EXT-005 | Was Factory Demo actually executed? | CI command + stdout + status | | |
| EXT-006 | Did Factory Demo return PASS? | Machine output | | |
| EXT-007 | Was deterministic harness actually executed? | CI output | | |
| EXT-008 | Were all 10 protected cases passed? | Harness result | | |
| EXT-009 | Is `green=true` machine-generated? | Harness result | | |
| EXT-010 | Was pytest executed? | CI step | | |
| EXT-011 | Are there zero failed tests? | pytest output | | |

## C. OPRO integrity

| ID | Question | Required evidence | Result | Auditor notes |
|---|---|---|---|---|
| EXT-012 | Is the benchmark version identified? | OPRO output | | |
| EXT-013 | Is the baseline score reproducible? | OPRO output + procedure | | |
| EXT-014 | Is the best score reproducible? | OPRO output + procedure | | |
| EXT-015 | Is best score >= baseline score? | Calculated comparison | | |
| EXT-016 | Is regression explicitly PASS? | OPRO output | | |
| EXT-017 | Is promotion status CANDIDATE? | OPRO output | | |
| EXT-018 | Was any promotion actually performed? | Git diff / workflow / release evidence | | |

## D. Machine evidence

| ID | Question | Required evidence | Result | Auditor notes |
|---|---|---|---|---|
| EXT-019 | Does the evidence artifact exist? | Artifact ID | | |
| EXT-020 | Is artifact SHA256 recorded? | Artifact digest | | |
| EXT-021 | Does artifact identity map to the audited commit? | Artifact metadata | | |
| EXT-022 | Can artifact contents be inspected? | Artifact ZIP | | |
| EXT-023 | Are execution claims distinguishable from documentation claims? | Evidence chain | | |

## E. Governance / CER

| ID | Question | Required evidence | Result | Auditor notes |
|---|---|---|---|---|
| EXT-024 | Are CER PASS/REVIEW/CHANGE/BLOCK semantics defined? | Architecture Contract | | |
| EXT-025 | Is BLOCK fail-closed? | Contract + test evidence | | |
| EXT-026 | Are retry paths governed rather than bypassing gates? | Contract + harness | | |
| EXT-027 | Is the baseline frozen independently of later audit-document commits? | Audit pack | | |

## F. Boundary challenge

The auditor should explicitly attempt to falsify the freeze claim:

1. Run the regression against a different commit and verify that it is not accepted as evidence for the audited baseline.
2. Check whether any artifact claims success without a matching native run.
3. Search for any promotion/release action after the OPRO candidate result.
4. Search the diff for GEPA implementation or RE Domain implementation.
5. Verify that the retry-loop test does not merely assert a stale RED expectation.
6. Verify that a documentation-only execution claim is rejected.

## Auditor conclusion

Select exactly one:

- **ACCEPTED** — all freeze-critical questions pass and no material contradiction exists.
- **ACCEPTED_WITH_FINDINGS** — freeze evidence is valid, but non-blocking audit findings remain.
- **REJECTED** — one or more hard-fail controls fail or evidence is contradictory.

## Mandatory rejection triggers

- audited commit/run mismatch;
- missing native execution evidence;
- Factory Demo failure;
- harness not 10/10 GREEN;
- OPRO regression failure;
- pytest failure;
- missing/invalid machine evidence;
- undocumented promotion;
- evidence presented solely as narrative/documentation;
- scope violation involving premature GEPA or RE implementation.
