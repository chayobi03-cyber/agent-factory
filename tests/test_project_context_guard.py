from pathlib import Path

import yaml

from scripts.validate_project_context import (
    EXPECTED_BRANCH,
    EXPECTED_GOVERNANCE_NAMESPACE,
    EXPECTED_PROJECT,
    EXPECTED_REPOSITORY,
    normalize_remote,
    resolve_branch,
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


def test_boundary_references_are_provenance_allowlisted():
    root = Path(__file__).resolve().parents[1]
    findings = scan_cross_project_references(root)
    assert findings == []


def test_current_session_state_declares_canonical_identity():
    root = Path(__file__).resolve().parents[1]
    state = yaml.safe_load(
        (root / "docs/governance/CURRENT_SESSION_STATE.yaml").read_text(encoding="utf-8")
    )
    assert state["project_id"] == EXPECTED_PROJECT
    assert state["repository"] == EXPECTED_REPOSITORY
    assert state["working_branch"] == EXPECTED_BRANCH
    assert state["governance_namespace"] == EXPECTED_GOVERNANCE_NAMESPACE


def test_resolve_branch_uses_ci_ref_when_git_is_detached(monkeypatch):
    monkeypatch.setenv("GITHUB_HEAD_REF", "")
    monkeypatch.setenv("GITHUB_REF_NAME", EXPECTED_BRANCH)

    from scripts import validate_project_context as guard

    original = guard.run_git
    monkeypatch.setattr(
        guard,
        "run_git",
        lambda *args: "" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = resolve_branch()
    assert branch == EXPECTED_BRANCH
    assert source == "github.ref"


def test_resolve_branch_uses_base_ref_for_pull_request_events(monkeypatch):
    """Root-cause regression test (2026-08-24): a pull_request-triggered run
    checks out the PR's HEAD in a detached state with GITHUB_HEAD_REF set to
    the *source* branch name (e.g. a fix branch) -- never EXPECTED_BRANCH --
    while GITHUB_BASE_REF is the PR's target branch. This guard must key off
    the base ref, not the head ref, or every PR ever fails Context Guard
    regardless of content. See 11_Audit/LSN-0001 and
    docs/governance/CER_CI_PR_EXECUTION_LESSONS_2026-08-20.md."""
    monkeypatch.setenv("GITHUB_HEAD_REF", "fix/some-unrelated-branch-name")
    monkeypatch.setenv("GITHUB_BASE_REF", EXPECTED_BRANCH)
    monkeypatch.setenv("GITHUB_REF_NAME", "refs/pull/13/merge")

    from scripts import validate_project_context as guard

    original = guard.run_git
    monkeypatch.setattr(
        guard,
        "run_git",
        lambda *args: "" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = resolve_branch()
    assert branch == EXPECTED_BRANCH
    assert source == "github.base_ref"
