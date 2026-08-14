import pytest

from cer_runtime import WorkflowRunState
from factory_runtime import WorkflowStateMachine


def test_retry_limit_is_enforced():
    machine = WorkflowStateMachine(retry_limit=2, loop_limit=10)
    state = WorkflowRunState("RUN-1", "TASK-1", "SNAP-1", status="RUNNING")
    state = machine.transition(state, "RETRYING")
    state = machine.transition(state, "RUNNING")
    state = machine.transition(state, "RETRYING")
    with pytest.raises(RuntimeError, match="retry limit"):
        machine.transition(state, "RETRYING")


def test_blocked_state_cannot_reenter():
    machine = WorkflowStateMachine()
    state = WorkflowRunState("RUN-2", "TASK-2", "SNAP-2", status="RUNNING")
    state = machine.transition(state, "BLOCKED")
    with pytest.raises(RuntimeError, match="fail-closed"):
        machine.transition(state, "RUNNING")


def test_terminal_completion_cannot_execute_again():
    machine = WorkflowStateMachine()
    state = WorkflowRunState("RUN-3", "TASK-3", "SNAP-3", status="RUNNING")
    state = machine.transition(state, "COMPLETED")
    with pytest.raises(ValueError):
        machine.transition(state, "RUNNING")
