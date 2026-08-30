"""The agent context is one document, and it does not drift from the state file.

Two failure modes are being prevented here, both of which this repository has
already been bitten by.

The first is one definition living in two places. Claude Code reads `CLAUDE.md`
and Gemini CLI reads `GEMINI.md`, so the obvious way to serve both is to write
the same instructions twice -- and then to update one of them. Both files
instead `@`-import `docs/AGENT_CONTEXT.md`, which both clients inline at load
time, so there is exactly one body. These tests fail if either importer grows
one.

The second is a document restating a governance fact that later moves. The
context file names the trunk, the repository, and the audited baseline SHA
because an agent needs them up front, so each is asserted equal to
`CURRENT_SESSION_STATE.yaml` rather than trusted. The constraints it lists are
checked as a *subset* of `state.forbidden`: the document says outright that its
list is incomplete and that the state file is authoritative, so completeness is
not asserted -- but a constraint it invents, or one it keeps after retirement,
fails here.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

CANONICAL = ROOT / "docs/AGENT_CONTEXT.md"

#: The per-client entry points. Each is a pointer, not a document.
IMPORTERS = (ROOT / "CLAUDE.md", ROOT / "GEMINI.md")

#: The import both clients resolve. Gemini CLI and Claude Code use the same
#: `@path` syntax and inline the target at load time, so one file reaches both.
IMPORT_LINE = "@docs/AGENT_CONTEXT.md"

#: An importer that stays a pointer is short and has no sections of its own.
#: Both limits are needed: a body pasted in without headings would slip past
#: the heading check, and a heading added to a short file would slip past the
#: line count.
MAX_IMPORTER_LINES = 20


def _state() -> dict:
    return yaml.safe_load(
        (ROOT / "docs/governance/CURRENT_SESSION_STATE.yaml").read_text(encoding="utf-8")
    )


def _canonical_text() -> str:
    return CANONICAL.read_text(encoding="utf-8")


def test_the_canonical_context_file_exists():
    assert CANONICAL.is_file(), (
        "docs/AGENT_CONTEXT.md is the single body both agent files import"
    )


@pytest.mark.parametrize("path", IMPORTERS, ids=lambda p: p.name)
def test_each_client_entry_point_imports_the_canonical_file(path: Path):
    assert path.is_file(), f"{path.name} is missing; the client would read no context"
    assert IMPORT_LINE in path.read_text(encoding="utf-8"), (
        f"{path.name} must import {IMPORT_LINE} rather than carry its own copy"
    )


@pytest.mark.parametrize("path", IMPORTERS, ids=lambda p: p.name)
def test_each_client_entry_point_stays_a_pointer(path: Path):
    """A body here is the drift this arrangement exists to prevent."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= MAX_IMPORTER_LINES, (
        f"{path.name} has grown to {len(lines)} lines. Content belongs in "
        f"docs/AGENT_CONTEXT.md, which both clients import."
    )
    sections = [line for line in lines if line.startswith("## ")]
    assert sections == [], (
        f"{path.name} has its own sections {sections}; that content would be "
        f"invisible to the other client. Put it in docs/AGENT_CONTEXT.md."
    )


def _identity_table() -> dict[str, str]:
    """The `## Identity` table, parsed into {row label: value}.

    Parsed rather than substring-searched. A first version of this test asserted
    `state["working_branch"] in document`, which passed even after the table was
    edited to say `master`: the word "main" still occurred in `push: [main]`
    further down. Checking a common word against a whole document proves
    nothing, so the value is read from the row that claims it.
    """
    text = _canonical_text()
    start = text.index("## Identity")
    end = text.index("\n## ", start + 1)
    rows = re.findall(r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|$", text[start:end], re.MULTILINE)
    return {label: value for label, value in rows}


#: Identity table row -> the state field that decides it.
IDENTITY_ROWS = {
    "project_id": "project_id",
    "repository": "repository",
    "trunk": "working_branch",
    "governance namespace": "governance_namespace",
    "audited baseline SHA": "audited_baseline_sha",
}


@pytest.mark.parametrize("row, field", IDENTITY_ROWS.items())
def test_identity_in_the_context_file_matches_state(row: str, field: str):
    """Whatever the context file tells an agent about identity must be true."""
    table = _identity_table()
    assert row in table, (
        f"the Identity table has no {row!r} row; rows found: {sorted(table)}"
    )
    assert table[row] == _state()[field], (
        f"docs/AGENT_CONTEXT.md says {row} is {table[row]!r} while "
        f"state.{field} is {_state()[field]!r}; an agent reading it would be "
        f"told something the state file denies"
    )


def _constraints_named_in_the_document() -> list[str]:
    """Backticked constraint tokens inside the constraints section only.

    Scoped to that section deliberately: `CONTRADICTORY_EVIDENCE` appears
    elsewhere in the document as the name of a defect, not of a constraint, and
    a repository-wide sweep would demand it be a forbidden entry.
    """
    text = _canonical_text()
    start = text.index("## Constraints that are not yours to relax")
    end = text.index("\n## ", start + 1)
    section = text[start:end]
    return [
        token
        for token in re.findall(r"`([^`]+)`", section)
        # Paths and attribute references are pointers, not constraint names.
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+", token)
    ]


def test_the_document_names_some_constraints():
    """Guards the extraction itself: a silent empty list would assert nothing."""
    assert len(_constraints_named_in_the_document()) >= 4


def test_every_constraint_named_is_a_real_forbidden_entry():
    forbidden = set(_state()["forbidden"])
    named = _constraints_named_in_the_document()
    unknown = [token for token in named if token not in forbidden]
    assert unknown == [], (
        f"docs/AGENT_CONTEXT.md names {unknown} as forbidden, but "
        f"state.forbidden does not list them. Either the entry was retired and "
        f"the document kept it, or the document invented it."
    )


def test_the_document_sends_the_reader_to_state_for_the_full_list():
    """The subset is only honest while the document says it is one."""
    text = _canonical_text()
    assert "deliberately not\ncomplete" in text or "deliberately not complete" in text
    assert "CURRENT_SESSION_STATE.yaml" in text


def test_the_document_does_not_hardcode_a_handoff_filename():
    """The handoff is named by `state.handoff` and followed, never remembered.

    A filename here would become the fourth place that pointer lives, after the
    state file, the context guard and the resume validator -- and the guard and
    the validator have already disagreed once for exactly this reason.
    """
    stale = re.findall(r"NEXT_SESSION_HANDOFF_[0-9]{4}-[0-9]{2}-[0-9]{2}\.md", _canonical_text())
    assert stale == [], (
        f"docs/AGENT_CONTEXT.md hardcodes {stale}; it should tell the reader to "
        f"follow state.handoff instead"
    )


def _highest_decision_in_the_register() -> int:
    register = (ROOT / "docs/governance/OPEN_DECISIONS_2026-08-25.md").read_text(encoding="utf-8")
    numbers = [int(n) for n in re.findall(r"^## D-(\d+) ", register, re.MULTILINE)]
    assert numbers, "found no decision headings in the register"
    return max(numbers)


@pytest.mark.parametrize(
    "doc",
    ["docs/AGENT_CONTEXT.md", None],
    ids=["agent-context", "handoff"],
)
def test_a_stated_decision_range_matches_the_register(doc: str | None):
    """`D-01..D-14` was written into two documents and went stale the moment a
    fifteenth decision was opened.

    `None` follows `state.handoff` rather than naming a file: the handoff moves,
    and a test that hardcoded its name would be the same defect one level up --
    which is exactly what the context guard was caught doing on 2026-08-27.
    """
    path = ROOT / (doc if doc else _state()["handoff"])
    ranges = re.findall(r"D-01\.\.D-(\d+)", path.read_text(encoding="utf-8"))
    if not ranges:
        pytest.skip(f"{path.name} states no decision range")
    highest = _highest_decision_in_the_register()
    for stated in ranges:
        assert int(stated) == highest, (
            f"{path.name} says the register runs to D-{stated} while its highest "
            f"entry is D-{highest:02d}"
        )
