# Merged-Branch Cleanup — 2026-08-25

Deleted 30 remote branches, each verified to have **zero commits** not already
reachable from the trunk at `fe13fa92b83615dcaff4278777206ea14fcbf439`. No history was lost: every
commit these refs pointed at remains in the trunk's history.

Rationale: `11_Audit/LSN-0001` identified the ambient condition — many stale
branches, no single canonical trunk — as the cause of a session re-deriving its
plan from the wrong line and proposing to rebuild ~6,000 lines that already
existed. Removing fully-merged refs removes that condition.

Retained deliberately:

| Branch | Why |
|---|---|
| `main` | canonical trunk |
| `p0/opro-baseline` | previous trunk name, kept as a pointer during the transition |
| `claude/handover-rxravc` | active working branch |
| `p0/opro-baseline-m1b-history-20260819` | `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` requires the M1-B financial detour be retained on a dedicated historical branch |
| `p1/domain-matrix-workflow-v0.1`, `governance/ci-pr-execution-lessons-2026-08-20`, `p0/m1b-ingestion-v1b` | carry unmerged commits **and** quarantined investment artifacts; salvage files individually, never merge |
| `p0/re-domain-pack-v0.1`, `p1/re-domain-pack-v0.1`, `audit/evidence-chain-remediation`, `fix/rc-schema-drift-e11a663a` | carry unmerged commits; contamination-free, pending salvage review |

## Restore

Any branch below is recreated with `git push origin <sha>:refs/heads/<name>`.

```
20a54b92aad0857f75c6200d984b13098c6f4927 audit-remediation/p0-evidence-chain
16972e2fa29496731319f088907170d93961ae48 evidence/base-16972e2f
d61b050437523c39a3363e89e625cce08a273928 evidence/current-head-20260818
d61b050437523c39a3363e89e625cce08a273928 evidence/current-head-20260818-final
d61b050437523c39a3363e89e625cce08a273928 evidence/current-head-20260818-final2
d61b050437523c39a3363e89e625cce08a273928 evidence/current-head-20260818-pr
d61b050437523c39a3363e89e625cce08a273928 evidence/current-head-20260818-pr2
e11a663ab6a51029496934f0157af6ba2b1d7176 evidence/current-head-20260820
0e0c66160f0ea005d0c3c61d88911834af0660bd evidence/resume-0e0c6616
9b097531529ac39401c36f863e326bd06e3de3c6 evidence/resume-9b097531
4ca7030124e40dfab237809c84d1df8b9cc10d06 evidence/resume-current-head
e62f89d75ba0024a0702a1573d18b71a30608e07 evidence/resume-e62f89d7
c309f9142094a04cc794a8095883d4cec6c22842 m1b/pit-reconciliation-remediation-20260820
e62f89d75ba0024a0702a1573d18b71a30608e07 p0/evidence-exec-e62f89d7
2adbf5304491cde04f02fb997f766b40460ccf60 p0/evidence-execution-remediation-e62f89d7
5c02d26cbc56684de14ae3fabff453784a62fed3 p0/factory-kernel-green
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-financial-provenance
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-financial-provenance-clean
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-financial-provenance-tmp
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-financial-provenance-v2
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-ingestion
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-ingestion-v1
2adbf5304491cde04f02fb997f766b40460ccf60 p0/m1b-ingestion-v1c
33ba2e963ab42dd86f8f9722d5f1dda95a9dd0f7 p0/m2-hotl-loop-20260820
9b097531529ac39401c36f863e326bd06e3de3c6 tmp/cer-target-sha-fix
189f73073e4ba3ffb512a4886889cd0500581f5f tmp/m2-entry-review-20260820
3db3a1386a9cad1ea4907930e7fb1491754b1e82 tmp/pytest-import-path-fix
e03f9e49cb2dd02f6eea68df1c8d5e23d2a6367e tmp/rc-parser-robustness
2adbf5304491cde04f02fb997f766b40460ccf60 tmp/resume-test-hardening
5ab787a649606502f4ff24ac883da490f10dfc48 tmp/resume-validator-contract-align
```
