#!/usr/bin/env python3
"""Validate the CER session continuation pointer against the live Git checkout."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml


class SessionStateError(RuntimeError):
    """Raised when session state cannot be safely resumed."""


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SessionStateError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SessionStateError(f"state file not found: {path}") from exc
    if not isinstance(data, dict):
        raise SessionStateError("session state must be a YAML mapping")
    return data


def validate(state: dict[str, Any]) -> list[str]:
    required = [
        "state_version",
        "session_id",
        "phase",
        "gate",
        "repository",
        "working_branch",
        "audited_baseline_sha",
        "task_id",
        "current_task",
        "last_completed",
        "current_focus",
        "next_action",
        "blocked_until",
        "forbidden",
        "handoff",
        "updated_at_utc",
    ]
    missing = [key for key in required if key not in state]
    if missing:
        raise SessionStateError(f"missing required fields: {', '.join(missing)}")

    actual_branch = run_git("branch", "--show-current")
    if actual_branch != state["working_branch"]:
        raise SessionStateError(
            f"branch mismatch: state={state['working_branch']} actual={actual_branch}"
        )

    repository = run_git("config", "--get", "remote.origin.url")
    if "chayobi03-cyber/agent-factory" not in repository:
        raise SessionStateError(f"unexpected repository remote: {repository}")

    handoff = Path(state["handoff"])
    if not handoff.exists():
        raise SessionStateError(f"handoff file not found: {handoff}")

    if not isinstance(state["forbidden"], list) or not isinstance(state["next_action"], list):
        raise SessionStateError("forbidden and next_action must be lists")

    return [
        f"session_id={state['session_id']}",
        f"branch={actual_branch}",
        f"head={run_git('rev-parse', 'HEAD')}",
        f"gate={state['gate']}",
        "resume_checks=PASS",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--state",
        default="docs/governance/CURRENT_SESSION_STATE.yaml",
        help="path to CURRENT_SESSION_STATE.yaml",
    )
    args = parser.parse_args()

    try:
        lines = validate(load_state(Path(args.state)))
    except SessionStateError as exc:
        print(f"RESUME_CHECK=BLOCKED: {exc}")
        return 2

    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
