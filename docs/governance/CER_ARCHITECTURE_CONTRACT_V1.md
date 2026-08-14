# CER Architecture Contract v1.0

**Status:** Draft for implementation freeze  
**Repository:** `chayobi03-cyber/agent-factory`  
**Canonical source:** Git repository `main`  
**Scope:** AgentFactory CER control plane and its contracts

## 1. Purpose

This contract defines the minimum immutable architecture boundary required for CER (Continuous Engineering Review) to operate as an executable governance/control plane rather than as documentation or a checklist.

This contract does not implement the runtime. It defines the objects, invariants, lifecycle rules, gate semantics, and acceptance criteria that the runtime must satisfy.

## 2. Source of Truth

The live Git repository is the canonical Source of Truth for the current system baseline.

- Git repository: `chayobi03-cyber/agent-factory`
- Canonical working tree: `main`
- Current repository structure is canonical.
- Historical ZIP/design-package archives are snapshots, handover, and recovery artifacts only.
- Historical package paths must not override current Git paths unless an explicit mapping/versioned migration record says so.

## 3. Canonical Object Chain

```text
Document
  -> Revision
  -> Section / Fragment
  -> Evidence
  -> Claim
  -> Verification
  -> CER Decision
  -> Workflow Gate
  -> WorkflowRun
  -> AgentStep
  -> Trace
  -> Failure
  -> RootCause
  -> Lesson
  -> Experiment
  -> BenchmarkRun
  -> Regression
  -> Approval
  -> Release
```

## 4. Canonical Identity and Versioning

Every persistent object must have an immutable identity. Mutable attributes are represented through a new revision/version rather than destructive mutation.

Minimum runtime identity:

```yaml
repository:
  name: chayobi03-cyber/agent-factory
  commit: <resolved_commit_sha>

baseline:
  architecture_version: <version>
  schema_version: <version>
  workflow_version: <version>
  benchmark_version: <version>

task:
  task_id: <id>

run:
  run_id: <id>
  parent_run_id: <id|null>

cer:
  policy_id: CER
  policy_version: <version>
  snapshot_id: <immutable_snapshot_id>

domain_pack:
  id: <id>
  version: <version>
```

## 5. Document and Revision Contract

### Document

Represents source identity independent of a particular revision.

Required semantics:

- stable `document_id`
- source URI or source key
- source authority classification
- document type
- ownership/access metadata as applicable
- creation/registration timestamp

### Revision

Represents an immutable source state.

Required semantics:

- stable `revision_id`
- `document_id`
- source content hash
- parser/extraction version
- revision timestamp or effective date when available
- supersession relation
- validity status
- reproducibility metadata

A Revision must never be silently replaced in place.

## 6. Evidence Contract

Evidence is a first-class object, not merely an ID embedded inside a Claim.

Minimum semantics:

```yaml
evidence_id: <id>
document_id: <id>
revision_id: <id>
fragment_id: <id>
locator: <stable_locator>
page: <integer|null>
source_hash: <hash>
authority: <authority_class>
extraction_method: <method>
extraction_version: <version>
validity: active|superseded|rejected
```

Evidence must be traceable to an exact source revision and stable locator.

Evidence from an obsolete or superseded revision may remain historically valid, but cannot silently override evidence from a newer authoritative revision.

## 7. Claim Contract

Claim remains the unit of reasoning and decision.

Minimum semantics:

- `claim_id`
- statement
- claim type
- evidence references
- confidence
- conditions
- status
- provenance
- verification results

Production-grade factual claims require evidence lineage.

A Claim without sufficient supporting evidence must resolve to an explicit non-production state such as `candidate`, `rejected`, or `abstained`; it must not be promoted by confidence alone.

## 8. Verification Contract

Verification evaluates Claims independently of generation.

Minimum verification dimensions:

- structural validation
- evidence support
- domain-rule validation
- cross-method or cross-provider validation where risk requires it
- citation/locator validation
- revision validity

Verification results are immutable for a given run context. A new verification produces a new result/version.

## 9. CER Snapshot Contract

CER Definition, CER Policy, and CER Runtime Snapshot remain distinct layers.

A `CER Snapshot` is the exact policy state used by one WorkflowRun.

Invariants:

1. Snapshot is immutable after run start.
2. Every AgentStep inherits the same snapshot unless a new WorkflowRun is created.
3. Historical CER text cannot override the active snapshot.
4. A policy change creates a candidate version and future snapshots; it does not mutate an active run.
5. Snapshot resolution must be reproducible from the repository commit and resolved policy artifacts.

## 10. CER Decision Contract

The minimum decision set is:

```text
PASS
REVIEW
CHANGE
BLOCK
```

Decision semantics:

- `PASS`: required checks satisfied; workflow may continue.
- `REVIEW`: execution may not cross the governed boundary until required human review is completed.
- `CHANGE`: a contract/workflow/architecture/knowledge change is required; current execution path stops or returns to a controlled change path.
- `BLOCK`: the current execution path is terminated or held; downstream governed steps cannot execute.

Every decision must record:

- decision_id
- run_id
- gate/step
- CER snapshot
- triggering findings
- evidence/claims involved
- required actions
- human requirement
- timestamp

## 11. Workflow Gate Contract

Each governed workflow step must support:

```text
precondition
  -> CER pre-gate
  -> execution
  -> verification
  -> CER post-gate
  -> trace
```

A gate must be fail-closed for `BLOCK`.

Gate bypass through an alternate agent, retry path, or workflow branch is prohibited unless that path is explicitly defined as an approved exception and is itself governed.

## 12. WorkflowRun State Contract

A WorkflowRun must support at minimum:

```text
CREATED
RUNNING
WAITING
REVIEW_REQUIRED
RETRYING
BLOCKED
COMPLETED
FAILED
ABORTED
```

Required runtime properties:

- idempotency key
- checkpoint/state persistence
- retry semantics
- budget limits
- timeout behavior
- loop detection
- replayability
- parent-child run lineage
- immutable execution manifest

## 13. AgentStep Contract

Each AgentStep must record:

- step_id
- run_id
- step type
- input reference
- output reference
- tool references
- retrieval configuration
- evidence references
- errors
- start/end time
- CER decision context

## 14. Domain Pack Contract

Domain Pack is a runtime isolation boundary, not merely a YAML configuration.

The shared kernel must depend on stable capability interfaces, while domain-specific ontology, terminology, source policy, routing rules, verification rules, tools, and report templates remain in the Domain Pack.

Minimum capability boundary:

```text
ingest
parse
normalize
retrieve
verify
evaluate
render_report
```

Capabilities may be optional where the workflow does not require them, but the kernel must not contain hidden domain-specific branches.

## 15. Benchmark Contract

A benchmark case must be capable of expressing:

- source snapshot/version
- expected revision
- question/task
- expected evidence and locators
- gold claims
- forbidden claims
- abstention expectation
- expected CER decision where applicable
- evaluator version
- protected cases
- scoring rubric

Benchmark truth must be independent of the model being evaluated wherever practical.

Benchmark runs must themselves be versioned and reproducible.

## 16. Learning Loop Contract

The learning loop is:

```text
Trace
 -> Failure
 -> RootCause
 -> Lesson
 -> CandidateChange
 -> Experiment
 -> BenchmarkRun
 -> Regression
 -> Approval
 -> Release
```

Each object must maintain lineage to its source run and change proposal.

A Lesson is not a production change. Candidate changes require offline validation, regression checks, and governed release before affecting future runtime behavior.

## 17. HOTL Contract

Risk policy is executable and deterministic where possible.

Default policy:

| Risk | Default |
|---|---|
| Low | automatic + post-hoc audit |
| Medium | automatic + verification + sampling |
| High | human approval required |
| Critical | human decision mandatory |

High/Critical actions must produce explicit human review records when approval is required.

## 18. Provider / Tool Reproducibility

The execution manifest must preserve sufficient identity to reproduce a run:

- provider
- model identity/revision
- request configuration hash
- prompt/instruction version or hash
- toolset version
- parser version
- retriever configuration/version

Provider substitution must be explicit and auditable.

## 19. Context Packet Contract

External agents receive a compact, resolved Context Packet containing the current versioned baseline rather than uncontrolled historical text.

Before execution, placeholders must be resolved. The runtime Context Packet must therefore contain concrete:

- repository commit
- architecture version
- schema version
- workflow version
- benchmark version
- CER policy version
- CER snapshot ID
- task ID
- domain pack ID/version
- required CER checks

## 20. Source-of-Truth Policy

The canonical hierarchy is:

```text
Current Run Context
 > CER Snapshot
 > Task
 > Project Baseline
 > Domain Pack
 > Current Git Repository
 > Historical Archive
 > Model Prior
```

The repository is the canonical implementation baseline.

ZIP archives, exported packages, and prior design structures are historical artifacts unless explicitly promoted through a versioned migration decision.

## 21. Release Gates

No architecture/runtime release may pass unless at minimum:

1. unsupported critical claims are blocked;
2. citation/provenance roundtrip passes;
3. revision/supersession handling passes;
4. CER snapshot is reproducible;
5. `BLOCK` cannot be bypassed;
6. high-risk actions have the required HOTL path;
7. protected regression cases do not degrade;
8. WorkflowRun trace is complete;
9. Domain Pack can be swapped without kernel modification for the tested capability set.

## 22. Contract Freeze Criteria

CER Architecture Contract v1.0 may be marked `FROZEN` only when:

- canonical Git source-of-truth mapping is current;
- Document/Revision/Evidence/Claim relationships are schema-valid;
- CER Snapshot is represented in WorkflowRun/Trace;
- workflow gate semantics are executable;
- Domain Pack interface is explicit;
- benchmark cases can validate CER decisions and protected regressions;
- replay/idempotency/loop/budget requirements have implementation tests;
- internal and external audit findings have been reconciled or explicitly documented as disputed.

## 23. Non-goals for v1.0

This contract does not require:

- mandatory GraphRAG;
- mandatory multi-agent execution;
- autonomous production self-modification;
- autonomous certification/compliance decisions;
- direct equipment control;
- a specific workflow/RAG framework.

## 24. Versioning Rule

This document is a versioned architecture contract. Changes affecting object identity, lifecycle, gate semantics, or reproducibility require a new contract version and impact analysis.
