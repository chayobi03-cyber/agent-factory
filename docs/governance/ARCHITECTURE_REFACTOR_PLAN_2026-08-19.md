# Agent Factory Architecture Refactor — 2026-08-19

## Decision

Return the active product path to the original Agent Factory mission: a domain-agnostic engineering agent platform.

## Refactor goals

1. Preserve CER, Evidence/Claim, Verification, HOTL, Trace, Benchmark, Regression, and Release governance in the shared kernel.
2. Keep engineering-domain behavior behind Domain Packs.
3. Treat provenance as a generic evidence capability, not as a financial-data subsystem.
4. Make RE the next real domain implementation after Factory Kernel verification.
5. Keep OPRO/GEPA as optional governed optimization engines rather than application domains.
6. Prevent application-specific experiments from redefining the core roadmap.

## Implementation sequence

```text
Factory Kernel GREEN
    ↓
RE Domain Pack
    ↓
Engineering document ingestion
    ↓
Layout / table / figure-aware parsing
    ↓
Hybrid retrieval
    ↓
Evidence + Claim verification
    ↓
RE QA workflow
    ↓
Engineering report generation
    ↓
Agentic tool workflow
    ↓
EMI / RFI / CST / ESD Domain Packs
    ↓
Optimization substrate / OPRO / GEPA
```

## Historical financial detour

The 2026-08-19 M1-B financial-data work is retained on a dedicated historical branch and is not part of the active core architecture. No financial-specific ingestion, schema, benchmark, or backtest requirement is allowed to enter the shared kernel unless a future architecture decision explicitly promotes it as a reusable Domain Pack capability.

## Release discipline

Every future domain-specific experiment must prove one of two things:

- the capability is reusable at the kernel boundary; or
- the implementation is cleanly isolated inside a Domain Pack / external benchmark.

The project mission must not be widened merely because a domain is convenient for testing a generic mechanism.
