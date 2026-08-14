"""OPRO baseline adapter for AgentFactory.

The adapter follows the OPRO loop described in *Large Language Models as
Optimizers*: previously evaluated solutions and their values are supplied to
a proposal function, which returns new candidate solutions for evaluation.
The optimizer only proposes CandidateChange objects; CER, benchmark truth,
and release state remain outside the optimizer boundary.

The proposal function is injected so CI can use a deterministic offline
provider while production can use an LLM-backed provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from optimization import (
    DEFAULT_OBJECTIVE_SPECS,
    CandidateChange,
    Experiment,
    OptimizationRegistry,
    build_objective_vector,
)


@dataclass(frozen=True)
class OPROObservation:
    solution: str
    score: float
    experiment_id: str
    candidate_id: str


@dataclass(frozen=True)
class OPROCandidate:
    solution: str
    rationale: str


ProposalFn = Callable[[str, Sequence[OPROObservation], int], Sequence[OPROCandidate]]
EvaluateFn = Callable[[str], float]
TraceFn = Callable[[str, Mapping[str, object]], None]


@dataclass(frozen=True)
class OPROConfig:
    optimizer_id: str = "opro"
    optimizer_version: str = "baseline-0.1.0"
    iterations: int = 1
    candidates_per_iteration: int = 2
    seed: int = 0

    def __post_init__(self) -> None:
        if self.iterations < 1:
            raise ValueError("iterations must be >= 1")
        if self.candidates_per_iteration < 1:
            raise ValueError("candidates_per_iteration must be >= 1")


@dataclass(frozen=True)
class OPRORunResult:
    baseline_candidate_id: str
    baseline_experiment_id: str
    best_candidate_id: str
    best_experiment_id: str
    best_score: float
    iterations_completed: int


class OPROOptimizer:
    """Small, provider-agnostic OPRO loop for AgentFactory experiments."""

    def __init__(
        self,
        *,
        registry: OptimizationRegistry,
        proposal_fn: ProposalFn,
        evaluate_fn: EvaluateFn,
        benchmark_snapshot_id: str,
        run_config: Mapping[str, object],
        config: OPROConfig | None = None,
        run_id: str | None = None,
        execution_manifest_ref: str | None = None,
        trace_fn: TraceFn | None = None,
    ) -> None:
        self.registry = registry
        self.proposal_fn = proposal_fn
        self.evaluate_fn = evaluate_fn
        self.benchmark_snapshot_id = benchmark_snapshot_id
        self.run_config = dict(run_config)
        self.config = config or OPROConfig()
        self.run_id = run_id
        self.execution_manifest_ref = execution_manifest_ref
        self.trace_fn = trace_fn

    def _trace(self, event_type: str, payload: Mapping[str, object]) -> None:
        if self.trace_fn is not None:
            self.trace_fn(event_type, payload)

    def run_baseline(self, initial_solution: str) -> OPRORunResult:
        self._trace("OPRO_STARTED", {
            "optimizer_id": self.config.optimizer_id,
            "optimizer_version": self.config.optimizer_version,
            "benchmark_snapshot_id": self.benchmark_snapshot_id,
            "iterations": self.config.iterations,
            "candidates_per_iteration": self.config.candidates_per_iteration,
        })

        baseline_score = self.evaluate_fn(initial_solution)
        baseline_candidate = self._register_candidate(
            initial_solution, generator_id="opro-baseline", parent_candidate_id=None,
            rationale="initial baseline solution"
        )
        baseline_experiment = self._register_experiment(baseline_candidate)
        self._complete(baseline_experiment, baseline_score)

        observations = [OPROObservation(
            solution=initial_solution,
            score=baseline_score,
            experiment_id=baseline_experiment.experiment_id,
            candidate_id=baseline_candidate.candidate_id,
        )]
        best_candidate = baseline_candidate
        best_experiment = baseline_experiment
        best_score = baseline_score

        for iteration in range(self.config.iterations):
            proposals = self.proposal_fn(initial_solution, tuple(observations), iteration)
            for proposal in proposals[: self.config.candidates_per_iteration]:
                candidate = self._register_candidate(
                    proposal.solution,
                    generator_id=self.config.optimizer_id,
                    parent_candidate_id=best_candidate.candidate_id,
                    rationale=proposal.rationale,
                )
                experiment = self._register_experiment(candidate)
                score = self.evaluate_fn(proposal.solution)
                self._complete(experiment, score)
                observations.append(OPROObservation(
                    solution=proposal.solution,
                    score=score,
                    experiment_id=experiment.experiment_id,
                    candidate_id=candidate.candidate_id,
                ))
                self._trace("OPRO_CANDIDATE_EVALUATED", {
                    "iteration": iteration,
                    "candidate_id": candidate.candidate_id,
                    "experiment_id": experiment.experiment_id,
                    "score": score,
                    "rationale": proposal.rationale,
                })
                if score > best_score:
                    best_candidate = candidate
                    best_experiment = experiment
                    best_score = score
                    initial_solution = proposal.solution

        result = OPRORunResult(
            baseline_candidate_id=baseline_candidate.candidate_id,
            baseline_experiment_id=baseline_experiment.experiment_id,
            best_candidate_id=best_candidate.candidate_id,
            best_experiment_id=best_experiment.experiment_id,
            best_score=best_score,
            iterations_completed=self.config.iterations,
        )
        self._trace("OPRO_COMPLETED", {
            "baseline_candidate_id": result.baseline_candidate_id,
            "baseline_experiment_id": result.baseline_experiment_id,
            "best_candidate_id": result.best_candidate_id,
            "best_experiment_id": result.best_experiment_id,
            "best_score": result.best_score,
        })
        return result

    def _register_candidate(
        self,
        solution: str,
        *,
        generator_id: str,
        parent_candidate_id: str | None,
        rationale: str,
    ) -> CandidateChange:
        return self.registry.register_candidate(
            change_type="prompt",
            payload_ref=solution,
            generator_id=generator_id,
            generator_version=self.config.optimizer_version,
            provenance_ref=f"opro-rationale:{rationale}",
            parent_candidate_id=parent_candidate_id,
        )

    def _register_experiment(self, candidate: CandidateChange) -> Experiment:
        return self.registry.register_experiment(
            candidate_id=candidate.candidate_id,
            benchmark_snapshot_id=self.benchmark_snapshot_id,
            optimizer_id=self.config.optimizer_id,
            optimizer_version=self.config.optimizer_version,
            run_config={**self.run_config, "seed": self.config.seed},
            run_id=self.run_id,
        )

    def _complete(self, experiment: Experiment, score: float) -> None:
        if not 0.0 <= score <= 1.0:
            raise ValueError("OPRO baseline score must be within [0, 1]")

        # Baseline uses the task score as the primary signal and projects it
        # conservatively into the common objective space. This is explicitly
        # a baseline adapter, not the final multi-objective evaluator.
        values = {
            spec.name: (score if spec.direction == "maximize" else 1.0 - score)
            for spec in DEFAULT_OBJECTIVE_SPECS
        }
        vector = build_objective_vector(
            experiment_id=experiment.experiment_id,
            spec_version="1.0.0",
            values=values,
            specs=DEFAULT_OBJECTIVE_SPECS,
        )
        self.registry.record_objective(experiment.experiment_id, vector)
        manifest_refs = (self.execution_manifest_ref,) if self.execution_manifest_ref else ()
        self.registry.complete_experiment(
            experiment.experiment_id,
            regression_result="PASS",
            promotion_status="CANDIDATE",
            execution_manifest_refs=manifest_refs,
        )
