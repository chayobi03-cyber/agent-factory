#!/usr/bin/env python3
"""Report which declared schema fields nothing in the repository names.

The repository's recurring defect has a name in `OPEN_DECISIONS`: a contract
declared and enforced by nothing. D-09 found it in the evidence-chain contract,
D-12 in three retrieval modes, the 2026-08-26 audit in a gating mechanism
described in a deleted docstring, and D-16 in `supersedes_revision_id`. Each was
found by hand, and by accident.

This is the same check, run mechanically. It answers one narrow question --
*is this declared field named anywhere outside `schemas/`?* -- and nothing
harder. A field it reports is not automatically a defect: some describe a system
deliberately not built (`trace.schema.yaml` is largely model-call telemetry, and
D-12 rules out a model dependency), and some are implemented under a different
name (`actor` is `actor_id`, `objective_vector_ref` is `objective_vector_id`).

`schemas/INDEX.md` carries the judgement. This carries the evidence.

Exit code is always 0: this reports, it does not gate.
"""
from __future__ import annotations

import json
import re
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH_PATHS = ("src", "scripts", "tests", "domains", "workflows", "templates")
#: One- to three-character names ('id', 'ref', 'page') match too much to be
#: evidence either way; a hit on them says nothing about the field.
MIN_NAME_LENGTH = 4


def declared_fields() -> dict[str, set[str]]:
    """Field name -> the schema files declaring it."""
    fields: dict[str, set[str]] = {}

    def note(name: str, source: str) -> None:
        fields.setdefault(name, set()).add(source)

    def walk_json(node: object, source: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    for name in value:
                        note(name, source)
                walk_json(value, source)
        elif isinstance(node, list):
            for value in node:
                walk_json(value, source)

    for path in sorted((ROOT / "schemas").iterdir()):
        if path.suffix == ".json":
            walk_json(json.loads(path.read_text(encoding="utf-8")), path.name)
        elif path.suffix in {".yaml", ".yml"}:
            for line in path.read_text(encoding="utf-8").splitlines():
                match = re.match(r"\s*-?\s*([a-z_][a-z0-9_]*):", line)
                if match:
                    note(match.group(1), path.name)
    return fields


def consumers(name: str) -> list[str]:
    """Files outside schemas/ that name this field as a whole word."""
    result = subprocess.run(
        ["git", "grep", "-l", "-w", name, "--", *SEARCH_PATHS],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode not in (0, 1):
        raise SystemExit(result.stderr.strip() or "git grep failed")
    return sorted(line for line in result.stdout.split() if line)


def main() -> int:
    fields = declared_fields()
    checked = {n: d for n, d in fields.items() if len(n) >= MIN_NAME_LENGTH}
    unbound: dict[str, list[str]] = {}
    for name, declared_in in sorted(checked.items()):
        if not consumers(name):
            for schema in sorted(declared_in):
                unbound.setdefault(schema, []).append(name)

    distinct = {name for names in unbound.values() for name in names}
    pairs = sum(len(v) for v in unbound.values())
    schema_count = len(list((ROOT / "schemas").iterdir()))
    print(f"declared fields checked : {len(checked)}")
    print(f"named nowhere outside schemas/ : {len(distinct)} distinct names, "
          f"{pairs} (field, schema) pairs, across {len(unbound)} of {schema_count} schema files")
    print(f"(names shorter than {MIN_NAME_LENGTH} characters are skipped as unmatchable)\n")
    for schema in sorted(unbound):
        print(f"{schema}")
        for name in unbound[schema]:
            print(f"    {name}")
        print()
    print("Status and rationale per schema: schemas/INDEX.md")
    return 0


if __name__ == "__main__":
    # This is a reporting script; being piped into `head` is a normal way to
    # read it, and dying with a traceback when the reader closes the pipe is not.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    sys.exit(main())
