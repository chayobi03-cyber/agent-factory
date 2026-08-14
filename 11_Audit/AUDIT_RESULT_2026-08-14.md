# External LLM Audit Result — 2026-08-14

## Verdict

**AMBER — viable but material changes are required.**

The Agent Factory direction is viable, but production readiness depends on making provenance, revision semantics, claim-level evidence, durable workflow state, evaluation, HOTL governance, and controlled workflow optimization executable contracts rather than conceptual components.

## Highest-priority findings

- P0: Document → Revision → Evidence → Claim lineage must be immutable and enforceable.
- P0: Workflow state, idempotency, retry, loop detection, budgets, and replay must be explicit.
- P0: Domain Pack must isolate domain-specific ontology, rules, aliases, routing, validators, and report templates from the kernel.
- P0: Benchmark/evaluator quality must precede GEPA/OPRO/MIPRO/DSPy optimization.
- P0: HOTL must be an executable risk policy, not only a prompt instruction.
- P0: Workflow optimization requires offline evaluation, hidden regression, shadow/A-B testing, approval, and rollback.

## Strategic conclusion

The strongest architectural direction is to treat Agent Factory as a **Meta-Agent Engineering Platform** rather than a collection of domain RAG agents.

> 도메인 지식을 안전하게 ingestion하고, 여러 reasoning/retrieval 방법을 실험하고, evidence 기반으로 답변하며, workflow의 실패를 학습하여 다음 버전의 Agent를 만드는 Meta-Agent Engineering Platform.

## Recommended lifecycle

```text
Artifact
 → Document / Revision
 → Canonical Content
 → Evidence
 → Query / Intent / Domain / Risk
 → Adaptive Retrieval / Reasoning
 → Claim
 → Verification
 → HOTL Governance
 → Answer / Report
 → Trace
 → Failure / Root Cause
 → Lesson
 → Experiment / Benchmark
 → Regression
 → Controlled Release
 → Next Agent Version
```

## RE PoC recommendation

Keep the first PoC narrow:

```text
Legacy RE PDF
 → Parsing / OCR / Layout
 → Canonical Document
 → Hybrid Retrieval
 → Evidence
 → Claim
 → Verification
 → Answer
```

Then add evidence-first report generation, citation validation, HOTL, trace/lesson, and finally controlled optimization. Avoid premature full GraphRAG, broad multi-agent ensembles, and autonomous production self-modification.

## Key architectural rule

**Method Ensemble is not the same as Multi-Agent.** Prefer method-level comparison and adaptive retrieval/reasoning selection before increasing the number of autonomous agents.

## Optimization rule

Recommended order:

1. Evaluator / benchmark quality
2. Retrieval configuration
3. Query routing
4. Prompt/instruction/demonstration optimization
5. Verification/report workflow optimization
6. Full workflow topology optimization
7. Controlled autonomous candidate generation

## Audit action backlog

Use the detailed `AUDIT-GRADE ACTION LIST` from the external audit as the initial P0–P3 backlog. The key P0 contracts are provenance/revision, evidence/claim, workflow state, Domain Pack, benchmark/evaluator, HOTL policy, provider gateway, and replayable trace.

## Audit limitation

The external reviewer noted that the audit could not fully verify file-level contradictions without a pinned repository snapshot. Future audits must consume a repository snapshot, commit SHA, and source-of-truth manifest so findings can be mapped to exact artifacts and line ranges.
