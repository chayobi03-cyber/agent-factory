# Agent Factory — Vision

## Core Definition

> **도메인 지식을 안전하게 ingestion하고, 여러 reasoning/retrieval 방법을 실험하고, evidence 기반으로 답변하며, workflow의 실패를 학습하여 다음 버전의 Agent를 만드는 Meta-Agent Engineering Platform**

## Mission

Agent Factory는 특정 도메인의 단일 RAG Agent를 만드는 프레임워크가 아니다. 다양한 엔지니어링 도메인을 동일한 Kernel 위에 Domain Pack으로 추가하고, 지식의 provenance와 evidence를 보존하며, 여러 방법론을 비교·검증하고, 실행 trace에서 실패와 lesson을 추출하여 다음 Agent/Workflow 버전을 개선하는 지속 진화형 Agent Engineering Platform을 목표로 한다.

## Design Principles

1. **Evidence before prose** — Claim과 Evidence를 먼저 확정하고 답변/Report를 생성한다.
2. **Domain-independent Kernel** — RE, EMI, RFI, CST MWS, ESD 및 미지의 신규 도메인을 Domain Pack으로 확장한다.
3. **Method pluralism** — BM25, vector, hybrid, metadata, parent/child, reranking, graph, agentic retrieval 및 reasoning 방법을 상황에 따라 선택·비교한다.
4. **Evaluation before optimization** — Benchmark와 evaluator의 품질을 먼저 확보한 뒤 GEPA/OPRO/MIPRO/DSPy 등의 최적화를 적용한다.
5. **Risk-based HOTL** — 사람의 개입을 최소화하되 고위험·저근거 작업은 강제 승인한다.
6. **Traceability by default** — 문서 revision, evidence, claim, model, tool, workflow, verification, human decision을 재현 가능하게 추적한다.
7. **Continuous learning without uncontrolled self-modification** — Trace → Failure → Root Cause → Lesson → Candidate → Offline Eval → Regression → Controlled Release의 폐쇄 루프를 사용한다.
8. **Provider neutrality** — GPT, Claude, Gemini 및 향후 모델을 Provider Gateway 뒤에 추상화한다.
9. **Deterministic checks where possible** — citation, schema, unit, range, revision, policy 등은 LLM 판단보다 결정론적 검증을 우선한다.
10. **No framework lock-in** — 특정 Agent/RAG framework보다 계약, 데이터 모델, 평가, 관찰 가능성을 핵심 자산으로 둔다.

## Target Lifecycle

```text
Source Artifact
    ↓
Safe Ingestion / Parsing / Quality Gate
    ↓
Canonical Document / Revision / Provenance
    ↓
Evidence Ledger + Domain Knowledge
    ↓
Query / Intent / Domain / Risk
    ↓
Adaptive Retrieval & Reasoning Methods
    ↓
Claim Construction
    ↓
Independent Verification
    ↓
HOTL / Risk Governance
    ↓
Evidence-first Answer / Report
    ↓
Trace / Metrics / Human Feedback
    ↓
Failure / Root Cause / Lesson
    ↓
Experiment / Benchmark / Regression
    ↓
Controlled Workflow / Agent Release
    ↓
Next Agent Version
```

## Initial Domain Roadmap

- **Phase 1:** RE (Radiated Emissions)
- **Phase 2:** EMI / RFI / CST MWS analysis
- **Phase 3:** ESD
- **Future:** additional engineering domains through Domain Pack onboarding

## Strategic Objective

최종 목표는 `RE Agent`를 완성하는 것이 아니라, **RE Agent를 만들면서 얻은 지식·계약·평가·실패·최적화 방법을 재사용하여 두 번째, 세 번째, N번째 도메인 Agent를 더 빠르고 안전하게 만드는 Factory 자체를 고도화하는 것**이다.

따라서 Agent Factory의 가장 중요한 산출물은 개별 Agent가 아니라 다음의 재사용 가능한 자산이다.

```text
Kernel Contracts
+ Domain Pack Contract
+ Evidence/Claim Model
+ Workflow Engine
+ Benchmark/Evaluation System
+ HOTL Governance
+ Trace/Lesson System
+ Optimization/Release System
= Agent Factory Capability
```

## North Star

> **도메인이 추가될수록 코어 코드가 복잡해지는 시스템이 아니라, 도메인이 추가될수록 Factory의 지식·평가·방법론·실패 교훈이 축적되어 다음 Agent의 구축 비용과 위험이 감소하는 시스템을 만든다.**
