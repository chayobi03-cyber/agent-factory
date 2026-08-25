import pytest

from optimization import DEFAULT_OBJECTIVE_SPECS, OptimizationRegistry, build_objective_vector


def test_objective_vector_normalizes_and_preserves_direction():
    registry = OptimizationRegistry()
    candidate = registry.register_candidate(
        change_type="prompt", payload_ref="prompt://v2", generator_id="manual",
        generator_version="1", provenance_ref="prov://1"
    )
    experiment = registry.register_experiment(
        candidate_id=candidate.candidate_id,
        benchmark_snapshot_id="BENCH-SNAP-1",
        optimizer_id="manual",
        optimizer_version="1",
        run_config={"seed": 1},
    )
    vector = build_objective_vector(
        experiment_id=experiment.experiment_id,
        spec_version="1.0.0",
        values={spec.name: (0.8 if spec.direction == "maximize" else 0.2)
                for spec in DEFAULT_OBJECTIVE_SPECS},
        specs=DEFAULT_OBJECTIVE_SPECS,
    )
    assert vector.vector_hash
    assert len(vector.values) == 8
    assert all(0.0 <= item.normalized_value <= 1.0 for item in vector.values)


def test_objective_spaces_can_compare_pareto_dominance():
    registry = OptimizationRegistry()
    c = registry.register_candidate(change_type="prompt", payload_ref="p", generator_id="g", generator_version="1", provenance_ref="r")
    e1 = registry.register_experiment(candidate_id=c.candidate_id, benchmark_snapshot_id="B", optimizer_id="x", optimizer_version="1", run_config={"seed": 1})
    e2 = registry.register_experiment(candidate_id=c.candidate_id, benchmark_snapshot_id="B", optimizer_id="x", optimizer_version="1", run_config={"seed": 2})
    values_a = {spec.name: (0.9 if spec.direction == "maximize" else 0.1) for spec in DEFAULT_OBJECTIVE_SPECS}
    values_b = {spec.name: (0.8 if spec.direction == "maximize" else 0.2) for spec in DEFAULT_OBJECTIVE_SPECS}
    a = build_objective_vector(experiment_id=e1.experiment_id, spec_version="1", values=values_a, specs=DEFAULT_OBJECTIVE_SPECS)
    b = build_objective_vector(experiment_id=e2.experiment_id, spec_version="1", values=values_b, specs=DEFAULT_OBJECTIVE_SPECS)
    assert a.dominates(b)
    assert not b.dominates(a)


def test_registry_blocks_direct_governance_mutation():
    registry = OptimizationRegistry()
    with pytest.raises(ValueError):
        registry.register_candidate(change_type="cer_policy", payload_ref="p", generator_id="opro", generator_version="1", provenance_ref="r")
    with pytest.raises(ValueError):
        registry.register_candidate(change_type="benchmark_truth", payload_ref="p", generator_id="gepa", generator_version="1", provenance_ref="r")


def test_experiment_requires_passing_regression_for_approval():
    registry = OptimizationRegistry()
    candidate = registry.register_candidate(change_type="workflow_parameter", payload_ref="p", generator_id="manual", generator_version="1", provenance_ref="r")
    experiment = registry.register_experiment(candidate_id=candidate.candidate_id, benchmark_snapshot_id="B", optimizer_id="manual", optimizer_version="1", run_config={})
    with pytest.raises(ValueError):
        registry.complete_experiment(experiment.experiment_id, regression_result="FAIL", promotion_status="APPROVED")
    updated = registry.complete_experiment(experiment.experiment_id, regression_result="PASS", promotion_status="APPROVED", execution_manifest_refs=["RUN-MANIFEST-1"])
    assert updated.promotion_status == "APPROVED"
