# Technology Survey Baseline

Date: 2026-08-14

## Anthropic
Building Effective Agents emphasizes starting with simple prompt/workflow patterns and increasing autonomy only when justified; useful patterns include sequential, parallel, evaluator-optimizer, and agentic loops.

Application: single-agent-first, workflow as versioned artifact, modular tools/skills, complexity budget.

## OpenAI Agents / AgentKit
Relevant primitives include agent orchestration, handoffs, guardrails, tracing/observability, datasets/trace grading and prompt optimization directions.

Application: provider-neutral trace and evaluation abstractions; OpenAI can be one provider adapter rather than the system architecture.

## Microsoft GraphRAG
Entity/relationship extraction and graph/community structures can improve relationship-heavy and multi-hop queries. Indexing cost means GraphRAG should be an optional adaptive branch, not a universal default.

## DSPy / MIPROv2 / GEPA
DSPy treats LM programs and metrics as optimization targets. MIPROv2 searches instruction/few-shot combinations. GEPA uses textual feedback/reflection to evolve program components and can be extended conceptually to workflow policy optimization.

Application: optimizer layer only; benchmark and hidden holdout are mandatory to prevent overfitting.

## Agentic RAG research direction
Recent work increasingly emphasizes iterative retrieval/navigation, planning and trajectory-level evaluation rather than one-shot retrieval.

Application: complex queries can activate iterative search; trajectories become first-class evaluation artifacts.

## Design decisions
We intentionally do not lock the product to one framework or one RAG method. The architecture exposes adapters for models, retrievers, graph, tools and optimizers and compares methods using the same benchmark cases.

## Key references
- Anthropic: https://resources.anthropic.com/building-effective-ai-agents
- OpenAI AgentKit: https://openai.com/index/introducing-agentkit/
- OpenAI Agents SDK tracing: https://openai.github.io/openai-agents-python/tracing/
- Microsoft GraphRAG: https://github.com/microsoft/graphrag
- DSPy optimizers: https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md
