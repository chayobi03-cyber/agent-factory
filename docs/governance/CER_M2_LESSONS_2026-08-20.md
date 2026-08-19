# CER / M2 Lessons Learned — 2026-08-20

## Evidence lessons
1. M1-B GREEN is a prerequisite for M2 but is not M2 performance evidence.
2. A defined case matrix is readiness evidence, not historical execution evidence.
3. REVIEW_REQUIRED is preferable to a synthetic PASS when primary historical execution is absent.

## Data / PIT lessons
1. `observation_time` and PIT availability time remain separate in every M2 record.
2. Vintage/revision identity is part of historical replay identity.
3. Numeric equality does not establish provenance equality.
4. Raw payload hash and transformation version must remain bound to the source snapshot.

## Workflow lessons
1. M2 uses the same evidence chain as the CER/Factory Kernel gate.
2. OOS, stress, and Monte Carlo require explicit predecessor gates.
3. The 12-case matrix must be deterministic before real historical execution.
4. A material failure must follow a bounded RCA/remediation loop instead of repeated blind retries.

## Automation lessons
1. Negative tests are first-class M2 regression seeds.
2. Structural matrix checks precede historical execution.
3. REVIEW_REQUIRED is distinct from PASS and BLOCKED.
4. Failure cases should become regression witnesses where technically feasible.

## Agentic / HOTL lessons
1. Missing vintage or availability evidence is a review boundary; the agent must not infer it.
2. Agents may propose lineage mappings, but the gate requires machine evidence.
3. For material failures, use up to three cycles of `cause analysis → countermeasure → regression/evidence → human review`.
4. After resolution, explicitly review whether the lesson should become a permanent rule, regression seed, or automation.
5. After three unsuccessful cycles, stop blind retries and escalate to architecture/specification/tooling/human review classification.

## Permanent rules
- M1-B GREEN does not equal M2 performance PASS.
- `observation_time != PIT availability_time` unless explicitly proven.
- Vintage/revision identity is part of provenance identity.
- Exact value equality does not imply evidence equality.
- Synthetic fixture evidence cannot satisfy a historical-performance gate.
- No OOS/stress/Monte Carlo before the corresponding predecessor evidence gate.
- Missing historical execution evidence yields REVIEW_REQUIRED, never PASS.
- Material failures use a maximum three-cycle RCA/remediation loop before escalation.
- Resolution triggers a rule-gap review; recurring failure patterns must become regression/automation/governance candidates.
- Human approval is never inferred from local PASS, CI PASS, or absence of an error.
