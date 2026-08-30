#!/usr/bin/env python3
"""Exercise the same Factory workflow across multiple synthetic domains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import sys
from pathlib import Path

# The other six scripts in this directory each put `src/` on `sys.path`
# themselves; these two read the ambient PYTHONPATH, which only
# `.github/workflows/factory-kernel.yml` and the session-start hook set. They
# therefore raised ModuleNotFoundError for anyone running them directly, and
# the failure was invisible until you ran exactly these two -- checking the
# other six proved nothing about them (recorded in the 2026-08-29 handoff as
# an open question about which convention should win).
#
# Resolved towards the majority, and in the direction that removes a
# dependency rather than adding one: all eight now run on a bare clone with no
# environment set. The exported PYTHONPATH stays valid and is now redundant
# rather than required. `tests/test_scripts_run_standalone.py` fails if a
# script goes back to needing it.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synthetic_domain_matrix import run_matrix  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default="fixtures/domain_matrix/domain_packs.yaml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run_matrix(Path(args.fixtures))
    passed = all(
        item["verification"]["supported"]
        and item["evaluation"]["passed"]
        and item["cer_decision"] == "PASS"
        and item["workflow_executed"]
        and item["report_rendered"]
        for item in results
    )
    output = {
        "fixture_only": True,
        "domain_count": len(results),
        "passed": passed,
        "lifecycle": "ingest>parse>normalize>retrieve>verify>evaluate>cer_gate>execute>report>trace",
        "domains": results,
    }
    print(json.dumps(output, indent=2, sort_keys=True)) if args.json else print(output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
