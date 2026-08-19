# Agent Factory v0.1

Domain-Agnostic Agent Factory for **engineering knowledge, RAG, agentic workflows, evidence-grounded answers/reports, Human-on-the-Loop, benchmarking, and controlled continuous improvement**.

## Product Mission

Agent Factory is not a vertical financial-analysis product. It is a reusable engineering-agent platform.

The platform must prove that one shared Factory Kernel can execute the same governed workflow across multiple domains while domain knowledge remains isolated behind Domain Pack interfaces.

Initial validation therefore uses **synthetic domain knowledge** across multiple representative domains. The first real domain implementation remains RE (Radiated Emission), followed by EMI/EMC, RFI, CST MWS, ESD, and additional engineering domains through Domain Packs.

See `docs/governance/AGENT_FACTORY_SCOPE_V1.md` for the canonical scope and non-goals.

## Factory Kernel

The shared kernel provides the generic control path:

```text
Task
 → CER Snapshot
 → WorkflowRun
 → AgentStep
 → Tool / Retrieval
 → Evidence / Claim
 → Verification
 → CER Gate
 → PASS / REVIEW / CHANGE / BLOCK
 → Human Decision when required
 → Trace
 → Benchmark / Regression
 → Release
```

The kernel must remain domain-neutral. Engineering-specific ontology, parsing rules, retrieval policy, verification rules, tools, and report templates belong in Domain Packs.

## Synthetic Domain Matrix

Before live domain ingestion, the same kernel workflow is exercised against synthetic Domain Packs for:

- RE
- EMI
- CST
- ESD

The fixture knowledge is intentionally dummy data. The acceptance target is workflow and architecture reuse, not domain accuracy.

```bash
python3 scripts/domain_matrix_demo.py --json
```

The matrix verifies that each domain can be loaded, routed through retrieval/evidence/claim verification, evaluated by the same CER gate, and represented in trace without kernel-specific branches.

## Factory Demo

The executable golden-path demo uses synthetic engineering evidence. It validates the shared factory control path without requiring a live domain implementation.

```bash
python3 scripts/factory_demo.py --scenario all
python3 scripts/factory_demo.py --scenario all --json
```

## Architecture Principles

1. Agent Kernel / Domain Pack separation
2. Evidence-first answers and reports
3. Adaptive retrieval: BM25 / Vector / Hybrid / Graph / Agentic
4. Multi-method comparison and arbitration
5. Layered verification: structural → evidence → domain rules → cross-method
6. Risk-based Human-on-the-Loop
7. Trace → Failure → Lesson → Candidate Change → Evaluation → Release
8. Agent CI/CD and regression testing
9. Domain onboarding without modifying the kernel
10. Generic evidence provenance independent of any one application domain
11. Synthetic multi-domain workflow validation before live domain complexity

## Current Roadmap Focus

```text
Factory Kernel GREEN
    ↓
Synthetic Multi-Domain Matrix
    ↓
Generic Engineering Evidence / Revision / Fragment Contract
    ↓
First Real Domain Pack: RE
    ↓
Engineering document ingestion
    ↓
Layout / table / figure-aware parsing
    ↓
Hybrid retrieval
    ↓
Evidence + Claim verification
    ↓
RE QA / diagnosis
    ↓
Engineering reporting
    ↓
Agentic tool workflows
    ↓
EMI / RFI / CST / ESD Domain Packs
    ↓
Optimization substrate / OPRO / GEPA
```

## Explicit Non-Goals

Financial-data ingestion, investment/backtesting, portfolio management, and financial optimization are not core Agent Factory requirements. Such experiments may exist in isolated historical branches, but must not alter the shared kernel mission.

Autonomous production self-modification and autonomous equipment control are also outside the current scope.

## Repository Structure

- `docs/` — vision, MDD, roadmap, PoC, governance
- `schemas/` — canonical data contracts
- `workflows/` — workflow definitions
- `templates/` — Domain Pack / benchmark / lesson / agent context templates
- `fixtures/` — synthetic regression and domain-matrix fixtures
- `src/` — implementation interfaces and runtime skeleton
- `scripts/` — executable factory demos and validation
- `tests/` — regression and contract tests

## Source of Truth

The live Git repository is the canonical implementation baseline. Historical ZIP/design packages and isolated experiment branches are historical evidence unless explicitly promoted by a versioned architecture decision.

Baseline date: 2026-08-19
