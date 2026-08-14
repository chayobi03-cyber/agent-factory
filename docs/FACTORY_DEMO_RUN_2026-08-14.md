# Factory Demo Execution Evidence — 2026-08-14

## Command

```bash
python3 scripts/factory_demo.py --scenario all --json
```

## Scope

Synthetic engineering evidence only. No real RE parser, retriever, or domain implementation is used.

## Result

| Scenario | CER path | Human action | Final state |
|---|---|---:|---|
| PASS | PASS | 0 | COMPLETED |
| REVIEW | REVIEW → Human APPROVE → PASS | 1 | COMPLETED |
| BLOCK | BLOCK | 0 | BLOCKED |

## Verified invariants

1. Supported evidence-backed claim can pass the CER gate without human intervention.
2. High-risk claim enters `REVIEW` and `REVIEW_REQUIRED`; execution resumes only after an explicit HumanDecision `APPROVE`.
3. Unsupported claim enters `BLOCK` and `BLOCKED`.
4. `BLOCKED` cannot transition back to execution.
5. HumanDecision preserves `run_id`, `gate_id`, `snapshot_id`, actor, reason, and resulting state.
6. The demo is domain-neutral and uses only synthetic evidence.

## Observed machine-readable results

```text
PASS   → COMPLETED, human=0
REVIEW → REVIEW_REQUIRED → APPROVE → PASS → COMPLETED, human=1
BLOCK  → BLOCKED, human=0
```

This artifact is an execution evidence record for the Factory kernel/HOTL demo. It is not evidence of RE domain readiness.
