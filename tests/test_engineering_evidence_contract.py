import pathlib

import pytest
import yaml

from src.engineering_evidence import bind_manifest, build_envelope, sha256_json, validate_envelope

SCHEMA_PATH = pathlib.Path("schemas/engineering_evidence.schema.yaml")
FIXTURE_PATH = pathlib.Path("fixtures/engineering_evidence/domain_envelopes.yaml")


def _identity(target="sha-demo"):
    return {
        "repository": "chayobi03-cyber/agent-factory",
        "workflow": "test",
        "workflow_version": "runtime-envelope-v1",
        "run_id": "1",
        "job_id": "1",
        "target_sha": target,
        "runtime_sha": target,
        "execution_id": "test:1:1:sha-demo",
        "event": "test",
    }


def _envelopes():
    fixture = yaml.safe_load(FIXTURE_PATH.read_text())
    identity = _identity()
    artifact = {
        "artifact_ref": "fixture.json",
        "artifact_name": "fixture.json",
        "media_type": "application/json",
        "size_bytes": 1,
        "digest_algorithm": "sha256",
        "digest": sha256_json({"fixture": True}),
        "digest_verified": True,
        "download_verified": False,
    }
    return [build_envelope(
        domain=item["domain_id"],
        domain_pack_version=item["domain_pack_version"],
        scenario=item["scenario"],
        task_id=f"task-{item['domain_id']}",
        domain_payload_ref=f"#/domains/{item['domain_id']}",
        execution_identity=identity,
        provenance={"source_refs": ["fixture"], "source_type": "fixture", "source_hashes": [], "observed_at": "2026-01-01T00:00:00+00:00"},
        runtime={"runner_os": "test", "runtime_version": "3.11", "tool_versions": {}},
        result={"status": "success", "summary": item["summary"], "failure_reason": None},
        artifact=artifact,
        observed_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    ) for item in fixture["domains"]]


def test_schema_has_generic_sections_only():
    schema = yaml.safe_load(SCHEMA_PATH.read_text())
    assert set(schema) == {
        "contract_version", "evidence", "execution_identity", "provenance", "runtime",
        "result", "validation", "artifact", "manifest", "quality", "hotl", "created_at",
    }
    schema_text = SCHEMA_PATH.read_text()
    for domain_field in ("re_frequency", "emi_limit", "cst_solver", "esd_voltage"):
        assert domain_field not in schema_text


def test_four_domains_share_identical_envelope_shape():
    envelopes = bind_manifest(_envelopes(), execution_identity=_identity())["evidence_envelopes"]
    assert {e["evidence"]["domain"] for e in envelopes} == {"RE", "EMI", "CST", "ESD"}
    signatures = {
        tuple(sorted((section, tuple(sorted(value)) if isinstance(value, dict) else type(value).__name__)
                     for section, value in e.items()))
        for e in envelopes
    }
    assert len(signatures) == 1


def test_valid_envelope_requires_matching_execution_identity():
    manifest = bind_manifest(_envelopes(), execution_identity=_identity())
    for envelope in manifest["evidence_envelopes"]:
        assert validate_envelope(envelope, governed_repository="chayobi03-cyber/agent-factory") == []


def test_sha_mismatch_is_not_green():
    envelope = _envelopes()[0]
    envelope["execution_identity"]["runtime_sha"] = "different"
    assert "target_sha/runtime_sha mismatch" in validate_envelope(
        envelope, governed_repository="chayobi03-cyber/agent-factory", require_manifest=False
    )
