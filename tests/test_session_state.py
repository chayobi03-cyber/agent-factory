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
