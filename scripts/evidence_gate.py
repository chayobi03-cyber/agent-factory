#!/usr/bin/env python3
"""Validate an execution-evidence directory and emit a deterministic gate decision."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = (
    "evidence_id",
    "command",
    "repository",
    "commit_sha",
    "timestamp_utc",
    "exit_code",
    "stdout",
    "stderr",
    "stdout_sha256",
    "stderr_sha256",
    "workflow_run_id",
    "job_id",
    "artifact_id",
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_record(path: Path, expected_commit: str) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: invalid JSON: {exc}"]

    missing = [key for key in REQUIRED if key not in data]
    if missing:
        errors.append(f"{path.name}: missing fields: {','.join(missing)}")
        return errors

    if data["commit_sha"] != expected_commit:
        errors.append(f"{path.name}: commit mismatch: {data['commit_sha']} != {expected_commit}")
    if data["workflow_run_id"] is None:
        errors.append(f"{path.name}: workflow_run_id unavailable")
    if data["exit_code"] != 0:
        errors.append(f"{path.name}: exit_code={data['exit_code']}")
    if data["stdout_sha256"] != digest(data["stdout"]):
        errors.append(f"{path.name}: stdout_sha256 mismatch")
    if data["stderr_sha256"] != digest(data["stderr"]):
        errors.append(f"{path.name}: stderr_sha256 mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = sorted(args.evidence_dir.glob("*.json"))
    errors: list[str] = []
    records = []
    for path in files:
        if path.name in {"manifest.json", "artifact-metadata.json"}:
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        records.append(record)
        errors.extend(validate_record(path, args.expected_commit))

    decision = "GREEN" if files and not errors else "AMBER"
    result = {
        "decision": decision,
        "expected_commit": args.expected_commit,
        "record_count": len(records),
        "errors": errors,
        "mandatory_evidence_complete": decision == "GREEN",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if decision == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
