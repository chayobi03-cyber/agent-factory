"""The suite must not depend on the shell it is run from.

`AGENTFACTORY_TARGET_BRANCH` is the local escape hatch that lets the three
validators resolve which branch a feature checkout targets (OPEN_DECISIONS
D-02). It is exactly what a contributor exports before running the validators
by hand -- and the handoff document tells them to -- so it is routinely set in
the same shell that then runs pytest.

Three test files had each remembered to clear it, once, in one test. The fourth
place did not exist until `validate_session_state.py` took the same escape hatch
on 2026-08-27, and its tests were written without the guard: the suite then
passed with the variable unset and failed with it set, deterministically, while
reading as an intermittent failure because whether it was set depended on which
shell the run happened in.

Clearing it once here is the fix. A test that wants either variable sets it with
`monkeypatch.setenv`, which runs after this fixture, so nothing that
deliberately exercises the override is affected.
"""
import pytest

#: Environment a test must never inherit from whoever started pytest.
LEAKY = ("AGENTFACTORY_TARGET_BRANCH", "GITHUB_ACTIONS")


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch):
    for name in LEAKY:
        monkeypatch.delenv(name, raising=False)
