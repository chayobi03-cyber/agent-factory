# External LLM Audit Prompt — Agent Factory v0.1

## Role

You are an independent senior reviewer for AI Agent Systems, RAG, knowledge engineering, evaluation, software architecture, and engineering-domain automation.

You are auditing the repository/design package **Agent Factory v0.1**. The target system is a domain-agnostic Agent Factory that ingests legacy engineering documents, builds domain knowledge, answers natural-language questions with evidence, produces engineering reports, supports multiple retrieval/reasoning methods, uses HOTL risk controls, and continuously improves its workflows from traces and lessons.

The first implementation domain is **RE (Radiated Emissions)**. Planned expansion domains include **EMI, RFI, CST MWS analysis, ESD**, and additional engineering domains.

## Audit objective

Do NOT judge only whether the documents look complete. Determine whether the architecture can realistically become a maintainable, extensible, evidence-grounded, evaluation-driven Agent Factory.

Audit the complete design as if it were being prepared for:

1. production engineering use,
2. long-term multi-domain expansion,
3. legacy-document ingestion,
4. multi-LLM/provider operation (e.g. GPT, Claude, Gemini),
5. autonomous workflow optimization with human governance.

## Required review dimensions

### A. System architecture
- Domain-independent kernel vs domain-specific pack separation
- Agent/workflow boundaries
- Query routing and workflow selection
- Retrieval orchestration
- Evidence/Claim architecture
- Verification architecture
- Reporting architecture
- Traceability and observability
- Provider/model abstraction
- Tool integration
- Failure isolation
- Scalability and operability

### B. Knowledge and document engineering
- Legacy document parsing strategy
- OCR/layout/table/figure handling
- canonical document model
- metadata and provenance
- revision/supersession management
- ontology/domain-pack design
- chunking strategy
- hybrid retrieval
- graph/knowledge representation
- evidence lineage

### C. RAG and Agent methodology
Compare whether the design appropriately distinguishes and combines:
- vector retrieval
- lexical/BM25 retrieval
- hybrid retrieval
- metadata filtering
- reranking
- parent/child retrieval
- graph retrieval
- multi-query retrieval
- agentic retrieval
- deep research/search
- hypothesis/counter-hypothesis reasoning
- multi-agent workflows
- method ensemble/arbitration

Identify where one method is being overused or where method selection is insufficiently specified.

### D. Evidence and answer integrity
Evaluate:
- Claim/Evidence linkage
- citation correctness
- source authority
- contradiction handling
- uncertainty representation
- unsupported-claim prevention
- cross-document consistency
- stale/revision conflict handling
- evidence-first report generation

### E. Evaluation and benchmark
Check whether the benchmark design can measure:
- parser quality
- retrieval quality
- evidence recall/precision
- answer correctness/completeness
- grounding/faithfulness
- domain consistency
- agent trajectory quality
- tool success
- cost/latency
- human intervention
- workflow-level quality
- regression after knowledge/model/prompt/workflow changes

Assess whether ground truth is sufficiently explicit and auditable.

### F. Optimization / GEPA / MIPRO / OPRO / DSPy
Evaluate whether optimization is being applied to the correct layers:
- prompts
- instructions
- demonstrations
- query rewriting
- retrieval configuration
- routing
- tool selection
- verification
- report generation
- complete workflows

Check for risks of optimizing against weak or contaminated evaluators.

### G. HOTL and governance
Evaluate:
- risk-based escalation
- automatic vs human-controlled actions
- approval thresholds
- audit trail
- human correction capture
- lesson extraction
- rollback
- safe release of workflow changes
- production autonomy boundaries

### H. Learning loop / Workflow optimization
Check whether this lifecycle is actually implementable:

`Trace -> Failure -> Root Cause -> Lesson -> Candidate Change -> Offline Eval -> Regression -> A/B -> Controlled Release`

Determine whether the design has sufficient schemas, storage, metrics, and experiment controls to support this loop.

### I. Multi-domain extensibility
Stress-test the design against:
- RE
- EMI
- RFI
- CST MWS
- ESD
- a completely new domain not known to the original designers

Ask whether a new domain can be onboarded mainly through a Domain Pack, or whether hidden domain-specific code will be required.

### J. Engineering implementation realism
Look for:
- interfaces that are underspecified
- schemas that cannot support the workflow
- missing state models
- missing idempotency
- missing versioning
- missing error handling
- missing deterministic validation
- ambiguous responsibilities
- excessive framework dependence
- over-engineering
- under-engineering
- hidden operational costs

## Mandatory adversarial tests

Attempt to break the design using at least these scenarios:

1. A 500-page PDF containing tables, figures, OCR errors, and multiple revisions.
2. Two documents that contradict each other.
3. A user asks a question outside the current domain.
4. A query requires three-hop reasoning across separate documents.
5. The correct evidence is available but lexical and semantic terminology differ.
6. The top retrieved evidence is authoritative but obsolete.
7. An LLM generates a plausible but unsupported engineering claim.
8. A report cites an incorrect page or source.
9. A workflow optimization improves benchmark score but worsens production cost.
10. A new domain is added without changing core runtime code.
11. One LLM provider becomes unavailable.
12. Human feedback contradicts the previous benchmark label.
13. A new source ingestion causes a regression in an existing domain.
14. The same engineering question is solved differently by two methods.
15. An agent enters a repeated tool/reasoning loop.
16. A high-risk recommendation is generated with high confidence but weak evidence.

## Review output format

Return the audit in exactly this structure.

### 1. Executive verdict
Give one of:
- GREEN — architecture is fundamentally sound
- AMBER — viable but material changes are required
- RED — major redesign required

Give a one-paragraph justification.

### 2. Architecture scorecard
Provide a table:

| Area | Score (0-5) | Severity | Finding |
|---|---:|---|---|

Use scores:
- 0 = absent
- 1 = conceptual only
- 2 = weak/underspecified
- 3 = implementable with gaps
- 4 = strong
- 5 = production-grade

### 3. Critical findings
List all findings that can materially invalidate the architecture.
For every finding include:
- ID
- severity: Critical / High / Medium / Low
- affected files/sections
- why it matters
- concrete remediation
- validation method

### 4. Missing architecture
Identify important capabilities that are absent, especially:
- state management
- provenance
- versioning
- evaluation
- safety/governance
- data lifecycle
- observability
- workflow control

### 5. Design contradictions
Find contradictions between:
- MDD
- architecture
- schemas
- workflows
- benchmark
- WBS
- RE PoC
- implementation skeleton
- ADRs

### 6. Schema audit
Check whether the schemas are sufficient for actual runtime behavior.
Explicitly check relationships among:
- Document
- Revision
- Section
- Evidence
- Claim
- Entity
- Rule
- Query
- RetrievalResult
- WorkflowRun
- AgentStep
- Verification
- HumanFeedback
- Lesson
- Experiment
- BenchmarkCase
- Report

### 7. Multi-method / Ensemble audit
Determine whether method comparison is rigorous enough.
Recommend where to use:
- single method
- adaptive routing
- parallel methods
- judge/arbitration
- deterministic checks

### 8. GEPA/OPRO/MIPRO audit
Specify which optimization layer should be optimized first, second, and later.
Identify risks of metric gaming or evaluator overfitting.

### 9. HOTL audit
Define which classes of actions should be:
- fully automatic
- automatic + audit
- human review
- human mandatory

### 10. RE PoC audit
Determine whether the proposed RE PoC is small enough to execute but rich enough to validate the factory architecture.
Identify what should be removed, added, or postponed.

### 11. Domain expansion test
Score expected onboarding difficulty for RE -> EMI -> RFI -> CST MWS -> ESD -> unknown domain.
Explain any architectural coupling that will make expansion expensive.

### 12. Priority remediation backlog
Create:
- P0: must fix before implementation
- P1: must fix before RE production pilot
- P2: fix before second domain
- P3: optimization / later maturity

### 13. Revised architecture recommendation
Provide a concise target architecture showing major components and interfaces.

### 14. Revised roadmap
Recommend an implementation order with explicit exit criteria for each phase.

### 15. Red-team conclusion
State the strongest argument AGAINST the current architecture.
Then state what evidence would convince you that the architecture is ready.

## Review rules

1. Be adversarial but constructive.
2. Do not praise completeness without evidence.
3. Prefer concrete failure modes over generic advice.
4. Distinguish conceptual quality from implementation readiness.
5. Identify over-engineering as well as under-engineering.
6. Do not assume an LLM judge is ground truth.
7. Do not assume vector RAG is sufficient.
8. Do not assume GraphRAG is necessary everywhere.
9. Do not recommend a framework merely because it is popular.
10. Treat source provenance, versioning, evidence lineage, and regression testing as first-class engineering concerns.
11. When a requirement is ambiguous, state the ambiguity and propose a precise contract.
12. When recommending a change, explain its trade-off.

## Final requirement

At the end, produce a section titled **AUDIT-GRADE ACTION LIST** containing no more than 20 actions. Each action must have:

`Action ID | Priority | Owner Type | Artifact/Component | Change | Acceptance Test | Dependency`

The audit should be detailed enough that another engineering team could turn the findings directly into GitHub issues without further interpretation.
