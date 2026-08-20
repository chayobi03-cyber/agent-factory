#!/usr/bin/env python3
"""Fail-closed RC-01..RC-08 validator for CER session resume."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO = "chayobi03-cyber/agent-factory"
PROJECT = "agent-factory"
GOVERNANCE_NAMESPACE = "AgentFactory"
SUPPORTED_SCHEMA_VERSION = "1.2.0"
FORWARD_BLOCK_GATES = {"NOT_GREEN", "BLOCKED", "HOLD", "INCONCLUSIVE"}


@dataclass(frozen=True)
class ResumeCheck:
    check_id: str
    observed_value: str
    expected_value: str
    result: str
    source_reference: str


class ResumeError(RuntimeError):
    pass


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ResumeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def resolve_branch() -> tuple[str, str]:
    """Return branch plus source; CI refs are required for detached checkouts."""
    branch = run_git("branch", "--show-current")
    if branch:
        return branch, "git.branch"
    ci_branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME")
    if ci_branch:
        return ci_branch, "github.ref"
    raise ResumeError("unable to resolve current branch from Git or GitHub Actions environment")


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ResumeError(f"state file not found: {path}") from exc
    if not isinstance(state, dict):
        raise ResumeError("session state must be a YAML mapping")
    return state


def read_required(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ResumeError(f"required context file not found: {path}") from exc


def read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def parse_handoff(text: str) -> dict[str, str]:
    """Parse identity fields from the handoff with markdown/format tolerance."""
    values: dict[str, str] = {}
    normalized = text.replace("—", "-").replace("–", "-")
    patterns = {
        "repository": r"\brepository\s*:\s*`([^`]+)`",
        "branch": r"\bbranch\s*:\s*`([^`]+)`",
        "project": r"\bproject_id\s*:\s*`([^`]+)`",
        "governance_namespace": r"\bgovernance_namespace\s*:\s*`([^`]+)`",
        "baseline": r"\baudited\s+(?:OPRO\s+)?baseline\s+SHA\b[^\n]*?([0-9a-f]{40})",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            values[key] = match.group(1)
    return values


def check(check_id: str, observed: str, expected: str, source: str, ok: bool, review: bool = False) -> ResumeCheck:
    if ok:
        result = "PASS"
    else:
        result = "REVIEW_REQUIRED" if review else "BLOCKED"
    return ResumeCheck(check_id, observed, expected, result, source)


def resolve_target_sha(actual_head: str) -> tuple[str | None, bool, str]:
    """Return (target_sha, binding_ok, source) without changing local/offline semantics."""
    target_sha = os.environ.get("CER_TARGET_SHA")
    required = os.environ.get("CER_EXECUTION_IDENTITY_REQUIRED") == "1"
    if not target_sha:
        if required:
            raise ResumeError("CER_TARGET_SHA is required when CER_EXECUTION_IDENTITY_REQUIRED=1")
        return None, True, "execution.identity.optional"
    if not re.fullmatch(r"[0-9a-f]{40}", target_sha):
        raise ResumeError("CER_TARGET_SHA must be a 40-character commit SHA")
    return target_sha, actual_head == target_sha, "CER_TARGET_SHA + git.HEAD"


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Case-insensitive phrase matching with whitespace normalization."""
    normalized_text = re.sub(r"\s+", " ", text).strip().lower()
    return any(
        re.sub(r"\s+", " ", phrase).strip().lower() in normalized_text
        for phrase in phrases
    )


def validate(state: dict[str, Any], repo_root: Path | None = None) -> list[ResumeCheck]:
    root = repo_root or Path.cwd()
    required = [
        "state_version", "session_id", "phase", "gate", "project_id", "repository", "working_branch",
        "governance_namespace", "audited_baseline_sha", "task_id", "current_task", "last_completed", "current_focus",
        "next_action", "blocked_until", "forbidden", "handoff", "resume_contract", "resume_status",
        "resume_checks", "checkpoint", "updated_at_utc",
    ]
    missing = [key for key in required if key not in state]
    if missing:
        raise ResumeError(f"missing required fields: {', '.join(missing)}")

    actual_branch, branch_source = resolve_branch()
    actual_head = run_git("rev-parse", "HEAD")
    remote = run_git("config", "--get", "remote.origin.url")
    branch_ok = actual_branch == state["working_branch"]

    target_sha, target_binding_ok, target_source = resolve_target_sha(actual_head)

    checkpoint = state["checkpoint"]
    checkpoint_sha = str(checkpoint.get("checkpoint_sha", ""))
    checkpoint_mode = str(checkpoint.get("mode", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", checkpoint_sha):
        raise ResumeError("checkpoint.checkpoint_sha must be a 40-character commit SHA")
    if checkpoint_mode not in {"exact", "descendant"}:
        raise ResumeError("checkpoint.mode must be exact or descendant")

    if checkpoint_mode == "exact":
        head_ok = actual_head == checkpoint_sha
    else:
        probe = subprocess.run(
            ["git", "merge-base", "--is-ancestor", checkpoint_sha, actual_head],
            capture_output=True,
            text=True,
            check=False,
        )
        head_ok = probe.returncode == 0

    handoff_path = Path(state["handoff"])
    if not handoff_path.is_absolute():
        handoff_path = root / handoff_path
    handoff_text = read_required(handoff_path)
    handoff = parse_handoff(handoff_text)

    contract_path = Path(state["resume_contract"])
    if not contract_path.is_absolute():
        contract_path = root / contract_path
    schema_path = root / "schemas/session_state.schema.yaml"
    target_contract_path = root / "docs/governance/CER_TARGET_SHA_EXECUTION_CONTRACT_V1.md"
    contract_text = read_optional(contract_path)
    schema_text = read_optional(schema_path)
    target_contract_text = read_optional(target_contract_path)

    baseline_ok = state["audited_baseline_sha"] == handoff.get("baseline")
    handoff_state_ok = (
        handoff.get("repository") == state["repository"]
        and handoff.get("branch") == state["working_branch"]
        and handoff.get("project") == state["project_id"]
        and handoff.get("governance_namespace") == state["governance_namespace"]
        and handoff_path.exists()
    )
    handoff_git_ok = (
        REPO in remote
        and handoff.get("repository") == REPO
        and handoff.get("branch") == actual_branch
    )
    handoff_baseline_ok = handoff.get("baseline") == state["audited_baseline_sha"]

    forbidden = {str(item) for item in state.get("forbidden", [])}
    gate_constraints_ok = (
        state["gate"] not in FORWARD_BLOCK_GATES
        or {"OPRO_promotion", "RE_domain_implementation"}.issubset(forbidden)
    )
    handoff_normalized = re.sub(r"\s+", " ", handoff_text.lower())
    handoff_constraints_ok = (
        _contains_any(handoff_normalized, ("gepa implementation forbidden", "gepa implementation 금지"))
        and _contains_any(handoff_normalized, ("opro promotion forbidden", "opro promotion 금지"))
        and _contains_any(handoff_normalized, ("re domain implementation forbidden", "re domain implementation 금지"))
        and _contains_any(
            handoff_normalized,
            (
                "audited opro baseline sha must not change",
                "audited opro baseline sha immutable",
                "audited opro baseline sha - do not change",
            ),
        )
        and _contains_any(
            handoff_normalized,
            (
                "pass without primary execution evidence forbidden",
                "state/documentation never substitutes for primary evidence",
            ),
        )
    )
    forbidden_ok = gate_constraints_ok and handoff_constraints_ok

    context_ok = (
        bool(contract_text)
        and bool(schema_text)
        and bool(target_contract_text)
        and f"schema_version: {SUPPORTED_SCHEMA_VERSION}" in schema_text
        and f"project_id: {PROJECT}" in schema_text
        and f"governance_namespace: {GOVERNANCE_NAMESPACE}" in schema_text
        and ("CER Session Continuity Contract" in contract_text or "CER Resume Contract" in contract_text)
        and "RC-08" in contract_text
        and "execution_sha == target_sha" in target_contract_text
        and state["project_id"] == PROJECT
        and state["governance_namespace"] == GOVERNANCE_NAMESPACE
    )

    rc02_ok = head_ok and target_binding_ok
    target_observed = actual_head if target_sha is None else f"target={target_sha};checkout={actual_head}"
    target_expected = "checkpoint relation + target_sha binding" if target_sha is not None else "checkpoint relation"

    return [
        check("RC-01", actual_branch, str(state["working_branch"]), f"state.working_branch + {branch_source}", branch_ok),
        check("RC-02", target_observed, target_expected, f"state.checkpoint + git.HEAD + {target_source}", rc02_ok),
        check("RC-03", str(state["audited_baseline_sha"]), str(handoff.get("baseline")), "state.audited_baseline_sha + handoff", baseline_ok),
        check("RC-04", str(handoff_path), f"{state['project_id']}@{state['repository']}@{state['working_branch']}:{state['governance_namespace']}", "state.handoff + handoff identity", handoff_state_ok),
        check("RC-05", remote, f"{REPO}@{actual_branch}", "git.remote + handoff", handoff_git_ok),
        check("RC-06", str(handoff.get("baseline")), str(state["audited_baseline_sha"]), "handoff.baseline + state", handoff_baseline_ok),
        check("RC-07", str(state["gate"]), "gate/forbidden/handoff constraints consistent", "state.gate + forbidden + handoff", forbidden_ok),
        check("RC-08", f"{contract_path};{schema_path};{target_contract_path}", "required context exists and is compatible", "resume contract + schema + target-SHA contract", context_ok, review=True),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default="docs/governance/CURRENT_SESSION_STATE.yaml")
    args = parser.parse_args()

    try:
        checks = validate(load_state(Path(args.state)))
    except ResumeError as exc:
        print(f"RESUME_CHECK=BLOCKED: {exc}")
        return 2

    overall = "RESUME_ALLOWED"
    for item in checks:
        print(f"{item.check_id}={item.result} observed={item.observed_value!r} expected={item.expected_value!r} source={item.source_reference}")
        if item.result == "BLOCKED":
            overall = "RESUME_BLOCKED"
        elif item.result == "REVIEW_REQUIRED" and overall == "RESUME_ALLOWED":
            overall = "RESUME_REVIEW_REQUIRED"

    print(f"RESUME_STATUS={overall}")
    return 0 if overall == "RESUME_ALLOWED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
