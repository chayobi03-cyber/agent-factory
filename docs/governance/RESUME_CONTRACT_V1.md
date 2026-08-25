# CER Resume Contract v1.1

> **SUPERSEDED 2026-08-25** by `CER_SESSION_CONTINUITY_CONTRACT_V1.md`
> (OPEN_DECISIONS D-07). Both documents are labelled v1.1 and cover the same
> purpose; only the Continuity Contract is read by code —
> `CURRENT_SESSION_STATE.resume_contract` points at it and RC-08 loads it
> directly. Nothing anywhere references this file.
>
> Retained as history. Its own header previously read *"Active governance
> contract"*, which is what made two documents each claim to be the live resume
> contract while one of them was enforced and the other was not.

**Status:** Superseded — historical record, not enforced
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

`CURRENT_SESSION_STATE.working_branch` MUST equal the actual Git branch.

Mismatch => `RESUME_BLOCKED`.

### RC-02 — State ↔ Git HEAD/checkpoint

The state `checkpoint.checkpoint_sha` is the durable checkpoint anchor. Its declared `checkpoint.mode` MUST define the accepted ancestry relation:

- `exact`: current HEAD MUST equal `checkpoint.checkpoint_sha`.
- `descendant`: current HEAD MUST be a descendant of `checkpoint.checkpoint_sha` and intervening commits MUST be reachable from that checkpoint.

Unexpected divergence => `RESUME_BLOCKED`.

The current HEAD MUST NOT be copied into the same state commit merely to make the check pass.

### RC-03 — State ↔ Audited baseline

`CURRENT_SESSION_STATE.audited_baseline_sha` MUST equal the audited baseline recorded by the active handoff/audit authority.

Mismatch => `RESUME_BLOCKED`.

### RC-04 — State ↔ Handoff

The handoff path declared by `CURRENT_SESSION_STATE.handoff` MUST exist and its declared repository, branch, and audited baseline MUST agree with the state.

Mismatch => `RESUME_BLOCKED`.

### RC-05 — Handoff ↔ Git

The active handoff repository/branch MUST agree with the actual Git repository and branch.

Mismatch => `RESUME_BLOCKED`.

### RC-06 — Handoff ↔ Audited baseline

The handoff MUST preserve the audited baseline identity and MUST NOT silently replace it with the current HEAD.

Mismatch => `RESUME_BLOCKED`.

### RC-07 — Gate ↔ Forbidden actions/constraints

The state gate and handoff constraints MUST agree.
For a gate of `NOT_GREEN`, `BLOCKED`, `HOLD`, or `INCONCLUSIVE`, the handoff MUST retain the governed downstream restrictions, including the prohibition on OPRO promotion and the prohibition on backtest/OOS/optimization/Monte Carlo before M1-B GREEN when those constraints are active.

A downstream action that violates a state or handoff constraint MUST NOT be executed.

Mismatch => `RESUME_BLOCKED`.

### RC-08 — Required context/evidence

The handoff and state MUST reference the active CER continuity contract and session-state schema, and those artifacts MUST exist and be version-compatible with the current repository.

Missing, stale, or incompatible required context => `RESUME_REVIEW_REQUIRED`.

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
CHECK RC-01..RC-08
  ↓
all PASS
  ├─ yes → RESUME_ALLOWED
  └─ no
       ├─ context/evidence ambiguity → RESUME_REVIEW_REQUIRED
       └─ identity / branch / baseline contradiction → RESUME_BLOCKED
```

`RESUME_ALLOWED` is required before execution of governed work.

## 5. State Precedence

When values disagree:

1. audited baseline identity and immutable evidence win over mutable session notes;
2. Git repository state is authoritative for actual branch/HEAD;
3. handoff is authoritative for declared next action and explicit constraints;
4. `CURRENT_SESSION_STATE` is authoritative for the current checkpoint only when it passes RC-01..RC-08;
5. conversational memory is lowest priority.

## 6. Checkpoint Rule

A session checkpoint MUST record:

- session identifier
- repository
- branch
- checkpoint commit SHA
- checkpoint mode (`exact` or `descendant`)
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

Every resume attempt SHOULD emit machine-readable results for RC-01..RC-08 with:

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
