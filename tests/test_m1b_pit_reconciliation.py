import json
from pathlib import Path


FIXTURE = Path("fixtures/m1b/pit_reconciliation_2020-01.json")
EXPECTED_SERIES = {"FEDFUNDS", "DEXUSEU", "T10YIE", "UNRATE", "CPIAUCSL"}


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_five_series_have_first_party_pit_evidence_and_reconciliation_coverage():
    payload = load_fixture()
    rows = payload["observations"]
    assert {row["series_id"] for row in rows} == EXPECTED_SERIES
    assert len(rows) == 5
    for row in rows:
        pit = row["pit"]
        reconciliation = row["reconciliation"]
        assert pit["available_as_of"]
        assert pit["vintage_boundary"]
        assert reconciliation["group"]
        assert reconciliation["status"] in {"matched", "discrepancy", "accepted"}


def test_cross_source_discrepancy_is_preserved_not_overwritten():
    row = next(row for row in load_fixture()["observations"] if row["series_id"] == "DEXUSEU")
    reconciliation = row["reconciliation"]
    assert reconciliation["status"] == "discrepancy"
    assert reconciliation["comparator_value"] != row["value"]
    assert "not identical" in reconciliation["notes"]


def test_t10yie_reconciliation_does_not_claim_standalone_source_equality():
    row = next(row for row in load_fixture()["observations"] if row["series_id"] == "T10YIE")
    assert row["reconciliation"]["status"] == "accepted"
    assert "standalone Treasury series is not asserted" in row["reconciliation"]["notes"]


def test_fixture_is_deterministic_json():
    payload = load_fixture()
    assert json.dumps(payload, sort_keys=True, separators=(",", ":"))
