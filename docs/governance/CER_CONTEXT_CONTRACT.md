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

## 10. Governance Principle

CER is not merely a checklist. It is a versioned Context/Governance Control Plane for Agent Factory.
