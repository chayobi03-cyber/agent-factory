from __future__ import annotations

import pytest

from src.m2_historical import (
    M2HistoricalError,
    canonical_hash,
    replay_key,
    require_historical_evidence,
    validate_partitions,
    validate_pit,
    validate_provenance_identity,
)


def test_m2_01_stale_vintage_rejected() -> None:
    with pytest.raises(M2HistoricalError, match="vintage/revision"):
        validate_pit(
            observation_time="2020-01-01T00:00:00+00:00",
            availability_time="2020-01-10T00:00:00+00:00",
            vintage_as_of="2020-02-01T00:00:00+00:00",
            cutoff_time="2020-01-31T23:59:59+00:00",
        )


def test_m2_02_future_timestamp_rejected() -> None:
    with pytest.raises(M2HistoricalError, match="future observation"):
        validate_pit(
            observation_time="2020-02-01T00:00:00+00:00",
            availability_time="2020-02-01T00:00:00+00:00",
            vintage_as_of="2020-02-01T00:00:00+00:00",
            cutoff_time="2020-01-31T23:59:59+00:00",
        )


def test_m2_03_pit_cutoff_violation_rejected() -> None:
    with pytest.raises(M2HistoricalError, match="PIT availability"):
        validate_pit(
            observation_time="2020-01-01T00:00:00+00:00",
            availability_time="2020-02-02T00:00:00+00:00",
            vintage_as_of="2020-02-02T00:00:00+00:00",
            cutoff_time="2020-01-31T23:59:59+00:00",
        )


def test_m2_04_train_oos_overlap_rejected() -> None:
    with pytest.raises(M2HistoricalError, match="partition overlap"):
        validate_partitions(
            train=("2020-01-01", "2021-12-31"),
            validation=("2022-01-01", "2022-12-31"),
            oos=("2021-07-01", "2023-12-31"),
        )


def test_m2_05_revised_vs_original_provenance_mismatch_detected() -> None:
    with pytest.raises(M2HistoricalError, match="source hash mismatch"):
        validate_provenance_identity(
            source_hash="revision-hash",
            expected_source_hash="original-hash",
            dataset_id="dataset-A",
            expected_dataset_id="dataset-A",
            experiment_id="M2-E1",
            expected_experiment_id="M2-E1",
        )


def test_m2_06_raw_payload_order_invariance() -> None:
    left = {"b": [2, 1], "a": {"z": 3, "y": 4}}
    right = {"a": {"y": 4, "z": 3}, "b": [2, 1]}
    assert canonical_hash(left) == canonical_hash(right)


def test_m2_07_transform_version_changes_replay_key() -> None:
    common = {
        "source": "FRED",
        "dataset_id": "CPIAUCSL",
        "dataset_version": "2025-v1",
        "vintage_id": "2025-02-01",
        "pit_cutoff": "2025-02-01T00:00:00Z",
        "partition_id": "M2-H12-OOS",
        "case_id": "M2-H12",
    }
    key_a = replay_key(transform_version="m2-transform-v1", **common)
    key_b = replay_key(transform_version="m2-transform-v2", **common)
    assert key_a != key_b


def test_m2_08_source_hash_mismatch_detected() -> None:
    with pytest.raises(M2HistoricalError, match="source hash mismatch"):
        validate_provenance_identity(
            source_hash="actual",
            expected_source_hash="expected",
            dataset_id="dataset-A",
            expected_dataset_id="dataset-A",
            experiment_id="M2-E1",
            expected_experiment_id="M2-E1",
        )


def test_m2_09_dataset_identity_mismatch_detected() -> None:
    with pytest.raises(M2HistoricalError, match="dataset identity mismatch"):
        validate_provenance_identity(
            source_hash="same",
            expected_source_hash="same",
            dataset_id="dataset-B",
            expected_dataset_id="dataset-A",
            experiment_id="M2-E1",
            expected_experiment_id="M2-E1",
        )


def test_m2_10_experiment_identity_mismatch_detected() -> None:
    with pytest.raises(M2HistoricalError, match="experiment identity mismatch"):
        validate_provenance_identity(
            source_hash="same",
            expected_source_hash="same",
            dataset_id="dataset-A",
            expected_dataset_id="dataset-A",
            experiment_id="M2-E2",
            expected_experiment_id="M2-E1",
        )


def test_m2_11_missing_evidence_artifact_rejected() -> None:
    with pytest.raises(M2HistoricalError, match="artifact"):
        require_historical_evidence(
            artifact_id=None,
            execution_sha=None,
            execution_status="VERIFIED",
            synthetic_fixture=False,
        )


def test_m2_12_synthetic_fixture_cannot_satisfy_historical_gate() -> None:
    with pytest.raises(M2HistoricalError, match="synthetic fixture"):
        require_historical_evidence(
            artifact_id="artifact-1",
            execution_sha="a" * 40,
            execution_status="VERIFIED",
            synthetic_fixture=True,
        )


def test_m2_12_case_matrix_has_distinct_case_ids() -> None:
    import yaml
    from pathlib import Path

    matrix = yaml.safe_load(Path("fixtures/m2/historical_experiment_12_case.yaml").read_text())
    cases = matrix["cases"]
    assert len(cases) == 12
    assert len({case["case_id"] for case in cases}) == 12
    assert all(case["execution_identity"] == "NOT_EXECUTED" for case in cases)
