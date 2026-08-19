#!/usr/bin/env python3
"""Emit a machine-readable M2 entry-readiness decision without claiming execution."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.m2_historical import replay_key, validate_partitions

M1B_EVIDENCE = "docs/governance/M1B_PIT_RECONCILIATION_EVIDENCE_2026-08-20.yaml"
MATRIX = "fixtures/m2/historical_experiment_12_case.yaml"


def main() -> int:
    m1b = yaml.safe_load(Path(M1B_EVIDENCE).read_text(encoding="utf-8"))
    matrix = yaml.safe_load(Path(MATRIX).read_text(encoding="utf-8"))
    cases = matrix.get("cases", [])

    checks: list[dict[str, object]] = []
    checks.append({
        "check_id": "M2-ENTRY-01",
        "name": "M1-B evidence reference exists",
        "result": "PASS" if m1b.get("final_gate", {}).get("m1b_status") == "GREEN" else "BLOCKED",
        "source": M1B_EVIDENCE,
    })

    all_partition_valid = True
    replay_examples: list[str] = []
    for case in cases:
        p = case["partition"]
        try:
            validate_partitions(
                train=tuple(p["train"].split("/")),
                validation=tuple(p["validation"].split("/")),
                oos=tuple(p["oos"].split("/")),
            )
            replay_examples.append(
                replay_key(
                    source="M1B_VERIFIED_SOURCE_STACK",
                    dataset_id="ACTUAL_HISTORICAL_SNAPSHOT_REQUIRED",
                    dataset_version=case["dataset_version"],
                    vintage_id=case["PIT_cutoff"],
                    pit_cutoff=case["PIT_cutoff"],
                    transform_version=case["transform_version"],
                    partition_id=case["case_id"],
                    case_id=case["case_id"],
                )
            )
        except Exception:
            all_partition_valid = False
            break

    checks.append({
        "check_id": "M2-ENTRY-02",
        "name": "12-case partition matrix is structurally valid",
        "result": "PASS" if len(cases) == 12 and all_partition_valid else "BLOCKED",
        "case_count": len(cases),
    })
    checks.append({
        "check_id": "M2-ENTRY-03",
        "name": "Historical execution evidence exists",
        "result": "REVIEW_REQUIRED",
        "reason": "12 cases are readiness-defined but not yet executed against actual historical snapshots.",
    })
    checks.append({
        "check_id": "M2-ENTRY-04",
        "name": "OOS readiness evidence exists",
        "result": "REVIEW_REQUIRED",
        "reason": "No verified historical execution exists from which to establish the OOS gate.",
    })

    status = "REVIEW_REQUIRED"
    if any(item["result"] == "BLOCKED" for item in checks):
        status = "BLOCKED"

    output = {
        "schema_version": 1,
        "decision_type": "M2_ENTRY_REVIEW",
        "status": status,
        "m1b_evidence": M1B_EVIDENCE,
        "matrix": MATRIX,
        "case_count": len(cases),
        "historical_execution_verified": False,
        "oos_verified": False,
        "stress_verified": False,
        "monte_carlo_verified": False,
        "checks": checks,
        "replay_identity_sample": replay_examples[:2],
    }
    Path("m2-entry-review.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    # REVIEW_REQUIRED is an intentional non-green readiness classification; it is not a CI failure.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
