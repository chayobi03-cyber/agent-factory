from evaluation_harness import FactoryKernelHarness


def test_harness_contains_required_minimum_cases():
    ids = {case.case_id for case in FactoryKernelHarness().cases}
    assert {
        "supported_claim",
        "unsupported_claim",
        "high_risk_claim",
        "review_approve",
        "review_reject",
        "review_modify",
        "stale_snapshot",
        "contradictory_evidence",
        "retry_loop",
        "duplicate_execution",
    } <= ids


def test_harness_ground_truth_is_not_llm():
    report = FactoryKernelHarness().report()
    assert report["ground_truth"] == "deterministic"


def test_harness_reports_current_kernel_gaps_explicitly():
    report = FactoryKernelHarness().report()
    failures = {item["case_id"] for item in report["results"] if not item["passed"]}
    # These are intentional red cases until the corresponding kernel controls exist.
    assert "contradictory_evidence" in failures
    assert "review_modify" in failures
