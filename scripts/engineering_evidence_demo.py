#!/usr/bin/env python3
"""Generate and validate a runtime Generic Engineering Evidence manifest."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

from engineering_evidence import bind_manifest, build_envelope, sha256_file, validate_envelope


REPO = "chayobi03-cyber/agent-factory"


def runtime_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default="fixtures/engineering_evidence/domain_envelopes.yaml")
    parser.add_argument("--output-dir", default="engineering-evidence")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    fixture = yaml.safe_load(Path(args.fixtures).read_text())
    domains = fixture["domains"]
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "fixture_only": True,
        "fixture_version": fixture["version"],
        "domains": domains,
    }
    payload_path = out_dir / "engineering-domain-payloads.json"
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    payload_digest = sha256_file(payload_path)
    payload_size = payload_path.stat().st_size

    checked_out_sha = runtime_sha()
    target_sha = os.environ.get("CER_TARGET_SHA", os.environ.get("GITHUB_SHA", checked_out_sha))
    repository = os.environ.get("GITHUB_REPOSITORY", REPO)
    if checked_out_sha != target_sha:
        raise SystemExit(f"target/runtime SHA mismatch: target={target_sha} runtime={checked_out_sha}")

    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    job_id = os.environ.get("GITHUB_JOB", "local")
    workflow = os.environ.get("GITHUB_WORKFLOW", "Engineering Evidence Runtime")
    event = os.environ.get("GITHUB_EVENT_NAME", "local")
    execution_id = f"{repository}:{run_id}:{job_id}:{checked_out_sha[:12]}"
    observed_at = datetime.now(timezone.utc).isoformat()
    execution_identity = {
        "repository": repository,
        "workflow": workflow,
        "workflow_version": "runtime-envelope-v1",
        "run_id": str(run_id),
        "job_id": str(job_id),
        "target_sha": target_sha,
        "runtime_sha": checked_out_sha,
        "execution_id": execution_id,
        "event": event,
    }
    runtime = {
        "runner_os": platform.platform(),
        "runtime_version": platform.python_version(),
        "tool_versions": {"pyyaml": yaml.__version__},
        "model_provider": None,
        "model_name": None,
        "parser_version": None,
        "retriever_version": None,
    }
    provenance = {
        "source_refs": [args.fixtures],
        "source_type": "synthetic_domain_fixture",
        "source_hashes": [sha256_file(Path(args.fixtures))],
        "document_id": None,
        "revision_id": None,
        "fragment_id": None,
        "locator": args.fixtures,
        "authority": "Agent Factory synthetic regression fixture",
        "ingestion_method": "fixture_loader",
        "extraction_version": None,
        "observed_at": observed_at,
    }
    artifact = {
        "artifact_ref": str(payload_path),
        "artifact_name": payload_path.name,
        "media_type": "application/json",
        "size_bytes": payload_size,
        "digest_algorithm": "sha256",
        "digest": payload_digest,
        "digest_verified": sha256_file(payload_path) == payload_digest,
        "download_verified": False,
    }
    envelopes = []
    for domain in domains:
        envelopes.append(build_envelope(
            domain=domain["domain_id"],
            domain_pack_version=domain["domain_pack_version"],
            scenario=domain["scenario"],
            task_id=f"generic-evidence-{domain['domain_id'].lower()}",
            domain_payload_ref=f"#/domains/{domain['domain_id']}",
            execution_identity=execution_identity,
            provenance=provenance,
            runtime=runtime,
            result={"status": "success", "summary": domain["summary"], "failure_reason": None},
            artifact=artifact,
            observed_at=observed_at,
            created_at=observed_at,
        ))

    manifest = bind_manifest(envelopes, execution_identity=execution_identity)
    manifest["validation"] = {"status": "PASS", "validator_version": "engineering-evidence-v1"}
    errors = []
    for envelope in envelopes:
        errors.extend(validate_envelope(envelope, governed_repository=repository))
    if errors:
        manifest["validation"] = {"status": "FAIL", "validator_version": "engineering-evidence-v1", "errors": errors}
    else:
        manifest["validation"]["checks"] = [
            "target_sha==runtime_sha",
            "artifact_digest_verified",
            "manifest_hash_bound",
            "cross_domain_schema_identical",
        ]

    manifest_path = out_dir / "engineering-evidence-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    result = {
        "passed": not errors,
        "domain_count": len(envelopes),
        "domains": [e["evidence"]["domain"] for e in envelopes],
        "manifest": str(manifest_path),
        "manifest_hash": manifest["manifest_hash"],
        "target_sha": target_sha,
        "runtime_sha": checked_out_sha,
    }
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
