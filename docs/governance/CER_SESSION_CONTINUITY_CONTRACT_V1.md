# CER Session Continuity Contract v1.1

**Status:** Active governance contract
**Repository:** `chayobi03-cyber/agent-factory`
**Scope:** Session continuity, checkpoint, resume, handoff, and closure control

## 1. Purpose

Session Continuity makes a work session independently resumable without relying on prior chat history as canonical state.

The governing principle is:

> Chat is working context. Session State is the continuation pointer. Git is canonical memory. Evidence Chain is the source of verified facts.

Session Continuity is a governance/control layer over existing CER and WorkflowRun concepts. It does not replace WorkflowRun, CER Snapshot, Evidence, Verification, or Audit Decision objects.

## 2. Canonical Artifacts

Every governed session may use the following artifacts:

- `docs/governance/CURRENT_SESSION_STATE.yaml` — compact machine-readable continuation pointer.
- `docs/governance/NEXT_SESSION_HANDOFF_*.md` — human-readable handoff context.
- Evidence manifests and raw evidence — verified execution facts.
- Git commit SHA — immutable checkpoint identity for the repository state.

The state file MUST remain small and pointer-oriented. Detailed narrative belongs in the handoff document or evidence artifacts.

## 3. Session State Contract

The canonical session state MUST contain enough information to identify the next safe action without replaying prior conversation history.

Minimum fields:

```yaml
state_version: 1
session_id: <id>
phase: <phase>
gate: <gate>
repository: chayobi03-cyber/agent-factory
working_branch: <branch>
audited_baseline_sha: <sha|null>
task_id: <id>
current_task: <task>
last_completed:
  - <step>
current_focus:
  - <focus>
next_action:
  - <action>
blocked_until:
  - <condition>
forbidden:
  - <action>
handoff: <path>
updated_at_utc: <timestamp>
```

The current Git HEAD MUST NOT be stored as a self-referential field in the same commit. Resume logic resolves the actual branch/HEAD directly from Git and compares it with the checkpoint identity and referenced baseline/handoff.

## 4. State Semantics

`CURRENT_SESSION_STATE.yaml` describes intent and continuation state, not proof of execution.

Therefore:

- `last_completed` is not execution evidence.
- `gate` is not an audit decision unless backed by the corresponding CER/Audit evidence.
- `next_action` is a workflow instruction, not a verification result.
- `audited_baseline_sha` identifies the system-under-audit and MUST NOT be silently replaced.

Expected, observed, verified, and decided values remain separate objects under the Evidence Chain contract.

## 5. Resume Contract — Three-Way Consistency Check

A new session MUST perform a resume consistency check before executing `next_action`.

The minimum invariant is a three-way consistency relationship:

```text
        CURRENT_SESSION_STATE
             ↕       ↕
      Git branch / HEAD
             ↕       ↕
    Audited baseline / Handoff
```

The three anchors are not interchangeable. The resume decision MUST validate all of them.

### RC-01 — State ↔ Git branch

`CURRENT_SESSION_STATE.working_branch` MUST equal the actual checked-out Git branch.

Mismatch => `RESUME_BLOCKED`.

### RC-02 — State ↔ Git checkpoint/HEAD

Resume logic MUST resolve the actual Git HEAD. The state MAY record a prior checkpoint SHA or checkpoint relation, but MUST NOT rely on a self-referential HEAD value.

Supported checkpoint relations:

- `exact`: actual HEAD equals the recorded checkpoint SHA.
- `descendant`: actual HEAD descends from the recorded checkpoint SHA and every intervening commit is explicitly acceptable under the active handoff.

Unexpected divergence, unknown ancestry, or an unapproved intervening change => `RESUME_BLOCKED` or `RESUME_REVIEW_REQUIRED`.

### RC-03 — State ↔ audited baseline

`CURRENT_SESSION_STATE.audited_baseline_sha` MUST equal the audited baseline declared by the active governance/handoff authority.

Mismatch => `RESUME_BLOCKED`.

### RC-04 — State ↔ handoff

The handoff referenced by `CURRENT_SESSION_STATE.handoff` MUST exist and agree with repository, branch, audited baseline, current phase, and applicable constraints.

Mismatch => `RESUME_BLOCKED`.

### RC-05 — Handoff ↔ Git

The active handoff MUST identify the same repository and branch as Git. Where the handoff records a checkpoint or expected commit relation, Git MUST satisfy that relation.

Mismatch => `RESUME_BLOCKED`.

### RC-06 — Handoff ↔ audited baseline

The handoff MUST preserve the audited baseline identity and MUST NOT infer a new baseline from the current HEAD.

Mismatch => `RESUME_BLOCKED`.

### RC-07 — Gate ↔ forbidden actions

State and handoff constraints MUST agree. A downstream action is prohibited when a mandatory gate is `HOLD`, `INCONCLUSIVE`, `BLOCKED`, or otherwise not GREEN.

Mismatch => `RESUME_BLOCKED`.

### RC-08 — Evidence context

Referenced CER, schema, audit, and evidence artifacts MUST exist and be version-compatible with the state/handoff before execution crosses a governed boundary.

Missing, stale, or conflicting required context => `RESUME_REVIEW_REQUIRED` or `RESUME_BLOCKED`.

## 6. Resume Decision Algorithm

```text
Load CURRENT_SESSION_STATE
  ↓
Resolve actual Git branch + HEAD
  ↓
Resolve active handoff
  ↓
Resolve audited baseline authority
  ↓
Run RC-01..RC-08
  ↓
ALL PASS
  ├─ yes → RESUME_ALLOWED
  └─ no
       ├─ recoverable ambiguity → RESUME_REVIEW_REQUIRED
       └─ identity / baseline / branch contradiction → RESUME_BLOCKED
```

`RESUME_ALLOWED` is required before executing the governed `next_action`.

## 7. State Precedence

When values disagree:

1. immutable audited baseline identity and verified evidence win over mutable session notes;
2. Git is authoritative for actual repository branch/HEAD;
3. the active handoff is authoritative for declared next action and explicit constraints;
4. `CURRENT_SESSION_STATE` is authoritative for the continuation pointer only after RC-01..RC-08 PASS;
5. conversational memory is lowest priority.

## 8. Context Loading Policy

Session restart MUST use progressive disclosure:

### Always load

- `CURRENT_SESSION_STATE.yaml`
- repository/project rules
- active CER continuity contract and snapshot references

### Load when required

- `NEXT_SESSION_HANDOFF_*.md`
- current evidence manifest
- relevant schemas
- relevant test/benchmark artifacts

### Do not automatically reload

- the complete prior conversation
- obsolete audit packages
- completed-step raw outputs unless referenced by current evidence

The repository and versioned runtime artifacts take precedence over model memory or unpinned narrative.

## 9. Checkpoint Contract

A checkpoint is a durable intermediate state transition.

The logical sequence is:

```text
Checkpoint requested
 → validate state
 → update CURRENT_SESSION_STATE
 → update required evidence references
 → inspect Git diff
 → commit checkpoint
```

A checkpoint MAY occur before task completion. A checkpoint MUST NOT claim PASS, GREEN, or completion without the evidence required by the corresponding gate.

## 10. Closure Contract

Session closure is a governed workflow and follows:

```text
Execute
 → Capture
 → Hash
 → Verify
 → Classify
 → CER CHECK
 → Audit Decision
 → Sign-off
 → Update State/Handoff
 → Git Commit
```

The closure gate remains fail-closed. Session closure cannot convert missing, stale, or inconclusive execution evidence into PASS.

## 11. WorkflowRun Relationship

Session Continuity and WorkflowRun are distinct:

- WorkflowRun records runtime execution state and replay lineage.
- Session State records the next safe continuation point across human/LLM sessions.
- `workflow_run.checkpoint_ref` MAY reference the corresponding session checkpoint or related state artifact.
- A Session State update does not itself constitute a new WorkflowRun.

## 12. Standard Session Triggers

### CER START

1. Resolve actual Git branch and HEAD.
2. Load `CURRENT_SESSION_STATE.yaml`.
3. Resolve active handoff and audited baseline.
4. Run RC-01..RC-08.
5. If `RESUME_ALLOWED`, load only the context required by `next_action`.
6. Execute `next_action`.

### CHECKPOINT

Persist the current continuation state and commit it without overstating verification status.

### CLOSE

Perform the governed closure workflow, update state/handoff, and create the final session checkpoint commit.

## 13. Failure Semantics

Automatic resume MUST stop when any of the following is detected:

- working branch mismatch
- unexpected Git ancestry or checkpoint divergence
- audited baseline mismatch
- missing or conflicting handoff
- missing required evidence/context
- unresolved mandatory HOLD/INCONCLUSIVE gate
- stale or conflicting versioned context
- forbidden action requested by the state

The correct disposition is `RESUME_REVIEW_REQUIRED` or `RESUME_BLOCKED`, depending on the CER policy.

## 14. Security and Integrity Principle

Git commit identity is the continuation anchor, but Git commit existence alone is not execution evidence. Execution claims require machine-generated evidence with the required command, commit SHA, timestamp, exit code, and result metadata.

Session Continuity MUST never be used to bypass CER gates, audit evidence requirements, or the OPRO/RE implementation constraints defined by the active governance baseline.

## 15. Acceptance Criteria

Session Continuity v1.1 is accepted when:

- state schema is versioned;
- a canonical state file exists;
- a human-readable handoff convention exists;
- the three-way resume invariant is explicit;
- RC-01..RC-08 are machine-checkable;
- checkpoint/close triggers are defined;
- WorkflowRun relationship is explicit;
- fail-closed resume behavior is defined;
- regression validates state structure and mismatch/forbidden handling.
