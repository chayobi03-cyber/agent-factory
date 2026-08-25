# CER Session Closure — 2026-08-18 Optimization Lessons

## 1. Session disposition

This session reviewed and consolidated lessons from the AgentFactory OPRO baseline work, the current GEPA restriction, and the newly established Session Continuity control.

The purpose was not to execute a new OPRO/GEPA optimization run. The purpose was to convert prior experience into reusable governance rules and a method-independent optimization workflow.

Current disposition:

- Audit Evidence Chain: NOT GREEN.
- Audited OPRO baseline SHA remains immutable: `20a54b92aad0857f75c6200d984b13098c6f4927`.
- OPRO promotion: FORBIDDEN until the applicable evidence/baseline gates are GREEN.
- GEPA implementation: FORBIDDEN until the applicable evidence/release gates are GREEN.
- M1-B financial-data gate: NOT GREEN.
- Backtest/OOS/optimization/Monte Carlo remain downstream of the M1-B gate for the current financial workflow.

## 2. OPRO lessons

### OPT-LSN-001 — Evaluator first, optimizer second

An optimizer is only meaningful against a stable, protected evaluator. Evaluation drift invalidates candidate comparison.

### OPT-LSN-002 — Baseline identity must be immutable

The audited implementation baseline and optimization candidates are different identities. Optimization must never redefine the system-under-audit commit.

### OPT-LSN-003 — Candidate lineage is mandatory

Every candidate must be traceable to its parent baseline, method/version, evaluator, benchmark, configuration, observed result, verification result, and final decision.

### OPT-LSN-004 — Metric improvement is not evidence of correctness

A higher optimizer score is an observed metric. Promotion requires evidence lineage, independent verification, protected regression, and the applicable CER/audit gates.

## 3. GEPA lessons

### OPT-LSN-005 — Structural search requires stronger change isolation

Broader prompt/instruction/program evolution can produce larger behavioral changes. Candidate changes must be isolated, attributable, reviewable, and rollbackable.

### OPT-LSN-006 — Protect against optimizer feedback loops

The optimizer must not be allowed to redefine its own truth source, protected cases, or promotion criteria.

### OPT-LSN-007 — Holdout/protected evaluation must remain outside mutable optimization intent

Protected and holdout evaluation must be version-pinned and unavailable for mutation through the candidate-generation mechanism.

### OPT-LSN-008 — Long-running optimization needs durable checkpoints

Search interruption must not destroy lineage or baseline integrity. Optimizer state and candidate checkpoints must support resume/reject/rollback.

## 4. Lessons from applying these ideas to AgentFactory governance

### OPT-LSN-009 — Method should be replaceable, control should be stable

Do not encode OPRO or GEPA semantics into the core CER contract. Use method adapters over a common candidate/evaluation/evidence interface.

### OPT-LSN-010 — Optimization belongs downstream of evidence and evaluation gates

The ordering is:

```text
Data/Source Integrity
 -> Evidence Chain GREEN
 -> Baseline VERIFIED/FROZEN
 -> Protected Evaluation GREEN
 -> Optimization
 -> Candidate Verification
 -> Regression
 -> Decision
 -> Promotion
```

### OPT-LSN-011 — Use the smallest sufficient optimization method

Choose the optimization family based on the problem class rather than permanently preferring one method. Deterministic search, OPRO-class search, GEPA-class search, or a future optimizer are interchangeable at the governance boundary.

### OPT-LSN-012 — Keep task-specific heuristics out of global governance

Provider rankings, one-off thresholds, and domain-specific implementation details belong in task/domain artifacts unless repeated evidence demonstrates that they should become a global control.

## 5. Governance rules strengthened

The following are promoted as reusable rules:

1. Optimization cannot bypass CER, evidence, benchmark, regression, or audit gates.
2. Evaluation contracts are method-independent and protected from optimizer mutation.
3. Baseline SHA and candidate identity are always separated.
4. Candidate lineage must be machine-addressable.
5. Observed metrics never substitute for verification or audit decision.
6. Every new optimizer enters through an adapter plus offline/protected regression fixture.
7. Optimization changes must be checkpointable, interruptible, reproducible, and rollbackable.
8. Protected evaluation must be isolated from mutable search intent.
9. Method selection is experiment-specific; governance controls are reusable.
10. A new method must not require kernel contract changes unless an explicit impact analysis proves that the existing abstraction is insufficient.

## 6. Method-independent optimization workflow

The target workflow is now:

```text
Experiment Request
 -> Scope / Risk Classification
 -> Resume Validation
 -> Baseline Resolution
 -> Evaluation Lock
 -> Protected Benchmark Lock
 -> Optimizer Selection
 -> Candidate Generation
 -> Candidate Evaluation
 -> Evidence Capture
 -> Independent Verification
 -> Protected Regression
 -> CER Decision
 -> Human Review when required
 -> Promotion / Reject / Hold / Review
 -> Checkpoint / Rollback identity
 -> Experiment Closure
```

## 7. Extension model

Future optimization methods should provide an adapter around the common contract:

```text
OptimizerSpec
  id
  version
  objective_ref
  search_space_ref
  checkpoint_policy
  budget_policy
  evaluator_ref
  evidence_policy
  stop_policy
```

The core runtime should consume candidate/evaluation/evidence objects rather than optimizer-specific internals.

## 8. Lessons classified by implementation status

### Implemented / verified in governance

- Session Continuity contract v1.1.
- CURRENT_SESSION_STATE machine pointer.
- RC-01..RC-08 validator and regression structure.
- Progressive-disclosure resume policy.
- Method-independent optimization control contract.

### Implemented but execution verification still pending

- Current continuity CI integration.
- End-to-end RC-01..RC-08 execution result on the active branch.

### Conceptual / future implementation

- OPRO adapter under the common optimizer interface.
- GEPA adapter under the common optimizer interface.
- Protected benchmark service.
- Generic optimization experiment manifest.
- Candidate lineage/rollback runtime.

## 9. Next-session workflow plan

Priority order:

P0 — Resume and Evidence

1. CER START.
2. Resolve Git branch/HEAD and validate RC-01..RC-08.
3. Inspect latest CI workflow run and capture raw machine evidence.
4. Reconcile the current Audit Evidence Chain findings.

P1 — Financial M1-B gate

5. Finalize the minimum financial source stack against the defined evaluation axes.
6. Select five real historical series.
7. Ingest raw data with provenance, timestamps, source identity, hashes, and reproducibility metadata.
8. Cross-reconcile sources and construct machine-verifiable evidence.
9. Determine M1-B GREEN / NOT GREEN.

P2 — Baseline/evaluation readiness

10. Only after required evidence gates are GREEN, freeze the protected evaluation contract.
11. Establish protected benchmark cases, holdout policy, budget, and regression criteria.
12. Define OPRO adapter fixture without changing the kernel contract.

P3 — Controlled OPRO

13. Run a bounded OPRO experiment against the protected evaluator.
14. Capture complete candidate/evaluation/evidence lineage.
15. Verify protected regression and decide PROMOTE/REJECT/HOLD/REVIEW.
16. Freeze the resulting baseline only through the explicit promotion gate.

P4 — GEPA readiness, not automatic execution

17. Evaluate whether the remaining optimization problem actually requires GEPA-class structural search.
18. If justified and gates permit, create a GEPA adapter fixture and compare it against the same evaluator/protected benchmark.
19. Preserve OPRO as a baseline method rather than assuming GEPA is superior.

## 10. Session closure decision

The session is closed with Audit Evidence Chain status still `NOT_GREEN`. No OPRO promotion or GEPA implementation is authorized by this closure.

The durable objective for the next session is to complete the evidence/resume gate first, then make financial M1-B data trustworthy, then construct a protected optimization boundary that can accept OPRO, GEPA, or future methods without changing the core governance contract.
