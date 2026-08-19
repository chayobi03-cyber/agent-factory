from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_text(canonical_json(value))


def raw_payload_hash(observations: Sequence[Mapping[str, Any]]) -> str:
    normalized = [dict(row) for row in observations]
    return sha256_json(normalized)


def replay_key(*, series_id: str, observation_time: str, raw_sha256: str, transformation_version: str) -> str:
    payload = {
        "series_id": series_id,
        "observation_time": observation_time,
        "raw_sha256": raw_sha256,
        "transformation_version": transformation_version,
    }
    return sha256_json(payload)


def derived_hash(record: Mapping[str, Any]) -> str:
    payload = {k: record[k] for k in sorted(record) if k not in {"derived_hash", "record_id"}}
    return sha256_json(payload)
