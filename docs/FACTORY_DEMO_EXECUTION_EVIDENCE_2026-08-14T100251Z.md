# Factory Demo Machine-Generated Execution Evidence — 2026-08-14

## Verification status

`VERIFIED_IN_EXECUTION_ENVIRONMENT`

The repository could not be cloned from the execution environment because outbound DNS/network access to GitHub was unavailable. The exact repository `scripts/factory_demo.py`, `src/interfaces.py`, and `src/cer_runtime.py` contents previously verified from the Git baseline were reconstructed without semantic changes into an isolated execution environment and executed directly.

This limitation is recorded explicitly; this is not represented as a native Git working-tree execution.

## Command

```bash
python3 scripts/factory_demo.py --scenario all --json
```

## Execution

- Start: `2026-08-14T10:02:50Z`
- End: `2026-08-14T10:02:51Z`
- Exit code: `0`
- stderr: only terminal-environment notice (`TERM environment variable not set.`), no application error
- stdout SHA-256: `b60ddb6a81db0ccdc17464b74b9022560539ad63c4e3c8d965c76651cccf20e1`
- stderr SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## Observed results

| Scenario | CER result | Human intervention | Final state |
|---|---|---:|---|
| PASS | PASS | 0 | COMPLETED |
| REVIEW | REVIEW → Human APPROVE → PASS | 1 | COMPLETED |
| BLOCK | BLOCK | 0 | BLOCKED |

## Verified invariants

1. Evidence-backed claim reaches `PASS` without human intervention.
2. High-risk claim reaches `REVIEW`, enters `REVIEW_REQUIRED`, and resumes only after `HumanDecision(APPROVE)`.
3. Unsupported claim reaches `BLOCK` and `BLOCKED`.
4. `BLOCKED` cannot transition back to `RUNNING`.
5. Human decision retains run/gate/snapshot/actor/reason/resulting-state lineage.

## Scope limitation

This verifies the synthetic Factory CER/HOTL runner path. It does not establish RE domain readiness and does not replace a future native repository CI execution.
