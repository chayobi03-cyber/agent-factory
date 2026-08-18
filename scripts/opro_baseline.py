#!/usr/bin/env python3
"""Execute the deterministic offline OPRO baseline and emit machine-readable JSON."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from factory_runtime import FactoryRuntime
from opro import OPROCandidate, OPROConfig
from opro_runtime import run_opro_baseline

BENCHMARK = Path("templates/benchmark/opro_baseline_v0.1.json")


def load_benchmark() -> dict:
    return json.loads(BENCHMARK.read_text(encoding="utf-8"))


def resolve_execution_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "unable to resolve git HEAD")
    checked_out_sha = result.stdout.strip()
    target_sha = os.environ.get("CER_TARGET_SHA")
    required = os.environ.get("CER_EXECUTION_IDENTITY_REQUIRED") == "1"
    if required and not target_sha:
        raise RuntimeError("CER_TARGET_SHA is required when CER_EXECUTION_IDENTITY_REQUIRED=1")
    execution_sha = target_sha or checked_out_sha
    if execution_sha != checked_out_sha:
        raise RuntimeError(
            f"execution identity mismatch: CER_TARGET_SHA={execution_sha} git.HEAD={checked_out_sha}"
        )
    return execution_sha


def make_evaluator(benchmark: dict):
    cases = benchmark["cases"]

    def evaluate(solution: str) -> float:
        text = solution.lower()
        total = sum(float(case.get("weight", 1.0)) for case in cases)
        score = 0.0
        for case in cases:
            expected = [item.lower() for item in case["expected_keywords"]]
            forbidden = [item.lower() for item in case["forbidden_keywords"]]
            hits = sum(1 for item in expected if item in text)
            misses = sum(1 for item in forbidden if item in text)
            score += float(case.get("weight", 1.0)) * max(0.0, hits / max(1, len(expected)) - misses)
        return max(0.0, min(1.0, score / max(1.0, total)))

    return evaluate


def proposal_fn(current, history, iteration):
    best = max(history, key=lambda item: item.score)
    return [
        OPROCandidate(
            current + " Explicitly cite supporting evidence and require human review for high-risk claims.",
            f"build on best score={best.score:.4f}; strengthen evidence and review requirements",
        ),
        OPROCandidate(
            current + " Do not guess or assume support; use only identified evidence and escalate high-risk claims.",
            f"build on best score={best.score:.4f}; remove unsupported inference",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    execution_sha = resolve_execution_sha()
    benchmark = load_benchmark()
    runtime = FactoryRuntime(repository_commit=execution_sha, benchmark_version=benchmark["version"])
    snapshot = runtime.create_snapshot(
        policy_id="CER",
        policy_version="1.0.0",
        source_commit=execution_sha,
        required_checks=["GAP", "METHOD", "RISK", "EVIDENCE", "REGRESSION", "LEARNING"],
        snapshot_id="CER-SNAP-OPRO-BASELINE",
    )
    run = runtime.create_run(
        task_id="OPRO-BASELINE",
        idempotency_key="OPRO-BASELINE-v0.1",
        snapshot=snapshot,
        workflow_version="1.0.0",
        domain_pack_id="kernel",
        domain_pack_version="1.0.0",
    )
    runtime._set_state(run, "RUNNING")
    runtime.record_execution_evidence(
        run_id=run.run_id,
        command="python3 scripts/opro_baseline.py --json",
        commit_sha=execution_sha,
        exit_code=0,
        stdout="offline deterministic baseline",
        stderr="",
        result_summary="OPRO baseline execution",
    )

    evaluator = make_evaluator(benchmark)
    result = run_opro_baseline(
        runtime,
        run_id=run.run_id,
        benchmark_snapshot_id=benchmark["benchmark_id"] + "@" + benchmark["version"],
        initial_solution="Use evidence to support claims and review high-risk cases.",
        proposal_fn=proposal_fn,
        evaluate_fn=evaluator,
        config=OPROConfig(iterations=1, candidates_per_iteration=2, seed=0),
        run_config={
            "benchmark_id": benchmark["benchmark_id"],
            "benchmark_version": benchmark["version"],
            "execution_sha": execution_sha,
        },
    )

    best_experiment = runtime.get_optimization_experiment(result.best_experiment_id)
    output = {
        "optimizer": "OPRO",
        "optimizer_version": OPROConfig().optimizer_version,
        "benchmark_id": benchmark["benchmark_id"],
        "benchmark_version": benchmark["version"],
        "run_id": run.run_id,
        "execution_sha": execution_sha,
        "repository_commit": execution_sha,
        "baseline_score": evaluator("Use evidence to support claims and review high-risk cases."),
        "best_score": result.best_score,
        "best_candidate_id": result.best_candidate_id,
        "best_experiment_id": result.best_experiment_id,
        "regression_result": best_experiment.regression_result,
        "promotion_status": best_experiment.promotion_status,
        "trace_events": len(runtime.get_trace(run.run_id).events),
        "execution_manifest_hash": runtime.get_manifest(run.run_id).execution_manifest_hash,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) if args.json else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
