#!/usr/bin/env python3
"""Run deterministic Factory Kernel benchmark and emit machine-readable output."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation_harness import FactoryKernelHarness


def resolve_execution_sha() -> str:
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    if actual.returncode != 0:
        raise RuntimeError(actual.stderr.strip() or "unable to resolve git HEAD")
    checked_out_sha = actual.stdout.strip()
    target_sha = os.environ.get("CER_TARGET_SHA")
    required = os.environ.get("CER_EXECUTION_IDENTITY_REQUIRED") == "1"
    if required and not target_sha:
        raise RuntimeError("CER_TARGET_SHA is required when CER_EXECUTION_IDENTITY_REQUIRED=1")
    execution_sha = target_sha or checked_out_sha
    if execution_sha != checked_out_sha:
        raise RuntimeError(
            f"execution identity mismatch: CER_TARGET_SHA={execution_sha} git.HEAD={checked_out_sha}"
        )
    return execution_sha


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    execution_sha = resolve_execution_sha()
    report = FactoryKernelHarness(repository_commit=execution_sha).report()
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["execution_sha"] = execution_sha
    report["repository_commit"] = execution_sha

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Factory Kernel Harness: {report['passed']}/{report['case_count']} PASS @ {execution_sha}")
        for item in report["results"]:
            marker = "PASS" if item["passed"] else "FAIL"
            print(f"[{marker}] {item['case_id']}: expected={item['target']}/{item['expected_state']} "
                  f"actual={item['actual_result']}/{item['actual_state']}")
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
