import importlib
from pathlib import Path

import pytest
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
    assert EXPECTED_BRANCH == "main"
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
    # This asserts the `push`-event fallback, where GitHub does not set
    # GITHUB_BASE_REF at all. It must be cleared explicitly rather than left
    # to the ambient environment: under a pull_request-triggered CI run the
    # real GITHUB_BASE_REF leaks in, base-ref resolution correctly wins, and
    # the test fails on its source assertion even though the code is right.
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
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


# --- D-02: the guard asks "where would this land", locally too ---------------


def test_local_override_lets_a_feature_branch_resolve_its_landing_target(monkeypatch):
    """Before this, the guard compared the *checkout name* to EXPECTED_BRANCH,
    so it failed on every local feature branch and the only way to verify a
    change was to name the checkout after the trunk."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", EXPECTED_BRANCH)

    from scripts import validate_project_context as guard

    original = guard.run_git
    monkeypatch.setattr(
        guard,
        "run_git",
        lambda *args: "feature/some-local-work" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = guard.resolve_branch()
    assert branch == EXPECTED_BRANCH
    assert source == "local.target_branch_override"


def test_local_override_is_ignored_inside_github_actions(monkeypatch):
    """The override must never be able to weaken CI. With GITHUB_ACTIONS set it
    is not consulted at all, whatever it says."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", "anything-at-all")

    from scripts import validate_project_context as guard

    original = guard.run_git
    monkeypatch.setattr(
        guard,
        "run_git",
        lambda *args: "some-ci-checkout" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = guard.resolve_branch()
    assert branch == "some-ci-checkout"
    assert source == "git.branch"


def test_absent_override_leaves_resolution_unchanged(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("AGENTFACTORY_TARGET_BRANCH", raising=False)

    from scripts import validate_project_context as guard

    original = guard.run_git
    monkeypatch.setattr(
        guard,
        "run_git",
        lambda *args: "feature/some-local-work" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = guard.resolve_branch()
    assert branch == "feature/some-local-work"
    assert source == "git.branch"


# --- D-02, second half: both validators must resolve the same way ------------
#
# The override was added to the Context Guard and not to the resume validator,
# so on a feature checkout CONTEXT_GUARD=PASS sat directly above
# RESUME_STATUS=RESUME_BLOCKED -- for the branch-name reason the override
# exists to remove. These pin the two together rather than testing the second
# copy in isolation, because the failure was the *disagreement*, not either
# implementation on its own.


@pytest.mark.parametrize(
    "module_name",
    ["scripts.validate_project_context", "scripts.validate_session_resume"],
)
def test_both_validators_honour_the_local_landing_target(monkeypatch, module_name):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", EXPECTED_BRANCH)

    module = importlib.import_module(module_name)
    original = module.run_git
    monkeypatch.setattr(
        module,
        "run_git",
        lambda *args: "feature/local" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = module.resolve_branch()
    assert branch == EXPECTED_BRANCH
    assert source == "local.target_branch_override"


@pytest.mark.parametrize(
    "module_name",
    ["scripts.validate_project_context", "scripts.validate_session_resume"],
)
def test_neither_validator_honours_the_override_inside_ci(monkeypatch, module_name):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", "anything-at-all")

    module = importlib.import_module(module_name)
    original = module.run_git
    monkeypatch.setattr(
        module,
        "run_git",
        lambda *args: "some-ci-checkout" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = module.resolve_branch()
    assert branch == "some-ci-checkout"
    assert source == "git.branch"


# --- one handoff pointer, followed by every validator ------------------------


def test_the_guard_follows_the_handoff_named_by_state(tmp_path, monkeypatch):
    """The path was hardcoded here while the resume validator read state.handoff.

    The two agreed only because nobody had written a second handoff document
    yet. The first one would have left this guard checking the old document's
    identity and the resume validator checking the new one's, with both green
    and each satisfied by a different file.
    """
    from scripts import validate_project_context as guard

    root = Path(__file__).resolve().parents[1]
    (tmp_path / "docs" / "governance").mkdir(parents=True)
    for name in ("CURRENT_SESSION_STATE.yaml", "AGENT_FACTORY_SCOPE_V1.md"):
        (tmp_path / "docs" / "governance" / name).write_text(
            (root / "docs" / "governance" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    state_path = tmp_path / "docs" / "governance" / "CURRENT_SESSION_STATE.yaml"

    import yaml

    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    declared = state["handoff"]
    assert declared.endswith("NEXT_SESSION_HANDOFF_2026-08-30.md"), (
        "the state's handoff pointer moved; this test names the file it expects"
    )

    # Point state at a handoff carrying the wrong identity. If the guard were
    # still reading a path of its own it would never see this file.
    (tmp_path / "docs" / "governance" / "OTHER_HANDOFF.md").write_text(
        "project_id: `not-agent-factory`\n", encoding="utf-8"
    )
    state["handoff"] = "docs/governance/OTHER_HANDOFF.md"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", EXPECTED_BRANCH)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    # tmp_path is not a git checkout; the identity checks under test do not need
    # one, so git answers as the real repository would.
    monkeypatch.setattr(
        guard, "run_git",
        lambda *args: ("https://github.com/chayobi03-cyber/agent-factory.git"
                       if args[:1] == ("config",) else EXPECTED_BRANCH),
    )
    # The tree scans shell out to git themselves and are not what is under test.
    monkeypatch.setattr(guard, "scan_cross_project_references", lambda root: [])
    monkeypatch.setattr(guard, "scan_forbidden_paths", lambda root: [])
    failures = guard.validate_identity(tmp_path)
    assert any("handoff" in f for f in failures), failures


def test_a_missing_handoff_target_is_an_error_not_a_pass(tmp_path):
    from scripts import validate_project_context as guard

    root = Path(__file__).resolve().parents[1]
    (tmp_path / "docs" / "governance").mkdir(parents=True)
    for name in ("CURRENT_SESSION_STATE.yaml", "AGENT_FACTORY_SCOPE_V1.md"):
        (tmp_path / "docs" / "governance" / name).write_text(
            (root / "docs" / "governance" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    state_path = tmp_path / "docs" / "governance" / "CURRENT_SESSION_STATE.yaml"

    import yaml

    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    state["handoff"] = "docs/governance/NO_SUCH_HANDOFF.md"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    with pytest.raises(guard.ContextGuardError, match="missing file"):
        guard.validate_identity(tmp_path)
