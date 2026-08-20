from pathlib import Path

import yaml

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


def test_current_session_state_declares_canonical_identity():
    root = Path(__file__).resolve().parents[1]
    state = yaml.safe_load(
        (root / "docs/governance/CURRENT_SESSION_STATE.yaml").read_text(encoding="utf-8")
    )
    assert state["repository"] == EXPECTED_REPOSITORY
    assert state["working_branch"] == EXPECTED_BRANCH
    assert state.get("project_id", EXPECTED_PROJECT) == EXPECTED_PROJECT
    assert state.get("governance_namespace", EXPECTED_GOVERNANCE_NAMESPACE) == EXPECTED_GOVERNANCE_NAMESPACE
