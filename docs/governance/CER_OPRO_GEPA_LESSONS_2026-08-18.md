# CER Lessons — OPRO/GEPA Workflow Hardening — 2026-08-18

## Purpose

Convert the session's resume-control failure into reusable governance and workflow improvements without implementing GEPA or changing the audited OPRO baseline.

Audited OPRO baseline (immutable): `20a54b92aad0857f75c6200d984b13098c6f4927`

## 1. OPRO-style lessons: optimize the workflow objective, not the safety boundary

### OPRO-LSN-001 — Optimize for verified progress

The workflow objective must not be "complete the next task". It is:

`maximize verified useful progress subject to governance constraints`

A workflow that reaches M1-B faster but weakens provenance, identity, or evidence gates is a regression, not an optimization.

### OPRO-LSN-002 — Make failure modes explicit in the objective

Resume quality must score at least:

- identity consistency;
- evidence availability;
- reproducibility;
- fail-closed behavior;
- execution cost;
- context size;
- useful downstream progress.

A single aggregate score must not hide a hard safety failure.

### OPRO-LSN-003 — Prefer smallest sufficient source/workflow stack

For M1-B, provider count is not the optimization target. The target is the minimum source stack that satisfies authority, historical depth, corporate-action handling, PIT, API stability, licensing, reproducibility, cost, and operational-burden requirements.

## 2. GEPA-style lessons: reflective workflow evolution

GEPA is not implemented by this rule set. Its reflective principle is applied only as a methodology for improving prompts, gates, and workflow structure.

### GEPA-LSN-001 — Diagnose before modifying

When a gate fails, classify the failure before changing implementation:

`identity / state / evidence / execution / environment / specification / tooling`

Do not patch symptoms without identifying the failed invariant.

### GEPA-LSN-002 — Preserve failed cases as regression seeds

Every material failure or ambiguity becomes a deterministic regression fixture where feasible. The exact session case should remain reproducible after the remediation.

### GEPA-LSN-003 — Promote only validated improvements

A lesson becomes a permanent rule only when it has:

`lesson → proposed rule → regression witness → CI evidence → governance promotion`

Otherwise it remains task-level guidance.

### GEPA-LSN-004 — Keep workflow variants explicit

When multiple workflow designs are plausible, retain the alternatives as named candidates and compare them against the same acceptance criteria. Do not silently replace one workflow with another.

## 3. New workflow-control rules

1. **Canonical identity triad:** state, Git ref/HEAD, and handoff must expose machine-comparable identity fields.
2. **Checkpoint monotonicity:** a later state checkpoint may advance only along verified Git ancestry; stale handoff anchors must not be accepted as current.
3. **Execution-evidence binding:** every CI PASS used by a gate must bind run ID + workflow + ref + commit SHA + job/check result + artifact identity.
4. **Evidence freshness:** evidence must be checked against the current checkpoint and declared task scope; old successful runs cannot satisfy a new execution requirement unless explicitly version-bound.
5. **Fail-closed ambiguity:** unavailable run metadata, missing artifacts, detached-HEAD ambiguity, or stale checkpoint references produce `INCONCLUSIVE`/`REVIEW_REQUIRED`, never PASS.
6. **Gate separation:** continuity GREEN, Audit Evidence Chain GREEN, and M1-B GREEN remain separate gates. Passing one never implies another.
7. **No downstream execution on unresolved identity:** if RC-01~RC-06 contains a contradiction, do not execute `next_action`.
8. **Progressive disclosure:** load only the minimum context required for the active gate; expand context only on a failed check or explicit dependency.
9. **Reproducibility packet:** each promoted workflow change must identify its fixture set, expected result, actual result, evidence artifact, and commit SHA.
10. **Reversible promotion:** governance changes should be isolated, reviewable, and easy to revert without touching the audited baseline.

## 4. M1-B workflow hardening

The next M1-B workflow must use these stages:

`Source candidate discovery`
→ `evaluation matrix`
→ `minimum-stack decision`
→ `5-series fixture selection`
→ `raw ingest`
→ `provenance + hash`
→ `cross-source reconciliation`
→ `PIT evidence`
→ `machine-verifiable evidence`
→ `M1-B decision`

Each stage emits evidence before the next stage is allowed to consume it.

## 5. Acceptance model

Use two classes of criteria:

### Hard gates

- baseline identity preserved;
- branch/checkpoint identity valid;
- provenance present;
- PIT evidence sufficient;
- machine evidence reproducible;
- required regression green.

Hard-gate failure cannot be compensated by a high aggregate score.

### Optimization criteria

Among hard-gate-valid candidates, optimize:

- authority;
- historical depth;
- corporate-action coverage;
- API stability;
- licensing;
- reproducibility;
- cost;
- operational burden;
- implementation complexity.

## 6. Anti-patterns to retain as regression cases

- stale handoff checkpoint after a newer state commit;
- using an unrelated historical Actions run as current evidence;
- declaring PASS when the execution environment cannot be verified;
- treating documentation presence as proof of runtime execution;
- allowing downstream work after an unresolved resume contradiction;
- allowing provider convenience to override PIT/provenance requirements;
- optimizing provider count instead of verified coverage.

## 7. Constraints

This document does not authorize:

- GEPA implementation;
- RE Domain implementation;
- OPRO promotion;
- audited baseline modification;
- backtest/OOS/optimization/Monte Carlo before M1-B GREEN.

## 8. Next-session operating principle

`VERIFY → DIAGNOSE → REPAIR → REGRESS → EVIDENCE → PROMOTE`

Only after the continuity gate is `RESUME_ALLOWED` may the workflow enter M1-B.

## 9. Session 2026-08-18 current-SHA CI evidence lessons

### OPRO-LSN-004 — Execution identity must be captured before interpreting results

An evidence-only PR successfully triggered `Factory Kernel Regression` against target head SHA `0e0c66160f0ea005d0c3c61d88911834af0660bd`, proving that immutable-target execution can be obtained without changing the target commit. However, the pull-request workflow checked out a synthetic merge SHA. Therefore `github.sha` alone is insufficient for target identity; the workflow must capture the PR head SHA explicitly.

### GEPA-LSN-005 — A validator crash is a first-class regression seed

The target run `32124843431` failed before RC-01..RC-08 could produce verdicts because `check("RC-07", ...)` omitted the required `source` argument. This was not an evidence absence problem; it was an executable governance defect. The failure is preserved as a regression seed and the validator invocation was repaired.

### Permanent Rule — Evidence publication must survive gate failure

The CI workflow now captures:

- CI execution identity;
- raw resume validator output;
- raw demo/harness/OPRO/pytest output;
- machine evidence artifact.

Artifact publication remains `if: always()` so a failed gate does not erase the evidence required to diagnose it.

### Permanent Rule — GREEN regression steps cannot be non-blocking

`continue-on-error` was removed from the deterministic harness because a regression contributing to a GREEN decision must fail the job when it fails. Non-blocking execution is acceptable only for explicitly diagnostic/non-gating work.

### Permanent Rule — Artifact digest is an independent evidence check

Workflow success is not equivalent to evidence integrity. The next session must download the current-SHA artifact, compare its GitHub-reported digest with an independently recomputed digest, and record the comparison as a separate evidence verdict.

## 10. Automation candidates

1. Add a reusable `audit-evidence-verify` script that consumes run metadata + artifact metadata and emits a machine-verifiable chain verdict.
2. Add a regression fixture that asserts `validate_session_resume.main()` executes without `TypeError` and returns the expected exit code for a consistent fixture.
3. Add workflow metadata/artifact checks that reject a merge SHA when a target head SHA is expected.
4. Add an automated stale-evidence detector comparing evidence SHA to the current state checkpoint and target ref.

These are candidates only until separately implemented, tested, and promoted through the same evidence gate.
