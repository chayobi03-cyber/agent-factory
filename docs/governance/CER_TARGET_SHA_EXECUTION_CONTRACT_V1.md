# CER Target-SHA Execution Binding Contract V1

## Purpose

Bind every governed CI execution to one machine-verifiable repository SHA. The execution SHA is the commit actually checked out and tested; it is not inferred from a synthetic pull-request merge SHA.

## Execution identity invariant

For `Factory Kernel Regression`:

```text
repository == chayobi03-cyber/agent-factory
branch/ref == declared source branch/ref
execution_sha == target_sha
checked_out_sha == target_sha
```

Where the workflow is triggered by `pull_request`, `target_sha` MUST be `github.event.pull_request.head.sha`. `github.sha` MAY be a synthetic merge SHA and MUST NOT be used as the execution identity for resume evidence.

For non-PR execution, `target_sha` MUST be `github.sha`.

## Checkout rule

The workflow MUST checkout exactly `target_sha` with full history (`fetch-depth: 0`) so checkpoint ancestry can be verified. Detached HEAD is acceptable; branch identity is resolved from GitHub Actions metadata when Git cannot report a local branch.

## Environment contract

The workflow MUST expose:

- `CER_TARGET_SHA` — exact execution target SHA;
- `CER_EXECUTION_IDENTITY_REQUIRED=1` — fail-closed marker for CI binding.

The CI identity artifact MUST record `github_sha`, `target_sha`, `checked_out_sha`, `head_ref`, and a boolean `target_sha_match`.

## Harness binding

`run_harness.py` MUST resolve the execution SHA from `CER_TARGET_SHA` when present, verify it equals the checked-out `git rev-parse HEAD`, and bind that SHA into the harness report and runtime `repository_commit`.

## OPRO binding

`opro_baseline.py` MUST resolve the execution SHA from `CER_TARGET_SHA` when present, verify it equals the checked-out `git rev-parse HEAD`, and bind that SHA into the runtime snapshot/run execution evidence and machine-readable output. Synthetic or placeholder commit identifiers are forbidden.

## Resume validator binding

`validate_session_resume.py` MUST preserve the existing RC-01..RC-08 semantics and additionally enforce `CER_TARGET_SHA == git rev-parse HEAD` whenever `CER_TARGET_SHA` is supplied. Under `CER_EXECUTION_IDENTITY_REQUIRED=1`, missing or mismatched `CER_TARGET_SHA` is `RESUME_BLOCKED`.

The target-SHA binding is part of the RC-02 execution identity precondition; it does not create a ninth RC.

## Failure semantics

Any target-SHA mismatch, missing required CI binding, or checkout mismatch is a hard identity failure. It MUST NOT be converted to `REVIEW_REQUIRED` or PASS.

## Evidence chain

A valid machine evidence package must be traceable as:

```text
run → job → log → artifact → digest → target SHA → RC-01..RC-08
```

All downstream evidence is invalid for resume purposes when the target SHA identity cannot be reconciled.
