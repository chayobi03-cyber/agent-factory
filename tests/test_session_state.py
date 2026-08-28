from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validate_session_state import SessionStateError, validate


def test_session_state_has_required_resume_fields(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    handoff = tmp_path / "handoff.md"
    handoff.write_text("# handoff\n", encoding="utf-8")

    state = {
        "state_version": 1,
        "session_id": "test-session",
        "phase": "TEST",
        "gate": "NOT_GREEN",
        "repository": "chayobi03-cyber/agent-factory",
        "working_branch": "p0/opro-baseline",
        "audited_baseline_sha": "abc",
        "task_id": "TEST-1",
        "current_task": "test",
        "last_completed": [],
        "current_focus": [],
        "next_action": ["test"],
        "blocked_until": [],
        "forbidden": [],
        "handoff": str(handoff),
        "updated_at_utc": "2026-08-18T00:00:00Z",
    }

    def fake_git(*args: str) -> str:
        if args == ("branch", "--show-current"):
            return "p0/opro-baseline"
        if args == ("config", "--get", "remote.origin.url"):
            return "https://github.com/chayobi03-cyber/agent-factory.git"
        if args == ("rev-parse", "HEAD"):
            return "deadbeef"
        raise AssertionError(args)

    monkeypatch.setattr("scripts.validate_session_state.run_git", fake_git)
    result = validate(state)

    assert "resume_checks=PASS" in result


def test_session_state_branch_mismatch_is_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    handoff = tmp_path / "handoff.md"
    handoff.write_text("# handoff\n", encoding="utf-8")

    state = {
        "state_version": 1,
        "session_id": "test-session",
        "phase": "TEST",
        "gate": "NOT_GREEN",
        "repository": "chayobi03-cyber/agent-factory",
        "working_branch": "p0/opro-baseline",
        "audited_baseline_sha": "abc",
        "task_id": "TEST-1",
        "current_task": "test",
        "last_completed": [],
        "current_focus": [],
        "next_action": ["test"],
        "blocked_until": [],
        "forbidden": [],
        "handoff": str(handoff),
        "updated_at_utc": "2026-08-18T00:00:00Z",
    }

    monkeypatch.setattr(
        "scripts.validate_session_state.run_git",
        lambda *args: "main" if args == ("branch", "--show-current") else "https://github.com/chayobi03-cyber/agent-factory.git",
    )

    with pytest.raises(SessionStateError, match="branch mismatch"):
        validate(state)


# --- D-02, third and last: this validator was missed on 2026-08-25 -----------


def test_local_override_lets_a_feature_branch_resolve_its_landing_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Context Guard and the resume validator both took this escape hatch
    when D-02 was settled; this one did not, so the three disagreed about what
    a valid local checkout was and nothing noticed until all three were run."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", "main")

    from scripts import validate_session_state as validator

    monkeypatch.setattr(validator, "run_git", lambda *args: "feature/some-local-work")
    assert validator.resolve_branch() == "main"


def test_local_override_is_ignored_inside_github_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The override must never be able to weaken CI."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("AGENTFACTORY_TARGET_BRANCH", "anything-at-all")

    from scripts import validate_session_state as validator

    monkeypatch.setattr(validator, "run_git", lambda *args: "some-ci-checkout")
    assert validator.resolve_branch() == "some-ci-checkout"


def test_absent_override_leaves_resolution_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("AGENTFACTORY_TARGET_BRANCH", raising=False)

    from scripts import validate_session_state as validator

    monkeypatch.setattr(validator, "run_git", lambda *args: "feature/some-local-work")
    assert validator.resolve_branch() == "feature/some-local-work"


def test_all_three_validators_honour_the_same_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """One definition of "which branch is this", not three.

    D-02 was recorded as resolved "in both validators" when there were three.
    This asserts the set rather than the pair, so adding a fourth that forgets
    the hatch fails here rather than in someone's terminal.
    """
    import ast

    root = Path(__file__).resolve().parents[1] / "scripts"
    validators = [
        "validate_project_context.py",
        "validate_session_resume.py",
        "validate_session_state.py",
    ]
    for name in validators:
        source = (root / name).read_text(encoding="utf-8")
        assert "AGENTFACTORY_TARGET_BRANCH" in source, f"{name} ignores the override"
        assert "GITHUB_ACTIONS" in source, f"{name} would let the override weaken CI"
        ast.parse(source)


def test_the_suite_does_not_inherit_the_local_branch_override() -> None:
    """The guard that made this file's failure look intermittent.

    `test_session_state_has_required_resume_fields` stubs git to return the
    branch its fixture names, and `resolve_branch` prefers
    AGENTFACTORY_TARGET_BRANCH over that stub. With the variable exported --
    which the handoff tells contributors to do before running the validators --
    the branch check compared the override against the fixture's branch and
    raised. Set: fail. Unset: pass. Deterministic, and indistinguishable from a
    flake unless you notice which shell each run happened in.

    tests/conftest.py clears it for every test; this asserts the clearing is
    real rather than assumed.
    """
    import os

    assert "AGENTFACTORY_TARGET_BRANCH" not in os.environ
    assert "GITHUB_ACTIONS" not in os.environ
