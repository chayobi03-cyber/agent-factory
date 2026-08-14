"""Optimization substrate: objective vectors and immutable candidate/experiment registry."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Mapping, Sequence

DEFAULT_OBJECTIVES = (
    ("quality", "maximize"),
    ("evidence_support", "maximize"),
    ("regression_safety", "maximize"),
    ("latency", "minimize"),
    ("cost", "minimize"),
    ("human_intervention", "minimize"),
    ("trace_completeness", "maximize"),
    ("reproducibility", "maximize"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ObjectiveSpec:
    name: str
    direction: str
    minimum: float = 0.0
    maximum: float = 1.0

    def normalize(self, value: float) -> float:
        if self.direction not in {"maximize", "minimize"}:
            raise ValueError(f"unsupported objective direction: {self.direction}")
        if self.maximum <= self.minimum:
            raise ValueError(f"invalid objective range for {self.name}")
        if not self.minimum <= value <= self.maximum:
            raise ValueError(f"objective {self.name} value out of range: {value}")
        normalized = (value - self.minimum) / (self.maximum - self.minimum)
        return normalized if self.direction == "maximize" else 1.0 - normalized


@dataclass(frozen=True)
class ObjectiveValue:
    name: str
    raw_value: float
    normalized_value: float
    direction: str


@dataclass(frozen=True)
class ObjectiveVector:
    vector_id: str
    experiment_id: str
    spec_version: str
    values: tuple[ObjectiveValue, ...]
    vector_hash: str

    def as_mapping(self) -> Mapping[str, float]:
        return {item.name: item.normalized_value for item in self.values}

    def dominates(self, other: "ObjectiveVector") -> bool:
        if {v.name for v in self.values} != {v.name for v in other.values}:
            raise ValueError("objective spaces do not match")
        ours = self.as_mapping()
        theirs = other.as_mapping()
        return all(ours[name] >= theirs[name] for name in ours) and any(
            ours[name] > theirs[name] for name in ours
        )


def build_objective_vector(
    *, experiment_id: str, spec_version: str, values: Mapping[str, float],
    specs: Sequence[ObjectiveSpec],
) -> ObjectiveVector:
    spec_map = {item.name: item for item in specs}
    if set(values) != set(spec_map):
        raise ValueError("objective values must exactly match the objective specification")
    items = []
    for name in sorted(values):
        spec = spec_map[name]
        items.append(ObjectiveValue(name, values[name], spec.normalize(values[name]), spec.direction))
    vector_id = f"OBJ-{uuid.uuid4().hex[:12]}"
    digest = stable_hash({"experiment_id": experiment_id, "spec_version": spec_version,
                          "values": [asdict(item) for item in items]})
    return ObjectiveVector(vector_id, experiment_id, spec_version, tuple(items), digest)


@dataclass(frozen=True)
class CandidateChange:
    candidate_id: str
    parent_candidate_id: str | None
    change_type: str
    payload_ref: str
    generator_id: str
    generator_version: str
    provenance_ref: str
    created_at: str
    status: str = "CANDIDATE"


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    candidate_id: str
    benchmark_snapshot_id: str
    optimizer_id: str
    optimizer_version: str
    run_config_hash: str
    started_at: str
    completed_at: str | None = None
    execution_manifest_refs: tuple[str, ...] = ()
    objective_vector_id: str | None = None
    regression_result: str = "NOT_RUN"
    promotion_status: str = "CANDIDATE"
    run_id: str | None = None


class OptimizationRegistry:
    """In-memory reference registry; persistence is a future storage adapter."""

    def __init__(self) -> None:
        self._candidates: dict[str, CandidateChange] = {}
        self._experiments: dict[str, Experiment] = {}
        self._objectives: dict[str, ObjectiveVector] = {}

    def register_candidate(self, *, change_type: str, payload_ref: str, generator_id: str,
                           generator_version: str, provenance_ref: str,
                           parent_candidate_id: str | None = None) -> CandidateChange:
        if change_type.startswith("cer_") or change_type.startswith("benchmark_truth"):
            raise ValueError("optimizer cannot directly mutate CER governance or benchmark truth")
        if parent_candidate_id is not None and parent_candidate_id not in self._candidates:
            raise KeyError(parent_candidate_id)
        candidate = CandidateChange(
            f"CAND-{uuid.uuid4().hex[:12]}", parent_candidate_id, change_type,
            payload_ref, generator_id, generator_version, provenance_ref, utc_now()
        )
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def get_candidate(self, candidate_id: str) -> CandidateChange:
        return self._candidates[candidate_id]

    def register_experiment(self, *, candidate_id: str, benchmark_snapshot_id: str,
                            optimizer_id: str, optimizer_version: str,
                            run_config: Mapping[str, object], run_id: str | None = None) -> Experiment:
        if candidate_id not in self._candidates:
            raise KeyError(candidate_id)
        experiment = Experiment(
            f"EXP-{uuid.uuid4().hex[:12]}", candidate_id, benchmark_snapshot_id,
            optimizer_id, optimizer_version, stable_hash(run_config), utc_now(), run_id=run_id
        )
        self._experiments[experiment.experiment_id] = experiment
        return experiment

    def record_objective(self, experiment_id: str, vector: ObjectiveVector) -> Experiment:
        experiment = self._experiments[experiment_id]
        if vector.experiment_id != experiment_id:
            raise ValueError("objective vector does not match experiment")
        self._objectives[vector.vector_id] = vector
        updated = Experiment(**{**asdict(experiment), "objective_vector_id": vector.vector_id})
        self._experiments[experiment_id] = updated
        return updated

    def complete_experiment(self, experiment_id: str, *, regression_result: str,
                            promotion_status: str = "CANDIDATE",
                            execution_manifest_refs: Sequence[str] = ()) -> Experiment:
        experiment = self._experiments[experiment_id]
        if regression_result not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}:
            raise ValueError(regression_result)
        if promotion_status not in {"CANDIDATE", "REJECTED", "REVIEW_REQUIRED", "APPROVED", "RELEASED"}:
            raise ValueError(promotion_status)
        if promotion_status in {"APPROVED", "RELEASED"} and regression_result != "PASS":
            raise ValueError("promotion requires passing regression")
        updated = Experiment(**{**asdict(experiment),
                                "completed_at": utc_now(),
                                "execution_manifest_refs": tuple(execution_manifest_refs),
                                "regression_result": regression_result,
                                "promotion_status": promotion_status})
        self._experiments[experiment_id] = updated
        return updated

    def get_experiment(self, experiment_id: str) -> Experiment:
        return self._experiments[experiment_id]

    def get_objective(self, vector_id: str) -> ObjectiveVector:
        return self._objectives[vector_id]

    def all_candidates(self) -> tuple[CandidateChange, ...]:
        return tuple(self._candidates.values())

    def all_experiments(self) -> tuple[Experiment, ...]:
        return tuple(self._experiments.values())


DEFAULT_OBJECTIVE_SPECS = tuple(ObjectiveSpec(name, direction) for name, direction in DEFAULT_OBJECTIVES)
