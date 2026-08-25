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
        "schema_id: session_state\nschema_version: 1.2.0\nproject_id: agent-factory\ngovernance_namespace: AgentFactory\n",
        encoding="utf-8",
    )
    target_contract = tmp_path / "docs" / "governance"
    target_contract.mkdir(parents=True)
    (target_contract / "CER_TARGET_SHA_EXECUTION_CONTRACT_V1.md").write_text(
        "execution_sha == target_sha\n",
        encoding="utf-8",
    )
    handoff = tmp_path / "handoff.md"
    handoff.write_text(
        "\n".join(
            [
                "# Handoff",
                "- project_id: `agent-factory`",
                "- repository: `chayobi03-cyber/agent-factory`",
                "- branch: `p0/opro-baseline`",
                "- governance_namespace: `AgentFactory`",
                f"- audited OPRO baseline SHA: `{baseline}`",
                "GEPA implementation forbidden.",
                "RE Domain implementation forbidden.",
                "OPRO promotion forbidden.",
                "Audited OPRO baseline SHA must not change.",
                "PASS without primary execution evidence forbidden.",
            ]
        ),
        encoding="utf-8",
    )
    state = {
        "state_version": 1,
        "session_id": "test-session",
        "phase": "TEST",
        "gate": gate,
        "project_id": "agent-factory",
        "repository": "chayobi03-cyber/agent-factory",
        "governance_namespace": "AgentFactory",
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
    monkeypatch.setenv("CER_EXECUTION_IDENTITY_REQUIRED", "1")
    monkeypatch.setenv("CER_TARGET_SHA", head)
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


def test_rc02_target_sha_mismatch_is_blocked(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch)
    monkeypatch.setenv("CER_TARGET_SHA", "cccccccccccccccccccccccccccccccccccccccc")
    checks = resume.validate(state, root)
    assert results(checks)["RC-02"].result == "BLOCKED"


def test_rc02_target_sha_match_passes(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch)
    monkeypatch.setenv("CER_TARGET_SHA", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    checks = resume.validate(state, root)
    assert results(checks)["RC-02"].result == "PASS"


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
        "- repository: `chayobi03-cyber/agent-factory`\n- branch: `p0/opro-baseline`\n- audited OPRO baseline SHA: `1111111111111111111111111111111111111111`\nGEPA implementation forbidden.\nRE Domain implementation forbidden.\nOPRO promotion forbidden.\nAudited OPRO baseline SHA must not change.\nPASS without primary execution evidence forbidden.\n",
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


def test_rc07_active_gate_with_protected_constraints_passes(monkeypatch, tmp_path):
    state, root = make_fixture(tmp_path)
    install_git(monkeypatch)
    checks = resume.validate(state, root)
    assert results(checks)["RC-07"].result == "PASS"


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


def test_structured_frontmatter_handoff_passes_without_prose_matching(monkeypatch, tmp_path):
    """Root-cause regression witness: a handoff using ONLY the YAML front-matter
    (no prose phrasing at all) must still satisfy RC-03..RC-07. This is what
    repeatedly broke when handoff wording drifted; front-matter cannot drift
    the same way because it is parsed structurally, not phrase-matched."""
    state, root = make_fixture(tmp_path)
    handoff_path = Path(state["handoff"])
    handoff_path.write_text(
        "\n".join(
            [
                "---",
                "project_id: agent-factory",
                "repository: chayobi03-cyber/agent-factory",
                "branch: p0/opro-baseline",
                "governance_namespace: AgentFactory",
                f"audited_baseline_sha: {BASELINE}",
                "forbidden:",
                "  - GEPA_implementation",
                "  - OPRO_promotion",
                "  - RE_domain_implementation",
                "  - audited_baseline_redefinition",
                "  - PASS_without_primary_execution_evidence",
                "---",
                "# Handoff (structured, no prose constraint wording at all)",
            ]
        ),
        encoding="utf-8",
    )
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
    # main() resolves repo_root from cwd (as it does in real CI/local invocation);
    # chdir so this matches the fixture root instead of the real repository root.
    monkeypatch.chdir(root)
    assert resume.main() == 0


def test_resolve_branch_uses_base_ref_for_pull_request_events(monkeypatch):
    """Root-cause regression test: the resume validator carried the same
    pull_request false negative as the Context Guard (LSN-0002). On a
    pull_request event the checkout is detached and GITHUB_HEAD_REF is the
    PR's *source* branch, so RC-01 compared it against state.working_branch
    and blocked every PR regardless of content -- and RC-05 inherited the
    wrong branch in its expected identity. Resolution must key off the base
    ref, which is the branch the work would land in."""
    monkeypatch.setenv("GITHUB_HEAD_REF", "claude/some-unrelated-branch-name")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    monkeypatch.setenv("GITHUB_REF_NAME", "refs/pull/14/merge")

    original = resume.run_git
    monkeypatch.setattr(
        resume,
        "run_git",
        lambda *args: "" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = resume.resolve_branch()
    assert branch == "main"
    assert source == "github.base_ref"


def test_resolve_branch_uses_ref_name_for_push_events(monkeypatch):
    """Regression guard: the push path must keep resolving via GITHUB_REF_NAME
    once GITHUB_BASE_REF is absent (it is only set for pull_request events)."""
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

    original = resume.run_git
    monkeypatch.setattr(
        resume,
        "run_git",
        lambda *args: "" if args == ("branch", "--show-current") else original(*args),
    )
    branch, source = resume.resolve_branch()
    assert branch == "main"
    assert source == "github.ref"


# --- D-01: the kernel-gated constraint is time-bounded, not permanent --------
#
# Until 2026-08-25 the validator demanded `RE_domain_implementation` in every
# handoff unconditionally, while ROADMAP_WBS.md makes M1 RE the next milestone
# *after* the Factory Kernel gate. The two could not both hold: clearing the
# gate was exactly what should permit the work the constraint forbade.


def test_kernel_gated_constraint_is_required_while_the_gate_is_closed():
    declared = set(resume.PERMANENT_HANDOFF_CONSTRAINTS)
    assert not resume.constraints_satisfied("NOT_GREEN", declared)
    assert resume.constraints_satisfied("NOT_GREEN", declared | {"RE_domain_implementation"})


def test_kernel_gated_constraint_is_discharged_once_the_gate_clears():
    """The point of the fix: a handoff written after the gate went GREEN no
    longer has to declare the milestone it gates as forbidden."""
    declared = set(resume.PERMANENT_HANDOFF_CONSTRAINTS)
    assert resume.constraints_satisfied("FACTORY_KERNEL_GREEN", declared)
    # ...and keeping the token is still fine -- discharged, not banned.
    assert resume.constraints_satisfied(
        "FACTORY_KERNEL_GREEN", declared | {"RE_domain_implementation_until_kernel_gate"}
    )


def test_both_spellings_of_the_kernel_gated_constraint_are_accepted():
    """CURRENT_SESSION_STATE.yaml has always used the `_until_kernel_gate` form
    while the handoff front-matter used the bare one; they mean the same thing."""
    base = set(resume.PERMANENT_HANDOFF_CONSTRAINTS)
    for token in ("RE_domain_implementation", "RE_domain_implementation_until_kernel_gate"):
        assert resume.constraints_satisfied("NOT_GREEN", base | {token}), token


def test_permanent_constraints_survive_the_gate_clearing():
    """Discharging the kernel-gated constraint must not discharge the others."""
    full = set(resume.PERMANENT_HANDOFF_CONSTRAINTS)
    for dropped in sorted(full):
        weakened = full - {dropped}
        assert not resume.constraints_satisfied("FACTORY_KERNEL_GREEN", weakened), dropped
        assert not resume.constraints_satisfied("NOT_GREEN", weakened | {"RE_domain_implementation"}), dropped


def test_rc07_passes_on_a_green_gate_handoff_that_omits_the_re_constraint(monkeypatch, tmp_path):
    """End-to-end witness for D-01: with the kernel gate GREEN, a structured
    handoff that does not mention RE domain implementation at all still
    satisfies RC-07. Before the fix this combination was unreachable."""
    state, root = make_fixture(tmp_path, gate="FACTORY_KERNEL_GREEN")
    state["forbidden"] = ["OPRO_promotion"]
    handoff_path = Path(state["handoff"])
    handoff_path.write_text(
        "\n".join(
            [
                "---",
                "project_id: agent-factory",
                "repository: chayobi03-cyber/agent-factory",
                "branch: p0/opro-baseline",
                "governance_namespace: AgentFactory",
                f"audited_baseline_sha: {BASELINE}",
                "forbidden:",
                "  - GEPA_implementation",
                "  - OPRO_promotion",
                "  - audited_baseline_redefinition",
                "  - PASS_without_primary_execution_evidence",
                "---",
                "# Handoff written after the Factory Kernel gate went GREEN",
            ]
        ),
        encoding="utf-8",
    )
    install_git(monkeypatch)
    checks = {item.check_id: item for item in resume.validate(state, root)}
    assert checks["RC-07"].result == "PASS"


def test_rc07_still_blocks_a_closed_gate_handoff_that_omits_the_re_constraint(monkeypatch, tmp_path):
    """Regression guard on the other side: the constraint must still bite while
    the gate is closed, or the fix would have removed the protection entirely."""
    state, root = make_fixture(tmp_path, gate="NOT_GREEN")
    handoff_path = Path(state["handoff"])
    handoff_path.write_text(
        "\n".join(
            [
                "---",
                "project_id: agent-factory",
                "repository: chayobi03-cyber/agent-factory",
                "branch: p0/opro-baseline",
                "governance_namespace: AgentFactory",
                f"audited_baseline_sha: {BASELINE}",
                "forbidden:",
                "  - GEPA_implementation",
                "  - OPRO_promotion",
                "  - audited_baseline_redefinition",
                "  - PASS_without_primary_execution_evidence",
                "---",
                "# Handoff written while the gate is still closed",
            ]
        ),
        encoding="utf-8",
    )
    install_git(monkeypatch)
    checks = {item.check_id: item for item in resume.validate(state, root)}
    assert checks["RC-07"].result != "PASS"
