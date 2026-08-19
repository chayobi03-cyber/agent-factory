# Agent Factory Scope v1.0

## 1. Mission

Agent Factory is a **domain-agnostic engineering agent platform** for turning legacy engineering knowledge, tools, and evidence into traceable agentic workflows.

The platform exists to:

- ingest and represent engineering knowledge;
- retrieve evidence with provenance;
- execute agent/tool workflows under CER governance;
- verify claims independently of generation;
- support risk-based Human-on-the-Loop (HOTL);
- produce evidence-grounded engineering answers and reports;
- learn through Trace → Failure → RootCause → Lesson → Experiment → Regression → Release.

## 2. Primary Domain Strategy

The first production-like domain is **RE (Radiated Emission)**.

Planned extensions are:

1. RE / Radiated Emission
2. EMI / EMC
3. RFI
4. CST MWS / simulation workflows
5. ESD
6. additional engineering domains through Domain Packs

A new domain must be onboarded through the Domain Pack boundary without introducing hidden domain-specific branches into the shared kernel.

## 3. Kernel Boundary

The shared kernel owns generic execution and governance capabilities:

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

The kernel MUST NOT contain financial, RE, CST, PCB, ESD, or other domain-specific business logic.

## 4. Domain Pack Boundary

Domain-specific behavior belongs in a Domain Pack:

```text
ontology
aliases
units
source policies
parsing rules
retrieval policies
verification rules
tool adapters
risk rules
report templates
benchmarks
```

The stable kernel capability interface remains:

```text
ingest
parse
normalize
retrieve
verify
evaluate
render_report
```

## 5. Evidence / Provenance

Evidence provenance is a **generic platform capability**, not a financial-data subsystem.

Generic provenance must support:

- source identity and authority;
- immutable source revision/snapshot;
- content hash;
- stable locator;
- extraction/parser version;
- transformation lineage;
- derived hash;
- revision/supersession state;
- reproducibility and replay metadata.

This applies equally to engineering PDFs, tables, figures, simulation results, tool output, and other domain evidence.

## 6. Financial Data Policy

Financial data is **not a core Agent Factory product requirement**.

Financial-data ingestion, financial backtesting, portfolio analysis, or market-data optimization must not be added to the shared kernel merely to exercise provenance or optimization controls.

A financial domain may be used later as an isolated Domain Pack or external benchmark/adapter if it directly tests a reusable platform capability. Such work must remain outside the core kernel and cannot redefine the project mission.

## 7. Optimization Boundary

OPRO, GEPA, or other optimizers are optional execution/experiment engines. They do not define the product mission and do not bypass:

- Evidence/Claim verification;
- CER gates;
- HOTL;
- regression;
- provenance;
- release approval.

Optimization work follows the generic benchmark/evidence substrate and must not force a new application domain into the platform.

## 8. Non-Goals for Current Roadmap

The current roadmap does not include:

- financial data products;
- financial backtesting;
- portfolio management;
- autonomous investment decisions;
- autonomous equipment control;
- production self-modification without governance;
- mandatory GraphRAG or multi-agent execution.

## 9. Source-of-Truth Rule

The live Git repository is the canonical implementation baseline. Historical experiments, temporary domain branches, and exported archives are retained only as historical evidence unless explicitly promoted by a versioned architectural decision.

## 10. Acceptance Test for Strategic Alignment

A proposed feature belongs in Agent Factory core only when all are true:

1. it is reusable across engineering domains;
2. it strengthens evidence-grounded agent execution;
3. it preserves the Kernel / Domain Pack boundary;
4. it is testable through deterministic or clearly bounded evaluation;
5. it does not introduce an application-specific mission into the core.
