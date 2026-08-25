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
# Every gate the Factory Kernel workflow runs must appear here, or the evidence
# chain silently certifies a subset. E-M1-RE-DEMO and E-DOMAIN-MATRIX were added
# 2026-08-25 when this tooling was recovered to the trunk: both gates postdate
# the 2026-08-18 branch this file came from, and without them a GREEN decision
# would have covered four of six gates while reading as complete.
EXPECTED_IDS = {
    "E-FACTORY-DEMO",
    "E-HARNESS",
    "E-OPRO-BASELINE",
    "E-M1-RE-DEMO",
    "E-DOMAIN-MATRIX",
    "E-PYTEST",
}


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

    m1 = load_json_output(records["E-M1-RE-DEMO"], "E-M1-RE-DEMO", errors)
    if m1 is not None:
        # Judged on docs/RE_POC.md's acceptance targets, not on every case
        # passing. The benchmark grew from 15 cases to 159 and now contains
        # questions the retriever is measurably not expected to answer -- the
        # near-miss abstention band, OPEN_DECISIONS D-11. Demanding 159/159
        # would not make this gate stricter; it would force the benchmark back
        # down to cases that already pass, which is how a benchmark stops
        # measuring anything.
        #
        # This still fails closed. The acceptance block must be present and
        # must say the targets were met -- a run that omits it, or that
        # reports a miss, is AMBER.
        total, passed, failed = m1.get("cases_total"), m1.get("cases_passed"), m1.get("cases_failed")
        acceptance = m1.get("acceptance")
        observed["m1_re_demo"] = {
            "benchmark_id": m1.get("benchmark_id"),
            "cases_total": total,
            "cases_passed": passed,
            "cases_failed": failed,
            "evidence_recall_at_10": (acceptance or {}).get("evidence_recall_at_10"),
            "evidence_recall_excluding_verbatim": (acceptance or {}).get("evidence_recall_excluding_verbatim"),
            "abstention_by_band": (acceptance or {}).get("abstention_by_band"),
        }
        if not isinstance(total, int) or total < 1:
            errors.append("E-M1-RE-DEMO: cases_total is not a positive integer")
        if not isinstance(acceptance, dict):
            errors.append("E-M1-RE-DEMO: no acceptance block -- cannot judge the run against RE_POC targets")
        else:
            # The figure excluding cases whose query restates its own answer,
            # falling back to the headline for evidence produced before that
            # split existed. Judging the headline would let a regression hide
            # behind eleven cases that cannot fail.
            recall = acceptance.get("evidence_recall_excluding_verbatim")
            if recall is None:
                recall = acceptance.get("evidence_recall_at_10")
            target = acceptance.get("evidence_recall_target")
            if not isinstance(recall, (int, float)) or not isinstance(target, (int, float)):
                errors.append("E-M1-RE-DEMO: evidence recall/target not numeric")
            elif recall < target:
                errors.append(f"E-M1-RE-DEMO: Evidence Recall@10 {recall} is below target {target}")
            if acceptance.get("abstention_decidable_bands_perfect") is not True:
                errors.append(
                    "E-M1-RE-DEMO: abstention is not perfect on the decidable bands "
                    f"({acceptance.get('abstention_by_band')})"
                )
            if acceptance.get("meets_acceptance_targets") is not True:
                errors.append("E-M1-RE-DEMO: run does not meet the RE_POC acceptance targets")

    matrix = load_json_output(records["E-DOMAIN-MATRIX"], "E-DOMAIN-MATRIX", errors)
    if matrix is not None:
        observed["domain_matrix"] = {
            "domain_count": matrix.get("domain_count"),
            "passed": matrix.get("passed"),
            "fixture_only": matrix.get("fixture_only"),
        }
        if matrix.get("passed") is not True:
            errors.append("E-DOMAIN-MATRIX: matrix run did not pass")
        if not isinstance(matrix.get("domain_count"), int) or matrix.get("domain_count") < 2:
            errors.append("E-DOMAIN-MATRIX: fewer than two domains exercised, which does not demonstrate a shared kernel")
        # The matrix proves the kernel loads Domain Packs without forking; it is
        # not a live-knowledge run. A matrix that stopped being fixture-only
        # would be asserting something it has not earned.
        if matrix.get("fixture_only") is not True:
            errors.append("E-DOMAIN-MATRIX: fixture_only is not true")

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
