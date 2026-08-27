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
        # Renamed from `contradictory_evidence` on 2026-08-26. The rule it
        # tested fired on any claim citing two items with differing text, which
        # is plurality rather than contradiction, so the case had been green for
        # a reason unrelated to its name.
        "conflicting_revisions",
        "differing_evidence_is_not_contradiction",
        "retry_loop",
        "duplicate_execution",
    } <= ids


def test_semantic_contradiction_is_a_pinned_gap_not_a_capability():
    """The kernel detects one document cited at two revisions, and nothing else.

    Two documents asserting incompatible things is a semantic judgement no
    lexical method here can make (OPEN_DECISIONS D-11). This asserts the
    benchmark still says so, so the gap cannot quietly be read as coverage.
    """
    report = FactoryKernelHarness().report()
    by_id = {item["case_id"]: item for item in report["results"]}
    # Detected and reported, but not gated on: the version that referred these
    # also referred 15 benchmark questions that were asking about the difference
    # between two revisions. See OPEN_DECISIONS D-14.
    assert by_id["conflicting_revisions"]["actual_result"] == "PASS"
    assert "not gated" in by_id["conflicting_revisions"]["detail"]
    assert by_id["differing_evidence_is_not_contradiction"]["actual_result"] == "PASS"


def test_harness_ground_truth_is_not_llm():
    report = FactoryKernelHarness().report()
    assert report["ground_truth"] == "deterministic"


def test_harness_reports_current_kernel_gaps_explicitly():
    report = FactoryKernelHarness().report()
    failures = {item["case_id"] for item in report["results"] if not item["passed"]}
    assert failures == set()
