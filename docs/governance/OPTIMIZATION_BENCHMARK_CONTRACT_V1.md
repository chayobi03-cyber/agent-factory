# Optimization Benchmark Contract v1.0

**Status:** Draft for implementation freeze
**Scope:** Optimization experiments performed against the Agent Factory Kernel
**Source of Truth:** Git repository + frozen benchmark snapshot

## 1. Purpose

This contract defines the executable boundary between benchmark evaluation and optimizer-generated changes. It makes optimization reproducible, traceable, and subordinate to CER governance.

## 2. Core Rule

An optimizer may propose a `CandidateChange`; it may not directly mutate the production kernel, CER policy, benchmark ground truth, or release baseline.

Required lifecycle:

```text
Benchmark Snapshot
  -> Experiment
  -> Candidate
  -> Execution
  -> Evaluation
  -> Objective Vector
  -> Regression
  -> CER Gate
  -> Approval
  -> Release
```

## 3. Benchmark Snapshot

Every optimization experiment resolves a frozen benchmark snapshot containing:

- benchmark_id
- benchmark_version
- repository_commit
- CER policy version
- CER snapshot identity where applicable
- protected case identifiers
- evaluator version
- objective specification version

The snapshot is immutable for the experiment.

## 4. Benchmark Case

A case must contain enough information to reproduce evaluation:

- case_id
- task/input reference
- preconditions
- expected behavior or expected decision
- expected state where applicable
- forbidden outcomes/transitions
- evidence requirements
- trace requirements
- evaluator reference
- protected flag

Ground truth must be independent of the optimizer output. An LLM judge may provide a secondary signal but cannot define protected ground truth.

## 5. Candidate Change

A candidate is an immutable proposed change with:

- candidate_id
- parent_candidate_id
- change_type
- payload/reference to changed prompt, parameter, workflow fragment, or adapter configuration
- generator identity
- generator version
- provenance
- creation timestamp

Kernel governance, CER gate semantics, and protected benchmark truth are not optimizer-owned change types.

## 6. Experiment

An Experiment binds a candidate to exactly one frozen benchmark snapshot and records:

- experiment_id
- candidate_id
- benchmark_snapshot_id
- optimizer identity/version
- run configuration hash
- start/end timestamp
- execution manifest references
- raw evaluation result references
- objective vector reference
- regression result
- promotion status

An experiment is immutable after completion.

## 7. Objective Evaluation

Evaluation produces named objective values rather than a single opaque score. The default objective vector is:

```text
quality
evidence_support
regression_safety
latency
cost
human_intervention
trace_completeness
reproducibility
```

Each objective declares direction (`maximize` or `minimize`) and normalization policy.

## 8. Promotion Rules

A candidate cannot be promoted when:

- a protected benchmark regresses;
- CER returns BLOCK;
- required evidence is missing;
- execution evidence is not machine-generated;
- reproducibility requirements fail;
- candidate provenance is incomplete.

Pareto-optimal does not imply releasable.

## 9. Optimizer Boundary

Supported optimizer classes may include OPRO and GEPA. Both are candidate generators/search strategies only.

```text
OPRO / GEPA
   -> CandidateChange
   -> Experiment
   -> Benchmark
   -> Objective Vector
   -> Regression
   -> CER
   -> HOTL/Approval
   -> Release
```

## 10. Lineage

Every promoted artifact must be traceable to:

`candidate -> experiment -> benchmark snapshot -> workflow run(s) -> trace -> evidence -> evaluation -> regression -> approval -> release`

## 11. Versioning

Changes to benchmark truth, objective semantics, promotion rules, or candidate identity require a new contract or versioned impact analysis. Active experiments never change benchmark semantics in place.
