# Merged-Branch Cleanup — prepared 2026-08-25, NOT YET EXECUTED

> **Status: PREPARED, NOT EXECUTED.** Deletion was attempted from the session that
> produced this record and refused with `HTTP 403` on every ref delete — that
> session's credentials permit pushes but not deletions, and the GitHub MCP server
> exposes no branch-deletion tool. The branches below are still on the remote.
> Run the procedure from a normal local clone, then change this heading.

## What was verified

Each of the 30 branches carries **zero commits** not already reachable from the
trunk. Deleting them loses no history: every commit they point at stays in `main`.

Rationale: `11_Audit/LSN-0001` identified the ambient condition — many stale
branches, no single canonical trunk — as the cause of a session re-deriving its plan
from the wrong line and proposing to rebuild ~6,000 lines that already existed.

## Procedure

### 1. Get a current clone and confirm you are on the trunk

```bash
git clone https://github.com/chayobi03-cyber/agent-factory.git
cd agent-factory
git fetch origin --prune
git checkout main && git pull
```

### 2. Re-verify before deleting anything

Do not trust this file's list blindly — the trunk has moved since it was written.
This re-derives the safe set against **your** current `main` and refuses to list
anything that still holds unique work:

```bash
KEEP="main claude/handover-rxravc p0/opro-baseline"
git ls-remote --heads origin | while read sha ref; do
  b=${ref#refs/heads/}
  case " $KEEP " in *" $b "*) continue;; esac
  if git merge-base --is-ancestor "$sha" origin/main 2>/dev/null; then
    echo "SAFE     $b"
  else
    echo "KEEP     $b  ($(git rev-list --count origin/main.."$sha") unique commits)"
  fi
done | sort
```

Expect 30 `SAFE` lines. If a branch you expected to be SAFE shows KEEP, someone
pushed to it after 2026-08-25 — investigate that branch instead of deleting it.

### 3. Delete

Deleting only what step 2 just proved safe, rather than a hardcoded list:

```bash
KEEP="main claude/handover-rxravc p0/opro-baseline"
SAFE=$(git ls-remote --heads origin | while read sha ref; do
  b=${ref#refs/heads/}
  case " $KEEP " in *" $b "*) continue;; esac
  git merge-base --is-ancestor "$sha" origin/main 2>/dev/null && echo "$b"
done)

echo "$SAFE" | wc -l                 # sanity-check the count first
git push origin --delete $SAFE       # then delete
```

`git push --delete` takes many refs at once, so this is a single round trip. If
the remote rejects the batch, delete in smaller groups — the operation is
idempotent and a partial run is safe to repeat.

### 4. Tidy local tracking refs

```bash
git fetch origin --prune
```

### 5. Mark this record executed

Change the heading and the status block at the top, and set
`OPEN_DECISIONS_2026-08-25.md` D-05 to resolved.

## Restore

Deletion is reversible from these SHAs for as long as the objects live in the
repository — no clone or backup needed:

```bash
git push origin <sha>:refs/heads/<name>
```

## Retained deliberately

| Branch | Why |
|---|---|
| `main` | canonical trunk |
| `p0/opro-baseline` | previous trunk name, kept during the transition (see D-06) |
| `claude/handover-rxravc` | working branch |
| `p0/opro-baseline-m1b-history-20260819` | `ARCHITECTURE_REFACTOR_PLAN_2026-08-19.md` requires the M1-B financial detour be retained on a dedicated historical branch |
| `audit/evidence-chain-remediation` | **PR #1** — carries the unmerged evidence-gate implementation of a canonical contract. See D-09. Do not delete. |
| `p1/domain-matrix-workflow-v0.1` | assets recovered to the trunk (D-04); branch retained because it also holds quarantined investment artifacts and its own history |
| `governance/ci-pr-execution-lessons-2026-08-20`, `p0/m1b-ingestion-v1b` | unmerged commits plus quarantined artifacts; salvage files individually, never merge |
| `p0/re-domain-pack-v0.1`, `p1/re-domain-pack-v0.1`, `fix/rc-schema-drift-e11a663a` | unmerged commits, contamination-free, pending salvage review |

## The 30 branches, with restore SHAs

Snapshot taken 2026-08-25 against trunk `19294f25b2574de34cc1f9b3d30e8650cc7c93e2`.
Step 2 re-derives this list; the snapshot is here for restore and audit.

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
