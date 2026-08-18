# M1-B Financial Source Contract V1

## Objective

Establish a minimum sufficient, auditable financial-data path before any strategy-performance analysis.

## Required chain

```text
Source
  → Raw snapshot
  → Provenance record
  → Normalized observation
  → Point-in-time availability
  → Replay key
  → Cross-source reconciliation
  → M1-B GREEN
```

## Source requirements

Each source MUST record provider, dataset, locator/endpoint, authority, retrieval method, retrieval version, retrieval timestamp, and raw payload SHA-256.

## Historical-series requirements

Each observation MUST preserve observation time, value, unit, currency when applicable, and the source's availability/as-of timestamp. The availability timestamp is the authoritative point-in-time boundary for downstream use.

## Provenance requirements

Derived observations MUST retain upstream record identifiers plus source and derived hashes. Normalization and transformation logic MUST be versioned.

## Replay requirements

Every normalized series MUST have a deterministic replay key. Replaying the same raw snapshot with the same transformation version MUST produce the same derived hash.

## Reconciliation requirements

When multiple sources represent the same economic series, reconciliation MUST record a cross-source group, status, tolerance where applicable, and discrepancy notes. Discrepancies are surfaced rather than silently overwritten.

## M1-B entry sequence

1. Define the minimum sufficient source stack.
2. Select five real historical series spanning the intended data requirements.
3. Capture immutable/raw snapshots where feasible.
4. Normalize into the provenance schema.
5. Validate point-in-time availability and replay determinism.
6. Reconcile cross-source observations.
7. Produce machine-verifiable QA evidence.

## Forbidden before M1-B GREEN

- backtest
- out-of-sample evaluation
- optimization
- Monte Carlo analysis
- OPRO promotion
- GEPA implementation

## Acceptance criterion

M1-B is GREEN only when the five historical series have complete provenance, PIT/replay evidence, and reconciliation evidence, with no unresolved integrity blocker.
