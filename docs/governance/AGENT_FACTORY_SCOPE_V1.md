# Agent Factory Scope v1.0

## Mission

Agent Factory is a **domain-agnostic engineering agent platform** for turning legacy engineering knowledge, engineering tools, and evidence into traceable agentic workflows.

The platform provides reusable capabilities for:

- engineering knowledge ingestion and representation;
- evidence-grounded retrieval;
- claim-level verification;
- governed agent and tool execution;
- risk-based Human-on-the-Loop (HOTL);
- engineering answers and reports with provenance;
- benchmarking, regression, and controlled continuous improvement.

## Primary domain strategy

The first real engineering domain is **RE (Radiated Emission)**. Subsequent domain expansion is expected through Domain Packs: EMI/EMC, RFI, CST MWS, ESD, and other engineering domains.

## Kernel boundary

The shared kernel owns generic execution and governance:

```text
Task
 → CER Snapshot
 → WorkflowRun
 → AgentStep
 → Tool / Retrieval
 → Evidence / Claim
 → Verification
 → CER Gate
 → HOTL
 → Trace
 → Benchmark / Regression
 → Release
```

The kernel MUST NOT contain RE, EMI, CST, PCB, ESD, financial, or other application-specific business logic.

## Domain Pack boundary

Domain-specific capability belongs behind stable interfaces:

```text
ingest
parse
normalize
retrieve
verify
evaluate
render_report
```

A Domain Pack may define ontology, aliases, units, source policies, parsing rules, retrieval policies, verification rules, tools, risk rules, report templates, and benchmarks. The kernel must not acquire hidden domain branches to support them.

## Evidence and provenance

Provenance is a generic platform capability. It must work for engineering PDFs, tables, figures, simulation results, tool outputs, and other domain evidence.

Minimum reusable provenance semantics are:

- immutable source identity/revision;
- stable locator;
- authority and extraction method;
- content/source hash;
- transformation lineage and version;
- derived hash;
- revision/supersession state;
- replay/reproducibility metadata.

## Financial-data boundary

Financial-data ingestion, financial backtesting, portfolio analysis, and investment optimization are **not Agent Factory core requirements**.

A financial workflow may be explored later as an isolated Domain Pack or external benchmark when it directly tests reusable platform capabilities. It must not redefine the kernel or roadmap.

## Optimization boundary

OPRO, GEPA, and other optimizers are optional governed experiment engines. They propose candidate changes; they do not define the product domain and cannot bypass Evidence/Claim verification, CER, HOTL, regression, or release controls.

## Current non-goals

- financial data products;
- investment/backtest systems;
- autonomous investment decisions;
- autonomous equipment control;
- production self-modification without governance;
- mandatory GraphRAG or multi-agent execution.

## Strategic alignment test

A new feature belongs in Agent Factory core only if it is reusable across engineering domains, strengthens evidence-grounded agent execution, preserves the Kernel/Domain Pack boundary, and is evaluable under the project's governance contracts.
