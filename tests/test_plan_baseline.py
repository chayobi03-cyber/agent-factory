"""The regression guard LSN-0001 said it could not have.

LSN-0001 recorded `regression_guard: N/A (process lesson, not a code
regression)` and `status: candidate`. Nothing enforced it, and on 2026-08-30 the
same failure arrived again -- the APF Living Specification package, 368 lines
proposing contracts that already run under CI, written against no stated
baseline (LSN-0003).

"Process lesson" turned out to describe why it was unenforced, not why it was
unenforceable. These are its cases.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "verify_plan_baseline.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def test_a_plan_declaring_no_baseline_is_referred(tmp_path):
    """The APF case, reduced: a plan that proposes work and names nothing.

    This is the one that matters. The package was rejected on content by a human
    audit; this refers it on structure, before anyone reads it.
    """
    plan = tmp_path / "plan.md"
    plan.write_text("# Next steps\n\nBuild a workflow state machine and a CER gate.\n")
    result = run(str(plan))
    assert result.returncode == 2
    assert "PLAN_BASELINE=REVIEW_REQUIRED" in result.stdout
    assert "no baseline declared" in result.stdout


def test_a_plan_written_against_the_current_head_passes():
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    result = run("--baseline", head, "--target", "HEAD")
    assert result.returncode == 0, result.stdout
    assert "PLAN_BASELINE=PASS" in result.stdout


def test_a_baseline_extracted_from_prose_is_used(tmp_path):
    """The declaration does not have to be structured to count."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    plan = tmp_path / "handoff.md"
    plan.write_text(f"Written against baseline {head}. Proposes adding a retriever.\n")
    result = run(str(plan), "--target", "HEAD")
    assert result.returncode == 0, result.stdout
    assert head[:12] in result.stdout


def test_an_unresolvable_baseline_is_referred_not_blocked_in_a_shallow_clone():
    """LSN-0002's lesson, applied to this guard.

    That lesson: a fail-closed guard tested under only one of the situations it
    runs in can make a legitimate one structurally unusable. Web sessions and CI
    checkouts are shallow clones, where a baseline beyond the fetch depth is
    unresolvable without being absent. Calling that BLOCKED would fail every
    handoff in this repository -- its own `audited_baseline_sha` (20a54b92) is
    outside the default depth.

    The distinction is asserted here because it is the difference between a
    guard people run and one they route around.
    """
    absent = "0" * 40
    result = run("--baseline", absent, "--target", "HEAD")
    assert result.returncode == 2
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip() == "true"
    if shallow:
        assert "PLAN_BASELINE=REVIEW_REQUIRED" in result.stdout
        assert "shallow clone" in result.stdout
    else:
        assert "PLAN_BASELINE=BLOCKED" in result.stdout


def test_a_missing_plan_file_is_blocked_not_passed():
    """A guard that cannot read its input must never report PASS."""
    result = run(str(ROOT / "does-not-exist.md"))
    assert result.returncode == 2
    assert "PLAN_BASELINE=BLOCKED" in result.stdout


@pytest.mark.parametrize("stream", ["stdout"])
def test_the_guard_never_prints_pass_on_a_failure_path(stream, tmp_path):
    """Fail-closed: no failing invocation may emit a PASS token."""
    plan = tmp_path / "empty.md"
    plan.write_text("no baseline here\n")
    for args in ([str(plan)], ["--baseline", "0" * 40], [str(ROOT / "nope.md")]):
        result = run(*args)
        assert result.returncode == 2
        assert "PLAN_BASELINE=PASS" not in getattr(result, stream)
