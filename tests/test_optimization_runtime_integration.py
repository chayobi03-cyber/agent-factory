import pytest

from factory_runtime import FactoryRuntime
from optimization import DEFAULT_OBJECTIVE_SPECS


def make_runtime():
    runtime = FactoryRuntime(repository_commit="integration-commit")
    snapshot = runtime.create_snapshot(
        policy_id="CER",
        policy_version="1.0.0",
        source_commit="integration-commit",
        required_checks=["GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"],
        snapshot_id="INT-SNAP-001",
    )
    run = runtime.create_run(
        task_id="OPT-INT",
        idempotency_key="OPT-INT-001",
        snapshot=snapshot,
    )
    return runtime, snapshot, run


def objective_values():
    return {spec.name: 0.8 for spec in DEFAULT_OBJECTIVE_SPECS}


def test_candidate_and_experiment_are_bound_to_factory_run_trace():
    runtime, snapshot, run = make_runtime()
    candidate = runtime.create_optimization_candidate(
        run_id=run.run_id,
        change_type="prompt_instruction",
        payload_ref="artifact:prompt:v1",
        generator_id="manual-baseline",
        generator_version="1",
        provenance_ref="trace:baseline",
    )
    experiment = runtime.create_optimization_experiment(
        run_id=run.run_id,
        candidate_id=candidate.candidate_id,
        benchmark_snapshot_id="factory-kernel-v0.1",
        optimizer_id="baseline",
        optimizer_version="1",
        run_config={"seed": 1},
    )
    assert experiment.run_id == run.run_id
    events = runtime.get_trace(run.run_id).events
    assert any(e.event_type == "OPTIMIZATION_CANDIDATE_REGISTERED" for e in events)
    assert any(e.event_type == "OPTIMIZATION_EXPERIMENT_REGISTERED" for e in events)


def test_objective_and_execution_manifest_are_linked_to_experiment():
    runtime, snapshot, run = make_runtime()
    candidate = runtime.create_optimization_candidate(
        run_id=run.run_id,
        change_type="prompt_instruction",
        payload_ref="artifact:prompt:v1",
        generator_id="manual-baseline",
        generator_version="1",
        provenance_ref="trace:baseline",
    )
    experiment = runtime.create_optimization_experiment(
        run_id=run.run_id,
        candidate_id=candidate.candidate_id,
        benchmark_snapshot_id="factory-kernel-v0.1",
        optimizer_id="baseline",
        optimizer_version="1",
        run_config={"seed": 1},
    )
    vector = runtime.record_optimization_objective(
        run_id=run.run_id,
        experiment_id=experiment.experiment_id,
        values=objective_values(),
    )
    runtime.record_execution_evidence(
        run_id=run.run_id,
        command="pytest -q",
        commit_sha="integration-commit",
        exit_code=0,
        stdout="PASSED",
        stderr="",
        result_summary="optimization integration",
    )
    completed = runtime.complete_optimization_experiment(
        run_id=run.run_id,
        experiment_id=experiment.experiment_id,
        regression_result="PASS",
    )
    assert completed.objective_vector_id == vector.vector_id
    assert completed.regression_result == "PASS"
    assert completed.execution_manifest_refs
    assert "integration-commit" not in completed.execution_manifest_refs[0] or runtime.get_manifest(run.run_id).execution_manifest_hash in completed.execution_manifest_refs[0]
    events = runtime.get_trace(run.run_id).events
    assert any(e.event_type == "OPTIMIZATION_OBJECTIVE_RECORDED" for e in events)
    assert any(e.event_type == "EXECUTION_EVIDENCE" for e in events)
    assert any(e.event_type == "OPTIMIZATION_EXPERIMENT_COMPLETED" for e in events)


def test_experiment_cannot_cross_run_boundary():
    runtime, snapshot, run = make_runtime()
    other_snapshot = runtime.create_snapshot(
        policy_id="CER", policy_version="1.0.0", source_commit="integration-commit",
        required_checks=["RISK"], snapshot_id="INT-SNAP-002",
    )
    other = runtime.create_run(task_id="OTHER", idempotency_key="OTHER-001", snapshot=other_snapshot)
    candidate = runtime.create_optimization_candidate(
        run_id=run.run_id,
        change_type="prompt_instruction",
        payload_ref="artifact:prompt:v1",
        generator_id="manual-baseline",
        generator_version="1",
        provenance_ref="trace:baseline",
    )
    experiment = runtime.create_optimization_experiment(
        run_id=run.run_id,
        candidate_id=candidate.candidate_id,
        benchmark_snapshot_id="factory-kernel-v0.1",
        optimizer_id="baseline",
        optimizer_version="1",
        run_config={"seed": 1},
    )
    with pytest.raises(ValueError):
        runtime.record_optimization_objective(
            run_id=other.run_id,
            experiment_id=experiment.experiment_id,
            values=objective_values(),
        )
