# AgentFactory Optimization Method Control v1.0

**Status:** Active governance guidance
**Scope:** OPRO, GEPA, future optimization/evolution methods, and controlled promotion into the AgentFactory workflow

## 1. Purpose

Optimization is treated as a governed experiment class, not as an unrestricted implementation activity.

The method must remain replaceable while the control boundary remains stable.

Canonical principle:

> Stable evaluation/evidence gates; replaceable optimization methods.

OPRO, GEPA, or any future optimizer may change candidate-generation strategy without changing the evidence, benchmark, regression, audit, or promotion contracts.

## 2. Method-independent optimization boundary

Every optimization method MUST enter through the same boundary:

```text
Baseline
  -> Protected Evaluation
  -> Candidate Generation
  -> Candidate Evaluation
  -> Evidence Capture
  -> Verification
  -> Regression
  -> Decision
  -> Promotion / Reject / Hold
```

The optimizer is allowed to propose candidates. It is not allowed to redefine truth, evaluation criteria, protected cases, audit evidence, or promotion policy.

## 3. OPRO lessons promoted

### OPT-LSN-001 — Freeze the evaluation before optimizing

The benchmark/evaluation harness must be stable before optimization results are interpreted.

A changing evaluator makes candidate scores non-comparable.

### OPT-LSN-002 — Baseline identity and candidate identity are separate

The system-under-test baseline remains immutable while optimization produces candidate revisions.

Candidate improvement must never silently redefine the audited baseline.

### OPT-LSN-003 — Optimization output must be reproducible

Each candidate requires at minimum:

- parent/baseline identity;
- optimizer identity/version;
- evaluation configuration/version;
- protected benchmark identity;
- candidate patch/prompt/config identity;
- observed metrics;
- evidence references;
- decision.

### OPT-LSN-004 — Score is not proof

An optimizer score is an observed metric, not an audit conclusion.

Promotion requires the independent evidence/verification chain and protected regression gates.

## 4. GEPA lessons promoted

GEPA remains governed by the current release constraints until the Evidence Chain and prerequisite baselines are GREEN.

### OPT-LSN-005 — Separate search from structural change

GEPA-style optimization may propose broader prompt/instruction/program changes. Such proposals must be treated as candidate changes and must pass the same contract, benchmark, regression, provenance, and approval gates as ordinary engineering changes.

### OPT-LSN-006 — Preserve causal attribution

A candidate change should identify what changed and why the observed improvement is attributed to that change. Bundling unrelated changes into one candidate weakens diagnosis and rollback.

### OPT-LSN-007 — Protect against benchmark overfitting

Protected cases, holdout cases, and where relevant out-of-sample evaluation must remain outside the optimizer's mutable search objective.

### OPT-LSN-008 — Optimization must be interruptible and rollbackable

Long-running or adaptive optimization must persist checkpoints and candidate lineage so it can stop, resume, compare, or roll back without corrupting the baseline.

## 5. Flexible optimizer interface

Future optimization methods should implement a common logical interface rather than hard-code OPRO/GEPA into the kernel:

```text
OptimizerSpec
  id
  version
  objective_ref
  search_space_ref
  candidate_generator
  checkpoint_policy
  budget_policy
  evaluator_ref
  evidence_policy
  stop_policy
```

The runtime should expose method adapters:

```text
OPROAdapter
GEPAAdapter
FutureOptimizerAdapter
```

The adapters produce the same candidate/evaluation/evidence contract.

## 6. Experiment state machine

Optimization experiments should use a method-independent state machine:

```text
CREATED
 -> BASELINE_VERIFIED
 -> SEARCHING
 -> CANDIDATE_READY
 -> EVALUATING
 -> VERIFIED
 -> REGRESSION
 -> DECISION
      -> PROMOTE
      -> REJECT
      -> HOLD
      -> REVIEW
```

Failure, interruption, or budget exhaustion produces an explicit non-promotion state rather than an implicit success/failure assumption.

## 7. Gate hierarchy

Optimization is downstream of governance gates:

```text
Source / Data Integrity
        ↓
Evidence Chain GREEN
        ↓
Baseline GREEN / FROZEN
        ↓
Protected Evaluation GREEN
        ↓
Optimization
        ↓
Candidate Verification
        ↓
Regression
        ↓
Promotion Decision
```

No optimizer may bypass an upstream gate.

## 8. Promotion policy

A candidate may be promoted only when all applicable conditions are satisfied:

- baseline identity is preserved;
- candidate lineage is complete;
- evaluation configuration is pinned;
- protected regression is GREEN;
- evidence is machine-verifiable;
- observed results are distinct from expected values;
- verification is independently recorded;
- required human approval exists for high/critical risk;
- rollback identity is recorded.

## 9. Method selection policy

The optimizer is selected based on the problem, not on a permanent preference for one method.

Use the smallest method that can answer the experiment:

- controlled local prompt/config search → OPRO-class method;
- broader structural/program/prompt evolution → GEPA-class method;
- deterministic parameter search → non-LLM optimizer may be preferable;
- multi-objective or constrained search → use a method that explicitly represents those constraints.

Method changes do not justify changing the evaluation contract.

## 10. Experiment evidence contract

Every optimization run must preserve:

```yaml
experiment_id: <id>
parent_baseline_sha: <sha>
method_id: <method>
method_version: <version>
evaluator_id: <id>
evaluator_version: <version>
benchmark_id: <id>
search_space_hash: <hash>
budget:
  max_steps: <int>
  max_cost: <number|null>
  timeout_seconds: <int|null>
observed_results: <ref>
verification_results: <ref>
regression_results: <ref>
decision: PROMOTE|REJECT|HOLD|REVIEW
candidate_identity: <ref>
rollback_identity: <ref>
```

## 11. Required regression dimensions

Optimizer regression should measure more than a single aggregate score where applicable:

- protected benchmark correctness;
- evidence/provenance preservation;
- citation/locator validity;
- schema/contract conformance;
- latency/cost/budget guardrails;
- failure/abstention behavior;
- risk policy compliance;
- unintended regressions in neighboring capabilities.

## 12. Expansion rule

When a new optimization method is introduced, first add an adapter and evaluation fixture. Do not alter the kernel contract merely to accommodate the optimizer.

Required change sequence:

```text
Method proposal
 -> Impact analysis
 -> Adapter contract
 -> Offline fixture
 -> Protected benchmark
 -> Regression
 -> Evidence validation
 -> Human approval if required
 -> Runtime enablement
```

## 13. Current constraints

For the current AgentFactory audited baseline:

- GEPA implementation remains prohibited until the active evidence/release gates explicitly permit it.
- OPRO promotion remains prohibited until Audit Evidence Chain remediation and prerequisite baseline gates are GREEN.
- RE Domain implementation remains prohibited under the current remediation baseline.

This document records lessons and future method architecture; it does not override those constraints.
