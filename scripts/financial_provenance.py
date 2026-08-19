#!/usr/bin/env python3
"""Build a canonical, deterministic financial provenance record from one raw snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _source_hash(
    *,
    provider: str,
    dataset: str,
    endpoint_or_locator: str,
    authority: str,
    retrieval_method: str,
    retrieval_version: str,
    raw_payload_sha256: str,
) -> str:
    return sha256_bytes(
        canonical_json(
            {
                "authority": authority,
                "dataset": dataset,
                "endpoint_or_locator": endpoint_or_locator,
                "provider": provider,
                "raw_payload_sha256": raw_payload_sha256,
                "retrieval_method": retrieval_method,
                "retrieval_version": retrieval_version,
            }
        )
    )


def _replay_key(
    *,
    series_id: str,
    raw_payload_sha256: str,
    normalization: str,
    transformation_version: str,
) -> str:
    return sha256_bytes(
        canonical_json(
            {
                "normalization": normalization,
                "raw_payload_sha256": raw_payload_sha256,
                "series_id": series_id,
                "transformation_version": transformation_version,
            }
        )
    )


def _derived_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical replay payload without self-referential hashes."""
    payload = json.loads(json.dumps(record))
    payload["provenance"]["derived_hash"] = ""
    payload["replay"]["expected_output_sha256"] = ""
    payload.pop("record_id", None)
    return payload


def build_record(
    *,
    series_id: str,
    provider: str,
    dataset: str,
    endpoint_or_locator: str,
    authority: str,
    retrieval_method: str,
    retrieval_version: str,
    retrieved_at_utc: str,
    source_as_of: str | None,
    request_parameters: dict[str, Any],
    raw_payload_sha256: str,
    observation_time: str,
    value: float,
    unit: str,
    currency: str | None,
    available_as_of: str,
    effective_from: str | None,
    effective_to: str | None,
    normalization: str,
    transformation_version: str,
    input_record_ids: list[str],
    cross_source_group: str | None,
    tolerance: float | None,
    discrepancy_notes: str | None,
) -> dict[str, Any]:
    source_hash = _source_hash(
        provider=provider,
        dataset=dataset,
        endpoint_or_locator=endpoint_or_locator,
        authority=authority,
        retrieval_method=retrieval_method,
        retrieval_version=retrieval_version,
        raw_payload_sha256=raw_payload_sha256,
    )
    replay_key = _replay_key(
        series_id=series_id,
        raw_payload_sha256=raw_payload_sha256,
        normalization=normalization,
        transformation_version=transformation_version,
    )

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "series_id": series_id,
        "source": {
            "provider": provider,
            "dataset": dataset,
            "endpoint_or_locator": endpoint_or_locator,
            "authority": authority,
            "retrieval_method": retrieval_method,
            "retrieval_version": retrieval_version,
        },
        "snapshot": {
            "retrieved_at_utc": retrieved_at_utc,
            "source_as_of": source_as_of,
            "request_parameters": request_parameters,
            "raw_payload_sha256": raw_payload_sha256,
        },
        "observation": {
            "observation_time": observation_time,
            "value": value,
            "unit": unit,
            "currency": currency,
        },
        "pit": {
            "available_as_of": available_as_of,
            "effective_from": effective_from,
            "effective_to": effective_to,
        },
        "transform": {
            "normalization": normalization,
            "transformation_version": transformation_version,
            "input_record_ids": input_record_ids,
        },
        "provenance": {
            "upstream_record_ids": input_record_ids,
            "source_hash": source_hash,
            "derived_hash": "",
        },
        "replay": {
            "replay_key": replay_key,
            "deterministic": True,
            "expected_output_sha256": "",
        },
        "reconciliation": {
            "cross_source_group": cross_source_group,
            "status": "unverified",
            "tolerance": tolerance,
            "discrepancy_notes": discrepancy_notes,
        },
        "validity": "active",
    }

    derived_hash = sha256_bytes(canonical_json(_derived_payload(record)))
    record["provenance"]["derived_hash"] = derived_hash
    record["replay"]["expected_output_sha256"] = derived_hash
    record["record_id"] = f"FPR-{derived_hash[:20]}"
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-file", required=True, help="Immutable raw snapshot file")
    parser.add_argument("--output", required=True, help="Output provenance JSON")
    parser.add_argument("--series-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--endpoint-or-locator", required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--retrieval-method", required=True)
    parser.add_argument("--retrieval-version", required=True)
    parser.add_argument("--observation-time", required=True)
    parser.add_argument("--value", required=True, type=float)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--currency")
    parser.add_argument("--available-as-of", required=True)
    parser.add_argument("--source-as-of")
    parser.add_argument("--effective-from")
    parser.add_argument("--effective-to")
    parser.add_argument("--normalization", required=True)
    parser.add_argument("--transformation-version", required=True)
    parser.add_argument("--request-parameters", default="{}")
    parser.add_argument("--input-record-id", action="append", default=[])
    parser.add_argument("--cross-source-group")
    parser.add_argument("--tolerance", type=float)
    parser.add_argument("--discrepancy-notes")
    args = parser.parse_args()

    raw = Path(args.raw_file).read_bytes()
    request_parameters = json.loads(args.request_parameters)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    record = build_record(
        series_id=args.series_id,
        provider=args.provider,
        dataset=args.dataset,
        endpoint_or_locator=args.endpoint_or_locator,
        authority=args.authority,
        retrieval_method=args.retrieval_method,
        retrieval_version=args.retrieval_version,
        retrieved_at_utc=now,
        source_as_of=args.source_as_of,
        request_parameters=request_parameters,
        raw_payload_sha256=sha256_bytes(raw),
        observation_time=args.observation_time,
        value=args.value,
        unit=args.unit,
        currency=args.currency,
        available_as_of=args.available_as_of,
        effective_from=args.effective_from,
        effective_to=args.effective_to,
        normalization=args.normalization,
        transformation_version=args.transformation_version,
        input_record_ids=args.input_record_id,
        cross_source_group=args.cross_source_group,
        tolerance=args.tolerance,
        discrepancy_notes=args.discrepancy_notes,
    )
    Path(args.output).write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "derived_hash": record["provenance"]["derived_hash"],
                "raw_payload_sha256": record["snapshot"]["raw_payload_sha256"],
                "record_id": record["record_id"],
                "replay_key": record["replay"]["replay_key"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
