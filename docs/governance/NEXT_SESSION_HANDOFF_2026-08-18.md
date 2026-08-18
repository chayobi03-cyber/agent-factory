# AgentFactory Next Session Handoff — 2026-08-18

## Objective

Resume governed work without relying on prior chat history as canonical state. First repair and verify continuity identity/evidence, then continue the financial-information M1-B gate.

## Canonical state

Read first, in order:

1. `docs/governance/CURRENT_SESSION_STATE.yaml`
2. `docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md`
3. `schemas/session_state.schema.yaml`
4. `docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md`
5. `docs/governance/AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md`
6. `docs/governance/CER_OPRO_GEPA_LESSONS_2026-08-18.md` when performing lesson-based workflow improvement

## Repository

- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- audited OPRO baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927`
- durable checkpoint anchor: `16972e2fa29496731319f088907170d93961ae48`
- current branch HEAD after this session's governance/evidence remediation: `3cb02f92dfb9ef7e750c66530192c3807c65d203`

## Resume Contract

A new session MUST NOT execute `next_action` until RC-01..RC-08 are verified against the current branch/HEAD.

```text
state → Git identity/ancestry → handoff → audited baseline → gate/constraints → required context/evidence
```

Any identity contradiction is `RESUME_BLOCKED`. Missing runtime evidence or environment ambiguity is `INCONCLUSIVE`, not PASS.

## Current evidence attempt and lesson

An evidence-only branch `evidence/resume-0e0c6616` was created exactly at target SHA `0e0c66160f0ea005d0c3c61d88911834af0660bd` and PR #2 was opened only to trigger the existing pull-request workflow without changing that commit. The PR was closed without merge after evidence capture.

The resulting workflow run was:

```text
run_id: 32124843431
workflow: Factory Kernel Regression
workflow_id: 334216760
event: pull_request
head branch: evidence/resume-0e0c6616
head SHA: 0e0c66160f0ea005d0c3c61d88911834af0660bd
job: kernel-regression / 95672989467
```

The execution proved the target-SHA workflow path works, but RC-01..RC-08 did not execute to a verdict because the validator crashed:

```text
TypeError: check() missing 1 required positional argument: 'ok'
```

Consequences:

- RC-01..RC-08 = NOT VERIFIED
- pytest/regression = skipped
- artifact digest = unavailable
- Audit Evidence Chain = NOT_GREEN
- RESUME_ALLOWED = NO

The failure was classified as an executable governance defect and repaired on `p0/opro-baseline`. The CI workflow was strengthened to capture execution identity and raw evidence and to fail closed on gating regression failures.

## Immediate next-session workflow

### Phase A — Verify remediation on current HEAD

1. Read canonical state, handoff, continuity contract, and audit evidence contract.
2. Confirm branch is `p0/opro-baseline` and current HEAD is a descendant of checkpoint `16972e2f...`.
3. Confirm audited baseline remains exactly `20a54b92...`.
4. Identify the newest `Factory Kernel Regression` run whose intended head SHA exactly equals the current `p0/opro-baseline` HEAD.
5. Capture run ID, event, ref, head SHA, run attempt, job IDs, step conclusions, and raw logs.
6. Verify RC-01..RC-08 are all PASS and `RESUME_STATUS=RESUME_ALLOWED`.
7. Verify Factory Demo, Deterministic Harness, OPRO Baseline E2E, and pytest results.
8. Download `factory-kernel-machine-evidence` when present.
9. Verify GitHub-reported artifact digest against an independently recomputed digest.
10. Bind the evidence package to the exact current SHA and record the verdict.
11. Only if all evidence gates are GREEN, set `RESUME_ALLOWED` and proceed to M1-B.

### Phase B — M1-B source decision

Only after `RESUME_ALLOWED`:

1. Discover a bounded candidate set of financial data sources.
2. Score candidates on authority, historical depth, corporate actions, PIT capability, API stability, licensing, reproducibility, cost, and operational burden.
3. Apply hard gates first; optimize only among hard-gate-valid candidates.
4. Select the minimum sufficient source stack; avoid unnecessary provider proliferation.
5. Record rationale and rejected alternatives.

### Phase C — M1-B evidence build

1. Select five real historical series.
2. Preserve raw responses/data.
3. Record source, endpoint/query, retrieval time, parameters, version/identifier, and provenance.
4. Compute content hashes.
5. Re-ingest/replay where practical to test reproducibility.
6. Cross-source reconcile with explicit tolerances and discrepancy classification.
7. Establish PIT evidence and identify survivorship/look-ahead risks.
8. Emit machine-verifiable evidence.
9. Run M1-B gate and classify `GREEN` / `NOT_GREEN` / `INCONCLUSIVE`.

## Workflow hardening rules promoted this session

- A current-SHA execution run is mandatory; historical runs for other SHAs cannot satisfy the gate.
- Evidence-only PRs may be used to execute an immutable target SHA, but MUST NOT be merged.
- For pull-request workflows, `github.sha` may be a synthetic merge SHA; capture `github.event.pull_request.head.sha` separately and bind evidence to the intended target.
- Validator runtime errors are regression failures, never PASS or INCONCLUSIVE evidence of success.
- CI artifacts MUST include execution identity and raw resume output even when the resume gate fails.
- Regression steps that contribute to GREEN MUST NOT use `continue-on-error`.
- Artifact digest verification is a separate evidence check from workflow success.
- `AUDIT_EVIDENCE_CHAIN=GREEN` and `RESUME_ALLOWED` remain separate gates.

## OPRO/GEPA methodological guardrails

Do NOT implement GEPA or promote OPRO in this phase. Use their methodological lessons only:

- OPRO: maximize verified useful progress subject to hard governance constraints.
- GEPA: diagnose failure, preserve the case as a regression seed, propose a targeted improvement, and promote only after evidence.
- Never optimize an aggregate score across a hard-gate failure.
- Keep workflow alternatives explicit when multiple designs are viable.
- Prefer small, reversible governance changes with deterministic witnesses.

## CHECKPOINT trigger

Checkpoint immediately after any of these:

- state/handoff identity is repaired;
- CI evidence is captured;
- a gate changes status;
- source-stack decision is made;
- an evidence schema/provenance contract changes;
- a material regression case is added.

Checkpoint sequence:

`Execute → Capture → Verify → Classify → CER CHECK → Update State/Handoff → Git Commit`

## CLOSE trigger

At session end:

`Lessons Learned → Permanent Rule → Task Guidance → Automation Candidate → Current State → Next Action → Evidence references → CER CHECK → Git Commit`

## Absolute constraints

- GEPA implementation forbidden.
- RE Domain implementation forbidden.
- OPRO promotion forbidden.
- Audited baseline SHA must not change.
- PASS without primary execution evidence forbidden.
- Backtest forbidden before M1-B GREEN.
- OOS forbidden before M1-B GREEN.
- Optimization forbidden before M1-B GREEN.
- Monte Carlo forbidden before M1-B GREEN.

## Definition of success for next session

The session succeeds only if it produces either:

1. `RESUME_ALLOWED` backed by current-SHA primary CI/Git evidence and then advances M1-B; or
2. a precise, machine-verifiable remediation package explaining why resume remains blocked.

Never convert an unavailable, stale, merge-SHA-only, or runtime-error execution result into PASS merely to maintain workflow momentum.
