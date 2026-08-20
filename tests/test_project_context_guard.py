from pathlib import Path

from scripts.validate_project_context import (
    EXPECTED_BRANCH,
    EXPECTED_GOVERNANCE_NAMESPACE,
    EXPECTED_PROJECT,
    EXPECTED_REPOSITORY,
    normalize_remote,
    scan_cross_project_references,
)


def test_project_context_constants_are_canonical():
    assert EXPECTED_PROJECT == "agent-factory"
    assert EXPECTED_REPOSITORY == "chayobi03-cyber/agent-factory"
    assert EXPECTED_BRANCH == "p0/opro-baseline"
    assert EXPECTED_GOVERNANCE_NAMESPACE == "AgentFactory"


def test_normalize_remote():
    assert normalize_remote("https://github.com/chayobi03-cyber/agent-factory.git") == EXPECTED_REPOSITORY
    assert normalize_remote("git@github.com:chayobi03-cyber/agent-factory.git") == EXPECTED_REPOSITORY


def test_boundary_lesson_is_the_only_allowlisted_investment_reference():
    root = Path(__file__).resolve().parents[1]
    findings = scan_cross_project_references(root)
    assert findings == []


def test_current_session_state_declares_agentfactory_identity():
    root = Path(__file__).resolve().parents[1]
    state = (root / "docs/governance/CURRENT_SESSION_STATE.yaml").read_text(encoding="utf-8")
    assert "repository: chayobi03-cyber/agent-factory" in state
    assert "working_branch: p0/opro-baseline" in state
    # Older valid states did not yet carry these fields; current remediation should.
    assert "session_id: 2026-08-20-repository-integrity-context-remediation" in state
    assert "gate: REVIEW_REQUIRED" in state
