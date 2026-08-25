# Generic Engineering Evidence Contract v1.0

**Status:** Draft for implementation / runtime validation
**Scope:** Domain-independent evidence envelope for Agent Factory execution and artifact verification

## 1. Purpose

This contract defines the common evidence envelope shared by all engineering domains. Domain Packs provide domain-specific evidence content; the Kernel owns identity, provenance, execution, artifact integrity, validation, and governance semantics.

The contract is intentionally domain-neutral. Adding a domain MUST require only a compatible Domain Pack and evidence payload mapping; the Kernel evidence semantics MUST NOT fork per domain.

## 2. Separation of responsibilities

### Generic Kernel-owned evidence

The Kernel owns:

- execution identity
- target/runtime commit binding
- run/job/workflow identity
- domain and scenario identity
- input provenance references
- runtime/tool metadata
- artifact references and digest verification
- validation disposition
- evidence-manifest binding
- timestamp and version metadata
- failure reason / limitation metadata
- confidence metadata
- Human-on-the-Loop decision point and decision reference

### Domain Pack-owned evidence

A Domain Pack owns only the domain payload referenced by the generic envelope, such as:

- engineering measurements
- domain terminology and ontology references
- domain-specific rule findings
- domain-specific calculation outputs
- domain-specific report facts
- domain-specific validator details

The generic contract MUST NOT encode RE/EMI/CST/ESD-specific fields.

## 3. Canonical object position

```text
Document
  ↓
Revision
  ↓
Fragment
  ↓
Domain Evidence Payload
  ↓
Generic Engineering Evidence Envelope
  ↓
Claim / Verification
  ↓
CER Decision
  ↓
WorkflowRun
  ↓
Artifact / Digest
  ↓
Evidence Manifest
```

The envelope is the machine-verifiable bridge between domain evidence and execution/audit evidence.

## 4. Canonical schema

```yaml
contract_version: semver

evidence:
  evidence_id: string
  evidence_type: string
  domain: string
  domain_pack_id: string
  domain_pack_version: semver
  scenario: string
  task_id: string

execution_identity:
  repository: string
  workflow: string
  workflow_version: string
  run_id: string
  job_id: string|null
  target_sha: string
  runtime_sha: string
  execution_id: string
  event: string

provenance:
  source_refs: list[string]
  source_type: string
  source_hashes: list[string]
  document_id: string|null
  revision_id: string|null
  fragment_id: string|null
  locator: string|null
  authority: string|null
  ingestion_method: string|null
  extraction_version: string|null
  observed_at: datetime

runtime:
  runner_os: string
  runtime_version: string
  tool_versions: map[string,string]
  model_provider: string|null
  model_name: string|null
  parser_version: string|null
  retriever_version: string|null

result:
  status: [success, partial, failed, abstained]
  summary: string
  domain_payload_ref: string|null
  failure_reason: string|null

validation:
  status: [PASS, FAIL, BLOCKED, NOT_OBSERVED, INVALID_EVIDENCE]
  checks: list[string]
  validator_version: string
  validated_at: datetime|null

artifact:
  artifact_ref: string
  artifact_name: string
  media_type: string
  size_bytes: integer|null
  digest_algorithm: [sha256]
  digest: string
  digest_verified: boolean
  download_verified: boolean

manifest:
  manifest_id: string
  manifest_hash: string
  parent_evidence_ids: list[string]

quality:
  confidence: number|null
  limitations: list[string]

hotl:
  decision_point: string|null
  required: boolean
  decision_id: string|null
  action: [none, approve, edit, reject, retry, escalate]
  actor_ref: string|null
  rationale: string|null
  decided_at: datetime|null

created_at: datetime
```

## 5. Mandatory machine invariants

1. `execution_identity.repository` MUST equal the governed repository.
2. `execution_identity.target_sha` MUST equal the SHA being evaluated.
3. `execution_identity.runtime_sha` MUST equal the checked-out/runtime SHA.
4. `target_sha == runtime_sha` is REQUIRED for a GREEN evidence verdict.
5. `evidence.domain` MUST identify the selected Domain Pack, but the generic schema MUST remain domain-neutral.
6. `artifact.digest_verified == true` is REQUIRED for GREEN.
7. `artifact.download_verified == true` is REQUIRED when the artifact is independently downloaded for verification.
8. `validation.status == PASS` is REQUIRED for GREEN.
9. `manifest.manifest_hash` MUST bind the envelope to the evidence manifest.
10. `result.status == failed` MUST NOT coexist with `validation.status == PASS` unless a separate governed partial-success decision explicitly exists.
11. A missing, stale, or conflicting execution identity MUST classify the evidence as `INVALID_EVIDENCE` or `NOT_OBSERVED`, never GREEN.
12. Domain-specific payloads MUST be referenced, not embedded as Kernel schema branches.

## 6. GREEN / BLOCKED disposition

```text
Evidence Envelope
      ↓
identity valid?
      ↓ yes
artifact valid + digest verified?
      ↓ yes
manifest bound?
      ↓ yes
validation PASS?
      ↓ yes
CER governance gate PASS?
      ├─ yes → GREEN
      └─ no  → BLOCKED

Any missing/contradictory identity or integrity proof → INVALID_EVIDENCE / NOT_OBSERVED
```

GREEN is a conclusion about the evidence chain, not about domain accuracy. Domain accuracy remains the responsibility of the Domain Pack validators and the applicable CER policy.

## 7. Extension rule

A new domain MUST implement a mapping from its domain-specific evidence payload to this generic envelope. It MUST NOT add domain-specific branches to the Kernel evidence schema.

This is the acceptance criterion for Kernel/Domain Pack separation.

## 8. Relationship to existing contracts

- `schemas/document_revision.schema.yaml` owns source revision and fragment lineage.
- `schemas/evidence.schema.yaml` owns source-grounded evidence identity.
- `schemas/claim_evidence.schema.yaml` owns claim-level provenance and verification.
- `schemas/cer_runtime.schema.yaml` owns WorkflowRun/AgentStep/CER execution semantics.
- `schemas/trace.schema.yaml` owns end-to-end run trace.
- This contract owns the common evidence envelope that binds those layers for machine verification.

No existing contract is replaced by this envelope.
