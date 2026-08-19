# HOTL RCA — 2026-08-20 M2 CI Evidence Retrieval

## Problem

The canonical branch was advanced to target SHA `33ba2e963ab42dd86f8f9722d5f1dda95a9dd0f7` so the M2/HOTL governance changes are now in the canonical branch. A current-SHA Factory Kernel execution run is required before M2 can move beyond `REVIEW_REQUIRED`.

The available workflow-run connector returned no run for this SHA, and combined status returned no status checks.

This is **not** treated as proof that GitHub Actions did not execute. The available workflow-run query is documented to expose pull-request-triggered runs only, while the workflow also has a push trigger. Therefore the current result is `EVIDENCE_UNAVAILABLE`, not PASS and not FAIL.

## RCA cycle 1 — Trigger configuration

### Observation
The workflow contains a push trigger for `p0/**` and a pull-request trigger for `main, p0/**`.

### Cause assessment
The workflow definition itself contains a valid push path for the canonical branch. No configuration contradiction was proven.

### Countermeasure
Keep the push trigger and preserve exact runtime SHA assertion. Do not weaken the gate merely to obtain a visible run.

### Result
Configuration is consistent. Problem remains evidence retrieval.

## RCA cycle 2 — Execution identity

### Observation
The workflow captures `target_sha`, `checked_out_sha`, and requires equality. The M2 readiness step is blocking and machine evidence is uploaded with `if: always()`.

### Cause assessment
The execution identity design is present, but it cannot be credited until an actual run/job/log/artifact is retrieved for the canonical SHA.

### Countermeasure
Require the complete chain:

`target SHA → run → job → log → artifact → digest`

before changing M2 status.

### Result
Identity design is adequate on inspection. Runtime proof remains unavailable.

## RCA cycle 3 — Evidence retrieval boundary

### Observation
The available GitHub workflow-run retrieval action only returns pull-request-triggered runs. The current canonical execution is expected from the push trigger, so absence from this query is not sufficient to classify the execution as failed.

### Cause assessment
The blocking issue is an evidence-observability/tooling boundary, not a proven CI failure.

### Countermeasure
Keep the gate fail-closed and classify the current result as `REVIEW_REQUIRED / EVIDENCE_UNAVAILABLE`. Add a follow-up action to obtain a directly queryable push-triggered run or an equivalent primary execution evidence path before M2 progression.

### Result
The issue is not solved by the available evidence path. Do not declare PASS/GREEN.

## Rule-gap review

This incident confirms an existing permanent rule:

> Missing or unqueryable runtime evidence is `INCONCLUSIVE` / `REVIEW_REQUIRED`, never PASS.

No new safety rule is required beyond the three-cycle HOTL rule. A tooling improvement is required: current-SHA push execution must be independently discoverable as run/job/log/artifact/digest evidence.

## Final classification

`M2 = REVIEW_REQUIRED`

`M2 historical execution = NOT_VERIFIED`

`OOS / optimization / stress / Monte Carlo = FORBIDDEN`
