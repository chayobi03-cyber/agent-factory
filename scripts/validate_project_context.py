#!/usr/bin/env python3
"""Fail-closed AgentFactory project/repository/context boundary guard."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

EXPECTED_PROJECT = "agent-factory"
EXPECTED_REPOSITORY = "chayobi03-cyber/agent-factory"
EXPECTED_BRANCH = "main"
EXPECTED_GOVERNANCE_NAMESPACE = "AgentFactory"
BOUNDARY_REFERENCE_FILES = {
    "docs/governance/AGENT_FACTORY_SCOPE_V1.md",
    "docs/governance/LESSONS_LEARNED_2026-08-20_CONTEXT_BOUNDARY.md",
    "docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md",
}
SCAN_PATHS = ("docs/governance", ".github/workflows")
CROSS_PROJECT_MARKERS = (
    "chayobi03-cyber/investment",
    "github.com/chayobi03-cyber/investment",
)
# High-confidence quarantine set. These are not generic keyword matches; they are
# known investment-specific artifacts identified by the forensic ownership review.
FORBIDDEN_CANONICAL_PATHS = {
    "docs/governance/M1B_MINIMUM_SOURCE_STACK_V1.md",
    "docs/governance/M1B_SOURCE_CONTRACT_V1.md",
    "docs/governance/M1B_FIRST_INGEST_EVIDENCE_2026-08-19.yaml",
    "docs/governance/M1B_PIT_RECONCILIATION_EVIDENCE_2026-08-19.yaml",
    "docs/governance/M1B_PIT_RECONCILIATION_EVIDENCE_2026-08-20.yaml",
    "docs/governance/CER_M1B_LESSONS_2026-08-19.md",
    "docs/governance/M2_HISTORICAL_INTEGRATION_CONTRACT_V1.md",
    "docs/governance/M2_ENTRY_REVIEW_2026-08-20.yaml",
    "fixtures/m1b/historical_series_2020-01.json",
    "fixtures/m1b/pit_reconciliation_2020-01.json",
    "fixtures/m2/historical_experiment_12_case.yaml",
    "schemas/financial_provenance.schema.yaml",
    "schemas/m2_historical_experiment.schema.yaml",
    "scripts/m2_entry_review.py",
    "src/m1b_fred.py",
    "src/m1b_provenance.py",
    "src/m2_historical.py",
    "tests/test_m1b_fred.py",
    "tests/test_m1b_pit_reconciliation.py",
    "tests/test_m1b_provenance.py",
    "tests/test_m2_historical_contract.py",
}


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


def resolve_branch() -> tuple[str, str]:
    """Resolve branch in normal Git checkouts and CI checkouts.

    Root-cause fix (2026-08-24): a `pull_request` event checks out the PR's
    HEAD ref in a detached state, and `GITHUB_HEAD_REF` is the PR's *source*
    branch name (e.g. a fix branch), which will almost never equal
    EXPECTED_BRANCH. The governance boundary this guard actually cares
    about is which branch the PR would land in -- the *base* ref
    (`GITHUB_BASE_REF`) -- not what the source branch happens to be named.
    Using HEAD_REF made every PR-triggered run fail this guard regardless
    of content, which is why PR-triggered CI runs never observed
    RC-01..08/pytest results after this guard was introduced (see
    11_Audit/LSN-0001 and CER_CI_PR_EXECUTION_LESSONS_2026-08-20.md for the
    PR#11 run that predated this guard and did pass). `GITHUB_REF_NAME`
    remains the fallback for `push` events, where it already correctly
    resolves to the pushed branch name.
    """
    branch = run_git("branch", "--show-current")
    if branch:
        return branch, "git.branch"
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        return base_ref, "github.base_ref"
    ci_branch = os.environ.get("GITHUB_REF_NAME")
    if ci_branch:
        return ci_branch, "github.ref"
    raise ContextGuardError("unable to resolve branch from Git or GitHub Actions environment")


def scan_cross_project_references(root: Path) -> list[str]:
    """Scan only governance/workflow surfaces; intentional boundary references are provenance-allowlisted."""
    result = subprocess.run(
        ["git", "grep", "-n", "-I", *sum((["-e", marker] for marker in CROSS_PROJECT_MARKERS), []), "--", *SCAN_PATHS],
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
        if path not in BOUNDARY_REFERENCE_FILES:
            findings.append(line)
    return findings


def scan_forbidden_paths(root: Path) -> list[str]:
    tracked = set(run_git("ls-files").splitlines())
    return sorted(path for path in FORBIDDEN_CANONICAL_PATHS if path in tracked)


def validate_identity(root: Path | None = None) -> list[str]:
    root = root or Path.cwd()
    state_path = root / "docs/governance/CURRENT_SESSION_STATE.yaml"
    handoff_path = root / "docs/governance/NEXT_SESSION_HANDOFF_2026-08-18.md"
    scope_path = root / "docs/governance/AGENT_FACTORY_SCOPE_V1.md"
    if not state_path.exists() or not handoff_path.exists() or not scope_path.exists():
        raise ContextGuardError("required governance identity/scope files are missing")

    import yaml

    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ContextGuardError("CURRENT_SESSION_STATE.yaml must be a mapping")

    branch, branch_source = resolve_branch()
    remote = normalize_remote(run_git("config", "--get", "remote.origin.url"))

    failures: list[str] = []
    if state.get("project_id") != EXPECTED_PROJECT:
        failures.append(f"state.project_id={state.get('project_id')!r}")
    if state.get("repository") != EXPECTED_REPOSITORY:
        failures.append(f"state.repository={state.get('repository')!r}")
    if state.get("working_branch") != EXPECTED_BRANCH:
        failures.append(f"state.working_branch={state.get('working_branch')!r}")
    if state.get("governance_namespace") != EXPECTED_GOVERNANCE_NAMESPACE:
        failures.append(f"state.governance_namespace={state.get('governance_namespace')!r}")
    if branch != EXPECTED_BRANCH:
        failures.append(f"resolved_branch={branch!r} source={branch_source}")
    if remote != EXPECTED_REPOSITORY:
        failures.append(f"git.remote={remote!r}")

    scope = scope_path.read_text(encoding="utf-8")
    if "project_id: agent-factory" not in scope or "governance_namespace: AgentFactory" not in scope:
        failures.append("canonical scope contract identity mismatch or missing")

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

    forbidden = scan_forbidden_paths(root)
    if forbidden:
        failures.append("investment-specific canonical artifacts present: " + ", ".join(forbidden))

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
