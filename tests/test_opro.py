from opro import OPROCandidate, OPROConfig, OPROOptimizer
from optimization import OptimizationRegistry


def test_opro_baseline_creates_lineage_and_improves_score():
    registry = OptimizationRegistry()

    def evaluate(solution: str) -> float:
        return {"baseline instruction": 0.50, "clear instruction": 0.75, "clear concise instruction": 0.90}[solution]

    def propose(_current, _history, _iteration):
        return [
            OPROCandidate("clear instruction", "add explicit objective"),
            OPROCandidate("clear concise instruction", "reduce ambiguity"),
        ]

    result = OPROOptimizer(
        registry=registry,
        proposal_fn=propose,
        evaluate_fn=evaluate,
        benchmark_snapshot_id="BENCH-SNAP-OPRO-1",
        run_config={"benchmark": "opro-baseline-v0.1"},
        config=OPROConfig(iterations=1, candidates_per_iteration=2),
    ).run_baseline("baseline instruction")

    assert result.best_score == 0.90
    assert result.best_candidate_id != result.baseline_candidate_id
    assert result.best_experiment_id != result.baseline_experiment_id

    best = registry.get_experiment(result.best_experiment_id)
    assert best.benchmark_snapshot_id == "BENCH-SNAP-OPRO-1"
    assert best.regression_result == "PASS"
    assert best.promotion_status == "CANDIDATE"


def test_opro_does_not_directly_mutate_governance():
    registry = OptimizationRegistry()
    optimizer = OPROOptimizer(
        registry=registry,
        proposal_fn=lambda *_: [],
        evaluate_fn=lambda _: 0.5,
        benchmark_snapshot_id="B",
        run_config={},
    )
    result = optimizer.run_baseline("safe prompt")
    candidate = registry.get_candidate(result.baseline_candidate_id)
    assert candidate.change_type == "prompt"
    assert candidate.generator_id == "opro-baseline"
