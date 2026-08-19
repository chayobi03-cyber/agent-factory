# Roadmap / WBS — Agent Factory v0.1

## Strategic scope

Agent Factory is a **domain-agnostic engineering agent platform**. The first real domain is RE (Radiated Emission); subsequent domains are onboarded through Domain Packs.

Financial-data ingestion, financial backtesting, portfolio analysis, and investment optimization are not core roadmap items. Domain-specific experiments must remain isolated unless a versioned architecture decision promotes a reusable capability into the kernel.

Authoritative scope: `docs/governance/AGENT_FACTORY_SCOPE_V1.md`.

## Priority Model
- P0: foundation / architecture contracts + Factory kernel runtime verification
- P1: RE baseline runtime after Factory kernel GREEN
- P2: agentic + method ensemble + lesson loop
- P3: optimization and additional engineering domains
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
Legacy engineering ingestion → parser → hybrid retrieval → evidence → grounded QA. Starts only after M0.5 Factory Kernel GREEN.

### M2 RE Engineering Agent
Hypothesis/counter-hypothesis, evidence verification, diagnosis workflow.

### M3 Engineering Reporting
Evidence-first report generation, citation audit, technical audit.

### M4 Agentic Engineering RAG
Planner/iterative retrieval/tool use for complex engineering queries.

### M5 Method Ensemble
Vector vs hybrid vs graph vs agentic comparison and arbitration.

### M6 EMI/RFI
Reuse kernel; create Domain Packs and benchmark suites.

### M7 CST / Simulation
Simulation/tool adapters, result parsing, and evidence integration.

### M8 Optimization
Generic optimization substrate → OPRO prompt optimization → GEPA evolutionary/Pareto optimization → workflow optimization. M8 is gated by Factory Kernel GREEN, benchmark reproducibility, trace completeness, and regression protection.

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
| AF-011 | Engineering document ingestion baseline | P1 | AF-010 | parsing benchmark |
| AF-012 | Hybrid retriever | P1 | AF-011 | retrieval benchmark |
| AF-013 | Evidence verifier | P1 | AF-002,012 | claim-evidence audit |
| AF-014 | RE QA workflow | P1 | AF-004,012,013 | RE benchmark pass |
| AF-015 | RE diagnosis workflow | P1 | AF-014 | diagnosis benchmark |
| AF-016 | Engineering report engine | P1 | AF-013 | citation/technical audit |
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
14. Application-specific experiments do not become core requirements without a versioned architecture decision.
