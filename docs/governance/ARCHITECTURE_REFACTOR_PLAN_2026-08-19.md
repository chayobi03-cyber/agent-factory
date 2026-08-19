# Agent Factory Architecture Refactor Plan — 2026-08-19

## Decision

Return the live implementation path to the original Agent Factory mission: a domain-agnostic engineering agent platform.

## Refactor objectives

1. Keep CER, Evidence/Claim, HOTL, Trace, Benchmark, and Regression in the shared kernel.
2. Keep engineering-specific behavior behind Domain Packs.
3. Treat provenance as a generic evidence capability rather than a financial-data subsystem.
4. Make RE the next domain implementation after Factory Kernel verification.
5. Keep OPRO/GEPA as optional governed optimization engines, not product-defining domains.
6. Remove financial-data work from the core roadmap and active session state.

## Implementation sequence

```text
Factory Kernel GREEN
    ↓
RE Domain Pack
    ↓
Engineering document ingestion
    ↓
Layout/table/figure-aware parsing
    ↓
Hybrid retrieval
    ↓
Evidence + Claim verification
    ↓
RE QA
    ↓
Engineering report
    ↓
Agentic tool workflow
    ↓
EMI/RFI/CST/ESD Domain Packs
    ↓
Optimization substrate / OPRO / GEPA
```

## Explicit rollback

The 2026-08-19 M1-B financial provenance implementation is not promoted into the core architecture. Its branches/PRs may remain as historical experiment artifacts, but the live baseline must not depend on them.

## Release discipline

Any future domain-specific experiment must first demonstrate that its capability is reusable at the kernel boundary or can be cleanly isolated as a Domain Pack. Domain-specific data ingestion must not alter the kernel mission.
