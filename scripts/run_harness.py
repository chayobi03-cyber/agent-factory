#!/usr/bin/env python3
"""Run deterministic Factory Kernel benchmark and emit machine-readable output."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation_harness import FactoryKernelHarness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = FactoryKernelHarness().report()
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["commit_sha"] = "harness-test-commit"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Factory Kernel Harness: {report['passed']}/{report['case_count']} PASS")
        for item in report["results"]:
            marker = "PASS" if item["passed"] else "FAIL"
            print(f"[{marker}] {item['case_id']}: expected={item['target']}/{item['expected_state']} "
                  f"actual={item['actual_result']}/{item['actual_state']}")
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
