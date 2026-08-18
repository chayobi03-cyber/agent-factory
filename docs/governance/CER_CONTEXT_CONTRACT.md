# CER Context Contract

## 1. Canonical Definition

CER (Continuous Engineering Review) is Agent Factory's versioned always-on engineering review policy. For every task or relevant change, the current CER snapshot evaluates Gap, Method, Risk, Evidence, Regression, and Learning, then converts findings into actionable updates to the task, workflow, architecture, knowledge, benchmark, or release baseline.

## 2. Three Layers

### CER Definition
Defines what CER is, its purpose, scope, principles, and terminology.

### CER Policy
Defines what checks run, triggers, severity, gates, and actions. Policies are versioned.

### CER Runtime Snapshot
Defines the exact CER policy frozen for a WorkflowRun. A run must not change CER policy mid-execution.

## 3. Context Priority

1. Current Run Context
2. Current CER Snapshot
3. Current Task
4. Current Project Baseline
5. Current Domain Pack
6. Source-of-Truth Repository
7. Historical Context
8. Model prior assumptions

Lower-priority context must never override a higher-priority versioned artifact.

## 4. Runtime Identity

Every run and agent handoff should carry:

```yaml
cer:
  policy_id: CER
  policy_version: 1.0.0
  snapshot_id: CER-SNAP-<run-id>
```

The same snapshot is used by all agents in a run unless a new run is explicitly created.

## 5. Required Review Dimensions

- GAP
- METHOD
- RISK
- EVIDENCE
- REGRESSION
- LEARNING

Context consistency is treated as part of Evidence/Regression governance and checks for stale versions, incompatible domain/workflow/schema versions, and conflicting historical context.

## 6. CER Change Lifecycle

```text
Current CER
 -> Change Proposal
 -> Impact Analysis
 -> Candidate Policy
 -> CER Benchmark
 -> Regression
 -> Approval
 -> Release
 -> New Runtime Snapshots
```

Changing CER must not silently alter an active WorkflowRun. Existing runs remain reproducible against their frozen snapshot.

## 7. Impact Analysis

CER changes must check impact on:

- schemas
- workflows
- agents
- Domain Packs
- benchmarks
- prompts/instructions
- reports/templates
- governance gates
- observability
- optimization experiments

## 8. External LLM Context Packet

External LLMs should receive a compact Context Packet rather than an uncontrolled copy of historical CER text.

```yaml
agent_factory_context:
  project:
    name: Agent Factory
    mission: domain-agnostic Meta-Agent Engineering Platform
  baseline:
    architecture: AF-ARCH-<version>
    schema: AF-SCHEMA-<version>
    workflow: AF-WF-<version>
    benchmark: AF-BENCH-<version>
  cer:
    policy_id: CER
    policy_version: <version>
    snapshot_id: <snapshot>
    mode: always_on
  task:
    task_id: <task>
    domain: <domain>
  source_of_truth:
    repository: chayobi03-cyber/agent-factory
    commit: <sha>
```

## 9. Handoff Contract

Agent-to-agent handoffs must preserve `task_id`, `parent_run_id`, CER policy version, snapshot ID, Domain Pack version, and required CER checks. Agents must not reinterpret CER from memory when a versioned snapshot is available.

Session-to-session continuation follows the same principle through the dedicated Session Continuity Contract. The machine-readable pointer is `docs/governance/CURRENT_SESSION_STATE.yaml`; detailed context belongs in the referenced `NEXT_SESSION_HANDOFF_*.md` document.

## 10. Session Continuity

Session Continuity is a governed control layer for resuming work across chats or execution environments without treating prior chat history as canonical state.

The canonical sequence is:

```text
CURRENT_SESSION_STATE
 -> Resolve Git branch/HEAD
 -> Validate baseline/evidence/context consistency
 -> Load required handoff/evidence only
 -> Check blocked_until / forbidden
 -> Execute next_action
```

Rules:

1. `CURRENT_SESSION_STATE.yaml` is a continuation pointer, not execution evidence.
2. Current Git HEAD is resolved directly from Git; it is not stored as a self-referential field in the same state commit.
3. `audited_baseline_sha` is immutable for the system-under-audit and cannot be silently replaced.
4. Branch, baseline, evidence, or version-context mismatches require `REVIEW_REQUIRED` or `BLOCKED`.
5. Session restart uses progressive disclosure: state first, then required handoff/evidence, not the complete prior conversation.
6. Checkpoint and closure operations must create durable Git state without overstating verification status.
7. Session Continuity cannot bypass CER gates, audit evidence requirements, or release/promotion constraints.

The full contract is defined in `docs/governance/CER_SESSION_CONTINUITY_CONTRACT_V1.md` and the schema in `schemas/session_state.schema.yaml`.

## 11. Session Closure CER

A work session is itself a governed workflow execution. Before declaring a session complete, the closure workflow must evaluate:

```text
Git State
 → Contract Reconciliation
 → Executable Verification
 → Evidence Capture
 → Lesson Review
 → Controlled Workflow Update
 → Regression
 → Closure Artifact
```

The closure gate is fail-closed.

Rules:

1. Source code inspection alone cannot satisfy executable verification.
2. A claimed execution result must have machine-generated evidence containing command, commit SHA, timestamp, exit code, and result summary.
3. Lessons must distinguish implemented/verified, implemented-but-unverified, conceptual gaps, and automation candidates.
4. Accepted lessons that change workflow behavior require an explicit controlled change and regression test.
5. Documentation-only execution evidence is insufficient for a release/closure gate.
6. If closure regression fails, the session cannot be considered closed.

## 12. Governance Principle

CER is not merely a checklist. It is a versioned Context/Governance Control Plane for Agent Factory.
