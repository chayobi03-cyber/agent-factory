# Agent Factory v0.1 Master Design Document

## 1. Product Definition
Agent Factory is a domain-agnostic platform that ingests legacy engineering documents, identifies query domain/intent/risk, selects an appropriate workflow and retrieval method, produces evidence-grounded answers and reports, records execution traces, captures human corrections as lessons, and continuously improves workflows through benchmark-driven optimization.

Initial domains: RE → EMI/RFI/CST MWS → ESD and other engineering domains.

## 2. Core Design Principles
| ID | Principle | Application |
|---|---|---|
| P-01 | Domain/Runtime separation | Domain Pack + shared Agent Kernel |
| P-02 | Evidence-first | Claims require provenance/evidence for production-grade factual answers |
| P-03 | Method agnostic | Vector/Hybrid/Graph/Agentic/Deep Search are pluggable |
| P-04 | Risk-based autonomy | HOTL authority is controlled by risk/uncertainty |
| P-05 | Deterministic where possible | schema/citation/unit/threshold checks use rules |
| P-06 | Evaluability | every workflow step is traceable and benchmarkable |
| P-07 | Reproducibility | source/prompt/model/workflow/parser versions are recorded |
| P-08 | Regression safety | knowledge/prompt/workflow/model changes require regression tests |
| P-09 | Incremental complexity | simple workflow first; agent/multi-agent only when justified |
| P-10 | Human feedback as asset | corrections become lessons and benchmark candidates |

## 3. Runtime Architecture
```text
User
  ↓
Query Gateway
  ↓
Query Router ── domain / intent / difficulty / risk / report / tool need
  ↓
Workflow Orchestrator
  ├── Simple QA
  ├── Evidence Analysis
  ├── Diagnosis
  └── Deep Research / Report
  ↓
Retrieval Orchestrator
  ├── BM25 / keyword
  ├── Vector
  ├── Hybrid
  ├── Metadata / parent-child
  ├── Graph
  ├── Reranker
  └── Agentic / iterative search
  ↓
Evidence Manager → Claim Manager
  ↓
Reasoning Engine
  ↓
Verification Engine
  ├── Structural
  ├── Claim-Evidence
  ├── Domain rules / physics
  └── Cross-method / cross-model
  ↓
Answer / Report
  ↓
Trace / Telemetry
  ↓
Evaluation → Failure Analysis → Lesson Engine → Workflow Optimizer
```

## 4. Domain Pack Contract
```yaml
domain_id: RE
version: 0.1.0
ontology: {entities: [], relations: []}
terminology: {canonical_terms: [], synonyms: {}, abbreviations: {}}
source_policy: {authorities: [], revision_rules: {}}
retrieval_policy: {allowed_modes: [bm25, vector, hybrid, graph, agentic], default_mode: hybrid}
reasoning_policy: {diagnosis: hypothesis_competition, comparison: evidence_matrix}
verification_policy: {require_evidence_for_claims: true, domain_rules: [], cross_method_for_high_risk: true}
report_policy: {template_id: engineering_report_v1}
tools: []
benchmark_catalog: []
risk_policy: {thresholds: {low: 0.30, medium: 0.55, high: 0.75, critical: 0.90}}
```

## 5. Canonical Knowledge Model
Objects: SourceDocument, DocumentRevision, Section, Paragraph, Table, Figure, Equation, Entity, Relation, Claim, Evidence, Rule, Hypothesis, Annotation.

Relations: REVISION_OF, CONTAINS, MENTIONS, RELATES_TO, SUPPORTS, CONTRADICTS, DERIVED_FROM, SUPERSEDES, APPLIES_TO, VALIDATED_BY.

## 6. Query Classes
- factual/definition
- document location
- revision comparison
- condition/cause analysis
- engineering diagnosis
- evidence-for/against hypothesis
- recommended additional test
- report generation
- evidence sufficiency / abstention

Diagnosis workflow:
`observation → hypotheses → evidence search → counter-evidence → domain verification → conclusion`

Report workflow:
`research plan → retrieval/tools → evidence pool → claims → outline → draft → citation audit → technical audit → final`

## 7. HOTL
| Risk | Default behavior |
|---|---|
| Low | full auto + post-hoc audit |
| Medium | auto + verification + sampling |
| High | draft + human approval |
| Critical | human decision mandatory; AI supplies evidence |

## 8. Continuous Improvement
```text
Production Trace
 → Failure Classification
 → Root Cause
 → Lesson
 → Candidate Change
 → Offline Benchmark
 → Regression / A-B
 → Human Approval
 → Release
```

Optimization targets include prompt, query rewrite, retrieval policy, routing, tool selection, verification policy, report template, and workflow topology. GEPA/MIPROv2/OPRO are optimization candidates rather than architectural dependencies.

## 9. Provider Neutrality
GPT, Claude, Gemini and other models are accessed through a model adapter. Generation and verification may use different providers when risk justifies it.

## 10. Non-goals for v0.1
- fully autonomous production mutation
- autonomous certification/compliance decisions
- direct equipment control
- mandatory GraphRAG for all queries
- provider-specific core architecture
