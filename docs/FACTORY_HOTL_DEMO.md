# AgentFactory HOTL Demo

This demo uses synthetic engineering evidence only. It does not connect a real RE domain implementation.

## Runtime command

From the repository root:

```bash
python3 scripts/factory_demo.py --scenario all
```

Machine-readable output:

```bash
python3 scripts/factory_demo.py --scenario all --json
```

Individual paths can be executed with `--scenario pass`, `--scenario review`, or `--scenario block`.

## Golden Paths

### 1. PASS — autonomous path

```text
Task
 → CER Snapshot
 → Demo Domain Pack
 → Evidence
 → Supported Claim
 → Verification
 → CER PASS
 → Workflow continues
 → Trace
```

Expected human intervention: `0`

### 2. REVIEW — human-on-the-loop path

```text
Task
 → CER Snapshot
 → Demo Domain Pack
 → Evidence
 → High-risk Claim
 → Verification
 → CER REVIEW
 → REVIEW_REQUIRED
 → Human Decision: APPROVE
 → CER PASS
 → Workflow continues
 → Trace + HumanDecision
```

Expected human intervention: `1` review action.

### 3. BLOCK — fail-closed path

```text
Task
 → CER Snapshot
 → Unsupported Claim
 → CER BLOCK
 → BLOCKED
 → Workflow terminates
```

Human approval must not bypass `BLOCK`.

## Human Decision Semantics

- `APPROVE` on `REVIEW` → `PASS`
- `REJECT` / `ESCALATE` on `REVIEW` → `BLOCK`
- `MODIFY` / `REQUEST_RETRY` on `REVIEW` → `CHANGE`
- `BLOCK` is never converted directly to `PASS`

A human correction is recorded as a new decision/reference and does not overwrite the original Claim or CER decision.

## Acceptance Criteria

1. PASS path runs without human intervention.
2. High-risk path enters `REVIEW_REQUIRED` and cannot cross the governed boundary without a HumanDecision.
3. Unsupported claims enter `BLOCKED`.
4. `BLOCKED` cannot transition back to execution.
5. HumanDecision contains `run_id`, `gate_id`, `snapshot_id`, actor, reason, and resulting state.
6. Trace links the HumanDecision through `human_decision_id` / human feedback metadata.
7. The demo remains Domain Pack driven and contains no RE-specific parser/retriever implementation.
8. The CLI can execute all three golden paths in one invocation.
9. The `--json` output is deterministic enough for an automated smoke-test comparison of decision/result states.

## Factory Demo Exit Criteria

The demo is considered operational when one command produces:

```text
PASS   → COMPLETED
REVIEW → REVIEW_REQUIRED → Human APPROVE → PASS → COMPLETED
BLOCK  → BLOCKED
```

The demo is a kernel/governance validation artifact. It is not evidence that the RE domain implementation is production-ready.
