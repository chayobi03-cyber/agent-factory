#!/usr/bin/env python3
"""Capture one command as machine-verifiable execution evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--", dest="_separator", nargs="?")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("a command is required")

    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    ended = datetime.now(timezone.utc).isoformat()

    stdout = proc.stdout
    stderr = proc.stderr
    record = {
        "evidence_id": args.evidence_id,
        "command": " ".join(command),
        "repository": os.getenv("GITHUB_REPOSITORY", "unknown"),
        "commit_sha": os.getenv("GITHUB_SHA", "unknown"),
        "timestamp_utc": ended,
        "exit_code": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256(stdout),
        "stderr_sha256": sha256(stderr),
        "workflow_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.getenv("GITHUB_RUN_ID") else None,
        "job_id": None,
        "artifact_id": None,
        "metadata": {
            "workflow_name": os.getenv("GITHUB_WORKFLOW"),
            "job_name": os.getenv("GITHUB_JOB"),
            "started_utc": started,
            "completed_utc": ended,
            "python_version": sys.version,
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
