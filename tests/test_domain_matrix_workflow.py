from pathlib import Path

from synthetic_domain_matrix import FixtureDomainPack, load_specs, run_matrix


FIXTURES = Path("fixtures/domain_matrix/domain_packs.yaml")


def test_multiple_domains_use_one_kernel_workflow():
    specs = load_specs(FIXTURES)
    results = run_matrix(FIXTURES, repository_commit="TEST-MATRIX")

    assert len(specs) == 4
    assert {item["domain_id"] for item in results} == {"RE", "EMI", "CST", "ESD"}
    assert all(item["verification"]["supported"] for item in results)
    assert all(item["evaluation"]["passed"] for item in results)
    assert all(item["cer_decision"] == "PASS" for item in results)
    assert all(item["workflow_executed"] for item in results)
    assert all(item["report_rendered"] for item in results)
    assert all(item["trace_events"] >= 6 for item in results)


def test_all_domain_capabilities_are_exercised():
    results = run_matrix(FIXTURES, repository_commit="TEST-MATRIX")
    expected = set(FixtureDomainPack.CAPABILITIES)
    assert all(set(item["capabilities_exercised"]) == expected for item in results)


def test_domain_fixtures_are_explicitly_non_production():
    specs = load_specs(FIXTURES)
    assert specs
    assert all(item["workflow"] == "engineering_qa" for item in specs)


def test_domain_specific_fact_does_not_change_workflow_contract():
    results = run_matrix(FIXTURES, repository_commit="TEST-MATRIX")
    required = {
        "domain_id",
        "workflow",
        "capabilities_exercised",
        "verification",
        "evaluation",
        "cer_decision",
        "workflow_executed",
        "report_rendered",
        "risk_level",
        "trace_events",
    }
    assert all(set(result) == required for result in results)
