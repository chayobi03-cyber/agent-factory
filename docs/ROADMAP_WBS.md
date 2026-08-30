# Roadmap / WBS — Agent Factory v0.1

## Priority Model
- P0: foundation / architecture contracts + Factory kernel runtime verification
- P1: RE baseline runtime after Factory kernel GREEN
- P2: agentic + method ensemble + lesson loop
- P3: optimization and additional domains
- P4: domain onboarding factory

## Optimization Principles
Optimization is **not allowed to bypass CER, Evidence/Claim verification, HOTL, Trace, or Regression**.

- **OPRO (Optimization by PROmpting):** prompt-level iterative optimization using benchmark feedback. Candidate prompts are versioned, evaluated offline, and promoted only through the normal CER/release gates.
- **GEPA (Genetic-Pareto / evolutionary prompt optimization):** multi-objective evolutionary optimization of prompts, workflow instructions, or agent policies. Candidate populations, mutations, evaluations, Pareto fronts, and selected releases must be traceable and reproducible.
- Both optimizers are optimization engines, not governance engines. They may propose changes; they cannot directly release changes or override a CER BLOCK.
- Optimizer evaluation must use deterministic benchmark ground truth where available. LLM-as-judge may be an auxiliary signal only and is never the sole release criterion.

## Milestones
### M0 Foundation
Canonical Document Model, Claim/Evidence, Domain Pack, Trace, Benchmark schemas, CER Control Plane, HOTL, Factory Demo, and session-closure CER.

### M0.5 Factory Kernel Verification
FactoryRuntime, executable CER gates, HOTL review queue, run manifest, replay/idempotency/loop controls, and PASS/REVIEW/BLOCK Golden Paths.

### M1 RE Hybrid RAG
Legacy ingestion → parser → hybrid retrieval → evidence → grounded QA. Starts only after M0.5 Factory Kernel GREEN.

### M2 RE Engineering Agent
Hypothesis/counter-hypothesis, evidence verification, diagnosis workflow.

### M3 Reporting
Evidence-first report generation, citation audit, technical audit.

### M4 Agentic RAG
Planner/iterative retrieval/tool use for complex queries.

### M5 Method Ensemble
Vector vs hybrid vs graph vs agentic comparison and arbitration.

Multi-provider comparison lands here, moved from the RE PoC target list on
2026-08-30 (OPEN_DECISIONS D-16). A hosted model API is permanently excluded
(D-12 option C), so "2 model providers minimum" was unreachable as a PoC
acceptance target by the route anyone would take. Comparing providers is a
method-ensemble question, and M5 is where method comparison and arbitration
already live. Provider neutrality stays an architecture principle
(`docs/MDD.md`); what M5 owes is a demonstration that the adapter boundary
holds, which the provider-free PoC does not make.

### M6 EMI/RFI
Reuse kernel; create Domain Packs and benchmark suites.

### M7 CST
Simulation/tool adapter, result parsing and evidence integration.

### M8 Optimization
Optimization substrate → OPRO prompt optimization → GEPA evolutionary/Pareto optimization → workflow optimization. M8 is gated by Factory Kernel GREEN, benchmark reproducibility, trace completeness, and regression protection.

### M9 Domain Factory
Automated domain discovery → pack candidate → benchmark candidate → validation → release.

## WBS
| ID | Task | Priority | Dependency | Acceptance |
|---|---|---|---|---|
| AF-001 | Canonical document model | P0 | - | schema approved |
| AF-002 | Claim/Evidence model | P0 | AF-001 | provenance roundtrip |
| AF-003 | Trace model | P0 | - | 100% trace completeness |
| AF-004 | Domain Pack | P0 | AF-001 | kernel loads Demo pack without code fork |
| AF-005 | Benchmark harness | P0 | AF-002,003 | reproducible run with execution evidence |
| AF-006 | FactoryRuntime | P0 | AF-002,003,004 | end-to-end run manifest |
| AF-007 | CER Gate enforcement | P0 | AF-006 | PASS/REVIEW/BLOCK E2E |
| AF-008 | HOTL controller | P0 | AF-007 | REVIEW requires HumanDecision |
| AF-009 | Session closure CER | P0 | AF-005,007,008 | closure workflow + regression |
| AF-010 | Factory Kernel GREEN gate | P0 | AF-006..009 | no unresolved critical P0 |
| AF-011 | Legacy parser baseline | P1 | AF-010 | parsing benchmark |
| AF-012 | Hybrid retriever | P1 | AF-011 | retrieval benchmark |
| AF-013 | Evidence verifier | P1 | AF-002,012 | claim-evidence audit |
| AF-014 | RE QA workflow | P1 | AF-004,012,013 | RE benchmark pass |
| AF-015 | RE diagnosis workflow | P1 | AF-014 | diagnosis benchmark |
| AF-016 | Report engine | P1 | AF-013 | citation/technical audit |
| AF-017 | Method ensemble | P2 | AF-005,012 | method comparison |
| AF-018 | Agentic retrieval | P2 | AF-012,013 | complex-case lift |
| AF-019 | Lesson engine | P2 | AF-003,008 | feedback capture |
| AF-020 | Optimization substrate | P3 | AF-005,007,008,009 | frozen benchmark + objective vector + candidate/experiment lineage |
| AF-020A | Optimization Benchmark Contract | P3 | AF-005,007,009 | immutable benchmark snapshot and deterministic ground truth contract |
| AF-020B | Objective Vector Engine | P3 | AF-020A | versioned multi-objective vector with direction/normalization and Pareto comparison |
| AF-020C | Candidate Registry | P3 | AF-020A | immutable candidate provenance/parent lineage |
| AF-020D | Experiment Registry | P3 | AF-020B,020C | candidate→benchmark→run→objective→regression lineage |
| AF-020E | OPRO optimizer adapter | P3 | AF-020D | prompt candidates improve protected benchmark without regression |
| AF-020F | GEPA optimizer adapter | P3 | AF-020E | evolutionary candidates + Pareto front are reproducible and traceable |
| AF-020G | Optimizer promotion gate | P3 | AF-020D,AF-007,AF-010 | optimizer cannot bypass CER/HOTL/BLOCK/regression |
| AF-021 | Workflow optimizer | P3 | AF-020G | Pareto improvement |
| AF-022 | EMI/RFI packs | P3 | AF-004,010 | kernel reuse |
| AF-023 | CST adapter | P3 | AF-004,002 | tool smoke test |
| AF-024 | Domain onboarding factory | P4 | AF-022 | new domain PoC |

## Optimization Implementation Sequence

```text
AF-020A Optimization Benchmark Contract
        ↓
AF-020B Objective Vector Engine
        ↓
AF-020C Candidate Registry
        ↓
AF-020D Experiment Registry
        ↓
AF-020E OPRO Adapter
        ↓
AF-020F GEPA Adapter
        ↓
AF-020G Promotion Gate
        ↓
Workflow Optimization
```

### Phase O0 — Optimization Contract
Define the optimizer interface, candidate representation, objective schema, benchmark binding, budget, stopping criteria, and promotion policy.

### Phase O1 — Objective Substrate
Implement deterministic objective normalization, direction handling, objective-vector hashing, and Pareto dominance comparison.

### Phase O2 — Candidate / Experiment Registry
Persist immutable candidate and experiment lineage. Each experiment binds one candidate to one frozen benchmark snapshot and records optimizer configuration, execution manifest references, objective results, regression state, and promotion status.

### Phase O3 — OPRO
Use OPRO first for controlled prompt search because it provides a simpler baseline for measuring whether iterative prompt optimization produces reproducible benchmark gains.

Required evidence per experiment:
- baseline prompt/version
- candidate prompt/version
- benchmark version
- objective values
- execution command
- model/configuration
- commit SHA
- timestamp
- stdout/stderr
- selected candidate and rejection reasons

### Phase O4 — GEPA
Introduce GEPA after OPRO has established the optimizer harness and protected benchmark protocol. GEPA can explore larger candidate spaces and optimize multiple objectives simultaneously.

Required evidence per generation:
- population identifier
- parent candidate(s)
- mutation/operator
- candidate hash
- benchmark results
- objective vector
- Pareto-front membership
- selection decision
- lineage

### Phase O5 — Optimizer Comparison
Run OPRO and GEPA against the same frozen benchmark and baseline. Compare:
- quality gain
- regression rate
- token/cost budget
- experiment count
- stability across seeds/runs
- Pareto efficiency
- trace completeness
- reproducibility

### Phase O6 — Controlled Promotion
An optimizer output becomes a **CandidateChange**, not an automatic release.

```text
Benchmark
  → Baseline
  → OPRO / GEPA
  → CandidateChange
  → Evaluation
  → Regression
  → CER Gate
  → HOTL when required
  → Approval
  → Release
```

A CER `BLOCK` always remains terminal. Neither OPRO nor GEPA may override it.

## Release Gates
1. No unsupported critical claim.
2. Citation/provenance roundtrip passes.
3. Revision/supersession handling passes.
4. CER snapshot is reproducible.
5. BLOCK cannot be bypassed.
6. High-risk workflow has executable HOTL path.
7. Protected regression cases do not degrade.
8. Trace and run manifest are complete.
9. Domain Pack can be changed independently of kernel for tested capabilities.
10. Session closure CER passes with machine-generated execution evidence.
11. Factory Kernel GREEN is required before RE Domain onboarding.
12. Optimizer outputs cannot bypass CER, HOTL, BLOCK, or regression gates.
13. OPRO/GEPA promotion requires reproducible benchmark evidence and complete candidate lineage.
