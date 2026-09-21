from pathlib import Path
import json

from scripts.goal_alignment_free_5case import evaluate


def test_all_five_cases_match_expected():
    data = json.loads(Path("fixtures/goal_alignment_free_5case.json").read_text())
    results = [evaluate(case) for case in data["cases"]]
    assert len(results) == 5
    assert all(item["contract_green"] for item in results)
    assert [item["observed"] for item in results] == ["PASS", "REVIEW", "BLOCK", "REVIEW", "BLOCK"]


def test_unsupported_claim_can_only_pass_by_explicit_block():
    data = json.loads(Path("fixtures/goal_alignment_free_5case.json").read_text())
    case = next(item for item in data["cases"] if item["case_id"] == "GA-03-unsupported-claim")
    tampered = dict(case)
    tampered["final"] = dict(case["final"], decision="PASS")
    result = evaluate(tampered)
    assert not result["contract_green"]
    assert "unsupported_claim_passed" in result["errors"]


def test_goal_drift_cannot_be_passed():
    data = json.loads(Path("fixtures/goal_alignment_free_5case.json").read_text())
    case = next(item for item in data["cases"] if item["case_id"] == "GA-05-goal-drift-injection")
    tampered = dict(case)
    tampered["final"] = dict(case["final"], decision="PASS")
    result = evaluate(tampered)
    assert not result["contract_green"]
    assert "goal_drift_allowed" in result["errors"]
