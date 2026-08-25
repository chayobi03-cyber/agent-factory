"""Regression tests for the audit evidence chain gate.

`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1.md` is canonical, and until 2026-08-25 the
trunk had no implementation of it at all -- the enforcement sat unmerged on a
branch (OPEN_DECISIONS D-09). These tests exist because the failure that
produced D-09 was a gate that could not fail: what matters is not that the gate
returns GREEN on good evidence, but that it refuses everything else.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "evidence_gate", Path(__file__).resolve().parents[1] / "scripts" / "evidence_gate.py"
)
gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gate)

COMMIT = "a" * 40


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record(evidence_id: str, stdout: str, **overrides):
    data = {
        "evidence_id": evidence_id,
        "command": "python3 scripts/example.py --json",
        "repository": "chayobi03-cyber/agent-factory",
        "commit_sha": COMMIT,
        "timestamp_utc": "2026-08-25T00:00:00+00:00",
        "exit_code": 0,
        "stdout": stdout,
        "stderr": "",
        "stdout_sha256": sha(stdout),
        "stderr_sha256": sha(""),
        "workflow_run_id": 1,
        "job_id": None,
        "artifact_id": None,
    }
    data.update(overrides)
    return data


PAYLOADS = {
    "E-FACTORY-DEMO": {
        "results": [
            {"scenario": "PASS", "final_state": "COMPLETED"},
            {"scenario": "REVIEW", "final_state": "COMPLETED"},
            {"scenario": "BLOCK", "final_state": "BLOCKED"},
        ]
    },
    "E-HARNESS": {"case_count": 10, "passed": 10, "failed": 0, "green": True},
    "E-OPRO-BASELINE": {
        "baseline_score": 0.7,
        "best_score": 0.9,
        "regression_result": "PASS",
        "promotion_status": "CANDIDATE",
    },
    "E-M1-RE-DEMO": {
        "benchmark_id": "re-hybrid-rag-v0.2",
        "cases_total": 159,
        "cases_passed": 142,
        "cases_failed": 17,
        # Judged on RE_POC acceptance targets, not on every case passing: the
        # benchmark deliberately contains a band the retriever is measured as
        # unable to answer (OPEN_DECISIONS D-11). Note this fixture is a
        # *passing* one with 17 failed cases -- that is the point.
        "acceptance": {
            "evidence_recall_at_10": 0.9137,
            "evidence_recall_excluding_verbatim": 0.9062,
            "verbatim_case_count": 11,
            "evidence_recall_target": 0.90,
            "evidence_recall_meets_target": True,
            "abstention_by_band": {
                "subject_outside_domain": {"held": 5, "total": 5},
                "entity_absent_from_corpus": {"held": 7, "total": 7},
                "near_miss_domain_subject": {"held": 3, "total": 8},
            },
            "abstention_decidable_bands_perfect": True,
            "meets_acceptance_targets": True,
        },
    },
    "E-DOMAIN-MATRIX": {"domain_count": 4, "passed": True, "fixture_only": True},
}

FILENAMES = {
    "E-FACTORY-DEMO": "factory-demo.json",
    "E-HARNESS": "factory-harness.json",
    "E-OPRO-BASELINE": "opro-baseline.json",
    "E-M1-RE-DEMO": "re-demo.json",
    "E-DOMAIN-MATRIX": "domain-matrix.json",
    "E-PYTEST": "pytest.json",
}


def write_pack(tmp_path: Path, *, mutate=None) -> Path:
    """A complete, internally consistent evidence pack for every expected gate."""
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    records = {
        eid: record(eid, json.dumps(payload)) for eid, payload in PAYLOADS.items()
    }
    records["E-PYTEST"] = record("E-PYTEST", "....\n100 passed in 0.50s\n")
    if mutate:
        mutate(records)
    for eid, data in records.items():
        (raw / FILENAMES[eid]).write_text(json.dumps(data), encoding="utf-8")
    return raw


def decide(raw: Path, commit: str = COMMIT):
    errors: list[str] = []
    records: dict[str, dict] = {}
    for path in sorted(raw.glob("*.json")):
        record_errors, data = gate.validate_record(path, commit)
        errors.extend(record_errors)
        if data.get("evidence_id"):
            records[data["evidence_id"]] = data
    missing = sorted(gate.EXPECTED_IDS - set(records))
    if missing:
        errors.append(f"missing mandatory evidence records: {','.join(missing)}")
    else:
        gate.validate_expected_results(records, errors)
    return ("GREEN" if not errors else "AMBER"), errors


def test_complete_consistent_evidence_is_green(tmp_path):
    decision, errors = decide(write_pack(tmp_path))
    assert decision == "GREEN", errors


def test_every_workflow_gate_is_represented():
    """A gate absent from EXPECTED_IDS is a gate the chain silently skips while
    still reading as complete. E-M1-RE-DEMO and E-DOMAIN-MATRIX postdate the
    branch this tooling came from."""
    assert gate.EXPECTED_IDS == {
        "E-FACTORY-DEMO",
        "E-HARNESS",
        "E-OPRO-BASELINE",
        "E-M1-RE-DEMO",
        "E-DOMAIN-MATRIX",
        "E-PYTEST",
    }


@pytest.mark.parametrize("dropped", sorted(FILENAMES))
def test_a_missing_gate_record_blocks(tmp_path, dropped):
    raw = write_pack(tmp_path)
    (raw / FILENAMES[dropped]).unlink()
    decision, errors = decide(raw)
    assert decision == "AMBER"
    assert any(dropped in e for e in errors)


def test_tampered_stdout_is_caught_by_its_digest(tmp_path):
    """The record's stdout_sha256 is what makes the captured output evidence
    rather than an assertion."""
    def mutate(records):
        records["E-HARNESS"]["stdout"] = json.dumps(
            {"case_count": 10, "passed": 10, "failed": 0, "green": True, "tampered": True}
        )
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("stdout_sha256 mismatch" in e for e in errors)


def test_evidence_from_another_commit_is_rejected(tmp_path):
    """Historical success must not satisfy the gate for a new target SHA."""
    decision, errors = decide(write_pack(tmp_path), commit="b" * 40)
    assert decision == "AMBER"
    assert any("commit mismatch" in e for e in errors)


def test_nonzero_exit_code_blocks(tmp_path):
    def mutate(records):
        records["E-PYTEST"]["exit_code"] = 1
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("exit_code=1" in e for e in errors)


def test_protected_harness_result_cannot_regress(tmp_path):
    def mutate(records):
        payload = {"case_count": 10, "passed": 9, "failed": 1, "green": False}
        records["E-HARNESS"]["stdout"] = json.dumps(payload)
        records["E-HARNESS"]["stdout_sha256"] = sha(records["E-HARNESS"]["stdout"])
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("E-HARNESS" in e for e in errors)


def test_opro_best_below_baseline_blocks(tmp_path):
    def mutate(records):
        payload = dict(PAYLOADS["E-OPRO-BASELINE"], best_score=0.5)
        records["E-OPRO-BASELINE"]["stdout"] = json.dumps(payload)
        records["E-OPRO-BASELINE"]["stdout_sha256"] = sha(records["E-OPRO-BASELINE"]["stdout"])
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("below baseline" in e for e in errors)


def _with_m1(records, **overrides):
    acceptance = dict(PAYLOADS["E-M1-RE-DEMO"]["acceptance"], **overrides.pop("acceptance", {}))
    payload = dict(PAYLOADS["E-M1-RE-DEMO"], acceptance=acceptance, **overrides)
    if overrides.get("acceptance_absent"):
        payload.pop("acceptance", None)
        payload.pop("acceptance_absent", None)
    records["E-M1-RE-DEMO"]["stdout"] = json.dumps(payload)
    records["E-M1-RE-DEMO"]["stdout_sha256"] = sha(records["E-M1-RE-DEMO"]["stdout"])


def test_m1_regression_hiding_behind_the_headline_recall_still_blocks(tmp_path):
    """The reason the gate judges the earned figure. A run whose headline still
    clears 0.90 because eleven self-answering cases cannot fail, while the
    cases that can fail have dropped below it, must not pass."""
    decision, errors = decide(write_pack(tmp_path, mutate=lambda r: _with_m1(
        r, acceptance={"evidence_recall_at_10": 0.9137,
                       "evidence_recall_excluding_verbatim": 0.83,
                       "evidence_recall_meets_target": False,
                       "meets_acceptance_targets": False})))
    assert decision == "AMBER"
    assert any("Recall@10" in e for e in errors)


def test_m1_recall_below_target_blocks(tmp_path):
    """The acceptance target is the gate now, so it has to be able to fail."""
    decision, errors = decide(write_pack(tmp_path, mutate=lambda r: _with_m1(
        r, acceptance={"evidence_recall_at_10": 0.81,
                       "evidence_recall_excluding_verbatim": 0.81,
                       "evidence_recall_meets_target": False,
                       "meets_acceptance_targets": False})))
    assert decision == "AMBER"
    assert any("Recall@10" in e for e in errors)


def test_m1_evidence_predating_the_verbatim_split_falls_back_to_the_headline(tmp_path):
    """Evidence captured before the split existed has no
    evidence_recall_excluding_verbatim field. Such a run must still be judged
    rather than skipped -- a missing field is not a pass."""
    def mutate(records):
        acceptance = dict(PAYLOADS["E-M1-RE-DEMO"]["acceptance"],
                          evidence_recall_at_10=0.81, evidence_recall_meets_target=False,
                          meets_acceptance_targets=False)
        acceptance.pop("evidence_recall_excluding_verbatim")
        payload = dict(PAYLOADS["E-M1-RE-DEMO"], acceptance=acceptance)
        records["E-M1-RE-DEMO"]["stdout"] = json.dumps(payload)
        records["E-M1-RE-DEMO"]["stdout_sha256"] = sha(records["E-M1-RE-DEMO"]["stdout"])
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("Recall@10" in e for e in errors)


def test_m1_missing_a_decidable_abstention_band_blocks(tmp_path):
    """Near-miss abstention is allowed to be imperfect. The two bands that are
    decidable from corpus statistics are not -- missing one of those is a
    defect, not the known D-11 limitation."""
    decision, errors = decide(write_pack(tmp_path, mutate=lambda r: _with_m1(
        r, acceptance={"abstention_by_band": {"subject_outside_domain": {"held": 4, "total": 5}},
                       "abstention_decidable_bands_perfect": False,
                       "meets_acceptance_targets": False})))
    assert decision == "AMBER"
    assert any("decidable bands" in e for e in errors)


def test_m1_evidence_without_an_acceptance_block_blocks(tmp_path):
    """A run from before the demo reported acceptance metrics cannot be judged
    against them, so it must not pass by silently skipping the check."""
    decision, errors = decide(write_pack(tmp_path, mutate=lambda r: _with_m1(r, acceptance_absent=True)))
    assert decision == "AMBER"
    assert any("no acceptance block" in e for e in errors)


def test_m1_run_that_meets_targets_with_failing_cases_is_green(tmp_path):
    """The inverse guard: 17 of 159 cases fail in the default fixture and the
    gate must still be GREEN, or the gate is back to demanding a benchmark
    that only contains questions the retriever already answers."""
    decision, errors = decide(write_pack(tmp_path))
    assert decision == "GREEN", errors


def test_single_domain_matrix_does_not_demonstrate_a_shared_kernel(tmp_path):
    def mutate(records):
        payload = dict(PAYLOADS["E-DOMAIN-MATRIX"], domain_count=1)
        records["E-DOMAIN-MATRIX"]["stdout"] = json.dumps(payload)
        records["E-DOMAIN-MATRIX"]["stdout_sha256"] = sha(records["E-DOMAIN-MATRIX"]["stdout"])
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("fewer than two domains" in e for e in errors)


def test_pytest_failure_marker_blocks(tmp_path):
    def mutate(records):
        records["E-PYTEST"]["stdout"] = "1 failed, 99 passed in 0.50s\n"
        records["E-PYTEST"]["stdout_sha256"] = sha(records["E-PYTEST"]["stdout"])
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("failed-test marker" in e for e in errors)


def test_pytest_without_an_explicit_passed_count_blocks(tmp_path):
    """Silence is not success: a run that produced no result line must not pass."""
    def mutate(records):
        records["E-PYTEST"]["stdout"] = "collected 0 items\n"
        records["E-PYTEST"]["stdout_sha256"] = sha(records["E-PYTEST"]["stdout"])
    decision, errors = decide(write_pack(tmp_path, mutate=mutate))
    assert decision == "AMBER"
    assert any("explicit" in e for e in errors)
