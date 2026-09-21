from pathlib import Path
import copy
import json

from scripts.goal_alignment_goalcard_5case import evaluate


FIXTURE = Path("fixtures/goal_alignment_goalcard_5case.json")


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_five_case_acceptance_matrix():
    data = load()
    results = [evaluate(case) for case in data["cases"]]
    assert len(results) == 5
    assert all(item["contract_green"] for item in results)
    assert [item["observed"] for item in results] == ["PASS", "BLOCK", "BLOCK", "BLOCK", "BLOCK"]


def test_extra_goal_is_hard_block():
    case = next(x for x in load()["cases"] if x["case_id"] == "T01-pass-grounded")
    tampered = copy.deepcopy(case)
    tampered["candidate_goal_card"]["objectives"].append(
        {"id": "O9", "text": "EMC 비용을 최소화한다"}
    )
    result = evaluate(tampered)
    assert result["observed"] == "BLOCK"
    assert any(x["code"] == "EXTRA_OBJECTIVE" for x in result["errors"])


def test_priority_shift_is_hard_block():
    case = next(x for x in load()["cases"] if x["case_id"] == "T01-pass-grounded")
    tampered = copy.deepcopy(case)
    tampered["candidate_goal_card"]["priority_order"] = ["O2", "O1"]
    result = evaluate(tampered)
    assert result["observed"] == "BLOCK"
    assert any(x["code"] == "PRIORITY_SHIFT" for x in result["errors"])


def test_missing_constraint_is_hard_block():
    case = next(x for x in load()["cases"] if x["case_id"] == "T01-pass-grounded")
    tampered = copy.deepcopy(case)
    tampered["candidate_goal_card"]["constraints"].pop()
    result = evaluate(tampered)
    assert result["observed"] == "BLOCK"
    assert any(x["code"] == "MISSING_CONSTRAINT" for x in result["errors"])


def test_decision_authority_change_is_hard_block():
    case = next(x for x in load()["cases"] if x["case_id"] == "T01-pass-grounded")
    tampered = copy.deepcopy(case)
    tampered["candidate_goal_card"]["decision_authority"] = "AI"
    result = evaluate(tampered)
    assert result["observed"] == "BLOCK"
    assert any(x["code"] == "DECISION_AUTHORITY_CHANGE" for x in result["errors"])
