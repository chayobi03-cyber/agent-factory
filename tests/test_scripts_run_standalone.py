"""Every script in `scripts/` runs on a bare clone, with no environment set.

`scripts/` resolved imports two ways. Six scripts put `src/` on `sys.path`
themselves; `opro_baseline.py` and `domain_matrix_demo.py` did not, and read
the ambient `PYTHONPATH` that only `.github/workflows/factory-kernel.yml` and
`.claude/hooks/session-start.sh` set. Both therefore raised
`ModuleNotFoundError` for anyone running them directly.

Two things kept it alive. The failure is invisible from the other six --
`re_demo.py` and `factory_demo.py` run without `PYTHONPATH` and prove nothing
about the two that don't. And CI *sets* `PYTHONPATH`, so no workflow could ever
have caught it: the environment that hides the defect is the one the only
automated check runs in.

The 2026-08-29 handoff recorded which convention should win as an open
question. The answer taken here is the majority one, in the direction that
removes a dependency rather than adding one: all eight bootstrap, and the
exported `PYTHONPATH` stays valid but is now redundant. This test is what makes
that an invariant instead of a note -- it scrubs `PYTHONPATH` and runs each
script in a subprocess, which is the only way to see it. An in-process import
would pass on the path pytest has already set up.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

#: How to invoke each script for real, or `None` to check only that it imports.
#:
#: Every script is listed, and `test_every_script_is_accounted_for` fails when
#: one is added without a decision here -- an unlisted script would otherwise
#: be silently skipped by the check written to catch exactly this defect.
#:
#: `None` for the three CI helpers, which take required arguments rather than
#: running on their own, and for `calibrate_retrieval.py`, whose full sweep
#: takes ~28s against this corpus. `tests/test_calibrate_retrieval.py` skips
#: its CLI for the same reason and drives the sweep functions directly.
RUN_ARGV: dict[str, list[str] | None] = {
    "calibrate_retrieval.py": None,
    "capture_execution.py": None,
    "domain_matrix_demo.py": ["--json"],
    "evidence_gate.py": None,
    "factory_demo.py": ["--scenario", "all", "--json"],
    "opro_baseline.py": ["--json"],
    "re_demo.py": ["--json"],
    "routing_benchmark.py": ["--json"],
    "run_domain.py": ["--list"],
    "run_harness.py": ["--json"],
    "validate_project_context.py": [],
    "validate_session_resume.py": [],
    "validate_session_state.py": [],
    "verify_artifact_sha256.py": None,
}


def _scripts() -> list[Path]:
    found = sorted(p for p in SCRIPTS.glob("*.py") if not p.name.startswith("_"))
    assert found, "found no scripts to check -- the tree layout changed"
    return found


def _bare_env() -> dict[str, str]:
    """The environment of someone who has just cloned the repository.

    `PYTHONPATH` scrubbed, because that is the crutch under test.
    `AGENTFACTORY_TARGET_BRANCH` set, because the three validators resolve the
    branch from git and a session branch is not the trunk (D-02). That is a
    different question from import resolution and would otherwise mask it.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["AGENTFACTORY_TARGET_BRANCH"] = "main"
    return env


def _run(script: Path, argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True, cwd=ROOT, env=_bare_env())


def test_every_script_is_accounted_for() -> None:
    present = {p.name for p in _scripts()}
    assert present == set(RUN_ARGV), (
        f"unlisted: {sorted(present - set(RUN_ARGV))}; "
        f"listed but absent: {sorted(set(RUN_ARGV) - present)}"
    )


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_a_script_imports_without_an_ambient_pythonpath(script: Path) -> None:
    """`--help` runs argparse, which runs after every module-level import, so a
    script whose local imports do not resolve exits non-zero here. This is what
    caught the two, and it covers the CI helpers that cannot be run bare."""
    done = _run(script, ["--help"])
    assert done.returncode == 0, (
        f"{script.name} does not import on a bare clone:\n{done.stderr.strip()}\n"
        "Put src/ on sys.path in the script, as the other seven do, rather than "
        "relying on a PYTHONPATH that only CI and the session hook set."
    )


@pytest.mark.parametrize(
    "script", [p for p in _scripts() if RUN_ARGV.get(p.name) is not None],
    ids=lambda p: p.name,
)
def test_a_script_runs_without_an_ambient_pythonpath(script: Path) -> None:
    """Importing is not running. Both defects were module-level and `--help`
    would have caught them, but an import deferred into a function would pass
    that check and still fail the first time anyone ran the thing."""
    done = _run(script, RUN_ARGV[script.name])
    assert done.returncode == 0, (
        f"{script.name} fails on a bare clone (exit {done.returncode}):\n"
        f"{done.stderr.strip()[-600:]}"
    )
