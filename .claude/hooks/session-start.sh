#!/bin/bash
# SessionStart hook for Claude Code on the web.
#
# A web session starts on a fresh container and on a `claude/*` working branch.
# Two things follow from that, and this hook fixes both so the verification
# block in the current handoff document runs as written:
#
#   1. pytest is not installed. The container carries a Debian-managed PyYAML
#      6.0.1 already, which is the repository's only other third-party import.
#   2. The checkout is not the trunk, so scripts/validate_project_context.py,
#      scripts/validate_session_resume.py and scripts/validate_session_state.py
#      all exit 2 -- they resolve the active branch from git and compare it to
#      the canonical trunk. AGENTFACTORY_TARGET_BRANCH is the documented local
#      escape hatch for exactly this (OPEN_DECISIONS D-02).
#
# Synchronous by design: the session should not begin until the tools it will
# be asked to run actually exist.
set -euo pipefail

# Local checkouts already have their own environment; only the remote container
# needs building up.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

project_dir="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$project_dir"

# --- Dependencies ---------------------------------------------------------
#
# Idempotent: a cached container re-running this hook reinstalls nothing.
#
# pytest only. CI installs `--upgrade pytest pyyaml`, which is right on a clean
# actions/setup-python runner but wrong here: pip cannot uninstall the
# Debian-managed PyYAML ("RECORD file not found") and the failure aborts the
# whole install, taking pytest down with it. Install what is missing instead.
if ! python3 -m pytest --version >/dev/null 2>&1; then
  echo "session-start: installing pytest"
  python3 -m pip install --quiet --disable-pip-version-check pytest
fi

if ! python3 -c "import yaml" >/dev/null 2>&1; then
  echo "session-start: installing pyyaml"
  python3 -m pip install --quiet --disable-pip-version-check pyyaml
fi

# --- Environment ----------------------------------------------------------
#
# The trunk name is read from state rather than written here. This repository
# has repeatedly been bitten by one definition living in two places, and the
# trunk has already moved once; scripts/validate_project_context.py pins its
# own EXPECTED_BRANCH against state.working_branch, so deriving from state
# keeps this hook from becoming a third copy that can drift.
target_branch="$(
  python3 - <<'PY' 2>/dev/null || true
import yaml
with open("docs/governance/CURRENT_SESSION_STATE.yaml", encoding="utf-8") as fh:
    state = yaml.safe_load(fh)
branch = state.get("working_branch")
if isinstance(branch, str) and branch.strip():
    print(branch.strip())
PY
)"

# PYTHONPATH matches what factory-kernel.yml sets. Six of the eight scripts in
# scripts/ insert the repository root on sys.path themselves and run without it;
# `opro_baseline.py` and `domain_matrix_demo.py` do not, and fail with
# ModuleNotFoundError outside CI. Import resolution is handled two different
# ways across one directory, and only the env-var half is invisible until you
# run those two -- so reproduce CI's environment rather than the half of it that
# happens to work.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PYTHONPATH=\"${project_dir}:${project_dir}/src\${PYTHONPATH:+:\$PYTHONPATH}\"" \
    >> "$CLAUDE_ENV_FILE"
  echo "session-start: PYTHONPATH=${project_dir}:${project_dir}/src"
fi

if [ -n "$target_branch" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  # Safe for the test suite: tests/conftest.py clears this variable per test,
  # so a value exported into the session cannot reach a test that did not ask
  # for it. Safe for CI: the validators ignore the override whenever
  # GITHUB_ACTIONS is set, so it can only ever loosen a local run.
  echo "export AGENTFACTORY_TARGET_BRANCH=\"${target_branch}\"" >> "$CLAUDE_ENV_FILE"
  echo "session-start: AGENTFACTORY_TARGET_BRANCH=${target_branch} (from state.working_branch)"
elif [ -z "$target_branch" ]; then
  echo "session-start: WARNING could not read working_branch from" \
       "docs/governance/CURRENT_SESSION_STATE.yaml;" \
       "export AGENTFACTORY_TARGET_BRANCH by hand before running the validators" >&2
fi

echo "session-start: ready"
