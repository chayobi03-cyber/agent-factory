#!/usr/bin/env python3
"""Fail-closed AgentFactory project/repository/context boundary guard."""

from __future__ import annotations

import subprocess
from pathlib import Path

EXPECTED_PROJECT = "agent-factory"
EXPECTED_REPOSITORY = "chayobi03-cyber/agent-factory"
EXPECTED_BRANCH = "p0/opro-baseline"
EXPECTED_GOVERNANCE_NAMESPACE = "AgentFactory"
BOUNDARY_ALLOWLIST = {
    "docs/governance/LESSONS_LEARNED_2026-08-20_CONTEXT_BOUNDARY.md",
}
CROSS_PROJECT_MARKERS = (
    "chayobi03-cyber/investment",
    "github.com/chayobi03-cyber/investment",
)


class ContextGuardError(RuntimeError):
    pass


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ContextGuardError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def normalize_remote(remote: str) -> str:
    value = remote.strip().removesuffix(".git")
    if value.startswith("git@github.com:"):
        return value.removeprefix("git@github.com:")
    for prefix in ("https://github.com/", "http://github.com/", "ssh://git@github.com/"):
        if value.startswith(prefix):
            return value.removeprefix(prefix)
    return value


def scan_cross_project_references(root: Path) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            "-I",
            "-e",
            "chayobi03-cyber/investment",
            "-e",
            "github.com/chayobi03-cyber/investment",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise ContextGuardError(result.stderr.strip() or "git grep failed")
    findings: list[str] = []
    for line in result.stdout.splitlines():
        path = line.split(":", 1)[0]
        if path not in BOUNDARY_ALLOWLIST:
            findings.append(line)
    return findings


def validate_identity(root: Path | None = None) -> list[str]:
    root = root or Path.cwd()
    state_path = root / "docs/governance/CURRENT_SESSION_STATE.yaml"
    handoff_path = root / "docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md"
    if not state_path.exists() or not handoff_path.exists():
        raise ContextGuardError("required governance identity files are missing")

    import yaml

    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ContextGuardError("CURRENT_SESSION_STATE.yaml must be a mapping")

    branch = run_git("branch", "--show-current")
    remote = normalize_remote(run_git("config", "--get", "remote.origin.url"))

    failures: list[str] = []
    if state.get("project_id") not in (None, EXPECTED_PROJECT):
        failures.append(f"state.project_id={state.get('project_id')!r}")
    if state.get("repository") != EXPECTED_REPOSITORY:
        failures.append(f"state.repository={state.get('repository')!r}")
    if state.get("working_branch") != EXPECTED_BRANCH:
        failures.append(f"state.working_branch={state.get('working_branch')!r}")
    if state.get("governance_namespace") not in (None, EXPECTED_GOVERNANCE_NAMESPACE):
        failures.append(f"state.governance_namespace={state.get('governance_namespace')!r}")
    if branch != EXPECTED_BRANCH:
        failures.append(f"git.branch={branch!r}")
    if remote != EXPECTED_REPOSITORY:
        failures.append(f"git.remote={remote!r}")

    handoff = handoff_path.read_text(encoding="utf-8")
    if f"project_id: `{EXPECTED_PROJECT}`" not in handoff:
        failures.append("handoff.project_id mismatch or missing")
    if f"governance_namespace: `{EXPECTED_GOVERNANCE_NAMESPACE}`" not in handoff:
        failures.append("handoff.governance_namespace mismatch or missing")
    if f"repository: `{EXPECTED_REPOSITORY}`" not in handoff:
        failures.append("handoff.repository mismatch or missing")
    if f"branch: `{EXPECTED_BRANCH}`" not in handoff:
        failures.append("handoff.branch mismatch or missing")

    findings = scan_cross_project_references(root)
    if findings:
        failures.append("cross-project reference(s): " + " | ".join(findings))

    return failures


def main() -> int:
    try:
        failures = validate_identity()
    except ContextGuardError as exc:
        print(f"CONTEXT_GUARD=BLOCKED: {exc}")
        return 2
    if failures:
        for failure in failures:
            print(f"CONTEXT_GUARD_FAILURE={failure}")
        print("CONTEXT_GUARD=REVIEW_REQUIRED")
        return 2
    print(f"PROJECT_ID={EXPECTED_PROJECT}")
    print(f"REPOSITORY={EXPECTED_REPOSITORY}")
    print(f"ACTIVE_BRANCH={EXPECTED_BRANCH}")
    print(f"GOVERNANCE_NAMESPACE={EXPECTED_GOVERNANCE_NAMESPACE}")
    print("CONTEXT_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
