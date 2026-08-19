from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Iterable


class M2HistoricalError(ValueError):
    """Raised when an M2 historical-integrity contract is violated."""


def _parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def canonical_hash(payload: Any) -> str:
    """Hash JSON content deterministically, independent of mapping key order."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def replay_key(*, source: str, dataset_id: str, dataset_version: str, vintage_id: str,
               pit_cutoff: str, transform_version: str, partition_id: str, case_id: str) -> str:
    payload = {
        "case_id": case_id,
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "partition_id": partition_id,
        "pit_cutoff": pit_cutoff,
        "source": source,
        "transform_version": transform_version,
        "vintage_id": vintage_id,
    }
    return canonical_hash(payload)


def validate_pit(*, observation_time: str, availability_time: str, vintage_as_of: str, cutoff_time: str) -> None:
    observation = _parse_time(observation_time)
    availability = _parse_time(availability_time)
    vintage = _parse_time(vintage_as_of)
    cutoff = _parse_time(cutoff_time)
    if observation > cutoff:
        raise M2HistoricalError("future observation relative to experiment cutoff")
    if availability > cutoff:
        raise M2HistoricalError("PIT availability occurs after experiment cutoff")
    if vintage > cutoff:
        raise M2HistoricalError("vintage/revision is not available by experiment cutoff")
    if availability < observation:
        raise M2HistoricalError("PIT availability precedes the represented observation timestamp")


def validate_partitions(*, train: tuple[str, str], validation: tuple[str, str], oos: tuple[str, str]) -> None:
    intervals = {
        "train": (_parse_time(train[0]), _parse_time(train[1])),
        "validation": (_parse_time(validation[0]), _parse_time(validation[1])),
        "oos": (_parse_time(oos[0]), _parse_time(oos[1])),
    }
    for name, (start, end) in intervals.items():
        if start > end:
            raise M2HistoricalError(f"{name} partition start is after end")
    names = list(intervals)
    for index, left_name in enumerate(names):
        left_start, left_end = intervals[left_name]
        for right_name in names[index + 1 :]:
            right_start, right_end = intervals[right_name]
            if left_start <= right_end and right_start <= left_end:
                raise M2HistoricalError(f"partition overlap: {left_name} and {right_name}")


def validate_provenance_identity(*, source_hash: str, expected_source_hash: str,
                                  dataset_id: str, expected_dataset_id: str,
                                  experiment_id: str, expected_experiment_id: str) -> None:
    if source_hash != expected_source_hash:
        raise M2HistoricalError("source hash mismatch")
    if dataset_id != expected_dataset_id:
        raise M2HistoricalError("dataset identity mismatch")
    if experiment_id != expected_experiment_id:
        raise M2HistoricalError("experiment identity mismatch")


def require_historical_evidence(*, artifact_id: str | None, execution_sha: str | None,
                                execution_status: str, synthetic_fixture: bool) -> None:
    if synthetic_fixture:
        raise M2HistoricalError("synthetic fixture cannot satisfy historical-performance gate")
    if execution_status != "VERIFIED":
        raise M2HistoricalError("historical execution evidence is not verified")
    if not artifact_id or not execution_sha:
        raise M2HistoricalError("historical execution artifact and execution SHA are required")


def validate_record(record: dict[str, Any]) -> None:
    try:
        validate_pit(
            observation_time=record["observation_time"],
            availability_time=record["availability_time"],
            vintage_as_of=record["vintage_as_of"],
            cutoff_time=record["cutoff_time"],
        )
        validate_partitions(
            train=tuple(record["train"]),
            validation=tuple(record["validation"]),
            oos=tuple(record["oos"]),
        )
    except KeyError as exc:
        raise M2HistoricalError(f"missing M2 record field: {exc.args[0]}") from exc


def all_case_ids(cases: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(str(case["case_id"]) for case in cases)
