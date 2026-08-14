# Roadmap / WBS — Agent Factory v0.1

## Priority Model
- P0: foundation / architecture contracts
- P1: RE baseline runtime
- P2: agentic + method ensemble + lesson loop
- P3: optimization and additional domains
- P4: domain onboarding factory

## Milestones
### M0 Foundation
Canonical Document Model, Claim/Evidence, Domain Pack, Trace, Benchmark schemas.

### M1 RE Hybrid RAG
Legacy ingestion → parser → hybrid retrieval → evidence → grounded QA.

### M2 RE Engineering Agent
Hypothesis/counter-hypothesis, evidence verification, diagnosis workflow.

### M3 Reporting
Evidence-first report generation, citation audit, technical audit.

### M4 Agentic RAG
Planner/iterative retrieval/tool use for complex queries.

### M5 Method Ensemble
Vector vs hybrid vs graph vs agentic comparison and arbitration.

### M6 EMI/RFI
Reuse kernel; create Domain Packs and benchmark suites.

### M7 CST
Simulation/tool adapter, result parsing and evidence integration.

### M8 Optimization
GEPA/MIPROv2/OPRO adapters, A/B and Pareto evaluation.

### M9 Domain Factory
Automated domain discovery → pack candidate → benchmark candidate → validation → release.

## WBS
| ID | Task | Priority | Dependency | Acceptance |
|---|---|---|---|---|
| AF-001 | Canonical document model | P0 | - | schema approved |
| AF-002 | Claim/Evidence model | P0 | AF-001 | provenance roundtrip |
| AF-003 | Trace model | P0 | - | 100% trace completeness |
| AF-004 | Domain Pack | P0 | AF-001 | kernel loads RE pack without code fork |
| AF-005 | Benchmark harness | P0 | AF-002,003 | reproducible run |
| AF-006 | Legacy parser baseline | P1 | AF-001 | parsing benchmark |
| AF-007 | Hybrid retriever | P1 | AF-001 | retrieval benchmark |
| AF-008 | Evidence verifier | P1 | AF-002,007 | claim-evidence audit |
| AF-009 | RE QA workflow | P1 | AF-004,007,008 | RE benchmark pass |
| AF-010 | RE diagnosis workflow | P1 | AF-009 | diagnosis benchmark |
| AF-011 | Report engine | P1 | AF-008 | citation/technical audit |
| AF-012 | HOTL controller | P1 | AF-003,010 | risk routing |
| AF-013 | Method ensemble | P2 | AF-005,007 | method comparison |
| AF-014 | Agentic retrieval | P2 | AF-007,008 | complex-case lift |
| AF-015 | Lesson engine | P2 | AF-003,012 | feedback capture |
| AF-016 | Optimizer harness | P3 | AF-012,015 | offline improvement |
| AF-017 | Workflow optimizer | P3 | AF-016 | Pareto improvement |
| AF-018 | EMI/RFI packs | P3 | AF-004 | kernel reuse |
| AF-019 | CST adapter | P3 | AF-004,002 | tool smoke test |
| AF-020 | Domain onboarding factory | P4 | AF-018 | new domain PoC |

## Release Gates
1. No unsupported critical claim.
2. Citation/provenance roundtrip passes.
3. Regression benchmark does not degrade protected cases.
4. High-risk workflow has HOTL path.
5. Trace is complete.
6. Domain Pack can be changed independently of kernel.
