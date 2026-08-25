# AgentFactory Scope Contract V1

**Status:** Canonical project boundary
**Owner:** AgentFactory

## 1. Purpose

AgentFactory is a domain-agnostic engineering agent factory. Its core responsibility is the reusable kernel: domain-pack loading, evidence/claim handling, CER gates, HOTL control, traceability, regression, benchmarking, and controlled optimization.

## 2. Canonical project identity

```yaml
project_id: agent-factory
repository: chayobi03-cyber/agent-factory
governance_namespace: AgentFactory
```

The active branch is supplied by Git/CI context and is never inferred from another project.

## 3. Domain scope

AgentFactory must support multiple engineering domains through Domain Packs without changing the kernel. The initial live engineering domain is RE (Radiated Emission), followed by other engineering domains such as EMI, RFI, CST MWS, and ESD as governed onboarding permits.

A domain-specific experiment may exist on a non-canonical branch, but it must not redefine the AgentFactory roadmap, canonical governance, or project-level session state.

## 4. Explicit exclusion

Financial-investment research is **not** an AgentFactory core domain and must not become the canonical milestone, governance, workflow, or session context of this repository.

Examples of investment-specific material that must remain outside canonical AgentFactory scope include:

- financial market data ingestion as a project milestone;
- FRED/ALFRED/Treasury/ECB/SEC investment data pipelines;
- portfolio-risk or portfolio-performance experiments;
- investment-specific historical backtests, OOS, stress, or Monte Carlo workflows;
- investment-specific performance gates or capital-preservation policies.

Such material may be referenced only as an explicitly quarantined forensic artifact or external-project boundary reference.

## 5. Generic governance is allowed

Generic concepts are AgentFactory-native when they protect the factory architecture independently of a particular domain, including:

- evidence provenance;
- deterministic execution identity;
- CER and fail-closed gates;
- HOTL decision semantics;
- regression and reproducibility;
- project/repository identity guards;
- generic failure-analysis loops;
- controlled optimization governance.

The presence of a term such as `HOTL`, `M2`, `PIT`, or `optimization` is not by itself contamination evidence. Ownership and purpose determine classification.

## 6. Canonical milestone boundary

The canonical AgentFactory roadmap is defined by `docs/ROADMAP_WBS.md`. Its current progression is:

```text
M0 Foundation
 -> M0.5 Factory Kernel Verification
 -> M1 RE Hybrid RAG
 -> M2 RE Engineering Agent
 -> M3 Reporting
 -> M4 Agentic RAG
 -> M5 Method Ensemble
 -> M6 EMI/RFI
 -> M7 CST
 -> M8 Optimization
 -> M9 Domain Factory
```

A branch must not silently replace these milestones with an unrelated project's milestone vocabulary.

## 7. Boundary rule

Canonical AgentFactory governance must not import another repository's governance, session state, lessons, evidence, workflow policy, or project-specific HOTL rules.

External project names may appear only in explicit boundary/audit documentation and must not become active project context.

## 8. Enforcement

The repository identity and project-context guard is:

`scripts/validate_project_context.py`

The guard must fail closed on a genuine identity mismatch while avoiding false positives for explicit forensic boundary documentation.
