"""Generic Engineering Evidence envelope creation and validation.

This module is deliberately independent of the Factory/CER runtime. Domain Packs
supply payload references; this layer enforces common execution, artifact, manifest,
and validation semantics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "contract_version", "evidence", "execution_identity", "provenance", "runtime",
    "result", "validation", "artifact", "manifest", "quality", "hotl", "created_at",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def _manifest_hash_input(manifest: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(manifest))
    copy["manifest_hash"] = ""
    for envelope in copy.get("evidence_envelopes", []):
        envelope.setdefault("manifest", {})["manifest_hash"] = ""
    return copy


def calculate_manifest_hash(manifest: dict[str, Any]) -> str:
    return sha256_json(_manifest_hash_input(manifest))


def build_envelope(*, domain: str, domain_pack_version: str, scenario: str, task_id: str,
                   domain_payload_ref: str, execution_identity: dict[str, Any],
                   provenance: dict[str, Any], runtime: dict[str, Any],
                   result: dict[str, Any], artifact: dict[str, Any],
                   observed_at: str, created_at: str) -> dict[str, Any]:
    evidence_id = sha256_json({
        "domain": domain,
        "task_id": task_id,
        "execution_id": execution_identity["execution_id"],
        "domain_payload_ref": domain_payload_ref,
    })[:24]
    return {
        "contract_version": "1.0.0",
        "evidence": {
            "evidence_id": evidence_id,
            "evidence_type": "engineering_domain_evidence",
            "domain": domain,
            "domain_pack_id": domain,
            "domain_pack_version": domain_pack_version,
            "scenario": scenario,
            "task_id": task_id,
        },
        "execution_identity": execution_identity,
        "provenance": provenance,
        "runtime": runtime,
        "result": {**result, "domain_payload_ref": domain_payload_ref},
        "validation": {
            "status": "PASS",
            "checks": [],
            "validator_version": "engineering-evidence-v1",
            "validated_at": observed_at,
        },
        "artifact": artifact,
        "manifest": {"manifest_id": "", "manifest_hash": "", "parent_evidence_ids": []},
        "quality": {"confidence": None, "limitations": []},
        "hotl": {
            "decision_point": None,
            "required": False,
            "decision_id": None,
            "action": "none",
            "actor_ref": None,
            "rationale": None,
            "decided_at": None,
        },
        "created_at": created_at,
    }


def validate_envelope(envelope: dict[str, Any], *, governed_repository: str,
                      require_manifest: bool = True) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_TOP_LEVEL - set(envelope)
    if missing:
        errors.append(f"missing top-level sections: {sorted(missing)}")
    identity = envelope.get("execution_identity", {})
    if identity.get("repository") != governed_repository:
        errors.append("execution repository mismatch")
    if identity.get("target_sha") != identity.get("runtime_sha"):
        errors.append("target_sha/runtime_sha mismatch")
    artifact = envelope.get("artifact", {})
    if artifact.get("digest_algorithm") != "sha256":
        errors.append("artifact digest algorithm must be sha256")
    if artifact.get("digest_verified") is not True:
        errors.append("artifact digest not verified")
    if envelope.get("validation", {}).get("status") != "PASS":
        errors.append("validation status is not PASS")
    if envelope.get("result", {}).get("status") == "failed" and envelope.get("validation", {}).get("status") == "PASS":
        errors.append("failed result cannot be PASS")
    if require_manifest and not envelope.get("manifest", {}).get("manifest_hash"):
        errors.append("manifest hash missing")
    return errors


def bind_manifest(envelopes: list[dict[str, Any]], *, execution_identity: dict[str, Any]) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "manifest_version": "1.0.0",
        "repository": execution_identity["repository"],
        "workflow": execution_identity["workflow"],
        "run_id": execution_identity["run_id"],
        "execution_id": execution_identity["execution_id"],
        "target_sha": execution_identity["target_sha"],
        "runtime_sha": execution_identity["runtime_sha"],
        "manifest_hash": "",
        "evidence_envelopes": envelopes,
    }
    manifest_hash = calculate_manifest_hash(manifest)
    manifest_id = sha256_json({"manifest_hash": manifest_hash, "execution_id": execution_identity["execution_id"]})[:24]
    for envelope in envelopes:
        envelope["manifest"]["manifest_id"] = manifest_id
        envelope["manifest"]["manifest_hash"] = manifest_hash
    manifest["manifest_hash"] = manifest_hash
    return manifest
