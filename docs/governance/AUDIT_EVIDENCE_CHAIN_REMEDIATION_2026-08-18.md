# Audit Evidence Chain Remediation — 2026-08-18

## Scope

This remediation changes **audit evidence capture/governance only**. The audited implementation baseline remains:

`20a54b92aad0857f75c6200d984b13098c6f4927`

No OPRO promotion, GEPA implementation, or RE Domain implementation is authorized by this change.

## Finding disposition

The prior native execution is independently resolvable as GitHub Actions run `31821110548`, job `94834241880`, head SHA `20a54b92aad0857f75c6200d984b13098c6f4927`. The job conclusion was `success`, the Factory Demo, harness, OPRO, and pytest steps completed successfully, and pytest reported `29 passed`. The uploaded machine-evidence artifact was ID `9226960041` with GitHub-reported SHA256 `6ec70c288a7582e76a7c1c77e7af7a0e8b45463b6e40cea033e36f2f43780525`.

The artifact was also downloaded and its ZIP SHA256 was independently recomputed as:

`6ec70c288a7582e76a7c1c77e7af7a0e8b45463b6e40cea033e36f2f43780525`

### Remaining finding on the historical run

The original artifact contains only three stdout files. It does not contain explicit per-command stderr, explicit exit-code records, or a machine-generated manifest linking every command to workflow/job/artifact identity. Therefore the historical run is **verified as execution evidence at E3**, but it is **not promoted to E4** merely by virtue of the artifact ZIP digest.

The historical audit matrix's unrestricted `GREEN` / `OPRO baseline freeze: ACCEPTED` disposition is therefore superseded by the Meta Audit remediation rule until the new evidence-chain workflow produces a complete E4 pack.

## Remediation implemented

1. `schemas/execution_evidence.schema.json`
   - Defines the execution evidence contract.
   - Separates execution identity from application-reported fields.
   - Requires stdout/stderr SHA256 values.

2. `scripts/capture_execution.py`
   - Captures exact command, repository, workflow run, commit SHA, timestamps, exit code, stdout, stderr, and hashes.
   - Returns the wrapped command's exit code after persisting the evidence record.

3. `scripts/evidence_gate.py`
   - Validates required fields, commit identity, exit code, workflow run identity, and stdout/stderr hashes.
   - Emits `GREEN` only when all captured execution records are complete and successful.

4. `.github/workflows/audit-evidence-chain.yml`
   - Re-executes Factory Demo, deterministic harness, OPRO baseline, and pytest.
   - Captures raw evidence before any audit decision is made.
   - Produces explicit expected / observed / verified / decision sections.
   - Uploads a raw evidence artifact and a separately addressable artifact metadata record.
   - Fails the evidence-chain gate unless the machine validation is GREEN.

## Decision policy

`FAIL -> RED`

`mandatory HOLD or INCONCLUSIVE -> AMBER`

`PASS with documentation weakness -> GREEN-W`

`all mandatory primary evidence resolved and independently verified -> GREEN`

OPRO freeze/promotion remains **BLOCKED** until the final Evidence Gate is GREEN and the Internal Audit + External/Cold Audit both resolve successfully.

## CER sequence

`Execute -> Capture -> Hash -> Verify -> Classify -> CER CHECK -> Audit decision -> Sign-off`

A future session may only replace the provisional disposition after the new workflow run, raw evidence artifact, artifact metadata, Internal Audit, and External/Cold Audit have all been independently resolved.
