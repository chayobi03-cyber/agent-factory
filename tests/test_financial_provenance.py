import json

from scripts.financial_provenance import build_record, canonical_json, sha256_bytes, _derived_payload


def make_record(*, raw=b"raw", retrieval_time="2026-08-19T00:00:00+00:00"):
    return build_record(
        series_id="TEST-1",
        provider="test-provider",
        dataset="test-dataset",
        endpoint_or_locator="https://example.invalid/series",
        authority="test-authority",
        retrieval_method="fixture",
        retrieval_version="v1",
        retrieved_at_utc=retrieval_time,
        source_as_of="2026-08-18",
        request_parameters={"start": "2026-08-01"},
        raw_payload_sha256=sha256_bytes(raw),
        observation_time="2026-08-18",
        value=1.25,
        unit="unit",
        currency=None,
        available_as_of="2026-08-18T12:00:00+00:00",
        effective_from=None,
        effective_to=None,
        normalization="identity",
        transformation_version="v1",
        input_record_ids=[],
        cross_source_group=None,
        tolerance=None,
        discrepancy_notes=None,
    )


def test_raw_snapshot_hash_is_stable():
    payload = b'{"value":1}'
    assert sha256_bytes(payload) == sha256_bytes(payload)


def test_replay_hash_is_independent_of_retrieval_timestamp():
    first = make_record(retrieval_time="2026-08-19T00:00:00+00:00")
    second = make_record(retrieval_time="2026-08-20T00:00:00+00:00")
    assert first["snapshot"]["retrieved_at_utc"] != second["snapshot"]["retrieved_at_utc"]
    assert first["provenance"]["derived_hash"] == second["provenance"]["derived_hash"]
    assert first["replay"]["replay_key"] == second["replay"]["replay_key"]


def test_derived_hash_matches_canonical_replay_payload():
    record = make_record()
    assert sha256_bytes(canonical_json(_derived_payload(record))) == record["provenance"]["derived_hash"]
    assert record["replay"]["expected_output_sha256"] == record["provenance"]["derived_hash"]
    assert record["record_id"] == f"FPR-{record['provenance']['derived_hash'][:20]}"


def test_raw_payload_change_changes_hash_chain():
    first = make_record(raw=b"raw-a")
    second = make_record(raw=b"raw-b")
    assert first["snapshot"]["raw_payload_sha256"] != second["snapshot"]["raw_payload_sha256"]
    assert first["provenance"]["source_hash"] != second["provenance"]["source_hash"]
    assert first["provenance"]["derived_hash"] != second["provenance"]["derived_hash"]
    assert first["replay"]["replay_key"] != second["replay"]["replay_key"]


def test_provenance_record_contains_required_chain_fields():
    record = make_record()
    assert record["snapshot"]["raw_payload_sha256"] == sha256_bytes(b"raw")
    assert record["provenance"]["source_hash"]
    assert record["provenance"]["derived_hash"]
    assert record["replay"]["replay_key"]
    assert record["replay"]["deterministic"] is True
    assert record["reconciliation"]["status"] == "unverified"


def test_canonical_record_is_json_serializable():
    record = build_record(
        series_id="TEST-2",
        provider="test-provider",
        dataset="test-dataset",
        endpoint_or_locator="fixture",
        authority="test-authority",
        retrieval_method="fixture",
        retrieval_version="v1",
        retrieved_at_utc="2026-08-19T00:00:00+00:00",
        source_as_of=None,
        request_parameters={},
        raw_payload_sha256=sha256_bytes(b"raw-2"),
        observation_time="2026-08-18",
        value=2.0,
        unit="percent",
        currency=None,
        available_as_of="2026-08-18T12:00:00+00:00",
        effective_from=None,
        effective_to=None,
        normalization="identity",
        transformation_version="v1",
        input_record_ids=["FPR-upstream"],
        cross_source_group="GROUP-1",
        tolerance=0.01,
        discrepancy_notes=None,
    )
    json.dumps(record, sort_keys=True)
