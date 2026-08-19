import json
from pathlib import Path

from src.m1b_provenance import derived_hash, raw_payload_hash, replay_key


FIXTURE = Path("fixtures/m1b/historical_series_2020-01.json")


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_contains_five_real_series():
    payload = load_fixture()
    ids = [row["series_id"] for row in payload["observations"]]
    assert len(ids) == 5
    assert len(set(ids)) == 5
    assert {"DEXUSEU", "T10YIE", "FEDFUNDS", "UNRATE", "CPIAUCSL"} == set(ids)


def test_raw_payload_hash_is_deterministic():
    payload = load_fixture()["observations"]
    assert raw_payload_hash(payload) == raw_payload_hash(list(reversed(payload)))


def test_replay_key_is_stable_and_sensitive_to_transform_version():
    raw_sha = raw_payload_hash(load_fixture()["observations"])
    key_v1 = replay_key(
        series_id="DEXUSEU",
        observation_time="2020-01-02",
        raw_sha256=raw_sha,
        transformation_version="m1b-normalize-v1",
    )
    key_v1_repeat = replay_key(
        series_id="DEXUSEU",
        observation_time="2020-01-02",
        raw_sha256=raw_sha,
        transformation_version="m1b-normalize-v1",
    )
    key_v2 = replay_key(
        series_id="DEXUSEU",
        observation_time="2020-01-02",
        raw_sha256=raw_sha,
        transformation_version="m1b-normalize-v2",
    )
    assert key_v1 == key_v1_repeat
    assert key_v1 != key_v2


def test_derived_hash_excludes_self_reference_fields():
    base = {"series_id": "UNRATE", "observation_time": "2020-01-01", "value": 3.6}
    first = derived_hash({**base, "record_id": "r1"})
    second = derived_hash({**base, "record_id": "r2", "derived_hash": "old"})
    assert first == second
