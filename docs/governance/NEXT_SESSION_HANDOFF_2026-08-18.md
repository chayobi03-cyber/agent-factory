# AgentFactory Next Session Handoff — 2026-08-20 M2 Entry Review

## Canonical state

Read first:

1. `docs/governance/CURRENT_SESSION_STATE.yaml`
2. `docs/governance/M2_HISTORICAL_INTEGRATION_CONTRACT_V1.md`
3. `docs/governance/M2_ENTRY_REVIEW_2026-08-20.yaml`
4. `fixtures/m2/historical_experiment_12_case.yaml`
5. `schemas/m2_historical_experiment.schema.yaml`
6. `docs/governance/CER_M2_LESSONS_2026-08-20.md`
7. `docs/governance/M1B_PIT_RECONCILIATION_EVIDENCE_2026-08-20.yaml`
8. `docs/governance/EVIDENCE_MANIFEST_2026-08-18_RUN-32126799804.yaml`

Do not reload the entire prior chat. Repository governance artifacts are canonical.

## Repository anchors

- repository: `chayobi03-cyber/agent-factory`
- branch: `p0/opro-baseline`
- audited OPRO baseline SHA — **DO NOT CHANGE**: `20a54b92aad0857f75c6200d984b13098c6f4927`
- canonical handoff ancestry anchor: `ee6f5fd3e470895f9c242c8004b64b4c4f74d6b4`
- M1-B final regression target/execution/checkout SHA: `c1efb9933fc5b3589cd43e986d4b1549f4338923`
- M1-B regression run/job: `32309992157 / 96250842729`
- M1-B artifact: `9386078714`
- M1-B artifact digest: `sha256:8d7864f6041352691d102d78375b76786d85b4916fdbfb313851be5358a2ec1a`

## Current gate

```text
Audit Evidence Chain = GREEN
CER Resume = ALLOWED
M1-B = GREEN
M2 = REVIEW_REQUIRED
OPRO promotion = FORBIDDEN
GEPA implementation = FORBIDDEN
RE Domain implementation = FORBIDDEN
```

M2 `REVIEW_REQUIRED` is intentional. The contract and readiness matrix are defined, but the actual historical 12-case experiment has not been executed and therefore has no primary historical performance evidence.

## M1-B evidence binding

`docs/governance/M1B_PIT_RECONCILIATION_EVIDENCE_2026-08-20.yaml` remains the authoritative M1-B data-lineage seed.

Raw snapshot SHA-256:
`12615dc1bc24a9bc41099c626e92eceaf8f12541ccdf460c810a6ddf4e3d7935`

M1-B evidence is **lineage input**, not M2 performance evidence.

## M2 contract now defined

`docs/governance/M2_HISTORICAL_INTEGRATION_CONTRACT_V1.md` defines:

- source and dataset identity;
- observation time versus PIT availability time;
- vintage/revision identity;
- raw and normalized hashes;
- transformation version and replay key;
- train/validation/OOS partition identity;
- experiment/case/evidence identity;
- deterministic replay;
- fail-closed gate vocabulary;
- OOS/stress/Monte Carlo sequencing.

## 12-case readiness matrix

`fixtures/m2/historical_experiment_12_case.yaml`

```text
12 cases = DEFINED
execution = NOT_EXECUTED
historical performance evidence = NOT_AVAILABLE
```

The matrix enforces:

```text
observation_time <= PIT availability_time <= cutoff
Train ∩ Validation = empty
Train ∩ OOS = empty
Validation ∩ OOS = empty
```

Changing vintage, cutoff, dataset identity, or transform version must alter replay identity.

## Automated M2 regression

Regression seeds are in:

`tests/test_m2_historical_contract.py`

They cover:

1. stale vintage rejection;
2. future timestamp rejection;
3. PIT cutoff violation;
4. train/OOS overlap;
5. revised-vs-original provenance mismatch;
6. raw payload order invariance;
7. transform version replay-key change;
8. source hash mismatch;
9. dataset identity mismatch;
10. experiment identity mismatch;
11. missing evidence artifact;
12. synthetic fixture cannot satisfy historical-performance gate.

CI also runs `scripts/m2_entry_review.py` and emits `m2-entry-review.json` into the machine evidence artifact. `REVIEW_REQUIRED` is an explicit non-green readiness classification; it must not be interpreted as PASS.

## Analysis boundary

```text
M2 entry review
  -> historical integration validation
  -> 12-case historical execution
  -> OOS readiness
  -> actual OOS
  -> stress readiness
  -> stress
  -> Monte Carlo readiness
  -> Monte Carlo
```

No backtest/OOS/optimization/stress/Monte Carlo execution is permitted merely because M1-B is GREEN.

## Next session starting point

1. Resolve actual `p0/opro-baseline` HEAD from Git.
2. Re-run CER RC-01..RC-08 from the new HEAD's primary execution evidence.
3. Inspect the M2 readiness artifact from CI.
4. Decide whether the repository has enough actual historical snapshots/vintage evidence to enter `M2_HISTORICAL_EXECUTION_EVIDENCE`.
5. Do not run OOS, stress, or Monte Carlo until the corresponding gate is independently GREEN.

## Absolute constraints

- audited OPRO baseline immutable;
- OPRO promotion forbidden;
- GEPA implementation forbidden;
- RE domain implementation forbidden;
- state/documentation never substitutes for primary execution evidence;
- synthetic fixture PASS never equals historical performance PASS;
- missing historical evidence => `REVIEW_REQUIRED`, never PASS.

## Session close

`Lessons Learned -> Permanent Rules -> Current State -> CER CHECK -> M2 readiness evidence -> Git commit`
