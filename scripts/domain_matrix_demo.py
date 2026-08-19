#!/usr/bin/env python3
"""Exercise the same Factory workflow across multiple synthetic domains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from synthetic_domain_matrix import run_matrix


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default="fixtures/domain_matrix/domain_packs.yaml")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run_matrix(Path(args.fixtures))
    passed = all(item["verification"]["supported"] and item["cer_decision"] in {"PASS", "REVIEW"} for item in results)
    output = {"fixture_only": True, "domain_count": len(results), "passed": passed, "domains": results}
    print(json.dumps(output, indent=2, sort_keys=True)) if args.json else print(output)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
