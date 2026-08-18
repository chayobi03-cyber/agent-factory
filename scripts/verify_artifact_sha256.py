#!/usr/bin/env python3
"""Independently verify an evidence artifact SHA256."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("expected_sha256")
    args = parser.parse_args()

    digest = hashlib.sha256(args.artifact.read_bytes()).hexdigest()
    result = "PASS" if digest == args.expected_sha256 else "FAIL"
    print(f"artifact={args.artifact}")
    print(f"observed_sha256={digest}")
    print(f"expected_sha256={args.expected_sha256}")
    print(f"decision={result}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
