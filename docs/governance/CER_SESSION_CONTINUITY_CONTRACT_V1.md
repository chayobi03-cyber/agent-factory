# CER Session Continuity Contract v1.0

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

The current Git HEAD MUST NOT be stored as a self-referential field in the same commit. Resume logic resolves the actual branch/HEAD directly from Git and compares it with any recorded audited baseline or referenced evidence identity.

## 4. State Semantics

`CURRENT_SESSION_STATE.yaml` describes intent and continuation state, not proof of execution.

Therefore:

- `last_completed` is not execution evidence.
- `gate` is not an audit decision unless backed by the corresponding CER/Audit evidence.
- `next_action` is a workflow instruction, not a verification result.
- `audited_baseline_sha` identifies the system-under-audit and MUST NOT be silently replaced.

Expected, observed, verified, and decided values remain separate objects under the Evidence Chain contract.

## 5. Resume Contract

A new session MUST perform a resume consistency check before executing `next_action`.

Minimum checks:

```text
Load CURRENT_SESSION_STATE
        ↓
Resolve actual Git branch and HEAD
        ↓
Validate audited baseline identity
        ↓
Resolve handoff path
        ↓
Validate referenced CER/evidence artifacts
        ↓
Check blocked_until / forbidden
        ↓
Execute next_action only when resume checks PASS
```

Any mismatch that can affect task identity, baseline identity, gate status, or evidence provenance MUST produce `REVIEW_REQUIRED` or `BLOCKED` rather than automatic continuation.

## 6. Context Loading Policy

Session restart MUST use progressive disclosure:

### Always load

- `CURRENT_SESSION_STATE.yaml`
- repository/project rules
- active CER contract and snapshot references

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

## 7. Checkpoint Contract

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

## 8. Closure Contract

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

## 9. WorkflowRun Relationship

Session Continuity and WorkflowRun are distinct:

- WorkflowRun records runtime execution state and replay lineage.
- Session State records the next safe continuation point across human/LLM sessions.
- `workflow_run.checkpoint_ref` MAY reference the corresponding session checkpoint or related state artifact.
- A Session State update does not itself constitute a new WorkflowRun.

## 10. Standard Session Triggers

The following operational triggers are defined:

### CER START

1. Resolve Git branch and HEAD.
2. Load `CURRENT_SESSION_STATE.yaml`.
3. Validate resume consistency.
4. Load only the required handoff/evidence context.
5. Evaluate current CER gate and constraints.
6. Execute `next_action`.

### CHECKPOINT

Persist the current continuation state and commit it without overstating verification status.

### CLOSE

Perform the governed closure workflow, update state/handoff, and create the final session checkpoint commit.

## 11. Failure Semantics

Automatic resume MUST stop when any of the following is detected:

- working branch mismatch
- audited baseline mismatch
- missing handoff referenced by state
- missing required evidence
- unresolved mandatory HOLD/INCONCLUSIVE gate
- stale or conflicting versioned context
- forbidden action requested by the state

The correct disposition is `REVIEW_REQUIRED` or `BLOCKED`, depending on the CER policy.

## 12. Security and Integrity Principle

Git commit identity is the continuation anchor, but Git commit existence alone is not execution evidence. Execution claims require machine-generated evidence with the required command, commit SHA, timestamp, exit code, and result metadata.

Session Continuity MUST never be used to bypass CER gates, audit evidence requirements, or the OPRO/RE implementation constraints defined by the active governance baseline.

## 13. Acceptance Criteria

Session Continuity v1.0 is accepted when:

- state schema is versioned;
- a canonical state file exists;
- a human-readable handoff convention exists;
- resume consistency rules are explicit;
- checkpoint/close triggers are defined;
- WorkflowRun relationship is explicit;
- fail-closed resume behavior is defined;
- regression validates state structure and forbidden/mismatch handling.
