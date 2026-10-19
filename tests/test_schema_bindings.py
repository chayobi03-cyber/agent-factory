"""The execution-evidence contract is written down twice. This makes the copies agree.

`schemas/execution_evidence.schema.json` declares thirteen required fields.
`scripts/evidence_gate.py` declares its own `REQUIRED` tuple and checks records
against that, never loading the schema -- so the schema file is named by nothing
in `src/`, `scripts/`, or `tests/`.

Today the two lists are identical. Nothing makes them so: adding a required
field to the schema, or dropping one from the gate, is a silent divergence
between the contract the repository publishes and the contract CI enforces. The
evidence chain (`AUDIT_EVIDENCE_CHAIN_CI_CONTRACT_V1`) rests on the gate, and
an external auditor reading the schema would be reading the wrong document.

The fix deliberately is not "make the gate load the schema". The gate is
fail-closed on the audit path; rewiring how it obtains its own invariants to
depend on a file read is a change to that path for no gain the test does not
already give. Binding them here costs nothing at runtime and fails the build on
divergence, which is the property that was missing.

Found by `scripts/audit_schema_bindings.py`.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _schema_required() -> set[str]:
    schema = json.loads((ROOT / "schemas" / "execution_evidence.schema.json").read_text(encoding="utf-8"))
    return set(schema["required"])


def _gate_required() -> set[str]:
    """Read `REQUIRED` from the gate's source without importing it.

    Parsing rather than importing keeps this test independent of whatever the
    gate does at import time, now or later.
    """
    tree = ast.parse((ROOT / "scripts" / "evidence_gate.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "REQUIRED" for t in node.targets
        ):
            return set(ast.literal_eval(node.value))
    raise AssertionError("scripts/evidence_gate.py no longer defines a module-level REQUIRED")


def test_the_gate_enforces_exactly_what_the_schema_requires():
    schema, gate = _schema_required(), _gate_required()
    assert schema == gate, (
        "execution-evidence contract has diverged between its two copies.\n"
        f"  required by schema, not enforced by gate: {sorted(schema - gate)}\n"
        f"  enforced by gate, not required by schema: {sorted(gate - schema)}\n"
        "Update both, or delete one and have the other read it."
    )


def test_the_contract_is_not_empty():
    """A binding between two empty sets would pass and mean nothing."""
    assert len(_schema_required()) >= 13
