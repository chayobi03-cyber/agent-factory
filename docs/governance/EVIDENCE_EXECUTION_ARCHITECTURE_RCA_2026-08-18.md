# Evidence Execution Architecture RCA — 2026-08-18

## Status

**Permanent governance rule.** This RCA supersedes repeated session-level attempts to solve current-SHA evidence failures as isolated CI/validator defects.

## Executive finding

AgentFactory does not yet have one canonical, closed-loop execution path that guarantees:

```text
immutable target SHA
  = intended execution SHA
  = runtime checkout SHA
  = evidence package SHA
```

and makes the resulting run/job/log/artifact/digest evidence independently retrievable.

This is the root cause behind repeated CER continuity / Audit Evidence Chain remediation sessions.

## Observed failure pattern

1. Session state and handoff correctly identify a target/checkpoint.
2. Git branch ancestry can be verified.
3. A CI execution is attempted through a PR/evidence branch.
4. GitHub Actions may execute a synthetic PR merge SHA rather than the intended target head SHA.
5. The connector/tooling does not provide a reliable canonical discovery path for the required push-triggered exact-SHA execution.
6. Runtime failures or missing artifacts prevent RC-01..RC-08 from being evaluated from one bound evidence package.
7. The session remains `RESUME_REVIEW_REQUIRED` / `INCONCLUSIVE` and the same problem is revisited in a later session.

## Root causes

### RCA-01 — No canonical exact-SHA execution path

The governance contract requires current-SHA primary execution evidence, but the workflow does not yet provide a deterministic execution controller whose target is an immutable SHA and whose checkout identity is explicitly asserted.

**Severity:** Critical.

### RCA-02 — PR merge execution is not equivalent to target-SHA execution

A pull-request workflow can checkout `refs/remotes/pull/<n>/merge`, producing a synthetic `github.sha`. Recording `pull_request.head.sha` is necessary but does not make the merge checkout itself equivalent to immutable target execution.

**Severity:** Critical.

### RCA-03 — Evidence retrieval capability is weaker than governance requirements

The governance model requires run → job → log → artifact → digest retrieval for the exact target SHA. Available GitHub tooling does not provide a sufficiently deterministic discovery/retrieval contract for every required push-triggered execution path.

**Severity:** Critical.

### RCA-04 — Session state and runtime evidence are insufficiently separated

`CURRENT_SESSION_STATE` is intended to be a continuation pointer, while execution proof belongs in an evidence manifest. Mixing historical evidence pointers into session state creates stale-evidence risk across sessions.

**Severity:** High.

### RCA-05 — Validator function tests did not initially cover the executable entrypoint

The RC validator contained a runtime `TypeError` that prevented RC-01..RC-08 from running in CI. Function-level regression coverage was insufficient to guarantee CLI execution safety.

**Severity:** High.

## Permanent rules

1. **Exact target identity is an execution invariant, not documentation.**
2. `state`, `handoff`, and Git ancestry are necessary context but never substitute for runtime evidence.
3. Canonical execution evidence MUST bind target SHA, execution ref, checkout SHA, run ID, attempt, job ID, raw logs, artifact ID, and digest.
4. `TARGET_SHA = EXECUTION_HEAD_SHA = CHECKOUT_SHA` MUST hold for canonical immutable-target evidence. A synthetic PR merge SHA is metadata, not the canonical target identity.
5. RC-01..RC-08 MUST be evaluated from one internally consistent evidence package; evidence from different SHA/run identities MUST NOT be mixed.
6. Historical successful Actions runs MUST NOT satisfy a current-SHA execution requirement.
7. Missing or unqueryable runtime evidence is `INCONCLUSIVE` / `RESUME_REVIEW_REQUIRED`, never PASS.
8. Validator changes require function-level, CLI-entrypoint, and CI execution regression coverage.
9. CI artifacts MUST be emitted with execution identity and raw outputs even on gate failure where technically possible.
10. `RESUME_ALLOWED`, `AUDIT_EVIDENCE_CHAIN=GREEN`, OPRO promotion, GEPA implementation, and M1-B progression remain separate gates.
11. Until Evidence Execution Architecture is remediated and verified, M1-B, OPRO promotion, and GEPA implementation remain blocked.

## Required architecture

```text
Target SHA
   |
   v
Evidence Execution Controller
   |
   +--> deterministic checkout
   +--> runtime identity assertion
   +--> workflow/run capture
   +--> job/step/log capture
   +--> artifact capture
   +--> independent digest verification
   |
   v
Evidence Manifest
   |
   +--> RC-01..RC-08
   +--> Factory Demo
   +--> Deterministic Harness
   +--> OPRO Baseline E2E
   +--> pytest
   |
   v
Audit Evidence Chain
   |
   v
RESUME_ALLOWED
```

## Required identity invariant

```text
TARGET_SHA
  = INTENDED_HEAD_SHA
  = EXECUTION_HEAD_SHA
  = CHECKOUT_SHA
```

If the invariant cannot be proven, canonical evidence is invalid.

## Remediation sequence

`VERIFY → DIAGNOSE → regression seed → targeted remediation → evidence → classify → CER CHECK → state/handoff update → Git commit`

Do not solve recurrence by repeatedly rerunning the same PR workflow without first repairing the execution/evidence architecture.

## Exit criteria for this RCA

The RCA is considered remediated only when a machine-verifiable evidence package can be produced for an arbitrary immutable target SHA and independently proves execution identity, result, artifact identity, and digest without relying on prior chat history.
