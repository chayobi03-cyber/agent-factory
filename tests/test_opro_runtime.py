from factory_runtime import FactoryRuntime
from opro import OPROCandidate, OPROConfig
from opro_runtime import run_opro_baseline


def test_opro_baseline_binds_experiments_to_factory_run():
    runtime = FactoryRuntime(repository_commit="abc123", benchmark_version="0.1.0")
    snapshot = runtime.create_snapshot(
        policy_id="CER",
        policy_version="1.0.0",
        source_commit="abc123",
        required_checks=["EVIDENCE", "REGRESSION"],
        snapshot_id="CER-SNAP-OPRO-TEST",
    )
    run = runtime.create_run(
        task_id="OPRO-TEST",
        idempotency_key="OPRO-TEST-1",
        snapshot=snapshot,
    )
    runtime._set_state(run, "RUNNING")
    runtime.record_execution_evidence(
        run_id=run.run_id,
        command="pytest tests/test_opro_runtime.py",
        commit_sha="abc123",
        exit_code=0,
        stdout="PASS",
        stderr="",
        result_summary="OPRO runtime test",
    )

    result = run_opro_baseline(
        runtime,
        run_id=run.run_id,
        benchmark_snapshot_id="opro-baseline-v0.1@0.1.0",
        initial_solution="baseline",
        proposal_fn=lambda *_: [OPROCandidate("better", "improve")],
        evaluate_fn=lambda solution: 0.5 if solution == "baseline" else 0.8,
        config=OPROConfig(iterations=1, candidates_per_iteration=1),
    )

    experiment = runtime.get_optimization_experiment(result.best_experiment_id)
    assert experiment.run_id == run.run_id
    assert experiment.benchmark_snapshot_id == "opro-baseline-v0.1@0.1.0"
    assert experiment.execution_manifest_refs
    events = runtime.get_trace(run.run_id).events
    assert any(event.event_type == "OPRO_STARTED" for event in events)
    assert any(event.event_type == "OPRO_CANDIDATE_EVALUATED" for event in events)
    assert any(event.event_type == "OPRO_RESULT" for event in events)
