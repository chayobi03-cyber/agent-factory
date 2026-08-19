import json
from unittest.mock import patch

import pytest

from src.m1b_fred import FredConfigurationError, fetch_pit_evidence


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._payload


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(FredConfigurationError):
        fetch_pit_evidence(
            series_id="FEDFUNDS",
            observation_time="2020-01-01",
            cutoff_date="2020-02-01",
        )


def test_binds_observation_to_requested_vintage(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    responses = iter(
        [
            {"vintage_dates": ["2020-02-01"]},
            {"observations": [{"date": "2020-01-01", "value": "1.55"}]},
        ]
    )

    def fake_urlopen(request, timeout):
        params = request.full_url.split("?", 1)[1]
        assert "series_id=FEDFUNDS" in params
        assert "realtime_start=2020-02-01" in params
        assert "realtime_end=2020-02-01" in params
        return FakeResponse(next(responses))

    with patch("src.m1b_fred.urlopen", side_effect=fake_urlopen):
        evidence = fetch_pit_evidence(
            series_id="FEDFUNDS",
            observation_time="2020-01-01",
            cutoff_date="2020-02-01",
        )

    assert evidence.value == 1.55
    assert evidence.realtime_start == "2020-02-01"
    assert evidence.pit_proven is True
    assert evidence.request_parameters["observation_start"] == "2020-01-01"


def test_adapter_does_not_invent_intraday_timestamp():
    assert "does not manufacture" in fetch_pit_evidence.__doc__.lower()
