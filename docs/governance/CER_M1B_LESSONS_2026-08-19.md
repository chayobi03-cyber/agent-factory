# CER / M1-B Lessons Learned — 2026-08-19

## What worked

1. Evidence Chain was closed from one primary execution package rather than from narrative state.
2. Target SHA, checkout SHA, execution identity, artifact, and digest were independently bound and verified.
3. M1-B source/provenance work was started only after `RESUME_ALLOWED` was proven.
4. The financial provenance schema separates observation time from PIT availability, preventing timestamp conflation.
5. Raw snapshot hashing is canonicalized so payload order does not change the hash.
6. Replay keys include transformation version, making transformation changes explicit and reproducible.
7. Cross-source reconciliation is recorded as an evidence object instead of silently choosing one source.

## What did not work / remaining gaps

1. A historical observation value alone is not sufficient PIT evidence.
2. The first fixture initially marked PIT as `UNVERIFIED`; this correctly blocked premature M1-B GREEN.
3. The current five-series fixture still lacks first-party release/as-of timestamps for FEDFUNDS, DEXUSEU, and T10YIE.
4. Cross-source reconciliation was not originally built into the first five-series set; a supplemental FRED DGS10 vs U.S. Treasury 10Y check was added to expose the pattern.
5. Repository state and runtime evidence can drift; the state file must remain a pointer to independently retrievable evidence, never the evidence itself.

## Permanent rules

- `observation_time != PIT availability_time` unless the source explicitly proves equivalence.
- A series cannot be marked PIT-verified from a current revised table alone.
- For revision-sensitive series, store a vintage/realtime cutoff and the exact query parameters.
- Every normalized observation must retain source hash, transformation version, upstream record IDs, and replay key.
- Cross-source discrepancies are surfaced, classified, and preserved; never silently overwritten.
- M1-B GREEN requires all five selected series to have complete provenance, PIT/replay evidence, and reconciliation evidence.
- A partial or supplemental reconciliation cannot substitute for required reconciliation coverage of the selected five-series set.

## Workflow improvements

```text
SELECT SERIES
  -> VERIFY DEFINITION / UNIT / FREQUENCY
  -> CAPTURE RAW SNAPSHOT
  -> CAPTURE SOURCE AS-OF / VINTAGE
  -> NORMALIZE
  -> HASH / REPLAY
  -> PIT CHECK
  -> CROSS-SOURCE RECONCILIATION
  -> MACHINE QA
  -> GATE
```

Use fail-closed classification:

```text
missing PIT timestamp      -> REVIEW_REQUIRED
missing raw hash            -> INVALID
replay mismatch             -> FAIL
cross-source discrepancy    -> REVIEW_REQUIRED
all required evidence pass  -> eligible for M1-B GREEN
```

## Regression seeds to keep

- reversed raw observation order must keep the same canonical hash;
- changing transformation version must change replay key;
- missing PIT availability timestamp must not pass;
- stale vintage must not satisfy a later cutoff;
- cross-source mismatch must remain visible;
- exact-value equality alone must not imply provenance equality.

## Current conclusion

M1-B remains `ACTIVE_NOT_GREEN`. The remaining blocker is first-party PIT availability evidence for the remaining three selected fixture series plus reconciliation coverage sufficient for the final five-series gate.
