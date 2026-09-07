# Schema Index

**Purpose:** so a reader can tell, per schema, which declarations are enforced
by running code and which are not. `docs/governance/INDEX.md` does this job for
governance documents; nothing did it for schemas, and the gap is why D-16 was
found by accident rather than by looking.

**Evidence:** `python3 scripts/audit_schema_bindings.py` reports, mechanically,
every declared field that nothing outside `schemas/` names. As of `395b839`:
**58 distinct field names, 75 (field, schema) pairs, across 9 of 12 schema
files.** That script carries the evidence; this document carries the judgement.

Status legend: **ENFORCED** (a named consumer reads or validates against it) ·
**PARTIAL** (implemented in substance, but the declaration is wider than the
code, or narrower) · **ASPIRATIONAL** (describes a system deliberately not
built yet) · **UNBOUND** (nothing reads it, and nothing explains why)

| Schema | Status | Consumer, or why not |
|---|---|---|
| `domain_pack.schema.yaml` | **ENFORCED** | `src/generic_domain_pack.py` loads it; six packs under `domains/` conform; `tests/test_generic_domain_pack.py`. |
| `session_state.schema.yaml` | **ENFORCED** | `scripts/validate_session_state.py` and `validate_session_resume.py`; RC-01..RC-08. |
| `engineering_evidence.schema.yaml` | **ENFORCED** | `src/engineering_evidence.py`, `tests/test_engineering_evidence_contract.py`, per `GENERIC_ENGINEERING_EVIDENCE_CONTRACT_V1.md`. |
| `evidence.schema.yaml` | **PARTIAL** | Evidence handling is live, but `extraction_method`, `extraction_version`, and `validity` are named nowhere. The active/superseded/rejected lifecycle is declared and never set. |
| `execution_evidence.schema.json` | **ENFORCED (indirectly)** | `scripts/evidence_gate.py` enforces the same 13 required fields from **its own hardcoded `REQUIRED` tuple** — it never loads this file. The two are held in agreement by `tests/test_schema_bindings.py`, added 2026-08-31; before that they agreed by coincidence. |
| `claim_evidence.schema.yaml` | **PARTIAL** | Claims and grounding are live (`src/claim_verification.py`). The declared six-boolean `verification` block is not: `structural`, `evidence_supported`, `domain_rule_passed`, `cross_method_passed`, `citation_locator_valid`, `revision_valid` appear nowhere in code. `VerificationReport` reports grounding and revision conflict under different names, and D-14 withdrew the conflict rule deliberately. The schema describes a six-layer verification the kernel does not perform. |
| `human_decision.schema.yaml` | **PARTIAL** | `HumanDecision` in `src/cer_runtime.py` implements most of it. Two differences: `actor: {type, id}` is flat `actor_id` in code (shape drift, not a gap), and **`previous_decision_id` is implemented nowhere** — see below. |
| `document_revision.schema.yaml` | **UNBOUND** | Named by nothing. `supersedes_revision_id`, `parent_fragment_id`, `content_hash`, `effective_at`, `validity`, `ordinal`, `source_uri`, `fragment_type`, `registered_at` are all declarations without code. The RE corpus builds its own structures. See D-16. |
| `trace.schema.yaml` | **ASPIRATIONAL** | Named by nothing, and mostly model-call telemetry: `input_tokens`, `output_tokens`, `estimated_usd`, `model_name`, `model_provider`, `model_revision`, `prompt_hash`, `request_id`, `request_config_hash`, `toolset_version`. The kernel has **no model dependency** — D-12 ruled it out and `tests/test_no_hosted_model_dependency.py` enforces it. This schema describes the system that would exist if D-12 were decided the other way. Not a defect; it should not be read as current. |
| `cer_runtime.schema.yaml` | **PARTIAL** | CER gate semantics are live and heavily tested, but this file is named by nothing and ten of its fields (`agent_step`, `step_id`, `input_ref`, `output_ref`, `error_refs`, `ended_at`, `resolved_at`, `execution_evidence`, `workflow_run`, `cer_decision_id`) have no code. The step-level execution record it describes is not the one `FactoryRuntime` keeps. |
| `optimization_benchmark.schema.yaml` | **PARTIAL** | OPRO is live (`src/opro.py`, `src/optimization.py`) and `objective_vector_ref` exists as `objective_vector_id` (name drift). `evaluator_ref`, `forbidden_outcomes`, `preconditions`, `expected_behavior`, `evidence_requirements`, `trace_requirements` have no code. |
| `audit_evidence_manifest.schema.json` | **PARTIAL** | The evidence-chain workflow produces manifests, but `expected_results`, `verified_results`, and `decision_results` are named nowhere. |

## The pattern worth naming: declared lineage, implemented nowhere

Three of the unbound fields are the same kind of thing — a pointer from a record
to the record it descends from:

| Relation | Declared in | Implemented |
|---|---|---|
| `supersedes_revision_id` | `document_revision.schema.yaml` | no |
| `previous_decision_id` | `human_decision.schema.yaml` | no |
| `parent_fragment_id` | `document_revision.schema.yaml` | no |

The repository declares lineage in three places and implements it in none. That
is a stronger statement than D-16 made when it was about one field, and it is
the concrete form of what the rejected APF package called
*provenance-as-relation* (RA-009): provenance here is a set of **fields
describing where a thing came from**, never a **link between two records**.

It has already cost something once. D-14 withdrew the revision-conflict rule,
recording the blocker as a corpus that does not declare which revision
supersedes which — while the schema for exactly that had been sitting in this
directory, unpopulated, the whole time.

## How to use this

- Before citing a schema as evidence that the system does something, check its
  row. **PARTIAL** and **ASPIRATIONAL** schemas describe intent, not behaviour.
- After changing a schema, re-run `scripts/audit_schema_bindings.py` and update
  the affected row. An unexplained new entry in that report is drift.
- When a field's row says nothing reads it, the choice is to bind it, or to
  delete it. Leaving it is how this list got long.

This index should be updated whenever a schema is added, bound, or retired —
otherwise it drifts exactly the way the documents it describes did.
