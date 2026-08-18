# CER Resume Contract v1.0

**Status:** Active governance contract
**Scope:** Cross-session continuity and safe workflow resumption
**Branch:** `p0/opro-baseline`

## 1. Purpose

A new session MUST NOT resume governed work from conversational context alone.
The resume decision is valid only after consistency checks across three independent state anchors:

```text
CURRENT_SESSION_STATE
        ↕
Git HEAD / branch
        ↕
Audited baseline / handoff
```

The contract is fail-closed: any mandatory inconsistency yields `RESUME_BLOCKED` or `RESUME_REVIEW_REQUIRED` and governed downstream execution must not continue.

## 2. Resume Inputs

The minimum resume inputs are:

1. `docs/governance/CURRENT_SESSION_STATE.yaml`
2. Git branch and HEAD
3. Current audited baseline SHA
4. `docs/governance/NEXT_SESSION_HANDOFF_*.md`
5. Applicable CER/audit constraints

Historical chat context is optional context only and is never a source of truth.

## 3. Mandatory Consistency Checks

### RC-01 — State ↔ Git branch

`CURRENT_SESSION_STATE.branch` MUST equal the actual Git branch.

Mismatch => `RESUME_BLOCKED`.

### RC-02 — State ↔ Git HEAD

`CURRENT_SESSION_STATE.git.head_sha` MUST describe the expected checkpoint relation.
The contract supports two valid modes:

- `exact`: current HEAD must equal the recorded checkpoint SHA.
- `descendant`: current HEAD must be a descendant of the recorded checkpoint SHA and the intervening commits must be explicitly acceptable under the handoff.

Unexpected divergence => `RESUME_BLOCKED`.

### RC-03 — State ↔ Audited baseline

`CURRENT_SESSION_STATE.audited_baseline_sha` MUST equal the audited baseline recorded by the active handoff/audit authority.

Mismatch => `RESUME_BLOCKED`.

### RC-04 — Handoff ↔ Git branch

The active handoff MUST identify the same repository and branch as the current state.

Mismatch => `RESUME_BLOCKED`.

### RC-05 — Handoff ↔ audited baseline

The handoff MUST preserve the audited baseline identity and MUST NOT silently replace it with the current HEAD.

Mismatch => `RESUME_BLOCKED`.

### RC-06 — Gate ↔ forbidden actions

The state gate and handoff constraints MUST agree.
A downstream action is prohibited when the gate says `NOT_GREEN`, `BLOCKED`, `HOLD`, or `INCONCLUSIVE` for a mandatory control.

Mismatch => `RESUME_BLOCKED`.

## 4. Resume Decision Algorithm

```text
LOAD state
  ↓
READ Git branch + HEAD
  ↓
READ active handoff
  ↓
RESOLVE audited baseline
  ↓
CHECK RC-01..RC-06
  ↓
all PASS
  ├─ yes → RESUME_ALLOWED
  └─ no
       ├─ recoverable evidence ambiguity → RESUME_REVIEW_REQUIRED
       └─ identity / baseline / branch contradiction → RESUME_BLOCKED
```

`RESUME_ALLOWED` is required before execution of governed work.

## 5. State Precedence

When values disagree:

1. audited baseline identity and immutable evidence win over mutable session notes;
2. Git repository state is authoritative for actual branch/HEAD;
3. handoff is authoritative for declared next action and explicit constraints;
4. `CURRENT_SESSION_STATE` is authoritative for the current checkpoint only when it passes RC-01..RC-06;
5. conversational memory is lowest priority.

## 6. Checkpoint Rule

A session checkpoint MUST record:

- session identifier
- repository
- branch
- checkpoint commit SHA
- audited baseline SHA
- current phase
- current gate
- completed work
- next action
- blocked/forbidden actions
- active handoff path

A checkpoint is not complete until these fields are committed to Git.

## 7. Context-Minimization Rule

A new session SHOULD load, in order:

1. `CURRENT_SESSION_STATE.yaml`
2. active handoff
3. only the evidence/contracts referenced by the next action

It SHOULD NOT reload the full prior conversation unless a consistency check fails or the handoff explicitly requires historical context.

## 8. Required Resume Log

Every resume attempt SHOULD emit machine-readable results for RC-01..RC-06 with:

- check_id
- observed_value
- expected_value
- result
- source_reference
- timestamp_utc

This log becomes evidence for the CER session trace.

## 9. Security / Governance Constraints

A resume mechanism MUST NOT:

- infer a new audited baseline from HEAD;
- rewrite the audited baseline because the branch advanced;
- treat a missing handoff as PASS;
- convert tool/rate-limit failure into PASS;
- cross a gated boundary while resume status is unresolved.

## 10. Relationship to Existing CER

This contract extends the existing CER requirements for immutable runtime identity, checkpoint/state persistence, replayability, and immutable execution manifests. It does not redefine the audited baseline or replace CER gate semantics.
