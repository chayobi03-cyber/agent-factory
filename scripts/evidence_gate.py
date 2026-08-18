#!/usr/bin/env python3
"""Validate execution evidence and protected regression results."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
EXPECTED_IDS = {"E-FACTORY-DEMO", "E-HARNESS", "E-OPRO-BASELINE", "E-PYTEST"}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json_output(record: dict, label: str, errors: list[str]) -> dict | None:
    try:
        return json.loads(record["stdout"])
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: stdout is not valid JSON: {exc}")
        return None


def validate_record(path: Path, expected_commit: str) -> tuple[list[str], dict]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        return [f"{path.name}: missing fields: {','.join(missing)}"], data
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
    return errors, data


def validate_expected_results(records: dict[str, dict], errors: list[str]) -> dict:
    observed: dict = {}

    demo = load_json_output(records["E-FACTORY-DEMO"], "E-FACTORY-DEMO", errors)
    if demo is not None:
        scenarios = {item.get("scenario"): item for item in demo.get("results", [])}
        observed["factory_demo_scenarios"] = sorted(scenarios)
        if set(scenarios) != {"PASS", "REVIEW", "BLOCK"}:
            errors.append("E-FACTORY-DEMO: expected PASS/REVIEW/BLOCK scenarios are incomplete")
        if scenarios.get("PASS", {}).get("final_state") != "COMPLETED":
            errors.append("E-FACTORY-DEMO: PASS scenario final_state is not COMPLETED")
        if scenarios.get("REVIEW", {}).get("final_state") != "COMPLETED":
            errors.append("E-FACTORY-DEMO: REVIEW scenario final_state is not COMPLETED")
        if scenarios.get("BLOCK", {}).get("final_state") != "BLOCKED":
            errors.append("E-FACTORY-DEMO: BLOCK scenario final_state is not BLOCKED")

    harness = load_json_output(records["E-HARNESS"], "E-HARNESS", errors)
    if harness is not None:
        observed["harness"] = {
            "case_count": harness.get("case_count"),
            "passed": harness.get("passed"),
            "failed": harness.get("failed"),
            "green": harness.get("green"),
        }
        if harness.get("case_count") != 10 or harness.get("passed") != 10 or harness.get("failed") != 0 or harness.get("green") is not True:
            errors.append("E-HARNESS: protected harness result is not 10/10 with green=true")

    opro = load_json_output(records["E-OPRO-BASELINE"], "E-OPRO-BASELINE", errors)
    if opro is not None:
        baseline = opro.get("baseline_score")
        best = opro.get("best_score")
        observed["opro"] = {
            "baseline_score": baseline,
            "best_score": best,
            "regression_result": opro.get("regression_result"),
            "promotion_status": opro.get("promotion_status"),
        }
        if not isinstance(baseline, (int, float)) or not isinstance(best, (int, float)):
            errors.append("E-OPRO-BASELINE: baseline_score/best_score not numeric")
        elif best < baseline:
            errors.append("E-OPRO-BASELINE: best_score is below baseline_score")
        if opro.get("regression_result") != "PASS":
            errors.append("E-OPRO-BASELINE: regression_result is not PASS")
        if opro.get("promotion_status") != "CANDIDATE":
            errors.append("E-OPRO-BASELINE: promotion_status is not CANDIDATE")

    pytest_record = records["E-PYTEST"]
    observed["pytest"] = {"stdout_tail": pytest_record["stdout"][-500:]}
    if re.search(r"\bfailed\b", pytest_record["stdout"].lower()):
        errors.append("E-PYTEST: stdout contains a failed-test marker")
    if not re.search(r"\b\d+ passed\b", pytest_record["stdout"]):
        errors.append("E-PYTEST: stdout does not contain an explicit '<N> passed' result")

    return observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    records: dict[str, dict] = {}
    for path in sorted(args.evidence_dir.glob("*.json")):
        if path.name in {"manifest.json", "artifact-metadata.json", "evidence-gate.json"}:
            continue
        try:
            record_errors, record = validate_record(path, args.expected_commit)
        except Exception as exc:
            errors.append(f"{path.name}: unreadable evidence record: {exc}")
            continue
        errors.extend(record_errors)
        if record.get("evidence_id"):
            records[record["evidence_id"]] = record

    missing_ids = sorted(EXPECTED_IDS - set(records))
    if missing_ids:
        errors.append(f"missing mandatory evidence records: {','.join(missing_ids)}")

    observed_results = validate_expected_results(records, errors) if not missing_ids else {}
    decision = "GREEN" if not errors else "AMBER"
    result = {
        "decision": decision,
        "expected_commit": args.expected_commit,
        "record_count": len(records),
        "errors": errors,
        "mandatory_evidence_complete": decision == "GREEN",
        "observed_results": observed_results,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if decision == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
