from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from scripts import validate_session_resume as resume

BASELINE = "20a54b92aad0857f75c6200d984b13098c6f4927"
CHECKPOINT = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def make_fixture(tmp_path: Path, *, gate: str = "NOT_GREEN", baseline: str = BASELINE):
    contract = tmp_path / "CER_SESSION_CONTINUITY_CONTRACT_V1.md"
    contract.write_text(
        "# CER Resume Contract\n\n## RC-08\n",
        encoding="utf-8",
    )
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()
    (schema_dir / "session_state.schema.yaml").write_text(
        "schema_id: session_state\nschema_version: 1.1.0\n",
        encoding="utf-8",
    )
    handoff = tmp_path / "handoff.md"
    handoff.write_text(
        "\n".join(
            [
                "# Handoff",
                "- repository: `chayobi03-cyber/agent-factory`",
                "- branch: `p0/opro-baseline`",
                f"- audited OPRO baseline SHA: `{baseline}`",
                "OPRO promotion remains forbidden",
                "Do not enter backtest/OOS/optimization/Monte Carlo before M1-B GREEN.",
            ]
        ),
        encoding="utf-8",
    )
    state = {
        "state_version": 1,
        "session_id": "test-session",
        "phase": "TEST",
        "gate": gate,
        "repository": "chayobi03-cyber/agent-factory",
        "working_branch": "p0/opro-baseline",
        "audited_baseline_sha": baseline,
        "task_id": "TEST-RESUME",
        "current_task": "resume",
        "last_completed": [],
        "current_focus": ["resume"],
        "next_action": ["test"],
        "blocked_until": ["audit_evidence_chain_GREEN"],
        "forbidden": ["OPRO_promotion", "RE_domain_implementation"],
        "handoff": str(handoff),
        "resume_contract": str(contract),
        "resume_status": "UNVERIFIED",
        "resume_checks": [f"RC-{i:02d}" for i in range(1, 9)],
        "checkpoint": {"mode": "descendant", "checkpoint_sha": CHECKPOINT},
        "updated_at_utc": "2026-08-18T00:00:00Z",
    }
    return state, tmp_path


def install_git(monkeypatch: pytest.MonkeyPatch, *, branch="p0/opro-baseline", head="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", remote=resume.REPO + ".git", ancestor=True):
    def fake_git(*args: str) -> str:
        if args == ("branch", "--show-current"):
            return branch
        if args == ("rev-parse", "HEAD"):
            return head
        if args == ("config", "--get", "remote.origin.url"):
            return remote
        raise AssertionError(args)

    monkeypatch.setattr(resume, "run_git", fake_git)
    real_run = resume.subprocess.run

    def fake_run(args, *a, **kw):
        if args[:3] == ["git", "merge-base", "--is-ancestor"]:
            return CompletedProcess(args, 0 if ancestor else 1, "", "")
        return real_run(args, *a, **kw)

    monkeypatch.setattr(resume.subprocess, "run", fake_run)


def results(items):
    return {item.check_id: item for item in items}


def test_rc01_branch_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch, branch="main")
    checks = resume.validate(state, root)
    assert results(checks)["RC-01"].result == "BLOCKED"


def test_rc02_checkpoint_divergence_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch, ancestor=False)
    checks = resume.validate(state, root)
    assert results(checks)["RC-02"].result == "BLOCKED"


def test_rc03_state_baseline_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    state["audited_baseline_sha"] = "1111111111111111111111111111111111111111"
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert results(checks)["RC-03"].result == "BLOCKED"


def test_rc04_state_handoff_identity_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    Path(state["handoff"]).write_text(
        "- repository: `chayobi03-cyber/agent-factory`\n- branch: `main`\n- audited OPRO baseline SHA: `20a54b92aad0857f75c6200d984b13098c6f4927`\n",
        encoding="utf-8",
    )
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert results(checks)["RC-04"].result == "BLOCKED"


def test_rc05_handoff_git_remote_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch, remote="https://github.com/other/repo.git")
    checks = resume.validate(state, root)
    assert results(checks)["RC-05"].result == "BLOCKED"


def test_rc06_handoff_baseline_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    Path(state["handoff"]).write_text(
        "- repository: `chayobi03-cyber/agent-factory`\n- branch: `p0/opro-baseline`\n- audited OPRO baseline SHA: `1111111111111111111111111111111111111111`\nOPRO promotion remains forbidden\nDo not enter backtest/OOS/optimization/Monte Carlo before M1-B GREEN.\n",
        encoding="utf-8",
    )
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert results(checks)["RC-06"].result == "BLOCKED"


def test_rc07_gate_constraint_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    state["forbidden"] = []
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert results(checks)["RC-07"].result == "BLOCKED"


def test_rc08_missing_required_context_requires_review(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    (root / "schemas" / "session_state.schema.yaml").unlink()
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert results(checks)["RC-08"].result == "REVIEW_REQUIRED"


def test_all_rc_checks_pass_for_consistent_resume(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert {item.check_id for item in checks} == {f"RC-{i:02d}" for i in range(1, 9)}
    assert all(item.result == "PASS" for item in checks)


def test_validator_main_executes_without_runtime_typeerror(monkeypatch, tmp_path):
    """Regression witness for the prior RC-07 check() argument crash."""
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch)
    monkeypatch.setattr(resume, "load_state", lambda path: state)
    monkeypatch.setattr(sys, "argv", ["validate_session_resume.py", "--state", str(root / "state.yaml")])
    assert resume.main() == 0
