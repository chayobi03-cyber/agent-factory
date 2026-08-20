"""FactoryRuntime bridge for the OPRO baseline adapter."""
from __future__ import annotations

from typing import Mapping

from factory_runtime import FactoryRuntime
from opro import OPROConfig, OPROOptimizer, OPRORunResult, ProposalFn, EvaluateFn


def run_opro_baseline(
    runtime: FactoryRuntime,
    *,
    run_id: str,
    benchmark_snapshot_id: str,
    initial_solution: str,
    proposal_fn: ProposalFn,
    evaluate_fn: EvaluateFn,
    config: OPROConfig | None = None,
    run_config: Mapping[str, object] | None = None,
) -> OPRORunResult:
    """Run OPRO inside an existing FactoryRun and bind all experiments to it."""
    manifest = runtime.get_manifest(run_id)
    manifest_ref = f"run-manifest:{run_id}:{manifest.execution_manifest_hash}"

    optimizer = OPROOptimizer(
        registry=runtime.optimization,
        proposal_fn=proposal_fn,
        evaluate_fn=evaluate_fn,
        benchmark_snapshot_id=benchmark_snapshot_id,
        run_config=run_config or {},
        config=config,
        run_id=run_id,
        execution_manifest_ref=manifest_ref,
        trace_fn=lambda event_type, payload: runtime.record_trace(run_id, event_type, payload),
    )
    result = optimizer.run_baseline(initial_solution)

    runtime.record_trace(run_id, "OPRO_RESULT", {
        "baseline_candidate_id": result.baseline_candidate_id,
        "baseline_experiment_id": result.baseline_experiment_id,
        "best_candidate_id": result.best_candidate_id,
        "best_experiment_id": result.best_experiment_id,
        "best_score": result.best_score,
        "benchmark_snapshot_id": benchmark_snapshot_id,
        "execution_manifest_ref": manifest_ref,
    })
    return result
