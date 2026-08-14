"""Minimal OPRO-style optimizer adapter for AgentFactory.

The adapter is deliberately provider-agnostic: the LLM/prompt optimizer is injected
as a callable. OPRO can only emit CandidateChange objects; promotion remains under
benchmark, regression, CER, and HOTL governance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from optimization import CandidateChange, OptimizationRegistry


@dataclass(frozen=True)
class OPROObservation:
    candidate_id: str
    objective_values: Mapping[str, float]
    feedback: str = ""


@dataclass(frozen=True)
class OPROBaselineConfig:
    optimizer_id: str = "opro"
    optimizer_version: str = "baseline-1.0"
    max_candidates: int = 3


class OPROBaseline:
    """Provider-neutral OPRO baseline candidate generator.

    `propose` receives prior observations and returns a candidate payload. The
    callable is intentionally outside the kernel so an LLM provider can be
    substituted without changing CER or benchmark semantics.
    """

    def __init__(self, registry: OptimizationRegistry,
                 proposer: Callable[[Sequence[OPROObservation]], str],
                 config: OPROBaselineConfig | None = None) -> None:
        self.registry = registry
        self.proposer = proposer
        self.config = config or OPROBaselineConfig()
        if self.config.max_candidates < 1:
            raise ValueError("max_candidates must be >= 1")

    def propose(self, *, observations: Sequence[OPROObservation],
                parent_candidate_id: str | None = None) -> CandidateChange:
        if len(observations) > self.config.max_candidates:
            observations = observations[-self.config.max_candidates:]
        payload = self.proposer(tuple(observations))
        if not payload or not payload.strip():
            raise ValueError("OPRO proposer returned an empty candidate")
        return self.registry.register_candidate(
            change_type="prompt",
            payload_ref=payload.strip(),
            generator_id=self.config.optimizer_id,
            generator_version=self.config.optimizer_version,
            provenance_ref="opro-observation-chain",
            parent_candidate_id=parent_candidate_id,
        )


def deterministic_baseline_proposer(observations: Sequence[OPROObservation]) -> str:
    """Deterministic local baseline used for regression tests.

    It does not claim to implement an LLM. It simply selects a candidate payload
    from the best observed quality signal, providing a reproducible OPRO adapter
    baseline before a real model provider is connected.
    """
    if not observations:
        return "baseline: preserve current instruction"
    best = max(observations, key=lambda item: item.objective_values.get("quality", 0.0))
    return f"baseline: improve from candidate {best.candidate_id}; feedback={best.feedback}"
