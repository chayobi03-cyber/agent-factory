# M2 Historical Integration Contract V1

**Status:** Design contract / not yet execution-verified
**Gate:** M2 ENTRY REVIEW
**Purpose:** Define a point-in-time-safe historical integration path before any historical performance claim.

## 1. Scope

M2 integrates revision-sensitive historical datasets into deterministic experiments. M2 is not a performance result by itself. M1-B GREEN is a prerequisite for entry, but its data-quality evidence is not performance evidence.

The required chain is:

```text
M1-B verified provenance
  -> historical dataset identity
  -> PIT/vintage resolution
  -> deterministic normalization
  -> train/validation/OOS partition identity
  -> 12-case experiment readiness
  -> historical execution evidence
  -> OOS gate
  -> stress readiness
  -> stress evidence
  -> Monte Carlo readiness
  -> Monte Carlo evidence
```

No stage may be skipped because an earlier stage is GREEN.

## 2. Mandatory lineage fields

Every historical record entering M2 MUST preserve:

1. source identity;
2. dataset identity and source version;
3. observation timestamp;
4. PIT availability timestamp;
5. vintage/revision identity and as-of boundary;
6. raw payload SHA-256;
7. normalized record SHA-256;
8. transformation rule/version;
9. deterministic replay key;
10. train/validation/OOS partition identity;
11. experiment case ID;
12. evidence artifact ID and execution SHA;
13. deterministic replay result;
14. gate result.

## 3. PIT rule

The operative rule is:

```text
observation_time <= PIT availability_time <= experiment cutoff
```

`observation_time` is the time represented by the data. `PIT availability_time` is when the value was actually available to the experiment. They MUST NOT be conflated unless the source explicitly proves equivalence.

A current revised table is not historical PIT evidence. A vintage/revision that was not available by the experiment cutoff MUST be rejected.

## 4. Provenance equality

Numeric equality does not imply evidence equality.

Two values that are numerically identical remain distinct evidence when any of the following differs:

- source;
- dataset version;
- vintage/revision;
- request parameters;
- raw payload hash;
- transformation version;
- upstream record identity.

Cross-source discrepancies are preserved and classified. They are not silently overwritten.

## 5. Deterministic replay

The replay key MUST bind at minimum:

```text
source identity
+ dataset identity/version
+ vintage identity
+ PIT cutoff
+ transform version
+ partition identity
+ experiment case identity
```

Replaying identical inputs with identical transformation version MUST reproduce the same normalized hash and replay key. Changing transformation version MUST change replay identity.

## 6. Partition boundary

Within each experiment case:

```text
Train ∩ Validation = empty
Train ∩ OOS        = empty
Validation ∩ OOS   = empty
```

The OOS interval is fixed before the experiment executes. OOS data MUST NOT be consulted during training, feature construction, parameter selection, or validation.

## 7. Twelve-case experiment

The first M2 experiment is a readiness-controlled 12-case matrix. The case definitions are stored in:

`fixtures/m2/historical_experiment_12_case.yaml`

Each case MUST declare:

- `case_id`;
- `historical_window`;
- `dataset_version`;
- `PIT_cutoff`;
- `input_sources`;
- `transform_version`;
- `expected_evidence`;
- `execution_identity`;
- `partition`;
- `risk_class`;
- `acceptance_gate`.

Case ordering MUST NOT affect provenance hashes. Changing vintage identity, PIT cutoff, dataset identity, or transform version MUST change replay identity.

## 8. Gate vocabulary

| Gate | Meaning |
|---|---|
| `PASS` | Required machine evidence is present, consistent, and verified. |
| `REVIEW_REQUIRED` | A required condition is not proven or an ambiguity/discrepancy needs review. |
| `BLOCKED` | A direct integrity contradiction or prohibited condition exists. |

Missing evidence never becomes PASS by inference.

## 9. OOS / Stress / Monte Carlo boundary

The allowed order is:

```text
M2 entry review
  -> historical integration validation
  -> 12-case historical experiment
  -> OOS readiness gate
  -> actual OOS
  -> stress readiness gate
  -> stress
  -> Monte Carlo readiness gate
  -> Monte Carlo
```

A later stage is blocked until the prior stage has independently verified evidence.

In particular:

```text
Synthetic fixture PASS != historical performance PASS
```

## 10. Required negative regressions

The M2 contract MUST automatically reject or flag:

1. stale vintage;
2. future timestamp;
3. PIT cutoff violation;
4. train/OOS overlap;
5. revised-vs-original provenance mismatch;
6. raw payload order sensitivity;
7. transform-version replay collision;
8. source hash mismatch;
9. dataset identity mismatch;
10. experiment identity mismatch;
11. missing evidence artifact;
12. synthetic fixture attempting to satisfy a historical-performance gate.

## 11. M2 entry decision for this session

The current repository has verified M1-B evidence and a working CER evidence path. It does **not** yet have primary execution evidence for the M2 historical experiment. Therefore the M2 entry decision remains:

```text
M2 = REVIEW_REQUIRED
```

This is not a failure of M1-B. It means the next gate has been defined but not yet executed.
