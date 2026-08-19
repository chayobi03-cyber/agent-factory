from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FRED_API_BASE = "https://api.stlouisfed.org/fred"


class FredConfigurationError(RuntimeError):
    """Raised when the first-party FRED API cannot be used safely."""


class FredResponseError(RuntimeError):
    """Raised when a first-party FRED response is invalid or rejected."""


@dataclass(frozen=True)
class FredObservationEvidence:
    series_id: str
    observation_time: str
    value: float
    realtime_start: str
    realtime_end: str
    vintage_dates: tuple[str, ...]
    request_parameters: dict[str, str]

    @property
    def pit_proven(self) -> bool:
        return bool(self.vintage_dates) and self.realtime_start in self.vintage_dates


def _api_key() -> str:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        raise FredConfigurationError("FRED_API_KEY is required for first-party vintage/PIT evidence")
    return key


def _get_json(path: str, params: dict[str, str]) -> dict:
    query = urlencode(params)
    request = Request(
        f"{FRED_API_BASE}/{path}?{query}",
        headers={"User-Agent": "agent-factory-m1b/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310 - fixed HTTPS first-party endpoint
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network-specific failure
        raise FredResponseError(f"FRED request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise FredResponseError("FRED response must be a JSON object")
    if "error_code" in payload:
        raise FredResponseError(
            f"FRED API error {payload.get('error_code')}: {payload.get('error_message', 'unknown error')}"
        )
    return payload


def fetch_pit_evidence(
    *,
    series_id: str,
    observation_time: str,
    cutoff_date: str,
) -> FredObservationEvidence:
    """Verify an observation against a specific FRED vintage date.

    FRED exposes the vintage/realtime boundary at date granularity here. The
    adapter records the exact request parameters and does not manufacture an
    intraday publication timestamp that the source does not provide.
    """
    api_key = _api_key()
    common = {"series_id": series_id, "api_key": api_key, "file_type": "json"}

    vintage_payload = _get_json(
        "series/vintagedates",
        {**common, "realtime_start": cutoff_date, "realtime_end": cutoff_date},
    )
    vintage_dates = tuple(str(item) for item in vintage_payload.get("vintage_dates", []))

    observations_payload = _get_json(
        "series/observations",
        {
            **common,
            "observation_start": observation_time,
            "observation_end": observation_time,
            "realtime_start": cutoff_date,
            "realtime_end": cutoff_date,
        },
    )
    observations = observations_payload.get("observations", [])
    if not observations:
        raise FredResponseError(
            f"No {series_id} observation for {observation_time} at vintage {cutoff_date}"
        )

    record = observations[0]
    try:
        value = float(record["value"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FredResponseError("FRED observation value is not numeric") from exc

    return FredObservationEvidence(
        series_id=series_id,
        observation_time=observation_time,
        value=value,
        realtime_start=cutoff_date,
        realtime_end=cutoff_date,
        vintage_dates=vintage_dates,
        request_parameters={
            "observation_start": observation_time,
            "observation_end": observation_time,
            "realtime_start": cutoff_date,
            "realtime_end": cutoff_date,
        },
    )
