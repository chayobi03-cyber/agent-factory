# Audit Evidence Chain CI Contract V1

## Purpose

Bind CI execution evidence to the exact commit/ref being resumed. A successful historical run is never evidence for a different commit.

## Evidence identity invariant

For every resume evidence package:

```text
repository == chayobi03-cyber/agent-factory
ref/branch == declared resume ref
head_sha == target resume SHA
workflow == Factory Kernel Regression
```

The audited OPRO baseline SHA is immutable metadata and MUST NOT be replaced by the current HEAD.

## Required evidence

A primary CI evidence package MUST contain:

1. workflow run ID;
2. workflow name and workflow file;
3. event;
4. head ref/branch;
5. head SHA;
6. run attempt/status/conclusion;
7. job and step conclusions;
8. raw RC-01..RC-08 stdout/stderr;
9. pytest result;
10. deterministic regression result;
11. OPRO baseline E2E result when applicable;
12. machine evidence artifact ID/name;
13. GitHub artifact digest;
14. independent digest verification where the artifact is downloaded;
15. evidence-to-commit binding verdict.

## Fail-closed rules

- Missing current-SHA execution evidence = `INCONCLUSIVE`, never PASS.
- SHA/ref mismatch = `INVALID_EVIDENCE` and `RESUME_BLOCKED`.
- A historical successful run for another SHA MUST NOT satisfy the current gate.
- A validator crash is a regression failure, not a successful resume result.
- Evidence publication MUST run with `if: always()` so failure diagnostics are preserved.
- Regression steps MUST NOT use `continue-on-error` when their result is part of a GREEN gate.
- Artifact publication MUST include the resume validator output and CI identity manifest.

## Evidence-only execution

When the target commit must be tested without changing that commit, create an evidence-only branch pointing exactly to the target SHA and open a non-merge PR that triggers the existing pull-request workflow. The PR MUST NOT be merged. The workflow's checkout merge ref is not itself the target SHA; therefore the run's `head_sha` and PR metadata MUST be captured and compared to the target SHA.

## Promotion boundary

`AUDIT_EVIDENCE_CHAIN=GREEN` requires both execution identity and result evidence. It does not authorize M1-B, OPRO promotion, GEPA implementation, or any other downstream action unless the separate gate permits it.

## Checkpoint

After CI evidence capture:

```text
Execute → Capture → Verify → Classify → CER CHECK → Update State/Handoff → Git Commit
```
