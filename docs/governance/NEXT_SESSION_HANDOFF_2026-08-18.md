# AgentFactory Next Session Handoff — 2026-08-18

## Objective

Transition from repeated CER continuity retries to **Evidence Execution Architecture remediation**. The immediate goal is to create one deterministic, machine-verifiable execution/evidence path for an immutable target SHA. Do not advance M1-B, OPRO promotion, or GEPA implementation until the repaired path produces valid primary evidence.

## Canonical state

Read first, in order:

1. `docs/governance/CURRENT_SESSION_STATE.yaml`
2. `docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md`
3. `schemas/session_state.schema.yaml`
4. `docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md`
5. `docs/governance/AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md`
6. `docs/governance/EVIDENCE_EXECUTION_ARCHITECTURE_RCA_2026-08-18.md`
7. `docs/governance/CER_OPRO_GEPA_LESSONS_2026-08-18.md` when workflow improvement is needed

Do not reload the entire prior chat. Repository governance artifacts are canonical.

## Repository

- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- audited OPRO baseline SHA — **DO NOT CHANGE**: `20a54b92aad0857f75c6200d984b13098c6f4927`
- durable checkpoint anchor: `16972e2fa29496731319f088907170d93961ae48`

Resolve the actual current branch HEAD dynamically. Never use a recorded historical HEAD as current identity.

## Current gate

```text
Audit Evidence Chain = NOT_GREEN
RESUME = BLOCKED
M1-B = LOCKED
OPRO promotion = FORBIDDEN
GEPA implementation = FORBIDDEN
```

## Root-cause rule

The recurring blocker is not treated as another isolated CI failure. The repository now records the permanent RCA in:

`docs/governance/EVIDENCE_EXECUTION_ARCHITECTURE_RCA_2026-08-18.md`

The root cause is the absence of a canonical closed-loop path proving:

```text
TARGET_SHA
  = INTENDED_HEAD_SHA
  = EXECUTION_HEAD_SHA
  = CHECKOUT_SHA
```

and binding that identity to run → job → log → artifact → digest evidence that can be independently retrieved.

## Phase 0 — CER START / dynamic identity

1. Resolve current `p0/opro-baseline` HEAD using primary Git evidence.
2. Verify ancestry from checkpoint `16972e2f...`.
3. Verify audited baseline remains exactly `20a54b92...`.
4. Verify state/handoff/contract/schema identity.
5. Classify intervening commits where required.
6. Keep `RESUME_BLOCKED` unless primary evidence proves otherwise.

## Phase 1 — Evidence Execution Architecture design

Design a minimal, deterministic **Evidence Execution Controller** with these responsibilities:

1. Accept an immutable target SHA.
2. Establish deterministic checkout of that SHA rather than relying on a synthetic PR merge checkout.
3. Assert and record runtime checkout SHA.
4. Trigger/identify the intended Factory Kernel Regression execution.
5. Capture workflow/run identity, event, ref, attempt, intended head SHA, execution SHA, checkout SHA, job IDs, step conclusions, and raw logs.
6. Capture artifact IDs/names and the GitHub-reported digest where available.
7. Independently recompute artifact digest.
8. Emit one machine-verifiable Evidence Manifest.
9. Make the manifest independently retrievable without prior chat context.

Do not overbuild. Prefer the smallest reversible architecture that closes the evidence identity loop.

## Phase 2 — Evidence Manifest contract

Define a schema/contract with at least:

```yaml
schema_version:
target_sha:
intended_head_sha:
execution_sha:
checkout_sha:
repository:
branch_or_ref:
workflow:
workflow_id:
run_id:
run_attempt:event:
jobs:
  - job_id:
    name:
    conclusion:
    steps:
artifacts:
  - artifact_id:
    name:
    digest:
    independently_verified_digest:
raw_log_digests:
rc_verdicts:
  RC-01:
  RC-02:
  RC-03:
  RC-04:
  RC-05:
  RC-06:
  RC-07:
  RC-08:
overall_result:
classification:
created_at:
```

Do not declare an execution valid merely because the workflow succeeded. Identity and digest must be independently verified.

## Phase 3 — Runtime identity regression

Add deterministic witnesses for:

- exact target SHA checkout;
- `TARGET_SHA != CHECKOUT_SHA` → fail closed;
- synthetic PR merge SHA distinguished from intended head SHA;
- validator CLI entrypoint execution;
- missing run/artifact/digest → INCONCLUSIVE, never PASS;
- artifact digest mismatch → fail closed.

Regression hierarchy:

```text
unit/function
→ CLI entrypoint
→ local evidence package
→ CI execution
→ artifact/digest verification
```

## Phase 4 — Evidence execution

Use target SHA selected dynamically at session start. Do not reuse historical runs from another SHA.

Produce and preserve:

```text
target SHA
→ execution
→ run
→ job
→ log
→ artifact
→ digest
→ Evidence Manifest
→ RC-01..RC-08
```

If the required execution cannot be retrieved or identity cannot be proven, classify `INCONCLUSIVE / RESUME_REVIEW_REQUIRED` and stop.

## Phase 5 — CER gate

Rejudge RC-01..RC-08 from **one internally bound evidence package**.

Only the following condition can change resume status:

```text
all RC-01..RC-08 PASS
+ exact execution identity proven
+ required workflow stages PASS
+ artifact exists
+ digest independently verified
= RESUME_ALLOWED
```

Otherwise remain blocked.

## Phase 6 — Only after RESUME_ALLOWED

Return to the original downstream roadmap:

1. minimum sufficient financial source stack;
2. five real historical series;
3. provenance/PIT/replay/cross-source reconciliation;
4. M1-B GREEN.

## Absolute constraints

- audited OPRO baseline SHA must not change;
- GEPA implementation forbidden;
- OPRO promotion forbidden;
- RE Domain implementation forbidden;
- PASS without primary execution evidence forbidden;
- stale/historical execution evidence cannot satisfy current-SHA requirements;
- documentation/state/handoff cannot substitute for runtime evidence;
- backtest/OOS/optimization/Monte Carlo forbidden before M1-B GREEN.

## Working methodology

Use:

`VERIFY → DIAGNOSE → regression seed → minimal targeted remediation → VERIFY → evidence → classify → CER CHECK → update state/handoff → Git commit`

Do not repeatedly rerun a known-invalid execution path without changing the architecture or proving why the prior classification was wrong.

## CHECKPOINT trigger

Checkpoint after:

- architecture contract change;
- evidence schema change;
- identity assertion change;
- regression seed addition;
- execution evidence capture;
- gate status change.

## SESSION CLOSE

`Lessons Learned → Permanent Rule → Workflow Rule → Task Guidance → Regression Seed → Unresolved Issue → Current State → Next Action → Evidence references → CER CHECK → Git Commit`

## Definition of success

The next session succeeds when it produces either:

1. a verified Evidence Execution Architecture capable of proving exact-SHA execution and machine-verifiable evidence; or
2. a precise machine-verifiable blocker with the missing capability identified.

Only after that evidence path is GREEN may the workflow resume M1-B.

## Ready-to-use next-session prompt

```text
AgentFactory 다음 세션 시작.

Repository:
chayobi03-cyber/agent-factory
Branch:
p0/opro-baseline
Audited OPRO baseline SHA — DO NOT CHANGE:
20a54b92aad0857f75c6200d984b13098c6f4927

CER START

이전 대화 전체를 재로드하지 않는다.
다음 canonical context를 순서대로 읽는다:
1. docs/governance/CURRENT_SESSION_STATE.yaml
2. docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md
3. schemas/session_state.schema.yaml
4. docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md
5. docs/governance/AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md
6. docs/governance/EVIDENCE_EXECUTION_ARCHITECTURE_RCA_2026-08-18.md
7. docs/governance/CER_OPRO_GEPA_LESSONS_2026-08-18.md

PHASE 0 — DYNAMIC IDENTITY

primary Git evidence로 실제 current HEAD를 동적으로 resolve한다.
checkpoint 16972e2fa29496731319f088907170d93961ae48 ancestry를 검증한다.
audited baseline 20a54b92aad0857f75c6200d984b13098c6f4927 불변을 확인한다.
state/handoff/schema/contract identity를 확인한다.

PHASE 1 — EVIDENCE EXECUTION ARCHITECTURE

RCA를 다시 개별 CI failure로 취급하지 않는다.
목표는 immutable target SHA를 입력으로 받아 정확한 checkout과 execution identity를 보장하고,
run → job → log → artifact → digest를 하나의 machine-verifiable Evidence Manifest로 묶는 것이다.

필수 invariant:
TARGET_SHA = INTENDED_HEAD_SHA = EXECUTION_HEAD_SHA = CHECKOUT_SHA

PR synthetic merge SHA는 canonical target identity가 아니다.

PHASE 2 — MANIFEST

Evidence Manifest에 repository/ref/workflow/run/attempt/job/step/log/artifact/digest/RC-01~RC-08/result/classification을 기록한다.
GitHub digest와 independently recomputed digest를 비교한다.

PHASE 3 — REGRESSION

exact-SHA checkout mismatch
synthetic merge SHA confusion
CLI validator runtime error
missing run/artifact/digest
artifact digest mismatch
를 모두 fail-closed regression seed로 만든다.

PHASE 4 — EXECUTE

현재 resolved HEAD를 대상으로 실제 evidence execution을 수행한다.
과거 다른 SHA의 성공 run을 재사용하지 않는다.

PHASE 5 — CER GATE

하나의 evidence package에서 RC-01~RC-08을 재판정한다.

all PASS + exact execution identity + artifact + independent digest + required workflow stages PASS
→ RESUME_ALLOWED

그 외
→ INCONCLUSIVE / RESUME_REVIEW_REQUIRED
→ downstream stop

ABSOLUTE CONSTRAINTS

GEPA implementation 금지
OPRO promotion 금지
RE Domain implementation 금지
audited baseline SHA 변경 금지
PASS without primary execution evidence 금지
M1-B GREEN 전 backtest/OOS/optimization/Monte Carlo 금지

방법론:
VERIFY → DIAGNOSE → regression seed → minimal remediation → VERIFY → evidence → classify → CER CHECK → state/handoff → Git commit

목표는 작업량이 아니라 검증된 유용한 진전이며,
identity + provenance + reproducibility + auditability + fail-closed safety를 유지한다.
```
