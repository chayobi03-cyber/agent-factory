"""Regression tests for Goal Alignment v0.1."""
import json
from pathlib import Path

from goal_alignment.evaluator import _load_jsonl, evaluate_case, evaluate_goal_card


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "goal_alignment" / "gold"
CASES = ROOT / "goal_alignment" / "cases" / "goal_alignment_v0_1.jsonl"


def test_five_case_baseline_matches_expected_gate_results():
    rows = _load_jsonl(CASES)
    assert [row["case_id"] for row in rows] == ["T01", "T02", "T03", "T04", "T05"]
    for row in rows:
        result = evaluate_case(row, GOLD)
        assert result["status"] == row["expected_status"], result
        assert result["error_codes"] == row["expected_error_codes"], result


def test_objective_drift_blocks():
    rows = {row["case_id"]: row for row in _load_jsonl(CASES)}
    row = rows["T02"]
    gold = json.loads((GOLD / row["gold_file"]).read_text(encoding="utf-8"))
    result = evaluate_goal_card(gold, row["candidate_goal_card"])
    assert result["status"] == "BLOCK"
    assert "GA001" in result["error_codes"]


def test_priority_reordering_blocks():
    rows = {row["case_id"]: row for row in _load_jsonl(CASES)}
    row = rows["T03"]
    gold = json.loads((GOLD / row["gold_file"]).read_text(encoding="utf-8"))
    result = evaluate_goal_card(gold, row["candidate_goal_card"])
    assert result["status"] == "BLOCK"
    assert result["error_codes"] == ["GA002"]


def test_missing_hard_constraint_blocks():
    rows = {row["case_id"]: row for row in _load_jsonl(CASES)}
    row = rows["T04"]
    gold = json.loads((GOLD / row["gold_file"]).read_text(encoding="utf-8"))
    result = evaluate_goal_card(gold, row["candidate_goal_card"])
    assert result["status"] == "BLOCK"
    assert result["error_codes"] == ["GA003"]


def test_forbidden_scope_contradiction_blocks():
    rows = {row["case_id"]: row for row in _load_jsonl(CASES)}
    row = rows["T05"]
    gold = json.loads((GOLD / row["gold_file"]).read_text(encoding="utf-8"))
    result = evaluate_goal_card(gold, row["candidate_goal_card"])
    assert result["status"] == "BLOCK"
    assert result["error_codes"] == ["GA005"]
