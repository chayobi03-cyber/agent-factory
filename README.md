# Agent Factory v0.1

Domain-Agnostic Agent Factory for legacy engineering knowledge, RAG, agentic workflows, evidence-grounded answers/reports, HOTL, benchmarking, and continuous workflow optimization.

## v0.1 PoC
- Factory kernel / HOTL demo first
- First real domain: RE (Radiated Emission) after kernel validation
- Future domains: EMI, RFI, CST MWS, ESD, and additional engineering domains
- Provider-neutral: GPT / Claude / Gemini and other LLMs

## Factory Demo

The current executable demo intentionally uses **synthetic engineering evidence** and does not connect a real RE implementation. It validates the shared factory control path:

```text
Task
 → CER Snapshot
 → Domain Pack
 → Agent
 → Evidence / Claim
 → CER Gate
 → PASS / REVIEW / BLOCK
 → Human Decision when required
 → Trace
```

Run all golden paths from the repository root:

```bash
python3 scripts/factory_demo.py --scenario all
```

Machine-readable output:

```bash
python3 scripts/factory_demo.py --scenario all --json
```

Demo details and acceptance criteria: `docs/FACTORY_HOTL_DEMO.md`

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

## Repository Structure
- `docs/` — MDD, architecture, roadmap, PoC, technology survey, governance, factory demo
- `schemas/` — canonical data contracts
- `workflows/` — workflow definitions
- `templates/` — Domain Pack / benchmark / lesson templates
- `src/` — implementation interfaces and runtime skeleton
- `scripts/` — runnable factory demos

## Design Package
The original v0.1 design package contains the detailed MDD, interfaces, schemas, workflows, benchmark, WBS, RE PoC, ADRs, and implementation skeleton. The repository version is the source-controlled baseline for continuing implementation.

Baseline date: 2026-08-14
